# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Impact assessment of a change on one area of the quality system."""

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class LsChangeControlAssessment(models.Model):
    """Evaluation of the impact of a change on a single impact area."""

    _name = "ls.change_control.assessment"
    _description = "Change Control Impact Assessment"
    _inherit = ["mail.thread"]
    _order = "request_id, impact_area_id"

    request_id = fields.Many2one(
        comodel_name="ls.change_control.request",
        string="Change Request",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", related="request_id.company_id",
                                 store=True,
                                 index=True,)
    request_state = fields.Selection(
        related="request_id.state",
        string="Request Status",
        store=True,
        index=True,
    )
    impact_area_id = fields.Many2one(comodel_name="ls.change_control.impact_area", required=True,
                                     ondelete="restrict",
                                     index=True,)
    assessor_id = fields.Many2one(comodel_name="res.users", tracking=True,
                                  domain="[('share', '=', False)]",
                                  help="Subject matter expert responsible for assessing this area.",
                                  )
    impact = fields.Selection(
        selection=[
            ("none", "No Impact"),
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Impact Level",
        default="none",
        required=True,
        tracking=True,
    )
    assessment = fields.Text(help="Rationale supporting the declared impact level.",)
    actions_required = fields.Text(help="Actions that must be planned before the change becomes "
                                   "effective on this area.",)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("completed", "Completed"),
        ],
        string="Status",
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    date_completed = fields.Datetime(
        string="Completion Date",
        readonly=True,
        copy=False,
    )
    completed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                      copy=False,)

    _area_uniq_per_request = models.Constraint(
        "UNIQUE(request_id, impact_area_id)",
        "An impact area can only be assessed once per change request.",
    )

    @api.depends("impact_area_id", "request_id")
    def _compute_display_name(self):
        """Show the request reference and the impact area."""
        for assessment in self:
            assessment.display_name = "%s / %s" % (
                assessment.request_id.name or "",
                assessment.impact_area_id.name or "",
            )

    def write(self, vals):
        """Freeze a completed assessment except in superuser mode."""
        if not self.env.su:
            protected = {"state", "date_completed", "completed_by_id"}
            forbidden = sorted(set(vals) & protected)
            if forbidden:
                raise AccessError(
                    _(
                        "The following fields are maintained by the "
                        "assessment workflow and cannot be written "
                        "directly: %(fields)s.",
                        fields=", ".join(forbidden),
                    )
                )
            completed = self.filtered(lambda a: a.state == "completed")
            business_fields = {
                "impact",
                "assessment",
                "actions_required",
                "assessor_id",
                "impact_area_id",
            }
            if completed and set(vals) & business_fields:
                raise UserError(
                    _(
                        "Assessment %(name)s is completed and can no longer "
                        "be modified.",
                        name=completed[0].display_name,
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_change_control_assessment(self):
        """Forbid the deletion of a completed assessment."""
        completed = self.filtered(lambda a: a.state == "completed")
        if completed:
            raise UserError(
                _(
                    "Assessment %(name)s is completed and cannot be deleted.",
                    name=completed[0].display_name,
                )
            )

    def action_complete(self):
        """Mark the assessment as completed.

        The assessor assigned to the assessment or a change control manager
        may complete it. A rationale is mandatory as soon as an impact is
        declared.
        """
        for assessment in self:
            if assessment.state == "completed":
                raise UserError(
                    _("Assessment %(name)s is already completed.",
                      name=assessment.display_name)
                )
            if assessment.request_id.state != "impact_assessment":
                raise UserError(
                    _(
                        "Assessments can only be completed while request "
                        "%(name)s is in the Impact Assessment state.",
                        name=assessment.request_id.name,
                    )
                )
            is_manager = self.env.user.has_group(
                "ls_change_control.group_ls_change_control_manager"
            )
            if assessment.assessor_id != self.env.user and not is_manager:
                raise AccessError(
                    _(
                        "Only the assigned assessor or a Change Control "
                        "Manager may complete assessment %(name)s.",
                        name=assessment.display_name,
                    )
                )
            if not assessment.assessment or not assessment.assessment.strip():
                raise UserError(
                    _(
                        "A written assessment is required before completing "
                        "the assessment of area '%(area)s'.",
                        area=assessment.impact_area_id.name,
                    )
                )
            if assessment.impact != "none" and not assessment.actions_required:
                raise UserError(
                    _(
                        "An impact was declared on area '%(area)s'. The "
                        "required actions must be described.",
                        area=assessment.impact_area_id.name,
                    )
                )
        self.sudo().write(
            {
                "state": "completed",
                "date_completed": fields.Datetime.now(),
                "completed_by_id": self.env.user.id,
            }
        )
        for assessment in self:
            # The assessor may not hold write access on the request, which
            # Odoo requires to post on its chatter; the note is posted with
            # superuser rights and keeps the assessor as its author.
            assessment.request_id.sudo().message_post(
                body=_(
                    "Impact assessment completed for area '%(area)s' with "
                    "impact level '%(impact)s'.",
                    area=assessment.impact_area_id.name,
                    impact=dict(
                        self._fields["impact"].selection
                    ).get(assessment.impact, assessment.impact),
                ),
                subtype_xmlid="mail.mt_note",
            )
        return True
