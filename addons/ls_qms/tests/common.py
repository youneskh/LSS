# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Shared fixtures for the Life Sciences QMS test suite."""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user


class LsQmsCommon(TransactionCase):
    """Users, department and document factories used by every test case."""

    @classmethod
    def setUpClass(cls):
        """Create the four QMS roles and a department."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.user_viewer = new_test_user(
            cls.env,
            login="ls_qms_viewer",
            groups="ls_qms.group_ls_qms_viewer",
            name="QMS Viewer",
        )
        cls.user_author = new_test_user(
            cls.env,
            login="ls_qms_author",
            groups="ls_qms.group_ls_qms_user",
            name="QMS Author",
        )
        cls.user_approver = new_test_user(
            cls.env,
            login="ls_qms_approver",
            groups="ls_qms.group_ls_qms_approver",
            name="QMS Approver",
        )
        cls.user_manager = new_test_user(
            cls.env,
            login="ls_qms_manager",
            groups="ls_qms.group_ls_qms_manager",
            name="QMS Manager",
        )
        cls.department = cls.env["hr.department"].create(
            {"name": "Quality Assurance Test"}
        )
        cls.today = fields.Date.context_today(cls.env["ls.qms.policy"])

    @classmethod
    def _create_sop(cls, **values):
        """Return a draft procedure with every mandatory section filled."""
        defaults = {
            "name": "Test Procedure",
            "author_id": cls.user_author.id,
            "department_id": cls.department.id,
            "purpose": "<p>Purpose of the procedure.</p>",
            "scope": "Scope of the procedure.",
            "procedure": "<p>Step one. Step two.</p>",
            "review_period_months": 24,
        }
        defaults.update(values)
        return cls.env["ls.qms.sop"].create(defaults)

    @classmethod
    def _create_policy(cls, **values):
        """Return a draft quality policy with a statement."""
        defaults = {
            "name": "Test Quality Policy",
            "author_id": cls.user_author.id,
            "policy_statement": "<p>We comply with applicable requirements.</p>",
            "scope": "All activities of the site.",
        }
        defaults.update(values)
        return cls.env["ls.qms.policy"].create(defaults)

    @classmethod
    def _create_quality_plan(cls, **values):
        """Return a draft quality plan carrying one control line."""
        defaults = {
            "name": "Test Quality Plan",
            "author_id": cls.user_author.id,
            "subject": "Line 1",
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "stage": "Compression",
                        "characteristic": "Tablet mass",
                        "specification": "250 mg plus or minus 5 percent",
                        "control_method": "Analytical balance",
                        "frequency": "Every 30 minutes",
                    },
                )
            ],
        }
        defaults.update(values)
        return cls.env["ls.qms.quality_plan"].create(defaults)

    @classmethod
    def _create_objective(cls, **values):
        """Return a draft quality objective of the increase kind."""
        defaults = {
            "name": "Test Objective",
            "responsible_id": cls.user_author.id,
            "department_id": cls.department.id,
            "direction": "increase",
            "baseline_value": 70.0,
            "target_value": 90.0,
            "date_start": cls.today - relativedelta(months=6),
            "date_target": cls.today + relativedelta(months=6),
        }
        defaults.update(values)
        return cls.env["ls.qms.objective"].create(defaults)

    @classmethod
    def _create_quality_record(cls, **values):
        """Return a draft quality record."""
        defaults = {
            "name": "Test Management Review",
            "record_type": "management_review",
            "author_id": cls.user_author.id,
            "date_record": cls.today,
            "retention_period_months": 60,
        }
        defaults.update(values)
        return cls.env["ls.qms.quality_record"].create(defaults)

    def _publish(self, document):
        """Run a document through the full approval path.

        :param document: controlled document in draft state.
        :return: the same document, published.
        """
        document.with_user(self.user_author).action_submit_for_review()
        document.with_user(self.user_approver).action_approve()
        document.with_user(self.user_approver).action_publish()
        return document
