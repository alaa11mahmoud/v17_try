{
    'name': 'Tecfy Custom POS',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'Tecfy Customizes POS Component functionality ',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'tecfy_custom_pos/static/src/js/custom_pos_component.js',
            'tecfy_custom_pos/static/src/css/custom_pos_component.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
