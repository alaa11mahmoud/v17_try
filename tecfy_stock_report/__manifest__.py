{
    'name': 'Tecfy Stock Report',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Generate stock movement reports for products',
    'data': [
        'views/stock_report_view.xml',
        'wizard/stock_report_wizard_view.xml',
        'wizard/stock_report_template.xml',
        'security/your_security_file.xml',
    ],
    'depends': ['stock', 'web'],
    'installable': True,
    'application': True,
}
