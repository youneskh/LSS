# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the Common Technical Document dossier."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestCtd(LsPharmaCommon):
    """Exercise the dossier life cycle and the shipped section template."""

    def setUp(self):
        """Create a draft dossier for each test."""
        super().setUp()
        self.dossier = self.env["ls.pharma.ctd_dossier"].create(
            {
                "title": "Marketing authorisation, tablet 500 mg",
                "product_id": self.product.id,
                "dossier_type": "new",
                "authority_name": "National competent authority",
                "dossier_version": "1.0",
            }
        )

    def test_reference_is_taken_from_the_sequence(self):
        """A new dossier receives a reference from its dedicated sequence."""
        self.assertTrue(self.dossier.name.startswith("CTD/"))

    def test_template_sections_are_installed(self):
        """The shipped template covers the five modules of ICH M4(R4)."""
        templates = self.env["ls.pharma.ctd.section"].search(
            [("is_template", "=", True)]
        )
        self.assertTrue(templates)
        self.assertEqual(
            sorted(set(templates.mapped("module"))),
            ["1", "2", "3", "4", "5"],
        )
        codes = set(templates.mapped("code"))
        for code in ("1.1", "2.3", "3.2.S.1.1", "3.2.P.8.3", "4.2", "5.3"):
            self.assertIn(code, codes)

    def test_template_sections_have_no_dossier(self):
        """A template section is never attached to a dossier."""
        templates = self.env["ls.pharma.ctd.section"].search(
            [("is_template", "=", True)]
        )
        self.assertFalse(templates.mapped("dossier_id"))

    def test_loading_the_template_populates_the_dossier(self):
        """Loading the structure copies every template section once."""
        templates = self.env["ls.pharma.ctd.section"].search_count(
            [("is_template", "=", True)]
        )
        created = self.dossier.action_load_template()
        self.assertEqual(len(created), templates)
        self.assertEqual(self.dossier.section_count, templates)
        self.assertFalse(any(self.dossier.section_ids.mapped("is_template")))

    def test_loading_the_template_twice_creates_no_duplicate(self):
        """A second load adds nothing, because the codes already exist."""
        self.dossier.action_load_template()
        first_count = self.dossier.section_count
        second = self.dossier.action_load_template()
        self.assertEqual(len(second), 0)
        self.assertEqual(self.dossier.section_count, first_count)

    def test_completion_percentage(self):
        """The completion percentage follows the completed sections."""
        self.env["ls.pharma.ctd.section"].create(
            [
                {
                    "dossier_id": self.dossier.id,
                    "module": "3",
                    "code": "3.2.S.1.1",
                    "name": "Nomenclature",
                    "document_reference": "DOC-001",
                },
                {
                    "dossier_id": self.dossier.id,
                    "module": "3",
                    "code": "3.2.S.1.2",
                    "name": "Structure",
                    "document_reference": "DOC-002",
                },
            ]
        )
        self.assertEqual(self.dossier.section_count, 2)
        self.assertAlmostEqual(
            self.dossier.completion_percentage, 0.0, places=2
        )
        self.dossier.section_ids[0].action_mark_complete()
        self.assertAlmostEqual(
            self.dossier.completion_percentage, 50.0, places=2
        )

    def test_section_needs_a_document_before_it_is_ready(self):
        """A section cannot be declared ready without a document reference."""
        section = self.env["ls.pharma.ctd.section"].create(
            {
                "dossier_id": self.dossier.id,
                "module": "2",
                "code": "2.3",
                "name": "Quality Overall Summary",
            }
        )
        section.action_start()
        self.assertEqual(section.state, "in_preparation")
        with self.assertRaises(UserError):
            section.action_mark_ready()
        section.document_reference = "QOS-2026-01"
        section.action_mark_ready()
        self.assertEqual(section.state, "ready")

    def test_dossier_life_cycle(self):
        """A dossier walks from draft to approved."""
        section = self.env["ls.pharma.ctd.section"].create(
            {
                "dossier_id": self.dossier.id,
                "module": "1",
                "code": "1.1",
                "name": "Table of Contents of the Submission",
                "document_reference": "TOC-001",
            }
        )
        self.dossier.action_start_preparation()
        self.assertEqual(self.dossier.state, "in_preparation")
        with self.assertRaises(UserError):
            self.dossier.action_mark_ready()
        section.action_start()
        section.action_mark_ready()
        self.dossier.action_mark_ready()
        self.assertEqual(self.dossier.state, "ready")
        self.dossier.action_submit()
        self.assertEqual(self.dossier.state, "submitted")
        self.assertTrue(self.dossier.date_submission)
        self.assertEqual(section.state, "submitted")

    def test_approval_requires_an_authorisation_number(self):
        """A dossier cannot be approved without an authorisation number."""
        self._submit_dossier()
        with self.assertRaises(UserError):
            self.dossier.action_approve()
        self.dossier.authorisation_number = "MA-2026-0001"
        self.dossier.action_approve()
        self.assertEqual(self.dossier.state, "approved")
        self.assertTrue(self.dossier.date_decision)

    def test_deficiency_can_be_recorded_after_submission(self):
        """A deficiency is recorded on a submitted dossier."""
        self._submit_dossier()
        self.dossier.action_record_deficiency()
        self.assertEqual(self.dossier.state, "deficiency")

    def test_submitted_dossier_cannot_be_deleted(self):
        """A submitted dossier can no longer be deleted."""
        self._submit_dossier()
        with self.assertRaises(UserError):
            self.dossier.unlink()

    def test_deficiency_section_needs_a_description(self):
        """A section in deficiency must describe the deficiency."""
        section = self.env["ls.pharma.ctd.section"].create(
            {
                "dossier_id": self.dossier.id,
                "module": "3",
                "code": "3.2.P.5.1",
                "name": "Specifications",
            }
        )
        with self.assertRaises(UserError):
            section.write({"state": "deficiency"})
        section.write(
            {
                "state": "deficiency",
                "deficiency_note": "The assay limits need justification.",
            }
        )
        self.assertEqual(section.state, "deficiency")

    def _submit_dossier(self):
        """Drive the dossier to the submitted state."""
        section = self.env["ls.pharma.ctd.section"].create(
            {
                "dossier_id": self.dossier.id,
                "module": "1",
                "code": "1.1",
                "name": "Table of Contents of the Submission",
                "document_reference": "TOC-001",
            }
        )
        self.dossier.action_start_preparation()
        section.action_start()
        section.action_mark_ready()
        self.dossier.action_mark_ready()
        self.dossier.action_submit()
