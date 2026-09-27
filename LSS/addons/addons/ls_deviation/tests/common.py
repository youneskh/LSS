# Copyright 2026 Life Sciences Suite
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the deviation management test suite."""

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user


class DeviationCommon(TransactionCase):
    """Base fixture creating users, master data and a helper factory.

    Users are created with :func:`odoo.tests.common.new_test_user`, which
    accepts group external identifiers directly. Using the helper avoids
    referencing the user-to-group relational field by name.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

        cls.user_viewer = new_test_user(
            cls.env,
            login="dev_viewer",
            name="Deviation Viewer",
            groups="base.group_user,ls_deviation.group_ls_deviation_viewer",
        )
        cls.user_reporter = new_test_user(
            cls.env,
            login="dev_reporter",
            name="Deviation Reporter",
            groups="base.group_user,ls_deviation.group_ls_deviation_reporter",
        )
        cls.user_investigator = new_test_user(
            cls.env,
            login="dev_investigator",
            name="Deviation Investigator",
            groups="base.group_user,ls_deviation.group_ls_deviation_investigator",
        )
        cls.user_manager = new_test_user(
            cls.env,
            login="dev_manager",
            name="Deviation Manager",
            groups="base.group_user,ls_deviation.group_ls_deviation_manager",
        )

        cls.deviation_type = cls.env.ref("ls_deviation.type_procedural")
        cls.deviation_type_yield = cls.env.ref("ls_deviation.type_yield")
        cls.category = cls.env.ref("ls_deviation.category_production")
        cls.rca_method = cls.env.ref("ls_deviation.rca_five_whys")

        cls.product = cls.env["product.product"].create(
            {"name": "Test Tablet 10 mg", "tracking": "lot"}
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "LOT-TEST-0001",
                "product_id": cls.product.id,
                "company_id": cls.company.id,
            }
        )
        cls.other_lot = cls.env["stock.lot"].create(
            {
                "name": "LOT-TEST-0002",
                "product_id": cls.product.id,
                "company_id": cls.company.id,
            }
        )

    @classmethod
    def _deviation_values(cls, **overrides):
        """Return a valid minimal set of creation values."""
        now = fields.Datetime.now()
        values = {
            "title": "Test deviation",
            "description": "A factual account of the test deviation.",
            "deviation_type_id": cls.deviation_type.id,
            "category_id": cls.category.id,
            "occurrence_date": now - timedelta(hours=2),
            "detection_date": now - timedelta(hours=1),
        }
        values.update(overrides)
        return values

    @classmethod
    def _create_deviation(cls, env=None, **overrides):
        """Create a deviation, optionally as another user."""
        model = (env or cls.env)["ls.deviation"]
        return model.create(cls._deviation_values(**overrides))

    def _advance_to_assessed(self, deviation):
        """Populate the assessment fields and move to ``assessed``."""
        deviation.write(
            {
                "severity": "major",
                "impact_product_quality": True,
                "impact_assessment": "Assessed impact narrative.",
                "owner_id": self.user_investigator.id,
            }
        )
        deviation.action_assess()
        return deviation

    def _advance_to_investigation(self, deviation):
        """Add a completed investigation and move to ``investigation``."""
        self._advance_to_assessed(deviation)
        self.env["ls.deviation.investigation"].create(
            {
                "deviation_id": deviation.id,
                "name": "Root cause investigation",
                "rca_method_id": self.rca_method.id,
                "investigator_id": self.user_investigator.id,
            }
        )
        deviation.action_start_investigation()
        return deviation

    def _advance_to_disposition(self, deviation, with_disposition=True):
        """Complete the investigation and move to ``disposition``."""
        self._advance_to_investigation(deviation)
        investigation = deviation.investigation_ids[0]
        investigation.write(
            {
                "findings": "Documented findings of the investigation.",
                "root_cause": "Determined root cause statement.",
            }
        )
        investigation.action_start()
        investigation.action_complete()
        deviation.extension_rationale = (
            "Two adjacent batches on the same equipment train were reviewed."
        )
        if with_disposition and deviation.has_impact:
            disposition = self.env["ls.deviation.disposition"].create(
                {
                    "deviation_id": deviation.id,
                    "product_id": self.product.id,
                    "lot_id": self.lot.id,
                    "quantity": 100.0,
                    "decision": "use_as_is",
                    "justification": "Quality attributes unaffected.",
                }
            )
            disposition.with_user(self.user_manager).action_approve()
        deviation.action_disposition()
        return deviation
