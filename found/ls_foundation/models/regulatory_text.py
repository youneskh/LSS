from odoo import models, fields

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
