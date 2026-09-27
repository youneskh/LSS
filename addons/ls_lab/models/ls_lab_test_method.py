# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Analytical test method register."""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class LsLabTestMethod(models.Model):
    """A controlled analytical test method.

    An approved method is frozen: it cannot be edited, only superseded by a new
    version. Specifications may only reference approved methods.
    """

    _name = "ls.lab.test_method"
    _description = "Laboratory Test Method"
    _inherit = ["ls.lab.controlled.mixin", "mail.thread", "mail.activity.mixin"]
    _order = "code, version desc"

    _CONTROLLED_FIELDS = (
        "name",
        "technique",
        "result_type",
        "default_uom_id",
        "decimal_precision",
        "reference_document",
        "procedure_summary",
        "description",
        "instrument_required",
        "instrument_category",
        "validation_status",
        "validation_reference",
    )
    _FROZEN_STATES = ("approved", "obsolete")
    _SEQUENCE_CODE = "ls.lab.test_method"
    _SEQUENCE_FIELD = "code"

    name = fields.Char(
        string="Method Name",
        required=True,
        translate=True,
        tracking=True,
    )
    code = fields.Char(
        string="Method Code",
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
            ("review", "Under Review"),
            ("approved", "Approved"),
            ("obsolete", "Obsolete"),
        ],
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
    )
    technique = fields.Selection(
        selection=[
            ("chromatographic", "Chromatographic"),
            ("spectroscopic", "Spectroscopic"),
            ("titrimetric", "Titrimetric"),
            ("gravimetric", "Gravimetric"),
            ("physical", "Physical"),
            ("microbiological", "Microbiological"),
            ("biochemical", "Biochemical"),
            ("other", "Other"),
        ],
        default="physical",
        required=True,
        tracking=True,
    )
    result_type = fields.Selection(
        selection=[
            ("numeric", "Numeric"),
            ("text", "Text"),
            ("boolean", "Pass / Fail"),
        ],
        default="numeric",
        required=True,
        tracking=True,
        help="Determines which result field the analyst completes and how "
             "conformity is evaluated.",
    )
    default_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Default Unit of Measure",
    )
    decimal_precision = fields.Integer(
        string="Decimal Places",
        default=2,
        help="Number of decimal places displayed for numeric results.",
    )
    reference_document = fields.Char(help="Free-text reference to the procedure, monograph or standard on "
                                     "which the method is based. No monograph content is stored by "
                                     "this module.",)
    procedure_summary = fields.Text(translate=True)
    description = fields.Text(translate=True)
    instrument_required = fields.Boolean()
    instrument_category = fields.Char(help="Free-text category of instrument required, for example 'HPLC'.",)
    validation_status = fields.Selection(
        selection=[
            ("not_required", "Not Required"),
            ("planned", "Planned"),
            ("in_progress", "In Progress"),
            ("validated", "Validated"),
            ("revalidation_due", "Revalidation Due"),
        ],
        string="Method Validation Status",
        default="not_required",
        required=True,
        tracking=True,
        help="Records the validation status of the analytical procedure. This "
             "module does not perform method validation; it records the status "
             "asserted by the organisation.",
    )
    validation_reference = fields.Char(help="Free-text reference to the method validation record held "
                                       "elsewhere, for example in the validation management module.",)
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    approval_date = fields.Datetime(readonly=True,
                                    copy=False,
                                    tracking=True,)
    obsolete_reason = fields.Text(string="Obsolescence Reason", copy=False)
    predecessor_id = fields.Many2one(
        comodel_name="ls.lab.test_method",
        string="Supersedes",
        readonly=True,
        copy=False,
    )
    successor_id = fields.Many2one(
        comodel_name="ls.lab.test_method",
        string="Superseded By",
        readonly=True,
        copy=False,
    )
    specification_line_ids = fields.One2many(
        comodel_name="ls.lab.specification_line",
        inverse_name="test_method_id",
        string="Used In Specifications",
    )
    specification_line_count = fields.Integer(
        string="Specification Usage",
        compute="_compute_specification_line_count",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", default=lambda self: self.env.company,
                                 index=True,)

    _code_version_uniq = models.Constraint(
        "UNIQUE (code, version)",
        "A test method version must be unique for a given method code.",
    )

    @api.depends("specification_line_ids")
    def _compute_specification_line_count(self):
        """Count the specification lines referencing each method."""
        grouped = self.env["ls.lab.specification_line"]._read_group(
            domain=[("test_method_id", "in", self.ids)],
            groupby=["test_method_id"],
            aggregates=["__count"],
        )
        counts = {method.id: count for method, count in grouped}
        for method in self:
            method.specification_line_count = counts.get(method.id, 0)

    @api.depends("code", "name", "version")
    def _compute_display_name(self):
        """Display code, version and name so that versions are distinguishable."""
        for method in self:
            method.display_name = f"[{method.code} v{method.version}] {method.name}"

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_submit_review(self):
        """Move a draft method to Under Review."""
        self._assert_state("draft", "Submit for Review")
        return self.write({"state": "review"})

    def action_reset_draft(self):
        """Return a method under review to Draft."""
        self._assert_state("review", "Reset to Draft")
        return self.write({"state": "draft"})

    def action_approve(self):
        """Approve a method under review and freeze it."""
        self._assert_state("review", "Approve")
        return self.write({
            "state": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        })

    def action_set_obsolete(self):
        """Make an approved method obsolete.

        A reason must already be recorded, so that the obsolescence of a
        controlled document is never undocumented.
        """
        self._assert_state("approved", "Set Obsolete")
        without_reason = self.filtered(lambda m: not m.obsolete_reason)
        if without_reason:
            raise UserError(
                self.env._(
                    "An obsolescence reason is required before a method may be "
                    "made obsolete. Missing on: %(records)s.",
                    records=", ".join(without_reason.mapped("display_name")),
                )
            )
        return self.write({"state": "obsolete"})

    def action_create_revision(self):
        """Create the next draft version of an approved method."""
        self.ensure_one()
        self._assert_state("approved", "Create Revision")
        successor = self._create_successor_version()
        successor.message_post(
            body=self.env._(
                "Created as version %(version)s superseding %(predecessor)s.",
                version=successor.version,
                predecessor=self.display_name,
            )
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "ls.lab.test_method",
            "res_id": successor.id,
            "view_mode": "form",
            "target": "current",
        }

    # ------------------------------------------------------------------
    # Scheduled action
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_method_review_due(self):
        """Post a notice on approved methods due for periodic review.

        The review interval is a system parameter, not a hardcoded regulatory
        value. This scheduled action is notification-only and never changes a
        method state (BRU-29).
        """
        interval_months = int(
            self.env["ir.config_parameter"].sudo().get_param(
                "ls_lab.method_review_interval_months", default="24"
            )
        )
        if interval_months <= 0:
            return 0
        threshold = fields.Datetime.now() - relativedelta(months=interval_months)
        due_methods = self.search([
            ("state", "=", "approved"),
            ("approval_date", "<", threshold),
        ])
        for method in due_methods:
            method.message_post(
                body=self.env._(
                    "This method was approved on %(approval_date)s, which is more "
                    "than %(interval)s months ago, and is due for periodic "
                    "review. This notice does not change the method status.",
                    approval_date=method.approval_date,
                    interval=interval_months,
                )
            )
        return len(due_methods)
