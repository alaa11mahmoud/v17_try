{
    'name': 'Tecfy POS Pricelist Quantity',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'POS Pricelist with quantity control',
    'depends': ['point_of_sale', 'product'],
    'author': 'Ahmed Elgamil',
    'data': [
        'views/product_pricelist_views.xml',
        # 'views/product_template_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'tecfy_pos_pricelist_qty/static/src/js/models.js',
            'tecfy_pos_pricelist_qty/static/src/js/payment_screen.js',
            'tecfy_pos_pricelist_qty/static/src/js/debug.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}