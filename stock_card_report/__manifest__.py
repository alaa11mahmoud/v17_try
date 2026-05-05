{
    'name': 'Stock Card Report',
    'version': '1.0',
    'category': 'Customizations',
    'depends': ['stock'],
    'author': 'Menisy',
    'summary': 'Generate stock card reports with date range and product filter.',
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_card_report_wizard_view.xml',
        'views/stock_card_report_menu.xml',
        'views/stock_card_line_view.xml',
    ],
    'installable': True,
    'application': True,
}
