# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the batch production and control record."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestBatchRecord(LsPharmaCommon):
    """Exercise the record life cycle and the controls of 21 CFR 211.188."""

    def setUp(self):
        """Create a started batch and its record for each test."""
        super().setUp()
        self.batch = self._create_batch()
        self._add_components(self.batch)
        self.batch.with_user(self.production_manager).action_start()
        self.record = self._create_batch_record(self.batch)

    def test_reference_is_taken_from_the_sequence(self):
        """A new record receives a reference from its dedicated sequence."""
        self.assertTrue(self.record.name.startswith("EBR/"))

    def test_execution_requires_a_checked_master_record(self):
        """Execution cannot start before the master record has been checked.

        21 CFR 211.188(a) requires an accurate reproduction of the
        appropriate master production or control record, checked for accuracy,
        dated and signed.
        """
        record = self._create_batch_record(
            self.batch,
            master_checked_by_user_id=False,
            master_checked_date=False,
        )
        with self.assertRaises(UserError):
            record.with_user(self.operator).action_start_execution()

    def test_execution_completes_only_when_every_step_is_settled(self):
        """An unsettled step blocks the completion of the execution."""
        self._add_steps(self.record, count=3)
        self.record.with_user(self.operator).action_start_execution()
        with self.assertRaises(UserError):
            self.record.with_user(self.operator).action_complete_execution()

    def test_not_applicable_steps_do_not_block_completion(self):
        """A step marked as not applicable settles like a completed step."""
        steps = self._add_steps(self.record, count=2)
        self.record.with_user(self.operator).action_start_execution()
        steps[0].write(
            {
                "state": "done",
                "performed_by_user_id": self.operator.id,
                "checked_by_user_id": self.second_operator.id,
                "date_performed": "2026-01-06 10:00:00",
            }
        )
        steps[1].remark = "Not applicable: single-strength batch."
        steps[1].action_not_applicable()
        self.record.with_user(self.operator).action_complete_execution()
        self.assertEqual(self.record.state, "completed")

    def test_reviewer_cannot_be_the_executor(self):
        """The quality unit review is performed by a different user.

        21 CFR 211.192 places the review with the quality control unit, which
        is independent of the person who executed the record.
        """
        self._add_steps(self.record)
        self.record.with_user(self.operator).action_start_execution()
        self._complete_steps(self.record, self.operator)
        self.record.with_user(self.operator).action_complete_execution()
        self.record.with_user(self.production_manager).action_submit_review()
        with self.assertRaises(UserError):
            self.record.with_user(self.operator).action_approve()
        self.record.with_user(self.qa_user).action_approve()
        self.assertEqual(self.record.state, "approved")
        self.assertEqual(self.record.reviewed_by_user_id, self.qa_user)

    def test_open_discrepancy_blocks_approval(self):
        """An open discrepancy blocks the approval of the record.

        21 CFR 211.192 requires every unexplained discrepancy to be thoroughly
        investigated before release.
        """
        self._add_steps(self.record)
        self.record.with_user(self.operator).action_start_execution()
        self._complete_steps(self.record, self.operator)
        discrepancy = self.env["ls.pharma.batch_record.discrepancy"].create(
            {
                "record_id": self.record.id,
                "name": "Compression force excursion",
                "classification": "major",
                "description": "The compression force left its range.",
            }
        )
        self.record.with_user(self.operator).action_complete_execution()
        self.record.with_user(self.production_manager).action_submit_review()
        self.assertEqual(self.record.open_discrepancy_count, 1)
        with self.assertRaises(UserError):
            self.record.with_user(self.qa_user).action_approve()
        discrepancy.action_start_investigation()
        discrepancy.write(
            {
                "investigation": "Machine log reviewed against the setpoint.",
                "conclusion": "Transient sensor fault, product unaffected.",
                "follow_up": "Sensor replaced under maintenance order.",
                "investigated_by_user_id": self.qa_user.id,
            }
        )
        discrepancy.action_close()
        self.assertEqual(self.record.open_discrepancy_count, 0)
        self.record.with_user(self.qa_user).action_approve()
        self.assertEqual(self.record.state, "approved")

    def test_discrepancy_cannot_be_closed_without_a_conclusion(self):
        """A discrepancy needs a written conclusion before it is closed."""
        discrepancy = self.env["ls.pharma.batch_record.discrepancy"].create(
            {
                "record_id": self.record.id,
                "name": "Unexplained weight variation",
                "description": "Tablet weight drifted during compression.",
            }
        )
        discrepancy.action_start_investigation()
        with self.assertRaises(UserError):
            discrepancy.action_close()

    def test_numeric_control_conformity(self):
        """A numeric result outside its limits is not conform."""
        control = self.env["ls.pharma.batch_record.control"].create(
            {
                "record_id": self.record.id,
                "name": "Average mass",
                "control_type": "in_process",
                "result_type": "numeric",
                "has_minimum": True,
                "specification_min": 495.0,
                "has_maximum": True,
                "specification_max": 505.0,
                "result_value": 500.0,
                "result_uom": "mg",
            }
        )
        self.assertTrue(control.is_conform)
        control.result_value = 510.0
        self.assertFalse(control.is_conform)
        self.assertEqual(self.record.nonconforming_control_count, 1)

    def test_labeling_reconciliation(self):
        """Labelling quantities reconcile only when the difference is nil.

        21 CFR 211.125 requires reconciliation of the quantities of labelling
        issued, used and returned.
        """
        labeling = self.env["ls.pharma.batch_record.labeling"].create(
            {
                "record_id": self.record.id,
                "name": "Carton label",
                "label_version": "2.0",
                "quantity_issued": 1000.0,
                "quantity_used": 950.0,
                "quantity_returned": 40.0,
                "quantity_destroyed": 10.0,
            }
        )
        self.assertAlmostEqual(labeling.quantity_difference, 0.0, places=2)
        self.assertTrue(labeling.is_reconciled)
        labeling.quantity_destroyed = 5.0
        self.assertAlmostEqual(labeling.quantity_difference, 5.0, places=2)
        self.assertFalse(labeling.is_reconciled)
        self.assertEqual(self.record.unreconciled_label_count, 1)

    def test_line_clearance_before_and_after(self):
        """Both clearance moments can be recorded on one record.

        21 CFR 211.188(b)(6) requires the inspection of the packaging and
        labelling area before and after use.
        """
        clearances = self.env["ls.pharma.batch_record.clearance"].create(
            [
                {
                    "record_id": self.record.id,
                    "moment": "before",
                    "area": "Packaging line 2",
                    "performed_by_user_id": self.operator.id,
                    "verified_by_user_id": self.second_operator.id,
                    "result": "pass",
                },
                {
                    "record_id": self.record.id,
                    "moment": "after",
                    "area": "Packaging line 2",
                    "performed_by_user_id": self.operator.id,
                    "verified_by_user_id": self.second_operator.id,
                    "result": "pass",
                },
            ]
        )
        self.assertEqual(len(clearances), 2)
        self.assertEqual(
            set(self.record.clearance_ids.mapped("moment")),
            {"before", "after"},
        )

    def test_reserve_sample_count(self):
        """Reserve samples are counted separately from other samples.

        21 CFR 211.170 requires reserve samples to be retained.
        """
        self.env["ls.pharma.batch_record.sample"].create(
            [
                {
                    "record_id": self.record.id,
                    "name": "Reserve sample 1",
                    "sample_type": "reserve",
                    "quantity": 60.0,
                    "uom_id": self.uom.id,
                    "storage_location": "Reserve store A",
                    "retention_until": "2030-12-31",
                },
                {
                    "record_id": self.record.id,
                    "name": "In-process sample",
                    "sample_type": "in_process",
                    "quantity": 5.0,
                    "uom_id": self.uom.id,
                },
            ]
        )
        self.assertEqual(self.record.reserve_sample_count, 1)

    def test_completion_percentage(self):
        """The completion percentage follows the settled steps.

        With four steps of which two are done the percentage is
        2 / 4 * 100 = 50.
        """
        steps = self._add_steps(self.record, count=4)
        self.record.with_user(self.operator).action_start_execution()
        for step in steps[:2]:
            step.write(
                {
                    "state": "done",
                    "performed_by_user_id": self.operator.id,
                    "checked_by_user_id": self.second_operator.id,
                    "date_performed": "2026-01-06 10:00:00",
                }
            )
        self.assertEqual(self.record.step_count, 4)
        self.assertEqual(self.record.step_done_count, 2)
        self.assertAlmostEqual(
            self.record.completion_percentage, 50.0, places=2
        )

    def test_rejection_requires_a_conclusion(self):
        """A record cannot be rejected without a written conclusion."""
        self._add_steps(self.record)
        self.record.with_user(self.operator).action_start_execution()
        self._complete_steps(self.record, self.operator)
        self.record.with_user(self.operator).action_complete_execution()
        self.record.with_user(self.production_manager).action_submit_review()
        with self.assertRaises(UserError):
            self.record.with_user(self.qa_user).action_reject()
        self.record.review_conclusion = "Yield discrepancy unresolved."
        self.record.with_user(self.qa_user).action_reject()
        self.assertEqual(self.record.state, "rejected")
