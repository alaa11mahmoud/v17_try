# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).
{
    'name': 'Tecfy POS Custom Close Session',
    'version': '17.0.1.0',
    "license": "OPL-1",
    'category': 'Sales/Point of Sale',
    'author': 'Tecfy',
    'website': 'https://www.tecfy.co',
    'summary': 'Tecfy POS Custom Close Session',
    'description': "Tecfy POS Custom Close Session.",
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'tecfy_pos_close_session/static/src/**/*',
        ],
    },
    'installable': True,
}