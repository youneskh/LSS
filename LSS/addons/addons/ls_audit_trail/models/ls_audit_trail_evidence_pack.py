# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).
"""Evidence pack: a sealed, self-describing export of audit trail entries."""

from __future__ import annotations

import base64
import csv
import io
import zipfile

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from ..tools import constants, serialization


class LsAuditTrailEvidencePack(models.Model):
    """A sealed archive of audit entries, produced for a reviewer or inspector.

    A pack is defined while it is in the ``draft`` state, generated once, and is
    then immutable. Generation produces a ZIP archive containing three files:

    ``audit_entries.json``
        The complete entries, including every digest, in canonical JSON.

    ``audit_entries.csv``
        One row per field change, for review in a spreadsheet application.

    ``manifest.json``
        The selection criteria, the number of exported entries, the chain range,
        the SHA-256 digest of each of the two files above, and the outcome of an
        integrity verification executed over the exported range.

    The digest of the archive itself is stored on the record, so a reviewer can
    confirm that the file they received is the file that was produced.
    """

    _name = "ls.audit_trail.evidence_pack"
    _inherit = ["mail.thread"]
    _description = "Audit Trail Evidence Pack"
    _order = "create_date desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        default=lambda self: _("New"),
        copy=False,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("generated", "Generated"),
        ],
        string="Status",
        required=True,
        default="draft",
        readonly=True,
        index=True,
        tracking=True,
    )
    active = fields.Boolean(default=True,
                            help=(
                                "Packs are never deleted. Archiving hides a superseded pack while "
                                "keeping it available for inspection."),
                            )
    purpose = fields.Text(required=True,
                          tracking=True,
                          help=(
                              "Documented reason for producing the pack, for example the "
                              "inspection or the investigation it supports."),
                          )
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 ondelete="restrict",
                                 help="Company whose audit chain is exported.",)
    date_from = fields.Datetime(
        string="From",
        required=True,
        help="Earliest event date included in the pack.",
    )
    date_to = fields.Datetime(
        string="To",
        required=True,
        help="Latest event date included in the pack.",
    )
    model_names = fields.Char(
        string="Model Filter",
        help=(
            "Comma separated list of technical model names. Leave empty to "
            "include every audited model."
        ),
    )
    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="ls_audit_trail_evidence_pack_user_rel",
        column1="pack_id",
        column2="user_id",
        string="User Filter",
        help="Leave empty to include the operations of every user.",
    )
    entry_count = fields.Integer(
        string="Exported Entries",
        readonly=True,
    )
    line_count = fields.Integer(
        string="Exported Field Changes",
        readonly=True,
    )
    first_sequence = fields.Integer(
        string="First Chain Position",
        readonly=True,
    )
    last_sequence = fields.Integer(
        string="Last Chain Position",
        readonly=True,
    )
    pack_digest = fields.Char(
        string="Archive Digest",
        size=constants.DIGEST_LENGTH,
        readonly=True,
        copy=False,
        help="SHA-256 digest of the generated ZIP archive.",
    )
    verification_id = fields.Many2one(
        comodel_name="ls.audit_trail.verification",
        string="Integrity Verification",
        readonly=True,
        ondelete="set null",
        copy=False,
        help="Verification run executed over the exported range at generation time.",
    )
    verification_result = fields.Selection(
        string="Integrity Result",
        related="verification_id.result",
        readonly=True,
    )
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Archive",
        readonly=True,
        ondelete="restrict",
        copy=False,
    )
    generated_by = fields.Many2one(comodel_name="res.users", readonly=True,
                                   ondelete="restrict",
                                   copy=False,)
    generated_on = fields.Datetime(readonly=True,
                                   copy=False,)

    @api.constrains("date_from", "date_to")
    def _check_date_range(self):
        """Reject an inverted date range."""
        for pack in self:
            if pack.date_from and pack.date_to and pack.date_from > pack.date_to:
                raise ValidationError(
                    _("The start of the range must not be later than its end.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the reference of every new pack."""
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.audit_trail.evidence_pack"
                ) or _("New")
        return super().create(vals_list)

    def write(self, vals):
        """Allow modifications only while the pack is a draft.

        Archiving and unarchiving remain available after generation, so that a
        superseded pack can be hidden without being destroyed.

        :param vals: field values requested by the caller.
        :return: ``True``.
        :raise AccessError: when a generated pack is modified.
        """
        always_allowed = {"active", "message_main_attachment_id"}
        if set(vals) - always_allowed:
            generated = self.filtered(lambda pack: pack.state == "generated")
            if generated:
                raise AccessError(
                    _(
                        "The evidence packs %(packs)s have been generated and "
                        "are immutable.",
                        packs=", ".join(generated.mapped("name")),
                    )
                )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_audit_trail_evidence_pack(self):
        """Reject every deletion.

        :raise AccessError: always.
        """
        raise AccessError(
            _(
                "Evidence packs cannot be deleted. Archive the pack instead, "
                "which keeps it available for inspection."
            )
        )

    def _ls_entry_domain(self):
        """Build the search domain selecting the entries of the pack.

        :return: an Odoo search domain.
        """
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("event_datetime", ">=", self.date_from),
            ("event_datetime", "<=", self.date_to),
        ]
        if self.model_names:
            names = [
                name.strip() for name in self.model_names.split(",") if name.strip()
            ]
            if names:
                domain.append(("model_name", "in", names))
        if self.user_ids:
            domain.append(("user_id", "in", self.user_ids.ids))
        return domain

    def _ls_entry_payloads(self, entries):
        """Build the exportable representation of ``entries``.

        :param entries: an ``ls.audit_trail.log`` recordset.
        :return: a list of dictionaries, one per entry.
        """
        self.ensure_one()
        payloads = []
        for entry in entries:
            payloads.append(
                {
                    "sequence_number": entry.sequence_number,
                    "entry_type": entry.entry_type,
                    "event_datetime": fields.Datetime.to_string(entry.event_datetime),
                    "company": entry.company_id.display_name,
                    "user_login": entry.user_login,
                    "user_name": entry.user_id.display_name,
                    "remote_addr": entry.remote_addr or "",
                    "model_name": entry.model_name,
                    "res_id": entry.res_id,
                    "res_name": entry.res_name or "",
                    "operation": entry.operation or "",
                    "payload_digest": entry.payload_digest or "",
                    "hash_prev": entry.hash_prev or "",
                    "hash_current": entry.hash_current or "",
                    "purged_from_sequence": entry.purged_from_sequence,
                    "purged_to_sequence": entry.purged_to_sequence,
                    "purged_entry_count": entry.purged_entry_count,
                    "purged_aggregate_digest": entry.purged_aggregate_digest or "",
                    "purge_reason": entry.purge_reason or "",
                    "lines": [
                        {
                            "field_name": line.field_name,
                            "field_label": line.field_label,
                            "field_type": line.field_type,
                            "old_value_technical": line.old_value_technical or "",
                            "new_value_technical": line.new_value_technical or "",
                            "old_value_display": line.old_value_display or "",
                            "new_value_display": line.new_value_display or "",
                        }
                        for line in entry.line_ids.sorted("field_name")
                    ],
                }
            )
        return payloads

    def _ls_build_csv(self, payloads):
        """Render one CSV row per exported field change.

        An entry that changed no field, which occurs for a creation with only
        empty values and for a retention anchor, produces a single row with
        empty field columns so that it is still visible in the CSV.

        :param payloads: the list produced by :meth:`~._ls_entry_payloads`.
        :return: the CSV document as a string.
        """
        self.ensure_one()
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(
            buffer,
            fieldnames=list(constants.EVIDENCE_CSV_COLUMNS),
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for payload in payloads:
            base_row = {
                column: payload.get(column, "")
                for column in constants.EVIDENCE_CSV_COLUMNS
            }
            if not payload["lines"]:
                writer.writerow(base_row)
                continue
            for line in payload["lines"]:
                row = dict(base_row)
                row.update(line)
                writer.writerow(
                    {
                        column: row.get(column, "")
                        for column in constants.EVIDENCE_CSV_COLUMNS
                    }
                )
        return buffer.getvalue()

    def _ls_build_manifest(self, payloads, entries_json, entries_csv, verification):
        """Describe the archive and the integrity state of its content.

        :param payloads: the list produced by :meth:`~._ls_entry_payloads`.
        :param entries_json: the JSON document written to the archive.
        :param entries_csv: the CSV document written to the archive.
        :param verification: the ``ls.audit_trail.verification`` record executed
            over the exported range.
        :return: the manifest document as a string.
        """
        self.ensure_one()
        sequences = [payload["sequence_number"] for payload in payloads]
        return serialization.canonical_json(
            {
                "format_version": "1.0",
                "producer": "ls_audit_trail 19.0.1.0.0",
                "pack_reference": self.name,
                "purpose": self.purpose,
                "generated_on": fields.Datetime.to_string(fields.Datetime.now()),
                "generated_by_login": self.env.user.login,
                "generated_by_name": self.env.user.display_name,
                "company": self.company_id.display_name,
                "selection": {
                    "date_from": fields.Datetime.to_string(self.date_from),
                    "date_to": fields.Datetime.to_string(self.date_to),
                    "model_names": self.model_names or "",
                    "user_logins": sorted(self.user_ids.mapped("login")),
                },
                "entry_count": len(payloads),
                "line_count": sum(len(payload["lines"]) for payload in payloads),
                "first_sequence": min(sequences) if sequences else 0,
                "last_sequence": max(sequences) if sequences else 0,
                "files": {
                    constants.EVIDENCE_FILE_ENTRIES_JSON: {
                        "sha256": serialization.sha256_hex(entries_json),
                        "bytes": len(entries_json.encode("utf-8")),
                    },
                    constants.EVIDENCE_FILE_ENTRIES_CSV: {
                        "sha256": serialization.sha256_hex(entries_csv),
                        "bytes": len(entries_csv.encode("utf-8")),
                    },
                },
                "integrity_verification": {
                    "reference": verification.name,
                    "result": verification.result,
                    "entries_checked": verification.entries_checked,
                    "details": verification.details or "",
                },
            }
        )

    def action_generate(self):
        """Generate the archive of the pack and seal the record.

        :return: an ``ir.actions.act_window`` dictionary reopening the pack.
        :raise UserError: when the pack is not a draft or selects no entry.
        """
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only a draft evidence pack can be generated."))
        log_model = self.env["ls.audit_trail.log"].sudo()
        entries = log_model.search(
            self._ls_entry_domain(), order="sequence_number asc"
        )
        if not entries:
            raise UserError(
                _("The selected criteria match no audit trail entry.")
            )
        verification = self.env["ls.audit_trail.verification"].sudo()._ls_run(
            company=self.company_id,
            date_from=self.date_from,
            date_to=self.date_to,
            source="manual",
        )
        payloads = self._ls_entry_payloads(entries)
        entries_json = serialization.canonical_json({"entries": payloads})
        entries_csv = self._ls_build_csv(payloads)
        manifest = self._ls_build_manifest(
            payloads, entries_json, entries_csv, verification
        )
        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(
            archive_buffer, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr(constants.EVIDENCE_FILE_ENTRIES_JSON, entries_json)
            archive.writestr(constants.EVIDENCE_FILE_ENTRIES_CSV, entries_csv)
            archive.writestr(constants.EVIDENCE_FILE_MANIFEST, manifest)
        archive_bytes = archive_buffer.getvalue()
        attachment = self.env["ir.attachment"].sudo().create(
            {
                "name": f"{self.name}.zip",
                "type": "binary",
                "mimetype": "application/zip",
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(archive_bytes),
            }
        )
        sequences = entries.mapped("sequence_number")
        self.write(
            {
                "state": "generated",
                "entry_count": len(payloads),
                "line_count": sum(len(payload["lines"]) for payload in payloads),
                "first_sequence": min(sequences),
                "last_sequence": max(sequences),
                "pack_digest": serialization.sha256_hex(archive_bytes),
                "verification_id": verification.id,
                "attachment_id": attachment.id,
                "generated_by": self.env.uid,
                "generated_on": fields.Datetime.now(),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_download(self):
        """Return an action downloading the archive of the pack.

        :return: an ``ir.actions.act_url`` dictionary.
        :raise UserError: when the pack has not been generated.
        """
        self.ensure_one()
        if not self.attachment_id:
            raise UserError(_("This evidence pack has not been generated yet."))
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{self.attachment_id.id}?download=true",
            "target": "self",
        }

    def action_verify_archive(self):
        """Recompute the digest of the stored archive and compare it.

        :return: ``True`` when the stored archive still matches its digest.
        :raise UserError: when the pack has not been generated, or when the
            stored archive no longer matches its recorded digest.
        """
        self.ensure_one()
        if not self.attachment_id or not self.pack_digest:
            raise UserError(_("This evidence pack has not been generated yet."))
        stored = base64.b64decode(self.attachment_id.sudo().datas or b"")
        recomputed = serialization.sha256_hex(stored)
        if recomputed != self.pack_digest:
            raise UserError(
                _(
                    "The stored archive of %(pack)s does not match its recorded "
                    "digest. Recorded: %(recorded)s. Recomputed: "
                    "%(recomputed)s.",
                    pack=self.name,
                    recorded=self.pack_digest,
                    recomputed=recomputed,
                )
            )
        self.message_post(
            body=_(
                "The stored archive matches its recorded digest %(digest)s.",
                digest=self.pack_digest,
            )
        )
        return True
