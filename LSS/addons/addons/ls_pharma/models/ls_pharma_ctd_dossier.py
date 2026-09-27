# Copyright 2026 Life Sciences Suite Architecture Team
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
"""Common Technical Document dossiers."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..constants import CTD_DOSSIER_STATES, CTD_DOSSIER_TYPES


class LsPharmaCtdDossier(models.Model):
    """A regulatory dossier organised in the Common Technical Document format.

    ICH M4(R4) organises the Common Technical Document into five modules.
    Module 1 carries the administrative information and the prescribing
    information and is specific to each region; its content and format are
    specified by the relevant regulatory authority. Modules 2 to 5 are
    intended to be common to all regions and carry, respectively, the
    summaries, the quality information, the nonclinical study reports and
    the clinical study reports.

    Source: ICH M4(R4), Organisation of the Common Technical Document for the
    Registration of Pharmaceuticals for Human Use.

    This model tracks the preparation status of each section of a dossier.
    It does not generate, validate or transmit an electronic submission
    sequence.
    """

    _name = "ls.pharma.ctd_dossier"
    _description = "Common Technical Document Dossier"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_submission desc, name desc"

    _name_company_uniq = models.Constraint(
        "UNIQUE(name, company_id)",
        "The dossier reference must be unique per company.",
    )

    name = fields.Char(
        string="Dossier Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env._("New"),
    )
    title = fields.Char(required=True, tracking=True)
    product_id = fields.Many2one(comodel_name="product.product", required=True,
                                 index=True,
                                 tracking=True,)
    dossier_type = fields.Selection(selection=CTD_DOSSIER_TYPES, required=True,
                                    default="new",
                                    tracking=True,)
    authority_name = fields.Char(
        string="Regulatory Authority",
        required=True,
        tracking=True,
        help=(
            "Authority to which the dossier is submitted. The field is free "
            "text so that any national authority can be recorded without the "
            "module presuming a list of authorities."
        ),
    )
    authority_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Authority Contact",
    )
    marketing_auth_holder_id = fields.Many2one(
        comodel_name="res.partner",
        string="Marketing Authorisation Holder",
    )
    dossier_version = fields.Char(string="Version", required=True, default="1.0")
    date_submission = fields.Date(string="Submission Date", tracking=True)
    date_decision = fields.Date(string="Decision Date", tracking=True)
    authorisation_number = fields.Char(tracking=True, copy=False)
    section_ids = fields.One2many(
        comodel_name="ls.pharma.ctd.section",
        inverse_name="dossier_id",
        string="Sections",
    )
    section_count = fields.Integer(
        string="Sections", compute="_compute_progress", store=True
    )
    section_complete_count = fields.Integer(
        string="Sections Complete", compute="_compute_progress", store=True
    )
    completion_percentage = fields.Float(
        string="Completion (%)",
        compute="_compute_progress",
        store=True,
        digits=(16, 2),
        help="Percentage of sections marked complete. The value ranges from 0 to 100.",
    )
    deficiency_count = fields.Integer(
        string="Sections in Deficiency", compute="_compute_progress", store=True
    )
    state = fields.Selection(
        selection=CTD_DOSSIER_STATES,
        string="Status",
        default="draft",
        required=True,
        copy=False,
        tracking=True,
        index=True,
    )
    note = fields.Text(string="Notes")
    company_id = fields.Many2one(comodel_name="res.company", required=True,
                                 default=lambda self: self.env.company,
                                 index=True,)
    active = fields.Boolean(default=True)

    @api.depends("section_ids.state")
    def _compute_progress(self):
        """Compute the preparation progress of the dossier."""
        for dossier in self:
            sections = dossier.section_ids
            complete = sections.filtered(
                lambda section: section.state == "complete"
            )
            dossier.section_count = len(sections)
            dossier.section_complete_count = len(complete)
            dossier.completion_percentage = (
                (len(complete) / len(sections)) * 100.0 if sections else 0.0
            )
            dossier.deficiency_count = len(
                sections.filtered(lambda section: section.state == "deficiency")
            )

    @api.depends("name", "title")
    def _compute_display_name(self):
        """Show the dossier reference together with its title."""
        for dossier in self:
            if dossier.title:
                dossier.display_name = "%s - %s" % (dossier.name, dossier.title)
            else:
                dossier.display_name = dossier.name or ""

    @api.constrains("date_submission", "date_decision")
    def _check_dates(self):
        """Reject a decision date that precedes the submission date."""
        for dossier in self:
            if (
                dossier.date_submission
                and dossier.date_decision
                and dossier.date_decision < dossier.date_submission
            ):
                raise ValidationError(
                    self.env._(
                        "The decision on dossier %(name)s cannot predate its "
                        "submission.",
                        name=dossier.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the dossier reference from the dedicated sequence."""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == self.env._("New"):
                sequence = self.env["ir.sequence"].next_by_code(
                    "ls.pharma.ctd_dossier"
                )
                vals["name"] = sequence or self.env._("New")
        return super().create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ls_unlink_check_ls_pharma_ctd_dossier(self):
        """Forbid the deletion of a dossier that has been submitted."""
        for dossier in self:
            if dossier.state not in ("draft", "in_preparation"):
                raise UserError(
                    self.env._(
                        "Dossier %(name)s has been submitted and can no "
                        "longer be deleted.",
                        name=dossier.name,
                    )
                )

    def action_load_template(self):
        """Create the standard section structure of ICH M4(R4).

        The template records shipped with this module are copied into the
        dossier.  Sections that already exist under the same code are left
        untouched.

        :returns: the created sections.
        :rtype: recordset of ``ls.pharma.ctd.section``
        """
        section_model = self.env["ls.pharma.ctd.section"]
        template_sections = section_model.search(
            [("is_template", "=", True)], order="module, sequence, code"
        )
        created = section_model
        for dossier in self:
            if dossier.state not in ("draft", "in_preparation"):
                raise UserError(
                    self.env._(
                        "The template can only be loaded while dossier "
                        "%(name)s is in preparation.",
                        name=dossier.name,
                    )
                )
            existing_codes = set(dossier.section_ids.mapped("code"))
            values_list = [
                {
                    "dossier_id": dossier.id,
                    "module": template.module,
                    "code": template.code,
                    "name": template.name,
                    "sequence": template.sequence,
                    "is_template": False,
                }
                for template in template_sections
                if template.code not in existing_codes
            ]
            if values_list:
                created |= section_model.create(values_list)
        return created

    def action_start_preparation(self):
        """Move the selected dossiers to the preparation state."""
        for dossier in self:
            if dossier.state != "draft":
                raise UserError(
                    self.env._(
                        "Dossier %(name)s is not in the draft state.",
                        name=dossier.name,
                    )
                )
        self.write({"state": "in_preparation"})
        return True

    def action_mark_ready(self):
        """Declare the selected dossiers ready for submission."""
        for dossier in self:
            if dossier.state != "in_preparation":
                raise UserError(
                    self.env._(
                        "Dossier %(name)s is not in preparation.",
                        name=dossier.name,
                    )
                )
            pending = dossier.section_ids.filtered(
                lambda section: section.state
                not in ("ready", "complete", "submitted")
            )
            if pending:
                raise UserError(
                    self.env._(
                        "Dossier %(name)s still has %(count)s section(s) that "
                        "are not ready.",
                        name=dossier.name,
                        count=len(pending),
                    )
                )
        self.write({"state": "ready"})
        return True

    def action_submit(self):
        """Record the submission of the selected dossiers."""
        for dossier in self:
            if dossier.state != "ready":
                raise UserError(
                    self.env._(
                        "Dossier %(name)s must be ready before it can be "
                        "submitted.",
                        name=dossier.name,
                    )
                )
            dossier.write(
                {
                    "state": "submitted",
                    "date_submission": dossier.date_submission
                    or fields.Date.context_today(self),
                }
            )
            dossier.section_ids.filtered(
                lambda section: section.state == "ready"
            ).write({"state": "submitted"})
        return True

    def action_record_deficiency(self):
        """Record that a deficiency has been received on the dossiers."""
        for dossier in self:
            if dossier.state != "submitted":
                raise UserError(
                    self.env._(
                        "A deficiency can only be recorded on a submitted "
                        "dossier. Dossier %(name)s is in state %(state)s.",
                        name=dossier.name,
                        state=dossier.state,
                    )
                )
        self.write({"state": "deficiency"})
        return True

    def action_approve(self):
        """Record the approval of the selected dossiers."""
        for dossier in self:
            if dossier.state not in ("submitted", "deficiency"):
                raise UserError(
                    self.env._(
                        "Dossier %(name)s cannot be approved from state "
                        "%(state)s.",
                        name=dossier.name,
                        state=dossier.state,
                    )
                )
            if not dossier.authorisation_number:
                raise UserError(
                    self.env._(
                        "The authorisation number must be recorded before "
                        "dossier %(name)s can be approved.",
                        name=dossier.name,
                    )
                )
            dossier.write(
                {
                    "state": "approved",
                    "date_decision": dossier.date_decision
                    or fields.Date.context_today(self),
                }
            )
        return True

    def action_withdraw(self):
        """Record the withdrawal of the selected dossiers."""
        self.write({"state": "withdrawn"})
        return True
