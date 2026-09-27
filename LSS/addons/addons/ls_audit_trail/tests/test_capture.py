# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Capture tests: what the engine records, and what it deliberately does not."""

from odoo.tests import tagged

from ..tools import constants

from .common import AuditTrailCase


@tagged("post_install", "-at_install")
class TestCapture(AuditTrailCase):
    """Verify the content of the entries produced by each ORM operation."""

    def test_create_is_captured(self):
        """A creation produces one entry carrying the initial values."""
        self._activate_rule(field_ids=(self.field_name + self.field_email).ids)
        partner = self.env["res.partner"].create(
            {"name": "Aseptic Filling Ltd", "email": "qa@example.org"}
        )
        entries = self._entries_for(partner, constants.OPERATION_CREATE)
        self.assertEqual(len(entries), 1)
        entry = entries
        self.assertEqual(entry.user_id, self.env.user)
        self.assertEqual(entry.user_login, self.env.user.login)
        self.assertEqual(entry.model_name, "res.partner")
        self.assertEqual(entry.res_id, partner.id)
        self.assertEqual(entry.entry_type, constants.ENTRY_TYPE_DATA)
        values = {line.field_name: line.new_value_technical for line in entry.line_ids}
        self.assertEqual(values["name"], "Aseptic Filling Ltd")
        self.assertEqual(values["email"], "qa@example.org")
        for line in entry.line_ids:
            self.assertEqual(line.old_value_technical, "")

    def test_write_is_captured_with_old_and_new_values(self):
        """A modification records the value before and after the write."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Batch 001"})
        partner.write({"name": "Batch 001 rev B"})
        entries = self._entries_for(partner, constants.OPERATION_WRITE)
        self.assertEqual(len(entries), 1)
        line = entries.line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.field_name, "name")
        self.assertEqual(line.old_value_technical, "Batch 001")
        self.assertEqual(line.new_value_technical, "Batch 001 rev B")

    def test_write_without_change_produces_no_entry(self):
        """Writing the value a field already holds records nothing."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Unchanged"})
        partner.write({"name": "Unchanged"})
        self.assertFalse(self._entries_for(partner, constants.OPERATION_WRITE))

    def test_write_of_unaudited_field_produces_no_entry(self):
        """A field outside the rule is not captured."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Scoped"})
        partner.write({"email": "outside@example.org"})
        self.assertFalse(self._entries_for(partner, constants.OPERATION_WRITE))

    def test_excluded_field_is_not_captured(self):
        """A field listed as excluded is never captured, even in all-field mode."""
        self._activate_rule(
            excluded_field_ids=[(6, 0, self.field_comment.ids)]
        )
        partner = self.env["res.partner"].create({"name": "Exclusion"})
        partner.write({"comment": "<p>internal remark</p>"})
        entries = self._entries_for(partner, constants.OPERATION_WRITE)
        self.assertFalse(entries.line_ids.filtered(
            lambda line: line.field_name == "comment"
        ))

    def test_unlink_is_captured_before_deletion(self):
        """A deletion records the last known values of the record."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "To be removed"})
        partner_id = partner.id
        partner.unlink()
        entries = self.log_model.sudo().search(
            [
                ("model_name", "=", "res.partner"),
                ("res_id", "=", partner_id),
                ("operation", "=", constants.OPERATION_UNLINK),
            ]
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries.res_name, "To be removed")
        line = entries.line_ids.filtered(lambda item: item.field_name == "name")
        self.assertEqual(line.old_value_technical, "To be removed")
        self.assertEqual(line.new_value_technical, "")

    def test_operation_flags_are_honoured(self):
        """Only the operations enabled on the rule are captured."""
        self._activate_rule(
            field_ids=self.field_name.ids,
            log_create=False,
            log_write=True,
            log_unlink=False,
        )
        partner = self.env["res.partner"].create({"name": "Write only"})
        self.assertFalse(self._entries_for(partner, constants.OPERATION_CREATE))
        partner.write({"name": "Write only rev B"})
        self.assertEqual(
            len(self._entries_for(partner, constants.OPERATION_WRITE)), 1
        )

    def test_many2one_is_stored_as_identifier_and_name(self):
        """A many2one records the identifier technically and the name for humans."""
        field_country = self.env["ir.model.fields"]._get("res.partner", "country_id")
        self._activate_rule(field_ids=field_country.ids)
        country = self.env.ref("base.be")
        partner = self.env["res.partner"].create({"name": "Relational"})
        partner.write({"country_id": country.id})
        line = self._entries_for(partner, constants.OPERATION_WRITE).line_ids
        self.assertEqual(line.new_value_technical, str(country.id))
        self.assertEqual(line.new_value_display, country.display_name)

    def test_binary_is_stored_as_fingerprint_only(self):
        """A binary field records a digest and a length, never the content."""
        field_image = self.env["ir.model.fields"]._get("res.partner", "image_1920")
        self._activate_rule(field_ids=field_image.ids)
        partner = self.env["res.partner"].create({"name": "Binary"})
        # A valid one pixel RGB PNG, base64 encoded (generated with Pillow;
        # the image field decodes and resizes it, so it must be well formed).
        payload = (
            b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4"
            b"z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
        )
        partner.write({"image_1920": payload})
        line = self._entries_for(partner, constants.OPERATION_WRITE).line_ids
        self.assertTrue(line.new_value_technical.startswith("sha256:"))
        self.assertIn(";bytes:", line.new_value_technical)
        self.assertNotIn("iVBOR", line.new_value_technical)

    def test_selection_display_uses_the_label(self):
        """A selection field records the key technically and the label for humans."""
        field_type = self.env["ir.model.fields"]._get("res.partner", "type")
        self._activate_rule(field_ids=field_type.ids)
        partner = self.env["res.partner"].create({"name": "Selection"})
        partner.write({"type": "invoice"})
        line = self._entries_for(partner, constants.OPERATION_WRITE).line_ids
        self.assertEqual(line.new_value_technical, "invoice")
        self.assertTrue(line.new_value_display)
        self.assertNotEqual(line.new_value_display, "invoice")

    def test_line_context_columns_are_populated(self):
        """The denormalised context of a line matches its parent entry."""
        self._activate_rule(field_ids=self.field_name.ids)
        partner = self.env["res.partner"].create({"name": "Denormalised"})
        entry = self._entries_for(partner, constants.OPERATION_CREATE)
        line = entry.line_ids
        self.assertEqual(line.company_id, entry.company_id)
        self.assertEqual(line.event_datetime, entry.event_datetime)
        self.assertEqual(line.model_name, entry.model_name)
        self.assertEqual(line.res_id, entry.res_id)
        self.assertEqual(line.user_id, entry.user_id)
        self.assertEqual(line.operation, entry.operation)
        self.assertEqual(line.sequence_number, entry.sequence_number)

    def test_batch_create_produces_one_entry_per_record(self):
        """A batched creation produces exactly one entry per record."""
        self._activate_rule(field_ids=self.field_name.ids)
        partners = self.env["res.partner"].create(
            [{"name": f"Batched {index}"} for index in range(5)]
        )
        for partner in partners:
            with self.subTest(partner=partner.id):
                self.assertEqual(
                    len(self._entries_for(partner, constants.OPERATION_CREATE)), 1
                )

    def test_engine_models_are_never_audited(self):
        """A capture never causes the engine to audit its own models."""
        self._activate_rule(field_ids=self.field_name.ids)
        self.env["res.partner"].create({"name": "No recursion"})
        self.assertFalse(
            self.log_model.sudo().search_count(
                [("model_name", "like", "ls.audit_trail")]
            )
        )
