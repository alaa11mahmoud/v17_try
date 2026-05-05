from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    quantity = fields.Float(
        string='Quantity',
        default=0.0,
        help='Available quantity for this price rule'
    )
    
    enable_pricelist_qty_discount = fields.Boolean(
        string='Enable Pricelist Quantity Discount',
        default=False,
        help='Enable discount based on pricelist quantity'
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError('Quantity cannot be negative')

    def decrease_quantity(self, qty):
        """Decrease the available quantity"""
        self.ensure_one()
        if self.quantity >= qty:
            self.quantity -= qty
            return True
        return False