from odoo import models, fields

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
