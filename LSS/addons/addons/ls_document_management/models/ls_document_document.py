# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Controlled document master record.

Implements the lifecycle Draft -> Under Review -> Approved -> Published ->
Archived, the parallel approval routing, the link between a document and its
effective version, and the retention evaluation performed by the scheduled
action.
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

STATE_DRAFT = "draft"
STATE_UNDER_REVIEW = "under_review"
STATE_APPROVED = "approved"
STATE_PUBLISHED = "published"
STATE_ARCHIVED = "archived"


class LsDocumentDocument(models.Model):
    """A controlled document under formal document control."""

    _name = "ls.document.document"
    _description = "Life Sciences Controlled Document"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "reference desc, id desc"

    reference = fields.Char(
        string="Document Number",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
    )
    name = fields.Char(
        string="Title",
        required=True,
        translate=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    description = fields.Text(translate=True)
    state = fields.Selection(
        selection=[
            (STATE_DRAFT, "Draft"),
            (STATE_UNDER_REVIEW, "Under Review"),
            (STATE_APPROVED, "Approved"),
            (STATE_PUBLISHED, "Published"),
            (STATE_ARCHIVED, "Archived"),
        ],
        string="Status",
        required=True,
        default=STATE_DRAFT,
        copy=False,
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    folder_id = fields.Many2one(comodel_name="ls.document.folder", required=True,
                                index=True,
                                ondelete="restrict",
                                check_company=True,
                                tracking=True,)
    tag_ids = fields.Many2many(
        comodel_name="ls.document.tag",
        relation="ls_document_document_tag_rel",
        column1="document_id",
        column2="tag_id",
        string="Tags",
    )
    owner_id = fields.Many2one(
        comodel_name="res.users",
        string="Document Owner",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User accountable for the content and periodic review.",
    )
    version_ids = fields.One2many(
        comodel_name="ls.document.version",
        inverse_name="document_id",
        string="Versions",
    )
    version_count = fields.Integer(compute="_compute_version_count",)
    latest_version_id = fields.Many2one(comodel_name="ls.document.version", compute="_compute_latest_version_id",
                                        store=True,)
    current_version_id = fields.Many2one(
        comodel_name="ls.document.version",
        string="Effective Version",
        readonly=True,
        copy=False,
        ondelete="set null",
        tracking=True,
        help="Version currently in force, set when the document is published.",
    )
    approver_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_document_document_approver_rel",
        column1="document_id",
        column2="user_id",
        string="Approvers",
        copy=False,
        help=(
            "Users who must all approve the document before it can be "
            "published. Approvals are requested in parallel."
        ),
    )
    approval_ids = fields.One2many(
        comodel_name="ls.document.approval",
        inverse_name="document_id",
        string="Approvals",
        copy=False,
    )
    link_ids = fields.One2many(
        comodel_name="ls.document.link",
        inverse_name="document_id",
        string="Linked Records",
        copy=False,
    )
    link_count = fields.Integer(
        string="Linked Record Count",
        compute="_compute_link_count",
    )
    effective_date = fields.Date(readonly=True,
                                 copy=False,
                                 tracking=True,
                                 help="Date on which the current version entered into force.",)
    archive_date = fields.Date(
        string="Archiving Date",
        readonly=True,
        copy=False,
        tracking=True,
    )
    retention_policy_id = fields.Many2one(comodel_name="ls.document.retention_policy", check_company=True,
                                          tracking=True,)
    retention_due_date = fields.Date(compute="_compute_retention_due_date",
                                     store=True,
                                     help="Date on which the retention period of this document elapses.",)
    retention_state = fields.Selection(
        selection=[
            ("not_applicable", "Not Applicable"),
            ("active", "Within Retention"),
            ("due_soon", "Due Soon"),
            ("elapsed", "Retention Elapsed"),
        ],
        string="Retention Status",
        required=True,
        default="not_applicable",
        readonly=True,
        copy=False,
        index=True,
        help=(
            "Maintained by the retention scheduled action and by the "
            "publication and archiving actions."
        ),
    )
    legal_hold = fields.Boolean(tracking=True,
                                help=(
                                    "When set, the document is exempt from any automatic retention "
                                    "action and cannot be archived automatically."),
                                )

    _reference_company_uniq = models.Constraint(
        "UNIQUE(reference, company_id)",
        "The document number must be unique per company.",
    )

    @api.depends("reference", "name")
    def _compute_display_name(self):
        """Display the document as ``[NUMBER] Title``."""
        for document in self:
            document.display_name = "[%s] %s" % (
                document.reference or "",
                document.name or "",
            )

    @api.depends("version_ids")
    def _compute_version_count(self):
        """Count the versions attached to the document."""
        for document in self:
            document.version_count = len(document.version_ids)

    @api.depends("version_ids.version_number")
    def _compute_latest_version_id(self):
        """Return the version bearing the highest version number."""
        for document in self:
            versions = document.version_ids.sorted(
                key=lambda version: version.version_number, reverse=True
            )
            document.latest_version_id = versions[0] if versions else False

    @api.depends("link_ids")
    def _compute_link_count(self):
        """Count the business records linked to the document."""
        for document in self:
            document.link_count = len(document.link_ids)

    @api.depends(
        "retention_policy_id.duration_value",
        "retention_policy_id.duration_unit",
        "retention_policy_id.retention_trigger",
        "effective_date",
        "archive_date",
    )
    def _compute_retention_due_date(self):
        """Derive the retention due date from the policy and trigger date."""
        for document in self:
            policy = document.retention_policy_id
            if not policy:
                document.retention_due_date = False
                continue
            if policy.retention_trigger == "publication":
                trigger_date = document.effective_date
            else:
                trigger_date = document.archive_date
            document.retention_due_date = policy.compute_due_date(trigger_date)

    @api.onchange("folder_id")
    def _onchange_folder_id(self):
        """Propose the folder defaults for retention policy and approvers."""
        for document in self:
            folder = document.folder_id
            if not folder:
                continue
            if folder.retention_policy_id and not document.retention_policy_id:
                document.retention_policy_id = folder.retention_policy_id
            if folder.default_approver_ids and not document.approver_ids:
                document.approver_ids = folder.default_approver_ids

    @api.constrains("approver_ids", "state")
    def _check_approvers_present(self):
        """A document leaving the Draft state must have at least one approver."""
        for document in self:
            if document.state == STATE_UNDER_REVIEW and not document.approver_ids:
                raise ValidationError(
                    _(
                        "Document '%(reference)s' cannot be submitted for "
                        "review without at least one approver.",
                        reference=document.reference,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the document number from the dedicated sequence."""
        for vals in vals_list:
            if vals.get("reference", _("New")) == _("New"):
                sequence = self.env["ir.sequence"].next_by_code(
                    "ls.document.document"
                )
                vals["reference"] = sequence or _("New")
        return super().create(vals_list)

    def write(self, vals):
        """Protect the folder assignment of documents that are in force."""
        if "folder_id" in vals:
            for document in self:
                if document.state in (STATE_PUBLISHED, STATE_ARCHIVED):
                    raise UserError(
                        _(
                            "The folder of document '%(reference)s' cannot be "
                            "changed while it is published or archived. Start "
                            "a revision first.",
                            reference=document.reference,
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_document_document(self):
        """Allow deletion only for drafts that were never published."""
        for document in self:
            if document.state != STATE_DRAFT:
                raise UserError(
                    _(
                        "Document '%(reference)s' cannot be deleted because "
                        "it is in status '%(state)s'. Only draft documents "
                        "may be deleted.",
                        reference=document.reference,
                        state=dict(
                            self._fields["state"].selection
                        )[document.state],
                    )
                )
            if document.current_version_id:
                raise UserError(
                    _(
                        "Document '%(reference)s' cannot be deleted because "
                        "it has already been published at least once. Archive "
                        "it instead.",
                        reference=document.reference,
                    )
                )

    def _create_approvals(self):
        """Create one pending approval per approver for the latest version."""
        self.ensure_one()
        approval_model = self.env["ls.document.approval"]
        previous = self.approval_ids.filtered(
            lambda approval: approval.state == "pending"
        )
        previous.write({"state": "cancelled"})
        # Every pending state change (this cancellation, and a rejection
        # recorded earlier in the same transaction) must reach the database
        # before the new approvals are inserted: the partial unique index on
        # pending approvals is checked at INSERT time, while ORM writes are
        # only flushed later.
        approval_model.flush_model(["state"])
        for approver in self.approver_ids:
            approval_model.create(
                {
                    "document_id": self.id,
                    "version_id": self.latest_version_id.id,
                    "approver_id": approver.id,
                }
            )

    def _pending_approvals(self):
        """Return the approvals of the current review cycle still pending."""
        self.ensure_one()
        return self.approval_ids.filtered(
            lambda approval: approval.state == "pending"
            and approval.version_id == self.latest_version_id
        )

    def action_submit_review(self):
        """Move a draft document to Under Review and request approvals."""
        for document in self:
            if document.state != STATE_DRAFT:
                raise UserError(
                    _(
                        "Only draft documents can be submitted for review "
                        "(document '%(reference)s').",
                        reference=document.reference,
                    )
                )
            if not document.latest_version_id:
                raise UserError(
                    _(
                        "Document '%(reference)s' has no version. Upload a "
                        "file before submitting it for review.",
                        reference=document.reference,
                    )
                )
            if not document.approver_ids:
                raise UserError(
                    _(
                        "Document '%(reference)s' has no approver. Add at "
                        "least one approver before submitting it.",
                        reference=document.reference,
                    )
                )
            document.state = STATE_UNDER_REVIEW
            document._create_approvals()
            document.message_post(
                body=_(
                    "Version %(version)s submitted for review. "
                    "%(count)s approval(s) requested.",
                    version=document.latest_version_id.version_number,
                    count=len(document.approver_ids),
                )
            )
        return True

    def _evaluate_approvals(self):
        """Move the document to Approved once every approval is granted."""
        self.ensure_one()
        if self.state != STATE_UNDER_REVIEW:
            return False
        if self._pending_approvals():
            return False
        self.state = STATE_APPROVED
        self.message_post(body=_("All approvals granted. Document approved."))
        return True

    def action_reject(self):
        """Open the wizard capturing the mandatory rejection reason."""
        self.ensure_one()
        if self.state != STATE_UNDER_REVIEW:
            raise UserError(
                _(
                    "Only documents under review can be rejected "
                    "(document '%(reference)s').",
                    reference=self.reference,
                )
            )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_document_management.action_ls_document_reject_wizard"
        )
        action["context"] = {"default_document_id": self.id}
        return action

    def _check_manager_role(self):
        """Verify that the current user holds the Document Manager role.

        Publication and archiving change the regulatory status of a document
        and are therefore reserved to Document Managers. The check is applied
        server side so that it cannot be bypassed by a direct RPC call.

        :raises UserError: when the current user is not a Document Manager.
        """
        if not self.env.user.has_group(
            "ls_document_management.group_ls_document_manager"
        ):
            raise UserError(
                _(
                    "Only a Life Sciences Document Manager may publish or "
                    "archive a controlled document."
                )
            )

    def action_publish(self):
        """Put the approved version into force."""
        self._check_manager_role()
        for document in self:
            if document.state != STATE_APPROVED:
                raise UserError(
                    _(
                        "Only approved documents can be published "
                        "(document '%(reference)s').",
                        reference=document.reference,
                    )
                )
            new_version = document.latest_version_id
            if not new_version:
                raise UserError(
                    _(
                        "Document '%(reference)s' has no version to publish.",
                        reference=document.reference,
                    )
                )
            previous_version = document.current_version_id
            if previous_version and previous_version != new_version:
                previous_version.write({"is_superseded": True})
            document.write(
                {
                    "state": STATE_PUBLISHED,
                    "current_version_id": new_version.id,
                    "effective_date": fields.Date.context_today(document),
                }
            )
            document.update_retention_state()
            document.message_post(
                body=_(
                    "Version %(version)s published and effective from "
                    "%(date)s.",
                    version=new_version.version_number,
                    date=document.effective_date,
                )
            )
        return True

    def action_start_revision(self):
        """Return a published document to Draft to prepare a new version.

        The effective version stays in force so that users keep access to the
        approved content while the revision is being prepared.
        """
        for document in self:
            if document.state != STATE_PUBLISHED:
                raise UserError(
                    _(
                        "Only published documents can enter revision "
                        "(document '%(reference)s').",
                        reference=document.reference,
                    )
                )
            document.state = STATE_DRAFT
            document.message_post(
                body=_(
                    "Revision started. Version %(version)s remains effective "
                    "until a new version is published.",
                    version=document.current_version_id.version_number,
                )
            )
        return True

    def action_archive_document(self):
        """Withdraw a published document from use.

        Reserved to Document Managers. The scheduled action uses
        :meth:`_archive_document` directly, which applies the same state
        checks without the role check.
        """
        self._check_manager_role()
        return self._archive_document(
            _("Document archived and withdrawn from use.")
        )

    def _archive_document(self, message_body):
        """Apply the archiving transition without checking the user role.

        :param message_body: body of the message logged on the document.
        :return: ``True`` when every document was archived.
        :raises UserError: when a document is not in the Published status.
        """
        for document in self:
            if document.state != STATE_PUBLISHED:
                raise UserError(
                    _(
                        "Only published documents can be archived "
                        "(document '%(reference)s').",
                        reference=document.reference,
                    )
                )
            document.write(
                {
                    "state": STATE_ARCHIVED,
                    "archive_date": fields.Date.context_today(document),
                }
            )
            document.update_retention_state()
            document.message_post(body=message_body)
        return True

    def action_reset_to_draft(self):
        """Return an approved document to Draft before publication."""
        for document in self:
            if document.state != STATE_APPROVED:
                raise UserError(
                    _(
                        "Only approved documents that are not yet published "
                        "can be reset to draft (document '%(reference)s').",
                        reference=document.reference,
                    )
                )
            document.approval_ids.filtered(
                lambda approval: approval.state == "pending"
            ).write({"state": "cancelled"})
            document.state = STATE_DRAFT
            document.message_post(body=_("Document reset to draft."))
        return True

    def action_open_new_version_wizard(self):
        """Open the wizard used to upload a new version."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_document_management.action_ls_document_new_version_wizard"
        )
        action["context"] = {"default_document_id": self.id}
        return action

    def action_open_versions(self):
        """Open the version history of the document."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_document_management.action_ls_document_version"
        )
        action["domain"] = [("document_id", "=", self.id)]
        action["context"] = {"default_document_id": self.id}
        return action

    def action_open_links(self):
        """Open the records linked to the document."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "ls_document_management.action_ls_document_link"
        )
        action["domain"] = [("document_id", "=", self.id)]
        action["context"] = {"default_document_id": self.id}
        return action

    def update_retention_state(self):
        """Recompute and store the retention status of the documents.

        The status is stored rather than computed on the fly so that it can be
        used in list filters and grouping. It is refreshed by the retention
        scheduled action and by the publication and archiving actions.

        :return: ``True`` when the update completed.
        """
        today = fields.Date.context_today(self)
        for document in self:
            policy = document.retention_policy_id
            due_date = document.retention_due_date
            if not policy or not due_date:
                document.retention_state = "not_applicable"
                continue
            if due_date <= today:
                document.retention_state = "elapsed"
            elif (due_date - today).days <= policy.notice_period_days:
                document.retention_state = "due_soon"
            else:
                document.retention_state = "active"
        return True

    def _notify_document_managers(self, body):
        """Post a message notifying every Document Manager.

        :param body: HTML body of the message to post.
        """
        self.ensure_one()
        users = self.env["res.users"].sudo().search([("active", "=", True)])
        managers = users.filtered(
            lambda user: user.has_group(
                "ls_document_management.group_ls_document_manager"
            )
        )
        if not managers:
            _logger.info(
                "No Document Manager found to notify for document %s.",
                self.reference,
            )
            return False
        self.message_post(body=body, partner_ids=managers.partner_id.ids)
        return True

    @api.model
    def _cron_evaluate_retention(self):
        """Refresh retention statuses and apply end-of-retention actions.

        Executed by the scheduled action. Documents under legal hold are
        refreshed but never archived automatically. No document is ever
        deleted by this method.

        :return: ``True`` when the run completed.
        """
        documents = self.search(
            [
                ("retention_policy_id", "!=", False),
                ("state", "in", (STATE_PUBLISHED, STATE_ARCHIVED)),
            ]
        )
        documents.update_retention_state()
        elapsed = documents.filtered(
            lambda document: document.retention_state == "elapsed"
        )
        for document in elapsed:
            if document.legal_hold:
                document._notify_document_managers(
                    body=_(
                        "Retention period elapsed on %(date)s. No action was "
                        "taken because the document is under legal hold.",
                        date=document.retention_due_date,
                    )
                )
                continue
            action = document.retention_policy_id.end_of_life_action
            if action == "archive" and document.state == STATE_PUBLISHED:
                document._archive_document(
                    _(
                        "Retention period elapsed on %(date)s. The document "
                        "was archived automatically and requires a "
                        "disposition decision.",
                        date=document.retention_due_date,
                    )
                )
                document._notify_document_managers(
                    body=_(
                        "Retention period elapsed. This document was archived "
                        "automatically and requires a disposition decision."
                    )
                )
            else:
                document._notify_document_managers(
                    body=_(
                        "Retention period elapsed on %(date)s. The document "
                        "requires a disposition decision.",
                        date=document.retention_due_date,
                    )
                )
        _logger.info(
            "Retention evaluation completed: %s document(s) evaluated, "
            "%s with elapsed retention.",
            len(documents),
            len(elapsed),
        )
        return True
