# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the Validation Management test suite."""

from odoo.tests.common import TransactionCase, new_test_user

from ..models.ls_validation_constants import PARAM_PASSWORD_REQUIRED


class ValidationCommon(TransactionCase):
    """Base class building the users and the master data used by the tests."""

    @classmethod
    def setUpClass(cls):
        """Create users, an item, a master plan and an approved protocol."""
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            PARAM_PASSWORD_REQUIRED, "0"
        )
        cls.company = cls.env.company
        cls.user_viewer = new_test_user(
            cls.env,
            login="ls_viewer",
            groups="ls_validation.group_ls_validation_viewer",
            name="Validation Viewer",
        )
        cls.user_engineer = new_test_user(
            cls.env,
            login="ls_engineer",
            groups="ls_validation.group_ls_validation_engineer",
            name="Validation Engineer",
        )
        cls.user_engineer_2 = new_test_user(
            cls.env,
            login="ls_engineer_2",
            groups="ls_validation.group_ls_validation_engineer",
            name="Second Validation Engineer",
        )
        cls.user_approver = new_test_user(
            cls.env,
            login="ls_approver",
            groups="ls_validation.group_ls_validation_approver",
            name="Validation Approver",
        )
        cls.user_manager = new_test_user(
            cls.env,
            login="ls_manager",
            groups="ls_validation.group_ls_validation_manager",
            name="Validation Manager",
        )

        cls.item = cls.env["ls.validation.item"].create(
            {
                "code": "TEST-EQ-001",
                "name": "Test Sterilizer",
                "item_type": "equipment",
                "gxp_impact": "direct",
                "criticality": "high",
                "revalidation_interval_months": 36,
            }
        )
        cls.master_plan = cls.env["ls.validation.master.plan"].create(
            {
                "name": "Test Validation Master Plan",
                "scope": "<p>Test scope</p>",
                "item_ids": [(6, 0, cls.item.ids)],
            }
        )

    @classmethod
    def _create_protocol(cls, item=None, test_count=2, critical=True):
        """Create a draft protocol carrying ``test_count`` test cases."""
        item = item or cls.item
        tests = []
        for index in range(1, test_count + 1):
            tests.append(
                (
                    0,
                    0,
                    {
                        "sequence": index * 10,
                        "code": "TC-%03d" % index,
                        "name": "Test case %d" % index,
                        "acceptance_criteria": "Criterion %d" % index,
                        "is_critical": critical and index == 1,
                    },
                )
            )
        return cls.env["ls.validation.protocol"].create(
            {
                "name": "Operational Qualification",
                "protocol_type": "oq",
                "item_id": item.id,
                "test_ids": tests,
            }
        )

    def _sign(self, record, action_method, user):
        """Run a signature protected transition through the wizard.

        :param record: record carrying the transition.
        :param str action_method: name of the action opening the wizard.
        :param user: user performing the signature.
        :return: the result of the signed callback.
        """
        record_as_user = record.with_user(user)
        action = getattr(record_as_user, action_method)()
        context = action["context"]
        wizard = (
            self.env["ls.validation.sign.wizard"]
            .with_user(user)
            .create(
                {
                    "res_model": context["default_res_model"],
                    "res_id": context["default_res_id"],
                    "meaning": context["default_meaning"],
                    "callback": context["default_callback"],
                    "login": user.login,
                    "reason": "Automated test",
                }
            )
        )
        return wizard.action_sign()

    def _approve_protocol(self, protocol):
        """Bring a draft protocol to the approved state."""
        protocol.with_user(self.user_engineer).action_submit_review()
        self._sign(protocol, "action_approve", self.user_approver)
        return protocol

    def _execute_protocol(self, protocol, verdict="pass"):
        """Create, fill and approve an execution of a protocol.

        :param protocol: an approved protocol.
        :param str verdict: verdict applied to every result line.
        :return: the execution record.
        """
        execution = (
            self.env["ls.validation.execution"]
            .with_user(self.user_engineer)
            .create({"protocol_id": protocol.id})
        )
        execution.action_start()
        for line in execution.result_ids:
            line.write({"actual_result": "Observed value", "verdict": verdict})
        execution.action_complete()
        self._sign(execution, "action_review", self.user_engineer_2)
        self._sign(execution, "action_approve", self.user_approver)
        return execution
