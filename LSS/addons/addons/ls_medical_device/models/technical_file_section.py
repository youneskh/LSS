# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Sections of a technical documentation set, and their templates.

Two models are defined here. ``ls.md.technical_file_section_template`` holds the
reusable outline of an annex, shipped as editable data. ``ls.md.
technical_file_section`` holds the sections of one concrete documentation set,
each recording where the underlying evidence is held and whether the section is
complete.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import constants


class LsMdTechnicalFileSectionTemplate(models.Model):
    """Reusable outline of an annex of Regulation (EU) 2017/745."""

    _name = "ls.md.technical_file_section_template"
    _description = "Technical Documentation Section Template"
    _order = "annex_reference, sequence, section_number"

    name = fields.Char(string="Section Title", required=True, translate=True)
    section_number = fields.Char(required=True,
                                 help="Number of the section within the annex, for example '1.1'.",)
    annex_reference = fields.Selection(
        selection=constants.TECHNICAL_FILE_ANNEX_SELECTION,
        string="Annex",
        required=True,
        default="annex_ii",
    )
    sequence = fields.Integer(default=10)
    is_mandatory = fields.Boolean(
        string="Mandatory",
        default=True,
        help=(
            "Mandatory sections must be marked complete before the "
            "documentation set can be approved."
        ),
    )
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)

    _annex_section_unique = models.Constraint(
        "UNIQUE(annex_reference, section_number)",
        "A section number can appear only once per annex in the template.",
    )

    @api.depends("section_number", "name")
    def _compute_display_name(self):
        """Show the section number followed by its title."""
        for record in self:
            record.display_name = (
                f"{record.section_number or ''} {record.name or ''}".strip()
            )


class LsMdTechnicalFileSection(models.Model):
    """One section of one technical documentation set."""

    _name = "ls.md.technical_file_section"
    _description = "Technical Documentation Section"
    _order = "technical_file_id, sequence, section_number"

    technical_file_id = fields.Many2one(
        comodel_name="ls.md.technical_file",
        string="Technical Documentation",
        required=True,
        ondelete="cascade",
        index=True,
    )
    device_id = fields.Many2one(comodel_name="ls.md.device", related="technical_file_id.device_id",
                                store=True,
                                index=True,)
    company_id = fields.Many2one(comodel_name="res.company", related="technical_file_id.company_id",
                                 store=True,
                                 index=True,)
    sequence = fields.Integer(default=10)
    section_number = fields.Char(required=True)
    name = fields.Char(string="Section Title", required=True)
    description = fields.Text()
    is_mandatory = fields.Boolean(string="Mandatory", default=True)
    is_complete = fields.Boolean(
        string="Complete",
        help="The evidence required by this section is available and referenced.",
    )
    not_applicable = fields.Boolean(help=(
            "The section does not apply to this device. A justification is "
            "required, as Annex II point 4(a) requires an explanation where a "
            "requirement is considered not to apply."
        ),
    )
    not_applicable_justification = fields.Text(string="Justification")
    evidence_reference = fields.Char(help=(
            "Reference of the document or record holding the evidence for this "
            "section."),
    )
    evidence_location = fields.Char(help="Location at which the referenced evidence is held.",)
    responsible_id = fields.Many2one(comodel_name="res.users", help="User responsible for the content of this section.",)
    review_date = fields.Date(string="Last Reviewed")
    notes = fields.Text()

    _file_section_unique = models.Constraint(
        "UNIQUE(technical_file_id, section_number)",
        "A section number can appear only once in a documentation set.",
    )

    @api.depends("section_number", "name")
    def _compute_display_name(self):
        """Show the section number followed by its title."""
        for record in self:
            record.display_name = (
                f"{record.section_number or ''} {record.name or ''}".strip()
            )

    @api.onchange("not_applicable")
    def _onchange_not_applicable(self):
        """Mark a section that does not apply as complete.

        A section that does not apply cannot be filled in, so it is treated as
        satisfied once a justification has been recorded. The justification
        itself is enforced by the constraint below.
        """
        for record in self:
            if record.not_applicable:
                record.is_complete = True

    @api.constrains("not_applicable", "not_applicable_justification")
    def _check_not_applicable_justification(self):
        """Require a justification whenever a section is declared not applicable."""
        for record in self:
            if record.not_applicable and not record.not_applicable_justification:
                raise ValidationError(
                    self.env._(
                        "Section '%(section)s' is declared not applicable. "
                        "Record the justification required by Annex II point "
                        "4(a).",
                        section=record.display_name,
                    )
                )

    @api.constrains("is_complete", "evidence_reference", "not_applicable")
    def _check_evidence_reference(self):
        """Require an evidence reference before a section can be complete."""
        for record in self:
            if (
                record.is_complete
                and not record.not_applicable
                and not record.evidence_reference
            ):
                raise ValidationError(
                    self.env._(
                        "Section '%(section)s' cannot be marked complete "
                        "without an evidence reference.",
                        section=record.display_name,
                    )
                )

    def _check_parent_editable(self):
        """Raise when the parent documentation set is closed for editing."""
        for record in self:
            parent = record.technical_file_id
            # Sections are frozen from the submission for review, so that the
            # reviewer approves the documentation that was submitted.
            if parent and parent.state != "draft":
                raise UserError(
                    self.env._(
                        "Technical documentation '%(name)s' is closed for "
                        "editing. Create a new version to change its sections.",
                        name=parent.name or "",
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Reject the creation of a section in a closed documentation set."""
        records = super().create(vals_list)
        records._check_parent_editable()
        return records

    def write(self, vals):
        """Reject changes to a section of a closed documentation set."""
        self._check_parent_editable()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_md_technical_file_section(self):
        """Reject deletion of a section of a closed documentation set."""
        self._check_parent_editable()
