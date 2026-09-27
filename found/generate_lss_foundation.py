#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur du module LSS Foundation & Licensing - Version autonome
Ne dépend d'aucun autre module (hors base, mail, product, account).
Exécutez ce script pour créer l'arborescence complète du module.
"""

import os
import shutil

MODULE_NAME = "lss_foundation"
BASE_DIR = os.path.join(os.getcwd(), MODULE_NAME)

# Dictionnaire des fichiers à créer
FILES = {}

# ============================================================
#  __manifest__.py
# ============================================================
FILES["__manifest__.py"] = '''{
    'name': 'LSS Foundation & Licensing',
    'version': '19.0.1.0.0',
    'category': 'Regulatory Affairs/Life Sciences',
    'summary': 'Business establishment & regulatory workflow management for Life Sciences in Algeria',
    'description': """
        Guides companies through the entire regulatory setup process:
        - Project qualification
        - Regulatory roadmap generation
        - Document management
        - License tracking
        - Regulatory library
        - Investment tracking
        - Authorities database
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': [
        'base',
        'mail',
        'product',
        'account',
    ],
    'data': [
        'security/lss_foundation_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/authority_data.xml',
        'data/license_type_data.xml',
        'data/procedure_data.xml',
        'data/regulatory_text_data.xml',
        'data/document_type_data.xml',
        'views/menu_views.xml',
        'views/project_views.xml',
        'views/authority_views.xml',
        'views/procedure_views.xml',
        'views/step_views.xml',
        'views/license_views.xml',
        'views/regulatory_text_views.xml',
        'views/checklist_views.xml',
        'views/document_views.xml',
        'views/investment_views.xml',
        'wizards/views/generate_roadmap_wizard_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
'''

# ============================================================
#  __init__.py (root)
# ============================================================
FILES["__init__.py"] = '''from . import models
from . import wizards
'''

# ============================================================
#  models/__init__.py
# ============================================================
FILES["models/__init__.py"] = '''from . import project
from . import authority
from . import procedure
from . import step
from . import license
from . import regulatory_text
from . import checklist
from . import document
from . import investment
'''

# ============================================================
#  models/project.py
# ============================================================
FILES["models/project.py"] = '''from odoo import models, fields, api, _
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
'''

# ============================================================
#  models/authority.py
# ============================================================
FILES["models/authority.py"] = '''from odoo import models, fields

class LssFoundationAuthority(models.Model):
    _name = 'lss.foundation.authority'
    _description = 'Regulatory Authority'
    _order = 'name'

    name = fields.Char(string='Authority Name', required=True)
    code = fields.Char(string='Code', required=True)
    type = fields.Selection([
        ('national', 'National'), ('local', 'Local'),
        ('sectoral', 'Sectoral'), ('international', 'International'),
    ], string='Type')
    jurisdiction = fields.Char(string='Jurisdiction')
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    website = fields.Char(string='Website')
    contact_person = fields.Char(string='Contact Person')
    regulatory_reference = fields.Char(string='Legal Basis')
    competencies = fields.Text(string='Competencies')
    services = fields.Text(string='Services Provided')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)
'''

# ============================================================
#  models/procedure.py
# ============================================================
FILES["models/procedure.py"] = '''from odoo import models, fields

class LssFoundationProcedure(models.Model):
    _name = 'lss.foundation.procedure'
    _description = 'Regulatory Procedure'
    _order = 'name'

    name = fields.Char(string='Procedure Name', required=True)
    code = fields.Char(string='Code', required=True)
    authority_id = fields.Many2one('lss.foundation.authority', string='Authority', required=True)
    procedure_type = fields.Selection([
        ('registration', 'Registration'), ('licensing', 'Licensing'),
        ('authorization', 'Authorization'), ('declaration', 'Declaration'),
        ('certification', 'Certification'), ('inspection', 'Inspection'),
        ('renewal', 'Renewal'), ('modification', 'Modification'),
        ('suspension', 'Suspension'), ('appeal', 'Appeal'),
    ], string='Procedure Type', required=True)
    regulatory_reference = fields.Many2one('lss.foundation.regulatory_text', string='Regulatory Reference')
    description = fields.Text(string='Description')
    required_documents = fields.Many2many('lss.foundation.document.type', string='Required Documents')
    fees = fields.Monetary(string='Fees (if published)')
    currency_id = fields.Many2one('res.currency', string='Currency')
    processing_time = fields.Integer(string='Processing Time (days, if published)')
    validity_period = fields.Integer(string='Validity Period (months, if applicable)')
    renewal_lead_time = fields.Integer(string='Renewal Lead Time (days)')
    sector = fields.Selection([
        ('pharma', 'Pharmaceutical'), ('medical_devices', 'Medical Devices'),
        ('cosmetics', 'Cosmetics'), ('laboratory', 'Laboratory'),
        ('pharma_packaging', 'Pharmaceutical Packaging'),
        ('medical_plastics', 'Medical Plastics'),
        ('distribution', 'Distribution'), ('import_export', 'Import/Export'),
        ('all', 'All'),
    ], string='Sector', default='all')
    activity_types = fields.Selection([
        ('manufacturing', 'Manufacturing'), ('import', 'Import'),
        ('export', 'Export'), ('distribution', 'Distribution'),
        ('quality_control', 'Quality Control'), ('packaging', 'Packaging'),
        ('storage', 'Storage'), ('laboratory', 'Laboratory'),
        ('all', 'All'),
    ], string='Activity Types', default='all')
    is_mandatory = fields.Boolean(string='Mandatory', default=True)
    active = fields.Boolean(string='Active', default=True)
