# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for the ls.complaint.investigation model."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestInvestigation(TestLsComplaintCommon):
    """Verify the investigation state machine and its controls."""

    def setUp(self):
        """Create a complaint already in the Investigation state."""
        super().setUp()
        self.complaint = self._create_complaint()
        self._bring_to_investigation(self.complaint)
        self.investigation = self.complaint.investigation_ids

    def test_01_sequence_and_display_name(self):
        """The investigation gets a reference and a qualified display name."""
        self.assertTrue(self.investigation.name.startswith("CMP/INV/"))
        self.assertIn(self.complaint.name, self.investigation.display_name)

    def test_02_company_is_inherited(self):
        """The company is inherited from the parent complaint."""
        self.assertEqual(self.investigation.company_id, self.complaint.company_id)

    def test_03_complete_requires_analysis_data(self):
        """Completion is refused while the analysis is incomplete."""
        self.investigation.action_start()
        with self.assertRaises(UserError):
            self.investigation.action_complete()

    def test_04_root_cause_description_required(self):
        """A determined root cause requires a description."""
        self.investigation.action_start()
        self.investigation.write(
            {
                "methodology": "ishikawa",
                "investigation_summary": "Summary",
                "root_cause_category": "material",
                "conclusion": "confirmed",
            }
        )
        with self.assertRaises(UserError):
            self.investigation.action_complete()
        self.investigation.root_cause_description = "Out of specification excipient."
        self.investigation.action_complete()
        self.assertEqual(self.investigation.state, "completed")

    def test_05_not_determined_needs_no_description(self):
        """An undetermined root cause does not require a description."""
        self.investigation.action_start()
        self.investigation.write(
            {
                "methodology": "is_is_not",
                "investigation_summary": "Summary",
                "root_cause_category": "not_determined",
                "conclusion": "inconclusive",
            }
        )
        self.investigation.action_complete()
        self.assertEqual(self.investigation.state, "completed")

    def test_06_approval_segregation_of_duties(self):
        """The investigator cannot approve his own investigation."""
        self.investigation.investigator_id = self.user_investigator
        self._prepare_completed()
        with self.assertRaises(UserError):
            self.investigation.with_user(self.user_investigator).action_approve()
        self.investigation.with_user(self.user_reviewer).action_approve()
        self.assertEqual(self.investigation.state, "approved")
        self.assertEqual(self.investigation.approved_by_id, self.user_reviewer)

    def test_07_approver_constraint(self):
        """The stored approver cannot equal the investigator."""
        investigation = self.env["ls.complaint.investigation"].create(
            {
                "complaint_id": self.complaint.id,
                "investigator_id": self.user_investigator.id,
            }
        )
        with self.assertRaises(ValidationError):
            investigation.write({"approved_by_id": self.user_investigator.id})

    def test_08_reject_requires_reason(self):
        """Rejection without a documented reason is refused."""
        self._prepare_completed()
        with self.assertRaises(UserError):
            self.investigation.action_reject()
        self.investigation.rejection_reason = "Insufficient evidence."
        self.investigation.action_reject()
        self.assertEqual(self.investigation.state, "rejected")

    def test_09_finalised_investigation_is_frozen(self):
        """An approved investigation can no longer be modified."""
        self._prepare_completed()
        self.investigation.with_user(self.user_reviewer).action_approve()
        with self.assertRaises(UserError):
            self.investigation.investigation_summary = "Tampered"

    def test_10_unlink_guard(self):
        """A started investigation cannot be deleted."""
        self.investigation.action_start()
        with self.assertRaises(UserError):
            self.investigation.unlink()

    def test_11_date_consistency(self):
        """A completion date earlier than the start date is refused."""
        self.investigation.action_start()
        with self.assertRaises(ValidationError):
            self.investigation.write(
                {"date_completed": self.investigation.date_started.replace(year=2000)}
            )

    def test_12_other_methodology_requires_description(self):
        """'Other Methodology' without a description is refused."""
        self.investigation.action_start()
        with self.assertRaises(ValidationError):
            self.investigation.methodology = "other"

    def test_13_wrong_state_transition(self):
        """A transition from a wrong state raises a user error."""
        with self.assertRaises(UserError):
            self.investigation.action_complete()
        with self.assertRaises(UserError):
            self.investigation.action_approve()

    def _prepare_completed(self):
        """Bring the investigation to the Completed state."""
        self.investigation.action_start()
        self.investigation.write(
            {
                "methodology": "five_whys",
                "investigation_summary": "Summary",
                "root_cause_category": "machine",
                "root_cause_description": "Worn tooling.",
                "conclusion": "confirmed",
            }
        )
        self.investigation.action_complete()
