from odoo import models, fields, api, _

class LssGenerateRoadmapWizard(models.TransientModel):
    _name = 'lss.generate.roadmap.wizard'
    _description = 'Generate Roadmap Wizard'

    project_id = fields.Many2one('lss.foundation.project', string='Project', required=True)

    def action_generate(self):
        self.ensure_one()
        self.project_id.action_generate_roadmap()
        return {'type': 'ir.actions.act_window_close'}
