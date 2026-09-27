# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixture for the audit management test suite.

The fixture builds a complete environment that already satisfies every
constraint enforced by the module, in particular the impartiality rules: the
audit team, the auditees and the area owners are four distinct users.
"""

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class AuditCommon(TransactionCase):
    """Base class providing a ready-to-use audit environment."""

    @classmethod
    def setUpClass(cls):
        """Build users, configuration, checklist, programme and audit."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.today = fields.Date.context_today(cls.env["ls.audit.schedule"])

        cls.group_auditee = cls.env.ref("ls_audit.group_ls_audit_auditee")
        cls.group_auditor = cls.env.ref("ls_audit.group_ls_audit_auditor")
        cls.group_lead = cls.env.ref("ls_audit.group_ls_audit_lead_auditor")
        cls.group_manager = cls.env.ref("ls_audit.group_ls_audit_manager")

        cls.user_manager = cls._create_user(
            "test_audit_manager", "Test Audit Manager", cls.group_manager
        )
        cls.user_lead = cls._create_user(
            "test_lead_auditor", "Test Lead Auditor", cls.group_lead
        )
        cls.user_auditor = cls._create_user(
            "test_auditor", "Test Auditor", cls.group_auditor
        )
        cls.user_auditee = cls._create_user(
            "test_auditee", "Test Auditee", cls.group_auditee
        )
        cls.user_other_auditee = cls._create_user(
            "test_auditee_2", "Test Second Auditee", cls.group_auditee
        )

        cls.audit_type = cls.env["ls.audit.type"].create(
            {
                "name": "Internal System Audit",
                "code": "TEST-INT",
                "company_id": cls.company.id,
            }
        )
        cls.area_parent = cls.env["ls.audit.area"].create(
            {
                "name": "Test Site",
                "code": "TEST-SITE",
                "company_id": cls.company.id,
            }
        )
        cls.area = cls.env["ls.audit.area"].create(
            {
                "name": "Test Filling Area",
                "code": "TEST-FILL",
                "parent_id": cls.area_parent.id,
                "responsible_id": cls.user_auditee.id,
                "company_id": cls.company.id,
            }
        )
        cls.area_other = cls.env["ls.audit.area"].create(
            {
                "name": "Test Warehouse Area",
                "code": "TEST-WH",
                "parent_id": cls.area_parent.id,
                "responsible_id": cls.user_other_auditee.id,
                "company_id": cls.company.id,
            }
        )

        cls.qualification_lead = cls.env["ls.audit.auditor"].create(
            {
                "user_id": cls.user_lead.id,
                "is_lead_auditor": True,
                "qualification_date": cls.today - relativedelta(years=1),
                "expiry_date": cls.today + relativedelta(years=2),
                "company_id": cls.company.id,
            }
        )
        cls.qualification_auditor = cls.env["ls.audit.auditor"].create(
            {
                "user_id": cls.user_auditor.id,
                "is_lead_auditor": False,
                "qualification_date": cls.today - relativedelta(months=6),
                "expiry_date": cls.today + relativedelta(years=1),
                "company_id": cls.company.id,
            }
        )

        cls.category_major = cls.env.ref("ls_audit.finding_category_major")
        cls.category_minor = cls.env.ref("ls_audit.finding_category_minor")
        cls.category_observation = cls.env.ref(
            "ls_audit.finding_category_observation"
        )

        cls.checklist = cls._create_approved_checklist()

        cls.program = cls.env["ls.audit.program"].create(
            {
                "name": "Test Programme",
                "date_start": cls.today - relativedelta(months=6),
                "date_end": cls.today + relativedelta(months=6),
                "responsible_id": cls.user_manager.id,
                "company_id": cls.company.id,
            }
        )
        cls.audit = cls._create_audit()

    @classmethod
    def _create_user(cls, login, name, group):
        """Create an internal user belonging to ``group``.

        The field is named ``group_ids`` because Odoo 19 renamed
        ``res.users.groups_id`` to ``group_ids``.

        :param login: unique login of the user.
        :param name: display name of the user.
        :param group: ``res.groups`` record to assign.
        :return: the created user.
        :rtype: recordset
        """
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": name,
                    "login": login,
                    "email": "%s@example.com" % login,
                    "company_id": cls.company.id,
                    "company_ids": [(6, 0, cls.company.ids)],
                    "group_ids": [(6, 0, group.ids)],
                }
            )
        )

    @classmethod
    def _create_approved_checklist(cls):
        """Create and approve a three-question checklist.

        :return: the approved checklist.
        :rtype: recordset
        """
        checklist = cls.env["ls.audit.checklist"].create(
            {
                "name": "Test Documentation Checklist",
                "code": "TEST-CHK",
                "version": 1,
                "audit_type_id": cls.audit_type.id,
                "company_id": cls.company.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 10,
                            "name": "Are current procedures available?",
                            "reference_clause": "SOP-QA-001",
                            "is_mandatory": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 20,
                            "name": "Are obsolete documents withdrawn?",
                            "reference_clause": "SOP-QA-001",
                            "is_mandatory": True,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 30,
                            "name": "Are corrections traceable?",
                            "reference_clause": "SOP-QA-007",
                            "is_mandatory": False,
                        },
                    ),
                ],
            }
        )
        checklist.action_approve()
        return checklist

    @classmethod
    def _create_audit(cls, **overrides):
        """Create a valid audit in the planned status.

        :param overrides: values overriding the defaults.
        :return: the created audit.
        :rtype: recordset
        """
        values = {
            "name": "Test Audit",
            "program_id": cls.program.id,
            "audit_type_id": cls.audit_type.id,
            "area_ids": [(6, 0, cls.area.ids)],
            "objective": "Determine conformity of documentation control.",
            "scope": "Filling line 1, current year records.",
            "criteria": "SOP-QA-001, SOP-QA-007.",
            "lead_auditor_id": cls.user_lead.id,
            "auditor_ids": [(6, 0, cls.user_auditor.ids)],
            "auditee_ids": [(6, 0, cls.user_auditee.ids)],
            "date_planned": cls.today,
            "company_id": cls.company.id,
        }
        values.update(overrides)
        return cls.env["ls.audit.schedule"].create(values)

    def _load_checklist(self, audit=None, checklist=None):
        """Load a checklist into an audit through the wizard.

        :param audit: audit to load into, defaults to ``self.audit``.
        :param checklist: checklist to load, defaults to ``self.checklist``.
        :return: the created responses.
        :rtype: recordset
        """
        audit = audit or self.audit
        checklist = checklist or self.checklist
        wizard = self.env["ls.audit.checklist.load"].create(
            {
                "audit_id": audit.id,
                "checklist_id": checklist.id,
                "replace_existing": True,
            }
        )
        wizard.action_load()
        return audit.response_ids

    def _bring_audit_to_in_progress(self, audit=None):
        """Move an audit from planned to in progress.

        :param audit: audit to advance, defaults to ``self.audit``.
        :return: the advanced audit.
        :rtype: recordset
        """
        audit = audit or self.audit
        self._load_checklist(audit)
        # An audit can only be scheduled inside an approved programme.
        if audit.program_id.state == "draft":
            audit.program_id.action_approve()
        audit.action_schedule()
        audit.action_start()
        return audit

    def _assess_all_responses(self, audit=None, result="conform"):
        """Assess every mandatory question of an audit.

        :param audit: audit to assess, defaults to ``self.audit``.
        :param result: result to record on each question.
        :return: the assessed responses.
        :rtype: recordset
        """
        audit = audit or self.audit
        values = {"result": result}
        if result in ("nonconform", "observation"):
            values["evidence"] = "Evidence recorded during the audit."
        audit.response_ids.write(values)
        return audit.response_ids

    def _create_finding(self, audit=None, category=None, **overrides):
        """Create a finding on an audit.

        :param audit: audit the finding belongs to.
        :param category: finding category, defaults to the major category.
        :param overrides: values overriding the defaults.
        :return: the created finding.
        :rtype: recordset
        """
        audit = audit or self.audit
        category = category or self.category_major
        values = {
            "name": "Obsolete procedure found at the point of use",
            "audit_id": audit.id,
            "area_id": audit.area_ids[0].id,
            "category_id": category.id,
            "description": "A superseded revision was available for use.",
            "evidence": "Document SOP-PR-014 rev 2 observed at line 1.",
            "auditee_id": self.user_auditee.id,
            "raised_by_id": self.user_lead.id,
            "company_id": self.company.id,
        }
        values.update(overrides)
        return self.env["ls.audit.finding"].create(values)

    def _create_report(self, audit=None, **overrides):
        """Create a draft audit report.

        :param audit: audit the report concludes.
        :param overrides: values overriding the defaults.
        :return: the created report.
        :rtype: recordset
        """
        audit = audit or self.audit
        values = {
            "name": "Test Audit Report",
            "audit_id": audit.id,
            "executive_summary": "The audit was conducted as planned.",
            "conclusion": "The area conforms with the exception of the "
                          "findings listed.",
            "prepared_by_id": self.user_lead.id,
            "distribution_ids": [(6, 0, self.user_auditee.ids)],
            "company_id": self.company.id,
        }
        values.update(overrides)
        return self.env["ls.audit.report"].create(values)
