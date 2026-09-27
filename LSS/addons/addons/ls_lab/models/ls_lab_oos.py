# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Out-of-specification and out-of-trend investigations.

The two-phase structure implemented here follows the organisation of the FDA
guidance for industry *Investigating Out-of-Specification (OOS) Test Results
for Pharmaceutical Production*, Level 2 revision, May 2022, docket
FDA-1998-D-0019: a laboratory phase, followed where no assignable laboratory
cause is found by an investigation extending outside the laboratory, with
retesting performed only on documented justification.

This module does not implement outlier testing. That determination is a
scientific judgement the guidance treats restrictively and automating it would
invite misuse.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class LsLabOos(models.Model):
    """An investigation raised by a non-conforming or out-of-trend result."""

    _name = "ls.lab.oos"
    _description = "Laboratory OOS / OOT Investigation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "opened_date desc, name desc"

    name = fields.Char(
        string="Investigation Reference",
        required=True,
        readonly=True,
        copy=False,
        default="New",
        tracking=True,
    )
    oos_type = fields.Selection(
        selection=[
            ("oos", "Out Of Specification"),
            ("oot", "Out Of Trend"),
        ],
        string="Type",
        default="oos",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("open", "Open"),
            ("phase1", "Phase I - Laboratory"),
            ("phase1_done", "Phase I Complete"),
            ("phase2", "Phase II - Full Investigation"),
            ("concluded", "Concluded"),
            ("closed", "Closed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="open",
        required=True,
        copy=False,
        tracking=True,
    )
    test_result_id = fields.Many2one(
        comodel_name="ls.lab.test_result",
        string="Originating Result",
        required=True,
        ondelete="restrict",
        index=True,
    )
    sample_id = fields.Many2one(related="test_result_id.sample_id", store=True,
                                index=True,)
    product_id = fields.Many2one(related="test_result_id.product_id", store=True,
                                 index=True,)
    test_method_id = fields.Many2one(related="test_result_id.test_method_id", store=True,)
    recorded_value = fields.Char(related="test_result_id.result_display", store=True,)
    acceptance_criterion = fields.Char(related="test_result_id.criterion_display", store=True,)
    investigator_id = fields.Many2one(comodel_name="res.users", required=True,
                                      default=lambda self: self.env.user,
                                      tracking=True,)
    opened_date = fields.Datetime(
        string="Opened On",
        default=fields.Datetime.now,
        required=True,
        readonly=True,
    )
    description = fields.Text()

    # ------------------------------------------------------------------
    # Phase I - laboratory investigation
    # ------------------------------------------------------------------
    chk_analyst_interview = fields.Boolean(string="Analyst Interviewed")
    chk_calculation_verified = fields.Boolean(string="Calculation Verified")
    chk_instrument_verified = fields.Boolean(string="Instrument Performance Verified")
    chk_standard_verified = fields.Boolean(string="Standards And Reagents Verified")
    chk_sample_integrity = fields.Boolean(string="Sample Integrity Verified")
    chk_method_followed = fields.Boolean(string="Method Adherence Verified")
    phase1_findings = fields.Text(string="Phase I Findings")
    phase1_conclusion = fields.Selection(
        selection=[
            ("lab_error_confirmed", "Assignable Laboratory Cause Identified"),
            ("no_lab_error", "No Assignable Laboratory Cause"),
        ],
        string="Phase I Conclusion",
        tracking=True,
    )
    phase1_completed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Phase I Completed By",
        readonly=True,
        copy=False,
    )
    phase1_date = fields.Datetime(
        string="Phase I Completion Date", readonly=True, copy=False
    )

    # ------------------------------------------------------------------
    # Phase II - investigation beyond the laboratory
    # ------------------------------------------------------------------
    phase2_findings = fields.Text(string="Phase II Findings")
    manufacturing_review = fields.Text()
    root_cause = fields.Text()
    phase2_completed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Phase II Completed By",
        readonly=True,
        copy=False,
    )
    phase2_date = fields.Datetime(
        string="Phase II Completion Date", readonly=True, copy=False
    )

    # ------------------------------------------------------------------
    # Additional testing authorisation
    # ------------------------------------------------------------------
    retest_authorised = fields.Boolean(readonly=True, copy=False, tracking=True)
    retest_justification = fields.Text(help="Scientific justification for retesting a portion of the original "
                                       "sample. Required before any retest result may be recorded.",)
    retest_authorised_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                              copy=False,)
    retest_authorisation_date = fields.Datetime(readonly=True, copy=False)
    resample_authorised = fields.Boolean(readonly=True, copy=False, tracking=True)
    resample_justification = fields.Text()
    resample_authorised_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                                copy=False,)
    resample_authorisation_date = fields.Datetime(readonly=True, copy=False)
    retest_result_ids = fields.One2many(
        comodel_name="ls.lab.test_result",
        inverse_name="oos_id",
        string="Related Results",
    )
    retest_result_count = fields.Integer(
        string="Related Result Count", compute="_compute_retest_result_count"
    )

    # ------------------------------------------------------------------
    # Conclusion
    # ------------------------------------------------------------------
    final_conclusion = fields.Selection(
        selection=[
            ("assignable_lab_cause", "Assignable Laboratory Cause"),
            ("assignable_manufacturing_cause", "Assignable Manufacturing Cause"),
            ("no_assignable_cause", "No Assignable Cause Identified"),
        ],
        tracking=True,
    )
    product_disposition = fields.Selection(
        selection=[
            ("reject", "Reject"),
            ("release", "Release"),
            ("quarantine_pending", "Remain In Quarantine"),
            ("further_investigation", "Further Investigation Required"),
        ],
        tracking=True,
        help="The disposition decision recorded by the quality unit. This "
             "module records the decision and its author; it does not make it.",
    )
    disposition_justification = fields.Text()
    capa_reference = fields.Char(help="Free-text reference to the corrective and preventive action "
                                 "record held in the CAPA module.",)
    qa_approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Quality Approver",
        readonly=True,
        copy=False,
        tracking=True,
    )
    closure_date = fields.Datetime(readonly=True, copy=False)
    cancel_reason = fields.Text(string="Cancellation Reason", copy=False)
    company_id = fields.Many2one(related="sample_id.company_id", store=True,
                                 index=True,)

    _name_uniq = models.Constraint(
        "UNIQUE (name)",
        "The investigation reference must be unique.",
    )

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    @api.depends("retest_result_ids")
    def _compute_retest_result_count(self):
        """Count the results linked to this investigation."""
        for investigation in self:
            investigation.retest_result_count = len(investigation.retest_result_ids)

    @api.depends("name", "product_id")
    def _compute_display_name(self):
        """Show the investigation reference with its product."""
        for investigation in self:
            product = investigation.product_id.display_name or ""
            investigation.display_name = f"{investigation.name} - {product}".strip(" -")

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("qa_approver_id", "investigator_id")
    def _check_approver_segregation(self):
        """The quality approver may not be the investigator (BRU-20)."""
        for investigation in self.filtered("qa_approver_id"):
            if investigation.qa_approver_id == investigation.investigator_id:
                raise ValidationError(
                    self.env._(
                        "User '%(user)s' conducted investigation '%(investigation)s' "
                        "and therefore cannot also approve its closure.",
                        user=investigation.qa_approver_id.display_name,
                        investigation=investigation.name,
                    )
                )

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the investigation reference from the sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.lab.oos"
                ) or "New"
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_lab_oos(self):
        """Refuse deletion of an investigation in any state."""
        raise UserError(
            self.env._(
                "Investigations cannot be deleted. Cancel the investigation with "
                "a recorded reason so that the history is preserved."
            )
        )

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def _assert_state(self, expected, action_label):
        """Raise unless every investigation is in one of the expected states."""
        expected = expected if isinstance(expected, (list, tuple, set)) else (expected,)
        wrong = self.filtered(lambda rec: rec.state not in expected)
        if wrong:
            raise UserError(
                self.env._(
                    "Action '%(action)s' is not available for investigation(s) "
                    "%(records)s in their current state.",
                    action=action_label,
                    records=", ".join(wrong.mapped("name")),
                )
            )

    def action_start_phase1(self):
        """Begin the laboratory phase of the investigation."""
        self._assert_state("open", "Start Phase I")
        return self.write({"state": "phase1"})

    def action_complete_phase1(self):
        """Close the laboratory phase, requiring findings and a conclusion."""
        self._assert_state("phase1", "Complete Phase I")
        for investigation in self:
            if not investigation.phase1_conclusion:
                raise UserError(
                    self.env._(
                        "A Phase I conclusion is required before the laboratory "
                        "phase of investigation '%(investigation)s' can be closed.",
                        investigation=investigation.name,
                    )
                )
            if not investigation.phase1_findings:
                raise UserError(
                    self.env._(
                        "Phase I findings must be recorded for investigation "
                        "'%(investigation)s'.",
                        investigation=investigation.name,
                    )
                )
        return self.write({
            "state": "phase1_done",
            "phase1_completed_by_id": self.env.user.id,
            "phase1_date": fields.Datetime.now(),
        })

    def action_start_phase2(self):
        """Extend the investigation beyond the laboratory (BRU-21)."""
        self._assert_state("phase1_done", "Start Phase II")
        for investigation in self:
            if investigation.phase1_conclusion != "no_lab_error":
                raise UserError(
                    self.env._(
                        "Phase II applies only when Phase I identified no "
                        "assignable laboratory cause. Investigation "
                        "'%(investigation)s' concluded otherwise.",
                        investigation=investigation.name,
                    )
                )
        return self.write({"state": "phase2"})

    def action_complete_phase2(self):
        """Close the full investigation, requiring findings and a root cause."""
        self._assert_state("phase2", "Complete Phase II")
        for investigation in self:
            if not investigation.phase2_findings:
                raise UserError(
                    self.env._(
                        "Phase II findings must be recorded for investigation "
                        "'%(investigation)s'.",
                        investigation=investigation.name,
                    )
                )
        return self.write({
            "state": "concluded",
            "phase2_completed_by_id": self.env.user.id,
            "phase2_date": fields.Datetime.now(),
        })

    def action_conclude(self):
        """Conclude directly after Phase I when a laboratory cause was found."""
        self._assert_state("phase1_done", "Conclude")
        for investigation in self:
            if investigation.phase1_conclusion != "lab_error_confirmed":
                raise UserError(
                    self.env._(
                        "Investigation '%(investigation)s' found no assignable "
                        "laboratory cause and must proceed to Phase II before "
                        "it can be concluded.",
                        investigation=investigation.name,
                    )
                )
        return self.write({"state": "concluded"})

    def action_authorise_retest(self):
        """Record retest authorisation with its justification (BRU-18)."""
        self._assert_state(
            ("phase1", "phase1_done", "phase2"), "Authorise Retest"
        )
        for investigation in self:
            if not investigation.retest_justification:
                raise UserError(
                    self.env._(
                        "A written scientific justification is required before a "
                        "retest can be authorised on investigation "
                        "'%(investigation)s'.",
                        investigation=investigation.name,
                    )
                )
        return self.write({
            "retest_authorised": True,
            "retest_authorised_by_id": self.env.user.id,
            "retest_authorisation_date": fields.Datetime.now(),
        })

    def action_authorise_resample(self):
        """Record resample authorisation with its justification."""
        self._assert_state(
            ("phase1", "phase1_done", "phase2"), "Authorise Resample"
        )
        for investigation in self:
            if not investigation.resample_justification:
                raise UserError(
                    self.env._(
                        "A written scientific justification is required before a "
                        "resample can be authorised on investigation "
                        "'%(investigation)s'.",
                        investigation=investigation.name,
                    )
                )
        return self.write({
            "resample_authorised": True,
            "resample_authorised_by_id": self.env.user.id,
            "resample_authorisation_date": fields.Datetime.now(),
        })

    def action_close(self):
        """Close the investigation with a conclusion and disposition (BRU-19)."""
        self._assert_state("concluded", "Close")
        for investigation in self:
            if not investigation.final_conclusion:
                raise UserError(
                    self.env._(
                        "A final conclusion is required before investigation "
                        "'%(investigation)s' can be closed.",
                        investigation=investigation.name,
                    )
                )
            if not investigation.product_disposition:
                raise UserError(
                    self.env._(
                        "A product disposition is required before investigation "
                        "'%(investigation)s' can be closed.",
                        investigation=investigation.name,
                    )
                )
            if investigation.investigator_id == self.env.user:
                raise UserError(
                    self.env._(
                        "You conducted investigation '%(investigation)s' and "
                        "cannot also approve its closure. A different user from "
                        "the quality unit must close it.",
                        investigation=investigation.name,
                    )
                )
        return self.write({
            "state": "closed",
            "qa_approver_id": self.env.user.id,
            "closure_date": fields.Datetime.now(),
        })

    def action_cancel(self):
        """Cancel the investigation, requiring a recorded reason."""
        self._assert_state(
            ("open", "phase1", "phase1_done", "phase2", "concluded"), "Cancel"
        )
        for investigation in self:
            if not investigation.cancel_reason:
                raise UserError(
                    self.env._(
                        "A cancellation reason must be recorded before "
                        "investigation '%(investigation)s' can be cancelled.",
                        investigation=investigation.name,
                    )
                )
        return self.write({"state": "cancelled"})

    def action_view_results(self):
        """Open the results linked to this investigation."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Related Results"),
            "res_model": "ls.lab.test_result",
            "view_mode": "list,form",
            "domain": [("oos_id", "=", self.id)],
        }
