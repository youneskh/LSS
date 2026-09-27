# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Technical documentation records.

Annex II of Regulation (EU) 2017/745 sets out the minimum content and structure
of the technical documentation. Annex III sets out the technical documentation
on post-market surveillance. Annex XIII Section 2 covers custom-made devices.

This model holds the index of a technical documentation set: which annex it
follows, which version it is, its approval status, and a line per section
recording where the underlying evidence is held and whether that section is
complete. The module is an index and a completeness control; the underlying
documents remain in the document management system of the organisation and are
referenced here.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdTechnicalFile(models.Model):
    """Index of one technical documentation set for one device."""

    _name = "ls.md.technical_file"
    _description = "Medical Device Technical Documentation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "device_id, version desc, id desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
    )
    title = fields.Char(required=True, tracking=True)
    device_id = fields.Many2one(comodel_name="ls.md.device", required=True,
                                ondelete="cascade",
                                index=True,
                                tracking=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="device_id.company_id",
                                 store=True,
                                 index=True,)
    annex_reference = fields.Selection(
        selection=constants.TECHNICAL_FILE_ANNEX_SELECTION,
        string="Annex",
        required=True,
        default="annex_ii",
        tracking=True,
        help="Annex of Regulation (EU) 2017/745 whose structure this set follows.",
    )
    version = fields.Integer(default=1, required=True, tracking=True)
    state = fields.Selection(
        selection=constants.REGULATORY_DOC_STATE_SELECTION,
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
        copy=False,
    )
    compilation_date = fields.Date(default=fields.Date.context_today,
                                   tracking=True,)
    responsible_id = fields.Many2one(comodel_name="res.users", default=lambda self: self.env.user,
                                     tracking=True,)
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approved By",
        readonly=True,
        copy=False,
        tracking=True,
    )
    approval_date = fields.Datetime(readonly=True, copy=False, tracking=True)
    section_ids = fields.One2many(
        comodel_name="ls.md.technical_file_section",
        inverse_name="technical_file_id",
        string="Sections",
        copy=True,
    )
    section_count = fields.Integer(compute="_compute_completeness", store=True)
    complete_section_count = fields.Integer(
        string="Complete Sections", compute="_compute_completeness", store=True
    )
    missing_mandatory_count = fields.Integer(
        string="Missing Mandatory Sections",
        compute="_compute_completeness",
        store=True,
        help="Number of mandatory sections that are not marked complete.",
    )
    completeness_ratio = fields.Float(
        string="Completeness",
        compute="_compute_completeness",
        store=True,
        digits=(16, 4),
        help=(
            "Proportion of sections marked complete, expressed as a value "
            "between zero and one."
        ),
    )
    retention_until = fields.Date(
        string="Retain Until",
        related="device_id.documentation_retention_until",
        store=True,
        help=(
            "End of the retention period computed from the device withdrawal "
            "date and the retention duration of Article 10(8)."
        ),
    )
    storage_location = fields.Char(help=(
            "Location at which the technical documentation set is held, for "
            "example a document management system path or an archive "
            "reference."),
    )
    notes = fields.Text()

    _version_positive = models.Constraint(
        "CHECK(version > 0)",
        "The technical documentation version must be strictly positive.",
    )
    _device_annex_version_unique = models.Constraint(
        "UNIQUE(device_id, annex_reference, version)",
        "A device cannot have two technical documentation sets with the same "
        "annex and version.",
    )

    # ------------------------------------------------------------------
    # Compute methods
    # ------------------------------------------------------------------
    @api.depends("section_ids", "section_ids.is_complete", "section_ids.is_mandatory")
    def _compute_completeness(self):
        """Derive the completeness indicators of the documentation set."""
        for record in self:
            sections = record.section_ids
            complete = sections.filtered(lambda section: section.is_complete)
            mandatory = sections.filtered(lambda section: section.is_mandatory)
            record.section_count = len(sections)
            record.complete_section_count = len(complete)
            record.missing_mandatory_count = len(
                mandatory.filtered(lambda section: not section.is_complete)
            )
            record.completeness_ratio = (
                len(complete) / len(sections) if sections else 0.0
            )

    @api.depends("name", "title", "version")
    def _compute_display_name(self):
        """Show the reference, the title and the version."""
        for record in self:
            record.display_name = self.env._(
                "%(reference)s - %(title)s (v%(version)s)",
                reference=record.name or "",
                title=record.title or "",
                version=record.version,
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains("annex_reference", "device_id")
    def _check_custom_made_annex(self):
        """Match the annex to the custom-made status of the device.

        Annex XIII Section 2 applies to custom-made devices; Annex II applies to
        devices other than custom-made devices. The constraint records the
        mismatch rather than silently accepting a set filed under the wrong
        structure.
        """
        for record in self:
            device = record.device_id
            if not device:
                continue
            if device.is_custom_made and record.annex_reference == "annex_ii":
                raise ValidationError(
                    self.env._(
                        "Device '%(device)s' is custom-made. Technical "
                        "documentation for custom-made devices follows Annex "
                        "XIII rather than Annex II.",
                        device=device.display_name,
                    )
                )
            if not device.is_custom_made and record.annex_reference == "annex_xiii":
                raise ValidationError(
                    self.env._(
                        "Device '%(device)s' is not custom-made and cannot use "
                        "the Annex XIII documentation structure.",
                        device=device.display_name,
                    )
                )

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Allocate the reference and seed the section template."""
        placeholder = self.env._("New")
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == placeholder:
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "ls.md.technical_file"
                ) or self.env._("TDF/UNSEQUENCED")
        records = super().create(vals_list)
        records._seed_sections_from_template()
        return records

    def _seed_sections_from_template(self):
        """Copy the shipped section template into a new documentation set.

        Sections are only seeded when the set has none, so that a set created
        with explicit section lines or duplicated from an existing set keeps
        its own content.
        """
        template_model = self.env["ls.md.technical_file_section_template"]
        section_model = self.env["ls.md.technical_file_section"]
        for record in self:
            if record.section_ids:
                continue
            templates = template_model.search(
                [("annex_reference", "=", record.annex_reference)]
            )
            section_model.create(
                [
                    {
                        "technical_file_id": record.id,
                        "sequence": template.sequence,
                        "section_number": template.section_number,
                        "name": template.name,
                        "description": template.description,
                        "is_mandatory": template.is_mandatory,
                    }
                    for template in templates
                ]
            )
        return True

    def write(self, vals):
        """Freeze the identity of an approved documentation set."""
        protected = {"title", "device_id", "version", "annex_reference"}
        if protected.intersection(vals):
            for record in self:
                if record.state == "approved":
                    raise UserError(
                        self.env._(
                            "Technical documentation '%(name)s' is approved. "
                            "Create a new version to record further changes.",
                            name=record.name or "",
                        )
                    )
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_technical_file(self):
        """Prevent deletion of approved or superseded documentation sets."""
        for record in self:
            if record.state not in ("draft", "cancelled"):
                raise UserError(
                    self.env._(
                        "Technical documentation '%(name)s' can no longer be "
                        "deleted. Cancel it instead.",
                        name=record.name or "",
                    )
                )

    def copy_data(self, default=None):
        """Create the next version of the documentation set when duplicating."""
        default = dict(default or {})
        default.setdefault("name", self.env._("New"))
        default.setdefault("state", "draft")
        default.setdefault("approver_id", False)
        default.setdefault("approval_date", False)
        if len(self) == 1:
            default.setdefault("version", self.version + 1)
        return super().copy_data(default=default)

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def _check_approval_authority(self):
        """Raise unless the current user may approve regulatory records."""
        if not (
            self.env.user.has_group(constants.GROUP_REGULATORY)
            or self.env.user.has_group(constants.GROUP_MANAGER)
        ):
            raise UserError(
                self.env._(
                    "Approving technical documentation requires the Medical "
                    "Devices Regulatory Affairs or Manager access level."
                )
            )

    def action_submit_for_review(self):
        """Move a draft documentation set to review."""
        for record in self:
            if record.state != "draft":
                raise UserError(
                    self.env._(
                        "Only draft technical documentation can be submitted "
                        "for review."
                    )
                )
            if not record.section_ids:
                raise UserError(
                    self.env._(
                        "Technical documentation '%(name)s' contains no "
                        "section.",
                        name=record.name or "",
                    )
                )
            record.state = "under_review"
        return True

    def action_approve(self):
        """Approve the documentation set once all mandatory sections are complete."""
        self._check_approval_authority()
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only technical documentation under review can be "
                        "approved."
                    )
                )
            if record.responsible_id == self.env.user:
                raise UserError(
                    self.env._(
                        "The person responsible for '%(name)s' cannot approve it "
                        "(segregation of duties).",
                        name=record.display_name or "",
                    )
                )
            if record.missing_mandatory_count:
                raise UserError(
                    self.env._(
                        "Technical documentation '%(name)s' has %(count)s "
                        "mandatory section(s) that are not marked complete.",
                        name=record.name or "",
                        count=record.missing_mandatory_count,
                    )
                )
            record.write(
                {
                    "state": "approved",
                    "approver_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),
                }
            )
        return True

    def action_supersede(self):
        """Mark an approved documentation set as superseded."""
        self._check_approval_authority()
        for record in self:
            if record.state != "approved":
                raise UserError(
                    self.env._(
                        "Only approved technical documentation can be "
                        "superseded."
                    )
                )
            record.state = "superseded"
        return True

    def action_cancel(self):
        """Cancel a documentation set that will not be completed."""
        for record in self:
            if record.state in ("superseded", "cancelled"):
                raise UserError(
                    self.env._(
                        "Technical documentation '%(name)s' is already closed.",
                        name=record.name or "",
                    )
                )
            record.state = "cancelled"
        return True

    def action_reset_to_draft(self):
        """Return a documentation set under review to draft."""
        for record in self:
            if record.state != "under_review":
                raise UserError(
                    self.env._(
                        "Only technical documentation under review can be "
                        "returned to draft."
                    )
                )
            record.state = "draft"
        return True
