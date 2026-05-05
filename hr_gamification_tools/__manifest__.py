{
    'name': 'HR Gamification Tools',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Add Gamification Tools menu to Employees module',
    'description': """
This module adds a Gamification Tools menu under the Employees app,
restricted to a specific user group: Gamification Challenges and Goals.
    """,
    'depends': ['hr', 'gamification'],
    'data': [
        'security/security.xml',
        'views/hr_gamification_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
