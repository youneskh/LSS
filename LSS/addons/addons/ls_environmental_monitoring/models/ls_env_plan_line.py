# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Monitoring plan line."""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .constants import (
    FREQUENCY_DAYS,
    FREQUENCY_MONTH,
    FREQUENCY_UNITS,
    FREQUENCY_WEEK,
    FREQUENCY_YEAR,
    OCCUPANCY_IN_OPERATION,
    OCCUPANCY_STATES,
    PLAN_APPROVED,
)


class LsEnvPlanLine(models.Model):
    """One monitoring requirement: a parameter at a point at a frequency."""

    _name = "ls.env.plan.line"
    _description = "Environmental Monitoring Plan Line"
    _order = "plan_id, sampling_point_id, parameter_id"

    plan_id = fields.Many2one(comodel_name="ls.env.plan", required=True,
                              index=True,
                              ondelete="cascade",)
    plan_state = fields.Selection(
        related="plan_id.state",
        string="Plan Status",
        store=True,
        index=True,
    )
    sampling_point_id = fields.Many2one(comodel_name="ls.env.sampling_point", required=True,
                                        index=True,
                                        ondelete="restrict",)
    area_id = fields.Many2one(comodel_name="ls.env.area", related="sampling_point_id.area_id",
                              store=True,)
    parameter_id = fields.Many2one(comodel_name="ls.env.parameter", required=True,
                                   index=True,
                                   ondelete="restrict",)
    method_id = fields.Many2one(comodel_name="ls.env.method", ondelete="restrict",
                                help="Method applied for this requirement. When empty, the method is "
                                "recorded at the time the sample is taken.",)
    occupancy_state = fields.Selection(selection=OCCUPANCY_STATES, required=True,
                                       default=OCCUPANCY_IN_OPERATION,
                                       help="State the area is expected to be in when the sample is taken.",)
    frequency_interval = fields.Integer(
        string="Every",
        required=True,
        default=1,
        help="Number of frequency units between two scheduled samples.",
    )
    frequency_unit = fields.Selection(selection=FREQUENCY_UNITS, required=True,
                                      default=FREQUENCY_WEEK,)
    start_date = fields.Date(help="First date on which this requirement applies. When empty, the "
                             "effective date of the plan is used.",)
    next_due_date = fields.Date(
        string="Next Due",
        readonly=True,
        copy=False,
        help="Next date for which a sample has still to be generated.",
    )
    responsible_id = fields.Many2one(comodel_name="res.users", help="User expected to collect the sample.",)
    notes = fields.Text()
    company_id = fields.Many2one(comodel_name="res.company", related="plan_id.company_id",
                                 store=True,
                                 index=True,)

    _frequency_interval_positive = models.Constraint(
        "CHECK(frequency_interval > 0)",
        "The frequency interval must be greater than zero.",
    )
    _point_parameter_occupancy_unique = models.Constraint(
        "UNIQUE(plan_id, sampling_point_id, parameter_id, occupancy_state)",
        "A plan may define only one line per sampling point, parameter and "
        "occupancy state.",
    )

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

    @api.constrains("sampling_point_id", "parameter_id", "company_id")
    def _check_company_consistency(self):
        """Reject references to records of a different company."""
        for record in self:
            if record.sampling_point_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "The sampling point must belong to the same company as the "
                        "plan."
                    )
                )
            if record.parameter_id.company_id != record.company_id:
                raise ValidationError(
                    self.env._(
                        "The parameter must belong to the same company as the plan."
                    )
                )

    def _interval_delta(self):
        """Return the interval between two occurrences as a relative delta.

        Months and years are advanced by calendar arithmetic rather than by a
        fixed number of days, so a monthly requirement stays on the same day
        of the month across months of differing length.

        :rtype: dateutil.relativedelta.relativedelta
        """
        self.ensure_one()
        interval = self.frequency_interval
        if self.frequency_unit == FREQUENCY_MONTH:
            return relativedelta(months=interval)
        if self.frequency_unit == FREQUENCY_YEAR:
            return relativedelta(years=interval)
        days_per_unit = FREQUENCY_DAYS.get(self.frequency_unit)
        if days_per_unit is None:
            raise ValidationError(
                self.env._(
                    "Frequency unit '%(unit)s' is not supported.",
                    unit=self.frequency_unit,
                )
            )
        return relativedelta(days=interval * days_per_unit)

    def _first_due_date(self):
        """Return the date on which this requirement first falls due."""
        self.ensure_one()
        if self.start_date:
            return self.start_date
        if self.plan_id.effective_date:
            return self.plan_id.effective_date
        return fields.Date.context_today(self)

    def _reset_next_due_date(self):
        """Initialise the next due date on lines that do not yet have one."""
        for record in self:
            if not record.next_due_date:
                record.next_due_date = record._first_due_date()

    def _due_dates_until(self, end_date, limit):
        """Return the outstanding due dates up to and including ``end_date``.

        :param end_date: last date to schedule, inclusive
        :param int limit: maximum number of dates to return
        :returns: list of dates in ascending order
        :rtype: list
        """
        self.ensure_one()
        if self.plan_state != PLAN_APPROVED:
            return []
        current = self._next_occurrence_on_or_after(
            self.next_due_date or self._first_due_date()
        )
        dates = []
        while current <= end_date and len(dates) < limit:
            dates.append(current)
            current = self._next_occurrence_on_or_after(current, strictly=True)
        return dates

    def _next_occurrence_on_or_after(self, reference, strictly=False):
        """Return the first occurrence of the requirement from ``reference``.

        Occurrences are computed from the start date of the line, or else
        the effective date of the plan (the anchor), as
        ``anchor + n * interval``, never by adding the interval to the
        previous occurrence: adding one month to 28 February would give
        28 March and every later occurrence would drift from the 31st.

        :param reference: date from which to search.
        :param bool strictly: return an occurrence strictly after
            ``reference`` instead of on or after it.
        :rtype: datetime.date
        """
        self.ensure_one()
        delta = self._interval_delta()
        anchor = self.start_date or self.plan_id.effective_date
        if not anchor:
            # Without a fixed start, the series continues from the reference.
            return reference + delta if strictly else reference
        index = 0
        occurrence = anchor
        while occurrence < reference or (strictly and occurrence == reference):
            index += 1
            occurrence = anchor + delta * index
        return occurrence

    @api.depends("sampling_point_id", "parameter_id")
    def _compute_display_name(self):
        """Show the sampling point and parameter together."""
        for record in self:
            record.display_name = "%s / %s" % (
                record.sampling_point_id.code or "",
                record.parameter_id.code or "",
            )
