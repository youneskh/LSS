# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Shared fixtures for the CAPA test suite."""

from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class CapaCommon(TransactionCase):
    """Base class providing users, a category and CAPA helper builders."""

    @classmethod
    def setUpClass(cls):
        """Create the shared fixtures used across the CAPA test suite."""
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.today = fields.Date.context_today(cls.env["ls.capa.issue"])

        cls.group_viewer = cls.env.ref("ls_capa.group_ls_capa_viewer")
        cls.group_investigator = cls.env.ref(
            "ls_capa.group_ls_capa_investigator"
        )
        cls.group_coordinator = cls.env.ref(
            "ls_capa.group_ls_capa_coordinator"
        )
        cls.group_manager = cls.env.ref("ls_capa.group_ls_capa_manager")

        cls.user_viewer = cls._create_user("capa_viewer", cls.group_viewer)
        cls.user_investigator = cls._create_user(
            "capa_investigator", cls.group_investigator
        )
        cls.user_coordinator = cls._create_user(
            "capa_coordinator", cls.group_coordinator
        )
        cls.user_manager = cls._create_user("capa_manager", cls.group_manager)

        cls.category = cls.env["ls.capa.category"].create(
            {
                "name": "Test Category",
                "code": "TESTCAT",
                "default_due_days": 30,
                "company_id": cls.company.id,
            }
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @classmethod
    def _user_groups_field(cls):
        """Return the name of the groups many2many field on ``res.users``.

        Odoo 19 renamed several ``groups_id`` fields to ``group_ids``. The
        field name is resolved from the registry rather than hard-coded so
        that the test suite does not depend on which variant is present.

        :return: the technical field name.
        :rtype: str
        """
        user_fields = cls.env["res.users"]._fields
        return "group_ids" if "group_ids" in user_fields else "groups_id"

    @classmethod
    def _create_user(cls, login, group):
        """Create an internal user belonging to ``group``.

        :param str login: login of the new user.
        :param group: ``res.groups`` record the user is added to.
        :return: the created user.
        :rtype: res.users
        """
        groups = cls.env.ref("base.group_user") | group
        vals = {
            "name": login,
            "login": login,
            "email": "%s@example.org" % login,
            "company_id": cls.company.id,
            "company_ids": [fields.Command.set(cls.company.ids)],
            cls._user_groups_field(): [fields.Command.set(groups.ids)],
        }
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True, mail_create_nosubscribe=True)
            .create(vals)
        )

    def _make_issue(self, **overrides):
        """Create a CAPA record with sensible defaults.

        :param overrides: field values overriding the defaults.
        :return: the created CAPA record.
        :rtype: ls.capa.issue
        """
        vals = {
            "title": "Test CAPA",
            "description": "A quality issue used by the automated tests.",
            "source": "deviation",
            "capa_type": "corrective",
            "severity": "major",
            "category_id": self.category.id,
            # Identified a month ago, so that tests can set a due date in
            # the past without breaking the due >= identified rule.
            "date_identified": self.today - timedelta(days=30),
            "owner_id": self.env.user.id,
            "company_id": self.company.id,
        }
        vals.update(overrides)
        return self.env["ls.capa.issue"].create(vals)

    def _make_root_cause(self, issue, **overrides):
        """Create a Five Whys root cause analysis attached to ``issue``.

        :param issue: the parent CAPA record.
        :param overrides: field values overriding the defaults.
        :return: the created root cause analysis.
        :rtype: ls.capa.root_cause
        """
        vals = {
            "issue_id": issue.id,
            "method": "five_whys",
            "description": "Calibration interval was not enforced.",
            "why_1": "The measurement drifted.",
        }
        vals.update(overrides)
        return self.env["ls.capa.root_cause"].create(vals)

    def _make_action(self, issue, **overrides):
        """Create a CAPA action attached to ``issue``.

        :param issue: the parent CAPA record.
        :param overrides: field values overriding the defaults.
        :return: the created action.
        :rtype: ls.capa.action
        """
        vals = {
            "issue_id": issue.id,
            "action_type": "corrective",
            "description": "Recalibrate the instrument.",
            "responsible_id": self.env.user.id,
            "date_planned": self.today + timedelta(days=10),
        }
        vals.update(overrides)
        return self.env["ls.capa.action"].create(vals)

    def _make_effectiveness(self, issue, **overrides):
        """Create an effectiveness check attached to ``issue``.

        :param issue: the parent CAPA record.
        :param overrides: field values overriding the defaults.
        :return: the created effectiveness check.
        :rtype: ls.capa.effectiveness
        """
        vals = {
            "issue_id": issue.id,
            "method": "data_review",
            "criteria": "No recurrence across twenty batches.",
            "date_planned": self.today + timedelta(days=60),
            "verifier_id": self.env.user.id,
        }
        vals.update(overrides)
        return self.env["ls.capa.effectiveness"].create(vals)

    def _advance_to_in_progress(self, issue):
        """Drive ``issue`` from Identified to In Progress.

        :param issue: the CAPA record to advance.
        :return: the action created along the way.
        :rtype: ls.capa.action
        """
        issue.impact_assessment = "No impact on released product."
        issue.action_assess()
        issue.action_start_investigation()
        self._make_root_cause(issue).action_confirm()
        issue.action_start_action_planning()
        action = self._make_action(issue)
        issue.action_start_progress()
        return action

    def _advance_to_verified(self, issue):
        """Drive ``issue`` from Identified to Verified.

        :param issue: the CAPA record to advance.
        :return: the effectiveness check concluded as effective.
        :rtype: ls.capa.effectiveness
        """
        action = self._advance_to_in_progress(issue)
        action.completion_evidence = "Calibration certificate CC-2026-091."
        action.action_done()
        issue.action_complete()
        check = self._make_effectiveness(issue)
        check.conclusion = "No recurrence observed."
        check.action_mark_effective()
        issue.action_verify()
        return check
