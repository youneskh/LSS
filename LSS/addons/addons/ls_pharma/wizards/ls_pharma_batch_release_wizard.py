# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Wizard used to record a batch release decision."""

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..constants import RELEASE_CHECKLIST, RELEASE_CHECKLIST_FIELDS, RELEASE_DECISIONS


class LsPharmaBatchReleaseWizard(models.TransientModel):
    """Collect and validate a batch release decision before recording it.

    The wizard presents the checklist, pre-computes the checks that the
    system can evaluate on its own, and refuses to proceed when a
    precondition of 21 CFR 211.192 is not met.  The persistent decision is
    created by :meth:`action_confirm` and is append only from that point on.
    """

    _name = "ls.pharma.batch.release.wizard"
    _description = "Batch Release Decision Wizard"

    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", required=True,
                               readonly=True,)
    product_id = fields.Many2one(comodel_name="product.product", related="batch_id.product_id",
                                 readonly=True,)
    batch_state = fields.Selection(
        related="batch_id.state", string="Batch Status", readonly=True
    )
    yield_percentage = fields.Float(
        related="batch_id.yield_percentage", string="Yield (%)", readonly=True
    )
    yield_investigation_required = fields.Boolean(
        related="batch_id.yield_investigation_required", readonly=True
    )
    decision = fields.Selection(selection=RELEASE_DECISIONS, required=True,
                                default="released",)
    statement = fields.Text(string="Decision Statement", required=True)
    check_record_reviewed = fields.Boolean(
        string="Batch Records Reviewed and Approved"
    )
    check_discrepancies_closed = fields.Boolean(
        string="Discrepancies Investigated and Closed"
    )
    check_yield_within_limits = fields.Boolean(string="Yield Within Limits")
    check_components_verified = fields.Boolean(
        string="Component Charge-In Verified by a Second Person"
    )
    check_qc_conform = fields.Boolean(string="Laboratory Results Conform")
    check_labeling_reconciled = fields.Boolean(string="Labelling Reconciled")
    check_reserve_samples = fields.Boolean(string="Reserve Samples Retained")
    check_stability_programme = fields.Boolean(
        string="Covered by the Stability Programme"
    )
    system_evaluation = fields.Text(compute="_compute_system_evaluation",
                                    help=(
                                        "Result of the checks that the system can evaluate from the data "
                                        "it holds. It is advisory: the person taking the decision remains "
                                        "responsible for confirming every entry of the checklist."),
                                    )

    @api.depends("batch_id")
    def _compute_system_evaluation(self):
        """Summarise the checks that the system can evaluate on its own."""
        for wizard in self:
            batch = wizard.batch_id
            if not batch:
                wizard.system_evaluation = ""
                continue
            lines = []
            unapproved = batch.batch_record_ids.filtered(
                lambda record: record.state != "approved"
            )
            lines.append(
                self.env._(
                    "Batch records approved by the quality unit: %(done)s of "
                    "%(total)s.",
                    done=len(batch.batch_record_ids) - len(unapproved),
                    total=len(batch.batch_record_ids),
                )
            )
            open_discrepancies = sum(
                record.open_discrepancy_count
                for record in batch.batch_record_ids
            )
            lines.append(
                self.env._(
                    "Open discrepancies: %(count)s.", count=open_discrepancies
                )
            )
            nonconforming = sum(
                record.nonconforming_control_count
                for record in batch.batch_record_ids
            )
            lines.append(
                self.env._(
                    "Non-conforming control results: %(count)s.",
                    count=nonconforming,
                )
            )
            unreconciled = sum(
                record.unreconciled_label_count
                for record in batch.batch_record_ids
            )
            lines.append(
                self.env._(
                    "Unreconciled labelling items: %(count)s.",
                    count=unreconciled,
                )
            )
            reserve_samples = sum(
                record.reserve_sample_count for record in batch.batch_record_ids
            )
            lines.append(
                self.env._(
                    "Reserve samples recorded: %(count)s.", count=reserve_samples
                )
            )
            unverified = batch.component_ids.filtered(
                lambda component: not component.is_automated_charge
                and not component.verified_by_user_id
            )
            lines.append(
                self.env._(
                    "Component charges without a second-person verification: "
                    "%(count)s.",
                    count=len(unverified),
                )
            )
            if batch.yield_investigation_required:
                lines.append(
                    self.env._(
                        "The yield of %(value).2f%% falls outside the "
                        "established limits and requires an investigation "
                        "under 21 CFR 211.192.",
                        value=batch.yield_percentage,
                    )
                )
            lines.append(
                self.env._(
                    "Stability studies covering this batch: %(count)s.",
                    count=batch.stability_study_count,
                )
            )
            wizard.system_evaluation = "\n".join(lines)

    def action_confirm(self):
        """Record the decision and propagate it to the batch.

        :returns: an action opening the created decision.
        :rtype: dict
        """
        self.ensure_one()
        if self.decision == "released":
            missing = [
                label
                for field_name, label, _reference in RELEASE_CHECKLIST
                if not self[field_name]
            ]
            if missing:
                raise UserError(
                    self.env._(
                        "The following checks must be confirmed before batch "
                        "%(name)s can be released: %(missing)s.",
                        name=self.batch_id.name,
                        missing="; ".join(missing),
                    )
                )
        values = {
            "batch_id": self.batch_id.id,
            "decision": self.decision,
            "decision_date": fields.Datetime.now(),
            "decided_by_user_id": self.env.user.id,
            "statement": self.statement,
        }
        values.update(
            {field_name: self[field_name] for field_name in RELEASE_CHECKLIST_FIELDS}
        )
        release = self.env["ls.pharma.batch.release"].create(values)
        release._apply_to_batch()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Batch Release Decision"),
            "res_model": "ls.pharma.batch.release",
            "res_id": release.id,
            "view_mode": "form",
        }
