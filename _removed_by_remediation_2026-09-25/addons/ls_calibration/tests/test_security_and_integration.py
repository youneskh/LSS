# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of access rights, wizards, certificates and module integrity."""

from dateutil.relativedelta import relativedelta

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .common import CalibrationCommon


@tagged("post_install", "-at_install")
class TestCalibrationSecurity(CalibrationCommon):
    """Group membership and access-right enforcement."""

    def test_viewer_cannot_create_a_record(self):
        """A viewer has no create right on calibration records."""
        with self.assertRaises(AccessError):
            self.env["ls.calibration.record"].with_user(
                self.user_viewer
            ).create(
                {
                    "instrument_id": self.instrument.id,
                    "scheduled_date": self.today,
                }
            )

    def test_viewer_can_read_a_record(self):
        """A viewer may read calibration records."""
        record = self._create_record()
        self.assertTrue(record.with_user(self.user_viewer).read(["name"]))

    def test_technician_cannot_create_master_data(self):
        """A technician cannot create instrument categories."""
        with self.assertRaises(AccessError):
            self.env["ls.calibration.instrument.category"].with_user(
                self.user_technician
            ).create({"name": "Unauthorised", "code": "UNAUTH"})

    def test_technician_cannot_create_reference_standards(self):
        """A technician cannot create reference standards."""
        with self.assertRaises(AccessError):
            self.env["ls.calibration.standard"].with_user(
                self.user_technician
            ).create(
                {
                    "name": "Unauthorised standard",
                    "code": "STD-UNAUTH",
                    "valid_until": self.today + relativedelta(months=6),
                }
            )

    def test_manager_can_create_master_data(self):
        """A manager may create master data."""
        category = self.env["ls.calibration.instrument.category"].with_user(
            self.user_manager
        ).create({"name": "Managed category", "code": "MGD"})
        self.assertTrue(category.id)

    def test_technician_cannot_delete_records(self):
        """A technician has no delete right on calibration records."""
        record = self._create_record()
        with self.assertRaises(AccessError):
            record.with_user(self.user_technician).unlink()

    def test_group_hierarchy_is_cumulative(self):
        """Each group implies the rights of the group below it."""
        self.assertTrue(
            self.user_manager.has_group(
                "ls_calibration.group_ls_calibration_approver"
            )
        )
        self.assertTrue(
            self.user_manager.has_group(
                "ls_calibration.group_ls_calibration_technician"
            )
        )
        self.assertTrue(
            self.user_approver.has_group(
                "ls_calibration.group_ls_calibration_viewer"
            )
        )
        self.assertFalse(
            self.user_technician.has_group(
                "ls_calibration.group_ls_calibration_approver"
            )
        )

    def test_certificate_cannot_be_deleted(self):
        """Certificates are never deletable, even by a manager."""
        record = self._create_record()
        self._perform_and_submit(record)
        record.with_user(self.user_approver).action_review()
        record.with_user(self.user_approver_two).action_approve()
        certificate = self.env["ls.calibration.certificate"].create(
            {
                "record_id": record.id,
                "certificate_type": "internal",
                "issue_date": self.today,
                "issuer_name": "Metrology function",
            }
        )
        with self.assertRaises(UserError):
            certificate.with_user(self.user_manager).unlink()


