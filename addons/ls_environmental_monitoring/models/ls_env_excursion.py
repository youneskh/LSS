# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Out-of-limit excursion."""

from odoo import api, fields, models
from odoo.exceptions import UserError

from .constants import (
    EVAL_SPEC,
    EVALUATION_SEVERITY,
    EVALUATIONS,
    EXCURSION_ASSESSMENT,
    EXCURSION_CANCELLED,
    EXCURSION_CLOSED,
    EXCURSION_INVESTIGATION,
    EXCURSION_OPEN,
    EXCURSION_PENDING_CLOSURE,
    EXCURSION_SEVERITIES,
    EXCURSION_STATES,
    EXCURSION_TRANSITIONS,
)


class LsEnvExcursion(models.Model):
    """A recorded breach of an alert, action or specification threshold.

    The excursion is the record of what was found, what it was judged to mean
    and what was done about it. Corrective and preventive action itself is
    outside the scope of this module; the record carries an external reference
    field and an overridable hook so that a corrective action module, when one
    is installed, can link its own record without this module depending on it.
    """

    _name = "ls.env.excursion"
    _description = "Environmental Monitoring Excursion"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "detection_date desc, name desc"

    name = fields.Char(
        string="Excursion Reference",
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env._("New"),
        index=True,
    )
    sample_id = fields.Many2one(comodel_name="ls.env.sample", required=True,
                                index=True,
                                ondelete="restrict",)
    result_ids = fields.One2many(
        comodel_name="ls.env.result",
        inverse_name="excursion_id",
        string="Breaching Results",
    )
    sampling_point_id = fields.Many2one(comodel_name="ls.env.sampling_point", related="sample_id.sampling_point_id",
                                        store=True,
                                        index=True,)
    area_id = fields.Many2one(comodel_name="ls.env.area", related="sample_id.area_id",
                              store=True,
                              index=True,)
    batch_reference = fields.Char(
        string="Batch / Campaign Reference",
        related="sample_id.batch_reference",
        store=True,
    )
    excursion_type = fields.Selection(
        selection=EVALUATIONS,
        string="Breach Type",
        required=True,
        readonly=True,
        index=True,
        help="Most severe outcome among the results that triggered this "
        "excursion.",
    )
    severity = fields.Selection(selection=EXCURSION_SEVERITIES, tracking=True,
                                help="Severity assigned during impact assessment.",)
    detection_date = fields.Datetime(
        string="Detected On",
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        index=True,
    )
    state = fields.Selection(
        selection=EXCURSION_STATES,
        string="Status",
        default=EXCURSION_OPEN,
        required=True,
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
    )
    owner_id = fields.Many2one(comodel_name="res.users", tracking=True,
                               default=lambda self: self.env.user,
                               help="User accountable for progressing this excursion.",)
    immediate_actions = fields.Text(tracking=True,
                                    help="Actions taken on detection, before assessment was complete.",)
    impact_assessment = fields.Text(tracking=True,
                                    help="Assessment of the effect on product, process and area status.",)
    product_impact = fields.Selection(
        selection=[
            ("none", "No Product Impact Identified"),
            ("potential", "Potential Product Impact"),
            ("confirmed", "Confirmed Product Impact"),
            ("not_assessed", "Not Yet Assessed"),
        ],
        default="not_assessed",
        tracking=True,
    )
    investigation_required = fields.Boolean(tracking=True)
    root_cause = fields.Text(tracking=True)
    corrective_actions = fields.Text(tracking=True)
    external_reference = fields.Char(
        string="External Record Reference",
        tracking=True,
        help="Identifier of a record raised in another system or module, for "
        "example a deviation or corrective action reference. Recorded as free "
        "text so that this module does not depend on those modules being "
        "installed.",
    )
    closure_justification = fields.Text(readonly=True, copy=False)
    closed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                   copy=False,
                                   tracking=True,)
    closure_datetime = fields.Datetime(
        string="Closed On", readonly=True, copy=False
    )
    company_id = fields.Many2one(comodel_name="res.company", related="sample_id.company_id",
                                 store=True,
                                 index=True,)

    _name_company_unique = models.Constraint(
        "UNIQUE(name, company_id)",
        "The excursion reference must be unique per company.",
    )

    @api.model
    def _prepare_from_results(self, sample, results):
        """Build the values for an excursion covering ``results``.

        :param sample: the ``ls.env.sample`` the results belong to
        :param results: the breaching ``ls.env.result`` records
        :rtype: dict
        """
        worst = max(
            results.mapped("evaluation"),
            key=lambda evaluation: EVALUATION_SEVERITY[evaluation],
        )
        return {
            "sample_id": sample.id,
            "excursion_type": worst,
            "detection_date": fields.Datetime.now(),
            "investigation_required": worst == EVAL_SPEC,
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the excursion reference from the configured sequence."""
        for vals in vals_list:
            if vals.get("name", self.env._("New")) == self.env._("New"):
                sample = self.env["ls.env.sample"].browse(vals.get("sample_id"))
                company_id = (
                    sample.company_id.id if sample else self.env.company.id
                )
                sequence = self.env["ir.sequence"].with_company(company_id)
                vals["name"] = (
                    sequence.next_by_code("ls.env.excursion") or self.env._("New")
                )
        return super().create(vals_list)

    def _check_transition(self, target_state):
        """Raise unless every record may move to ``target_state``."""
        state_labels = dict(EXCURSION_STATES)
        for record in self:
            if target_state not in EXCURSION_TRANSITIONS.get(record.state, ()):
                raise UserError(
                    self.env._(
                        "Excursion '%(excursion)s' cannot move from '%(current)s' "
                        "to '%(target)s'.",
                        excursion=record.name,
                        current=state_labels.get(record.state, record.state),
                        target=state_labels.get(target_state, target_state),
                    )
                )

    def action_start_assessment(self):
        """Move the excursion into impact assessment."""
        self._check_transition(EXCURSION_ASSESSMENT)
        self.write({"state": EXCURSION_ASSESSMENT})
        return True

    def action_start_investigation(self):
        """Move the excursion into investigation."""
        self._check_transition(EXCURSION_INVESTIGATION)
        for record in self:
            if not record.impact_assessment:
                raise UserError(
                    self.env._(
                        "An impact assessment must be recorded on excursion "
                        "'%(excursion)s' before an investigation is opened.",
                        excursion=record.name,
                    )
                )
        self.write({"state": EXCURSION_INVESTIGATION, "investigation_required": True})
        return True

    def action_propose_closure(self):
        """Move the excursion to pending closure."""
        self._check_transition(EXCURSION_PENDING_CLOSURE)
        for record in self:
            if not record.impact_assessment:
                raise UserError(
                    self.env._(
                        "An impact assessment must be recorded on excursion "
                        "'%(excursion)s' before closure is proposed.",
                        excursion=record.name,
                    )
                )
            if record.investigation_required and not record.root_cause:
                raise UserError(
                    self.env._(
                        "Excursion '%(excursion)s' requires an investigation, so a "
                        "root cause must be recorded before closure is proposed.",
                        excursion=record.name,
                    )
                )
            if record.product_impact == "not_assessed":
                raise UserError(
                    self.env._(
                        "The product impact of excursion '%(excursion)s' must be "
                        "assessed before closure is proposed.",
                        excursion=record.name,
                    )
                )
        self.write({"state": EXCURSION_PENDING_CLOSURE})
        return True

    def action_open_closure_wizard(self):
        """Open the wizard that records the closure justification."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Close Excursion"),
            "res_model": "ls.env.excursion.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_excursion_id": self.id},
        }

    def close(self, justification):
        """Close the excursion with a recorded justification.

        The closer must not be the owner, so that closure is confirmed by a
        second person.

        :param str justification: basis on which the excursion is closed
        """
        for record in self:
            record._check_transition(EXCURSION_CLOSED)
            if not justification:
                raise UserError(
                    self.env._(
                        "A justification is required to close an excursion."
                    )
                )
            if record.owner_id == self.env.user:
                raise UserError(
                    self.env._(
                        "Excursion '%(excursion)s' must be closed by a user other "
                        "than its owner.",
                        excursion=record.name,
                    )
                )
            record.write(
                {
                    "state": EXCURSION_CLOSED,
                    "closure_justification": justification,
                    "closed_by_id": self.env.user.id,
                    "closure_datetime": fields.Datetime.now(),
                }
            )
        return True

    def action_reopen_investigation(self):
        """Return an excursion pending closure to investigation."""
        self._check_transition(EXCURSION_INVESTIGATION)
        self.write({"state": EXCURSION_INVESTIGATION})
        return True

    def action_cancel(self):
        """Cancel an excursion raised in error."""
        self._check_transition(EXCURSION_CANCELLED)
        self.write({"state": EXCURSION_CANCELLED})
        return True

    def action_create_external_record(self):
        """Extension point for modules that manage corrective action.

        This module does not implement corrective and preventive action. A
        module that does may override this method to create its own record and
        write its identifier back to ``external_reference``. The default
        implementation reports that no such module is installed rather than
        failing silently.
        """
        self.ensure_one()
        raise UserError(
            self.env._(
                "No module providing corrective action management is installed. "
                "Record the reference of the external record in the External "
                "Record Reference field."
            )
        )

    def write(self, vals):
        """Prevent changes to an excursion once it is closed or cancelled."""
        editable_when_locked = {
            "message_follower_ids",
            "message_ids",
            "activity_ids",
            "external_reference",
        }
        if not editable_when_locked.issuperset(vals):
            for record in self:
                if record.state in (EXCURSION_CLOSED, EXCURSION_CANCELLED):
                    raise UserError(
                        self.env._(
                            "Excursion '%(excursion)s' is closed and can no longer "
                            "be modified.",
                            excursion=record.name,
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_env_excursion(self):
        """Prevent deletion of excursions.

        An excursion is evidence that a breach occurred and is cancelled
        rather than removed.
        """
        raise UserError(
            self.env._(
                "An excursion cannot be deleted. Cancel it instead so that the "
                "record is retained."
            )
        )
