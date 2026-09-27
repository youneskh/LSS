from odoo import models, fields

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
