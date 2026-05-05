# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'Tecfy POS Payment',
    'version': '17.0.1.0',
    "license": "OPL-1",
    'category': 'Sales/Point of Sale',
    'author': 'Tecfy',
    'website': 'https://www.tecfy.co',
    'summary': 'Payment.',
    'description': "Payment.",
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'tecfy_pos_payment/static/src/**/*',
        ],
    },
    'installable': True,
}
