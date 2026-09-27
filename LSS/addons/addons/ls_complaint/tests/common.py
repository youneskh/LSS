# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the ls_complaint test suite."""

from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestLsComplaintCommon(TransactionCase):
    """Common set-up shared by every ls_complaint test case."""

    @classmethod
    def setUpClass(cls):
        """Create the users, master data and helper records used by the tests."""
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.group_viewer = cls.env.ref("ls_complaint.group_ls_complaint_viewer")
        cls.group_investigator = cls.env.ref(
            "ls_complaint.group_ls_complaint_investigator"
        )
        cls.group_reviewer = cls.env.ref("ls_complaint.group_ls_complaint_reviewer")
        cls.group_manager = cls.env.ref("ls_complaint.group_ls_complaint_manager")

        cls.user_viewer = cls._create_user("ls_viewer", cls.group_viewer)
        cls.user_investigator = cls._create_user(
            "ls_investigator", cls.group_investigator
        )
        cls.user_other_investigator = cls._create_user(
            "ls_investigator_2", cls.group_investigator
        )
        cls.user_reviewer = cls._create_user("ls_reviewer", cls.group_reviewer)
        cls.user_manager = cls._create_user("ls_manager", cls.group_manager)

        cls.category = cls.env["ls.complaint.category"].create(
            {
                "name": "Test Product Defect",
                "code": "TST-PQD",
                "default_severity": "major",
                "requires_investigation": True,
                "acknowledgement_target_days": 2,
                "investigation_target_days": 20,
                "closure_target_days": 30,
                "ae_reporting_deadline_days": 15,
                "company_id": cls.company.id,
            }
        )
        cls.category_no_investigation = cls.env["ls.complaint.category"].create(
            {
                "name": "Test Packaging",
                "code": "TST-PKG",
                "default_severity": "minor",
                "requires_investigation": False,
                "closure_target_days": 30,
                "company_id": cls.company.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Complainant"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Tablet 10 mg", "default_code": "TST-TAB-10"}
        )
        cls.other_product = cls.env["product.product"].create(
            {"name": "Test Syrup 100 ml", "default_code": "TST-SYR-100"}
        )

    @classmethod
    def _create_user(cls, login, group):
        """Create an internal user belonging to ``group``.

        :param str login: unique login of the user
        :param group: ``res.groups`` record the user must belong to
        :return: the created ``res.users`` record
        """
        user = cls.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "email": f"{login}@example.com",
                "company_id": cls.env.ref("base.main_company").id,
                "company_ids": [Command.set([cls.env.ref("base.main_company").id])],
            }
        )
        cls.env.ref("base.group_user").sudo().write({"user_ids": [Command.link(user.id)]})
        group.sudo().write({"user_ids": [Command.link(user.id)]})
        return user

    @classmethod
    def _make_lot_trackable(cls, product):
        """Enable lot tracking on ``product`` in a version tolerant way.

        The field controlling stockability changed name across Odoo releases,
        so the fields actually present on the model are inspected before being
        written.

        :param product: ``product.product`` record
        :return: the product record
        """
        values = {}
        if "is_storable" in product._fields:
            values["is_storable"] = True
        if "type" in product._fields:
            values["type"] = "consu"
        if "tracking" in product._fields:
            values["tracking"] = "lot"
        if values:
            product.sudo().write(values)
        return product

    def _create_lot(self, product, name):
        """Create a lot for ``product``.

        :param product: ``product.product`` record
        :param str name: lot number
        :return: the created ``stock.lot`` record
        """
        self._make_lot_trackable(product)
        return self.env["stock.lot"].create(
            {
                "name": name,
                "product_id": product.id,
                "company_id": self.company.id,
            }
        )

    def _create_complaint(self, **overrides):
        """Create a complaint with sensible defaults.

        :param overrides: field values overriding the defaults
        :return: the created ``ls.complaint`` record
        """
        values = {
            "summary": "Chipped tablets",
            "description": "Several tablets are chipped on the edge.",
            "channel": "phone",
            "complainant_type": "pharmacy",
            "partner_id": self.partner.id,
            "category_id": self.category.id,
            "product_related": True,
            "product_id": self.product.id,
            "lot_name": "LOT-TEST-001",
            "quantity_complained": 4.0,
            "owner_id": self.user_investigator.id,
            "received_by_id": self.user_investigator.id,
            "company_id": self.company.id,
        }
        values.update(overrides)
        return self.env["ls.complaint"].create(values)

    def _bring_to_investigation(self, complaint):
        """Advance a complaint from Received to Investigation.

        :param complaint: ``ls.complaint`` record
        :return: the complaint record
        """
        complaint.action_start_assessment()
        complaint.write(
            {
                "severity": "major",
                "complaint_type": "quality_defect",
                "assessment_summary": "Initial assessment performed.",
            }
        )
        complaint.action_start_investigation()
        return complaint

    def _approve_investigation(self, investigation):
        """Run an investigation through to approval.

        :param investigation: ``ls.complaint.investigation`` record
        :return: the investigation record
        """
        investigation.action_start()
        investigation.write(
            {
                "methodology": "five_whys",
                "investigation_summary": "Samples examined, batch record reviewed.",
                "root_cause_category": "machine",
                "root_cause_description": "Worn tooling on the tablet press.",
                "conclusion": "confirmed",
            }
        )
        investigation.action_complete()
        investigation.with_user(self.user_reviewer).action_approve()
        return investigation

    def _add_done_resolution(self, complaint):
        """Attach a completed resolution to a complaint.

        :param complaint: ``ls.complaint`` record
        :return: the created ``ls.complaint.resolution`` record
        """
        resolution = self.env["ls.complaint.resolution"].create(
            {
                "complaint_id": complaint.id,
                "resolution_type": "replacement",
                "description": "Replacement units shipped.",
                "owner_id": self.user_investigator.id,
                "due_date": fields.Date.context_today(complaint),
                "completion_evidence": "Delivery note DN-0001.",
            }
        )
        resolution.action_start()
        resolution.action_done()
        return resolution
