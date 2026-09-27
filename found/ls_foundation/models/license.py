from odoo import models, fields, api
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
