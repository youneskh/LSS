# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Controlled document mixin shared by all QMS documentary models.

This mixin implements the document lifecycle defined in the Life Sciences
Suite Functional Specification section 7.2:

    Draft -> Under Review -> Approved -> Published -> Under Revision
                                                   -> Obsolete

It is inherited by :class:`~odoo.addons.ls_qms.models.ls_qms_policy`,
``ls.qms.sop``, ``ls.qms.work_instruction`` and ``ls.qms.quality_plan``.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

#: Lifecycle states of a controlled document.
DOCUMENT_STATES = [
    ("draft", "Draft"),
    ("under_review", "Under Review"),
    ("approved", "Approved"),
    ("published", "Published"),
    ("under_revision", "Under Revision"),
    ("obsolete", "Obsolete"),
]

#: Allowed state machine transitions: {source_state: (target_state, ...)}.
DOCUMENT_TRANSITIONS = {
    "draft": ("under_review", "obsolete"),
    "under_review": ("approved", "draft"),
    "approved": ("published", "draft", "obsolete"),
    "published": ("under_revision", "obsolete"),
    "under_revision": ("under_review", "obsolete"),
    "obsolete": (),
}

#: States in which the documentary content is frozen.
LOCKED_STATES = ("published", "obsolete")

#: Concrete models that inherit this mixin. Extending modules that add a new
#: controlled document type must extend this tuple by overriding
#: :meth:`LsQmsDocumentMixin._ls_qms_document_models`.
LS_QMS_DOCUMENT_MODELS = (
    "ls.qms.policy",
    "ls.qms.sop",
    "ls.qms.work_instruction",
    "ls.qms.quality_plan",
)

#: Default review period applied when no system parameter is configured.
DEFAULT_REVIEW_PERIOD_MONTHS = 24

#: Default number of days before the review due date at which a document is
#: reported as "Due Soon" and a review activity is scheduled.
DEFAULT_REVIEW_LEAD_DAYS = 30


