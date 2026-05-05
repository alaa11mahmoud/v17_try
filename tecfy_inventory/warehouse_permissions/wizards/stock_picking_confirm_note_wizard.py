from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class StockPickingConfirmNoteWizard(models.TransientModel):
    _name = 'stock.picking.confirm.note.wizard'
    _description = 'Confirm Picking with Notes'

    picking_id = fields.Many2one('stock.picking', required=True, string="Picking")
    line_ids = fields.One2many('stock.picking.confirm.note.line', 'wizard_id', string="Operation Lines")

    def write(self, vals):
        _logger.info(f"Wizard write called with vals: {vals}")

        # If line_ids are being updated, we need to fix the missing product_id and quantity
        if 'line_ids' in vals:
            _logger.info("Processing line_ids updates...")

            # Get the picking and its moves
            picking = self.picking_id
            moves = picking.move_ids_without_package
            _logger.info(f"Picking has {len(moves)} moves")

            fixed_line_ids = []
            move_index = 0

            for line_operation in vals['line_ids']:
                _logger.info(f"Processing line operation: {line_operation}")

                # Handle different operation types: (0, 0, {...}) for create, (1, id, {...}) for update, etc.
                if len(line_operation) >= 3:
                    operation_type = line_operation[0]
                    line_data = line_operation[2] if len(line_operation) > 2 else {}

                    if operation_type == 0:  # Create operation (0, 0, {...})
                        # This is a new line being created, add missing product info
                        if move_index < len(moves):
                            move = moves[move_index]
                            line_data['product_id'] = move.product_id.id
                            line_data['quantity'] = move.product_uom_qty
                            _logger.info(
                                f"Added product_id={move.product_id.id}, quantity={move.product_uom_qty} to line {move_index}")
                            move_index += 1

                        fixed_line_ids.append((0, 0, line_data))

                    elif operation_type == 1:  # Update operation (1, id, {...})
                        # This is updating an existing line, preserve the operation
                        fixed_line_ids.append(line_operation)

                    else:
                        # Other operations (delete, etc.), preserve as-is
                        fixed_line_ids.append(line_operation)
                else:
                    # Malformed operation, preserve as-is
                    fixed_line_ids.append(line_operation)

            vals['line_ids'] = fixed_line_ids
            _logger.info(f"Fixed line_ids: {fixed_line_ids}")

        result = super().write(vals)
        _logger.info("Wizard write completed successfully")
        return result

    @api.model
    def create(self, vals):
        _logger.info(f"Creating wizard with vals: {vals}")

        # Handle the same logic for create if needed
        if 'line_ids' in vals:
            picking_id = vals.get('picking_id') or self.env.context.get('default_picking_id')
            if picking_id:
                picking = self.env['stock.picking'].browse(picking_id)
                moves = picking.move_ids_without_package

                fixed_line_ids = []
                move_index = 0

                for line_operation in vals['line_ids']:
                    if len(line_operation) >= 3 and line_operation[0] == 0:
                        line_data = line_operation[2]
                        if move_index < len(moves) and not line_data.get('product_id'):
                            move = moves[move_index]
                            line_data['product_id'] = move.product_id.id
                            line_data['quantity'] = move.product_uom_qty
                            move_index += 1
                        fixed_line_ids.append((0, 0, line_data))
                    else:
                        fixed_line_ids.append(line_operation)

                vals['line_ids'] = fixed_line_ids

        # Ensure picking_id is set
        if not vals.get('picking_id') and self.env.context.get('default_picking_id'):
            vals['picking_id'] = self.env.context.get('default_picking_id')

        result = super().create(vals)
        _logger.info(f"Created wizard ID={result.id}")
        return result

    @api.model
    def default_get(self, fields):
        _logger.info("=== WIZARD DEFAULT_GET START ===")
        res = super().default_get(fields)
        picking_id = self.env.context.get('default_picking_id')
        _logger.info(f"Context picking_id: {picking_id}")

        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            _logger.info(f"Picking: {picking.name}, Move count: {len(picking.move_ids_without_package)}")

            lines_data = []
            for i, move in enumerate(picking.move_ids_without_package):
                line_data = {
                    'product_id': move.product_id.id,
                    'quantity': move.product_uom_qty,
                    'note': '',  # Initialize with empty note
                }
                lines_data.append((0, 0, line_data))
                _logger.info(
                    f"Move {i}: Product={move.product_id.display_name} (ID:{move.product_id.id}), Qty={move.product_uom_qty}")

            res['line_ids'] = lines_data
            res['picking_id'] = picking_id  # Ensure picking_id is set
            _logger.info(f"Created {len(lines_data)} wizard lines")

        _logger.info(f"Returning res: {res}")
        _logger.info("=== WIZARD DEFAULT_GET END ===")
        return res

    def action_confirm_with_note(self):
        _logger.info("=== ACTION_CONFIRM_WITH_NOTE START ===")
        self.ensure_one()

        # Log wizard line details
        _logger.info(f"Wizard has {len(self.line_ids)} lines:")
        for i, line in enumerate(self.line_ids):
            _logger.info(
                f"  Line {i}: Product={line.product_id.display_name} (ID:{line.product_id.id}), Qty={line.quantity}, Note='{line.note}'")

        # Access check
        dest_wh = self.env['stock.warehouse'].search(
            [('lot_stock_id', '=', self.picking_id.location_dest_id.id)],
            limit=1
        )
        allowed_users = dest_wh.admin_ids | dest_wh.user_ids
        if self.env.user not in allowed_users:
            raise UserError(_('You are not allowed to confirm this transfer.'))

        picking_id = self.env.context.get('default_picking_id')
        _logger.info(f"Processing picking_id: {picking_id}")

        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            _logger.info(f"Picking: {picking.name}, Move count: {len(picking.move_ids_without_package)}")

            # Create a mapping of product_id to move for easier lookup
            move_by_product = {move.product_id.id: move for move in picking.move_ids_without_package}
            _logger.info(f"Created move mapping with {len(move_by_product)} products")

            messages_posted = 0
            for i, line in enumerate(self.line_ids):
                _logger.info(f"Processing line {i}: Product ID={line.product_id.id}, Note='{line.note}'")

                if line.note and line.product_id:
                    if line.product_id.id in move_by_product:
                        move = move_by_product[line.product_id.id]
                        message = f"{move.product_id.display_name}: {line.note}"
                        _logger.info(f"Posting message: {message}")
                        self.picking_id.message_post(body=message)
                        messages_posted += 1
                    else:
                        _logger.warning(f"Product ID {line.product_id.id} not found in move mapping!")
                else:
                    _logger.info(f"Line {i} has no note or no product, skipping")

            _logger.info(f"Posted {messages_posted} messages total")

        _logger.info("=== ACTION_CONFIRM_WITH_NOTE END ===")
        # Confirm the picking while skipping the wizard
        return self.picking_id.with_context(skip_note_wizard=True).action_confirm()


class StockPickingConfirmNoteLine(models.TransientModel):
    _name = 'stock.picking.confirm.note.line'
    _description = 'Note per Product Line'

    wizard_id = fields.Many2one('stock.picking.confirm.note.wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product")
    quantity = fields.Float(string="Quantity", readonly=True)
    note = fields.Text(string="Note")

    @api.model
    def create(self, vals):
        _logger.info(
            f"Creating wizard line: Product ID={vals.get('product_id')}, Qty={vals.get('quantity')}, Note='{vals.get('note')}'")
        result = super().create(vals)
        _logger.info(f"Created wizard line ID={result.id}")
        return result

    def write(self, vals):
        _logger.info(f"Writing to wizard line ID={self.id}: {vals}")
        if 'note' in vals:
            _logger.info(f"Note being updated from '{self.note}' to '{vals['note']}'")
        return super().write(vals)