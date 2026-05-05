from odoo import models, api


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    @api.model
    def check_product_stock(self, **kwargs):
        product_id = kwargs.get('product_id')
        session_id = kwargs.get('session_id')
        quantity = kwargs.get('quantity')

        session = self.env['pos.session'].browse(session_id)
        location = session.config_id.picking_type_id.default_location_src_id

        stock = self.env['stock.quant'].search([
            ('product_id', '=', product_id),
            ('location_id', '=', location.id)
        ], limit=1)

        available_qty = stock.quantity if stock else 0

        if quantity > available_qty:
            return {
                'allowed': False,
                'message': f"Available quantity is {available_qty}. Cannot set quantity to {quantity}.",
                'available_qty': available_qty,
            }

        return {
            'allowed': True,
            'available_qty': available_qty,
            'message': f"Available quantity is {available_qty}. You can set quantity to {quantity}."
        }
