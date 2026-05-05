from odoo import models, api, fields

class PosOrderLinee(models.Model):
    _inherit = "pos.order.line"

    pack_lot_ids = fields.One2many(compute='_compute_pack_lot_ids', store=True, readonly=True)

    @api.depends('order_id.picking_ids.move_line_ids.lot_id', 'product_id')
    def _compute_pack_lot_ids(self):
        for line in self:
            if line.pack_lot_ids:
                continue
                
            lot_names = []
            if line.order_id and line.product_id:
                for picking in line.order_id.picking_ids:
                    move_lines = picking.move_line_ids.filtered(
                        lambda ml: ml.product_id.id == line.product_id.id and ml.lot_id
                    )
                    for ml in move_lines:
                        if ml.lot_id.name and ml.lot_id.name not in lot_names:
                            lot_names.append(ml.lot_id.name)
            
            if lot_names:
                commands = []
                for name in lot_names:
                    commands.append((0, 0, {'lot_name': name}))
                line.pack_lot_ids = commands
