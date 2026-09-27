from odoo import models, fields, api
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
