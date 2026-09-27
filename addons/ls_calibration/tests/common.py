# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures of the calibration test suite."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class LsCalibrationCommon(TransactionCase):
    """Common instruments, plans and users used by the calibration tests."""

    @classmethod
    def setUpClass(cls):
        """Create the users, the instruments and the calibration plans."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.today = fields.Date.context_today(cls.env["ls.calibration.instrument"])

        cls.group_viewer = cls.env.ref(
            "ls_calibration.group_ls_calibration_viewer"
        )
        cls.group_technician = cls.env.ref(
            "ls_calibration.group_ls_calibration_technician"
        )
        cls.group_manager = cls.env.ref(
            "ls_calibration.group_ls_calibration_manager"
        )

        cls.user_viewer = cls._create_user("calibration_viewer", cls.group_viewer)
        cls.user_technician = cls._create_user(
            "calibration_technician", cls.group_technician
        )
        cls.user_manager = cls._create_user(
            "calibration_manager", cls.group_manager
        )

        cls.instrument = cls.env["ls.calibration.instrument"].create(
            {
                "name": "Test balance",
                "manufacturer": "Test Instruments",
                "model_reference": "TB-100",
                "serial_number": "SN-TB-0001",
                "location": "Test laboratory",
                "criticality": "critical",
                "gxp_impact": "direct",
                "range_min": 0.0,
                "range_max": 200.0,
                "unit": "g",
                "tolerance_type": "absolute",
                "tolerance_value": 0.01,
                "alert_lead_days": 30,
                "state": "in_service",
            }
        )
        cls.standard = cls.env["ls.calibration.instrument"].create(
            {
                "name": "Test mass standard",
                "unit": "g",
                "state": "in_service",
            }
        )
        cls.plan = cls.env["ls.calibration.plan"].create(
            {
                "instrument_id": cls.instrument.id,
                "description": "Annual calibration",
                "procedure_reference": "SOP-TEST-001",
                "interval_number": 12,
                "interval_uom": "month",
                "start_date": cls.today,
                "point_ids": [
                    fields.Command.create(
                        {
                            "sequence": 10,
                            "name": "Point 1",
                            "nominal_value": 10.0,
                            "unit": "g",
                            "tolerance_type": "absolute",
                            "tolerance_value": 0.01,
                        }
                    ),
                    fields.Command.create(
                        {
                            "sequence": 20,
                            "name": "Point 2",
                            "nominal_value": 100.0,
                            "unit": "g",
                            "tolerance_type": "absolute",
                            "tolerance_value": 0.01,
                        }
                    ),
                ],
            }
        )
        cls.plan.action_activate()

    @classmethod
    def _users_group_field(cls):
        """Return the name of the groups field of ``res.users``.

        The field is named ``groups_id`` up to Odoo 18. A rename to
        ``group_ids`` in Odoo 19 is reported by migration tooling but could
        not be verified from official documentation, therefore the field is
        resolved from the model at run time.

        :return: the technical name of the many2many field to ``res.groups``.
        """
        user_fields = cls.env["res.users"]._fields
        for field_name in ("groups_id", "group_ids"):
            if field_name in user_fields:
                return field_name
        raise AssertionError(
            "No many2many field to res.groups found on res.users."
        )

    @classmethod
    def _create_user(cls, login, group):
        """Create an internal user belonging to one calibration group.

        :param login: login and name of the created user.
        :param group: ``res.groups`` record to be assigned.
        :return: the created ``res.users`` record.
        """
        values = {
            "name": login,
            "login": login,
            "email": f"{login}@example.org",
            cls._users_group_field(): [
                fields.Command.set([cls.env.ref("base.group_user").id, group.id])
            ],
        }
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True, mail_create_nolog=True)
            .create(values)
        )

    @classmethod
    def _create_record(cls, values=None):
        """Create a calibration record with the test points of the plan.

        :param values: optional overrides of the record values.
        :return: the created ``ls.calibration.record`` record.
        """
        record_values = cls.plan._prepare_record_values()
        record_values.update(
            {
                "calibration_date": fields.Datetime.now(),
                "performed_by_id": cls.user_technician.id,
                "standard_ids": [fields.Command.set(cls.standard.ids)],
            }
        )
        record_values.update(values or {})
        return cls.env["ls.calibration.record"].create(record_values)

    @classmethod
    def _fill_readings(cls, record, as_found=None, as_left=None):
        """Set the as-found and as-left readings of every test point.

        :param record: calibration record to be completed.
        :param as_found: list of as-found readings, nominal values by default.
        :param as_left: list of as-left readings, as-found values by default.
        """
        lines = record.line_ids
        found = as_found or lines.mapped("nominal_value")
        left = as_left or found
        for line, found_value, left_value in zip(lines, found, left, strict=True):
            line.write(
                {"as_found_value": found_value, "as_left_value": left_value}
            )

    @classmethod
    def _months_later(cls, months):
        """Return the date shifted by a number of months from today.

        :param months: number of months to be added.
        :return: the resulting :class:`datetime.date`.
        """
        return cls.today + relativedelta(months=months)


# Backwards-compatible alias used by the calibration test modules.
CalibrationCommon = LsCalibrationCommon
