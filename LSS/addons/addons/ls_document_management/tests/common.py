# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared fixtures for the ls_document_management test suite."""

import base64

from odoo.tests.common import TransactionCase

DEMO_FILE_CONTENT = b"Life Sciences Suite controlled document test content."


class LsDocumentCommon(TransactionCase):
    """Base class providing users, folders, policies and helper methods."""

    @classmethod
    def setUpClass(cls):
        """Create the reference data shared by every test case."""
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.group_viewer = cls.env.ref(
            "ls_document_management.group_ls_document_viewer"
        )
        cls.group_editor = cls.env.ref(
            "ls_document_management.group_ls_document_editor"
        )
        cls.group_approver = cls.env.ref(
            "ls_document_management.group_ls_document_approver"
        )
        cls.group_manager = cls.env.ref(
            "ls_document_management.group_ls_document_manager"
        )

        cls.user_viewer = cls._create_user("ls_viewer", cls.group_viewer)
        cls.user_editor = cls._create_user("ls_editor", cls.group_editor)
        cls.user_approver = cls._create_user("ls_approver", cls.group_approver)
        cls.user_approver_2 = cls._create_user(
            "ls_approver_2", cls.group_approver
        )
        cls.user_manager = cls._create_user("ls_manager", cls.group_manager)

        cls.policy = cls.env["ls.document.retention_policy"].create(
            {
                "name": "Test policy - 5 years from publication",
                "code": "TEST-5Y",
                "duration_value": 5,
                "duration_unit": "year",
                "retention_trigger": "publication",
                "notice_period_days": 90,
                "end_of_life_action": "notify",
            }
        )
        cls.folder = cls.env["ls.document.folder"].create(
            {
                "name": "Test Root Folder",
                "retention_policy_id": cls.policy.id,
            }
        )
        cls.child_folder = cls.env["ls.document.folder"].create(
            {
                "name": "Test Child Folder",
                "parent_id": cls.folder.id,
            }
        )

    @classmethod
    def _create_user(cls, login, group):
        """Create an internal user belonging to a single document role.

        :param login: login of the user to create.
        :param group: ``res.groups`` record granting the document role.
        :return: the created ``res.users`` record.
        """
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": login,
                    "login": login,
                    "email": "%s@example.org" % login,
                    "group_ids": [
                        (4, cls.env.ref("base.group_user").id),
                        (4, group.id),
                    ],
                }
            )
        )

    @classmethod
    def _encoded_content(cls, payload=None):
        """Return a base64 encoded payload suitable for a Binary field.

        :param payload: raw bytes to encode, defaults to the module fixture.
        :return: base64 encoded bytes.
        """
        return base64.b64encode(payload or DEMO_FILE_CONTENT)

    def _create_document(self, user=None, **values):
        """Create a controlled document with sensible defaults.

        :param user: optional ``res.users`` record to act as.
        :param values: field values overriding the defaults.
        :return: the created ``ls.document.document`` record.
        """
        model = self.env["ls.document.document"]
        if user:
            model = model.with_user(user)
        defaults = {
            "name": "Test Document",
            "folder_id": self.folder.id,
            "retention_policy_id": self.policy.id,
        }
        defaults.update(values)
        return model.create(defaults)

    def _create_version(self, document, user=None, **values):
        """Create a version on a document with sensible defaults.

        :param document: ``ls.document.document`` record.
        :param user: optional ``res.users`` record to act as.
        :param values: field values overriding the defaults.
        :return: the created ``ls.document.version`` record.
        """
        model = self.env["ls.document.version"]
        if user:
            model = model.with_user(user)
        defaults = {
            "document_id": document.id,
            "filename": "procedure.txt",
            "content": self._encoded_content(),
            "change_summary": "Initial issue.",
        }
        defaults.update(values)
        return model.create(defaults)

    def _approve_all(self, document):
        """Grant every pending approval of a document.

        :param document: ``ls.document.document`` record.
        """
        for approval in document.approval_ids.filtered(
            lambda item: item.state == "pending"
        ):
            approval.with_user(approval.approver_id).action_approve()
