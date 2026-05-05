{
    'name': 'POS Auto Invoice',
    'category': 'Point of Sale',
    'summary': 'Automatically check invoice button in POS payment screen',
    'description': """
        This module automatically checks the invoice button when the POS payment screen opens.
        
        Features:
        - Invoice button is automatically checked when payment screen loads
        - Simple and lightweight implementation
        - Works with Odoo 17 POS interface
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_auto_invoice/static/src/js/payment_screen_override.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