@tagged("post_install", "-at_install")
class TestCalibrationCertificate(CalibrationCommon):
    """Certificate issue rules."""

    def _approved_record(self):
        """Return an approved calibration record."""
        record = self._create_record()
        self._perform_and_submit(record)
        record.with_user(self.user_approver).action_review()
        record.with_user(self.user_approver_two).action_approve()
        return record

    def test_certificate_requires_approved_record(self):
        """A certificate cannot be attached to an unapproved calibration."""
        record = self._create_record()
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.certificate"].create(
                {
                    "record_id": record.id,
                    "certificate_type": "internal",
                    "issue_date": self.today,
                }
            )

    def test_number_drawn_from_sequence(self):
        """A certificate receives a number from the certificate sequence."""
        certificate = self.env["ls.calibration.certificate"].create(
            {
                "record_id": self._approved_record().id,
                "certificate_type": "internal",
                "issue_date": self.today,
            }
        )
        self.assertIn("CRT/", certificate.name)

    def test_external_certificate_requires_document(self):
        """An external certificate must carry the received document."""
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.certificate"].create(
                {
                    "record_id": self._approved_record().id,
                    "certificate_type": "external",
                    "issue_date": self.today,
                }
            )

    def test_issue_date_cannot_precede_calibration(self):
        """A certificate cannot be dated before the calibration."""
        record = self._approved_record()
        with self.assertRaises(ValidationError):
            self.env["ls.calibration.certificate"].create(
                {
                    "record_id": record.id,
                    "certificate_type": "internal",
                    "issue_date": self.today - relativedelta(days=1),
                }
            )

    def test_valid_until_mirrors_next_due(self):
        """The certificate validity mirrors the record's next due date."""
        record = self._approved_record()
        certificate = self.env["ls.calibration.certificate"].create(
            {
                "record_id": record.id,
                "certificate_type": "internal",
                "issue_date": self.today,
            }
        )
        self.assertEqual(certificate.valid_until, record.next_due_date)

    def test_printing_an_external_certificate_is_refused(self):
        """The internal certificate report does not apply to external ones."""
        record = self._approved_record()
        certificate = self.env["ls.calibration.certificate"].create(
            {
                "record_id": record.id,
                "certificate_type": "external",
                "issue_date": self.today,
                "document": b"ZmFrZSBjZXJ0aWZpY2F0ZQ==",
                "document_filename": "certificate.pdf",
            }
        )
        with self.assertRaises(UserError):
            certificate.action_print()


@tagged("post_install", "-at_install")
class TestCalibrationStandard(CalibrationCommon):
    """Reference standard validity and protection."""

    def test_validity_computed_from_expiry(self):
        """The validity flag follows the expiry date."""
        self.assertTrue(self.standard.is_valid)
        expired = self.env["ls.calibration.standard"].create(
            {
                "name": "Expired standard",
                "code": "STD-EXPIRED",
                "valid_until": self.today - relativedelta(days=1),
            }
        )
        self.assertFalse(expired.is_valid)

    def test_standard_in_use_cannot_be_deleted(self):
        """A standard cited by a record cannot be deleted."""
        self._create_record()
        with self.assertRaises(UserError):
            self.standard.unlink()

    def test_cron_refreshes_validity(self):
        """The scheduled action recomputes the stored validity flag."""
        self.assertTrue(
            self.env["ls.calibration.standard"]._cron_refresh_validity()
        )


