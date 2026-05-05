# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    max_line_discount = fields.Float(
        string='Max Line Discount (%)',
        default=100.0,
        help='Maximum discount percentage allowed on order lines. Set to 100 for no limit, 0 to disable discounts.',
    )

    @api.constrains('max_line_discount')
    def _check_max_line_discount(self):
        """Validate that max_line_discount is between 0 and 100"""
        for record in self:
            if record.max_line_discount < 0 or record.max_line_discount > 100:
                raise ValidationError(
                    'Maximum line discount must be between 0 and 100.'
                )
