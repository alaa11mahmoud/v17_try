from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    warehouse_id_custom = fields.Many2many(
        'stock.warehouse',
        string='Warehouses (Custom)',
        compute='_compute_warehouse_custom',
        store=False
    )

    allowed_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_allowed_users',
        string='Allowed Users',
        store=True,
    )

    @api.depends('location_id', 'location_dest_id')
    def _compute_warehouse_custom(self):
        for picking in self:
            domain = ['|',
                      ('lot_stock_id', '=', picking.location_id.id),
                      ('lot_stock_id', '=', picking.location_dest_id.id)]
            warehouse = self.env['stock.warehouse'].sudo().search(domain)
            picking.warehouse_id_custom = warehouse

    @api.depends('location_id', 'location_dest_id')
    def _compute_allowed_users(self):
        for picking in self:
            warehouses = self.env['stock.warehouse'].sudo().search([
                '|',
                ('lot_stock_id', '=', picking.location_id.id),
                ('lot_stock_id', '=', picking.location_dest_id.id)
            ])
            users = warehouses.mapped('admin_ids') | warehouses.mapped('user_ids')
            picking.allowed_user_ids = users
            _logger.info(f"[DEBUG] Picking: {picking.name}, Allowed Users: {users.ids}")

    def button_validate(self):
        for picking in self:
            source_wh = self.env['stock.warehouse'].search([('lot_stock_id', '=', picking.location_id.id)], limit=1)
            dest_wh = self.env['stock.warehouse'].search([('lot_stock_id', '=', picking.location_dest_id.id)], limit=1)

            allowed_admin_ids = (source_wh.admin_ids | dest_wh.admin_ids).ids

            if self.env.user.id not in allowed_admin_ids:
                raise UserError(
                    _('You are not allowed to validate this transfer. Only the warehouse admins of the source or destination warehouse can do that.')
                )

        return super().button_validate()

    def action_confirm(self):
        for picking in self:
            if picking.state == 'draft' and picking.picking_type_id.code == 'internal':
                # Detect return picking
                is_return = any(p.origin_returned_move_id for p in picking.move_ids)

                if is_return:
                    _logger.info(f"[DEBUG] Skipping custom confirm logic for return Picking {picking.name}")
                    continue

                _logger.info(
                    f"[DEBUG] action_confirm called on Picking {picking.name} "
                    f"by User {self.env.user.name} (ID: {self.env.user.id}) — "
                    f"State: {picking.state}"
                )

                if self.env.context.get('skip_note_wizard'):
                    dest_wh = self.env['stock.warehouse'].search(
                        [('lot_stock_id', '=', picking.location_dest_id.id)],
                        limit=1
                    )
                    allowed_users = dest_wh.admin_ids | dest_wh.user_ids

                    if self.env.user not in allowed_users:
                        raise UserError(
                            _('You are not allowed to confirm this transfer. '
                              'Only users or admins of the destination warehouse can do that.')
                        )
                else:
                    # Show wizard for just one record
                    return {
                        'name': _('Add Confirmation Note'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'stock.picking.confirm.note.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_picking_id': picking.id,
                        },
                    }

        # Call the original confirmation logic
        return super().action_confirm()

    @api.model_create_multi
    def create(self, vals):
        # create the record first
        picking = super().create(vals)

        # Prepare the message content
        lines = picking.move_ids_without_package  # all stock moves (lines)
        if lines:
            message = "Products and quantities:"
            for line in lines:
                product_name = line.product_id.display_name
                qty = line.product_uom_qty
                message += f"- {product_name}: {qty}"

            # Log the message in chatter
            picking.message_post(body=message)

        return picking

    def unlink(self):
        for picking in self:
            dest_wh = self.env['stock.warehouse'].search(
                [('lot_stock_id', '=', picking.location_dest_id.id)],
                limit=1
            )
            source_wh = self.env['stock.warehouse'].search(
                [('lot_stock_id', '=', picking.location_id.id)],
                limit=1
            )
            disallowed_users = dest_wh.user_ids | source_wh.user_ids

            if self.env.user in disallowed_users:
                raise UserError(_('You cannot delete this picking because you confirmed it.'))
        return super().unlink()

    def write(self, vals):
        for picking in self:
            # Log the entire vals dict
            _logger.info(
                f"[DEBUG] Write called on Picking {picking.name} by User {self.env.user.name} (ID: {self.env.user.id})\n"
                f"Vals: {vals}"
            )
            # Log old and new state if state is being changed
            if 'state' in vals:
                old_state = picking.state
                new_state = vals['state']
                _logger.info(
                    f"[DEBUG] State change for Picking {picking.name} — Old state: {old_state}, New state: {new_state}"
                )
            
            # Only apply restrictions for internal transfers
            if picking.picking_type_id.code == 'internal':
                # Permission checks
                dest_wh = self.env['stock.warehouse'].search(
                    [('lot_stock_id', '=', picking.location_dest_id.id)],
                    limit=1
                )
                source_wh = self.env['stock.warehouse'].search(
                    [('lot_stock_id', '=', picking.location_id.id)],
                    limit=1
                )
                disallowed_users = dest_wh.user_ids | source_wh.user_ids
                if self.env.user in dest_wh.user_ids or (picking.state != 'draft' and self.env.user in disallowed_users):
                    raise UserError(_('You cannot edit this picking as user.'))
        
        tracked_fields = ['picking_type_id', 'location_id', 'location_dest_id']
        changes = {}

        for record in self:
            for field in tracked_fields:
                if field in vals:
                    old_value = record[field].display_name if record[field] else _("None")
                    new_record = self.env[record._fields[field].comodel_name].browse(vals[field])
                    new_value = new_record.display_name if new_record.exists() else _("None")
                    if old_value != new_value:
                        changes.setdefault(record.id, []).append(
                            (record._fields[field].string, old_value, new_value)
                        )

        result = super().write(vals)

        if changes:
            for record in self:
                if record.id in changes:
                    user = self.env.user.name
                    message_lines = [_(f"Updated by {user}:")]
                    for field_label, old, new in changes[record.id]:
                        message_lines.append(f"- {field_label}: {old} → {new}")
                    record.message_post(body=" ".join(message_lines))

        return result
