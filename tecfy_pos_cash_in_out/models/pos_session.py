from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def try_cash_in_out(self, _type, amount, reason, extras):
        self = self.sudo()
        sign = 1 if _type == 'in' else -1
        sessions = self.filtered('cash_journal_id')
        if not sessions:
            raise UserError(_("There is no cash payment method for this PoS Session"))
        
        self.env['account.bank.statement.line'].sudo().create([
            {
                'pos_session_id': session.id,
                'journal_id': session.cash_journal_id.id,
                'amount': sign * amount,
                'date': fields.Date.context_today(self),
                'payment_ref': '-'.join([session.name, extras['translatedType'], reason]),
            }
            for session in sessions
        ])