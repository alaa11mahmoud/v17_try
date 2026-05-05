{
    'name': 'POS Default Pricelist Selector',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Add custom default pricelist selector for POS',
    'description': """
        This module adds a new field to select a default pricelist 
        that will be automatically applied when creating new orders in POS.
    """,
    'author': 'Ahmed Elgamil',
    'depends': ['point_of_sale', 'product'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_default_pricelist/static/src/js/models.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}