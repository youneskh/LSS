# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Root cause analysis model."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsCapaRootCause(models.Model):
    """A root cause analysis performed within a CAPA investigation.

    Three analysis methods are supported, matching the methods named in the
    Life Sciences Suite functional specification: Five Whys, Ishikawa
    (cause and effect) and FMEA. The method selected drives which fields are
    required and displayed.
    """

    _name = "ls.capa.root_cause"
    _description = "CAPA Root Cause Analysis"
    _inherit = ["mail.thread"]
    _order = "issue_id, sequence, id"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
    )
    issue_id = fields.Many2one(
        comodel_name="ls.capa.issue",
        string="CAPA",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    method = fields.Selection(
        selection=[
            ("five_whys", "Five Whys"),
            ("ishikawa", "Ishikawa (Cause and Effect)"),
            ("fmea", "FMEA"),
            ("other", "Other Documented Method"),
        ],
        string="Analysis Method",
        required=True,
        default="five_whys",
        tracking=True,
    )
    description = fields.Text(
        string="Root Cause Statement",
        required=True,
        help="Statement of the identified root cause, phrased as a "
             "verifiable cause rather than a symptom.",
    )
    is_primary = fields.Boolean(
        string="Primary Root Cause",
        tracking=True,
        help="Marks the root cause considered the principal contributor.",
    )
    analyst_id = fields.Many2one(comodel_name="res.users", required=True,
                                 default=lambda self: self.env.user,
                                 tracking=True,)
    date_analysis = fields.Date(
        string="Analysis Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("confirmed", "Confirmed")],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="issue_id.company_id",
                                 store=True,
                                 index=True,)

    # ------------------------------------------------------------------
    # Five Whys
    # ------------------------------------------------------------------
    why_1 = fields.Char()
    why_2 = fields.Char()
    why_3 = fields.Char()
    why_4 = fields.Char()
    why_5 = fields.Char()

    # ------------------------------------------------------------------
    # Ishikawa
    # ------------------------------------------------------------------
    ishikawa_category = fields.Selection(
        selection=[
            ("man", "People"),
            ("machine", "Equipment"),
            ("material", "Material"),
            ("method", "Method"),
            ("measurement", "Measurement"),
            ("environment", "Environment"),
        ],
        help="Category of the cause and effect diagram in which the root "
             "cause was located.",
    )

    # ------------------------------------------------------------------
    # FMEA
    # ------------------------------------------------------------------
    fmea_severity = fields.Integer(help="Severity rating on a 1 to 10 scale.",)
    fmea_occurrence = fields.Integer(help="Occurrence rating on a 1 to 10 scale.",)
    fmea_detection = fields.Integer(help="Detection rating on a 1 to 10 scale.",)
    fmea_rpn = fields.Integer(compute="_compute_fmea_rpn",
                              store=True,
                              help="Risk Priority Number, computed as Severity multiplied by "
                              "Occurrence multiplied by Detection.",)

    action_ids = fields.One2many(
        comodel_name="ls.capa.action",
        inverse_name="root_cause_id",
        string="Actions Addressing This Root Cause",
    )

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "The root cause analysis reference must be unique.",
    )

    @api.depends("fmea_severity", "fmea_occurrence", "fmea_detection")
    def _compute_fmea_rpn(self):
        """Compute the Risk Priority Number for FMEA analyses."""
        for record in self:
            if record.method == "fmea":
                record.fmea_rpn = (
                    record.fmea_severity
                    * record.fmea_occurrence
                    * record.fmea_detection
                )
            else:
                record.fmea_rpn = 0

    @api.constrains(
        "method",
        "fmea_severity",
        "fmea_occurrence",
        "fmea_detection",
    )
    def _check_fmea_ratings(self):
        """Restrict FMEA ratings to the documented 1 to 10 scale."""
        for record in self:
            if record.method != "fmea":
                continue
            ratings = {
                _("Severity"): record.fmea_severity,
                _("Occurrence"): record.fmea_occurrence,
                _("Detection"): record.fmea_detection,
            }
            for label, value in ratings.items():
                if not 1 <= value <= 10:
                    raise ValidationError(
                        _(
                            "Root cause %(reference)s: the FMEA %(label)s "
                            "rating must be between 1 and 10.",
                            reference=record.name,
                            label=label,
                        )
                    )

    @api.constrains("method", "why_1")
    def _check_five_whys(self):
        """Require the first Why on Five Whys analyses."""
        for record in self:
            if record.method != "five_whys":
                continue
            if not (record.why_1 or "").strip():
                raise ValidationError(
                    _(
                        "Root cause %(reference)s: the first Why must be "
                        "documented for a Five Whys analysis.",
                        reference=record.name,
                    )
                )

    @api.constrains("method", "ishikawa_category")
    def _check_ishikawa(self):
        """Require a diagram category on Ishikawa analyses."""
        for record in self:
            if record.method == "ishikawa" and not record.ishikawa_category:
                raise ValidationError(
                    _(
                        "Root cause %(reference)s: an Ishikawa category must "
                        "be selected for a cause and effect analysis.",
                        reference=record.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the root cause reference from the sequence.

        :param list vals_list: list of value dictionaries.
        :return: the created recordset.
        :rtype: ls.capa.root_cause
        """
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.capa.root_cause"
                ) or _("New")
        return super().create(vals_list)

    def action_confirm(self):
        """Confirm the analysis so it can gate the Action Planning step.

        :return: True when every record was confirmed.
        :rtype: bool
        """
        invalid = self.filtered(lambda r: r.state != "draft")
        if invalid:
            raise UserError(
                _(
                    "Only draft root cause analyses can be confirmed: "
                    "%(refs)s.",
                    refs=", ".join(invalid.mapped("name")),
                )
            )
        self.write({"state": "confirmed"})
        return True

    def action_reset_to_draft(self):
        """Return a confirmed analysis to draft for further investigation.

        :return: True when every record was reset.
        :rtype: bool
        """
        blocked = self.filtered(
            lambda r: r.issue_id.state
            in ("in_progress", "completed", "verified", "closed")
        )
        if blocked:
            raise UserError(
                _(
                    "Root cause analyses cannot be reset once their CAPA "
                    "started execution: %(refs)s.",
                    refs=", ".join(blocked.mapped("name")),
                )
            )
        self.write({"state": "draft"})
        return True
