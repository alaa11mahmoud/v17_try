from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockCardReportWizard(models.TransientModel):
    _name = 'stock.card.report.wizard'
    _description = 'Stock Card Report Wizard'

    date_from = fields.Datetime(string="From Date")
    date_to = fields.Datetime(string="To Date")

    location_ids = fields.Many2many(
        'stock.location',
        string="Locations",
        domain=[('usage', '=', 'internal')],
        help="Select one or more internal stock locations. ⚠️ Do not select this if you are using Warehouse Addresses."
    )

    warehouse_partner_ids = fields.Many2many(
        'res.partner',
        string="Warehouse Addresses",
        domain=lambda self: [('id', 'in', self.env['stock.warehouse'].search([]).mapped('partner_id').ids)],
        help="Select the partner addresses of warehouses. ⚠️ Do not select this if you have chosen specific stock locations."
    )

    product_ids = fields.Many2many('product.product', string="Products")
    conflict_triggered = fields.Boolean(string="Conflict Triggered", default=False)

    @api.onchange('location_ids', 'warehouse_partner_ids')
    def _onchange_location_or_partner(self):
        if self.location_ids and self.warehouse_partner_ids:
            self.location_ids = [(5, 0, 0)]
            self.warehouse_partner_ids = [(5, 0, 0)]
            self.product_ids = [(5, 0, 0)]
            self.conflict_triggered = True

    def _get_location_ids_from_partners(self):
        """Return internal stock locations related to selected warehouse partners."""
        warehouse_partners = self.warehouse_partner_ids.ids
        warehouses = self.env['stock.warehouse'].search([('partner_id', 'in', warehouse_partners)])
        location_ids = []
        for wh in warehouses:
            location_ids += wh.view_location_id.child_ids.filtered(lambda l: l.usage == 'internal').ids
        return location_ids

    def action_print_report(self):
        if self.conflict_triggered:
            self.conflict_triggered = False
            raise ValidationError(
                "You cannot select both Locations and Warehouse Addresses.\nAll values have been reset. Please select only one.")

        self.ensure_one()
        self.env['stock.card.line'].search([('wizard_id', '=', self.id)]).unlink()

        products = self.product_ids or self.env['product.product'].search([])
        StockCardLine = self.env['stock.card.line']
        lines_to_create = []

        if self.location_ids:
            location_ids = self.location_ids.ids
        elif self.warehouse_partner_ids:
            location_ids = self._get_location_ids_from_partners()
        else:
            raise ValidationError("Please select either Locations or Warehouse Addresses.")

        for product in products:
            # ==== Compute Initial Balance ====
            init_balance = 0.0
            if self.date_from:
                init_domain = [
                    ('product_id', '=', product.id),
                    '|',
                    ('location_id', 'in', location_ids),
                    ('location_dest_id', 'in', location_ids),
                    ('date', '<', self.date_from),
                ]
                init_moves = self.env['stock.move.line'].search(init_domain)
                for move in init_moves:
                    if move.location_dest_id.id in location_ids:
                        init_balance += move.quantity
                    elif move.location_id.id in location_ids:
                        init_balance -= move.quantity

            # ==== Get Move Lines In Date Range ====
            domain = [
                ('product_id', '=', product.id),
                '|',
                ('location_id', 'in', location_ids),
                ('location_dest_id', 'in', location_ids),
            ]
            if self.date_from:
                domain.append(('date', '>=', self.date_from))
            if self.date_to:
                domain.append(('date', '<=', self.date_to))

            move_lines = self.env['stock.move.line'].search(domain, order='date')

            if not move_lines:
                continue

            # ==== Add Initial Balance Line ====
            balance = init_balance
            lines_to_create.append({
                'wizard_id': self.id,
                'date': self.date_from,
                'reference': 'Initial Balance',
                'created_by_id': False,
                'product_id': product.id,
                'location_from_id': False,
                'location_to_id': False,
                'qty_in': 0.0,
                'qty_out': 0.0,
                'balance': balance,
            })

            for move in move_lines:
                qty_in = qty_out = 0.0
                if move.location_dest_id.id in location_ids:
                    qty_in = move.quantity
                    balance += qty_in
                elif move.location_id.id in location_ids:
                    qty_out = move.quantity
                    balance -= qty_out

                # Try to get the valuation layer
                valuation_layer = self.env['stock.valuation.layer'].search(
                    [('stock_move_id', '=', move.move_id.id)],
                    limit=1
                )

                unit_cost = valuation_layer.unit_cost if valuation_layer else 0.0
                value = valuation_layer.value if valuation_layer else 0.0

                lines_to_create.append({
                    'wizard_id': self.id,
                    'date': move.date,
                    'reference': move.reference or move.move_id.name,
                    'created_by_id': move.move_id.create_uid.id,
                    'product_id': product.id,
                    'unit_cost': unit_cost,
                    'location_from_id': move.location_id.id,
                    'location_to_id': move.location_dest_id.id,
                    'qty_in': qty_in,
                    'qty_out': qty_out,
                    'value': value,
                    'balance': balance,
                })

        if lines_to_create:
            StockCardLine.create(lines_to_create)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Card Result',
            'res_model': 'stock.card.line',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('wizard_id', '=', self.id)],
            'context': {'default_wizard_id': self.id},
            'search_view_id': self.env.ref('stock_card_report.view_stock_card_line_search').id,
        }