'''

# ============================================================
#  models/step.py
# ============================================================
FILES["models/step.py"] = '''from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class LssFoundationStepTemplate(models.Model):
    _name = 'lss.foundation.step.template'
    _description = 'Step Template'
    _order = 'sequence'

    name = fields.Char(string='Step Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    procedure_id = fields.Many2one('lss.foundation.procedure', string='Procedure')
    objective = fields.Text(string='Objective')
    authority_id = fields.Many2one('lss.foundation.authority', string='Competent Authority')
    regulatory_reference = fields.Many2one('lss.foundation.regulatory_text', string='Regulatory Reference')
    required_documents = fields.Many2many('lss.foundation.document.type', string='Required Documents')
    forms = fields.Many2many('ir.attachment', string='Forms')
    fees = fields.Monetary(string='Fees (if published)')
    currency_id = fields.Many2one('res.currency', string='Currency')
    deadline = fields.Integer(string='Deadline (days, if published)')
    dependencies = fields.Many2many('lss.foundation.step.template', string='Dependencies')
    deliverables = fields.Text(string='Deliverables')


class LssFoundationStep(models.Model):
    _name = 'lss.foundation.step'
    _description = 'Regulatory Step in Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence'

    project_id = fields.Many2one('lss.foundation.project', string='Project', required=True)
    template_id = fields.Many2one('lss.foundation.step.template', string='Step Template')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Step Name', required=True)
    objective = fields.Text(string='Objective')
    authority_id = fields.Many2one('lss.foundation.authority', string='Competent Authority')
    regulatory_reference = fields.Many2one('lss.foundation.regulatory_text', string='Regulatory Reference')
    required_documents = fields.Many2many('lss.foundation.document.type', string='Required Documents')
    forms = fields.Many2many('ir.attachment', string='Forms')
    fees = fields.Monetary(string='Fees (if published)')
    currency_id = fields.Many2one('res.currency', string='Currency')
    deadline = fields.Integer(string='Deadline (days, if published)')
    dependencies = fields.Many2many('lss.foundation.step', string='Dependencies')
    deliverables = fields.Text(string='Deliverables')

    state = fields.Selection([
        ('todo', 'To Do'), ('preparing', 'Preparing'),
        ('submitted', 'Submitted'), ('under_review', 'Under Review'),
        ('approved', 'Approved'), ('rejected', 'Rejected'),
        ('renewal', 'Renewal'),
    ], string='Status', default='todo', tracking=True)

    start_date = fields.Date(string='Start Date')
    submission_date = fields.Date(string='Submission Date')
    approval_date = fields.Date(string='Approval Date')
    expiry_date = fields.Date(string='Expiry Date')
    renewal_date = fields.Date(string='Renewal Date')

    document_ids = fields.Many2many('lss.foundation.document', string='Documents')
    checklist_ids = fields.One2many('lss.foundation.checklist.item', 'step_id', string='Checklist Items')
    notes = fields.Text(string='Notes')

    @api.constrains('checklist_ids')
    def _check_checklist_completion(self):
        for step in self:
            if step.state in ['submitted', 'under_review']:
                pending = step.checklist_ids.filtered(
                    lambda c: c.required_for_next and c.answer not in ['yes', 'na']
                )
                if pending:
                    raise ValidationError(_('Some required checklist items are not completed.'))

    def action_start_preparing(self):
        self.state = 'preparing'
        self.start_date = fields.Date.today()

    def action_submit(self):
        pending = self.checklist_ids.filtered(
            lambda c: c.required_for_next and c.answer not in ['yes', 'na']
        )
        if pending:
            raise ValidationError(_('Complete all required checklist items before submitting.'))
        self.state = 'submitted'
        self.submission_date = fields.Date.today()

    def action_approve(self):
        self.state = 'approved'
        self.approval_date = fields.Date.today()
        if self.template_id and self.template_id.procedure_id.validity_period:
            months = self.template_id.procedure_id.validity_period
            self.expiry_date = fields.Date.add(self.approval_date, months=months)

    def action_reject(self):
        self.state = 'rejected'

    def action_renew(self):
        self.state = 'renewal'
        self.renewal_date = fields.Date.today()

    def action_cancel(self):
        self.state = 'todo'
'''

# ============================================================
#  models/license.py
# ============================================================
FILES["models/license.py"] = '''from odoo import models, fields, api
from datetime import date

class LssFoundationLicenseType(models.Model):
    _name = 'lss.foundation.license.type'
    _description = 'License Type'

    name = fields.Char(string='License Name', required=True)
    code = fields.Char(string='Code', required=True)
    sector = fields.Selection([
        ('pharma', 'Pharmaceutical'), ('medical_devices', 'Medical Devices'),
        ('cosmetics', 'Cosmetics'), ('laboratory', 'Laboratory'),
        ('pharma_packaging', 'Pharmaceutical Packaging'),
        ('medical_plastics', 'Medical Plastics'),
        ('distribution', 'Distribution'), ('import_export', 'Import/Export'),
        ('all', 'All'),
    ], string='Sector', default='all')
    activity_type = fields.Selection([
        ('manufacturing', 'Manufacturing'), ('import', 'Import'),
        ('export', 'Export'), ('distribution', 'Distribution'),
        ('quality_control', 'Quality Control'), ('packaging', 'Packaging'),
        ('storage', 'Storage'), ('laboratory', 'Laboratory'),
        ('all', 'All'),
    ], string='Activity Type', default='all')
    authority_id = fields.Many2one('lss.foundation.authority', string='Issuing Authority')
    regulatory_reference = fields.Many2one('lss.foundation.regulatory_text', string='Regulatory Reference')
    validity_period = fields.Integer(string='Validity Period (months)')
    renewal_lead_time = fields.Integer(string='Renewal Lead Time (days)')
    active = fields.Boolean(string='Active', default=True)


class LssFoundationLicense(models.Model):
    _name = 'lss.foundation.license'
    _description = 'License/Permit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one('lss.foundation.project', string='Project', required=True)
    license_type_id = fields.Many2one('lss.foundation.license.type', string='License Type', required=True)
    number = fields.Char(string='License Number')
    issuing_authority = fields.Many2one('lss.foundation.authority', string='Issuing Authority')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    renewal_reminder = fields.Date(string='Renewal Reminder Date')
    status = fields.Selection([
        ('applied', 'Applied'), ('pending', 'Pending'),
        ('granted', 'Granted'), ('active', 'Active'),
        ('expired', 'Expired'), ('suspended', 'Suspended'),
        ('revoked', 'Revoked'), ('renewal_pending', 'Renewal Pending'),
    ], string='Status', default='applied')
    regulatory_reference = fields.Many2one('lss.foundation.regulatory_text', string='Regulatory Reference')
    attachment_ids = fields.Many2many('ir.attachment', string='Supporting Documents')
    notes = fields.Text(string='Notes')

    days_until_expiry = fields.Integer(string='Days Until Expiry', compute='_compute_days_until_expiry')
    alert_level = fields.Selection([
        ('green', 'Green'), ('yellow', 'Yellow'), ('red', 'Red'),
    ], string='Alert Level', compute='_compute_alert_level')

    @api.depends('expiry_date')
    def _compute_days_until_expiry(self):
        for rec in self:
            if rec.expiry_date:
                rec.days_until_expiry = (rec.expiry_date - date.today()).days
            else:
                rec.days_until_expiry = 0

    @api.depends('days_until_expiry')
    def _compute_alert_level(self):
        for rec in self:
            if rec.days_until_expiry <= 30 and rec.days_until_expiry > 0:
                rec.alert_level = 'red'
            elif rec.days_until_expiry <= 90:
                rec.alert_level = 'yellow'
            else:
                rec.alert_level = 'green'
'''

# ============================================================
#  models/regulatory_text.py
# ============================================================
FILES["models/regulatory_text.py"] = '''from odoo import models, fields

class LssFoundationRegulatoryText(models.Model):
    _name = 'lss.foundation.regulatory_text'
    _description = 'Regulatory Text'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    title = fields.Char(string='Title', required=True)
    type = fields.Selection([
        ('law', 'Law'), ('decree', 'Decree'), ('order', 'Order'),
        ('decision', 'Decision'), ('instruction', 'Instruction'),
        ('circular', 'Circular'), ('guideline', 'Guideline'),
        ('standard', 'Standard'), ('other', 'Other'),
    ], string='Type', required=True)
    number = fields.Char(string='Number/Reference')
    issue_date = fields.Date(string='Issue Date')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date (if applicable)')
    authority_id = fields.Many2one('lss.foundation.authority', string='Issuing Authority', required=True)
    sector = fields.Selection([
        ('pharma', 'Pharmaceutical'), ('medical_devices', 'Medical Devices'),
        ('cosmetics', 'Cosmetics'), ('laboratory', 'Laboratory'),
        ('pharma_packaging', 'Pharmaceutical Packaging'),
        ('medical_plastics', 'Medical Plastics'),
        ('distribution', 'Distribution'), ('import_export', 'Import/Export'),
        ('all', 'All'),
    ], string='Sector', default='all')
    keywords = fields.Char(string='Keywords')
    summary = fields.Text(string='Summary')
    full_text = fields.Html(string='Full Text')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    status = fields.Selection([
        ('draft', 'Draft'), ('in_force', 'In Force'),
        ('suspended', 'Suspended'), ('repealed', 'Repealed'),
        ('superseded', 'Superseded'),
    ], string='Status', default='in_force')
    notes = fields.Text(string='Notes')
'''

# ============================================================
#  models/checklist.py
# ============================================================
FILES["models/checklist.py"] = '''from odoo import models, fields

class LssFoundationChecklistItem(models.Model):
    _name = 'lss.foundation.checklist.item'
    _description = 'Checklist Item'

    step_id = fields.Many2one('lss.foundation.step', string='Step', required=True)
    question = fields.Text(string='Question', required=True)
    answer = fields.Selection([
        ('yes', 'Yes'), ('no', 'No'), ('na', 'Not Applicable'), ('pending', 'Pending'),
    ], string='Answer', default='pending')
    required_for_next = fields.Boolean(string='Required to Unlock Next Step')
    regulatory_reference = fields.Many2one('lss.foundation.regulatory_text', string='Regulatory Reference')
    notes = fields.Text(string='Notes')
'''

# ============================================================
#  models/document.py
# ============================================================
FILES["models/document.py"] = '''from odoo import models, fields, api
from datetime import date

class LssFoundationDocumentType(models.Model):
    _name = 'lss.foundation.document.type'
    _description = 'Foundation Document Type'
    _order = 'name'

    name = fields.Char(string='Document Name', required=True)
    code = fields.Char(string='Code', required=True)
    category = fields.Selection([
        ('corporate', 'Corporate'), ('regulatory', 'Regulatory'),
        ('financial', 'Financial'), ('technical', 'Technical'),
        ('quality', 'Quality'), ('legal', 'Legal'),
    ], string='Category')
    regulatory_reference = fields.Many2one('lss.foundation.regulatory_text', string='Regulatory Reference')
    description = fields.Text(string='Description')
    required = fields.Boolean(string='Required', default=True)


class LssFoundationDocument(models.Model):
    _name = 'lss.foundation.document'
    _description = 'Foundation Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Document Name', required=True)
    document_type_id = fields.Many2one('lss.foundation.document.type', string='Document Type', required=True)
    project_id = fields.Many2one('lss.foundation.project', string='Project')
    step_id = fields.Many2one('lss.foundation.step', string='Associated Step')
    license_id = fields.Many2one('lss.foundation.license', string='Associated License')
    reference_number = fields.Char(string='Reference Number')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    version = fields.Integer(string='Version', default=1)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments', required=True)
    status = fields.Selection([
        ('draft', 'Draft'), ('pending_validation', 'Pending Validation'),
        ('validated', 'Validated'), ('rejected', 'Rejected'),
        ('expired', 'Expired'), ('renewed', 'Renewed'),
    ], string='Status', default='draft')
    verified = fields.Boolean(string='Verified')
    verified_by = fields.Many2one('res.users', string='Verified By')
    verification_date = fields.Date(string='Verification Date')
    notes = fields.Text(string='Notes')

    @api.depends('expiry_date')
    def _check_expiry(self):
        for rec in self:
            if rec.expiry_date and rec.expiry_date < date.today():
                rec.status = 'expired'

    def action_validate(self):
        self.status = 'validated'
        self.verified = True
        self.verified_by = self.env.user
        self.verification_date = date.today()

    def action_reject(self):
        self.status = 'rejected'
