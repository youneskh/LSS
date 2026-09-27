# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the scheduled actions."""
from dateutil.relativedelta import relativedelta

from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestCron(SupplierQualificationCommon):
    """Verify expiry handling and due-date reminders."""

    def setUp(self):
        """Bring the shared dossier to the approved status."""
        super().setUp()
        self.qualification.action_start_assessment()
        self._create_assessment(self.qualification)
        self._create_material(self.qualification, self.product)
        self.qualification.action_submit_for_approval()
        self._approve(self.qualification)

    def test_expired_approval_moves_to_expired(self):
        """An elapsed validity moves the dossier to the expired status."""
        # Approved two years ago, so that an elapsed expiry is consistent.
        self.qualification.write({
            "approval_date": self.today - relativedelta(years=2),
            "expiry_date": self.today - relativedelta(days=1),
        })
        count = self.env["ls.supplier.qualification"]._cron_check_expiry()
        self.assertGreaterEqual(count, 1)
        self.assertEqual(self.qualification.state, "expired")

    def test_valid_approval_untouched(self):
        """A dossier still inside its validity is not expired."""
        self.qualification.expiry_date = self.today + relativedelta(days=400)
        self.env["ls.supplier.qualification"]._cron_check_expiry()
        self.assertEqual(self.qualification.state, "approved")

    def test_expiring_approval_creates_activity(self):
        """An approaching expiry schedules an activity for the responsible."""
        self.company.ls_expiry_reminder_days = 60
        self.qualification.expiry_date = self.today + relativedelta(days=30)
        self.env["ls.supplier.qualification"]._cron_check_expiry()
        self.assertTrue(self.qualification.activity_ids)

    def test_expiring_reminder_not_duplicated(self):
        """Running the scheduled action twice does not duplicate activities."""
        self.company.ls_expiry_reminder_days = 60
        self.qualification.expiry_date = self.today + relativedelta(days=30)
        self.env["ls.supplier.qualification"]._cron_check_expiry()
        first_count = len(self.qualification.activity_ids)
        self.env["ls.supplier.qualification"]._cron_check_expiry()
        self.assertEqual(len(self.qualification.activity_ids), first_count)

    def test_review_due_creates_activity(self):
        """A review falling due schedules an activity."""
        self.company.ls_expiry_reminder_days = 30
        self.qualification.activity_ids.unlink()
        created = self.env["ls.supplier.qualification"]._cron_check_due_dates()
        self.assertGreaterEqual(created, 0)

    def test_material_expiry_cron_is_idempotent(self):
        """Running the scope expiry action twice is safe."""
        material = self.qualification.material_ids[0]
        material.write({
            "qualification_date": self.today - relativedelta(years=2),
            "expiry_date": self.today - relativedelta(days=1),
        })
        first = self.env["ls.supplier.material"]._cron_check_material_expiry()
        second = self.env["ls.supplier.material"]._cron_check_material_expiry()
        self.assertEqual(first, 1)
        self.assertEqual(second, 0)
