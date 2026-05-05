# from odoo import models


# class PosSession(models.Model):
#     _inherit = 'pos.session'

#     def _loader_params_product_product(self):
#         result = super()._loader_params_product_product()
#         if 'enable_pricelist_qty_discount' not in result['search_params']['fields']:
#             result['search_params']['fields'].append('enable_pricelist_qty_discount')
#         return result

#     def _loader_params_product_pricelist_item(self):
#         result = super()._loader_params_product_pricelist_item()
#         if 'quantity' not in result['search_params']['fields']:
#             result['search_params']['fields'].append('quantity')
#         return result
#     def _product_pricelist_item_fields(self):
#         return [
#                 'id',
#                 'product_tmpl_id',
#                 'product_id',
#                 'pricelist_id',
#                 'price_surcharge',
#                 'price_discount',
#                 'price_round',
#                 'price_min_margin',
#                 'price_max_margin',
#                 'company_id',
#                 'currency_id',
#                 'date_start',
#                 'date_end',
#                 'compute_price',
#                 'fixed_price',
#                 'percent_price',
#                 'base_pricelist_id',
#                 'base',
#                 'categ_id',
#                 'min_quantity',
#                 'quantity',
#                 ]