{
    'name': 'Wooden Marketplace',
    'version': '1.0.0',
    'category': 'E-commerce',
    'summary': 'A custom multi-vendor marketplace for wooden crafts and artisanal wood goods.',
    'depends': ['website_sale', 'sale', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'security/marketplace_security.xml',
        'views/templates/assets_backend.xml',
        'views/templates/templates.xml',
        'views/models_views.xml',
        'views/templates/product_form_template.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
