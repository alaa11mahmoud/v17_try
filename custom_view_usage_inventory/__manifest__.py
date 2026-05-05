{
	'name': "custom_view_usage_inventory",
	'version': '17.0.1.0.0',
	'category': 'Inventory',
	'summary': "This module is used to custom usage in inventory",
	'author': "tecfy",
	'depends': ['base',
        'stock'],
	'data': [
        "views/stock_picking_views.xml"
	],
	'license': 'AGPL-3',
	'installable': True,
	'auto_install': False,
	'application': False,
}
