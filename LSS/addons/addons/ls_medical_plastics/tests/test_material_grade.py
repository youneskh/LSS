# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the material grade register."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestMaterialGrade(MedicalPlasticsCommon):
    """Qualification workflow and constraints of material grades."""

    def test_display_name_includes_code(self):
        """The display name shows the internal code and the grade name."""
        self.assertEqual(self.grade.display_name, "[PP-MF12] PP Homopolymer MF-12")

    def test_code_must_be_unique_per_company(self):
        """Two grades cannot share an internal code within one company."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.mp.material.grade"].create(
                {"name": "Duplicate", "code": "PP-MF12", "polymer_type": "pp"}
            )

    def test_recycled_content_bounded(self):
        """Recycled content outside 0 to 100 is rejected."""
        with self.assertRaises(pg_errors.CheckViolation):
            self.env["ls.mp.material.grade"].create(
                {
                    "name": "Out of range",
                    "code": "PP-OOR",
                    "polymer_type": "pp",
                    "recycled_content": 150.0,
                }
            )

    def test_qualified_requires_date(self):
        """A grade cannot be qualified without a qualification date."""
        grade = self.env["ls.mp.material.grade"].create(
            {"name": "No Date", "code": "PP-ND", "polymer_type": "pp"}
        )
        with self.assertRaises(ValidationError):
            grade.write({"qualification_state": "qualified"})

    def test_action_qualify_stamps_date(self):
        """Qualifying through the action stamps today's date automatically."""
        grade = self.env["ls.mp.material.grade"].create(
            {"name": "Auto Date", "code": "PP-AD", "polymer_type": "pp"}
        )
        grade.action_qualify()
        self.assertEqual(grade.qualification_state, "qualified")
        self.assertTrue(grade.qualification_date)

    def test_conditional_qualification_requires_note(self):
        """Conditional qualification requires the conditions to be recorded."""
        grade = self.env["ls.mp.material.grade"].create(
            {"name": "Conditional", "code": "PP-CND", "polymer_type": "pp"}
        )
        with self.assertRaises(ValidationError):
            grade.action_qualify_conditionally()
        grade.qualification_note = "Pending extractables data from supplier."
        grade.action_qualify_conditionally()
        self.assertEqual(grade.qualification_state, "conditionally_qualified")

    def test_requalification_cannot_precede_qualification(self):
        """The requalification date must not precede the qualification date."""
        with self.assertRaises(ValidationError):
            self.grade.write({"requalification_date": "2025-01-01"})

    def test_invalid_transition_rejected(self):
        """Rejecting an already qualified grade is refused."""
        with self.assertRaises(ValidationError):
            self.grade.action_reject()

    def test_obsolete_then_reset(self):
        """A grade can be made obsolete and later returned to draft."""
        self.grade.action_set_obsolete()
        self.assertEqual(self.grade.qualification_state, "obsolete")
        self.grade.action_reset_to_draft()
        self.assertEqual(self.grade.qualification_state, "draft")

    def test_component_count(self):
        """The component counter reflects the components using the grade."""
        self.assertEqual(self.grade.component_count, 1)
