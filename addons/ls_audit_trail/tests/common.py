# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Shared fixtures for the ``ls_audit_trail`` test suite.

``res.partner`` is used as the audited model throughout the suite. It is part of
``base``, it owns fields of several different types, and auditing it exercises
exactly the same code path as auditing any Life Sciences model, without adding a
dependency on a module that is not installed.
"""

from odoo.tests.common import TransactionCase, new_test_user


class AuditTrailCase(TransactionCase):
    """Base class providing an audited model and the three audit roles."""

    @classmethod
    def setUpClass(cls):
        """Build the company, the users and the audit rule used by the suite."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.log_model = cls.env["ls.audit_trail.log"]
        cls.line_model = cls.env["ls.audit_trail.log.line"]
        cls.rule_model = cls.env["ls.audit_trail.rule"]
        cls.partner_model = cls.env["ir.model"]._get("res.partner")

        cls.field_name = cls.env["ir.model.fields"]._get("res.partner", "name")
        cls.field_email = cls.env["ir.model.fields"]._get("res.partner", "email")
        cls.field_comment = cls.env["ir.model.fields"]._get("res.partner", "comment")

        # Membership is granted with the group xml ids rather than with a domain
        # on the group field of res.users, because new_test_user accepts group
        # xml ids and that interface is stable across Odoo releases.
        cls.user_viewer = new_test_user(
            cls.env,
            login="ls_at_viewer",
            groups="base.group_user,ls_audit_trail.group_ls_audit_trail_viewer",
        )
        cls.user_auditor = new_test_user(
            cls.env,
            login="ls_at_auditor",
            groups="base.group_user,ls_audit_trail.group_ls_audit_trail_auditor",
        )
        cls.user_admin = new_test_user(
            cls.env,
            login="ls_at_admin",
            groups="base.group_user,ls_audit_trail.group_ls_audit_trail_admin",
        )
        cls.user_plain = new_test_user(
            cls.env, login="ls_at_plain", groups="base.group_user"
        )

    def _activate_rule(self, field_ids=None, **overrides):
        """Create an active audit rule on ``res.partner``.

        :param field_ids: list of ``ir.model.fields`` identifiers, or ``None``
            to audit every eligible field.
        :param overrides: extra field values for the rule.
        :return: the created ``ls.audit_trail.rule`` record.
        """
        values = {
            "name": "Test rule on res.partner",
            "model_id": self.partner_model.id,
            "log_create": True,
            "log_write": True,
            "log_unlink": True,
        }
        if field_ids is not None:
            values["field_ids"] = [(6, 0, field_ids)]
        values.update(overrides)
        return self.rule_model.create(values)

    def _entries_for(self, record, operation=None):
        """Return the audit entries recorded for ``record``.

        :param record: the audited record.
        :param operation: optional operation filter.
        :return: an ``ls.audit_trail.log`` recordset ordered by chain position.
        """
        domain = [("model_name", "=", record._name), ("res_id", "=", record.id)]
        if operation:
            domain.append(("operation", "=", operation))
        return self.log_model.sudo().search(domain, order="sequence_number asc")
