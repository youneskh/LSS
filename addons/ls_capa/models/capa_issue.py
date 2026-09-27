# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Master CAPA record and its state machine."""

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

CAPA_STATES = [
    ("identified", "Identified"),
    ("assessed", "Assessed"),
    ("investigation", "Investigation"),
    ("action_planning", "Action Planning"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("verified", "Verified"),
    ("closed", "Closed"),
]

OPEN_STATES = [state for state, _label in CAPA_STATES if state != "closed"]


class LsCapaIssue(models.Model):
    """A Corrective And Preventive Action record.

    The record carries the CAPA through the eight-state lifecycle defined in
    the Life Sciences Suite functional specification, from initial
    identification of a quality issue to formal closure after effectiveness
    has been verified.
    """

    _name = "ls.capa.issue"
    _description = "CAPA Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_identified desc, id desc"
    _rec_name = "name"

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------
    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _("New"),
        help="Unique CAPA reference allocated from a sequence on creation.",
    )
    title = fields.Char(required=True,
                        tracking=True,
                        help="Short statement of the quality issue being addressed.",)
    description = fields.Text(
        string="Issue Description",
        required=True,
        help="Factual description of the issue, including what was observed, "
             "where, and when.",
    )
    source = fields.Selection(
        selection=[
            ("internal_audit", "Internal Audit"),
            ("external_audit", "External Audit"),
            ("inspection", "Regulatory Inspection"),
            ("deviation", "Deviation"),
            ("complaint", "Customer Complaint"),
            ("nonconformity", "Non-Conformity"),
            ("management_review", "Management Review"),
            ("risk_assessment", "Risk Assessment"),
            ("environmental_monitoring", "Environmental Monitoring"),
            ("supplier", "Supplier Issue"),
            ("change_control", "Change Control"),
            ("other", "Other"),
        ],
        required=True,
        tracking=True,
        help="Process that generated the CAPA. Used for trend analysis.",
    )
    source_reference = fields.Char(help="Identifier of the originating record, for example the audit "
                                   "report number or the deviation reference.",)
    capa_type = fields.Selection(
        selection=[
            ("corrective", "Corrective"),
            ("preventive", "Preventive"),
            ("both", "Corrective and Preventive"),
        ],
        required=True,
        default="corrective",
        tracking=True,
        help="Corrective actions address an issue that has occurred. "
             "Preventive actions address an issue that could occur.",
    )
    severity = fields.Selection(
        selection=[
            ("critical", "Critical"),
            ("major", "Major"),
            ("minor", "Minor"),
        ],
        required=True,
        default="minor",
        tracking=True,
        help="Severity classification driving the escalation path and the "
             "proposed due date.",
    )
    priority = fields.Selection(
        selection=[("0", "Low"), ("1", "Normal"), ("2", "High")],
        default="1",
        tracking=True,
    )
    category_id = fields.Many2one(comodel_name="ls.capa.category", tracking=True,
                                  help="Process area classification used for grouping and reporting.",)

    # ------------------------------------------------------------------
    # Ownership and dates
    # ------------------------------------------------------------------
    date_identified = fields.Date(
        string="Identification Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date on which the issue was identified.",
    )
    date_due = fields.Date(
        string="Due Date",
        compute="_compute_date_due",
        store=True,
        readonly=False,
        tracking=True,
        help="Target date for CAPA closure. Proposed from the category lead "
             "time and editable by the CAPA owner.",
    )
    date_closed = fields.Datetime(
        string="Closure Date",
        readonly=True,
        copy=False,
        tracking=True,
    )
    identified_by_id = fields.Many2one(comodel_name="res.users", required=True,
                                       default=lambda self: self.env.user,
                                       tracking=True,)
    owner_id = fields.Many2one(
        comodel_name="res.users",
        string="CAPA Owner",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User accountable for progressing the CAPA to closure.",
    )
    closed_by_id = fields.Many2one(comodel_name="res.users", readonly=True,
                                   copy=False,)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    active = fields.Boolean(default=True)

    # ------------------------------------------------------------------
    # Impact assessment
    # ------------------------------------------------------------------
    state = fields.Selection(
        selection=CAPA_STATES,
        string="Status",
        default="identified",
        required=True,
        tracking=True,
        copy=False,
        index=True,
    )
    immediate_action = fields.Text(
        string="Immediate Action / Correction",
        help="Containment action already taken to limit the effect of the "
             "issue, recorded separately from the corrective action plan.",
    )
    impact_assessment = fields.Text(help="Assessment of the effect of the issue on product quality, "
                                    "patient safety and regulatory status.",)
    quality_impact = fields.Boolean(
        string="Product Quality Impact",
        tracking=True,
    )
    regulatory_impact = fields.Boolean(tracking=True,)
    safety_impact = fields.Boolean(
        string="Patient / User Safety Impact",
        tracking=True,
    )
    closure_summary = fields.Text(copy=False,
                                  help="Summary justifying closure, recorded at the closure step.",)

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------
    root_cause_ids = fields.One2many(
        comodel_name="ls.capa.root_cause",
        inverse_name="issue_id",
        string="Root Cause Analyses",
    )
    action_ids = fields.One2many(
        comodel_name="ls.capa.action",
        inverse_name="issue_id",
        string="Actions",
    )
    effectiveness_ids = fields.One2many(
        comodel_name="ls.capa.effectiveness",
        inverse_name="issue_id",
        string="Effectiveness Checks",
    )

    # ------------------------------------------------------------------
    # Computed indicators
    # ------------------------------------------------------------------
    root_cause_count = fields.Integer(compute="_compute_relation_counts",)
    action_count = fields.Integer(compute="_compute_relation_counts",)
    action_done_count = fields.Integer(
        string="Completed Action Count",
        compute="_compute_relation_counts",
    )
    effectiveness_count = fields.Integer(
        string="Effectiveness Check Count",
        compute="_compute_relation_counts",
    )
    progress = fields.Float(
        string="Action Progress (%)",
        compute="_compute_progress",
        store=True,
        aggregator="avg",
        help="Share of non-cancelled actions that reached the Done state.",
    )
    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_is_overdue",
        search="_search_is_overdue",
        help="True when the due date has passed and the CAPA is not closed.",
    )
    days_to_due = fields.Integer(
        string="Days To Due Date",
        compute="_compute_is_overdue",
        help="Calendar days remaining before the due date. Negative when "
             "the due date has passed.",
    )

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The CAPA reference must be unique per company.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends(
        "date_identified",
        "category_id",
        "category_id.default_due_days",
    )
    def _compute_date_due(self):
        """Propose a due date from the identification date and category.

        When no category is set the field is left untouched so a manually
        entered due date is never silently discarded.
        """
        for record in self:
            if record.date_identified and record.category_id:
                record.date_due = record.date_identified + timedelta(
                    days=record.category_id.default_due_days
                )
            elif not record.date_due:
                record.date_due = False

    @api.depends(
        "root_cause_ids",
        "action_ids",
        "action_ids.state",
        "effectiveness_ids",
    )
    def _compute_relation_counts(self):
        """Compute the counts displayed in the form view smart buttons."""
        for record in self:
            actions = record.action_ids
            record.root_cause_count = len(record.root_cause_ids)
            record.action_count = len(actions)
            record.action_done_count = len(
                actions.filtered(lambda a: a.state == "done")
            )
            record.effectiveness_count = len(record.effectiveness_ids)

    @api.depends("action_ids", "action_ids.state")
    def _compute_progress(self):
        """Compute completion progress over non-cancelled actions."""
        for record in self:
            relevant = record.action_ids.filtered(
                lambda a: a.state != "cancelled"
            )
            if not relevant:
                record.progress = 0.0
                continue
            done = len(relevant.filtered(lambda a: a.state == "done"))
            record.progress = 100.0 * done / len(relevant)

    @api.depends("date_due", "state")
    def _compute_is_overdue(self):
        """Flag CAPA records whose due date has passed before closure."""
        today = fields.Date.context_today(self)
        for record in self:
            if not record.date_due:
                record.is_overdue = False
                record.days_to_due = 0
                continue
            record.days_to_due = (record.date_due - today).days
            record.is_overdue = (
                record.state != "closed" and record.date_due < today
            )

    def _search_is_overdue(self, operator, value):
        """Allow searching and filtering on the non-stored overdue flag.

        :param str operator: comparison operator supplied by the search view.
        :param bool value: value the operator is applied against.
        :return: a search domain selecting overdue or non-overdue records.
        :rtype: list
        """
        if operator not in ("=", "!="):
            raise UserError(
                _("The Overdue filter only supports the = and != operators.")
            )
        today = fields.Date.context_today(self)
        overdue_domain = [
            ("date_due", "<", today),
            ("state", "!=", "closed"),
        ]
        positive = (operator == "=") == bool(value)
        if positive:
            return overdue_domain
        return [
            "|",
            ("date_due", ">=", today),
            ("state", "=", "closed"),
        ]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("date_identified", "date_due")
    def _check_dates(self):
        """Ensure the due date is not earlier than the identification date."""
        for record in self:
            if (
                record.date_due
                and record.date_identified
                and record.date_due < record.date_identified
            ):
                raise ValidationError(
                    _(
                        "CAPA %(reference)s: the due date cannot be earlier "
                        "than the identification date.",
                        reference=record.name,
                    )
                )

    @api.constrains("state", "closure_summary")
    def _check_closure_summary(self):
        """Require a closure summary on closed records."""
        for record in self:
            if record.state == "closed" and not (
                record.closure_summary or ""
            ).strip():
                raise ValidationError(
                    _(
                        "CAPA %(reference)s cannot be closed without a "
                        "closure summary.",
                        reference=record.name,
                    )
                )

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the CAPA reference from the sequence on creation.

        :param list vals_list: list of value dictionaries.
        :return: the created recordset.
        :rtype: ls.capa.issue
        """
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                company_id = vals.get("company_id") or self.env.company.id
                sequence = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("ls.capa.issue")
                )
                vals["name"] = sequence or _("New")
        return super().create(vals_list)

    def copy_data(self, default=None):
        """Reset the reference so duplicates receive their own sequence value.

        :param dict default: default values applied to the copy.
        :return: list of value dictionaries for the new records.
        :rtype: list
        """
        default = dict(default or {})
        default.setdefault("name", _("New"))
        return super().copy_data(default=default)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_capa_issue(self):
        """Prevent deletion of CAPA records that left the Identified state.

        Records that have progressed carry GxP-relevant evidence and are
        archived rather than deleted.

        :return: True when the deletion succeeded.
        :rtype: bool
        """
        blocked = self.filtered(lambda r: r.state != "identified")
        if blocked:
            raise UserError(
                _(
                    "The following CAPA records cannot be deleted because "
                    "they progressed beyond the Identified status: %(refs)s. "
                    "Archive them instead.",
                    refs=", ".join(blocked.mapped("name")),
                )
            )

    # ------------------------------------------------------------------
    # Workflow helpers
    # ------------------------------------------------------------------
    def _set_state(self, new_state):
        """Write the new state and post a tracked note in the chatter.

        :param str new_state: technical value of the target state.
        """
        labels = dict(CAPA_STATES)
        for record in self:
            record.write({"state": new_state})
            record.message_post(
                body=_(
                    "Status changed to %(status)s.",
                    status=labels[new_state],
                )
            )

    def _check_transition(self, expected_states):
        """Verify every record is in one of the states allowed for a step.

        :param list expected_states: technical state values allowed as source.
        :raise UserError: when at least one record is in another state.
        """
        labels = dict(CAPA_STATES)
        invalid = self.filtered(lambda r: r.state not in expected_states)
        if invalid:
            raise UserError(
                _(
                    "CAPA %(refs)s cannot perform this transition from the "
                    "current status. Expected status: %(expected)s.",
                    refs=", ".join(invalid.mapped("name")),
                    expected=", ".join(
                        labels[state] for state in expected_states
                    ),
                )
            )

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------
    def action_assess(self):
        """Move from Identified to Assessed.

        Requires a documented impact assessment.

        :return: True when the transition succeeded.
        :rtype: bool
        """
        self._check_transition(["identified"])
        missing = self.filtered(
            lambda r: not (r.impact_assessment or "").strip()
        )
        if missing:
            raise UserError(
                _(
                    "An impact assessment must be documented before "
                    "assessing CAPA %(refs)s.",
                    refs=", ".join(missing.mapped("name")),
                )
            )
        self._set_state("assessed")
        return True

    def action_start_investigation(self):
        """Move from Assessed to Investigation.

        :return: True when the transition succeeded.
        :rtype: bool
        """
        self._check_transition(["assessed"])
        self._set_state("investigation")
        return True

    def action_start_action_planning(self):
        """Move from Investigation to Action Planning.

        Requires at least one confirmed root cause analysis.

        :return: True when the transition succeeded.
        :rtype: bool
        """
        self._check_transition(["investigation"])
        missing = self.filtered(
            lambda r: not r.root_cause_ids.filtered(
                lambda rc: rc.state == "confirmed"
            )
        )
        if missing:
            raise UserError(
                _(
                    "At least one confirmed root cause analysis is required "
                    "before planning actions for CAPA %(refs)s.",
                    refs=", ".join(missing.mapped("name")),
                )
            )
        self._set_state("action_planning")
        return True

    def action_start_progress(self):
        """Move from Action Planning to In Progress.

        Requires at least one planned action.

        :return: True when the transition succeeded.
        :rtype: bool
        """
        self._check_transition(["action_planning"])
        missing = self.filtered(lambda r: not r.action_ids)
        if missing:
            raise UserError(
                _(
                    "At least one action must be planned before starting "
                    "CAPA %(refs)s.",
                    refs=", ".join(missing.mapped("name")),
                )
            )
        self._set_state("in_progress")
        return True

    def action_complete(self):
        """Move from In Progress to Completed.

        Requires every action to be either Done or Cancelled.

        :return: True when the transition succeeded.
        :rtype: bool
        """
        self._check_transition(["in_progress"])
        missing = self.filtered(
            lambda r: r.action_ids.filtered(
                lambda a: a.state not in ("done", "cancelled")
            )
        )
        if missing:
            raise UserError(
                _(
                    "All actions must be completed or cancelled before "
                    "completing CAPA %(refs)s.",
                    refs=", ".join(missing.mapped("name")),
                )
            )
        self._set_state("completed")
        return True

    def action_verify(self):
        """Move from Completed to Verified.

        Requires at least one effectiveness check concluded as Effective and
        no effectiveness check still awaiting a conclusion.

        :return: True when the transition succeeded.
        :rtype: bool
        """
        self._check_transition(["completed"])
        no_effective = self.filtered(
            lambda r: not r.effectiveness_ids.filtered(
                lambda e: e.result == "effective"
            )
        )
        if no_effective:
            raise UserError(
                _(
                    "At least one effectiveness check must conclude as "
                    "Effective before verifying CAPA %(refs)s.",
                    refs=", ".join(no_effective.mapped("name")),
                )
            )
        pending = self.filtered(
            lambda r: r.effectiveness_ids.filtered(
                lambda e: e.state != "done"
            )
        )
        if pending:
            raise UserError(
                _(
                    "Every effectiveness check must be completed before "
                    "verifying CAPA %(refs)s.",
                    refs=", ".join(pending.mapped("name")),
                )
            )
        self._set_state("verified")
        return True

    def action_open_close_wizard(self):
        """Open the closure wizard used to capture the closure summary.

        :return: an ``ir.actions.act_window`` dictionary.
        """
        self.ensure_one()
        self._check_transition(["verified"])
        return {
            "type": "ir.actions.act_window",
            "name": _("Close CAPA"),
            "res_model": "ls.capa.close.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_issue_id": self.id},
        }

    def action_close(self):
        """Move from Verified to Closed.

        Requires a closure summary, which is normally captured through the
        closure wizard.

        :return: True when the transition succeeded.
        :rtype: bool
        """
        self._check_transition(["verified"])
        missing = self.filtered(
            lambda r: not (r.closure_summary or "").strip()
        )
        if missing:
            raise UserError(
                _(
                    "A closure summary is required before closing CAPA "
                    "%(refs)s.",
                    refs=", ".join(missing.mapped("name")),
                )
            )
        self.write(
            {
                "state": "closed",
                "date_closed": fields.Datetime.now(),
                "closed_by_id": self.env.user.id,
            }
        )
        for record in self:
            record.message_post(body=_("CAPA closed."))
        return True

    # ------------------------------------------------------------------
    # Navigation actions
    # ------------------------------------------------------------------
    def _action_open_related(self, model, name, context=None):
        """Build a window action listing records related to this CAPA.

        :param str model: technical name of the related model.
        :param str name: title of the resulting action.
        :param dict context: extra context merged into the action.
        :return: an ``ir.actions.act_window`` dictionary.
        """
        self.ensure_one()
        action_context = {"default_issue_id": self.id}
        action_context.update(context or {})
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": model,
            "view_mode": "list,form",
            "domain": [("issue_id", "=", self.id)],
            "context": action_context,
        }

    def action_view_root_causes(self):
        """Open the root cause analyses of this CAPA."""
        return self._action_open_related(
            "ls.capa.root_cause", _("Root Cause Analyses")
        )

    def action_view_actions(self):
        """Open the actions of this CAPA."""
        return self._action_open_related("ls.capa.action", _("CAPA Actions"))

    def action_view_effectiveness(self):
        """Open the effectiveness checks of this CAPA."""
        return self._action_open_related(
            "ls.capa.effectiveness", _("Effectiveness Checks")
        )

    # ------------------------------------------------------------------
    # Scheduled actions
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_overdue(self):
        """Post a chatter reminder on every overdue open CAPA record.

        Executed by the ``ir.cron`` record shipped with this module. The
        method is idempotent within a day only in the sense that it always
        posts the current remaining-days figure; it does not deduplicate
        messages, so the cron interval controls the notification frequency.

        :return: True once all overdue records were processed.
        :rtype: bool
        """
        today = fields.Date.context_today(self)
        overdue = self.search(
            [
                ("state", "in", OPEN_STATES),
                ("date_due", "<", today),
            ]
        )
        for record in overdue:
            record.message_post(
                body=_(
                    "This CAPA is overdue. Due date was %(due)s.",
                    due=fields.Date.to_string(record.date_due),
                ),
                partner_ids=record.owner_id.partner_id.ids,
            )
        return True
