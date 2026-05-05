from odoo import fields, models, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    pricelist_select_id = fields.Many2one(
        'product.pricelist',
        string='Default Pricelist',
        help='The default pricelist for this Point of Sale configuration.'
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_pricelist_select_id = fields.Many2one(
        'product.pricelist',
        string='Default Pricelist',
        compute='_compute_pos_pricelist_select_id',
        inverse='_inverse_pos_pricelist_select_id',
        readonly=False,
        store=True,
    )

    @api.depends('pos_journal_id.currency_id', 'pos_config_id.company_id.currency_id', 'pos_use_pricelist')
    def _compute_pos_pricelist_select_id(self):
        for res_config in self:
            currency_id = res_config.pos_journal_id.currency_id.id if res_config.pos_journal_id.currency_id else res_config.pos_config_id.company_id.currency_id.id
            pricelists_in_current_currency = self.env['product.pricelist'].search([
                *self.env['product.pricelist']._check_company_domain(res_config.pos_config_id.company_id),
                ('currency_id', '=', currency_id),
            ])
            if not res_config.pos_use_pricelist:
                res_config.pos_pricelist_select_id = False
            else:
                if not res_config.pos_config_id.pricelist_select_id or res_config.pos_config_id.pricelist_select_id.currency_id.id != currency_id:
                    res_config.pos_pricelist_select_id = pricelists_in_current_currency[:1]
                else:
                    res_config.pos_pricelist_select_id = res_config.pos_config_id.pricelist_select_id

    def _inverse_pos_pricelist_select_id(self):
        for settings in self:
            if settings.pos_config_id:
                settings.pos_config_id.pricelist_select_id = settings.pos_pricelist_select_id