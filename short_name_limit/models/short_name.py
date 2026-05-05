from odoo import models, fields, api

class short_name_limit(models.Model):
    _inherit = 'stock.warehouse'
    
    code=fields.Char(size=10)

