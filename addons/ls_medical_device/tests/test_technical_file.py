# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the technical documentation record and its sections."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestTechnicalFile(MedicalDeviceCommon):
    """Behaviour of ``ls.md.technical_file``."""

    def setUp(self):
        """Create a draft technical documentation record."""
        super().setUp()
        self.technical_file = self.env["ls.md.technical_file"].create(
            {
                "title": "Technical Documentation Under Test",
                "device_id": self.device_iia.id,
                "annex_reference": "annex_ii",
                "responsible_id": self.user_second.id,
            }
        )

    def test_sections_seeded_from_template(self):
        """Creating a record seeds the sections from the shipped template."""
        self.assertTrue(self.technical_file.section_ids)
        self.assertEqual(
            self.technical_file.section_count,
            len(self.technical_file.section_ids),
        )

    def test_completeness_starts_at_zero(self):
        """No section is complete on a newly created record."""
        self.assertEqual(self.technical_file.complete_section_count, 0)
        self.assertEqual(self.technical_file.completeness_ratio, 0.0)

    def test_completeness_ratio_between_zero_and_one(self):
        """The completeness ratio is expressed as a value between 0 and 1."""
        sections = self.technical_file.section_ids
        sections[0].write(
            {"is_complete": True, "evidence_reference": "TEST-EVIDENCE"}
        )
        self.technical_file.invalidate_recordset()
        ratio = self.technical_file.completeness_ratio
        self.assertGreater(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)

    def test_missing_mandatory_counted(self):
        """Incomplete mandatory sections are counted."""
        mandatory = self.technical_file.section_ids.filtered("is_mandatory")
        self.assertEqual(
            self.technical_file.missing_mandatory_count, len(mandatory)
        )

    def test_not_applicable_requires_justification(self):
        """Declaring a section not applicable requires a justification."""
        section = self.technical_file.section_ids[0]
        with self.assertRaises(ValidationError):
            section.write({"not_applicable": True})

    def test_not_applicable_with_justification_accepted(self):
        """A justified not-applicable section is accepted."""
        section = self.technical_file.section_ids[0]
        section.write(
            {
                "not_applicable": True,
                "not_applicable_justification": "Not applicable for the test.",
            }
        )
        self.assertTrue(section.not_applicable)

    def test_sections_locked_after_submission(self):
        """Sections can no longer be edited once the record leaves draft."""
        for section in self.technical_file.section_ids:
            section.write(
                {
                    "is_complete": True,
                    "evidence_reference": "TEST-EVIDENCE",
                }
            )
        self.technical_file.action_submit_for_review()
        with self.assertRaises(UserError):
            self.technical_file.section_ids[0].write({"is_complete": False})

    def test_version_unique_per_device_and_annex(self):
        """A version is unique for one device and one annex."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.md.technical_file"].create(
                {
                    "title": "Duplicate",
                    "device_id": self.device_iia.id,
                    "annex_reference": "annex_ii",
                    "version": self.technical_file.version,
                }
            )
            self.env["ls.md.technical_file"].flush_model()

    def test_approval_workflow(self):
        """A complete record can be submitted and approved."""
        for section in self.technical_file.section_ids:
            section.write(
                {"is_complete": True, "evidence_reference": "TEST-EVIDENCE"}
            )
        self.technical_file.action_submit_for_review()
        self.technical_file.with_user(self.user_regulatory).action_approve()
        self.assertEqual(self.technical_file.state, "approved")

    def test_plain_user_cannot_approve(self):
        """A plain user cannot approve technical documentation."""
        for section in self.technical_file.section_ids:
            section.write(
                {"is_complete": True, "evidence_reference": "TEST-EVIDENCE"}
            )
        self.technical_file.action_submit_for_review()
        with self.assertRaises(UserError):
            self.technical_file.with_user(self.user_user).action_approve()

    def test_complete_requires_evidence_reference(self):
        """A section cannot be complete without an evidence reference."""
        section = self.technical_file.section_ids[0]
        with self.assertRaises(UserError):
            section.write({"is_complete": True})
