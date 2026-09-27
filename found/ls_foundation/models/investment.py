from odoo import models, fields

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
