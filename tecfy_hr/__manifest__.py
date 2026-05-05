# ———————————————————-
# Authored / Modified by: Abd-ElRahman Menisy
# Odoo Developer | Egypt
# Date: 2026-02-28
# Contributor: AbdElrahman Menisy
# Purpose: HR menu customization for Officer visibility
# ———————————————————-

{
    'name': 'Tecfy HR Customization',
    'version': '17.0.1.0.0',
    'summary': 'Customizes HR menus for Officers - Shows only Challenges menu',
    'category': 'Human Resources',
    'author': 'Tecfy',
    'contributors': ['AbdElrahman Menisy'],
    'license': 'LGPL-3',
    'depends': ['hr', 'hr_gamification', 'gamification'],
    'data': [
        'security/groups.xml',
        'security/challenge_rules.xml',
        'views/user_views.xml',
        'views/hr_menus.xml',
        'views/goal_views.xml',
    ],
    'installable': True,
    'application': False,
}
