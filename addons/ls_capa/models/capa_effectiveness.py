# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""CAPA effectiveness verification model."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsCapaEffectiveness(models.Model):
    """An effectiveness check verifying that a CAPA prevented recurrence.

    A check records the acceptance criteria agreed in advance, the method
    used to gather evidence, and the conclusion. When a check concludes that
    the CAPA was not effective, a follow-up CAPA can be raised directly from
    the record.
    """

    _name = "ls.capa.effectiveness"
    _description = "CAPA Effectiveness Check"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_id, date_planned, id"

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
    method = fields.Selection(
        selection=[
            ("data_review", "Data Review"),
            ("audit", "Follow-up Audit"),
            ("monitoring", "Process Monitoring"),
            ("retesting", "Retesting"),
            ("training_verification", "Training Verification"),
            ("other", "Other Documented Method"),
        ],
        string="Verification Method",
        required=True,
        default="data_review",
        tracking=True,
    )
    criteria = fields.Text(
        string="Acceptance Criteria",
        required=True,
        help="Objective criteria defined before the check is performed, "
             "against which effectiveness will be judged.",
    )
    date_planned = fields.Date(
        string="Planned Verification Date",
        required=True,
        tracking=True,
        help="Date on which the check is scheduled. It is normally set far "
             "enough after implementation for evidence to accumulate.",
    )
    date_check = fields.Date(
        string="Actual Verification Date",
        readonly=True,
        copy=False,
        tracking=True,
    )
    verifier_id = fields.Many2one(comodel_name="res.users", required=True,
                                  default=lambda self: self.env.user,
                                  tracking=True,
                                  help="User performing the effectiveness verification. Good practice "
                                  "is for this user to differ from the action owner.",)
    result = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("effective", "Effective"),
            ("not_effective", "Not Effective"),
        ],
        default="pending",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    conclusion = fields.Text(copy=False,
                             help="Narrative conclusion citing the evidence reviewed.",)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("done", "Done"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        copy=False,
    )
    new_capa_id = fields.Many2one(
        comodel_name="ls.capa.issue",
        string="Follow-up CAPA",
        readonly=True,
        copy=False,
        ondelete="set null",
        help="CAPA raised because this check concluded Not Effective.",
    )
    company_id = fields.Many2one(comodel_name="res.company", related="issue_id.company_id",
                                 store=True,
                                 index=True,)

    _name_uniq = models.Constraint(
        "UNIQUE(name)",
        "The effectiveness check reference must be unique.",
    )

    @api.constrains("state", "result", "conclusion")
    def _check_conclusion(self):
        """Require a conclusion and a decided result on completed checks."""
        for record in self:
            if record.state != "done":
                continue
            if record.result == "pending":
                raise ValidationError(
                    _(
                        "Effectiveness check %(reference)s cannot be "
                        "completed while its result is still Pending.",
                        reference=record.name,
                    )
                )
            if not (record.conclusion or "").strip():
                raise ValidationError(
                    _(
                        "Effectiveness check %(reference)s cannot be "
                        "completed without a conclusion.",
                        reference=record.name,
                    )
                )

    @api.constrains("date_planned", "issue_id")
    def _check_date_planned(self):
        """Ensure verification is not scheduled before identification."""
        for record in self:
            identified = record.issue_id.date_identified
            if (
                record.date_planned
                and identified
                and record.date_planned < identified
            ):
                raise ValidationError(
                    _(
                        "Effectiveness check %(reference)s cannot be planned "
                        "before the CAPA identification date.",
                        reference=record.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the effectiveness check reference from the sequence.

        :param list vals_list: list of value dictionaries.
        :return: the created recordset.
        :rtype: ls.capa.effectiveness
        """
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.capa.effectiveness"
                ) or _("New")
        return super().create(vals_list)

    def action_plan(self):
        """Move a draft check to Planned.

        :return: True when every record was planned.
        :rtype: bool
        """
        invalid = self.filtered(lambda r: r.state != "draft")
        if invalid:
            raise UserError(
                _(
                    "Only draft effectiveness checks can be planned: "
                    "%(refs)s.",
                    refs=", ".join(invalid.mapped("name")),
                )
            )
        self.write({"state": "planned"})
        return True

    def _conclude(self, result):
        """Complete the check with the supplied result.

        :param str result: either ``effective`` or ``not_effective``.
        :return: True when every record was completed.
        :rtype: bool
        """
        invalid = self.filtered(lambda r: r.state == "done")
        if invalid:
            raise UserError(
                _(
                    "Effectiveness checks %(refs)s are already completed.",
                    refs=", ".join(invalid.mapped("name")),
                )
            )
        missing = self.filtered(lambda r: not (r.conclusion or "").strip())
        if missing:
            raise UserError(
                _(
                    "A conclusion must be recorded before completing "
                    "effectiveness checks %(refs)s.",
                    refs=", ".join(missing.mapped("name")),
                )
            )
        self.write(
            {
                "state": "done",
                "result": result,
                "date_check": fields.Date.context_today(self),
            }
        )
        return True

    def action_mark_effective(self):
        """Conclude the check as Effective.

        :return: True when every record was concluded.
        :rtype: bool
        """
        return self._conclude("effective")

    def action_mark_not_effective(self):
        """Conclude the check as Not Effective.

        :return: True when every record was concluded.
        :rtype: bool
        """
        return self._conclude("not_effective")

    def action_create_followup_capa(self):
        """Raise a follow-up CAPA after an ineffective verification.

        :return: an ``ir.actions.act_window`` dictionary opening the new CAPA.
        """
        self.ensure_one()
        if self.result != "not_effective":
            raise UserError(
                _(
                    "A follow-up CAPA can only be raised from a check "
                    "concluded as Not Effective."
                )
            )
        if self.new_capa_id:
            raise UserError(
                _(
                    "Effectiveness check %(reference)s already raised a "
                    "follow-up CAPA.",
                    reference=self.name,
                )
            )
        origin = self.issue_id
        new_capa = self.env["ls.capa.issue"].create(
            {
                "title": _(
                    "Follow-up of %(reference)s", reference=origin.name
                ),
                "description": _(
                    "Raised because effectiveness check %(reference)s "
                    "concluded that the original CAPA was not effective.\n\n"
                    "Original conclusion:\n%(conclusion)s",
                    reference=self.name,
                    conclusion=self.conclusion or "",
                ),
                "source": origin.source,
                "source_reference": origin.name,
                "capa_type": origin.capa_type,
                "severity": origin.severity,
                "category_id": origin.category_id.id,
                "owner_id": origin.owner_id.id,
                "company_id": origin.company_id.id,
            }
        )
        self.new_capa_id = new_capa
        return {
            "type": "ir.actions.act_window",
            "name": _("Follow-up CAPA"),
            "res_model": "ls.capa.issue",
            "res_id": new_capa.id,
            "view_mode": "form",
        }
