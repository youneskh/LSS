# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the SQL and Python constraints of the calibration module."""

from contextlib import contextmanager

import psycopg2

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import LsCalibrationCommon

CONSTRAINT_ERRORS = (psycopg2.IntegrityError, ValidationError)


@tagged("post_install", "-at_install")
class TestLsCalibrationConstraints(LsCalibrationCommon):
    """Data integrity rules enforced by the database and by Python.

    The database constraints are declared with ``models.Constraint``. The
    exception raised on violation is a ``psycopg2.IntegrityError`` when the
    check reaches PostgreSQL and a ``ValidationError`` when the ORM rejects
    the value beforehand, therefore both are accepted by the assertions.
    """

    @contextmanager
    def _assert_constraint_violation(self):
        """Assert that the enclosed block violates a constraint.

        ``assertRaises`` of the Odoo test case accepts a single exception
        class, not a tuple, so the two accepted exceptions are caught here.
        The block runs inside a savepoint, which is rolled back on failure.
        """
        try:
            with self.cr.savepoint():
                yield
        except CONSTRAINT_ERRORS:
            return
        self.fail("The constraint was not enforced.")

    @mute_logger("odoo.sql_db")
    def test_instrument_code_is_unique(self):
        """Two instruments of a company cannot share a reference."""
        with self._assert_constraint_violation():
            self.env["ls.calibration.instrument"].create(
                {"name": "Duplicate", "code": self.instrument.code}
            )

    @mute_logger("odoo.sql_db")
    def test_instrument_range_consistency(self):
        """The maximum of the range cannot precede its minimum."""
        with self._assert_constraint_violation():
            self.env["ls.calibration.instrument"].create(
                {"name": "Invalid range", "range_min": 10.0, "range_max": 1.0}
            )

    @mute_logger("odoo.sql_db")
    def test_instrument_alert_lead_days_positive(self):
        """The alert lead time cannot be negative."""
        with self._assert_constraint_violation():
            self.env["ls.calibration.instrument"].create(
                {"name": "Invalid lead time", "alert_lead_days": -1}
            )

    @mute_logger("odoo.sql_db")
    def test_plan_interval_is_positive(self):
        """The calibration interval must be strictly positive."""
        with self._assert_constraint_violation():
            self.env["ls.calibration.plan"].create(
                {
                    "instrument_id": self.instrument.id,
                    "interval_number": 0,
                    "interval_uom": "month",
                    "start_date": self.today,
                }
            )

    @mute_logger("odoo.sql_db")
    def test_plan_point_tolerance_is_positive(self):
        """The tolerance of a test point cannot be negative."""
        with self._assert_constraint_violation():
            self.env["ls.calibration.plan.point"].create(
                {
                    "plan_id": self.plan.id,
                    "name": "Negative tolerance",
                    "nominal_value": 1.0,
                    "tolerance_value": -1.0,
                }
            )

    @mute_logger("odoo.sql_db")
    def test_record_reference_is_unique(self):
        """Two calibration records cannot share a reference."""
        record = self._create_record()
        with self._assert_constraint_violation():
            self.env["ls.calibration.record"].create(
                {"instrument_id": self.instrument.id, "name": record.name}
            )

    def test_record_plan_belongs_to_instrument(self):
        """A record cannot reference the plan of another instrument."""
        other_instrument = self.env["ls.calibration.instrument"].create(
            {"name": "Other instrument"}
        )
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.record"].create(
                {
                    "instrument_id": other_instrument.id,
                    "plan_id": self.plan.id,
                }
            )

    def test_record_standard_is_not_the_instrument(self):
        """An instrument cannot calibrate itself."""
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.record"].create(
                {
                    "instrument_id": self.instrument.id,
                    "standard_ids": [fields.Command.set(self.instrument.ids)],
                }
            )

    def test_certificate_validity_dates(self):
        """The validity end date cannot precede the issue date."""
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.certificate"].create(
                {
                    "instrument_id": self.instrument.id,
                    "issue_date": self.today,
                    "valid_until": self._months_later(-1),
                }
            )

    def test_certificate_record_belongs_to_instrument(self):
        """A certificate cannot reference a record of another instrument."""
        record = self._create_record()
        other_instrument = self.env["ls.calibration.instrument"].create(
            {"name": "Other instrument"}
        )
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.certificate"].create(
                {
                    "instrument_id": other_instrument.id,
                    "record_id": record.id,
                }
            )

    def test_certificate_workflow(self):
        """The certificate life cycle follows its state machine."""
        certificate = self.env["ls.calibration.certificate"].create(
            {"instrument_id": self.instrument.id}
        )
        self.assertTrue(certificate.name.startswith("CERT/"))
        self.assertEqual(certificate.state, "draft")
        certificate.action_issue()
        self.assertEqual(certificate.state, "issued")
        with self.assertRaises(UserError):
            certificate.action_issue()
        with self.assertRaises(UserError):
            certificate.write({"issue_date": self.today})
        with self.assertRaises(UserError):
            certificate.unlink()
        certificate.action_supersede()
        self.assertEqual(certificate.state, "superseded")
        with self.assertRaises(UserError):
            certificate.action_supersede()

    def test_external_certificate_requires_document(self):
        """An external certificate must carry its document before issue."""
        certificate = self.env["ls.calibration.certificate"].create(
            {
                "instrument_id": self.instrument.id,
                "issuer_type": "external",
                "issuer_partner_id": self.env.user.partner_id.id,
            }
        )
        with self.assertRaises(UserError):
            certificate.action_issue()
        certificate.write(
            {
                "certificate_file": b"dGVzdA==",
                "certificate_filename": "certificate.pdf",
            }
        )
        certificate.action_issue()
        self.assertEqual(certificate.state, "issued")

    def test_certificate_onchange_record(self):
        """Selecting a record aligns the instrument of the certificate."""
        record = self._create_record()
        certificate = self.env["ls.calibration.certificate"].new(
            {"record_id": record.id}
        )
        certificate._onchange_record_id()
        self.assertEqual(certificate.instrument_id, self.instrument)

    def test_certificate_copy(self):
        """A duplicated certificate restarts in the draft state."""
        certificate = self.env["ls.calibration.certificate"].create(
            {"instrument_id": self.instrument.id}
        )
        certificate.action_issue()
        duplicate = certificate.copy()
        self.assertEqual(duplicate.state, "draft")
        self.assertNotEqual(duplicate.name, certificate.name)
