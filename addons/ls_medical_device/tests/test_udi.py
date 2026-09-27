# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the UDI assignment record."""

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestUdi(MedicalDeviceCommon):
    """Behaviour of ``ls.md.udi``."""

    def setUp(self):
        """Create a draft UDI assignment used by the tests."""
        super().setUp()
        self.udi = self.env["ls.md.udi"].create(
            {
                "device_id": self.device_iia.id,
                "udi_kind": "udi_di",
                "udi_di": "TEST-UDI-DI-0001",
                "issuing_entity": "gs1",
                "packaging_level": "primary",
                "quantity_per_package": 1,
                "carrier_type": "2d",
            }
        )

    def test_identifier_unique(self):
        """Two assignments cannot share the same identifier."""
        with self.assertRaises(pg_errors.UniqueViolation):
            self.env["ls.md.udi"].create(
                {
                    "device_id": self.device_iii.id,
                    "udi_kind": "udi_di",
                    "udi_di": "TEST-UDI-DI-0001",
                    "issuing_entity": "gs1",
                    "packaging_level": "primary",
                }
            )
            self.env["ls.md.udi"].flush_model()

    def test_assign_then_publish(self):
        """A draft identifier can be assigned and then published."""
        self.udi.action_assign()
        self.assertEqual(self.udi.state, "assigned")
        self.assertTrue(self.udi.assignment_date)
        self.udi.write(
            {
                "database_name": "EUDAMED",
                "database_submission_date": self.udi.assignment_date,
            }
        )
        self.udi.action_publish()
        self.assertEqual(self.udi.state, "published")

    def test_publish_requires_assigned(self):
        """A draft identifier cannot be published directly."""
        with self.assertRaises(UserError):
            self.udi.action_publish()

    def test_quantity_must_be_positive(self):
        """A non-positive package quantity is rejected."""
        with self.assertRaises(pg_errors.CheckViolation):
            self.udi.write({"quantity_per_package": 0})
            self.udi.flush_recordset()

    def test_other_issuing_entity_requires_note(self):
        """Selecting the open issuing entity requires an explanatory note."""
        with self.assertRaises(ValidationError):
            self.env["ls.md.udi"].create(
                {
                    "device_id": self.device_iia.id,
                    "udi_kind": "udi_di",
                    "udi_di": "TEST-UDI-DI-OTHER",
                    "issuing_entity": "other",
                    "packaging_level": "primary",
                }
            )

    def test_mark_obsolete(self):
        """An assigned identifier can be marked obsolete with a reason."""
        self.udi.action_assign()
        self.udi.write({"obsolete_reason": "Superseded by a new identifier."})
        self.udi.action_mark_obsolete()
        self.assertEqual(self.udi.state, "obsolete")

    def test_pi_component_summary_computed(self):
        """The production identifier summary reflects the selected flags."""
        self.udi.write({"pi_lot_number": True, "pi_expiry_date": True})
        self.assertTrue(self.udi.pi_component_summary)

    def test_reset_to_draft(self):
        """An assigned identifier can be returned to the draft status."""
        self.udi.action_assign()
        self.udi.action_reset_to_draft()
        self.assertEqual(self.udi.state, "draft")
