# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of the security model.

Two properties are checked: that the access rights grant what the role model
intends and refuse the rest, and that the segregation of duties is enforced by
the models themselves rather than by the interface alone.
"""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import LsPharmaCommon


@tagged("post_install", "-at_install")
class TestSecurity(LsPharmaCommon):
    """Exercise the groups, the access rights and the record rules."""

    def test_groups_exist(self):
        """The six groups of the role model are installed."""
        for identifier in (
            "group_ls_pharma_viewer",
            "group_ls_pharma_operator",
            "group_ls_pharma_production_manager",
            "group_ls_pharma_qa",
            "group_ls_pharma_regulatory",
            "group_ls_pharma_manager",
        ):
            self.assertTrue(
                self.env.ref("ls_pharma.%s" % identifier),
                "the group %s is missing" % identifier,
            )

    def test_quality_assurance_does_not_imply_production(self):
        """The quality role does not inherit the production role.

        The independence of the quality unit required by 21 CFR 211.22 is
        visible in the role model itself, not only in the guards of the
        models.
        """
        qa_group = self.env.ref("ls_pharma.group_ls_pharma_qa")
        operator_group = self.env.ref("ls_pharma.group_ls_pharma_operator")
        self.assertNotIn(operator_group, qa_group.implied_ids)
        self.assertTrue(
            self.qa_user.has_group("ls_pharma.group_ls_pharma_qa")
        )
        self.assertFalse(
            self.qa_user.has_group("ls_pharma.group_ls_pharma_operator")
        )

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_viewer_cannot_create_a_batch(self):
        """A viewer has no write access on batches."""
        with self.assertRaises(AccessError):
            self.env["ls.pharma.batch"].with_user(self.viewer).create(
                {
                    "product_id": self.product.id,
                    "uom_id": self.uom.id,
                }
            )

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_viewer_can_read_a_batch(self):
        """A viewer may read the batches of its company."""
        batch = self._create_batch()
        self.assertTrue(batch.with_user(self.viewer).read(["name"]))

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_operator_cannot_delete_a_batch(self):
        """An operator has no delete right on batches."""
        batch = self._create_batch()
        with self.assertRaises(AccessError):
            batch.with_user(self.operator).unlink()

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_nobody_may_delete_a_release_decision(self):
        """No group carries the delete right on a release decision.

        The access rights and the model agree: the decision is append only.
        """
        model = self.env["ir.model"].search(
            [("model", "=", "ls.pharma.batch.release")]
        )
        accesses = self.env["ir.model.access"].search(
            [("model_id", "=", model.id)]
        )
        self.assertTrue(accesses)
        self.assertFalse(any(accesses.mapped("perm_unlink")))

    @mute_logger("odoo.addons.base.models.ir_rule", "odoo.models")
    def test_operator_cannot_approve_a_batch_record(self):
        """An operator has no write access on an approved record path.

        The approval itself is refused for the executing user by the model;
        this test checks the complementary access-right layer.
        """
        batch = self._create_batch()
        batch.with_user(self.production_manager).action_start()
        record = self._create_batch_record(batch)
        self._add_steps(record)
        record.with_user(self.operator).action_start_execution()
        self._complete_steps(record, self.operator)
        record.with_user(self.operator).action_complete_execution()
        record.with_user(self.production_manager).action_submit_review()
        with self.assertRaises(UserError):
            record.with_user(self.operator).action_approve()

    def test_record_rules_are_installed_for_every_persistent_model(self):
        """Every persistent model of the module carries a record rule.

        The two exclusions are declared in the record rules file: the shared
        stability conditions, which carry no company field, and the transient
        wizards, which the framework already restricts to their creator.
        """
        excluded = {
            "ls.pharma.stability.condition",
            "ls.pharma.batch.release.wizard",
            "ls.pharma.stability.schedule.wizard",
            "ls.pharma.serial.generate.wizard",
        }
        models = self.env["ir.model"].search(
            [("model", "=like", "ls.pharma.%")]
        )
        rules = self.env["ir.rule"].search(
            [("model_id", "in", models.ids)]
        )
        covered = set(rules.mapped("model_id.model"))
        for model in models:
            if model.model in excluded or model.transient or model.abstract:
                continue
            self.assertIn(
                model.model,
                covered,
                "the model %s carries no record rule" % model.model,
            )

    def test_release_decision_cannot_be_written_even_by_a_manager(self):
        """The append-only guard applies to every user, manager included."""
        batch, _record = self._run_batch_to_review()
        wizard = (
            self.env["ls.pharma.batch.release.wizard"]
            .with_user(self.qa_user)
            .create(
                {
                    "batch_id": batch.id,
                    "decision": "rejected",
                    "statement": "Rejected for the purposes of this test.",
                }
            )
        )
        wizard.action_confirm()
        release = batch.release_id
        with self.assertRaises(UserError):
            release.sudo().write({"decision": "released"})
        with self.assertRaises(UserError):
            release.sudo().unlink()
