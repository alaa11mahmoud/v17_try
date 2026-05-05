from odoo import models, fields


# class ProductTemplate(models.Model):
#     _inherit = 'product.template'

#     enable_pricelist_qty_discount = fields.Boolean(
#         string='Enable Pricelist Quantity Discount',
#         default=False,
#         help='Enable discount based on pricelist quantity'
#     )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # enable_pricelist_qty_discount = fields.Boolean(
    #     related='product_tmpl_id.enable_pricelist_qty_discount',
    #     readonly=False,
    #     store=True
    # )
    enable_pricelist_qty_discount = fields.Boolean(
        string='Enable Pricelist Quantity Discount',
        default=False,
        help='Enable discount based on pricelist quantity'
    )