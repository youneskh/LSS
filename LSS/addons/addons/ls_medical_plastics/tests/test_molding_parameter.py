# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for moulding parameter specifications and segregation of duties."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestMoldingParameter(MedicalPlasticsCommon):
    """Versioning, approval workflow and separation of responsibilities."""

    def test_fixture_specification_is_approved(self):
        """The fixture specification completes the approval workflow."""
        self.assertEqual(self.spec.state, "approved")
        self.assertEqual(self.spec.version, 1)
        self.assertTrue(self.spec.effective_date)
        self.assertEqual(self.spec.parameter_count, 3)
        self.assertEqual(self.spec.critical_parameter_count, 2)

    def test_reference_assigned_from_sequence(self):
        """The specification receives a reference from the sequence."""
        self.assertTrue(self.spec.name)
        self.assertNotEqual(self.spec.name, "New")

    def test_author_cannot_review(self):
        """The author of a specification may not review it."""
        spec = self._new_draft_spec()
        spec.with_user(self.user_engineer).action_submit_for_review()
        with self.assertRaises(ValidationError):
            spec.with_user(self.user_engineer).action_review()

    def test_author_cannot_approve(self):
        """The author of a specification may not approve it."""
        spec = self._new_draft_spec()
        spec.with_user(self.user_engineer).action_submit_for_review()
        spec.with_user(self.user_engineer_reviewer).action_review()
        with self.assertRaises(ValidationError):
            spec.with_user(self.user_engineer).action_approve()

    def test_technician_cannot_review_a_specification(self):
        """Reviewing a specification requires the engineer role."""
        spec = self._new_draft_spec()
        spec.with_user(self.user_engineer).action_submit_for_review()
        with self.assertRaises(AccessError):
            spec.with_user(self.user_technician).action_review()

    def test_reviewer_cannot_approve(self):
        """The reviewer of a specification may not also approve it."""
        spec = self._new_draft_spec()
        spec.with_user(self.user_engineer).action_submit_for_review()
        spec.with_user(self.user_manager).action_review()
        with self.assertRaises(ValidationError):
            spec.with_user(self.user_manager).action_approve()

    def test_approval_requires_prior_review(self):
        """A specification cannot be approved before it is reviewed."""
        spec = self._new_draft_spec()
        spec.with_user(self.user_engineer).action_submit_for_review()
        with self.assertRaises(ValidationError):
            spec.with_user(self.user_manager).action_approve()

    def test_submit_requires_parameters(self):
        """A specification without parameters cannot be submitted."""
        spec = self.env["ls.mp.molding_parameter"].with_user(self.user_engineer).create(
            {"component_id": self.component.id, "tool_id": self.tool.id}
        )
        with self.assertRaises(ValidationError):
            spec.with_user(self.user_engineer).action_submit_for_review()

    def test_only_one_approved_specification(self):
        """A second approved specification for the same context is refused."""
        spec = self._new_draft_spec()
        spec.with_user(self.user_engineer).action_submit_for_review()
        spec.with_user(self.user_engineer_reviewer).action_review()
        spec.with_user(self.user_manager).action_approve()
        self.assertEqual(self.spec.state, "superseded")
        self.assertEqual(spec.state, "approved")

    def test_new_version_copies_parameters(self):
        """Creating a new version copies the parameter lines."""
        action = self.spec.action_create_new_version()
        new_spec = self.env["ls.mp.molding_parameter"].browse(action["res_id"])
        self.assertEqual(new_spec.version, 2)
        self.assertEqual(new_spec.state, "draft")
        self.assertEqual(new_spec.previous_version_id, self.spec)
        self.assertEqual(len(new_spec.line_ids), len(self.spec.line_ids))

    def test_version_two_requires_change_reason(self):
        """From version 2 onwards a reason for change is mandatory."""
        action = self.spec.action_create_new_version()
        new_spec = self.env["ls.mp.molding_parameter"].browse(action["res_id"])
        with self.assertRaises(ValidationError):
            new_spec.write({"change_reason": False})

    def test_tool_must_produce_component(self):
        """A specification cannot cite a tool that does not make the component."""
        other_tool = self.env["ls.mp.tool"].create(
            {"name": "Unrelated Tool", "cavity_count": 1}
        )
        with self.assertRaises(ValidationError):
            self.env["ls.mp.molding_parameter"].create(
                {"component_id": self.component.id, "tool_id": other_tool.id}
            )

    def test_numeric_range_must_contain_target(self):
        """A parameter target outside its own range is refused."""
        with self.assertRaises(ValidationError):
            self.env["ls.mp.molding_parameter.line"].create(
                {
                    "spec_id": self.spec.id,
                    "name": "Bad Range",
                    "code": "BAD",
                    "parameter_uom": "bar",
                    "value_type": "numeric",
                    "min_value": 10.0,
                    "target_value": 50.0,
                    "max_value": 20.0,
                }
            )

    def test_qualitative_requires_expected_value(self):
        """A qualitative parameter must declare its expected value."""
        with self.assertRaises(ValidationError):
            self.env["ls.mp.molding_parameter.line"].create(
                {
                    "spec_id": self.spec.id,
                    "name": "Appearance",
                    "code": "APP",
                    "parameter_uom": "n/a",
                    "value_type": "qualitative",
                }
            )

    def test_critical_parameter_must_be_recorded(self):
        """A critical parameter cannot have recording disabled."""
        with self.assertRaises(ValidationError):
            self.env["ls.mp.molding_parameter.line"].create(
                {
                    "spec_id": self.spec.id,
                    "name": "Critical Unrecorded",
                    "code": "CRIT-U",
                    "parameter_uom": "bar",
                    "min_value": 1.0,
                    "target_value": 2.0,
                    "max_value": 3.0,
                    "is_critical": True,
                    "record_required": False,
                }
            )

    def test_parameter_code_unique_per_specification(self):
        """Parameter codes cannot repeat within one specification."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.mp.molding_parameter.line"].create(
                {
                    "spec_id": self.spec.id,
                    "name": "Duplicate Code",
                    "code": "MELT-T",
                    "parameter_uom": "degC",
                    "min_value": 1.0,
                    "target_value": 2.0,
                    "max_value": 3.0,
                }
            )

    def test_evaluate_value_numeric(self):
        """Numeric evaluation respects the declared range."""
        line = self.spec.line_ids.filtered(lambda item: item.code == "MELT-T")
        self.assertTrue(line._evaluate_value(220.0, False))
        self.assertFalse(line._evaluate_value(250.0, False))

    def test_approved_specification_cannot_be_deleted(self):
        """An approved specification cannot be deleted.

        The manager holds the delete right, so the refusal comes from the
        state rule and not from the access rights.
        """
        with self.assertRaises(ValidationError):
            self.spec.with_user(self.user_manager).unlink()

    def test_obsolete_blocked_by_open_run(self):
        """A specification used by an open run cannot be made obsolete."""
        run = self._create_run()
        run.action_start_setup()
        with self.assertRaises(ValidationError):
            self.spec.action_set_obsolete()

    def test_cron_specification_review_runs(self):
        """The scheduled review check executes without error."""
        self.spec.write({"review_interval_months": 1})
        self.assertTrue(
            self.env["ls.mp.molding_parameter"]._cron_check_specification_review()
        )

    def _new_draft_spec(self):
        """Create a second draft specification for the fixture context.

        :rtype: recordset of ``ls.mp.molding_parameter``
        """
        return self.env["ls.mp.molding_parameter"].with_user(self.user_engineer).create(
            {
                "component_id": self.component.id,
                "tool_id": self.tool.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Melt Temperature",
                            "code": "MELT-T",
                            "parameter_uom": "degC",
                            "value_type": "numeric",
                            "min_value": 212.0,
                            "target_value": 222.0,
                            "max_value": 232.0,
                            "is_critical": True,
                            "monitoring_frequency": "per_startup",
                        },
                    )
                ],
            }
        )
