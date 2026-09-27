# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Electronic batch production and control record."""

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..constants import BATCH_RECORD_STATES, BATCH_RECORD_TYPES


class LsPharmaBatchRecord(models.Model):
    """The batch production and control record of a batch.

    21 CFR 211.188 requires that batch production and control records be
    prepared for each batch of drug product produced and that they include
    complete information relating to the production and control of each
    batch.  Each requirement of that section is carried by a specific field
    or by a specific set of lines:

    ==================================  ====================================
    Provision                           Implementation
    ==================================  ====================================
    211.188(a) reproduction of the      ``master_record_reference``,
    master record, checked, dated and   ``master_record_version``,
    signed                              ``master_checked_by_user_id``,
                                        ``master_checked_date``
    211.188(b)(1) dates                 ``step_ids.date_performed``
    211.188(b)(2) equipment and lines   ``batch_id.equipment_ids``
    211.188(b)(3) identification of     ``batch_id.component_ids.
    each component batch                component_lot_id``
    211.188(b)(4) weights and measures  ``batch_id.component_ids.quantity``
    211.188(b)(5) in-process and        ``control_ids``
    laboratory control results
    211.188(b)(6) inspection of the     ``clearance_ids``
    packaging and labelling area
    before and after use
    211.188(b)(7) actual and            ``batch_id.actual_yield_qty`` and
    percentage of theoretical yield     ``batch_id.yield_percentage``
    211.188(b)(8) labelling control      ``labeling_ids``
    records
    211.188(b)(9) description of         ``container_closure_description``
    containers and closures
    211.188(b)(10) sampling performed    ``sample_ids``
    211.188(b)(11) identification of     ``step_ids.performed_by_user_id``
    the persons performing and           and
    checking each significant step       ``step_ids.checked_by_user_id``
    211.188(b)(12) investigations        ``discrepancy_ids``
    made according to 211.192
    211.188(b)(13) results of the        ``examination_result``
    examinations of 211.134
    ==================================  ====================================

    Provision 211.188(b)(13) refers to the examination of drug product
    containers and closures described in 21 CFR 211.134.  It is recorded as
    free text because the acceptable form of that examination depends on the
    product and is defined by the written procedures of the manufacturer.
    """

    _name = "ls.pharma.batch_record"
    _description = "Batch Production and Control Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "batch_id, name"

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The batch record reference must be unique per company.",
    )

    name = fields.Char(
        string="Record Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
    )
    batch_id = fields.Many2one(comodel_name="ls.pharma.batch", required=True,
                               ondelete="restrict",
                               index=True,
                               tracking=True,)
    product_id = fields.Many2one(comodel_name="product.product", related="batch_id.product_id",
                                 store=True,)
    record_type = fields.Selection(selection=BATCH_RECORD_TYPES, required=True,
                                   default="manufacturing",
                                   tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="batch_id.company_id",
                                 store=True,
                                 index=True,)

    # ------------------------------------------------------------------
    # 21 CFR 211.188(a) -- reproduction of the master record
    # ------------------------------------------------------------------
    master_record_reference = fields.Char(required=True,
                                          tracking=True,
                                          help=(
                                              "Reference of the master production and control record of which "
                                              "this record is a reproduction, as required by 21 CFR 211.188(a)."
                                              ),
                                          )
    master_record_version = fields.Char(required=True,
                                        tracking=True,)
    master_checked_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Master Record Checked By",
        tracking=True,
        help=(
            "User who checked that this record accurately reproduces the "
            "master production and control record."
        ),
    )
    master_checked_date = fields.Datetime(
        string="Master Record Checked On",
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Execution lines
    # ------------------------------------------------------------------
    step_ids = fields.One2many(
        comodel_name="ls.pharma.batch_record.step",
        inverse_name="record_id",
        string="Manufacturing Steps",
    )
    control_ids = fields.One2many(
        comodel_name="ls.pharma.batch_record.control",
        inverse_name="record_id",
        string="In-Process and Laboratory Controls",
    )
    clearance_ids = fields.One2many(
        comodel_name="ls.pharma.batch_record.clearance",
        inverse_name="record_id",
        string="Area Inspections",
    )
    labeling_ids = fields.One2many(
        comodel_name="ls.pharma.batch_record.labeling",
        inverse_name="record_id",
        string="Labelling Control",
    )
    sample_ids = fields.One2many(
        comodel_name="ls.pharma.batch_record.sample",
        inverse_name="record_id",
        string="Samples Taken",
    )
    discrepancy_ids = fields.One2many(
        comodel_name="ls.pharma.batch_record.discrepancy",
        inverse_name="record_id",
        string="Discrepancies and Investigations",
    )

    # ------------------------------------------------------------------
    # 21 CFR 211.188(b)(9) and (b)(13)
    # ------------------------------------------------------------------
    container_closure_description = fields.Text(
        string="Containers and Closures",
        help=(
            "Description of the drug product containers and closures, as "
            "required by 21 CFR 211.188(b)(9)."
        ),
    )
    examination_result = fields.Text(
        string="Container and Closure Examination",
        help=(
            "Results of the examinations made in accordance with "
            "21 CFR 211.134, as required by 21 CFR 211.188(b)(13)."
        ),
    )

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------
    step_count = fields.Integer(string="Steps", compute="_compute_counts", store=True)
    step_done_count = fields.Integer(
        string="Steps Completed", compute="_compute_counts", store=True
    )
    open_discrepancy_count = fields.Integer(
        string="Open Discrepancies", compute="_compute_counts", store=True
    )
    nonconforming_control_count = fields.Integer(
        string="Non-Conforming Controls", compute="_compute_counts", store=True
    )
    unreconciled_label_count = fields.Integer(
        string="Unreconciled Labels", compute="_compute_counts", store=True
    )
    reserve_sample_count = fields.Integer(
        string="Reserve Samples", compute="_compute_counts", store=True
    )
    completion_percentage = fields.Float(
        string="Execution Progress (%)",
        compute="_compute_counts",
        store=True,
        digits=(16, 2),
        help=(
            "Percentage of manufacturing steps that have been completed. The "
            "value ranges from 0 to 100."
        ),
    )

    # ------------------------------------------------------------------
    # Accountability and state
    # ------------------------------------------------------------------
    executed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Execution Completed By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    date_executed = fields.Datetime(
        string="Execution Completed On", readonly=True, copy=False
    )
    reviewed_by_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Reviewed By",
        readonly=True,
        copy=False,
        tracking=True,
        help=(
            "Member of the quality unit who reviewed the record under "
            "21 CFR 211.192. This user may not be the user who completed the "
            "execution."
        ),
    )
    date_reviewed = fields.Datetime(
        string="Reviewed On", readonly=True, copy=False
    )
    review_conclusion = fields.Text(copy=False)
    state = fields.Selection(
        selection=BATCH_RECORD_STATES,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends(
        "step_ids.state",
        "discrepancy_ids.state",
        "control_ids.is_conform",
        "labeling_ids.is_reconciled",
        "sample_ids.sample_type",
    )
    def _compute_counts(self):
        """Compute the aggregates that drive the review readiness checks."""
        for record in self:
            steps = record.step_ids
            done_steps = steps.filtered(lambda step: step.state == "done")
            record.step_count = len(steps)
            record.step_done_count = len(done_steps)
            record.completion_percentage = (
                (len(done_steps) / len(steps)) * 100.0 if steps else 0.0
            )
            record.open_discrepancy_count = len(
                record.discrepancy_ids.filtered(
                    lambda discrepancy: discrepancy.state != "closed"
                )
            )
            record.nonconforming_control_count = len(
                record.control_ids.filtered(lambda control: not control.is_conform)
            )
            record.unreconciled_label_count = len(
                record.labeling_ids.filtered(lambda label: not label.is_reconciled)
            )
            record.reserve_sample_count = len(
                record.sample_ids.filtered(
                    lambda sample: sample.sample_type == "reserve"
                )
            )

    @api.depends("name", "batch_id")
    def _compute_display_name(self):
        """Show the record reference together with the batch reference."""
        for record in self:
            if record.batch_id:
                record.display_name = "%s (%s)" % (record.name, record.batch_id.name)
            else:
                record.display_name = record.name or ""

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Assign the record reference from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == self.env._("New"):
                sequence = self.env["ir.sequence"].next_by_code(
                    "ls.pharma.batch_record"
                )
                vals["name"] = sequence or self.env._("New")
        return super().create(vals_list)

    def write(self, vals):
        """Freeze the execution content once the record has been approved."""
        protected = {
            "batch_id",
            "record_type",
            "master_record_reference",
            "master_record_version",
            "master_checked_by_user_id",
            "master_checked_date",
            "container_closure_description",
            "examination_result",
        }
        touched = protected.intersection(vals)
        if touched:
            for record in self:
                if record.state in ("approved", "rejected"):
                    raise UserError(
                        self.env._(
                            "Batch record %(name)s has been closed by the "
                            "quality unit. The fields %(fields)s can no "
                            "longer be modified.",
                            name=record.name,
                            fields=", ".join(sorted(touched)),
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_pharma_batch_record(self):
        """Forbid the deletion of a record that has left the draft state."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Batch record %(name)s has left the draft state and "
                        "can no longer be deleted.",
                        name=record.name,
                    )
                )

    def copy_data(self, default=None):
        """Reset the accountability data when a record is duplicated."""
        default = dict(default or {})
        default.setdefault("state", "draft")
        default.setdefault("name", self.env._("New"))
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def _assert_state(self, expected_states, action_label):
        """Raise unless every record is in one of ``expected_states``.

        :param tuple expected_states: technical states that permit the action.
        :param str action_label: label used in the error message.
        :raises UserError: when a record is in an unexpected state.
        """
        for record in self:
            if record.state not in expected_states:
                raise UserError(
                    self.env._(
                        "Batch record %(name)s is in state %(state)s and the "
                        "action %(action)s is not permitted from that state.",
                        name=record.name,
                        state=record.state,
                        action=action_label,
                    )
                )

    def action_start_execution(self):
        """Open the record for execution."""
        self._assert_state(("draft",), self.env._("Start Execution"))
        for record in self:
            if not record.master_checked_by_user_id or not record.master_checked_date:
                raise UserError(
                    self.env._(
                        "Batch record %(name)s cannot be executed until the "
                        "reproduction of the master production and control "
                        "record has been checked, dated and attributed, as "
                        "required by 21 CFR 211.188(a).",
                        name=record.name,
                    )
                )
        self.write({"state": "in_execution"})
        return True

    def action_complete_execution(self):
        """Declare the execution complete."""
        self._assert_state(("in_execution",), self.env._("Complete Execution"))
        for record in self:
            pending = record.step_ids.filtered(
                lambda step: step.state not in ("done", "not_applicable")
            )
            if pending:
                raise UserError(
                    self.env._(
                        "Batch record %(name)s still has %(count)s step(s) "
                        "that are neither completed nor marked as not "
                        "applicable.",
                        name=record.name,
                        count=len(pending),
                    )
                )
            record.write(
                {
                    "state": "completed",
                    "executed_by_user_id": self.env.user.id,
                    "date_executed": fields.Datetime.now(),
                }
            )
        return True

    def action_submit_review(self):
        """Submit the record to the quality unit."""
        self._assert_state(("completed",), self.env._("Submit for Review"))
        self.write({"state": "under_review"})
        return True

    def action_approve(self):
        """Approve the record on behalf of the quality unit.

        21 CFR 211.192 requires the quality control unit to review and
        approve the record before the batch is released or distributed, and
        requires every unexplained discrepancy to be thoroughly investigated.
        The approval is therefore refused while a discrepancy remains open,
        and the reviewer may not be the user who completed the execution.
        """
        self._assert_state(("under_review",), self.env._("Approve"))
        for record in self:
            if record.open_discrepancy_count:
                raise UserError(
                    self.env._(
                        "Batch record %(name)s still carries %(count)s open "
                        "discrepancy or discrepancies. 21 CFR 211.192 "
                        "requires that every unexplained discrepancy be "
                        "thoroughly investigated before release.",
                        name=record.name,
                        count=record.open_discrepancy_count,
                    )
                )
            if (
                record.executed_by_user_id
                and record.executed_by_user_id.id == self.env.user.id
            ):
                raise UserError(
                    self.env._(
                        "Batch record %(name)s was executed by the current "
                        "user. The review required by 21 CFR 211.192 is "
                        "carried out by the quality control unit and must be "
                        "performed by a different user.",
                        name=record.name,
                    )
                )
            record.write(
                {
                    "state": "approved",
                    "reviewed_by_user_id": self.env.user.id,
                    "date_reviewed": fields.Datetime.now(),
                }
            )
        return True

    def action_reject(self):
        """Reject the record on behalf of the quality unit."""
        self._assert_state(("under_review",), self.env._("Reject"))
        for record in self:
            if not record.review_conclusion:
                raise UserError(
                    self.env._(
                        "A written conclusion is required before batch record "
                        "%(name)s can be rejected.",
                        name=record.name,
                    )
                )
            record.write(
                {
                    "state": "rejected",
                    "reviewed_by_user_id": self.env.user.id,
                    "date_reviewed": fields.Datetime.now(),
                }
            )
        return True

    def action_return_to_execution(self):
        """Return a record under review to the execution state."""
        self._assert_state(
            ("completed", "under_review"), self.env._("Return to Execution")
        )
        self.write({"state": "in_execution"})
        return True
