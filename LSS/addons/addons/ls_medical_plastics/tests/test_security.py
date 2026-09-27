# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests for access rights, role hierarchy and multi-company isolation."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import MedicalPlasticsCommon


@tagged("post_install", "-at_install")
class TestSecurity(MedicalPlasticsCommon):
    """Access control at ORM level rather than in the user interface only."""

    def test_role_hierarchy_implied(self):
        """Each role inherits the permissions of the role below it."""
        self.assertTrue(
            self.user_manager.has_group("ls_medical_plastics.group_mp_engineer")
        )
        self.assertTrue(
            self.user_manager.has_group("ls_medical_plastics.group_mp_viewer")
        )
        self.assertTrue(
            self.user_engineer.has_group("ls_medical_plastics.group_mp_operator")
        )
        self.assertFalse(
            self.user_operator.has_group("ls_medical_plastics.group_mp_engineer")
        )

    def test_viewer_cannot_create_run(self):
        """A viewer has no create permission on moulding runs."""
        with self.assertRaises(AccessError):
            self.env["ls.mp.injection_molding"].with_user(self.user_viewer).create(
                {
                    "component_id": self.component.id,
                    "tool_id": self.tool.id,
                    "operator_id": self.user_viewer.id,
                }
            )

    def test_viewer_can_read_run(self):
        """A viewer can read moulding runs."""
        run = self._create_run()
        self.assertTrue(run.with_user(self.user_viewer).read(["name"]))

    def test_operator_can_create_run(self):
        """An operator can create moulding runs."""
        run = self.env["ls.mp.injection_molding"].with_user(self.user_operator).create(
            {
                "component_id": self.component.id,
                "tool_id": self.tool.id,
                "operator_id": self.user_operator.id,
            }
        )
        self.assertTrue(run.id)

    def test_operator_cannot_delete_run(self):
        """An operator has no delete permission on moulding runs."""
        run = self.env["ls.mp.injection_molding"].with_user(self.user_operator).create(
            {
                "component_id": self.component.id,
                "tool_id": self.tool.id,
                "operator_id": self.user_operator.id,
            }
        )
        with self.assertRaises(AccessError):
            run.with_user(self.user_operator).unlink()

    def test_operator_cannot_create_component(self):
        """An operator cannot create component master data."""
        with self.assertRaises(AccessError):
            self.env["ls.mp.component"].with_user(self.user_operator).create(
                {
                    "name": "Unauthorised",
                    "code": "UNAUTH",
                    "product_id": self.product_component.id,
                    "category": "closure_cap",
                }
            )

    def test_engineer_cannot_delete_component(self):
        """Deletion of component master data is reserved to managers."""
        with self.assertRaises(AccessError):
            self.component.with_user(self.user_engineer).unlink()

    def test_reading_write_denied_to_every_role(self):
        """No role holds write permission on parameter readings.

        The append-only nature of readings is enforced both by the access
        control list and by the model. This test asserts the access control
        layer, so that removing the model override alone would not silently
        make readings editable.
        """
        model = self.env["ir.model.access"]
        for group_xmlid in (
            "ls_medical_plastics.group_mp_viewer",
            "ls_medical_plastics.group_mp_operator",
            "ls_medical_plastics.group_mp_technician",
            "ls_medical_plastics.group_mp_engineer",
            "ls_medical_plastics.group_mp_manager",
        ):
            group = self.env.ref(group_xmlid)
            rules = model.search(
                [
                    ("model_id.model", "=", "ls.mp.injection_molding.reading"),
                    ("group_id", "=", group.id),
                ]
            )
            for rule in rules:
                self.assertFalse(
                    rule.perm_write,
                    f"Write permission granted to {group_xmlid} on readings.",
                )
                self.assertFalse(
                    rule.perm_unlink,
                    f"Delete permission granted to {group_xmlid} on readings.",
                )

    def test_operator_cannot_approve_specification(self):
        """Approving a specification is reserved to users above operator."""
        spec = self.env["ls.mp.molding_parameter"].with_user(self.user_engineer).create(
            {
                "component_id": self.component.id,
                "tool_id": self.tool.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Holding Pressure",
                            "code": "HOLD-P",
                            "parameter_uom": "bar",
                            "min_value": 100.0,
                            "target_value": 150.0,
                            "max_value": 200.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(AccessError):
            spec.with_user(self.user_operator).action_submit_for_review()

    def test_multi_company_isolation(self):
        """A user of another company cannot read this company's tools."""
        other_company = self.env["res.company"].create({"name": "Other Plant"})
        other_user = new_test_user(
            self.env,
            login="mp_other_company",
            name="Other Company User",
            groups="ls_medical_plastics.group_mp_manager",
            company_id=other_company.id,
            company_ids=[(6, 0, [other_company.id])],
        )
        visible = self.env["ls.mp.tool"].with_user(other_user).search(
            [("id", "=", self.tool.id)]
        )
        self.assertFalse(visible)

    def test_shared_scrap_reasons_visible_across_companies(self):
        """Scrap reasons without a company remain visible to every company."""
        other_company = self.env["res.company"].create({"name": "Second Plant"})
        other_user = new_test_user(
            self.env,
            login="mp_second_company",
            name="Second Company User",
            groups="ls_medical_plastics.group_mp_operator",
            company_id=other_company.id,
            company_ids=[(6, 0, [other_company.id])],
        )
        visible = self.env["ls.mp.scrap.reason"].with_user(other_user).search(
            [("id", "=", self.reason_short_shot.id)]
        )
        self.assertTrue(visible)

    def test_record_rules_carry_no_group_link(self):
        """Company isolation rules are global so no role can widen them.

        A rule restricted to a group would be combined with other group rules
        using a logical OR, which would let a user holding an additional role
        see records of another company. The check resolves the group-link
        field by inspecting the model rather than by naming it, because the
        field name on ``ir.rule`` in Odoo 19 could not be verified from
        official documentation.
        """
        rule = self.env.ref("ls_medical_plastics.rule_mp_tool_company")
        group_fields = [
            name
            for name, field in rule._fields.items()
            if field.type in ("many2many", "one2many")
            and field.comodel_name == "res.groups"
        ]
        self.assertTrue(
            group_fields,
            "No group-link field found on ir.rule; the test needs updating.",
        )
        for name in group_fields:
            self.assertFalse(
                rule[name],
                f"Rule is restricted through {name} and is therefore not global.",
            )
