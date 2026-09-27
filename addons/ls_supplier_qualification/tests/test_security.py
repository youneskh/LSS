# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Access-right and record-rule tests."""
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import SupplierQualificationCommon


@tagged("post_install", "-at_install")
class TestSecurity(SupplierQualificationCommon):
    """Verify that each group is limited to its intended operations."""

    def test_viewer_can_read(self):
        """A viewer reads dossiers."""
        dossier = self.qualification.with_user(self.user_viewer)
        self.assertTrue(dossier.name)

    def test_viewer_cannot_write(self):
        """A viewer cannot modify a dossier."""
        with self.assertRaises(AccessError):
            self.qualification.with_user(self.user_viewer).write({
                "notes": "<p>Attempted change.</p>",
            })

    def test_viewer_cannot_create(self):
        """A viewer cannot open a dossier."""
        with self.assertRaises(AccessError):
            self.env["ls.supplier.qualification"].with_user(
                self.user_viewer
            ).create({
                "partner_id": self.partner_two.id,
                "category_id": self.category_no_audit.id,
            })

    def test_assessor_can_create_dossier(self):
        """An assessor opens dossiers."""
        dossier = self.env["ls.supplier.qualification"].with_user(
            self.user_assessor
        ).create({
            "partner_id": self.partner_two.id,
            "category_id": self.category_no_audit.id,
        })
        self.assertTrue(dossier)

    def test_assessor_cannot_delete_dossier(self):
        """An assessor cannot delete a dossier."""
        with self.assertRaises(AccessError):
            self.qualification.with_user(self.user_assessor).unlink()

    def test_assessor_cannot_configure(self):
        """An assessor cannot create configuration records."""
        with self.assertRaises(AccessError):
            self.env["ls.supplier.category"].with_user(
                self.user_assessor
            ).create({
                "name": "Forbidden Category",
                "code": "FORB",
            })

    def test_manager_can_configure(self):
        """A manager creates configuration records."""
        category = self.env["ls.supplier.category"].with_user(
            self.user_manager
        ).create({
            "name": "Manager Category",
            "code": "MGRC",
        })
        self.assertTrue(category)

    def test_signature_log_is_read_only_for_everyone(self):
        """No group is granted write access on the signature log."""
        access = self.env["ir.model.access"].search([
            ("model_id.model", "=", "ls.supplier.signature"),
        ])
        self.assertTrue(access)
        for rule in access:
            self.assertFalse(rule.perm_write)
            self.assertFalse(rule.perm_create)
            self.assertFalse(rule.perm_unlink)

    def test_assessment_ownership_rule(self):
        """An assessor cannot modify an assessment owned by a colleague."""
        assessment = self.env["ls.supplier.assessment"].with_user(
            self.user_assessor
        ).create({
            "qualification_id": self.qualification.id,
            "template_id": self.template.id,
            "assessor_id": self.user_assessor.id,
        })
        with self.assertRaises(AccessError):
            assessment.with_user(self.user_assessor_two).write({
                "conclusion": "Attempted change.",
            })

    def test_manager_overrides_ownership_rule(self):
        """A manager modifies any assessment."""
        assessment = self.env["ls.supplier.assessment"].with_user(
            self.user_assessor
        ).create({
            "qualification_id": self.qualification.id,
            "template_id": self.template.id,
            "assessor_id": self.user_assessor.id,
        })
        assessment.with_user(self.user_manager).write({
            "conclusion": "Change made by the manager.",
        })
        self.assertEqual(assessment.conclusion, "Change made by the manager.")

    def test_multi_company_rule_present(self):
        """Every company-scoped model carries a global multi-company rule."""
        models = [
            "ls.supplier.qualification",
            "ls.supplier.material",
            "ls.supplier.assessment",
            "ls.supplier.audit",
            "ls.supplier.audit.finding",
            "ls.supplier.performance",
            "ls.supplier.review",
            "ls.supplier.signature",
        ]
        for model_name in models:
            rules = self.env["ir.rule"].search([
                ("model_id.model", "=", model_name),
            ])
            self.assertTrue(
                any("company_id" in rule.domain_force for rule in rules),
                "No multi-company rule found on %s" % model_name,
            )
