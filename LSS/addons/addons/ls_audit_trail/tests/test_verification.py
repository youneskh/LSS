# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Verification tests: tampering is detected, and detection is recorded."""

from odoo.tests import tagged

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestVerification(AuditTrailCase):
    """Verify that the integrity check reports what it is meant to report."""

    def setUp(self):
        """Record a short chain in a company of its own."""
        super().setUp()
        self.probe_company = self.env["res.company"].create({"name": "Verify co"})
        self._activate_rule(
            field_ids=self.field_name.ids, company_id=self.probe_company.id
        )
        self.partners = self.env["res.partner"].with_company(
            self.probe_company
        ).create(
            [
                {"name": f"Verify {index}", "company_id": self.probe_company.id}
                for index in range(4)
            ]
        )
        self.entries = self.log_model.sudo().search(
            [("company_id", "=", self.probe_company.id)],
            order="sequence_number asc",
        )
        self.assertEqual(len(self.entries), 4)

    def test_intact_chain_passes(self):
        """An untouched chain verifies without findings."""
        outcome = self.log_model.sudo()._ls_verify_chain(self.probe_company)
        self.assertTrue(outcome["passed"])
        self.assertEqual(outcome["checked"], 4)
        self.assertFalse(outcome["first_failure_id"])

    def test_altered_value_is_detected(self):
        """Changing a stored value with SQL breaks the payload digest."""
        line = self.entries[1].line_ids[0]
        self.env.cr.execute(
            "UPDATE ls_audit_trail_log_line SET new_value_technical = %s WHERE id = %s",
            ("tampered", line.id),
        )
        self.env.invalidate_all()
        outcome = self.log_model.sudo()._ls_verify_chain(self.probe_company)
        self.assertFalse(outcome["passed"])
        self.assertEqual(
            outcome["first_failure_sequence"], self.entries[1].sequence_number
        )

    def test_altered_attribution_is_detected(self):
        """Changing the recorded login with SQL breaks the payload digest."""
        self.env.cr.execute(
            "UPDATE ls_audit_trail_log SET user_login = %s WHERE id = %s",
            ("someone.else", self.entries[2].id),
        )
        self.env.invalidate_all()
        outcome = self.log_model.sudo()._ls_verify_chain(self.probe_company)
        self.assertFalse(outcome["passed"])
        self.assertEqual(
            outcome["first_failure_sequence"], self.entries[2].sequence_number
        )

    def test_removed_entry_is_detected(self):
        """Deleting an entry from the middle with SQL breaks continuity."""
        removed = self.entries[1]
        self.env.cr.execute(
            "DELETE FROM ls_audit_trail_log WHERE id = %s", (removed.id,)
        )
        self.env.invalidate_all()
        outcome = self.log_model.sudo()._ls_verify_chain(self.probe_company)
        self.assertFalse(outcome["passed"])

    def test_undocumented_head_truncation_is_detected(self):
        """Removing the head of a chain without an anchor is reported."""
        self.env.cr.execute(
            "DELETE FROM ls_audit_trail_log WHERE id = %s", (self.entries[0].id,)
        )
        self.env.invalidate_all()
        outcome = self.log_model.sudo()._ls_verify_chain(self.probe_company)
        self.assertFalse(outcome["passed"])
        self.assertIn("unaccounted", outcome["details"])

    def test_empty_range_is_reported_rather_than_failed(self):
        """A range containing no entry is not a failure."""
        empty_company = self.env["res.company"].create({"name": "No entries co"})
        outcome = self.log_model.sudo()._ls_verify_chain(empty_company)
        self.assertTrue(outcome["passed"])
        self.assertEqual(outcome["checked"], 0)

    def test_verification_record_captures_the_outcome(self):
        """Running a verification writes an immutable record of the outcome."""
        verification = self.env["ls.audit_trail.verification"].sudo()._ls_run(
            company=self.probe_company, source="manual"
        )
        self.assertEqual(verification.result, "passed")
        self.assertEqual(verification.entries_checked, 4)
        self.assertEqual(verification.company_id, self.probe_company)
        self.assertEqual(verification.source, "manual")

    def test_failed_verification_is_recorded_as_failed(self):
        """A detected divergence is recorded, not raised away."""
        self.env.cr.execute(
            "UPDATE ls_audit_trail_log SET res_name = %s WHERE id = %s",
            ("tampered", self.entries[3].id),
        )
        self.env.invalidate_all()
        verification = self.env["ls.audit_trail.verification"].sudo()._ls_run(
            company=self.probe_company, source="manual"
        )
        self.assertEqual(verification.result, "failed")
        self.assertTrue(verification.details)

    def test_wizard_runs_a_verification(self):
        """The wizard produces the same evidence as the scheduled action."""
        wizard = self.env["ls.audit_trail.verify.wizard"].with_user(
            self.user_auditor
        ).create({"company_id": self.probe_company.id, "scope": "full"})
        action = wizard.action_verify()
        verification = self.env["ls.audit_trail.verification"].sudo().browse(
            action["res_id"]
        )
        self.assertEqual(verification.result, "passed")

    def test_wizard_estimates_the_scope(self):
        """The wizard reports how many entries a run would verify."""
        wizard = self.env["ls.audit_trail.verify.wizard"].sudo().create(
            {"company_id": self.probe_company.id, "scope": "full"}
        )
        self.assertEqual(wizard.entry_estimate, 4)

    def test_scheduled_action_runs_for_every_company(self):
        """The scheduled action records one verification per company."""
        before = self.env["ls.audit_trail.verification"].sudo().search_count([])
        self.log_model.sudo()._ls_cron_verify_chain()
        after = self.env["ls.audit_trail.verification"].sudo().search_count([])
        companies = self.env["res.company"].sudo().search_count([])
        self.assertEqual(after - before, companies)

    def test_payload_excludes_nothing_that_matters(self):
        """Every immutable business column of an entry is inside the payload."""
        payload = self.entries[0]._ls_payload()
        for key in (
            "sequence_number",
            "company_id",
            "entry_type",
            "event_datetime",
            "user_id",
            "user_login",
            "model_name",
            "res_id",
            "operation",
            "lines",
        ):
            with self.subTest(key=key):
                self.assertIn(key, payload)
        self.assertEqual(payload["entry_type"], constants.ENTRY_TYPE_DATA)
