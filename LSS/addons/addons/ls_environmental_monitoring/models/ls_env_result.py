# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Environmental monitoring result."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    BREACH_EVALUATIONS,
    EVAL_ALERT,
    EVAL_NO_LIMIT,
    EVAL_NOT_EVALUATED,
    EVALUATIONS,
    MANDATORY_EXCURSION_EVALUATIONS,
    QUALITATIVE_VALUES,
    RESULT_TYPE_QUANTITATIVE,
    SAMPLE_APPROVED,
    SAMPLE_LOCKED_STATES,
)
from .evaluation import evaluate_qualitative, evaluate_quantitative


class LsEnvResult(models.Model):
    """One measured value for one parameter on one sample.

    The thresholds applied are copied onto the result at the moment of
    evaluation. Reading a historical result therefore never depends on the
    limit record still existing or still holding the same values, which is
    what allows a past evaluation to be reconstructed exactly.
    """

    _name = "ls.env.result"
    _description = "Environmental Monitoring Result"
    _inherit = ["mail.thread"]
    _order = "sample_id, parameter_id"

    sample_id = fields.Many2one(comodel_name="ls.env.sample", required=True,
                                index=True,
                                ondelete="cascade",)
    sample_state = fields.Selection(
        related="sample_id.state", string="Sample Status", store=True, index=True
    )
    sampling_point_id = fields.Many2one(comodel_name="ls.env.sampling_point", related="sample_id.sampling_point_id",
                                        store=True,
                                        index=True,)
    area_id = fields.Many2one(comodel_name="ls.env.area", related="sample_id.area_id",
                              store=True,
                              index=True,)
    occupancy_state = fields.Selection(related="sample_id.occupancy_state", store=True)
    collection_datetime = fields.Datetime(
        related="sample_id.collection_datetime",
        string="Collected On",
        store=True,
        index=True,
    )
    parameter_id = fields.Many2one(comodel_name="ls.env.parameter", required=True,
                                   index=True,
                                   ondelete="restrict",)
    result_type = fields.Selection(related="parameter_id.result_type", store=True)
    method_id = fields.Many2one(comodel_name="ls.env.method", ondelete="restrict",)
    value_numeric = fields.Float(
        string="Measured Value",
        digits=(16, 4),
        tracking=True,
        help="Recorded value for a quantitative parameter.",
    )
    value_set = fields.Boolean(
        string="Value Recorded",
        default=False,
        help="Distinguishes a recorded value of zero from no value at all.",
    )
    value_qualitative = fields.Selection(
        selection=QUALITATIVE_VALUES,
        string="Outcome",
        tracking=True,
        help="Recorded outcome for a qualitative parameter.",
    )
    uom_label = fields.Char(
        string="Unit", related="parameter_id.uom_label", store=True
    )
    microbial_identification = fields.Char(
        string="Organism Identified",
        tracking=True,
        help="Identification of recovered organisms, where identification was "
        "performed.",
    )
    # -- Snapshot of the criteria applied, taken at evaluation time ---------
    limit_id = fields.Many2one(
        comodel_name="ls.env.limit",
        string="Limit Applied",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )
    applied_direction = fields.Char(
        string="Bound Direction Applied", readonly=True, copy=False
    )
    applied_alert_value = fields.Float(
        string="Alert Limit Applied", digits=(16, 4), readonly=True, copy=False
    )
    applied_action_value = fields.Float(
        string="Action Limit Applied", digits=(16, 4), readonly=True, copy=False
    )
    applied_spec_value = fields.Float(
        string="Specification Limit Applied",
        digits=(16, 4),
        readonly=True,
        copy=False,
    )
    applied_alert_set = fields.Boolean(readonly=True, copy=False)
    applied_action_set = fields.Boolean(readonly=True, copy=False)
    applied_spec_set = fields.Boolean(readonly=True, copy=False)
    evaluation = fields.Selection(
        selection=EVALUATIONS,
        string="Outcome",
        default=EVAL_NOT_EVALUATED,
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
    )
    evaluation_datetime = fields.Datetime(
        string="Evaluated On", readonly=True, copy=False
    )
    is_breach = fields.Boolean(
        string="Threshold Breached",
        compute="_compute_is_breach",
        store=True,
        index=True,
    )
    # -- Amendment ---------------------------------------------------------
    is_amended = fields.Boolean(string="Amended", readonly=True, copy=False)
    original_value_numeric = fields.Float(
        string="Original Value", digits=(16, 4), readonly=True, copy=False
    )
    original_value_qualitative = fields.Selection(
        selection=QUALITATIVE_VALUES,
        string="Original Outcome",
        readonly=True,
        copy=False,
    )
    amendment_reason = fields.Text(readonly=True, copy=False)
    amended_by_id = fields.Many2one(comodel_name="res.users", readonly=True, copy=False)
    amendment_datetime = fields.Datetime(
        string="Amended On", readonly=True, copy=False
    )
    excursion_id = fields.Many2one(comodel_name="ls.env.excursion", readonly=True,
                                   copy=False,
                                   ondelete="set null",)
    notes = fields.Text()
    company_id = fields.Many2one(comodel_name="res.company", related="sample_id.company_id",
                                 store=True,
                                 index=True,)

    _sample_parameter_unique = models.Constraint(
        "UNIQUE(sample_id, parameter_id)",
        "A sample may record only one result per parameter.",
    )

    @api.depends("evaluation")
    def _compute_is_breach(self):
        """Flag results whose outcome breached a configured threshold."""
        for record in self:
            record.is_breach = record.evaluation in BREACH_EVALUATIONS

    @api.constrains("method_id", "parameter_id")
    def _check_method_parameter(self):
        """Reject a method that measures a different parameter."""
        for record in self:
            method = record.method_id
            if method and method.parameter_id != record.parameter_id:
                raise ValidationError(
                    self.env._(
                        "Method '%(method)s' does not measure parameter '%(param)s'.",
                        method=method.name,
                        param=record.parameter_id.name,
                    )
                )

    @api.constrains("value_numeric", "value_set", "parameter_id")
    def _check_value_not_negative(self):
        """Reject a negative count for a parameter that counts occurrences.

        Counts of colonies or particles cannot be negative. Parameters such as
        differential pressure legitimately take negative values and are not
        constrained here.
        """
        counting_types = (
            "viable_air_active",
            "viable_air_passive",
            "viable_surface",
            "viable_personnel",
            "nonviable_particle",
        )
        for record in self:
            if (
                record.value_set
                and record.parameter_id.parameter_type in counting_types
                and record.value_numeric < 0
            ):
                raise ValidationError(
                    self.env._(
                        "A count for parameter '%(param)s' cannot be negative.",
                        param=record.parameter_id.name,
                    )
                )

    def has_value(self):
        """Return whether a value has been recorded on this result.

        :rtype: bool
        """
        self.ensure_one()
        if self.result_type == RESULT_TYPE_QUANTITATIVE:
            return self.value_set
        return bool(self.value_qualitative)

    def _snapshot_limit(self, limit):
        """Copy the thresholds of ``limit`` onto the result."""
        self.ensure_one()
        if not limit:
            self.write(
                {
                    "limit_id": False,
                    "applied_direction": False,
                    "applied_alert_value": 0.0,
                    "applied_action_value": 0.0,
                    "applied_spec_value": 0.0,
                    "applied_alert_set": False,
                    "applied_action_set": False,
                    "applied_spec_set": False,
                }
            )
            return
        self.write(
            {
                "limit_id": limit.id,
                "applied_direction": limit.direction,
                "applied_alert_value": limit.alert_value,
                "applied_action_value": limit.action_value,
                "applied_spec_value": limit.spec_value,
                "applied_alert_set": limit.alert_set,
                "applied_action_set": limit.action_set,
                "applied_spec_set": limit.spec_set,
            }
        )

    def _find_applicable_limit(self):
        """Return the approved limit that applies to this result.

        Both bound directions are considered and the one that produces the more
        severe outcome is retained, so that a parameter constrained above and
        below is evaluated against whichever bound it actually breached.
        """
        self.ensure_one()
        point = self.sampling_point_id
        candidates = self.env["ls.env.limit"]
        for direction in ("upper", "lower"):
            candidates |= point.find_approved_limit(
                self.parameter_id, self.occupancy_state, direction
            )
        return candidates

    def action_evaluate(self):
        """Evaluate each result against the limits currently approved.

        Re-evaluating an already approved result is refused, because the
        outcome recorded at approval is the released record.
        """
        for record in self:
            if record.sample_state == SAMPLE_APPROVED:
                raise UserError(
                    self.env._(
                        "The result for parameter '%(param)s' belongs to an approved "
                        "sample and cannot be re-evaluated.",
                        param=record.parameter_id.name,
                    )
                )
            if not record.has_value():
                record.evaluation = EVAL_NOT_EVALUATED
                continue
            if record.result_type != RESULT_TYPE_QUANTITATIVE:
                record._snapshot_limit(self.env["ls.env.limit"])
                record.write(
                    {
                        "evaluation": evaluate_qualitative(record.value_qualitative),
                        "evaluation_datetime": fields.Datetime.now(),
                    }
                )
                continue
            limits = record._find_applicable_limit()
            best_limit = self.env["ls.env.limit"]
            best_outcome = None
            for limit in limits:
                thresholds = limit.get_thresholds()
                outcome = evaluate_quantitative(
                    record.value_numeric,
                    limit.direction,
                    alert=thresholds["alert"],
                    action=thresholds["action"],
                    spec=thresholds["spec"],
                )
                if best_outcome is None or _is_more_severe(outcome, best_outcome):
                    best_outcome = outcome
                    best_limit = limit
            if best_outcome is None:
                record._snapshot_limit(self.env["ls.env.limit"])
                record.write(
                    {
                        "evaluation": EVAL_NO_LIMIT,
                        "evaluation_datetime": fields.Datetime.now(),
                    }
                )
                continue
            record._snapshot_limit(best_limit)
            record.write(
                {
                    "evaluation": best_outcome,
                    "evaluation_datetime": fields.Datetime.now(),
                }
            )
        return True

    def _requires_excursion(self):
        """Return whether this result must open a formal excursion.

        Action and specification exceedances always require one. An alert
        exceedance requires one only when the applied limit is configured to
        escalate.
        """
        self.ensure_one()
        if self.evaluation in MANDATORY_EXCURSION_EVALUATIONS:
            return True
        if self.evaluation == EVAL_ALERT:
            return bool(self.limit_id and self.limit_id.escalate_alert)
        return False

    def _raise_excursions_if_required(self):
        """Create excursion records for the breaches on these results.

        All breaching results of one sample are grouped into a single
        excursion, because they describe one event at one location and time.
        """
        excursion_model = self.env["ls.env.excursion"]
        by_sample = {}
        for record in self:
            if record.excursion_id or not record._requires_excursion():
                continue
            existing = by_sample.get(record.sample_id, self.browse())
            by_sample[record.sample_id] = existing | record
        for sample, results in by_sample.items():
            excursion = excursion_model.create(
                excursion_model._prepare_from_results(sample, results)
            )
            results.write({"excursion_id": excursion.id})
            sample.message_post(
                body=self.env._(
                    "Excursion %(reference)s opened for this sample.",
                    reference=excursion.name,
                )
            )
        return True

    def action_amend(self):
        """Open the amendment wizard for a result on an approved sample."""
        self.ensure_one()
        if self.sample_state != SAMPLE_APPROVED:
            raise UserError(
                self.env._(
                    "Only a result on an approved sample is amended through this "
                    "route. Correct the value directly while the sample is still "
                    "under analysis."
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Amend Result"),
            "res_model": "ls.env.result.amend.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_result_id": self.id},
        }

    def amend_value(self, reason, value_numeric=None, value_qualitative=None):
        """Amend an approved result, retaining the original value.

        The original value is preserved on the record, the reason is mandatory
        and the amendment is written to the message log, so the correction is
        visible without displacing what was originally reported.

        :param str reason: justification for the amendment
        :param value_numeric: replacement numeric value, when applicable
        :param value_qualitative: replacement outcome, when applicable
        :raises UserError: when the reason is missing or the result has
            already been amended
        """
        self.ensure_one()
        if not reason:
            raise UserError(
                self.env._("A reason is required to amend a result.")
            )
        if self.is_amended:
            raise UserError(
                self.env._(
                    "This result has already been amended. Record any further "
                    "correction as a new investigation."
                )
            )
        values = {
            "is_amended": True,
            "amendment_reason": reason,
            "amended_by_id": self.env.user.id,
            "amendment_datetime": fields.Datetime.now(),
            "original_value_numeric": self.value_numeric,
            "original_value_qualitative": self.value_qualitative,
        }
        if value_numeric is not None:
            values["value_numeric"] = value_numeric
            values["value_set"] = True
        if value_qualitative is not None:
            values["value_qualitative"] = value_qualitative
        self.with_context(ls_env_amendment=True).write(values)
        self.message_post(
            body=self.env._(
                "Result amended. Reason: %(reason)s", reason=reason
            )
        )
        return True

    def write(self, vals):
        """Freeze the reported value once the parent sample is approved.

        The amendment route sets a context flag to pass this guard, so a
        correction is always accompanied by a reason and an author.
        """
        if not self.env.context.get("ls_env_amendment"):
            frozen = {
                "value_numeric",
                "value_set",
                "value_qualitative",
                "parameter_id",
                "method_id",
                "microbial_identification",
            }
            if frozen.intersection(vals):
                for record in self:
                    if record.sample_state in SAMPLE_LOCKED_STATES:
                        raise UserError(
                            self.env._(
                                "The result for parameter '%(param)s' belongs to a "
                                "closed sample and cannot be modified. Use the "
                                "amendment route to record a correction.",
                                param=record.parameter_id.name,
                            )
                        )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_env_result(self):
        """Prevent deletion of a result once its sample has been collected."""
        for record in self:
            if record.sample_state not in ("draft", "scheduled"):
                raise UserError(
                    self.env._(
                        "A result can only be removed while its sample is still "
                        "awaiting collection."
                    )
                )

    @api.depends("parameter_id", "sample_id")
    def _compute_display_name(self):
        """Show the sample reference and the parameter measured."""
        for record in self:
            record.display_name = "%s / %s" % (
                record.sample_id.name or "",
                record.parameter_id.code or "",
            )


def _is_more_severe(candidate, current):
    """Return whether ``candidate`` outranks ``current`` in severity.

    Defined at module level so that it remains importable by tests without
    instantiating a model.
    """
    from .constants import EVALUATION_SEVERITY

    return EVALUATION_SEVERITY[candidate] > EVALUATION_SEVERITY[current]
