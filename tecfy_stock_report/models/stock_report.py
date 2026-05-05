from odoo import models, fields, api

class StockReport(models.Model):
    _name = 'tecfy.stock.report'
    _description = 'Tecfy Stock Report'

    product_ids = fields.Many2many('product.product', string='Products', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    @api.model
    def get_stock_movements(self):
        domain = []
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        if self.warehouse_id:
            domain.append(('location_id', 'child_of', self.warehouse_id.lot_stock_id.id))
        if self.start_date:
            domain.append(('date', '>=', self.start_date))
        if self.end_date:
            domain.append(('date', '<=', self.end_date))
        
        return self.env['stock.move'].search(domain)