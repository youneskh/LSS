# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Tests for the two-phase OOS/OOT investigation."""

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestLsLabOos(LsLabCommon):
    """Cover BRU-15, BRU-17 to BRU-21 and the investigation state machine."""

    def _failing_result(self):
        """Return a sample and a result that has failed its criterion."""
        specification = self._create_approved_specification()
        sample = self._create_sample(specification)
        sample.action_start()
        sample.action_start_testing()
        result = sample.result_ids[0]
        result.with_user(self.analyst).write({"result_numeric": 80.0})
        result.with_user(self.analyst).action_enter()
        return sample, result

    def test_investigation_raised_automatically(self):
        """A failing result raises an investigation with a reference (BRU-16)."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        self.assertTrue(investigation)
        self.assertIn("LAB/OOS/", investigation.name)
        self.assertEqual(investigation.state, "open")
        self.assertEqual(investigation.test_result_id, result)
        self.assertEqual(investigation.recorded_value, result.result_display)

    def test_phase1_requires_conclusion_and_findings(self):
        """Phase I cannot close without findings and a conclusion."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        investigation.with_user(self.reviewer).action_start_phase1()
        with self.assertRaises(UserError):
            investigation.with_user(self.reviewer).action_complete_phase1()
        investigation.write({"phase1_conclusion": "no_lab_error"})
        with self.assertRaises(UserError):
            investigation.with_user(self.reviewer).action_complete_phase1()
        investigation.write({"phase1_findings": "No laboratory error identified."})
        investigation.with_user(self.reviewer).action_complete_phase1()
        self.assertEqual(investigation.state, "phase1_done")
        self.assertEqual(investigation.phase1_completed_by_id, self.reviewer)

    def test_phase2_only_after_no_lab_error(self):
        """Phase II is unavailable when a laboratory cause was found (BRU-21)."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        investigation.with_user(self.reviewer).action_start_phase1()
        investigation.write({
            "phase1_conclusion": "lab_error_confirmed",
            "phase1_findings": "Dilution error identified and confirmed.",
        })
        investigation.with_user(self.reviewer).action_complete_phase1()
        with self.assertRaises(UserError):
            investigation.with_user(self.reviewer).action_start_phase2()

    def test_conclude_directly_when_lab_error(self):
        """A confirmed laboratory cause allows direct conclusion."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        investigation.with_user(self.reviewer).action_start_phase1()
        investigation.write({
            "phase1_conclusion": "lab_error_confirmed",
            "phase1_findings": "Transcription error confirmed against raw data.",
        })
        investigation.with_user(self.reviewer).action_complete_phase1()
        investigation.with_user(self.reviewer).action_conclude()
        self.assertEqual(investigation.state, "concluded")

    def test_retest_requires_justification(self):
        """Retest authorisation without a justification is refused (BRU-18)."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        investigation.with_user(self.reviewer).action_start_phase1()
        with self.assertRaises(UserError):
            investigation.with_user(self.manager).action_authorise_retest()
        investigation.write({
            "retest_justification": "Retest of the original sample by a second analyst.",
        })
        investigation.with_user(self.manager).action_authorise_retest()
        self.assertTrue(investigation.retest_authorised)
        self.assertEqual(investigation.retest_authorised_by_id, self.manager)
        self.assertTrue(investigation.retest_authorisation_date)

    def test_retest_result_blocked_without_authorisation(self):
        """A retest result cannot be created before authorisation (BRU-17)."""
        sample, result = self._failing_result()
        investigation = result.oos_id
        with self.assertRaises(UserError):
            self.env["ls.lab.test_result"].create({
                "sample_id": sample.id,
                "specification_line_id": result.specification_line_id.id,
                "is_retest": True,
                "oos_id": investigation.id,
            })

    def test_retest_result_allowed_after_authorisation(self):
        """Once authorised, a retest result may be recorded."""
        sample, result = self._failing_result()
        investigation = result.oos_id
        investigation.with_user(self.reviewer).action_start_phase1()
        investigation.write({
            "retest_justification": "Authorised retest under the approved procedure.",
        })
        investigation.with_user(self.manager).action_authorise_retest()
        retest = self.env["ls.lab.test_result"].create({
            "sample_id": sample.id,
            "specification_line_id": result.specification_line_id.id,
            "is_retest": True,
            "oos_id": investigation.id,
            "retest_of_id": result.id,
        })
        self.assertTrue(retest.exists())
        self.assertIn(retest, investigation.retest_result_ids)

    def test_close_requires_conclusion_and_disposition(self):
        """Closure demands both a conclusion and a disposition (BRU-19)."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        investigation.with_user(self.reviewer).action_start_phase1()
        investigation.write({
            "phase1_conclusion": "lab_error_confirmed",
            "phase1_findings": "Confirmed laboratory cause.",
        })
        investigation.with_user(self.reviewer).action_complete_phase1()
        investigation.with_user(self.reviewer).action_conclude()
        with self.assertRaises(UserError):
            investigation.with_user(self.manager).action_close()
        investigation.write({"final_conclusion": "assignable_lab_cause"})
        with self.assertRaises(UserError):
            investigation.with_user(self.manager).action_close()
        investigation.write({"product_disposition": "release"})
        investigation.with_user(self.manager).action_close()
        self.assertEqual(investigation.state, "closed")
        self.assertEqual(investigation.qa_approver_id, self.manager)

    def test_investigator_cannot_close_own_investigation(self):
        """The investigator may not approve closure (BRU-20)."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        investigation.write({"investigator_id": self.reviewer.id})
        investigation.with_user(self.reviewer).action_start_phase1()
        investigation.write({
            "phase1_conclusion": "lab_error_confirmed",
            "phase1_findings": "Confirmed laboratory cause.",
            "final_conclusion": "assignable_lab_cause",
            "product_disposition": "release",
        })
        investigation.with_user(self.reviewer).action_complete_phase1()
        investigation.with_user(self.reviewer).action_conclude()
        with self.assertRaises(UserError):
            investigation.with_user(self.reviewer).action_close()

    def test_qa_approver_segregation_constraint(self):
        """The approver and investigator cannot be the same user (BRU-20)."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        with self.assertRaises(ValidationError):
            investigation.write({
                "investigator_id": self.manager.id,
                "qa_approver_id": self.manager.id,
            })

    def test_sample_cannot_be_approved_with_open_investigation(self):
        """An open investigation blocks sample approval (BRU-15)."""
        sample, result = self._failing_result()
        result.with_user(self.reviewer).action_review()
        sample.action_record_results()
        sample.with_user(self.reviewer).action_review()
        with self.assertRaises(UserError):
            sample.with_user(self.manager).action_approve()

    def test_investigation_cannot_be_deleted(self):
        """Investigations are never deletable."""
        _sample, result = self._failing_result()
        with self.assertRaises(UserError):
            result.oos_id.unlink()

    def test_cancel_requires_reason(self):
        """Cancelling an investigation demands a reason."""
        _sample, result = self._failing_result()
        investigation = result.oos_id
        with self.assertRaises(UserError):
            investigation.with_user(self.manager).action_cancel()
        investigation.write({"cancel_reason": "Raised in error against the wrong sample."})
        investigation.with_user(self.manager).action_cancel()
        self.assertEqual(investigation.state, "cancelled")
