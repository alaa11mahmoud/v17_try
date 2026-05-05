{
    'name': 'stock_card_rep_excel',
    'version': '1.0',
    'category': 'Customizations',
    'depends': ['stock', 'stock_card_report'],
    'author': 'Menisy',
    'summary': 'Generate stock card reports with date range and product filter.',
    'data': [
        'views/stock_card_actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_card_rep_excel/static/src/js/stock_card_export.js',
            'stock_card_rep_excel/static/src/xml/stock_card_export.xml',
        ],
    },
    'installable': True,
    'application': True,
}
