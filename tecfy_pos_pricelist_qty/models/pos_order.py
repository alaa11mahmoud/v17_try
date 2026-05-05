from odoo import models, api
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _order_fields(self, ui_order):
        """Add custom validation before order creation"""
        res = super()._order_fields(ui_order)
        
        # Validate and update pricelist quantities
        for line in ui_order.get('lines', []):
            line_data = line[2] if isinstance(line, (list, tuple)) else line
            
            product_id = line_data.get('product_id')
            qty = line_data.get('qty', 0)
            pricelist_item_id = line_data.get('pricelist_item_id')
            
            if product_id and pricelist_item_id and qty > 0:
                # جلب pricelist item للتحقق من الحقول
                pricelist_item = self.env['product.pricelist.item'].browse(pricelist_item_id)
                
                # التحقق من تفعيل الخصم على مستوى pricelist item بدلاً من المنتج
                if pricelist_item.exists() and pricelist_item.enable_pricelist_qty_discount:
                    if pricelist_item.quantity > 0:
                        if qty > pricelist_item.quantity:
                            product = self.env['product.product'].browse(product_id)
                            raise UserError(
                                f'Cannot sell more than available quantity ({pricelist_item.quantity}) '
                                f'for product {product.display_name}'
                            )
                        pricelist_item.decrease_quantity(qty)
        
        return res