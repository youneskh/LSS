# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the supplier qualification test suite."""
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user

GROUP_VIEWER = "ls_supplier_qualification.group_ls_supplier_viewer"
GROUP_ASSESSOR = "ls_supplier_qualification.group_ls_supplier_assessor"
GROUP_MANAGER = "ls_supplier_qualification.group_ls_supplier_manager"


class SupplierQualificationCommon(TransactionCase):
    """Base class building a reusable qualification data set."""

    @classmethod
    def setUpClass(cls):
        """Create users, configuration and one dossier shared by the tests."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.today = fields.Date.context_today(cls.env["ls.supplier.qualification"])

        cls.user_viewer = new_test_user(
            cls.env,
            login="ls_viewer",
            name="Supplier Viewer",
            groups="base.group_user,%s" % GROUP_VIEWER,
        )
        cls.user_assessor = new_test_user(
            cls.env,
            login="ls_assessor",
            name="Supplier Assessor",
            groups="base.group_user,%s" % GROUP_ASSESSOR,
        )
        cls.user_assessor_two = new_test_user(
            cls.env,
            login="ls_assessor2",
            name="Second Assessor",
            groups="base.group_user,%s" % GROUP_ASSESSOR,
        )
        cls.user_manager = new_test_user(
            cls.env,
            login="ls_manager",
            name="Supplier Manager",
            groups="base.group_user,%s" % GROUP_MANAGER,
        )

        cls.partner = cls.env["res.partner"].create({
            "name": "Test Supplier One",
            "is_company": True,
            "email": "supplier.one@example.invalid",
        })
        cls.partner_two = cls.env["res.partner"].create({
            "name": "Test Supplier Two",
            "is_company": True,
            "email": "supplier.two@example.invalid",
        })

        cls.product = cls.env["product.product"].create({
            "name": "Test Qualified Material",
        })
        cls.product_off_scope = cls.env["product.product"].create({
            "name": "Test Non-Qualified Material",
        })

        cls.criterion_mandatory = cls.env["ls.supplier.criterion"].create({
            "name": "Test mandatory criterion",
            "code": "TST-M1",
            "domain": "qms",
            "default_weight": 2.0,
            "is_mandatory": True,
        })
        cls.criterion_optional = cls.env["ls.supplier.criterion"].create({
            "name": "Test optional criterion",
            "code": "TST-O1",
            "domain": "logistics",
            "default_weight": 1.0,
        })

        cls.template = cls.env["ls.supplier.assessment.template"].create({
            "name": "Test Template",
            "code": "TST-TPL",
            "max_score_per_criterion": 5,
            "mandatory_min_score": 3,
            "pass_threshold": 80.0,
            "conditional_threshold": 60.0,
            "line_ids": [
                (0, 0, {
                    "criterion_id": cls.criterion_mandatory.id,
                    "weight": 2.0,
                    "is_mandatory": True,
                    "sequence": 10,
                }),
                (0, 0, {
                    "criterion_id": cls.criterion_optional.id,
                    "weight": 1.0,
                    "is_mandatory": False,
                    "sequence": 20,
                }),
            ],
        })

        cls.category_no_audit = cls.env["ls.supplier.category"].create({
            "name": "Test Category Without Audit",
            "code": "TST-NA",
            "criticality": "major",
            "requires_assessment": True,
            "requires_initial_audit": False,
            "requires_periodic_audit": False,
            "requalification_interval_months": 36,
            "review_interval_months": 12,
        })
        cls.category_with_audit = cls.env["ls.supplier.category"].create({
            "name": "Test Category With Audit",
            "code": "TST-WA",
            "criticality": "critical",
            "requires_assessment": True,
            "requires_initial_audit": True,
            "requires_periodic_audit": True,
            "audit_interval_months": 24,
            "requalification_interval_months": 24,
            "review_interval_months": 12,
        })

        cls.qualification = cls.env["ls.supplier.qualification"].create({
            "partner_id": cls.partner.id,
            "category_id": cls.category_no_audit.id,
            "responsible_id": cls.user_manager.id,
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def _create_material(cls, qualification, product=None, state="qualified"):
        """Create one scope line, qualified by default."""
        material = cls.env["ls.supplier.material"].create({
            "qualification_id": qualification.id,
            "name": "Scope line for %s" % qualification.name,
            "material_type": "api",
            "product_id": product.id if product else False,
        })
        if state == "qualified":
            material.action_qualify()
        elif state != "draft":
            material.state = state
        return material

    @classmethod
    def _create_assessment(cls, qualification, assessor=None, scores=(5, 5)):
        """Create, execute and complete one assessment.

        :param qualification: dossier the assessment belongs to.
        :param assessor: user recorded as the assessor.
        :param tuple scores: score given to the mandatory then the optional
            criterion.
        :return: the completed assessment.
        """
        assessment = cls.env["ls.supplier.assessment"].create({
            "qualification_id": qualification.id,
            "template_id": cls.template.id,
            "assessor_id": (assessor or cls.user_assessor).id,
            "assessment_type": "initial",
        })
        assessment.action_load_template()
        assessment.action_start()
        mandatory_score, optional_score = scores
        for line in assessment.line_ids:
            line.score = (
                mandatory_score if line.is_mandatory else optional_score
            )
            if line.score < assessment.mandatory_min_score:
                line.comment = "Justification recorded by the test suite."
        assessment.conclusion = "Conclusion recorded by the test suite."
        assessment.action_done()
        return assessment

    @classmethod
    def _create_closed_audit(cls, qualification, lead=None, severity="minor"):
        """Create an audit, close its single finding and close the audit."""
        audit = cls.env["ls.supplier.audit"].create({
            "qualification_id": qualification.id,
            "audit_type": "on_site",
            "audit_scope": "Scope defined by the test suite.",
            "planned_date": cls.today,
            "lead_auditor_id": (lead or cls.user_assessor).id,
        })
        finding = cls.env["ls.supplier.audit.finding"].create({
            "audit_id": audit.id,
            "name": "F-01",
            "severity": severity,
            "description": "Finding raised by the test suite.",
        })
        audit.action_plan()
        audit.action_start()
        audit.action_draft_report()
        audit.outcome = "acceptable_with_actions"
        audit.conclusion = "Conclusion recorded by the test suite."
        audit.action_issue_report()
        finding.supplier_response = "Response recorded by the test suite."
        finding.action_register_response()
        finding.corrective_action = "Action recorded by the test suite."
        finding.action_due_date = cls.today + relativedelta(days=30)
        finding.action_agree_action()
        finding.action_mark_implemented()
        finding.verification_method = "Verification recorded by the test suite."
        finding.action_verify()
        finding.action_close()
        audit.action_register_response()
        audit.action_close()
        return audit

    @classmethod
    def _approve(cls, qualification, approver=None, decision="approved"):
        """Run the approval wizard on a dossier pending approval."""
        user = approver or cls.user_manager
        wizard = cls.env["ls.supplier.approve.wizard"].with_user(user).create({
            "qualification_id": qualification.id,
            "decision": decision,
            "conditions": (
                "Conditions recorded by the test suite."
                if decision == "conditional" else False
            ),
            "expiry_date": cls.today + relativedelta(months=36),
            "reason": "Justification recorded by the test suite.",
            "signature_login": user.login,
        })
        wizard.action_confirm()
        return qualification
