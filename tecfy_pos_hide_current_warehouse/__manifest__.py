{
    'name': 'Tecfy POS Hide Current Warehouse',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Hide current POS warehouse from product info popup',
    'depends': ['point_of_sale'],
    'author': 'Ahmed Elgamil',
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'tecfy_pos_hide_current_warehouse/static/src/xml/product_info_popup.xml',
            'tecfy_pos_hide_current_warehouse/static/src/js/pos_store_patch.js',
            'tecfy_pos_hide_current_warehouse/static/src/css/custom_pos_component.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}