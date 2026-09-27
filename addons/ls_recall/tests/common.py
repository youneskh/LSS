# Part of the Life Sciences Suite for Odoo 19 Community Edition.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the recall test suite."""

from odoo.tests.common import TransactionCase


class RecallCommon(TransactionCase):
    """Base class building the users, product, lots and plan used by tests."""

    @classmethod
    def setUpClass(cls):
        """Create a self-contained data set for one company."""
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.group_viewer = cls.env.ref("ls_recall.group_ls_recall_viewer")
        cls.group_coordinator = cls.env.ref(
            "ls_recall.group_ls_recall_coordinator"
        )
        cls.group_manager = cls.env.ref("ls_recall.group_ls_recall_manager")

        cls.user_viewer = cls._create_user("recall_viewer", cls.group_viewer)
        cls.user_coordinator = cls._create_user(
            "recall_coordinator", cls.group_coordinator
        )
        cls.user_manager = cls._create_user(
            "recall_manager", cls.group_manager
        )

        cls.partner_a = cls.env["res.partner"].create(
            {"name": "Consignee A"}
        )
        cls.partner_b = cls.env["res.partner"].create(
            {"name": "Consignee B"}
        )
        cls.partner_authority = cls.env["res.partner"].create(
            {"name": "Competent Authority"}
        )

        cls.product = cls._create_tracked_product("Test tablets")
        cls.lot_1 = cls.env["stock.lot"].create(
            {"name": "LOT-0001", "product_id": cls.product.id}
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {"name": "LOT-0002", "product_id": cls.product.id}
        )

        cls.plan = cls.env["ls.recall.plan"].create(
            {
                "name": "Test recall plan",
                "responsible_user_id": cls.user_coordinator.id,
                "deputy_user_id": cls.user_manager.id,
                "description": "<p>Documented procedure.</p>",
                "target_reconciliation_rate": 100.0,
            }
        )

    @classmethod
    def _create_user(cls, login, group):
        """Create an internal user holding exactly one recall role.

        The group field of ``res.users`` was renamed from ``groups_id``
        to ``group_ids`` in Odoo 19, so the correct name is resolved from
        the model rather than hard-coded.
        """
        user_model = cls.env["res.users"].with_context(
            no_reset_password=True
        )
        field_name = (
            "group_ids" if "group_ids" in user_model._fields else "groups_id"
        )
        values = {
            "name": login,
            "login": login,
            "email": f"{login}@example.com",
            "company_id": cls.company.id,
            "company_ids": [(6, 0, cls.company.ids)],
            field_name: [
                (6, 0, [cls.env.ref("base.group_user").id, group.id])
            ],
        }
        return user_model.create(values)

    @classmethod
    def _create_tracked_product(cls, name):
        """Create a lot-tracked storable product.

        Odoo 18 replaced ``type='product'`` with ``type='consu'`` plus the
        ``is_storable`` boolean. The boolean is only set when the field
        exists, so the fixture works on either convention.
        """
        values = {"name": name, "type": "consu", "tracking": "lot"}
        if "is_storable" in cls.env["product.template"]._fields:
            values["is_storable"] = True
        return cls.env["product.product"].create(values)

    def _create_execution(self, **overrides):
        """Create a recall in the Planned state.

        :param overrides: field values replacing the defaults.
        :return: the created recall.
        """
        values = {
            "action_type": "recall",
            "product_id": self.product.id,
            "lot_ids": [(6, 0, self.lot_1.ids)],
            "classification": "class_ii",
            "depth": "retail",
            "reason": "Out-of-specification result.",
            "health_hazard_evaluation": "<p>Assessed.</p>",
            "responsible_user_id": self.user_coordinator.id,
            "effectiveness_level": "a",
        }
        values.update(overrides)
        return self.env["ls.recall.execution"].create(values)

    def _add_line(self, execution, partner, lot, shipped):
        """Attach a consignee line to a recall.

        :param execution: the recall record.
        :param partner: the consignee.
        :param lot: the lot delivered.
        :param float shipped: the quantity delivered.
        :return: the created line.
        """
        return self.env["ls.recall.line"].create(
            {
                "execution_id": execution.id,
                "partner_id": partner.id,
                "lot_id": lot.id,
                "qty_shipped": shipped,
            }
        )

    def _create_communication(self, execution, **overrides):
        """Create a fully confirmed recall notice ready to be approved."""
        values = {
            "execution_id": execution.id,
            "communication_type": "recall_notice",
            "channel": "email",
            "subject": "Urgent recall notice",
            "body": "<p>Please quarantine the affected lots.</p>",
            "partner_ids": [(6, 0, [self.partner_a.id])],
            "content_identifies_product": True,
            "content_states_reason": True,
            "content_gives_instructions": True,
            "content_requests_response": True,
            "content_gives_contact": True,
        }
        values.update(overrides)
        return self.env["ls.recall.communication"].create(values)

    def _advance_to_effectiveness(self, execution):
        """Drive a recall as far as the Effectiveness Check state.

        Used by tests that need a recall close to closure without
        repeating the whole sequence.
        """
        execution.action_initiate()
        self._add_line(execution, self.partner_a, self.lot_1, 100.0)
        execution.write({"state": "in_progress"})
        communication = self._create_communication(execution)
        communication.action_approve()
        communication.action_mark_sent()
        execution.action_start_communication()
        execution.action_generate_effectiveness_checks()
        for check in execution.effectiveness_ids:
            check.outcome = "action_taken"
            check.action_perform()
        execution.action_start_effectiveness()
        return execution
