# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Access right and record rule tests."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import DeviationCommon


@tagged("post_install", "-at_install")
class TestDeviationSecurity(DeviationCommon):
    """Verify that each role holds exactly the intended privileges."""

    @mute_logger("odoo.addons.base.models.ir_model", "odoo.models")
    def test_viewer_cannot_create(self):
        """A viewer holds no create privilege."""
        with self.assertRaises(AccessError):
            self._create_deviation(env=self.env(user=self.user_viewer))

    @mute_logger("odoo.addons.base.models.ir_model", "odoo.models")
    def test_viewer_cannot_write(self):
        """A viewer holds no write privilege."""
        deviation = self._create_deviation()
        with self.assertRaises(AccessError):
            deviation.with_user(self.user_viewer).write({"title": "Edited"})

    def test_viewer_can_read(self):
        """A viewer can read deviations."""
        deviation = self._create_deviation()
        self.assertTrue(deviation.with_user(self.user_viewer).title)

    def test_reporter_can_create(self):
        """A reporter can record a deviation."""
        deviation = self._create_deviation(env=self.env(user=self.user_reporter))
        self.assertEqual(deviation.reporter_id, self.user_reporter)

    @mute_logger("odoo.addons.base.models.ir_model", "odoo.models")
    def test_reporter_cannot_write_foreign_record(self):
        """The reporter record rule excludes records owned by others."""
        deviation = self._create_deviation(
            reporter_id=self.user_manager.id, owner_id=self.user_manager.id
        )
        with self.assertRaises(AccessError):
            deviation.with_user(self.user_reporter).write({"title": "Edited"})

    def test_reporter_can_write_own_reported_record(self):
        """A reporter maintains their own record while it is Reported."""
        deviation = self._create_deviation(env=self.env(user=self.user_reporter))
        deviation.with_user(self.user_reporter).write({"title": "Corrected"})
        self.assertEqual(deviation.title, "Corrected")

    @mute_logger("odoo.addons.base.models.ir_model", "odoo.models")
    def test_reporter_cannot_write_after_assessment(self):
        """The reporter rule is limited to the Reported state."""
        deviation = self._create_deviation(
            reporter_id=self.user_reporter.id, owner_id=self.user_reporter.id
        )
        self._advance_to_assessed(deviation)
        with self.assertRaises(AccessError):
            deviation.with_user(self.user_reporter).write({"title": "Edited"})

    def test_investigator_can_write_open_record(self):
        """An investigator maintains any open record."""
        deviation = self._advance_to_assessed(self._create_deviation())
        deviation.with_user(self.user_investigator).write({"title": "Updated"})
        self.assertEqual(deviation.title, "Updated")

    @mute_logger("odoo.addons.base.models.ir_model", "odoo.models")
    def test_investigator_cannot_unlink(self):
        """Only a manager holds the unlink privilege."""
        deviation = self._create_deviation()
        with self.assertRaises(AccessError):
            deviation.with_user(self.user_investigator).unlink()

    def test_manager_can_write_closed_record(self):
        """A manager retains write access to a terminal record."""
        deviation = self._create_deviation()
        deviation.state = "closed"
        deviation.with_user(self.user_manager).write({"title": "QA amendment"})
        self.assertEqual(deviation.title, "QA amendment")

    def test_only_manager_approves_disposition(self):
        """Disposition approval is restricted to the manager role."""
        deviation = self._advance_to_investigation(self._create_deviation())
        disposition = self.env["ls.deviation.disposition"].create(
            {
                "deviation_id": deviation.id,
                "product_id": self.product.id,
                "quantity": 10.0,
                "decision": "reject",
                "justification": "Out of specification.",
            }
        )
        with self.assertRaises(UserError):
            disposition.with_user(self.user_investigator).action_approve()
        disposition.with_user(self.user_manager).action_approve()
        self.assertEqual(disposition.state, "approved")

    def test_only_manager_rejects_disposition(self):
        """Disposition rejection is restricted to the manager role."""
        deviation = self._advance_to_investigation(self._create_deviation())
        disposition = self.env["ls.deviation.disposition"].create(
            {
                "deviation_id": deviation.id,
                "product_id": self.product.id,
                "quantity": 10.0,
                "decision": "rework",
                "justification": "Rework proposed.",
            }
        )
        with self.assertRaises(UserError):
            disposition.with_user(self.user_investigator).action_reject()

    def test_multi_company_rule_hides_foreign_records(self):
        """The global company rule excludes records of another company."""
        other_company = self.env["res.company"].create({"name": "Other Co"})
        deviation = self._create_deviation(company_id=other_company.id)
        visible = (
            self.env["ls.deviation"]
            .with_user(self.user_manager)
            .search([("id", "=", deviation.id)])
        )
        self.assertNotIn(deviation, visible)
