{
    'name': 'Tecfy Warehouse Permissions',
    'version': '17.0.0.1',
    'summary': 'Adds user and admin fields to stock warehouse',
    'description': """
        This module adds two new fields (user and admin) to the stock.warehouse model
        and displays them in the warehouse form view.
    """,
    'author': 'Menisy',
    'website': '',
    'category': 'Inventory',
    'depends': ['stock', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir.rule.xml',
        'views/stock_warehouse_views.xml',
        'views/stock_picking_confirm_note_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
