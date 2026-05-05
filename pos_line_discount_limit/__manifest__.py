# -*- coding: utf-8 -*-
{
    'name': 'POS Line Discount Limit',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Set maximum line discount limit for POS and prevent discounts on pricelist items',
    'description': """
        POS Line Discount Limit
        =======================
        
        This module adds the following features to Odoo 17 Point of Sale:
        
        * Add a maximum line discount field (0-100%) in POS configuration
        * Validate line discounts against the configured maximum limit
        * Prevent applying line discounts to products already discounted via pricelists
        * Display Arabic error messages for validation failures
    """,
    'author': 'Ahmed Elgamil',
    'website': 'https://www.tecfy.co',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_line_discount_limit/static/src/overrides/models.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
