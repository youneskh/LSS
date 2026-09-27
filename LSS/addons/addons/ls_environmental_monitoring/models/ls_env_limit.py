# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Alert, action and specification limits."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from .constants import (
    DIRECTION_LOWER,
    DIRECTION_UPPER,
    LIMIT_DIRECTIONS,
    LIMIT_OCCUPANCY_STATES,
    LIMIT_STATE_APPROVED,
    LIMIT_STATE_DRAFT,
    LIMIT_STATE_SUPERSEDED,
    LIMIT_STATES,
    OCCUPANCY_ANY,
)


class LsEnvLimit(models.Model):
    """Acceptance criteria for one parameter at one sampling point.

    The module ships no limit values. Every threshold is entered and approved
    by the implementing organisation, which owns the justification for the
    value it sets.

    Limits are versioned rather than edited in place. Approving a new limit
    supersedes the one it replaces instead of overwriting it, so that a result
    evaluated in the past can still be traced to the criteria that were in
    force at the time. Results additionally store their own copy of the
    thresholds applied, so historical evaluations remain readable even if a
    limit record is later archived.
    """

    _name = "ls.env.limit"
    _description = "Environmental Monitoring Limit"
    _inherit = ["mail.thread"]
    _order = "sampling_point_id, parameter_id, direction, version desc"

    name = fields.Char(
        string="Reference",
        compute="_compute_name",
        store=True,
    )
    sampling_point_id = fields.Many2one(comodel_name="ls.env.sampling_point", required=True,
                                        index=True,
                                        tracking=True,
                                        ondelete="cascade",)
    area_id = fields.Many2one(comodel_name="ls.env.area", related="sampling_point_id.area_id",
                              store=True,
                              index=True,)
    parameter_id = fields.Many2one(comodel_name="ls.env.parameter", required=True,
                                   index=True,
                                   tracking=True,
                                   ondelete="restrict",)
    occupancy_state = fields.Selection(selection=LIMIT_OCCUPANCY_STATES, required=True,
                                       default=OCCUPANCY_ANY,
                                       tracking=True,
                                       help="Occupancy state in which this limit applies. A limit set for a "
                                       "specific state takes precedence over one set for any state.",)
    direction = fields.Selection(
        selection=LIMIT_DIRECTIONS,
        string="Bound Direction",
        required=True,
        default=DIRECTION_UPPER,
        tracking=True,
        help="Whether a breach occurs when the measured value rises above or "
        "falls below the thresholds. A parameter constrained on both sides "
        "requires one limit record per direction.",
    )
    alert_value = fields.Float(
        string="Alert Limit",
        digits=(16, 4),
        tracking=True,
        help="Threshold at which a drift is signalled for review. Leave the "
        "field empty when no alert threshold is defined.",
    )
    action_value = fields.Float(
        string="Action Limit",
        digits=(16, 4),
        tracking=True,
        help="Threshold at which documented action is required. Leave the "
        "field empty when no action threshold is defined.",
    )
    spec_value = fields.Float(
        string="Specification Limit",
        digits=(16, 4),
        tracking=True,
        help="Threshold that constitutes a specification breach. Leave the "
        "field empty when no specification threshold is defined.",
    )
    alert_set = fields.Boolean(
        string="Alert Limit Defined",
        default=False,
        help="Enable to apply the alert threshold. When disabled the "
        "threshold is ignored during evaluation.",
    )
    action_set = fields.Boolean(string="Action Limit Defined", default=False)
    spec_set = fields.Boolean(string="Specification Limit Defined", default=False)
    escalate_alert = fields.Boolean(
        string="Raise Excursion on Alert",
        default=False,
        help="When enabled, exceeding the alert threshold opens a formal "
        "excursion record. Action and specification exceedances always open "
        "an excursion regardless of this setting.",
    )
    justification = fields.Text(tracking=True,
                                help="Basis on which these thresholds were set, for example the "
                                "outcome of a risk assessment or an analysis of historical data.",)
    source_reference = fields.Char(
        string="Controlling Document",
        tracking=True,
        help="Identifier of the internal document that defines these values.",
    )
    version = fields.Integer(default=1,
                             readonly=True,
                             copy=False,
                             tracking=True,)
    state = fields.Selection(
        selection=LIMIT_STATES,
        string="Status",
        default=LIMIT_STATE_DRAFT,
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    effective_date = fields.Date(
        string="Effective From",
        readonly=True,
        copy=False,
        tracking=True,
    )
    superseded_date = fields.Date(
        string="Superseded On",
        readonly=True,
        copy=False,
    )
    approved_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                     copy=False,
                                     tracking=True,)
    superseded_by_id = fields.Many2one(comodel_name="ls.env.limit", readonly=True,
                                       copy=False,
                                       ondelete="set null",)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)

    _alert_value_positive = models.Constraint(
        "CHECK(alert_value >= 0)",
        "The alert limit must not be negative.",
    )
    _action_value_positive = models.Constraint(
        "CHECK(action_value >= 0)",
        "The action limit must not be negative.",
    )
    _spec_value_positive = models.Constraint(
        "CHECK(spec_value >= 0)",
        "The specification limit must not be negative.",
    )
    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The version number must be greater than zero.",
    )

    @api.depends(
        "sampling_point_id.code",
        "parameter_id.code",
        "direction",
        "version",
    )
    def _compute_name(self):
        """Build a stable human-readable reference for the limit."""
        for record in self:
            record.name = "%s / %s / %s / v%s" % (
                record.sampling_point_id.code or "",
                record.parameter_id.code or "",
                record.direction or "",
                record.version or 1,
            )

    @api.constrains("alert_set", "action_set", "spec_set")
    def _check_at_least_one_threshold(self):
        """Reject a limit that defines no threshold at all."""
        for record in self:
            if not (record.alert_set or record.action_set or record.spec_set):
                raise ValidationError(
                    self.env._(
                        "Limit '%(limit)s' must define at least one threshold.",
                        limit=record.name or "",
                    )
                )

    @api.constrains(
        "alert_set",
        "action_set",
        "spec_set",
        "alert_value",
        "action_value",
        "spec_value",
        "direction",
    )
    def _check_threshold_ordering(self):
        """Reject thresholds ordered inconsistently with the bound direction.

        For an upper bound the alert threshold must not sit above the action
        threshold, and the action threshold must not sit above the
        specification threshold. A configuration that violates this ordering
        would make the less severe threshold unreachable and would silently
        misclassify results.
        """
        for record in self:
            defined = []
            if record.alert_set:
                defined.append((self.env._("alert"), record.alert_value))
            if record.action_set:
                defined.append((self.env._("action"), record.action_value))
            if record.spec_set:
                defined.append((self.env._("specification"), record.spec_value))
            for index in range(len(defined) - 1):
                lower_label, lower_value = defined[index]
                upper_label, upper_value = defined[index + 1]
                if record.direction == DIRECTION_UPPER and lower_value > upper_value:
                    raise ValidationError(
                        self.env._(
                            "For an upper bound, the %(first)s limit must not be "
                            "greater than the %(second)s limit.",
                            first=lower_label,
                            second=upper_label,
                        )
                    )
                if record.direction == DIRECTION_LOWER and lower_value < upper_value:
                    raise ValidationError(
                        self.env._(
                            "For a lower bound, the %(first)s limit must not be "
                            "less than the %(second)s limit.",
                            first=lower_label,
                            second=upper_label,
                        )
                    )

    @api.constrains(
        "state",
        "sampling_point_id",
        "parameter_id",
        "occupancy_state",
        "direction",
    )
    def _check_single_approved_limit(self):
        """Reject a second approved limit for the same combination.

        Two approved limits covering the same sampling point, parameter,
        occupancy state and direction would make evaluation ambiguous.
        """
        for record in self:
            if record.state != LIMIT_STATE_APPROVED:
                continue
            duplicate = self.search_count(
                [
                    ("id", "!=", record.id),
                    ("sampling_point_id", "=", record.sampling_point_id.id),
                    ("parameter_id", "=", record.parameter_id.id),
                    ("occupancy_state", "=", record.occupancy_state),
                    ("direction", "=", record.direction),
                    ("state", "=", LIMIT_STATE_APPROVED),
                ]
            )
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "An approved limit already exists for this sampling point, "
                        "parameter, occupancy state and direction. Supersede it "
                        "before approving a replacement."
                    )
                )

    @api.constrains("sampling_point_id", "parameter_id", "company_id")
    def _check_company_consistency(self):
        """Reject references to records of a different company."""
        for record in self:
            if record.sampling_point_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "The sampling point must belong to the same company as the "
                        "limit."
                    )
                )
            if record.parameter_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "The parameter must belong to the same company as the limit."
                    )
                )

    def action_approve(self):
        """Approve the limit and supersede the limit it replaces.

        The approver must not be the user who created the record, so that the
        value applied during evaluation has been confirmed by a second person.
        """
        for record in self:
            if record.state != LIMIT_STATE_DRAFT:
                raise UserError(
                    self.env._("Only a draft limit can be approved.")
                )
            if not record.justification:
                raise UserError(
                    self.env._(
                        "A justification is required before a limit can be approved."
                    )
                )
            if record.create_uid == self.env.user:
                raise UserError(
                    self.env._(
                        "A limit must be approved by a user other than the one who "
                        "created it."
                    )
                )
            predecessor = self.search(
                [
                    ("id", "!=", record.id),
                    ("sampling_point_id", "=", record.sampling_point_id.id),
                    ("parameter_id", "=", record.parameter_id.id),
                    ("occupancy_state", "=", record.occupancy_state),
                    ("direction", "=", record.direction),
                    ("state", "=", LIMIT_STATE_APPROVED),
                ],
                limit=1,
            )
            today = fields.Date.context_today(record)
            if predecessor:
                predecessor.write(
                    {
                        "state": LIMIT_STATE_SUPERSEDED,
                        "superseded_date": today,
                        "superseded_by_id": record.id,
                    }
                )
                predecessor.message_post(
                    body=self.env._(
                        "Superseded by version %(version)s.", version=record.version
                    )
                )
                record.version = predecessor.version + 1
            record.write(
                {
                    "state": LIMIT_STATE_APPROVED,
                    "effective_date": today,
                    "approved_by_id": self.env.user.id,
                }
            )
        return True

    def action_create_revision(self):
        """Create a draft copy of an approved limit for revision.

        The approved record is left untouched until the replacement is
        approved in turn.
        """
        self.ensure_one()
        if self.state != LIMIT_STATE_APPROVED:
            raise UserError(
                self.env._("Only an approved limit can be revised.")
            )
        revision = self.copy(
            {
                "state": LIMIT_STATE_DRAFT,
                "version": self.version + 1,
                "effective_date": False,
                "superseded_date": False,
                "approved_by_id": False,
                "superseded_by_id": False,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Limit Revision"),
            "res_model": "ls.env.limit",
            "res_id": revision.id,
            "view_mode": "form",
            "target": "current",
        }

    def get_thresholds(self):
        """Return the thresholds that are enabled on this limit.

        A threshold whose flag is not set is returned as ``None`` so that the
        evaluation engine treats it as unconfigured rather than as a limit of
        zero.

        :returns: mapping with the keys ``alert``, ``action`` and ``spec``
        :rtype: dict
        """
        self.ensure_one()
        return {
            "alert": self.alert_value if self.alert_set else None,
            "action": self.action_value if self.action_set else None,
            "spec": self.spec_value if self.spec_set else None,
        }

    def write(self, vals):
        """Prevent the thresholds of an approved limit from being altered.

        Changing an approved threshold in place would invalidate the
        evaluations already made against it. Revision is the supported route.
        """
        protected = {
            "alert_value",
            "action_value",
            "spec_value",
            "alert_set",
            "action_set",
            "spec_set",
            "direction",
            "occupancy_state",
            "parameter_id",
            "sampling_point_id",
        }
        if protected.intersection(vals):
            for record in self:
                if record.state == LIMIT_STATE_APPROVED:
                    raise UserError(
                        self.env._(
                            "The thresholds of an approved limit cannot be changed. "
                            "Create a revision instead."
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_env_limit(self):
        """Prevent deletion of a limit that has been approved.

        An approved limit is part of the evidence trail for every result
        evaluated against it and is superseded rather than removed.
        """
        for record in self:
            if record.state != LIMIT_STATE_DRAFT:
                raise UserError(
                    self.env._(
                        "Only a draft limit can be deleted. Supersede the limit "
                        "instead."
                    )
                )
