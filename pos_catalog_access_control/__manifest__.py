{
    'name': 'POS Catalog Access Control',
    'version': '1.0',
    'summary': 'Restrict access to the POS Catalog menu to Admins and a specific user.',
    'author': 'Abdelrahman Menisy',
    'website': '',
    'depends': ['point_of_sale'],
    'data': [
        'security/pos_catalog_group.xml',
        'views/pos_menu_access.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
