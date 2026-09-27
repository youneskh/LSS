# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Retention policies applied to controlled documents.

A retention policy defines how long a controlled document must be retained,
starting from a defined trigger event, and which action is taken when the
retention period elapses.

Destruction of records is deliberately NOT implemented. See the module
README for the rationale.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class LsDocumentRetentionPolicy(models.Model):
    """Definition of a document retention rule."""

    _name = "ls.document.retention_policy"
    _description = "Life Sciences Document Retention Policy"
    _order = "name"

    name = fields.Char(
        string="Policy Name",
        required=True,
        translate=True,
    )
    code = fields.Char(required=True,
                       help="Short unique identifier of the policy, used in reports.",)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    description = fields.Text(translate=True)
    duration_value = fields.Integer(
        string="Retention Duration",
        required=True,
        default=5,
        help="Number of duration units the document must be retained.",
    )
    duration_unit = fields.Selection(
        selection=[("month", "Months"), ("year", "Years")],
        required=True,
        default="year",
    )
    retention_trigger = fields.Selection(
        selection=[
            ("publication", "Publication Date"),
            ("archiving", "Archiving Date"),
        ],
        required=True,
        default="publication",
        help=(
            "Event from which the retention period is counted. "
            "'Publication Date' uses the effective date of the document. "
            "'Archiving Date' uses the date the document was archived."
        ),
    )
    end_of_life_action = fields.Selection(
        selection=[
            ("notify", "Notify Document Managers"),
            ("archive", "Archive Document and Notify"),
        ],
        string="End of Retention Action",
        required=True,
        default="notify",
        help=(
            "Action performed by the retention scheduled action once the "
            "retention due date is reached. No option destroys records."
        ),
    )
    notice_period_days = fields.Integer(
        string="Advance Notice (Days)",
        required=True,
        default=90,
        help=(
            "Number of days before the retention due date at which the "
            "document is flagged as 'Due Soon'."
        ),
    )
    folder_ids = fields.One2many(
        comodel_name="ls.document.folder",
        inverse_name="retention_policy_id",
        string="Folders",
    )
    document_ids = fields.One2many(
        comodel_name="ls.document.document",
        inverse_name="retention_policy_id",
        string="Documents",
    )

    _code_company_uniq = models.Constraint(
        "UNIQUE(code, company_id)",
        "The retention policy code must be unique per company.",
    )
    _duration_value_positive = models.Constraint(
        "CHECK(duration_value > 0)",
        "The retention duration must be strictly greater than zero.",
    )
    _notice_period_positive = models.Constraint(
        "CHECK(notice_period_days >= 0)",
        "The advance notice period cannot be negative.",
    )

    @api.depends("name", "code")
    def _compute_display_name(self):
        """Display the policy as ``[CODE] Name``."""
        for policy in self:
            policy.display_name = "[%s] %s" % (policy.code or "", policy.name or "")

    @api.constrains("duration_value", "duration_unit")
    def _check_duration(self):
        """Reject retention periods that cannot be expressed as a real date."""
        for policy in self:
            if policy.duration_unit == "year" and policy.duration_value > 200:
                raise ValidationError(
                    _(
                        "A retention duration of %(value)s years is not "
                        "supported. Use a value of 200 years or less.",
                        value=policy.duration_value,
                    )
                )

    def compute_due_date(self, trigger_date):
        """Return the retention due date for a given trigger date.

        :param trigger_date: ``datetime.date`` at which retention starts.
        :return: ``datetime.date`` when retention elapses, or ``False`` when
            no trigger date is available.
        """
        self.ensure_one()
        if not trigger_date:
            return False
        if self.duration_unit == "year":
            delta = relativedelta(years=self.duration_value)
        else:
            delta = relativedelta(months=self.duration_value)
        return trigger_date + delta
