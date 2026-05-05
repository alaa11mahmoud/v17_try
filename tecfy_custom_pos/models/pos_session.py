# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api


class PosSession(models.Model):
    """Inherited pos session for loading quantity fields from product"""
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Load forecast and on hand quantity field to pos session.
           :return dict: returns dictionary of field parameters for the
                        product model
        """
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend([
            'qty_available',
            'virtual_available',
            'pos_stock_quantity'
        ])
        return result

    def _get_pos_ui_product_product(self, params):
        """Override to add the new pos_stock_quantity field"""
        products = super()._get_pos_ui_product_product(params)
        for product in products:
            product_obj = self.env['product.product'].browse(product['id'])
            product['pos_stock_quantity'] = self._get_pos_stock_quantity(product_obj)
        return products

    def _get_pos_stock_quantity(self, product):
        """Calculate the stock quantity for the product in the POS's linked warehouse"""
        pos_config = self.config_id
        if pos_config.picking_type_id and pos_config.picking_type_id.default_location_src_id:
            location = pos_config.picking_type_id.default_location_src_id
            return product.with_context(location=location.id).qty_available
        return product.qty_available


class ProductProduct(models.Model):
    _inherit = 'product.product'

    pos_stock_quantity = fields.Float(
        string='POS Stock Quantity',
        compute='_compute_pos_stock_quantity',
        store=False
    )

    @api.depends('qty_available')
    def _compute_pos_stock_quantity(self):
        """Compute method for pos_stock_quantity"""
        for product in self:
            pos_session = self.env['pos.session'].search([('state', '=', 'opened')], limit=1)
            if pos_session:
                product.pos_stock_quantity = pos_session._get_pos_stock_quantity(product)
            else:
                product.pos_stock_quantity = product.qty_available