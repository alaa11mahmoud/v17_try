{
    'name': 'Tecfy Product',
    'version': '17.0.1.0.0',
    'summary': 'Product customizations: chatter search filters and restricted name field editing',
    'description': """
        Tecfy Product Module
        ====================
        * Adds search filters for products with failed/success logs in chatter
        * Enables searching within chatter messages from product list view
        * Restricts product name field editing to specific user (ID: 41)
        * Inherits and customizes product form views
    """,
    'category': 'Product',
    'author': 'Abdelrahman Menisy',
    'license': 'LGPL-3',
    'depends': ['product', 'mail'],
    'data': [
        'views/product_template_search_view.xml',
        'views/product_template_form_view.xml',
    ],
    'installable': True,
    'application': False,
}
