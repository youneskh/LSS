from odoo.tests import common, tagged

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
