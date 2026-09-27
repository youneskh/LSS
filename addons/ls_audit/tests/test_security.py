# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Tests of access rights and record rules."""

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import AuditCommon


@tagged("post_install", "-at_install")
class TestSecurity(AuditCommon):
    """Group hierarchy, model access and row level visibility."""

    def test_group_hierarchy_is_additive(self):
        """Each group implies the one below it."""
        self.assertIn(self.group_auditee, self.group_auditor.implied_ids)
        self.assertIn(self.group_auditor, self.group_lead.implied_ids)
        self.assertIn(self.group_lead, self.group_manager.implied_ids)

    def test_manager_inherits_every_group(self):
        """A manager belongs to every audit group."""
        groups = self.user_manager.all_group_ids
        self.assertIn(self.group_lead, groups)
        self.assertIn(self.group_auditor, groups)
        self.assertIn(self.group_auditee, groups)

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_auditee_cannot_create_an_audit(self):
        """An auditee has no create right on audits."""
        with self.assertRaises(AccessError):
            self.env["ls.audit.schedule"].with_user(
                self.user_auditee
            ).create(
                {
                    "name": "Unauthorised Audit",
                    "audit_type_id": self.audit_type.id,
                    "area_ids": [(6, 0, self.area.ids)],
                    "objective": "x",
                    "scope": "x",
                    "lead_auditor_id": self.user_lead.id,
                    "date_planned": self.today,
                    "company_id": self.company.id,
                }
            )

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_auditee_cannot_configure_audit_types(self):
        """An auditee has no write right on the configuration."""
        with self.assertRaises(AccessError):
            self.audit_type.with_user(self.user_auditee).write(
                {"name": "Renamed"}
            )

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_auditor_cannot_delete_a_finding(self):
        """An auditor has no delete right on findings."""
        finding = self._create_finding()
        with self.assertRaises(AccessError):
            finding.with_user(self.user_auditor).unlink()

    def test_manager_can_configure_audit_types(self):
        """A manager can maintain the configuration."""
        self.audit_type.with_user(self.user_manager).write(
            {"name": "Renamed by manager"}
        )
        self.assertEqual(self.audit_type.name, "Renamed by manager")

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_auditee_sees_only_their_own_findings(self):
        """The auditee record rule hides other people's findings."""
        own = self._create_finding(auditee_id=self.user_auditee.id)
        other = self._create_finding(
            auditee_id=self.user_other_auditee.id,
            area_id=self.area.id,
        )
        visible = self.env["ls.audit.finding"].with_user(
            self.user_auditee
        ).search([])
        self.assertIn(own, visible)
        self.assertNotIn(other, visible)

    def test_auditor_sees_every_finding(self):
        """The auditor record rule grants visibility on all findings."""
        own = self._create_finding(auditee_id=self.user_auditee.id)
        other = self._create_finding(
            auditee_id=self.user_other_auditee.id,
            area_id=self.area.id,
        )
        visible = self.env["ls.audit.finding"].with_user(
            self.user_auditor
        ).search([])
        self.assertIn(own, visible)
        self.assertIn(other, visible)

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_auditee_sees_only_audits_they_take_part_in(self):
        """The auditee record rule hides unrelated audits."""
        unrelated = self._create_audit(
            name="Unrelated Audit",
            area_ids=[(6, 0, self.area_other.ids)],
            auditee_ids=[(6, 0, self.user_other_auditee.ids)],
        )
        visible = self.env["ls.audit.schedule"].with_user(
            self.user_auditee
        ).search([])
        self.assertIn(self.audit, visible)
        self.assertNotIn(unrelated, visible)

    @mute_logger("odoo.addons.base.models.ir_rule")
    def test_auditee_does_not_see_a_draft_report(self):
        """Draft reports stay confidential to the audit team."""
        report = self._create_report()
        visible = self.env["ls.audit.report"].with_user(
            self.user_auditee
        ).search([])
        self.assertNotIn(report, visible)

    def test_every_model_has_an_access_rule(self):
        """No model of this module is left without an access rule."""
        model_names = [
            "ls.audit.type",
            "ls.audit.area",
            "ls.audit.auditor",
            "ls.audit.finding.category",
            "ls.audit.checklist",
            "ls.audit.checklist.line",
            "ls.audit.program",
            "ls.audit.schedule",
            "ls.audit.response",
            "ls.audit.finding",
            "ls.audit.report",
            "ls.audit.checklist.load",
            "ls.audit.finding.response",
            "ls.audit.cancel",
        ]
        for model_name in model_names:
            with self.subTest(model=model_name):
                count = self.env["ir.model.access"].search_count(
                    [("model_id.model", "=", model_name)]
                )
                self.assertGreater(
                    count, 0, "No ACL defined for %s" % model_name
                )

    def test_multi_company_rules_are_global(self):
        """Every multi-company rule applies to all users.

        A record rule is global when it carries no group, which is exactly
        what makes the company isolation impossible to bypass by adding a
        group to a user.
        """
        rule_xmlids = [
            "rule_ls_audit_program_company",
            "rule_ls_audit_schedule_company",
            "rule_ls_audit_finding_company",
            "rule_ls_audit_report_company",
            "rule_ls_audit_response_company",
        ]
        for xmlid in rule_xmlids:
            with self.subTest(rule=xmlid):
                rule = self.env.ref("ls_audit.%s" % xmlid)
                self.assertFalse(rule.groups)

    def test_group_rules_carry_a_group(self):
        """Every non-global rule is attached to at least one group."""
        rule_xmlids = [
            "rule_ls_audit_finding_auditee_own",
            "rule_ls_audit_finding_auditor_all",
            "rule_ls_audit_schedule_auditee_own",
            "rule_ls_audit_report_auditee_distributed",
        ]
        for xmlid in rule_xmlids:
            with self.subTest(rule=xmlid):
                rule = self.env.ref("ls_audit.%s" % xmlid)
                self.assertTrue(rule.groups)
