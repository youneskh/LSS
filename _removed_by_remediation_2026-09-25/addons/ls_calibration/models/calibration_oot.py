# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Out-of-tolerance (OOT) events.

When an instrument is found outside its acceptance limits at calibration, all
measurements taken since the previous successful calibration are of unknown
validity. This model records that finding, the assessment of its impact and
the disposition decided by the quality function.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsCalibrationOot(models.Model):
    """An as-found out-of-tolerance finding and its impact assessment."""

    _name = "ls.calibration.oot"
    _description = "Calibration Out-of-Tolerance Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "detection_date desc, name desc, id desc"

    name = fields.Char(
        string="OOT Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: constants.NEW_SEQUENCE_PLACEHOLDER,
        index=True,
    )
    record_id = fields.Many2one(
        comodel_name="ls.calibration.record",
        string="Calibration Record",
        required=True,
        ondelete="restrict",
        tracking=True,
        index=True,
    )
    instrument_id = fields.Many2one(comodel_name="ls.calibration.instrument", related="record_id.instrument_id",
                                    store=True,
                                    readonly=True,
                                    index=True,)
    criticality = fields.Selection(
        related="instrument_id.criticality",
        string="Instrument Criticality",
        store=True,
        readonly=True,
    )
    detection_date = fields.Date(
        string="Detected On",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Affected period
    # ------------------------------------------------------------------
    affected_period_start = fields.Date(
        string="Affected From",
        tracking=True,
        help="Date of the last calibration at which the instrument was found "
        "within tolerance. Empty when the instrument has no previous approved "
        "calibration, in which case the whole period of use is affected.",
    )
    affected_period_end = fields.Date(
        string="Affected To",
        required=True,
        tracking=True,
        help="Date at which the out-of-tolerance condition was detected.",
    )
    description = fields.Text(string="Description of the Finding", required=True)

    # ------------------------------------------------------------------
    # Assessment
    # ------------------------------------------------------------------
    impact_assessment = fields.Text(help="Assessment of the consequence of the out-of-tolerance condition "
                                    "on product, process and data generated during the affected period.",)
    product_impact = fields.Selection(selection=constants.OOT_PRODUCT_IMPACT_SELECTION, tracking=True,)
    affected_batches = fields.Text(
        string="Affected Batches / Data Sets",
        help="Free-text identification of the batches, lots or data sets "
        "generated during the affected period. Recorded as text; this module "
        "declares no dependency on a manufacturing application.",
    )
    disposition = fields.Selection(selection=constants.OOT_DISPOSITION_SELECTION, tracking=True,)
    disposition_justification = fields.Text()
    capa_reference = fields.Char(tracking=True,
                                 help="Reference of the corrective and preventive action raised for "
                                 "this event, recorded as text. This module declares no dependency on "
                                 "a CAPA application; a separate bridge module may replace this field "
                                 "with a relational link.",)

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=constants.OOT_STATE_SELECTION,
        string="Status",
        required=True,
        default=constants.OOT_STATE_OPEN,
        tracking=True,
        copy=False,
        index=True,
    )
    assessed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assessed By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    assessed_date = fields.Datetime(
        string="Assessed On", readonly=True, copy=False, tracking=True
    )
    closed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Closed By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    closed_date = fields.Datetime(
        string="Closed On", readonly=True, copy=False, tracking=True
    )
    responsible_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 index=True,
                                 default=lambda self: self.env.company,)

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The out-of-tolerance reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    @api.depends("name", "instrument_id.code")
    def _compute_display_name(self) -> None:
        """Show the OOT reference together with the instrument ID."""
        for event in self:
            event.display_name = f"{event.name} - {event.instrument_id.code}"

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("affected_period_start", "affected_period_end")
    def _check_affected_period(self) -> None:
        """The affected period must not end before it starts."""
        for event in self:
            if (
                event.affected_period_start
                and event.affected_period_end < event.affected_period_start
            ):
                raise ValidationError(
                    self.env._(
                        "Event %(event)s: the affected period cannot end "
                        "before it starts.",
                        event=event.name,
                    )
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _assert_transition(self, target_state: str) -> None:
        """Raise when the requested OOT transition is not permitted."""
        for event in self:
            allowed = constants.OOT_STATE_TRANSITIONS.get(event.state, ())
            if target_state not in allowed:
                raise UserError(
                    self.env._(
                        "Out-of-tolerance event %(event)s cannot move from "
                        "'%(current)s' to '%(target)s'.",
                        event=event.name,
                        current=event.state,
                        target=target_state,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list: list) -> "LsCalibrationOot":
        """Draw the OOT reference from the sequence and quarantine the asset.

        Raising an out-of-tolerance event on an in-service instrument places
        that instrument in quarantine, because its measurements can no longer
        be relied upon until the assessment concludes.
        """
        for vals in vals_list:
            if vals.get("name", constants.NEW_SEQUENCE_PLACEHOLDER) in (
                False,
                constants.NEW_SEQUENCE_PLACEHOLDER,
            ):
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = self.env["ir.sequence"].with_company(
                    company_id
                ).next_by_code(
                    constants.SEQUENCE_CODE_OOT
                ) or constants.NEW_SEQUENCE_PLACEHOLDER
        events = super().create(vals_list)
        events._quarantine_affected_instruments()
        return events

    def _quarantine_affected_instruments(self) -> None:
        """Place in-service instruments carrying a new OOT into quarantine."""
        for event in self:
            instrument = event.instrument_id
            if instrument.state != constants.INSTRUMENT_STATE_IN_SERVICE:
                continue
            instrument.write(
                {
                    "state": constants.INSTRUMENT_STATE_QUARANTINED,
                    "quarantine_reason": self.env._(
                        "Automatic quarantine on out-of-tolerance event "
                        "%(event)s.",
                        event=event.name,
                    ),
                }
            )
            instrument.message_post(
                body=self.env._(
                    "Placed in quarantine following out-of-tolerance event "
                    "%(event)s.",
                    event=event.name,
                )
            )

    def unlink(self) -> bool:
        """Permit deletion only while the event is still open."""
        for event in self:
            if event.state != constants.OOT_STATE_OPEN:
                raise UserError(
                    self.env._(
                        "Out-of-tolerance event %(event)s is in state "
                        "'%(state)s' and cannot be deleted.",
                        event=event.name,
                        state=event.state,
                    )
                )
        return super().unlink()

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_start_assessment(self) -> bool:
        """Move the event to ``under_assessment``."""
        self._assert_transition(constants.OOT_STATE_UNDER_ASSESSMENT)
        self.write({"state": constants.OOT_STATE_UNDER_ASSESSMENT})
        return True

    def action_complete_assessment(self) -> bool:
        """Record the impact assessment and the disposition."""
        self._assert_transition(constants.OOT_STATE_ASSESSED)
        for event in self:
            if not event.impact_assessment:
                raise UserError(
                    self.env._(
                        "Event %(event)s requires a documented impact "
                        "assessment.",
                        event=event.name,
                    )
                )
            if not event.product_impact:
                raise UserError(
                    self.env._(
                        "Event %(event)s requires a product impact "
                        "classification.",
                        event=event.name,
                    )
                )
            if not event.disposition:
                raise UserError(
                    self.env._(
                        "Event %(event)s requires a disposition.",
                        event=event.name,
                    )
                )
            if not event.disposition_justification:
                raise UserError(
                    self.env._(
                        "Event %(event)s requires a justification for the "
                        "disposition.",
                        event=event.name,
                    )
                )
        self.write(
            {
                "state": constants.OOT_STATE_ASSESSED,
                "assessed_by_user_id": self.env.user.id,
                "assessed_date": fields.Datetime.now(),
            }
        )
        return True

    def action_close(self) -> bool:
        """Close the event.

        Closure is refused while the assessed product impact is other than
        "no impact" and no corrective action reference has been recorded, so
        that a confirmed impact cannot be closed silently.
        """
        self._assert_transition(constants.OOT_STATE_CLOSED)
        for event in self:
            needs_capa = event.product_impact in (
                constants.OOT_PRODUCT_IMPACT_POTENTIAL,
                constants.OOT_PRODUCT_IMPACT_CONFIRMED,
            )
            if needs_capa and not event.capa_reference:
                raise UserError(
                    self.env._(
                        "Event %(event)s reports a product impact and "
                        "requires a corrective action reference before it can "
                        "be closed.",
                        event=event.name,
                    )
                )
            if event.assessed_by_user_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Event %(event)s was assessed by you and must be "
                        "closed by a different user.",
                        event=event.name,
                    )
                )
        self.write(
            {
                "state": constants.OOT_STATE_CLOSED,
                "closed_by_user_id": self.env.user.id,
                "closed_date": fields.Datetime.now(),
            }
        )
        return True

    def action_open_record(self) -> dict:
        """Open the calibration record that raised this event."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Calibration Record"),
            "res_model": "ls.calibration.record",
            "res_id": self.record_id.id,
            "view_mode": "form",
            "target": "current",
        }
