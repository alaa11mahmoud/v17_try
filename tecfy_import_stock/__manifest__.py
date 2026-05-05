# -*- coding: utf-8 -*-
{
    'name': 'Tecfy Import Stock',
    'version': '17.0.0.0',
    'category': 'stock',
    'summary': '',
    'description': '''
	''',
    'author': 'TECFY',
    'website': 'https://tecfy.co',
    'depends': ['base', 'stock','purchase'],
    'license': 'OPL-1',
    'data': [
            'security/ir.model.access.csv',
            'wizard/view_tecfy_import_stock.xml',
    ],
    'auto_install': True,
    'installable': True,
    'application': True,
    'qweb': [ ],
    "images": []
}