@tagged("post_install", "-at_install")
class TestCalibrationWizards(CalibrationCommon):
    """Transient models."""

    def test_generate_wizard_creates_records(self):
        """The generation wizard creates records and returns an action."""
        self.plan.action_approve()
        wizard = self.env["ls.calibration.plan.generate"].create(
            {"horizon_date": self.today + relativedelta(years=2)}
        )
        action = wizard.action_generate()
        self.assertEqual(action["res_model"], "ls.calibration.record")
        self.assertEqual(wizard.generated_count, 3)

    def test_generate_wizard_without_matching_plan(self):
        """The wizard refuses to run when no approved plan matches."""
        wizard = self.env["ls.calibration.plan.generate"].create(
            {"horizon_date": self.today + relativedelta(years=1)}
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_generate_wizard_category_filter(self):
        """The category restriction excludes non-matching plans."""
        self.plan.action_approve()
        other_category = self.env["ls.calibration.instrument.category"].create(
            {"name": "Other", "code": "OTH"}
        )
        wizard = self.env["ls.calibration.plan.generate"].create(
            {
                "horizon_date": self.today + relativedelta(years=1),
                "category_id": other_category.id,
            }
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_generate_wizard_skips_retired_instruments(self):
        """Retired instruments are excluded from generation."""
        self.plan.action_approve()
        self.instrument.action_take_out_of_service()
        self.instrument.action_retire()
        wizard = self.env["ls.calibration.plan.generate"].create(
            {"horizon_date": self.today + relativedelta(years=1)}
        )
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_reject_wizard_applies_reason(self):
        """The rejection wizard stores the reason on the record."""
        record = self._create_record()
        self._perform_and_submit(record)
        wizard = self.env["ls.calibration.record.reject"].with_user(
            self.user_approver
        ).create(
            {"record_id": record.id, "reason": "Standard out of calibration"}
        )
        wizard.action_confirm()
        self.assertEqual(record.state, "rejected")
        self.assertEqual(
            record.rejection_reason, "Standard out of calibration"
        )

    def test_reject_wizard_rejects_blank_reason(self):
        """A blank rejection reason is refused."""
        record = self._create_record()
        self._perform_and_submit(record)
        wizard = self.env["ls.calibration.record.reject"].create(
            {"record_id": record.id, "reason": "    "}
        )
        with self.assertRaises(UserError):
            wizard.action_confirm()


@tagged("post_install", "-at_install")
class TestCalibrationInstallation(CalibrationCommon):
    """Integrity of the shipped data and metadata."""

    def test_all_models_are_registered(self):
        """Every model declared by the module exists in the registry."""
        expected = [
            "ls.calibration.instrument.category",
            "ls.calibration.instrument",
            "ls.calibration.point",
            "ls.calibration.standard",
            "ls.calibration.plan",
            "ls.calibration.record",
            "ls.calibration.reading",
            "ls.calibration.certificate",
            "ls.calibration.oot",
            "ls.calibration.plan.generate",
            "ls.calibration.record.reject",
        ]
        for model_name in expected:
            self.assertIn(model_name, self.env, model_name)

    def test_sequences_exist(self):
        """Every sequence code used by the module resolves."""
        for code in (
            "ls.calibration.instrument",
            "ls.calibration.record",
            "ls.calibration.certificate",
            "ls.calibration.oot",
        ):
            self.assertTrue(
                self.env["ir.sequence"].search([("code", "=", code)]),
                code,
            )

    def test_groups_exist(self):
        """Every security group referenced by the module resolves."""
        for xml_id in (
            "ls_calibration.group_ls_calibration_viewer",
            "ls_calibration.group_ls_calibration_technician",
            "ls_calibration.group_ls_calibration_approver",
            "ls_calibration.group_ls_calibration_manager",
        ):
            self.assertTrue(self.env.ref(xml_id), xml_id)

    def test_report_actions_exist(self):
        """Both QWeb report actions resolve."""
        for xml_id in (
            "ls_calibration.action_report_ls_calibration_certificate",
            "ls_calibration.action_report_ls_calibration_record",
        ):
            self.assertTrue(self.env.ref(xml_id), xml_id)

    def test_scheduled_actions_exist(self):
        """The scheduled actions resolve and target existing methods."""
        cron = self.env.ref(
            "ls_calibration.ir_cron_ls_calibration_refresh_status"
        )
        self.assertEqual(cron.model_id.model, "ls.calibration.instrument")
        self.assertTrue(
            hasattr(
                self.env["ls.calibration.instrument"],
                "_cron_refresh_calibration_status",
            )
        )

    def test_status_refresh_cron_runs(self):
        """The status refresh scheduled action executes without error."""
        self.assertTrue(
            self.env[
                "ls.calibration.instrument"
            ]._cron_refresh_calibration_status()
        )

    def test_notification_cron_runs(self):
        """The notification scheduled action executes without error."""
        self.instrument.next_due_date = self.today - relativedelta(days=1)
        self.instrument._compute_calibration_status()
        self.assertTrue(
            self.env[
                "ls.calibration.record"
            ]._cron_notify_upcoming_calibrations()
        )

    def test_multi_company_rules_are_global(self):
        """Every shipped record rule is global, by design."""
        rules = self.env["ir.rule"].search(
            [("model_id.model", "like", "ls.calibration%")]
        )
        self.assertTrue(rules)
        for rule in rules:
            self.assertIn("company_ids", rule.domain_force)
