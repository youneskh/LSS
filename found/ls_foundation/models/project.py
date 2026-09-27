from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class LssFoundationProject(models.Model):
    _name = 'lss.foundation.project'
    _description = 'Business Establishment Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Project Name', required=True)
    company_name = fields.Char(string='Legal Company Name')
    company_type = fields.Selection([
        ('sarl', 'SARL'), ('spa', 'SPA'), ('eas', 'EAS'),
        ('suarl', 'SUARL'), ('snc', 'SNC'), ('other', 'Other'),
    ], string='Legal Form')
    sector = fields.Selection([
        ('pharma', 'Pharmaceutical'),
        ('medical_devices', 'Medical Devices'),
        ('cosmetics', 'Cosmetics'),
        ('laboratory', 'Laboratory'),
        ('pharma_packaging', 'Pharmaceutical Packaging'),
        ('medical_plastics', 'Medical Plastics'),
        ('distribution', 'Distribution'),
        ('import_export', 'Import/Export'),
    ], string='Sector', required=True)
    activity_type = fields.Selection([
        ('manufacturing', 'Manufacturing'),
        ('import', 'Import'),
        ('export', 'Export'),
        ('distribution', 'Distribution'),
        ('quality_control', 'Quality Control'),
        ('packaging', 'Packaging'),
        ('storage', 'Storage'),
        ('laboratory', 'Laboratory'),
    ], string='Activity Type', required=True)
    products = fields.Text(string='Products/Activities')

    applicable_authorities = fields.Many2many('lss.foundation.authority', string='Applicable Authorities')
    required_licenses = fields.Many2many('lss.foundation.license.type', string='Required Licenses')
    applicable_procedures = fields.Many2many('lss.foundation.procedure', string='Applicable Procedures')

    state = fields.Selection([
        ('qualification', 'Qualification'),
        ('roadmap_generation', 'Roadmap Generation'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ], string='Project Status', default='qualification', tracking=True)

    step_ids = fields.One2many('lss.foundation.step', 'project_id', string='Regulatory Steps')
    document_ids = fields.Many2many('lss.foundation.document', string='Documents')
    license_ids = fields.One2many('lss.foundation.license', 'project_id', string='Licenses')
    investment_ids = fields.One2many('lss.foundation.investment', 'project_id', string='Investments')

    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    target_completion_date = fields.Date(string='Target Completion Date')
    actual_completion_date = fields.Date(string='Actual Completion Date')

    @api.onchange('sector', 'activity_type')
    def _onchange_sector_activity(self):
        if self.sector and self.activity_type:
            # Détermination des autorités
            if self.sector == 'pharma':
                authorities_codes = ['ANPP', 'MIP', 'MS']
            elif self.sector == 'medical_devices':
                authorities_codes = ['MIP', 'MS', 'ANPP']
            elif self.sector == 'cosmetics':
                authorities_codes = ['MS', 'MIP']
            else:
                authorities_codes = ['MS', 'MIP']
            authorities = self.env['lss.foundation.authority'].search([('code', 'in', authorities_codes)])
            self.applicable_authorities = authorities

            # Procédures applicables
            procedures = self.env['lss.foundation.procedure'].search([
                ('sector', 'in', [self.sector, 'all']),
                ('activity_types', 'in', [self.activity_type, 'all'])
            ])
            self.applicable_procedures = procedures

            # Types de licences requis
            license_types = self.env['lss.foundation.license.type'].search([
                ('sector', 'in', [self.sector, 'all']),
                ('activity_type', 'in', [self.activity_type, 'all'])
            ])
            self.required_licenses = license_types

    def action_generate_roadmap(self):
        self.ensure_one()
        self.step_ids.unlink()
        sequence = 10
        for procedure in self.applicable_procedures:
            step_templates = self.env['lss.foundation.step.template'].search([
                ('procedure_id', '=', procedure.id)
            ], order='sequence')
            for template in step_templates:
                self.env['lss.foundation.step'].create({
                    'project_id': self.id,
                    'template_id': template.id,
                    'sequence': sequence,
                    'name': template.name,
                    'objective': template.objective,
                    'authority_id': template.authority_id.id,
                    'regulatory_reference': template.regulatory_reference.id,
                    'required_documents': [(6, 0, template.required_documents.ids)],
                    'forms': [(6, 0, template.forms.ids)],
                    'fees': template.fees,
                    'currency_id': template.currency_id.id,
                    'deadline': template.deadline,
                    'deliverables': template.deliverables,
                    'state': 'todo',
                })
                sequence += 10
        self.state = 'roadmap_generation'

    def action_start_project(self):
        if self.state == 'roadmap_generation':
            self.state = 'in_progress'
        else:
            raise ValidationError(_('Cannot start project in current state.'))

    def action_complete(self):
        if self.state == 'in_progress':
            unapproved = self.step_ids.filtered(lambda s: s.state not in ['approved', 'renewal'])
            if unapproved:
                raise ValidationError(_('Cannot complete: some steps are not approved.'))
            self.state = 'completed'
            self.actual_completion_date = fields.Date.today()
        else:
            raise ValidationError(_('Cannot complete project in current state.'))

    def action_suspend(self):
        self.state = 'suspended'

    def action_resume(self):
        self.state = 'in_progress'

    def action_cancel(self):
        self.state = 'cancelled'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('lss.foundation.project') or _('New')
        return super(LssFoundationProject, self).create(vals)
