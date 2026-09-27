# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Certificates of Analysis."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsLabCoa(models.Model):
    """A Certificate of Analysis issued from an approved sample.

    A certificate can only be issued from a sample in state ``approved``, and
    once issued it is frozen. Corrections are made by issuing a new version
    that supersedes the previous one, never by editing an issued certificate.
    """

    _name = "ls.lab.coa"
    _description = "Certificate of Analysis"
    _inherit = ["ls.lab.signed.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, name desc, version desc"

    name = fields.Char(
        string="Certificate Reference",
        required=True,
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    version = fields.Integer(default=1,
                             required=True,
                             readonly=True,
                             copy=False,
                             tracking=True,)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("superseded", "Superseded"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    sample_id = fields.Many2one(comodel_name="ls.lab.sample", required=True,
                                ondelete="restrict",
                                index=True,
                                tracking=True,)
    product_id = fields.Many2one(related="sample_id.product_id", store=True, index=True)
    lot_id = fields.Many2one(
        related="sample_id.lot_id", string="Lot / Serial Number", store=True
    )
    batch_reference = fields.Char(related="sample_id.batch_reference", store=True)
    specification_id = fields.Many2one(related="sample_id.specification_id", store=True)
    overall_result = fields.Selection(related="sample_id.overall_result", store=True)
    conclusion = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("conforms", "Conforms To Specification"),
            ("does_not_conform", "Does Not Conform To Specification"),
        ],
        compute="_compute_conclusion",
        store=True,
        help="Derived from the overall result of the source sample.",
    )
    reportable_result_ids = fields.Many2many(
        comodel_name="ls.lab.test_result",
        string="Reported Results",
        compute="_compute_reportable_result_ids",
        help="Results of the source sample flagged for inclusion on the "
             "certificate by the specification.",
    )
    customer_id = fields.Many2one(comodel_name="res.partner")
    remarks = fields.Text()
    issued_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                   copy=False,
                                   tracking=True,)
    issue_date = fields.Datetime(readonly=True, copy=False)
    cancel_reason = fields.Text(string="Cancellation Reason", copy=False)
    predecessor_id = fields.Many2one(
        comodel_name="ls.lab.coa",
        string="Supersedes",
        readonly=True,
        copy=False,
    )
    successor_id = fields.Many2one(
        comodel_name="ls.lab.coa",
        string="Superseded By",
        readonly=True,
        copy=False,
    )
    revision_reason = fields.Text(copy=False)
    company_id = fields.Many2one(related="sample_id.company_id", store=True, index=True)

    _name_version_uniq = models.Constraint(
        "UNIQUE (name, version)",
        "A certificate version must be unique for a given certificate reference.",
    )

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    @api.depends("sample_id.overall_result")
    def _compute_conclusion(self):
        """Derive the certificate conclusion from the sample verdict."""
        mapping = {
            "conform": "conforms",
            "non_conform": "does_not_conform",
            "pending": "pending",
        }
        for certificate in self:
            certificate.conclusion = mapping.get(
                certificate.sample_id.overall_result, "pending"
            )

    @api.depends("sample_id.result_ids.specification_line_id")
    def _compute_reportable_result_ids(self):
        """Select the results the specification marks as reportable."""
        for certificate in self:
            certificate.reportable_result_ids = certificate.sample_id.result_ids.filtered(
                lambda res: res.specification_line_id.report_on_coa
            )

    @api.depends("name", "version", "product_id")
    def _compute_display_name(self):
        """Show the certificate reference, version and product."""
        for certificate in self:
            product = certificate.product_id.display_name or ""
            certificate.display_name = (
                f"{certificate.name} v{certificate.version} - {product}".strip(" -")
            )

    # ------------------------------------------------------------------
    # Creation and modification guards
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the certificate reference from the sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.lab.coa"
                ) or "New"
        return super().create(vals_list)

    def write(self, vals):
        """Refuse changes to an issued certificate (BRU-23)."""
        controlled = {
            "sample_id",
            "customer_id",
            "remarks",
            "version",
        }
        if controlled & set(vals):
            frozen = self.filtered(
                lambda coa: coa.state in ("issued", "superseded")
            )
            if frozen:
                raise UserError(
                    self.env._(
                        "%(count)s certificate(s) have been issued and cannot be "
                        "modified. Issue a new version instead.",
                        count=len(frozen),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_lab_coa(self):
        """Refuse deletion of a certificate that has been issued."""
        issued = self.filtered(lambda coa: coa.state != "draft")
        if issued:
            raise UserError(
                self.env._(
                    "%(count)s certificate(s) have left the draft state and "
                    "cannot be deleted.",
                    count=len(issued),
                )
            )

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_issue(self):
        """Issue the certificate from an approved sample (BRU-22)."""
        for certificate in self:
            if certificate.state != "draft":
                raise UserError(
                    self.env._(
                        "Certificate '%(certificate)s' is in status '%(state)s' "
                        "and cannot be issued.",
                        certificate=certificate.name,
                        state=certificate.state,
                    )
                )
            if certificate.sample_id.state not in ("approved", "reported"):
                raise UserError(
                    self.env._(
                        "A certificate can only be issued from an approved "
                        "sample. Sample '%(sample)s' is in status '%(state)s'.",
                        sample=certificate.sample_id.name,
                        state=certificate.sample_id.state,
                    )
                )
        return self.write({
            "state": "issued",
            "issued_by_id": self.env.user.id,
            "issue_date": fields.Datetime.now(),
        })

    def action_cancel(self):
        """Cancel a draft certificate, requiring a reason."""
        for certificate in self:
            if certificate.state != "draft":
                raise UserError(
                    self.env._(
                        "Only draft certificates can be cancelled. "
                        "'%(certificate)s' is in status '%(state)s'.",
                        certificate=certificate.name,
                        state=certificate.state,
                    )
                )
            if not certificate.cancel_reason:
                raise UserError(
                    self.env._(
                        "A cancellation reason is required for certificate "
                        "'%(certificate)s'.",
                        certificate=certificate.name,
                    )
                )
        return self.write({"state": "cancelled"})

    def action_create_revision(self):
        """Create a new version superseding an issued certificate."""
        self.ensure_one()
        if self.state != "issued":
            raise UserError(
                self.env._(
                    "Only an issued certificate can be revised. "
                    "'%(certificate)s' is in status '%(state)s'.",
                    certificate=self.name,
                    state=self.state,
                )
            )
        if not self.revision_reason:
            raise UserError(
                self.env._(
                    "A revision reason is required before certificate "
                    "'%(certificate)s' can be superseded.",
                    certificate=self.name,
                )
            )
        successor = self.copy({
            "name": self.name,
            "version": self.version + 1,
            "state": "draft",
            "predecessor_id": self.id,
            "issued_by_id": False,
            "issue_date": False,
            "revision_reason": False,
        })
        self.sudo().write({"successor_id": successor.id, "state": "superseded"})
        successor.message_post(
            body=self.env._(
                "Issued as version %(version)s superseding version "
                "%(predecessor)s. Reason: %(reason)s",
                version=successor.version,
                predecessor=self.version,
                reason=self.revision_reason or "",
            )
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.coa",
            "res_id": successor.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_issue_signature(self):
        """Open the signature-intent wizard for certificate issue."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(
                self.env._(
                    "Certificate '%(certificate)s' is in status '%(state)s' and "
                    "cannot be issued.",
                    certificate=self.name,
                    state=self.state,
                )
            )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.signature_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
                "default_meaning": "issued",
            },
        }

    def _signature_target_action(self):
        """Issue the certificate once signature intent has been recorded."""
        return self.action_issue()
