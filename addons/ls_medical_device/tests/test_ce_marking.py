# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the CE marking and declaration of conformity record."""

from datetime import date, timedelta

from freezegun import freeze_time

from psycopg2 import errors as pg_errors

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import MedicalDeviceCommon


@tagged("post_install", "-at_install")
class TestCeMarking(MedicalDeviceCommon):
    """Behaviour of ``ls.md.ce_marking``."""

    def setUp(self):
        """Create a draft CE marking record."""
        super().setUp()
        self.marking = self.env["ls.md.ce_marking"].create(
            {
                "device_id": self.device_iia.id,
                "conformity_route": "annex_ix",
                "notified_body_id": self.notified_body.id,
                "scope": "Scope recorded for the test.",
            }
        )

    def test_notified_body_required_for_notified_route(self):
        """A route involving a notified body requires one to be recorded.

        A draft may be saved without it; the submission is refused.
        """
        marking = self.env["ls.md.ce_marking"].create(
            {
                "device_id": self.device_iia.id,
                "conformity_route": "annex_ix",
            }
        )
        with self.assertRaises(ValidationError):
            marking.with_user(self.user_regulatory).action_submit()

    def test_self_declaration_without_notified_body(self):
        """A self-declared route does not require a notified body."""
        marking = self.env["ls.md.ce_marking"].create(
            {
                "device_id": self.device_i.id,
                "conformity_route": "self_declaration",
            }
        )
        self.assertFalse(marking.notified_body_id)

    def test_validity_order_enforced(self):
        """An expiry date preceding the issue date is rejected."""
        with self.assertRaises(pg_errors.CheckViolation):
            self.marking.write(
                {
                    "issue_date": date(2026, 6, 1),
                    "expiry_date": date(2026, 1, 1),
                }
            )
            self.marking.flush_recordset()

    def test_workflow_to_valid(self):
        """A record moves from draft through submission to valid."""
        marking = self.marking.with_user(self.user_regulatory)
        marking.action_submit()
        self.assertEqual(marking.state, "submitted")
        marking.write(
            {
                "certificate_number": "TEST-CERT-0001",
                "issue_date": date.today(),
                "expiry_date": date.today() + timedelta(days=365),
            }
        )
        marking.action_mark_issued()
        self.assertEqual(marking.state, "issued")
        marking.action_activate()
        self.assertEqual(marking.state, "valid")

    def test_plain_user_cannot_activate(self):
        """A plain user cannot move a certificate to the valid status."""
        marking = self.marking.with_user(self.user_user)
        with self.assertRaises(UserError):
            marking.action_submit()

    def test_expiry_flags(self):
        """A certificate past its expiry date is flagged as expired."""
        marking = self.marking.with_user(self.user_regulatory)
        marking.action_submit()
        marking.write(
            {
                "certificate_number": "TEST-CERT-0002",
                "issue_date": date.today() - timedelta(days=800),
                "expiry_date": date.today() - timedelta(days=1),
            }
        )
        marking.action_mark_issued()
        marking.invalidate_recordset()
        self.assertTrue(marking.is_expired)
        self.assertLess(marking.days_to_expiry, 0)

    def test_certificate_number_unique(self):
        """Two records cannot share a certificate number."""
        marking = self.marking.with_user(self.user_regulatory)
        marking.action_submit()
        marking.write({"certificate_number": "TEST-CERT-UNIQUE"})
        marking.flush_recordset()
        other = self.env["ls.md.ce_marking"].create(
            {
                "device_id": self.device_iii.id,
                "conformity_route": "annex_ix",
                "notified_body_id": self.notified_body.id,
            }
        )
        with self.assertRaises(pg_errors.UniqueViolation):
            other.write({"certificate_number": "TEST-CERT-UNIQUE"})
            other.flush_recordset()

    def test_active_certificate_selected_on_device(self):
        """The device points at its issued or valid certificate."""
        marking = self.marking.with_user(self.user_regulatory)
        marking.action_submit()
        marking.write(
            {
                "certificate_number": "TEST-CERT-0003",
                "issue_date": date.today(),
                "expiry_date": date.today() + timedelta(days=365),
            }
        )
        marking.action_mark_issued()
        self.device_iia.invalidate_recordset()
        self.assertEqual(self.device_iia.active_ce_marking_id, self.marking)

    def test_cron_expires_certificates(self):
        """The scheduled job moves expired certificates to the expired state."""
        marking = self.marking.with_user(self.user_regulatory)
        marking.action_submit()
        marking.write(
            {
                "certificate_number": "TEST-CERT-0004",
                "issue_date": date.today() - timedelta(days=800),
                "expiry_date": date.today() + timedelta(days=1),
            }
        )
        marking.action_mark_issued()
        # An expired certificate cannot be activated: activate it while it is
        # valid, then run the job three days later.
        marking.action_activate()
        with freeze_time(date.today() + timedelta(days=3)):
            self.env["ls.md.ce_marking"]._cron_expire_certificates()
        marking.invalidate_recordset()
        self.assertEqual(marking.state, "expired")