'''

# ============================================================
#  models/investment.py
# ============================================================
FILES["models/investment.py"] = '''from odoo import models, fields

class LssFoundationInvestment(models.Model):
    _name = 'lss.foundation.investment'
    _description = 'Investment Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    project_id = fields.Many2one('lss.foundation.project', string='Project', required=True)
    name = fields.Char(string='Investment Item', required=True)
    category = fields.Selection([
        ('land', 'Land'), ('building', 'Building'), ('clean_room', 'Clean Room'),
        ('laboratory', 'Laboratory'), ('machinery', 'Machinery'),
        ('equipment_qualification', 'Equipment Qualification'),
        ('utilities', 'Utilities'), ('it', 'IT Infrastructure'),
        ('other', 'Other'),
    ], string='Category', required=True)
    amount = fields.Monetary(string='Amount')
    currency_id = fields.Many2one('res.currency', string='Currency')
    planned_start_date = fields.Date(string='Planned Start Date')
    planned_end_date = fields.Date(string='Planned End Date')
    actual_start_date = fields.Date(string='Actual Start Date')
    actual_end_date = fields.Date(string='Actual End Date')
    milestone = fields.Char(string='Milestone')
    status = fields.Selection([
        ('planned', 'Planned'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='planned')
    notes = fields.Text(string='Notes')
'''

# ============================================================
#  wizards/__init__.py
# ============================================================
FILES["wizards/__init__.py"] = '''from . import generate_roadmap_wizard
'''

# ============================================================
#  wizards/generate_roadmap_wizard.py
# ============================================================
FILES["wizards/generate_roadmap_wizard.py"] = '''from odoo import models, fields, api, _

class LssGenerateRoadmapWizard(models.TransientModel):
    _name = 'lss.generate.roadmap.wizard'
    _description = 'Generate Roadmap Wizard'

    project_id = fields.Many2one('lss.foundation.project', string='Project', required=True)

    def action_generate(self):
        self.ensure_one()
        self.project_id.action_generate_roadmap()
        return {'type': 'ir.actions.act_window_close'}
'''

# ============================================================
#  views/menu_views.xml
# ============================================================
FILES["views/menu_views.xml"] = '''<odoo>
    <menuitem id="menu_lss_foundation_root" name="LSS Foundation &amp; Licensing" sequence="5"
              web_icon="lss_foundation,static/description/icon.png"/>
    <menuitem id="menu_lss_foundation_projects" name="Projects" parent="menu_lss_foundation_root"
              action="action_lss_foundation_project"/>
    <menuitem id="menu_lss_foundation_authorities" name="Authorities" parent="menu_lss_foundation_root"
              action="action_lss_foundation_authority"/>
    <menuitem id="menu_lss_foundation_procedures" name="Procedures" parent="menu_lss_foundation_root"
              action="action_lss_foundation_procedure"/>
    <menuitem id="menu_lss_foundation_licenses" name="Licenses" parent="menu_lss_foundation_root"
              action="action_lss_foundation_license"/>
    <menuitem id="menu_lss_foundation_regulatory_texts" name="Regulatory Texts" parent="menu_lss_foundation_root"
              action="action_lss_foundation_regulatory_text"/>
    <menuitem id="menu_lss_foundation_configuration" name="Configuration" parent="menu_lss_foundation_root" sequence="100"
              groups="base.group_system"/>
    <menuitem id="menu_lss_foundation_document_types" name="Document Types" parent="menu_lss_foundation_configuration"
              action="action_lss_foundation_document_type"/>
    <menuitem id="menu_lss_foundation_license_types" name="License Types" parent="menu_lss_foundation_configuration"
              action="action_lss_foundation_license_type"/>
    <menuitem id="menu_lss_foundation_step_templates" name="Step Templates" parent="menu_lss_foundation_configuration"
              action="action_lss_foundation_step_template"/>
</odoo>
'''

# ============================================================
#  views/project_views.xml
# ============================================================
FILES["views/project_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_project_tree" model="ir.ui.view">
        <field name="name">lss.foundation.project.tree</field>
        <field name="model">lss.foundation.project</field>
        <field name="arch" type="xml">
            <tree decoration-success="state=='completed'" decoration-warning="state=='in_progress'" decoration-danger="state=='cancelled'">
                <field name="name"/>
                <field name="company_name"/>
                <field name="sector"/>
                <field name="activity_type"/>
                <field name="state" widget="badge"/>
                <field name="start_date"/>
                <field name="target_completion_date"/>
            </tree>
        </field>
    </record>

    <record id="view_lss_foundation_project_form" model="ir.ui.view">
        <field name="name">lss.foundation.project.form</field>
        <field name="model">lss.foundation.project</field>
        <field name="arch" type="xml">
            <form string="Business Establishment Project">
                <header>
                    <button name="action_generate_roadmap" string="Generate Roadmap"
                            type="object" class="btn-primary" states="qualification"/>
                    <button name="action_start_project" string="Start Project"
                            type="object" class="btn-success" states="roadmap_generation"/>
                    <button name="action_complete" string="Complete Project"
                            type="object" class="btn-success" states="in_progress"/>
                    <button name="action_suspend" string="Suspend"
                            type="object" class="btn-warning" states="in_progress"/>
                    <button name="action_resume" string="Resume"
                            type="object" class="btn-primary" states="suspended"/>
                    <button name="action_cancel" string="Cancel"
                            type="object" class="btn-danger" states="qualification,roadmap_generation,in_progress"/>
                    <field name="state" widget="statusbar" statusbar_visible="qualification,roadmap_generation,in_progress,completed"/>
                </header>
                <sheet>
                    <div class="oe_title"><h1><field name="name"/></h1></div>
                    <group>
                        <group>
                            <field name="company_name"/>
                            <field name="company_type"/>
                            <field name="sector" widget="selection"/>
                            <field name="activity_type" widget="selection"/>
                            <field name="products"/>
                        </group>
                        <group>
                            <field name="start_date"/>
                            <field name="target_completion_date"/>
                            <field name="actual_completion_date"/>
                            <field name="applicable_authorities" widget="many2many_tags"/>
                            <field name="required_licenses" widget="many2many_tags"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Roadmap">
                            <field name="step_ids">
                                <tree decoration-success="state=='approved'" decoration-warning="state in ['preparing','submitted','under_review']" decoration-danger="state in ['rejected','renewal']">
                                    <field name="sequence"/>
                                    <field name="name"/>
                                    <field name="authority_id"/>
                                    <field name="state" widget="badge"/>
                                    <field name="start_date"/>
                                    <field name="submission_date"/>
                                    <field name="approval_date"/>
                                </tree>
                            </field>
                        </page>
                        <page string="Licenses">
                            <field name="license_ids"/>
                        </page>
                        <page string="Documents">
                            <field name="document_ids" context="{'default_project_id': id}"/>
                        </page>
                        <page string="Investments">
                            <field name="investment_ids"/>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>

    <record id="action_lss_foundation_project" model="ir.actions.act_window">
        <field name="name">Projects</field>
        <field name="res_model">lss.foundation.project</field>
        <field name="view_mode">tree,form</field>
        <field name="help" type="html"><p>Manage business establishment projects with full regulatory guidance.</p></field>
    </record>
</odoo>
'''

# ============================================================
#  views/authority_views.xml
# ============================================================
FILES["views/authority_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_authority_tree" model="ir.ui.view">
        <field name="name">lss.foundation.authority.tree</field>
        <field name="model">lss.foundation.authority</field>
        <field name="arch" type="xml">
            <tree><field name="name"/><field name="code"/><field name="type"/><field name="website"/></tree>
        </field>
    </record>
    <record id="view_lss_foundation_authority_form" model="ir.ui.view">
        <field name="name">lss.foundation.authority.form</field>
        <field name="model">lss.foundation.authority</field>
        <field name="arch" type="xml">
            <form string="Regulatory Authority">
                <sheet>
                    <group><group><field name="name"/><field name="code"/><field name="type"/></group>
                    <group><field name="jurisdiction"/><field name="website"/><field name="email"/><field name="phone"/></group></group>
                    <field name="competencies"/><field name="services"/><field name="notes"/>
                </sheet>
            </form>
        </field>
    </record>
    <record id="action_lss_foundation_authority" model="ir.actions.act_window">
        <field name="name">Authorities</field>
        <field name="res_model">lss.foundation.authority</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
'''

# ============================================================
#  views/procedure_views.xml
# ============================================================
FILES["views/procedure_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_procedure_tree" model="ir.ui.view">
        <field name="name">lss.foundation.procedure.tree</field>
        <field name="model">lss.foundation.procedure</field>
        <field name="arch" type="xml">
            <tree><field name="name"/><field name="code"/><field name="authority_id"/><field name="procedure_type"/><field name="sector"/></tree>
        </field>
    </record>
    <record id="action_lss_foundation_procedure" model="ir.actions.act_window">
        <field name="name">Procedures</field>
        <field name="res_model">lss.foundation.procedure</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
'''

# ============================================================
#  views/step_views.xml
# ============================================================
FILES["views/step_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_step_tree" model="ir.ui.view">
        <field name="name">lss.foundation.step.tree</field>
        <field name="model">lss.foundation.step</field>
        <field name="arch" type="xml">
            <tree><field name="name"/><field name="project_id"/><field name="authority_id"/><field name="state" widget="badge"/><field name="start_date"/><field name="approval_date"/></tree>
        </field>
    </record>
    <record id="action_lss_foundation_step" model="ir.actions.act_window">
        <field name="name">Steps</field>
        <field name="res_model">lss.foundation.step</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
'''

# ============================================================
#  views/license_views.xml
# ============================================================
FILES["views/license_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_license_tree" model="ir.ui.view">
        <field name="name">lss.foundation.license.tree</field>
        <field name="model">lss.foundation.license</field>
        <field name="arch" type="xml">
            <tree decoration-danger="alert_level=='red'" decoration-warning="alert_level=='yellow'">
                <field name="number"/><field name="license_type_id"/><field name="issuing_authority"/><field name="issue_date"/><field name="expiry_date"/><field name="status" widget="badge"/><field name="alert_level" widget="badge"/>
            </tree>
        </field>
    </record>
    <record id="action_lss_foundation_license" model="ir.actions.act_window">
        <field name="name">Licenses</field>
        <field name="res_model">lss.foundation.license</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
'''

# ============================================================
#  views/regulatory_text_views.xml
# ============================================================
FILES["views/regulatory_text_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_regulatory_text_tree" model="ir.ui.view">
        <field name="name">lss.foundation.regulatory_text.tree</field>
        <field name="model">lss.foundation.regulatory_text</field>
        <field name="arch" type="xml">
            <tree><field name="title"/><field name="type"/><field name="number"/><field name="authority_id"/><field name="issue_date"/><field name="status" widget="badge"/></tree>
        </field>
    </record>
    <record id="action_lss_foundation_regulatory_text" model="ir.actions.act_window">
        <field name="name">Regulatory Texts</field>
        <field name="res_model">lss.foundation.regulatory_text</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
'''

# ============================================================
#  views/checklist_views.xml
# ============================================================
FILES["views/checklist_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_checklist_item_tree" model="ir.ui.view">
        <field name="name">lss.foundation.checklist.item.tree</field>
        <field name="model">lss.foundation.checklist.item</field>
        <field name="arch" type="xml">
            <tree><field name="question"/><field name="answer" widget="selection"/><field name="required_for_next"/></tree>
        </field>
    </record>
</odoo>
'''

# ============================================================
#  views/document_views.xml
# ============================================================
FILES["views/document_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_document_tree" model="ir.ui.view">
        <field name="name">lss.foundation.document.tree</field>
        <field name="model">lss.foundation.document</field>
        <field name="arch" type="xml">
            <tree><field name="name"/><field name="document_type_id"/><field name="reference_number"/><field name="issue_date"/><field name="status" widget="badge"/></tree>
        </field>
    </record>
    <record id="action_lss_foundation_document" model="ir.actions.act_window">
        <field name="name">Foundation Documents</field>
        <field name="res_model">lss.foundation.document</field>
        <field name="view_mode">tree,form</field>
    </record>
    <record id="action_lss_foundation_document_type" model="ir.actions.act_window">
        <field name="name">Document Types</field>
        <field name="res_model">lss.foundation.document.type</field>
        <field name="view_mode">tree,form</field>
    </record>
</odoo>
'''

# ============================================================
#  views/investment_views.xml
# ============================================================
FILES["views/investment_views.xml"] = '''<odoo>
    <record id="view_lss_foundation_investment_tree" model="ir.ui.view">
        <field name="name">lss.foundation.investment.tree</field>
        <field name="model">lss.foundation.investment</field>
        <field name="arch" type="xml">
            <tree><field name="name"/><field name="category"/><field name="amount"/><field name="status" widget="badge"/><field name="planned_start_date"/><field name="planned_end_date"/></tree>
        </field>
    </record>
</odoo>
'''

# ============================================================
#  wizards/views/generate_roadmap_wizard_views.xml
# ============================================================
FILES["wizards/views/generate_roadmap_wizard_views.xml"] = '''<odoo>
    <record id="view_lss_generate_roadmap_wizard" model="ir.ui.view">
        <field name="name">lss.generate.roadmap.wizard</field>
        <field name="model">lss.generate.roadmap.wizard</field>
        <field name="arch" type="xml">
            <form string="Generate Roadmap">
                <group><field name="project_id"/></group>
                <footer>
                    <button name="action_generate" string="Generate" type="object" class="btn-primary"/>
                    <button string="Cancel" class="btn-secondary" special="cancel"/>
                </footer>
            </form>
        </field>
    </record>
</odoo>
'''

# ============================================================
#  security/lss_foundation_security.xml
# ============================================================
FILES["security/lss_foundation_security.xml"] = '''<odoo>
    <record id="module_category_lss_foundation" model="ir.module.category">
        <field name="name">LSS Foundation &amp; Licensing</field>
        <field name="description">Business establishment and regulatory workflow</field>
        <field name="sequence">5</field>
    </record>
    <record id="group_lss_foundation_user" model="res.groups">
        <field name="name">User</field>
        <field name="category_id" ref="module_category_lss_foundation"/>
    </record>
    <record id="group_lss_foundation_manager" model="res.groups">
        <field name="name">Manager</field>
        <field name="category_id" ref="module_category_lss_foundation"/>
        <field name="implied_ids" eval="[(4, ref('group_lss_foundation_user'))]"/>
    </record>
    <record id="group_lss_foundation_regulatory" model="res.groups">
        <field name="name">Regulatory Affairs</field>
        <field name="category_id" ref="module_category_lss_foundation"/>
        <field name="implied_ids" eval="[(4, ref('group_lss_foundation_user'))]"/>
    </record>
</odoo>
'''

# ============================================================
#  security/ir.model.access.csv
# ============================================================
FILES["security/ir.model.access.csv"] = '''id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_lss_foundation_project_user,lss.foundation.project.user,model_lss_foundation_project,group_lss_foundation_user,1,0,0,0
access_lss_foundation_project_manager,lss.foundation.project.manager,model_lss_foundation_project,group_lss_foundation_manager,1,1,1,1
access_lss_foundation_authority_user,lss.foundation.authority.user,model_lss_foundation_authority,group_lss_foundation_user,1,0,0,0
access_lss_foundation_authority_regulatory,lss.foundation.authority.regulatory,model_lss_foundation_authority,group_lss_foundation_regulatory,1,1,1,1
access_lss_foundation_procedure_user,lss.foundation.procedure.user,model_lss_foundation_procedure,group_lss_foundation_user,1,0,0,0
access_lss_foundation_procedure_regulatory,lss.foundation.procedure.regulatory,model_lss_foundation_procedure,group_lss_foundation_regulatory,1,1,1,1
access_lss_foundation_step_user,lss.foundation.step.user,model_lss_foundation_step,group_lss_foundation_user,1,0,0,0
access_lss_foundation_step_manager,lss.foundation.step.manager,model_lss_foundation_step,group_lss_foundation_manager,1,1,1,1
access_lss_foundation_license_user,lss.foundation.license.user,model_lss_foundation_license,group_lss_foundation_user,1,0,0,0
access_lss_foundation_license_manager,lss.foundation.license.manager,model_lss_foundation_license,group_lss_foundation_manager,1,1,1,1
access_lss_foundation_regulatory_text_user,lss.foundation.regulatory_text.user,model_lss_foundation_regulatory_text,group_lss_foundation_user,1,0,0,0
access_lss_foundation_regulatory_text_regulatory,lss.foundation.regulatory_text.regulatory,model_lss_foundation_regulatory_text,group_lss_foundation_regulatory,1,1,1,1
access_lss_foundation_checklist_item_user,lss.foundation.checklist.item.user,model_lss_foundation_checklist_item,group_lss_foundation_user,1,1,1,0
access_lss_foundation_document_user,lss.foundation.document.user,model_lss_foundation_document,group_lss_foundation_user,1,1,1,0
access_lss_foundation_document_manager,lss.foundation.document.manager,model_lss_foundation_document,group_lss_foundation_manager,1,1,1,1
access_lss_foundation_investment_user,lss.foundation.investment.user,model_lss_foundation_investment,group_lss_foundation_user,1,0,0,0
access_lss_foundation_investment_manager,lss.foundation.investment.manager,model_lss_foundation_investment,group_lss_foundation_manager,1,1,1,1
access_lss_foundation_license_type_manager,lss.foundation.license.type.manager,model_lss_foundation_license_type,group_lss_foundation_manager,1,1,1,1
access_lss_foundation_step_template_manager,lss.foundation.step.template.manager,model_lss_foundation_step_template,group_lss_foundation_manager,1,1,1,1
access_lss_foundation_document_type_manager,lss.foundation.document.type.manager,model_lss_foundation_document_type,group_lss_foundation_manager,1,1,1,1
access_lss_generate_roadmap_wizard_manager,lss.generate.roadmap.wizard.manager,model_lss_generate_roadmap_wizard,group_lss_foundation_manager,1,1,1,1
'''

# ============================================================
#  data/sequence_data.xml
# ============================================================
FILES["data/sequence_data.xml"] = '''<odoo>
    <record id="seq_lss_foundation_project" model="ir.sequence">
        <field name="name">Foundation Project</field>
        <field name="code">lss.foundation.project</field>
        <field name="prefix">FP/%(year)s/</field>
        <field name="padding">5</field>
        <field name="company_id" eval="False"/>
    </record>
</odoo>
'''

# ============================================================
#  data/authority_data.xml
# ============================================================
FILES["data/authority_data.xml"] = '''<odoo>
    <record id="authority_anpp" model="lss.foundation.authority">
        <field name="name">ANPP - Agence Nationale des Produits Pharmaceutiques</field>
        <field name="code">ANPP</field>
        <field name="type">national</field>
        <field name="jurisdiction">Pharmaceutical products regulation</field>
        <field name="website">https://www.anpp.dz</field>
    </record>
    <record id="authority_mip" model="lss.foundation.authority">
        <field name="name">Ministère de l'Industrie Pharmaceutique</field>
        <field name="code">MIP</field>
        <field name="type">national</field>
        <field name="jurisdiction">Pharmaceutical industry policy</field>
    </record>
    <record id="authority_customs" model="lss.foundation.authority">
        <field name="name">Douanes Algériennes</field>
        <field name="code">CUSTOMS</field>
        <field name="type">national</field>
        <field name="jurisdiction">Customs clearance and tariffs</field>
    </record>
    <record id="authority_bank_algeria" model="lss.foundation.authority">
        <field name="name">Banque d'Algérie</field>
        <field name="code">BA</field>
        <field name="type">national</field>
        <field name="jurisdiction">Banking and foreign exchange</field>
    </record>
    <record id="authority_ms" model="lss.foundation.authority">
        <field name="name">Ministère de la Santé</field>
        <field name="code">MS</field>
        <field name="type">national</field>
        <field name="jurisdiction">Public health policy</field>
    </record>
</odoo>
'''

# ============================================================
#  data/license_type_data.xml
# ============================================================
FILES["data/license_type_data.xml"] = '''<odoo>
    <record id="license_type_anpp_marketing" model="lss.foundation.license.type">
        <field name="name">Autorisation de Mise sur le Marché (AMM)</field>
        <field name="code">AMM</field>
        <field name="sector">pharma</field>
        <field name="activity_type">manufacturing</field>
        <field name="authority_id" ref="authority_anpp"/>
        <field name="validity_period">60</field>
        <field name="renewal_lead_time">90</field>
    </record>
    <record id="license_type_import_pharma" model="lss.foundation.license.type">
        <field name="name">Licence d'Importation de Produits Pharmaceutiques</field>
        <field name="code">LIP</field>
        <field name="sector">pharma</field>
        <field name="activity_type">import</field>
        <field name="authority_id" ref="authority_mip"/>
        <field name="validity_period">12</field>
        <field name="renewal_lead_time">30</field>
    </record>
    <record id="license_type_export_pharma" model="lss.foundation.license.type">
        <field name="name">Licence d'Exportation de Produits Pharmaceutiques</field>
        <field name="code">LEP</field>
        <field name="sector">pharma</field>
        <field name="activity_type">export</field>
        <field name="authority_id" ref="authority_mip"/>
        <field name="validity_period">12</field>
        <field name="renewal_lead_time">30</field>
    </record>
</odoo>
'''

# ============================================================
#  data/procedure_data.xml
# ============================================================
FILES["data/procedure_data.xml"] = '''<odoo>
    <record id="procedure_register_commerce" model="lss.foundation.procedure">
        <field name="name">Immatriculation au Registre du Commerce</field>
        <field name="code">RC</field>
        <field name="authority_id" ref="authority_customs"/>
        <field name="procedure_type">registration</field>
        <field name="sector">all</field>
        <field name="activity_types">all</field>
        <field name="is_mandatory">1</field>
    </record>
    <record id="procedure_anpp_amm" model="lss.foundation.procedure">
        <field name="name">Demande d'AMM auprès de l'ANPP</field>
        <field name="code">AMM_ANPP</field>
        <field name="authority_id" ref="authority_anpp"/>
        <field name="procedure_type">authorization</field>
        <field name="sector">pharma</field>
        <field name="activity_types">manufacturing</field>
        <field name="is_mandatory">1</field>
        <field name="validity_period">60</field>
        <field name="renewal_lead_time">90</field>
    </record>
</odoo>
'''

# ============================================================
#  data/regulatory_text_data.xml
# ============================================================
FILES["data/regulatory_text_data.xml"] = '''<odoo>
    <record id="reg_text_law_18_11" model="lss.foundation.regulatory_text">
        <field name="title">Loi n° 18-11 relative à la santé</field>
        <field name="type">law</field>
        <field name="number">18-11</field>
        <field name="issue_date">2018-06-10</field>
        <field name="effective_date">2018-06-10</field>
        <field name="authority_id" ref="authority_anpp"/>
        <field name="sector">pharma</field>
        <field name="keywords">santé, médicaments, ANPP</field>
        <field name="status">in_force</field>
    </record>
</odoo>
'''

# ============================================================
#  data/document_type_data.xml
# ============================================================
FILES["data/document_type_data.xml"] = '''<odoo>
    <record id="doc_type_rc" model="lss.foundation.document.type">
        <field name="name">Registre du Commerce</field>
        <field name="code">RC</field>
        <field name="category">legal</field>
        <field name="required">1</field>
    </record>
    <record id="doc_type_nif" model="lss.foundation.document.type">
        <field name="name">NIF</field>
        <field name="code">NIF</field>
        <field name="category">legal</field>
        <field name="required">1</field>
    </record>
    <record id="doc_type_amm" model="lss.foundation.document.type">
        <field name="name">Autorisation de Mise sur le Marché</field>
        <field name="code">AMM</field>
        <field name="category">regulatory</field>
        <field name="regulatory_reference" ref="reg_text_law_18_11"/>
        <field name="required">1</field>
    </record>
</odoo>
'''

# ============================================================
#  demo/demo_data.xml
# ============================================================
FILES["demo/demo_data.xml"] = '''<odoo>
    <record id="demo_project_pharma" model="lss.foundation.project">
        <field name="name">Demo Pharma SARL</field>
        <field name="company_name">Demo Pharma SARL</field>
        <field name="sector">pharma</field>
        <field name="activity_type">manufacturing</field>
        <field name="products">Comprimés, gélules</field>
    </record>
</odoo>
'''

# ============================================================
#  i18n/lss_foundation.pot
# ============================================================
FILES["i18n/lss_foundation.pot"] = '''#
# LSS Foundation & Licensing
#
msgid ""
msgstr ""
"Project-Id-Version: LSS Foundation 19.0\\n"
"Language-Team: \\n"
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Business Establishment Project"
msgstr ""

msgid "Regulatory Authority"
msgstr ""

msgid "Regulatory Procedure"
msgstr ""

msgid "Regulatory Step"
msgstr ""

msgid "License"
msgstr ""

msgid "Regulatory Text"
msgstr ""

msgid "Checklist Item"
msgstr ""

msgid "Foundation Document"
msgstr ""

msgid "Investment Item"
msgstr ""

msgid "Pharmaceutical"
msgstr ""

msgid "Medical Devices"
msgstr ""

msgid "Cosmetics"
msgstr ""

msgid "Manufacturing"
msgstr ""

msgid "Import"
msgstr ""

msgid "Export"
msgstr ""

msgid "Generate Roadmap"
msgstr ""

msgid "Start Project"
msgstr ""
'''

# ============================================================
#  i18n/fr.po
# ============================================================
FILES["i18n/fr.po"] = '''#
# LSS Foundation & Licensing - French translation
#
msgid ""
msgstr ""
"Project-Id-Version: LSS Foundation 19.0\\n"
"Language: fr\\n"

msgid "Business Establishment Project"
msgstr "Projet d'Établissement d'Entreprise"

msgid "Regulatory Authority"
msgstr "Autorité Réglementaire"

msgid "Regulatory Procedure"
msgstr "Procédure Réglementaire"

msgid "Regulatory Step"
msgstr "Étape Réglementaire"

msgid "License"
msgstr "Licence"

msgid "Regulatory Text"
msgstr "Texte Réglementaire"

msgid "Checklist Item"
msgstr "Élément de Checklist"

msgid "Foundation Document"
msgstr "Document Fondation"

msgid "Investment Item"
msgstr "Élément d'Investissement"

msgid "Pharmaceutical"
msgstr "Pharmaceutique"

msgid "Medical Devices"
msgstr "Dispositifs Médicaux"

msgid "Cosmetics"
msgstr "Cosmétiques"

msgid "Manufacturing"
msgstr "Fabrication"

msgid "Import"
msgstr "Importation"

msgid "Export"
msgstr "Exportation"

msgid "Generate Roadmap"
msgstr "Générer la Feuille de Route"

msgid "Start Project"
msgstr "Démarrer le Projet"
'''

# ============================================================
#  i18n/ar.po
# ============================================================
FILES["i18n/ar.po"] = '''#
# LSS Foundation & Licensing - Arabic translation
#
msgid ""
msgstr ""
"Project-Id-Version: LSS Foundation 19.0\\n"
"Language: ar\\n"

msgid "Business Establishment Project"
msgstr "مشروع تأسيس الشركة"

msgid "Regulatory Authority"
msgstr "السلطة التنظيمية"

msgid "License"
msgstr "رخصة"

msgid "Regulatory Text"
msgstr "النص التنظيمي"

msgid "Generate Roadmap"
msgstr "توليد خريطة الطريق"
'''

# ============================================================
#  tests/__init__.py
# ============================================================
FILES["tests/__init__.py"] = '''from . import test_foundation
'''

# ============================================================
#  tests/test_foundation.py
# ============================================================
FILES["tests/test_foundation.py"] = '''from odoo.tests import common, tagged

@tagged('post_install', '-at_install')
class TestFoundation(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.Project = self.env['lss.foundation.project']
        self.Authority = self.env['lss.foundation.authority']
        self.Procedure = self.env['lss.foundation.procedure']

    def test_create_project(self):
        project = self.Project.create({
            'name': 'Test Project',
            'company_name': 'Test Pharma SARL',
            'sector': 'pharma',
            'activity_type': 'manufacturing',
        })
        self.assertEqual(project.state, 'qualification')
        self.assertTrue(project.applicable_authorities)

    def test_generate_roadmap(self):
        project = self.Project.create({
            'name': 'Test Project',
            'sector': 'pharma',
            'activity_type': 'manufacturing',
        })
        proc = self.Procedure.create({
            'name': 'Test Proc',
            'code': 'TP',
            'authority_id': self.env.ref('lss_foundation.authority_anpp').id,
            'procedure_type': 'authorization',
            'sector': 'pharma',
            'activity_types': 'manufacturing',
        })
        project._onchange_sector_activity()
        project.applicable_procedures = proc
        project.action_generate_roadmap()
        self.assertEqual(project.state, 'roadmap_generation')
        self.assertTrue(project.step_ids)

    def test_step_workflow(self):
        project = self.Project.create({
            'name': 'Test Project',
            'sector': 'pharma',
            'activity_type': 'manufacturing',
        })
        step = self.env['lss.foundation.step'].create({
            'project_id': project.id,
            'name': 'Test Step',
            'state': 'todo',
        })
        step.action_start_preparing()
        self.assertEqual(step.state, 'preparing')
        checklist = self.env['lss.foundation.checklist.item'].create({
            'step_id': step.id,
            'question': 'Document ready?',
            'required_for_next': True,
        })
        with self.assertRaises(Exception):
            step.action_submit()
        checklist.answer = 'yes'
        step.action_submit()
        self.assertEqual(step.state, 'submitted')
'''

# ============================================================
#  static/description/icon.png (fichier vide)
# ============================================================
FILES["static/description/icon.png"] = ''  # fichier vide

# ============================================================
#  Fonction d'écriture
# ============================================================
def write_file(path, content):
    full_path = os.path.join(BASE_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {path}")

# ============================================================
#  Main
# ============================================================
def main():
    print(f"📦 Génération du module {MODULE_NAME} ...")
    if os.path.exists(BASE_DIR):
        print("⚠️ Le dossier existe déjà. Suppression...")
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR)
    for filepath, content in FILES.items():
        write_file(filepath, content)
    print("\n" + "="*60)
    print(f"✅ Module {MODULE_NAME} généré avec succès !")
    print(f"📁 Emplacement : {BASE_DIR}")
    print("="*60)
    print("\n🔧 Prochaines étapes :")
    print("1. Placez le dossier dans votre répertoire addons d'Odoo.")
    print("2. Mettez à jour la liste des modules (Apps > Update Apps List).")
    print("3. Installez le module 'LSS Foundation & Licensing'.")
    print("4. Attribuez les droits aux utilisateurs.")
    print("\n⚠️ Remplacez static/description/icon.png par votre propre icône.")
    print("✅ Le module est totalement indépendant : pas de lien avec l'import/export.")

if __name__ == "__main__":
    main()