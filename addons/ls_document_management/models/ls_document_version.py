# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Immutable versions of a controlled document.

Each version stores one file, the reason for the change and a SHA-256
checksum of the file content. Once created, the content of a version can no
longer be modified: a change of content requires a new version.
"""

import base64
import hashlib

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

PROTECTED_FIELDS = (
    "document_id",
    "version_number",
    "content",
    "filename",
    "file_size",
    "checksum_sha256",
    "change_summary",
    "change_reason",
    "author_id",
)


class LsDocumentVersion(models.Model):
    """One immutable revision of a controlled document."""

    _name = "ls.document.version"
    _description = "Life Sciences Document Version"
    _order = "document_id, version_number desc"

    document_id = fields.Many2one(comodel_name="ls.document.document", required=True,
                                  index=True,
                                  ondelete="cascade",)
    version_number = fields.Integer(
        string="Version",
        required=True,
        readonly=True,
        copy=False,
        help="Sequential revision number, assigned automatically.",
    )
    company_id = fields.Many2one(comodel_name="res.company", related="document_id.company_id",
                                 store=True,
                                 index=True,)
    content = fields.Binary(
        string="File",
        attachment=True,
        required=True,
        help="Binary content of this version.",
    )
    filename = fields.Char(
        string="File Name",
        required=True,
    )
    file_size = fields.Integer(
        string="File Size (bytes)",
        readonly=True,
    )
    checksum_sha256 = fields.Char(
        string="SHA-256 Checksum",
        readonly=True,
        index=True,
        help=(
            "Hexadecimal SHA-256 digest of the file content, computed when "
            "the version is created. It supports verification that the "
            "stored content has not been altered."
        ),
    )
    change_summary = fields.Text(
        string="Summary of Change",
        required=True,
        help="Description of what changed compared with the previous version.",
    )
    change_reason = fields.Text(
        string="Reason for Change",
    )
    author_id = fields.Many2one(comodel_name="res.users", required=True,
                                readonly=True,
                                default=lambda self: self.env.user,)
    is_superseded = fields.Boolean(
        string="Superseded",
        readonly=True,
        copy=False,
        help="Set when a later version has been published in its place.",
    )
    approval_ids = fields.One2many(
        comodel_name="ls.document.approval",
        inverse_name="version_id",
        string="Approvals",
    )
    is_current = fields.Boolean(
        string="Effective",
        compute="_compute_is_current",
        store=True,
    )

    _document_version_uniq = models.Constraint(
        "UNIQUE(document_id, version_number)",
        "The version number must be unique for a given document.",
    )
    _version_number_positive = models.Constraint(
        "CHECK(version_number > 0)",
        "The version number must be strictly greater than zero.",
    )

    @api.depends("document_id.current_version_id")
    def _compute_is_current(self):
        """Flag the version that is currently in force."""
        for version in self:
            version.is_current = version.document_id.current_version_id == version

    @api.depends("document_id.reference", "version_number")
    def _compute_display_name(self):
        """Display the version as ``NUMBER v3``."""
        for version in self:
            version.display_name = "%s v%s" % (
                version.document_id.reference or "",
                version.version_number or 0,
            )

    @api.constrains("content")
    def _check_content_present(self):
        """Reject versions created without a file."""
        for version in self:
            if not version.content:
                raise ValidationError(
                    _("A document version must contain a file.")
                )

    @api.model
    def _build_file_metadata(self, content):
        """Return the size and SHA-256 digest of a base64 encoded content.

        :param content: base64 encoded file content, as stored by Odoo.
        :return: dict with the ``file_size`` and ``checksum_sha256`` keys, or
            an empty dict when no content was supplied.
        """
        if not content:
            return {}
        raw = base64.b64decode(content)
        return {
            "file_size": len(raw),
            "checksum_sha256": hashlib.sha256(raw).hexdigest(),
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the next version number and compute the file metadata."""
        next_numbers = {}
        for vals in vals_list:
            document_id = vals.get("document_id")
            if document_id and not vals.get("version_number"):
                if document_id not in next_numbers:
                    last = self.search(
                        [("document_id", "=", document_id)],
                        order="version_number desc",
                        limit=1,
                    )
                    next_numbers[document_id] = last.version_number or 0
                next_numbers[document_id] += 1
                vals["version_number"] = next_numbers[document_id]
            vals.update(self._build_file_metadata(vals.get("content")))
        return super().create(vals_list)

    def write(self, vals):
        """Reject any modification of the controlled content of a version."""
        modified = [field for field in PROTECTED_FIELDS if field in vals]
        if modified:
            raise UserError(
                _(
                    "A document version is a controlled record and cannot be "
                    "modified. Create a new version instead. Rejected "
                    "field(s): %(fields)s.",
                    fields=", ".join(sorted(modified)),
                )
            )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_document_version(self):
        """Allow deletion only of unused versions of a draft document."""
        for version in self:
            if version.is_current:
                raise UserError(
                    _(
                        "Version %(version)s of document '%(reference)s' is "
                        "the effective version and cannot be deleted.",
                        version=version.version_number,
                        reference=version.document_id.reference,
                    )
                )
            if version.document_id.state != "draft":
                raise UserError(
                    _(
                        "Version %(version)s cannot be deleted because "
                        "document '%(reference)s' is not in draft status.",
                        version=version.version_number,
                        reference=version.document_id.reference,
                    )
                )
            if version.approval_ids:
                raise UserError(
                    _(
                        "Version %(version)s cannot be deleted because it "
                        "carries approval records.",
                        version=version.version_number,
                    )
                )

    def verify_integrity(self):
        """Recompute the checksum and compare it with the stored digest.

        :return: ``True`` when every checked version matches its stored
            digest.
        :raises UserError: when a mismatch is detected.
        """
        for version in self:
            metadata = self._build_file_metadata(version.content)
            if metadata.get("checksum_sha256") != version.checksum_sha256:
                raise UserError(
                    _(
                        "Integrity check failed for version %(version)s of "
                        "document '%(reference)s'. The stored content does "
                        "not match the recorded SHA-256 checksum.",
                        version=version.version_number,
                        reference=version.document_id.reference,
                    )
                )
        return True