class LsQmsDocumentMixin(models.AbstractModel):
    """Lifecycle, versioning and periodic review behaviour of QMS documents."""

    _name = "ls.qms.document.mixin"
    _description = "Life Sciences QMS Controlled Document Mixin"
    _inherit = ["mail.thread", "mail.activity.mixin", "ls.qms.parameter.mixin"]
    _order = "reference, version desc"

    #: ``ir.sequence`` code used to allocate the document reference. Every
    #: concrete model inheriting this mixin must define it.
    _ls_qms_sequence_code = None

    name = fields.Char(
        string="Title",
        required=True,
        tracking=True,
    )
    reference = fields.Char(required=True,
                            readonly=True,
                            copy=False,
                            index=True,
                            default="/",
                            tracking=True,
                            help="Document identifier allocated by the numbering sequence. "
                            "All revisions of the same document share the same reference.",)
    version = fields.Integer(required=True,
                             readonly=True,
                             copy=False,
                             default=1,
                             tracking=True,
                             help="Revision number. Incremented each time a new revision is "
                             "created from a published document.",)
    state = fields.Selection(
        selection=DOCUMENT_STATES,
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        default="draft",
        index=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)
    author_id = fields.Many2one(comodel_name="res.users", required=True,
                                tracking=True,
                                default=lambda self: self.env.user,
                                help="Person responsible for drafting the document.",)
    reviewer_ids = fields.Many2many(
        comodel_name="res.users",
        string="Reviewers",
        help="Persons requested to review the document before approval.",
    )
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Owning Department",
        tracking=True,
    )
    date_submitted = fields.Datetime(
        string="Submitted On",
        readonly=True,
        copy=False,
    )
    date_approved = fields.Datetime(
        string="Approved On",
        readonly=True,
        copy=False,
    )
    date_effective = fields.Date(
        string="Effective Date",
        copy=False,
        tracking=True,
        help="Date on which the published revision becomes applicable.",
    )
    date_obsolete = fields.Date(
        string="Obsolete Since",
        readonly=True,
        copy=False,
        tracking=True,
    )
    review_period_months = fields.Integer(
        string="Review Period (Months)",
        required=True,
        default=lambda self: self._default_review_period_months(),
        help="Periodicity of the documented review. Set to 0 to exclude the "
        "document from the periodic review programme.",
    )
    date_next_review = fields.Date(
        string="Next Review Due",
        compute="_compute_date_next_review",
        store=True,
        readonly=False,
        tracking=True,
        help="Computed as Effective Date + Review Period. It can be "
        "overridden manually when a specific due date is required.",
    )
    review_state = fields.Selection(
        selection=[
            ("not_applicable", "Not Applicable"),
            ("ok", "Up To Date"),
            ("due_soon", "Due Soon"),
            ("overdue", "Overdue"),
        ],
        string="Review Status",
        compute="_compute_review_state",
        help="Computed at display time from the next review due date.",
    )
    reason_for_change = fields.Text(copy=False,
                                    help="Justification recorded when a new revision is created.",)
    attachment_count = fields.Integer(
        string="Attachments",
        compute="_compute_attachment_count",
    )

    # ------------------------------------------------------------------
    # Default value helpers
    # ------------------------------------------------------------------
    @api.model
    def _default_review_period_months(self):
        """Return the configured default review period, in months."""
        return self._get_int_parameter(
            "ls_qms.default_review_period_months",
            DEFAULT_REVIEW_PERIOD_MONTHS,
        )

    @api.model
    def _get_review_lead_days(self):
        """Return the number of days used to flag a review as due soon."""
        return self._get_int_parameter(
            "ls_qms.review_reminder_lead_days",
            DEFAULT_REVIEW_LEAD_DAYS,
        )

    @api.model
    def _is_segregation_enforced(self):
        """Return whether an author is forbidden to approve their own work."""
        return self._get_bool_parameter(
            "ls_qms.enforce_segregation_of_duties", True
        )

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends("date_effective", "review_period_months")
    def _compute_date_next_review(self):
        """Derive the next review due date from the effective date."""
        for document in self:
            if document.date_effective and document.review_period_months > 0:
                document.date_next_review = document.date_effective + relativedelta(
                    months=document.review_period_months
                )
            else:
                document.date_next_review = False

    @api.depends("state", "date_next_review")
    def _compute_review_state(self):
        """Classify each document against its periodic review due date."""
        today = fields.Date.context_today(self)
        lead_days = self._get_review_lead_days()
        for document in self:
            if document.state != "published" or not document.date_next_review:
                document.review_state = "not_applicable"
            elif document.date_next_review < today:
                document.review_state = "overdue"
            elif (document.date_next_review - today).days <= lead_days:
                document.review_state = "due_soon"
            else:
                document.review_state = "ok"

    @api.depends("reference", "name", "version")
    def _compute_display_name(self):
        """Render documents as ``[REFERENCE] Title (vN)``."""
        for document in self:
            document.display_name = "[%s] %s (v%s)" % (
                document.reference or "/",
                document.name or "",
                document.version,
            )

    def _compute_attachment_count(self):
        """Count the ``ir.attachment`` records linked to each document."""
        if not self.ids:
            for document in self:
                document.attachment_count = 0
            return
        grouped = self.env["ir.attachment"]._read_group(
            domain=[("res_model", "=", self._name), ("res_id", "in", self.ids)],
            groupby=["res_id"],
            aggregates=["__count"],
        )
        counts = dict(grouped)
        for document in self:
            document.attachment_count = counts.get(document.id, 0)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("state", "reference", "company_id")
    def _check_single_published_revision(self):
        """Forbid two simultaneously published revisions of one document."""
        for document in self.filtered(lambda doc: doc.state == "published"):
            duplicate = self.search_count(
                [
                    ("id", "!=", document.id),
                    ("reference", "=", document.reference),
                    ("company_id", "=", document.company_id.id),
                    ("state", "=", "published"),
                ]
            )
            if duplicate:
                raise ValidationError(
                    _(
                        "Document %(reference)s already has a published "
                        "revision. Only one revision may be effective at a "
                        "time.",
                        reference=document.reference,
                    )
                )

    @api.constrains("review_period_months")
    def _check_review_period_months(self):
        """Reject negative review periods."""
        for document in self:
            if document.review_period_months < 0:
                raise ValidationError(
                    _("The review period cannot be negative.")
                )

    @api.constrains("date_effective", "date_approved")
    def _check_effective_after_approval(self):
        """Ensure a document does not become effective before approval."""
        for document in self:
            if not document.date_effective or not document.date_approved:
                continue
            approval_date = document.date_approved.date()
            if document.date_effective < approval_date:
                raise ValidationError(
                    _(
                        "The effective date of %(reference)s cannot precede "
                        "its approval date.",
                        reference=document.reference,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the document reference from the numbering sequence."""
        for vals in vals_list:
            if not vals.get("reference") or vals["reference"] == "/":
                vals["reference"] = self._next_reference(vals)
        return super().create(vals_list)

    def write(self, vals):
        """Protect the content of published and obsolete revisions."""
        protected_fields = set(self._ls_qms_content_fields())
        if protected_fields.intersection(vals):
            locked = self.filtered(lambda doc: doc.state in LOCKED_STATES)
            if locked:
                raise UserError(
                    _(
                        "The content of %(references)s cannot be modified "
                        "because the revision is published or obsolete. "
                        "Create a new revision instead.",
                        references=", ".join(locked.mapped("reference")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_qms_document_mixin(self):
        """Allow deletion of draft revisions only."""
        undeletable = self.filtered(lambda doc: doc.state != "draft")
        if undeletable:
            raise UserError(
                _(
                    "Only draft documents may be deleted. %(references)s "
                    "must be set to obsolete instead.",
                    references=", ".join(undeletable.mapped("reference")),
                )
            )

    # ------------------------------------------------------------------
    # Business helpers
    # ------------------------------------------------------------------
    @api.model
    def _next_reference(self, vals=None):
        """Return the next reference from the model numbering sequence.

        :param dict vals: creation values, used to resolve the company.
        :rtype: str
        """
        if not self._ls_qms_sequence_code:
            raise UserError(
                _(
                    "Model %(model)s does not define a numbering sequence "
                    "code and cannot allocate a document reference.",
                    model=self._name,
                )
            )
        company_id = (vals or {}).get("company_id") or self.env.company.id
        sequence = self.env["ir.sequence"].with_company(company_id)
        reference = sequence.next_by_code(self._ls_qms_sequence_code)
        if not reference:
            raise UserError(
                _(
                    "The numbering sequence %(code)s is missing. Reinstall or "
                    "update the Life Sciences QMS module to restore it.",
                    code=self._ls_qms_sequence_code,
                )
            )
        return reference

    def _ls_qms_content_fields(self):
        """Return the field names frozen once a revision is published.

        Concrete models extend this list with their own content fields.

        :rtype: list
        """
        return [
            "name",
            "reference",
            "version",
            "date_effective",
            "reason_for_change",
            "author_id",
        ]

    @api.model
    def _ls_qms_document_models(self):
        """Return the concrete models using this mixin.

        :rtype: list
        """
        return [
            model_name
            for model_name in LS_QMS_DOCUMENT_MODELS
            if model_name in self.env
        ]

    def _ls_qms_check_transition(self, target_state):
        """Validate a state machine transition for every record in ``self``.

        :param str target_state: requested state.
        :raises UserError: when the transition is not allowed.
        """
        for document in self:
            allowed = DOCUMENT_TRANSITIONS.get(document.state, ())
            if target_state not in allowed:
                raise UserError(
                    _(
                        "Document %(reference)s cannot move from "
                        "%(source)s to %(target)s.",
                        reference=document.reference,
                        source=document.state,
                        target=target_state,
                    )
                )

    def _ls_qms_check_group(self, group_xml_id, action_label):
        """Raise a user error when the current user lacks ``group_xml_id``.

        :param str group_xml_id: full external identifier of the group.
        :param str action_label: human readable action, used in the message.
        """
        if not self.env.user.has_group(group_xml_id):
            raise UserError(
                _(
                    "You are not authorised to %(action)s quality documents.",
                    action=action_label,
                )
            )

    def _ls_qms_signature_hook(self, meaning):
        """Extension point for a regulated electronic signature.

        The base module records the acting user and the server timestamp on
        the document and in the message log. The ``ls_electronic_signature``
        module of the Life Sciences Suite is expected to override this method
        to request an authenticated signature before the transition is
        committed. This module does not itself implement authentication at
        the point of signing.

        :param str meaning: signature meaning, for example ``approval``.
        """
        self.ensure_one()
        return True

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_submit_for_review(self):
        """Move draft or under-revision documents to the review stage."""
        self._ls_qms_check_group("ls_qms.group_ls_qms_user", _("submit"))
        self._ls_qms_check_transition("under_review")
        self.write(
            {
                "state": "under_review",
                "date_submitted": fields.Datetime.now(),
            }
        )
        for document in self:
            document._ls_qms_schedule_reviewer_activities()
            document.message_post(
                body=_("Document submitted for review by %(user)s.",
                       user=self.env.user.display_name)
            )
        return True

    def action_approve(self):
        """Approve documents that completed their review."""
        self._ls_qms_check_group("ls_qms.group_ls_qms_approver", _("approve"))
        self._ls_qms_check_transition("approved")
        segregation = self._is_segregation_enforced()
        for document in self:
            if segregation and document.author_id == self.env.user:
                raise UserError(
                    _(
                        "Segregation of duties: the author of %(reference)s "
                        "may not approve it. Ask another approver to review "
                        "and approve the document.",
                        reference=document.reference,
                    )
                )
            document._ls_qms_signature_hook("approval")
        self.write(
            {
                "state": "approved",
                "approver_id": self.env.user.id,
                "date_approved": fields.Datetime.now(),
            }
        )
        for document in self:
            document.message_post(
                body=_("Document approved by %(user)s.",
                       user=self.env.user.display_name)
            )
        return True

    def action_publish(self):
        """Publish approved documents and retire the previous revision."""
        self._ls_qms_check_group("ls_qms.group_ls_qms_approver", _("publish"))
        self._ls_qms_check_transition("published")
        today = fields.Date.context_today(self)
        for document in self:
            values = {"state": "published"}
            if not document.date_effective:
                values["date_effective"] = today
            document.write(values)
            document._ls_qms_retire_previous_revision()
            document.message_post(
                body=_(
                    "Revision %(version)s published, effective %(date)s.",
                    version=document.version,
                    date=document.date_effective,
                )
            )
        return True

    def action_set_obsolete(self):
        """Withdraw documents from use."""
        self._ls_qms_check_group("ls_qms.group_ls_qms_manager", _("withdraw"))
        self._ls_qms_check_transition("obsolete")
        self.write(
            {
                "state": "obsolete",
                "date_obsolete": fields.Date.context_today(self),
            }
        )
        for document in self:
            document.message_post(
                body=_("Document set to obsolete by %(user)s.",
                       user=self.env.user.display_name)
            )
        return True

    def action_reset_to_draft(self):
        """Return a document under review or approved to the draft stage."""
        self._ls_qms_check_group("ls_qms.group_ls_qms_manager", _("reopen"))
        self._ls_qms_check_transition("draft")
        self.write(
            {
                "state": "draft",
                "approver_id": False,
                "date_approved": False,
                "date_submitted": False,
            }
        )
        for document in self:
            document.message_post(
                body=_("Document returned to draft by %(user)s.",
                       user=self.env.user.display_name)
            )
        return True

    def action_open_new_revision_wizard(self):
        """Open the wizard that creates the next revision."""
        self.ensure_one()
        self._ls_qms_check_group("ls_qms.group_ls_qms_user", _("revise"))
        self._ls_qms_check_transition("under_revision")
        return {
            "type": "ir.actions.act_window",
            "name": _("New Revision"),
            "res_model": "ls.qms.new.revision.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": self._name,
                "active_id": self.id,
            },
        }

    def action_open_reject_wizard(self):
        """Open the wizard that returns a document to its author."""
        self.ensure_one()
        self._ls_qms_check_group("ls_qms.group_ls_qms_approver", _("reject"))
        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Document"),
            "res_model": "ls.qms.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": self._name,
                "active_id": self.id,
            },
        }

    def action_open_attachments(self):
        """Open the attachments linked to the document."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }

    # ------------------------------------------------------------------
    # Revision management
    # ------------------------------------------------------------------
    def _ls_qms_revision_defaults(self, reason_for_change, date_effective=None):
        """Return the creation values of the next revision.

        :param str reason_for_change: mandatory change justification.
        :param date_effective: planned effective date of the new revision.
        :rtype: dict
        """
        self.ensure_one()
        return {
            "reference": self.reference,
            "version": self.version + 1,
            "state": "draft",
            "previous_revision_id": self.id,
            "reason_for_change": reason_for_change,
            "date_effective": date_effective or False,
            "date_submitted": False,
            "date_approved": False,
            "date_obsolete": False,
            "approver_id": False,
            "author_id": self.env.user.id,
        }

    def create_new_revision(self, reason_for_change, date_effective=None):
        """Create the next revision and place the current one under revision.

        :param str reason_for_change: mandatory change justification.
        :param date_effective: planned effective date of the new revision.
        :return: the newly created revision.
        :rtype: :class:`odoo.models.Model`
        """
        self.ensure_one()
        if not reason_for_change or not reason_for_change.strip():
            raise UserError(
                _("A reason for change is required to create a new revision.")
            )
        self._ls_qms_check_transition("under_revision")
        defaults = self._ls_qms_revision_defaults(
            reason_for_change, date_effective=date_effective
        )
        new_revision = self.copy(default=defaults)
        self.write({"state": "under_revision"})
        self.message_post(
            body=_(
                "Revision %(version)s created. Reason: %(reason)s",
                version=new_revision.version,
                reason=reason_for_change,
            )
        )
        return new_revision

    def ls_qms_reject(self, reason):
        """Return a document under review to its author.

        :param str reason: mandatory rejection reason, written to the
            message log and notified to the author as an activity.
        :rtype: bool
        """
        self.ensure_one()
        if not reason or not reason.strip():
            raise UserError(_("A rejection reason is required."))
        self._ls_qms_check_group("ls_qms.group_ls_qms_approver", _("reject"))
        self._ls_qms_check_transition("draft")
        self.write(
            {
                "state": "draft",
                "approver_id": False,
                "date_approved": False,
            }
        )
        self.message_post(
            body=_(
                "Document rejected by %(user)s. Reason: %(reason)s",
                user=self.env.user.display_name,
                reason=reason,
            )
        )
        activity_type = self.env.ref(
            "ls_qms.mail_activity_type_ls_qms_review",
            raise_if_not_found=False,
        )
        if activity_type:
            self.activity_schedule(
                act_type_xmlid="ls_qms.mail_activity_type_ls_qms_review",
                summary=_(
                    "Rework %(reference)s after rejection",
                    reference=self.reference,
                ),
                user_id=self.author_id.id,
            )
        return True

    def _ls_qms_retire_previous_revision(self):
        """Set the previous published revision of a document to obsolete."""
        self.ensure_one()
        previous = self.search(
            [
                ("id", "!=", self.id),
                ("reference", "=", self.reference),
                ("company_id", "=", self.company_id.id),
                ("state", "in", ("published", "under_revision")),
            ]
        )
        if not previous:
            return previous
        previous_values = {
            "state": "obsolete",
            "date_obsolete": fields.Date.context_today(self),
        }
        previous.write(previous_values)
        for document in previous:
            document.message_post(
                body=_(
                    "Superseded by revision %(version)s.",
                    version=self.version,
                )
            )
        return previous

    # ------------------------------------------------------------------
    # Periodic review programme
    # ------------------------------------------------------------------
    def _ls_qms_schedule_reviewer_activities(self):
        """Schedule a review activity for each declared reviewer."""
        self.ensure_one()
        activity_type = self.env.ref(
            "ls_qms.mail_activity_type_ls_qms_review",
            raise_if_not_found=False,
        )
        if not activity_type:
            return False
        for reviewer in self.reviewer_ids:
            self.activity_schedule(
                act_type_xmlid="ls_qms.mail_activity_type_ls_qms_review",
                summary=_("Review %(reference)s", reference=self.reference),
                user_id=reviewer.id,
            )
        return True

    @api.model
    def _ls_qms_documents_due_for_review(self, lead_days=None):
        """Return published documents whose review is due within ``lead_days``.

        :param int lead_days: look-ahead window. Defaults to the configured
            ``ls_qms.review_reminder_lead_days`` parameter.
        :rtype: :class:`odoo.models.Model`
        """
        if lead_days is None:
            lead_days = self._get_review_lead_days()
        horizon = fields.Date.context_today(self) + relativedelta(days=lead_days)
        return self.search(
            [
                ("state", "=", "published"),
                ("date_next_review", "!=", False),
                ("date_next_review", "<=", horizon),
            ]
        )

    @api.model
    def _cron_document_review_reminder(self):
        """Schedule review activities on documents reaching their due date.

        Executed by the ``ir.cron`` record
        ``ls_qms.ir_cron_ls_qms_document_review``. The method iterates over
        every concrete model using this mixin so that a single scheduled
        action covers all controlled document types.

        :return: the number of activities created.
        :rtype: int
        """
        activity_type = self.env.ref(
            "ls_qms.mail_activity_type_ls_qms_review",
            raise_if_not_found=False,
        )
        if not activity_type:
            return 0
        created = 0
        for model_name in self._ls_qms_document_models():
            model = self.env[model_name]
            for document in model._ls_qms_documents_due_for_review():
                if document._ls_qms_has_open_review_activity(activity_type):
                    continue
                document.activity_schedule(
                    act_type_xmlid="ls_qms.mail_activity_type_ls_qms_review",
                    date_deadline=document.date_next_review,
                    summary=_(
                        "Periodic review of %(reference)s",
                        reference=document.reference,
                    ),
                    user_id=document.author_id.id,
                )
                created += 1
        return created

    def _ls_qms_has_open_review_activity(self, activity_type):
        """Return whether an open review activity already exists.

        :param activity_type: ``mail.activity.type`` record to look for.
        :rtype: bool
        """
        self.ensure_one()
        return bool(
            self.env["mail.activity"].search_count(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", self.id),
                    ("activity_type_id", "=", activity_type.id),
                ]
            )
        )
