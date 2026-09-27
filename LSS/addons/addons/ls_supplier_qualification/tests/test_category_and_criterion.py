# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the configuration models."""
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestConfiguration(SupplierQualificationCommon):
    """Validate the configuration models and their constraints."""

    def test_category_counts_dossiers(self):
        """The category counter reflects the dossiers attached to it."""
        self.category_no_audit.invalidate_recordset(["qualification_count"])
        self.assertEqual(self.category_no_audit.qualification_count, 1)

    def test_category_rejects_non_positive_interval(self):
        """A requalification interval must be strictly positive."""
        with self.assertRaises(ValidationError):
            self.category_no_audit.requalification_interval_months = 0

    def test_category_periodic_audit_requires_interval(self):
        """Requiring periodic audits requires a positive audit interval."""
        with self.assertRaises(ValidationError):
            self.category_no_audit.write({
                "requires_periodic_audit": True,
                "audit_interval_months": 0,
            })

    def test_criterion_display_name(self):
        """A criterion is displayed as code followed by its wording."""
        self.assertEqual(
            self.criterion_mandatory.display_name,
            "TST-M1 - Test mandatory criterion",
        )

    def test_criterion_weight_must_be_positive(self):
        """A criterion default weight must be strictly positive."""
        with self.assertRaises(ValidationError):
            self.criterion_optional.default_weight = 0

    def test_template_thresholds_must_be_ordered(self):
        """The conditional threshold cannot exceed the pass threshold."""
        with self.assertRaises(ValidationError):
            self.template.conditional_threshold = 95.0

    def test_template_mandatory_min_within_scale(self):
        """The minimum mandatory score must fit inside the scale."""
        with self.assertRaises(ValidationError):
            self.template.mandatory_min_score = 9

    def test_template_copy_suffixes_identifiers(self):
        """Duplicating a template produces a distinct name and code."""
        copy = self.template.copy()
        self.assertNotEqual(copy.code, self.template.code)
        self.assertEqual(len(copy.line_ids), len(self.template.line_ids))

    def test_standard_display_name(self):
        """A standard is displayed as code followed by its designation."""
        standard = self.env.ref("ls_supplier_qualification.standard_iso_9001")
        self.assertEqual(standard.display_name, "ISO9001 - ISO 9001:2015")
