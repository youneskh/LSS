# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Shared setup for the tests of the ``ls_medical_device`` module.

Users are created with ``new_test_user`` rather than by writing the groups
relation directly. The name of the field holding the groups of ``res.users``
in Odoo 19.0 could not be verified from official documentation during
preparation of this module, and ``new_test_user`` accepts the group external
identifiers as a string, so the tests do not depend on that field name.
"""

from odoo.tests.common import TransactionCase, new_test_user

GROUP_VIEWER = "ls_medical_device.group_ls_md_viewer"
GROUP_USER = "ls_medical_device.group_ls_md_user"
GROUP_REGULATORY = "ls_medical_device.group_ls_md_regulatory"
GROUP_MANAGER = "ls_medical_device.group_ls_md_manager"


class MedicalDeviceCommon(TransactionCase):
    """Base class providing devices, users and configuration records."""

    @classmethod
    def setUpClass(cls):
        """Create the fixtures shared by every test case."""
        super().setUpClass()
        cls.company = cls.env.company

        cls.class_i = cls.env.ref("ls_medical_device.device_class_i")
        cls.class_iia = cls.env.ref("ls_medical_device.device_class_iia")
        cls.class_iib = cls.env.ref("ls_medical_device.device_class_iib")
        cls.class_iii = cls.env.ref("ls_medical_device.device_class_iii")

        cls.user_viewer = new_test_user(
            cls.env,
            login="ls_md_viewer",
            groups=GROUP_VIEWER,
            name="Medical Device Viewer",
        )
        cls.user_user = new_test_user(
            cls.env,
            login="ls_md_user",
            groups=GROUP_USER,
            name="Medical Device User",
        )
        cls.user_second = new_test_user(
            cls.env,
            login="ls_md_user_two",
            groups=GROUP_USER,
            name="Medical Device Second User",
        )
        cls.user_regulatory = new_test_user(
            cls.env,
            login="ls_md_regulatory",
            groups=GROUP_REGULATORY,
            name="Medical Device Regulatory Affairs",
        )
        cls.user_manager = new_test_user(
            cls.env,
            login="ls_md_manager",
            groups=GROUP_MANAGER,
            name="Medical Device Manager",
        )

        cls.notified_body = cls.env["ls.md.notified_body"].create(
            {
                "name": "Test Conformity Assessment Body",
                "identification_number": "TEST-0001",
            }
        )

        cls.device_iia = cls.env["ls.md.device"].create(
            {
                "name": "Test Class IIa Device",
                "device_class_id": cls.class_iia.id,
                "intended_purpose": "Intended purpose recorded for the test.",
            }
        )
        cls.device_iii = cls.env["ls.md.device"].create(
            {
                "name": "Test Class III Implantable Device",
                "device_class_id": cls.class_iii.id,
                "is_implantable": True,
                "intended_purpose": "Intended purpose recorded for the test.",
            }
        )
        cls.device_i = cls.env["ls.md.device"].create(
            {
                "name": "Test Class I Device",
                "device_class_id": cls.class_i.id,
                "intended_purpose": "Intended purpose recorded for the test.",
            }
        )

    def _approve_as_other_user(self, record, author_field="author_id"):
        """Approve a record as the regulatory user, avoiding self-approval.

        :param record: the record to approve.
        :param author_field: name of the field holding the author.
        """
        if author_field in record._fields and record[author_field] == self.env.user:
            record.write({author_field: self.user_second.id})
        record.with_user(self.user_regulatory).action_approve()
        return record
