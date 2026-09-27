# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the ``ls_pharma`` test suite.

No fixture names an external XML identifier.  Records of models that this
module does not own are either created through the ORM or found by searching
the database, so that the suite does not depend on identifiers whose
stability across Odoo versions this module cannot verify.
"""

from odoo.tests.common import TransactionCase, new_test_user

#: A valid GTIN-14 used throughout the suite.  The first thirteen digits are
#: arbitrary; the fourteenth is the modulo-10 check digit computed from them.
DEMO_GTIN14 = "03612345000019"


class LsPharmaCommon(TransactionCase):
    """Base class carrying the fixtures shared by the test modules."""

    @classmethod
    def setUpClass(cls):
        """Create the products, the materials and the users used by tests."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.uom = cls.env["uom.uom"].search([], limit=1)
        if not cls.uom:
            raise AssertionError(
                "The test database carries no unit of measure. The tests of "
                "ls_pharma need at least one, because a batch component "
                "requires a unit."
            )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Tablet 500 mg",
                "is_pharmaceutical": True,
                "pharma_dosage_form": "tablet",
                "pharma_strength": "500 mg",
                "pharma_gtin14": DEMO_GTIN14,
                "pharma_shelf_life_months": 24,
                "pharma_theoretical_yield_qty": 100000.0,
                "pharma_yield_min_percentage": 95.0,
                "pharma_yield_max_percentage": 102.0,
                "pharma_requires_serialization": True,
            }
        )
        cls.component_product = cls.env["product.product"].create(
            {"name": "Test Active Substance"}
        )
        cls.excipient_product = cls.env["product.product"].create(
            {"name": "Test Filler"}
        )

        cls.api = cls.env["ls.pharma.api"].create(
            {
                "name": "Test Active Substance",
                "code": "API-TEST",
                "inn_name": "Testolol",
                "pharmacopoeia": "ph_eur",
                "potency_basis": "as_is",
                "label_assay_percentage": 100.0,
                "product_id": cls.component_product.id,
            }
        )
        cls.api.action_qualify()

        cls.excipient = cls.env["ls.pharma.excipient"].create(
            {
                "name": "Test Filler",
                "code": "EXC-TEST",
                "excipient_function": "diluent",
                "pharmacopoeia": "ph_eur",
                "product_id": cls.excipient_product.id,
            }
        )
        cls.excipient.action_qualify()

        cls.operator = new_test_user(
            cls.env,
            login="ls_pharma_operator",
            groups="ls_pharma.group_ls_pharma_operator",
            name="Production Operator",
        )
        cls.second_operator = new_test_user(
            cls.env,
            login="ls_pharma_operator_two",
            groups="ls_pharma.group_ls_pharma_operator",
            name="Second Operator",
        )
        cls.production_manager = new_test_user(
            cls.env,
            login="ls_pharma_production_manager",
            groups="ls_pharma.group_ls_pharma_production_manager",
            name="Production Manager",
        )
        cls.qa_user = new_test_user(
            cls.env,
            login="ls_pharma_qa",
            groups="ls_pharma.group_ls_pharma_qa",
            name="Quality Assurance Officer",
        )
        cls.viewer = new_test_user(
            cls.env,
            login="ls_pharma_viewer",
            groups="ls_pharma.group_ls_pharma_viewer",
            name="Pharmaceutical Viewer",
        )

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------
    def _create_batch(self, **overrides):
        """Create a planned batch of the test product.

        :param overrides: values overriding the defaults of the fixture.
        :rtype: recordset of ``ls.pharma.batch``
        """
        values = {
            "product_id": self.product.id,
            "batch_type": "finished",
            "uom_id": self.uom.id,
            "planned_qty": 100000.0,
            "theoretical_yield_qty": 100000.0,
            "yield_min_percentage": 95.0,
            "yield_max_percentage": 102.0,
            "shelf_life_months": 24,
        }
        values.update(overrides)
        return self.env["ls.pharma.batch"].create(values)

    def _add_components(self, batch):
        """Add one active component and one excipient to a batch.

        :param batch: the batch that receives the components.
        :rtype: recordset of ``ls.pharma.batch.component``
        """
        return self.env["ls.pharma.batch.component"].create(
            [
                {
                    "batch_id": batch.id,
                    "product_id": self.component_product.id,
                    "api_id": self.api.id,
                    "is_active_ingredient": True,
                    "quantity": 50.0,
                    "uom_id": self.uom.id,
                    "assay_percentage": 100.0,
                    "charged_by_user_id": self.operator.id,
                    "verified_by_user_id": self.second_operator.id,
                },
                {
                    "batch_id": batch.id,
                    "product_id": self.excipient_product.id,
                    "excipient_id": self.excipient.id,
                    "quantity": 150.0,
                    "uom_id": self.uom.id,
                    "charged_by_user_id": self.operator.id,
                    "verified_by_user_id": self.second_operator.id,
                },
            ]
        )

    def _create_batch_record(self, batch, **overrides):
        """Create a batch production and control record for a batch.

        :param batch: the batch that the record documents.
        :rtype: recordset of ``ls.pharma.batch_record``
        """
        values = {
            "batch_id": batch.id,
            "record_type": "manufacturing",
            "master_record_reference": "MPR-TEST-001",
            "master_record_version": "3.0",
            "master_checked_by_user_id": self.production_manager.id,
            "master_checked_date": "2026-01-05 08:00:00",
        }
        values.update(overrides)
        return self.env["ls.pharma.batch_record"].create(values)

    def _add_steps(self, record, count=2):
        """Add processing steps to a batch record.

        :param record: the batch record that receives the steps.
        :param int count: number of steps to create.
        :rtype: recordset of ``ls.pharma.batch_record.step``
        """
        return self.env["ls.pharma.batch_record.step"].create(
            [
                {
                    "record_id": record.id,
                    "sequence": (index + 1) * 10,
                    "name": "Step %d" % (index + 1),
                    "instruction": "Perform step %d." % (index + 1),
                    "is_significant": True,
                }
                for index in range(count)
            ]
        )

    def _complete_steps(self, record, user):
        """Mark every step of a record as done on behalf of ``user``."""
        for step in record.step_ids:
            step.with_user(user).write(
                {
                    "performed_by_user_id": user.id,
                    "checked_by_user_id": self.second_operator.id,
                    "state": "done",
                    "date_performed": "2026-01-06 10:00:00",
                }
            )

    def _run_batch_to_review(self):
        """Drive a batch from planned to quality assurance review.

        The returned batch carries components, one approved batch record, an
        actual yield inside its limits and an expiry date, which are the
        preconditions of a release decision.

        :returns: the batch and its batch record.
        :rtype: tuple
        """
        batch = self._create_batch()
        self._add_components(batch)
        batch.with_user(self.production_manager).action_start()
        record = self._create_batch_record(batch)
        self._add_steps(record)
        record.with_user(self.operator).action_start_execution()
        self._complete_steps(record, self.operator)
        record.with_user(self.operator).action_complete_execution()
        record.with_user(self.production_manager).action_submit_review()
        record.with_user(self.qa_user).action_approve()
        batch.write(
            {
                "actual_yield_qty": 99000.0,
                "date_manufacture": "2026-01-07",
                "date_expiry": "2028-01-07",
            }
        )
        batch.with_user(self.production_manager).action_complete()
        batch.with_user(self.production_manager).action_submit_review()
        return batch, record
