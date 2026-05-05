{
    'name': 'Product Import from Excel',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Import products from an Excel file',
    'description': """
        This module allows users to upload an Excel file containing product information
        and import it into Odoo's product catalog.
    """,
    'author': 'Menisy',
    'website': 'https://yourwebsite.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_import_wizard_view.xml',
    ],
    'assets': {},
    'installable': True,
    'application': True,
    'auto_install': False,
}
