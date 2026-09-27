# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Constraint, compute and ORM override tests for ls.complaint."""

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from .common import TestLsComplaintCommon


@tagged("post_install", "-at_install")
class TestComplaintConstraints(TestLsComplaintCommon):
    """Verify the data integrity rules of the complaint model."""

    def test_01_receipt_date_not_in_future(self):
        """A receipt date in the future is refused."""
        with self.assertRaises(ValidationError):
            self._create_complaint(
                receipt_date=fields.Datetime.now() + timedelta(days=1)
            )

    def test_02_occurrence_after_receipt(self):
        """An occurrence date later than the receipt date is refused."""
        with self.assertRaises(ValidationError):
            self._create_complaint(
                occurrence_date=fields.Date.context_today(self.env.user)
                + timedelta(days=2)
            )

    def test_03_expiry_before_manufacturing(self):
        """An expiry date earlier than the manufacturing date is refused."""
        today = fields.Date.context_today(self.env.user)
        with self.assertRaises(ValidationError):
            self._create_complaint(
                manufacturing_date=today,
                expiry_date=today - timedelta(days=1),
            )

    def test_04_other_channel_requires_description(self):
        """'Other Channel' without a description is refused."""
        with self.assertRaises(ValidationError):
            self._create_complaint(channel="other")

    def test_05_other_type_requires_description(self):
        """'Other Type' without a description is refused."""
        complaint = self._create_complaint()
        with self.assertRaises(ValidationError):
            complaint.complaint_type = "other"

    def test_06_lot_must_match_product(self):
        """A lot belonging to another product is refused."""
        lot = self._create_lot(self.other_product, "LOT-OTHER")
        complaint = self._create_complaint()
        with self.assertRaises(ValidationError):
            complaint.lot_id = lot

    def test_07_reviewer_differs_from_owner(self):
        """The reviewer cannot be the responsible user."""
        complaint = self._create_complaint()
        with self.assertRaises(ValidationError):
            complaint.reviewer_id = complaint.owner_id

    def test_08_product_required_after_received(self):
        """A product related complaint must identify a product once assessed."""
        complaint = self._create_complaint(product_id=False)
        with self.assertRaises(ValidationError):
            complaint.action_start_assessment()

    def test_09_due_dates_from_category(self):
        """Target dates are derived from the category configuration."""
        complaint = self._create_complaint()
        base_date = fields.Datetime.context_timestamp(
            complaint, complaint.receipt_date
        ).date()
        self.assertEqual(
            complaint.acknowledgement_due_date, base_date + timedelta(days=2)
        )
        self.assertEqual(
            complaint.investigation_due_date, base_date + timedelta(days=20)
        )
        self.assertEqual(complaint.closure_due_date, base_date + timedelta(days=30))

    def test_10_no_due_date_without_target(self):
        """No target date is produced when the category has no target."""
        category = self.env["ls.complaint.category"].create(
            {"name": "No target", "code": "TST-NONE", "company_id": self.company.id}
        )
        complaint = self._create_complaint(category_id=category.id)
        self.assertFalse(complaint.acknowledgement_due_date)
        self.assertFalse(complaint.investigation_due_date)
        self.assertFalse(complaint.closure_due_date)

    def test_11_is_overdue_compute_and_search(self):
        """The overdue flag is computed and searchable."""
        complaint = self._create_complaint()
        self.assertFalse(complaint.is_overdue)
        complaint.receipt_date = fields.Datetime.now() - timedelta(days=90)
        complaint.invalidate_recordset()
        self.assertTrue(complaint.is_overdue)
        found = self.env["ls.complaint"].search(
            [("is_overdue", "=", True), ("id", "=", complaint.id)]
        )
        self.assertIn(complaint, found)
        not_found = self.env["ls.complaint"].search(
            [("is_overdue", "!=", True), ("id", "=", complaint.id)]
        )
        self.assertNotIn(complaint, not_found)

    def test_12_is_overdue_search_operator_guard(self):
        """An unsupported operator on the overdue filter raises an error.

        Odoo 19 rejects an ordering operator on a boolean field in its domain
        parser (ValueError), before the custom search method runs.
        """
        with self.assertRaises(ValueError):
            self.env["ls.complaint"].search([("is_overdue", ">", True)])

    def test_13_display_name(self):
        """The display name combines the reference and the subject."""
        complaint = self._create_complaint()
        self.assertIn(complaint.name, complaint.display_name)
        self.assertIn("Chipped tablets", complaint.display_name)

    def test_14_onchange_product_sets_uom_and_clears_lot(self):
        """The product onchange aligns the unit of measure and clears the lot."""
        lot = self._create_lot(self.product, "LOT-ONCHANGE")
        # A form record (not saved): on a saved record the lot/product
        # consistency constraint refuses the change before the onchange.
        complaint = self._create_complaint().new(
            {"product_id": self.product.id, "lot_id": lot.id}
        )
        complaint.product_id = self.other_product
        complaint._onchange_product_id()
        self.assertFalse(complaint.lot_id)
        self.assertEqual(complaint.product_uom_id, self.other_product.uom_id)

    def test_15_onchange_category_sets_severity(self):
        """The category onchange proposes the configured default severity."""
        complaint = self._create_complaint(severity=False)
        complaint._onchange_category_id()
        self.assertEqual(complaint.severity, "major")

    def test_16_onchange_partner_fills_contact(self):
        """The partner onchange copies the contact details."""
        self.partner.write({"email": "contact@example.com", "phone": "+1234"})
        complaint = self._create_complaint(contact_name=False)
        complaint._onchange_partner_id()
        self.assertEqual(complaint.contact_name, self.partner.name)
        self.assertEqual(complaint.contact_email, "contact@example.com")

    def test_17_unlink_guard(self):
        """A complaint that left the Received state cannot be deleted."""
        complaint = self._create_complaint()
        complaint.action_start_assessment()
        with self.assertRaises(UserError):
            complaint.unlink()
        complaint.action_cancel(reason="Test")
        complaint.action_reset_to_received()
        complaint.unlink()

    def test_18_copy_resets_regulated_data(self):
        """Duplicating a complaint resets the reference and the status."""
        complaint = self._create_complaint()
        complaint.action_start_assessment()
        copy = complaint.copy()
        self.assertNotEqual(copy.name, complaint.name)
        self.assertEqual(copy.state, "received")
        self.assertFalse(copy.date_closed)

    def test_19_regulatory_flags(self):
        """The reportable flag follows the child adverse events."""
        complaint = self._create_complaint()
        self.assertFalse(complaint.has_adverse_event)
        self.assertFalse(complaint.regulatory_reportable)
        event = self.env["ls.complaint.adverse_event"].create(
            {"complaint_id": complaint.id, "event_description": "Reaction."}
        )
        complaint.invalidate_recordset()
        self.assertTrue(complaint.has_adverse_event)
        self.assertFalse(complaint.regulatory_reportable)
        event.reportable = True
        complaint.invalidate_recordset()
        self.assertTrue(complaint.regulatory_reportable)

    def test_20_root_cause_summary(self):
        """The root cause summary aggregates the approved investigations."""
        complaint = self._create_complaint()
        self._bring_to_investigation(complaint)
        self.assertFalse(complaint.root_cause_summary)
        self._approve_investigation(complaint.investigation_ids)
        complaint.invalidate_recordset()
        self.assertIn("Worn tooling", complaint.root_cause_summary)
