from odoo import models, fields, api, _
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
