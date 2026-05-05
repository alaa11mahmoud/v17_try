# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockCardLine(models.TransientModel):
    _name = 'stock.card.line'
    _description = 'Stock Card Line'
    _order = 'product_id, date'
    _transient_max_hours = 2  # delete after 2 hours

    wizard_id = fields.Many2one('stock.card.report.wizard', string='Wizard')
    date = fields.Datetime(string='Date')
    reference = fields.Char(string='Reference')
    created_by_id = fields.Many2one('res.users', string='Created By')
    product_id = fields.Many2one('product.product', string='Product')
    unit_cost = fields.Float(string="Unit Cost")
    value = fields.Float(string="Total Cost")
    location_from_id = fields.Many2one('stock.location', string='From')
    location_to_id = fields.Many2one('stock.location', string='To')
    qty_in = fields.Float(string='In')
    qty_out = fields.Float(string='Out')
    balance = fields.Float(string='Balance')


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        
        res = super(StockCardLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        target_fields = [f for f in ['balance', 'unit_cost'] if f in fields]
        if target_fields:
            for line in res:
                if line.get('__domain'):
                   
                    last_record = self.search(line['__domain'] + [('reference', '!=', 'Initial Balance')], order='date desc, id desc', limit=1)
                    if not last_record:
                        last_record = self.search(line['__domain'], order='date desc, id desc', limit=1)
                    
                    if last_record:
                        for field in target_fields:
                            line[field] = getattr(last_record, field, 0.0)
                    else:
                        for field in target_fields:
                            line[field] = 0.0
        return res