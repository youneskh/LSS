# Part of the Life Sciences Suite. See LICENSE file for full copyright and licensing details.
"""Tests for stability studies and time points."""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LsLabCommon


@tagged("post_install", "-at_install")
class TestLsLabStability(LsLabCommon):
    """Cover BRU-24, BRU-25, BRU-27 and BRU-29."""

    def _create_study(self, start_date="2026-01-15"):
        """Return a draft study carrying three time points."""
        return self.env["ls.lab.stability_study"].create({
            "product_id": self.product.id,
            "storage_condition_id": self.storage_condition.id,
            "study_type": "long_term",
            "start_date": start_date,
            "timepoint_ids": [
                (0, 0, {"name": "Initial", "interval_months": 0, "sequence": 10}),
                (0, 0, {"name": "3 months", "interval_months": 3, "sequence": 20}),
                (0, 0, {"name": "6 months", "interval_months": 6, "sequence": 30}),
            ],
        })

    def test_sequence_assigned_on_create(self):
        """A study receives a reference from the sequence."""
        study = self._create_study()
        self.assertIn("LAB/STB/", study.name)
        self.assertEqual(study.state, "draft")

    def test_scheduled_dates_derive_from_start_date(self):
        """Time point dates are the start date plus the interval (BRU-25)."""
        study = self._create_study(start_date="2026-01-15")
        by_name = {tp.name: tp for tp in study.timepoint_ids}
        self.assertEqual(by_name["Initial"].scheduled_date, date(2026, 1, 15))
        self.assertEqual(by_name["3 months"].scheduled_date, date(2026, 4, 15))
        self.assertEqual(by_name["6 months"].scheduled_date, date(2026, 7, 15))

    def test_scheduled_dates_recompute_when_start_moves(self):
        """Changing the start date moves every derived due date."""
        study = self._create_study(start_date="2026-01-15")
        study.write({"start_date": "2026-02-15"})
        by_name = {tp.name: tp for tp in study.timepoint_ids}
        self.assertEqual(by_name["3 months"].scheduled_date, date(2026, 5, 15))

    def test_study_without_timepoints_cannot_be_approved(self):
        """A study with no time point cannot be approved."""
        study = self.env["ls.lab.stability_study"].create({
            "product_id": self.product.id,
            "storage_condition_id": self.storage_condition.id,
        })
        with self.assertRaises(UserError):
            study.with_user(self.manager).action_approve()

    def test_start_requires_start_date(self):
        """A study cannot start without a start date."""
        study = self._create_study(start_date=False)
        study.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            study.with_user(self.reviewer).action_start()

    def test_pull_wizard_creates_stability_sample(self):
        """The pull wizard creates a linked stability sample (BRU-24)."""
        specification = self._create_approved_specification(spec_type="stability")
        study = self._create_study()
        study.write({"specification_id": specification.id})
        study.with_user(self.manager).action_approve()
        study.with_user(self.reviewer).action_start()
        timepoint = study.timepoint_ids[0]

        wizard = self.env["ls.lab.stability_pull_wizard"].create({
            "timepoint_id": timepoint.id,
            "specification_id": specification.id,
            "pull_date": "2026-01-16",
        })
        wizard.action_confirm()

        self.assertEqual(timepoint.state, "sampled")
        self.assertTrue(timepoint.sample_id)
        self.assertEqual(timepoint.sample_id.sample_type, "stability")
        self.assertEqual(timepoint.sample_id.stability_timepoint_id, timepoint)
        self.assertTrue(timepoint.sample_id.result_ids)

    def test_pull_refused_when_study_not_ongoing(self):
        """No pull sample can be created from a study that has not started."""
        specification = self._create_approved_specification(spec_type="stability")
        study = self._create_study()
        timepoint = study.timepoint_ids[0]
        wizard = self.env["ls.lab.stability_pull_wizard"].create({
            "timepoint_id": timepoint.id,
            "specification_id": specification.id,
            "pull_date": "2026-01-16",
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_missed_timepoint_requires_notes(self):
        """Recording a missed time point demands notes (BRU-27)."""
        study = self._create_study()
        timepoint = study.timepoint_ids[0]
        with self.assertRaises(UserError):
            timepoint.with_user(self.manager).action_mark_missed()
        timepoint.write({"notes": "Sample unavailable; deviation raised."})
        timepoint.with_user(self.manager).action_mark_missed()
        self.assertEqual(timepoint.state, "missed")

    def test_study_completion_blocked_by_outstanding_timepoint(self):
        """A study cannot complete while a time point remains planned."""
        study = self._create_study()
        study.with_user(self.manager).action_approve()
        study.with_user(self.reviewer).action_start()
        with self.assertRaises(UserError):
            study.with_user(self.manager).action_complete()

    def test_termination_requires_reason(self):
        """Early termination demands a recorded reason."""
        study = self._create_study()
        study.with_user(self.manager).action_approve()
        with self.assertRaises(UserError):
            study.with_user(self.manager).action_terminate()
        study.write({"termination_reason": "Batch withdrawn from the market."})
        study.with_user(self.manager).action_terminate()
        self.assertEqual(study.state, "terminated")

    def test_timepoint_cron_does_not_change_state(self):
        """The due-time-point notice never mutates a state (BRU-29)."""
        study = self._create_study(start_date="2020-01-15")
        study.with_user(self.manager).action_approve()
        study.with_user(self.reviewer).action_start()
        states_before = study.timepoint_ids.mapped("state")
        self.env["ls.lab.stability_study"]._cron_notify_due_timepoints()
        self.assertEqual(study.timepoint_ids.mapped("state"), states_before)
        self.assertEqual(study.state, "ongoing")

    def test_no_storage_condition_shipped(self):
        """The module ships no storage condition data of its own."""
        shipped = self.env["ir.model.data"].search([
            ("module", "=", "ls_lab"),
            ("model", "=", "ls.lab.storage_condition"),
        ])
        self.assertFalse(
            shipped,
            "No storage condition may be shipped: guideline values are "
            "configuration owned by the implementing organisation.",
        )
