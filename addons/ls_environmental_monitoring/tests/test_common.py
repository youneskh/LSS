# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixture for the database-backed tests."""

from odoo.tests.common import TransactionCase, new_test_user

MANAGER_GROUP = "ls_environmental_monitoring.group_ls_env_manager"
TECHNICIAN_GROUP = "ls_environmental_monitoring.group_ls_env_technician"
VIEWER_GROUP = "ls_environmental_monitoring.group_ls_env_viewer"


class EnvMonitoringCommon(TransactionCase):
    """Base fixture providing a configured monitoring programme.

    Users are created with ``new_test_user`` and group membership is asserted
    with ``has_group``. Neither depends on the name of the field that links a
    user to its groups, which could not be verified for Odoo 19.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.manager = new_test_user(
            cls.env, login="em_manager", groups=MANAGER_GROUP)
        cls.technician = new_test_user(
            cls.env, login="em_technician", groups=TECHNICIAN_GROUP)
        cls.second_technician = new_test_user(
            cls.env, login="em_technician2", groups=TECHNICIAN_GROUP)
        # Limits and plans are authored by managers only (the technician role
        # records samples and results). A second manager authors the fixtures
        # so that ``cls.manager`` can approve them without approving its own
        # record.
        cls.author = new_test_user(
            cls.env, login="em_author", groups=MANAGER_GROUP)
        cls.viewer = new_test_user(
            cls.env, login="em_viewer", groups=VIEWER_GROUP)

        cls.grade = cls.env["ls.env.grade"].create(
            {"name": "Test Grade", "code": "TG"})
        cls.area = cls.env["ls.env.area"].create(
            {"name": "Filling Room", "code": "FR01", "grade_id": cls.grade.id})
        cls.child_area = cls.env["ls.env.area"].create(
            {"name": "Filling Zone", "code": "FR01Z", "parent_id": cls.area.id})

        cls.parameter_count = cls.env["ls.env.parameter"].create(
            {
                "name": "Settle Plate",
                "code": "SP",
                "parameter_type": "viable_air_passive",
                "result_type": "quantitative",
                "uom_label": "CFU/plate",
                "incubation_required": True,
            }
        )
        cls.parameter_qualitative = cls.env["ls.env.parameter"].create(
            {
                "name": "Surface Swab Outcome",
                "code": "SWB",
                "parameter_type": "viable_surface",
                "result_type": "qualitative",
            }
        )
        cls.parameter_temperature = cls.env["ls.env.parameter"].create(
            {
                "name": "Temperature",
                "code": "TEMP",
                "parameter_type": "temperature",
                "result_type": "quantitative",
                "uom_label": "degC",
            }
        )

        cls.method = cls.env["ls.env.method"].create(
            {
                "name": "Settle Plate 4h",
                "code": "M-SP4",
                "parameter_id": cls.parameter_count.id,
                "exposure_duration_minutes": 240,
            }
        )

        cls.point = cls.env["ls.env.sampling_point"].create(
            {
                "name": "Filling Head",
                "code": "SP-001",
                "area_id": cls.area.id,
                "is_critical": True,
            }
        )
        cls.point_two = cls.env["ls.env.sampling_point"].create(
            {"name": "Room Centre", "code": "SP-002", "area_id": cls.area.id}
        )

    @classmethod
    def _approve_limit(cls, limit):
        """Approve a limit as the manager, respecting the author check."""
        return limit.with_user(cls.manager).action_approve()

    @classmethod
    def _create_limit(cls, point, parameter, **overrides):
        """Create a draft limit authored by the second manager.

        Authoring as ``cls.author`` allows ``cls.manager`` to approve it without
        tripping the rule that an approver must differ from the author.
        """
        values = {
            "sampling_point_id": point.id,
            "parameter_id": parameter.id,
            "occupancy_state": "any",
            "direction": "upper",
            "action_set": True,
            "action_value": 10.0,
            "justification": "Derived from historical data review.",
        }
        values.update(overrides)
        return cls.env["ls.env.limit"].with_user(cls.author).create(values)

    def _create_sample(self, point=None, parameters=None, **overrides):
        """Create a draft sample with one result line per parameter."""
        point = point or self.point
        parameters = parameters or [self.parameter_count]
        values = {
            "sampling_point_id": point.id,
            "occupancy_state": "in_operation",
            "result_ids": [
                (0, 0, {"parameter_id": parameter.id})
                for parameter in parameters
            ],
        }
        values.update(overrides)
        return self.env["ls.env.sample"].create(values)
