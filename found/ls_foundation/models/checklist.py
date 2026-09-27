from odoo import models, fields

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
