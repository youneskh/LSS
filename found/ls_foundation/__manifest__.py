{
    'name': 'LSS Foundation & Licensing',
    'version': '19.0.1.0.0',
    'category': 'Regulatory Affairs/Life Sciences',
    'summary': 'Business establishment & regulatory workflow management for Life Sciences in Algeria',
    'description': """
        Guides companies through the entire regulatory setup process:
        - Project qualification
        - Regulatory roadmap generation
        - Document management
        - License tracking
        - Regulatory library
        - Investment tracking
        - Authorities database
    """,
    'author': 'Life Sciences Suite Architecture Team',
    'website': 'https://yourcompany.com',
    'depends': [
        'base',
        'mail',
        'product',
        'account',
    ],
    'data': [
        'security/lss_foundation_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/authority_data.xml',
        'data/license_type_data.xml',
        'data/procedure_data.xml',
        'data/regulatory_text_data.xml',
        'data/document_type_data.xml',
        'views/menu_views.xml',
        'views/project_views.xml',
        'views/authority_views.xml',
        'views/procedure_views.xml',
        'views/step_views.xml',
        'views/license_views.xml',
        'views/regulatory_text_views.xml',
        'views/checklist_views.xml',
        'views/document_views.xml',
        'views/investment_views.xml',
        'wizards/views/generate_roadmap_wizard_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
