import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _prepare_invoice_vals(self):
        _logger.info("=== _prepare_invoice_vals called ===")
        invoice_vals = super()._prepare_invoice_vals()
        
        if self.session_id.config_id.analytic_distribution:
            _logger.info("Found analytic distribution configuration")
            analytic_distribution = {
                str(analytic.id): 100.0 / len(self.session_id.config_id.analytic_distribution)
                for analytic in self.session_id.config_id.analytic_distribution
            }
            for line in invoice_vals.get('invoice_line_ids', []):
                if line[2]:  # Check if line has values
                    line[2]['analytic_distribution'] = analytic_distribution
                    _logger.info("Added analytic distribution to invoice line: %s", analytic_distribution)
        
        return invoice_vals

    def _prepare_invoice_line(self, order_line):
        _logger.info("=== _prepare_invoice_line called ===")
        res = super()._prepare_invoice_line(order_line)
        
        if self.session_id.config_id.analytic_distribution:
            analytic_distribution = {
                str(analytic.id): 100.0 / len(self.session_id.config_id.analytic_distribution)
                for analytic in self.session_id.config_id.analytic_distribution
            }
            res['analytic_distribution'] = analytic_distribution
            _logger.info("Added analytic distribution to invoice line: %s", analytic_distribution)
            
        return res

    def _create_order_entry(self):
        _logger.info("=== _create_order_entry called ===")
        move = super()._create_order_entry()
        
        if self.session_id.config_id.analytic_distribution:
            analytic_distribution = {
                str(analytic.id): 100.0 / len(self.session_id.config_id.analytic_distribution)
                for analytic in self.session_id.config_id.analytic_distribution
            }
            for line in move.line_ids:
                # Skip receivable/payable accounts
                if line.account_id.internal_type in ['receivable', 'payable']:
                    continue
                line.analytic_distribution = analytic_distribution
                _logger.info("Added analytic distribution to move line: %s", analytic_distribution)
        
        return move

    def _prepare_account_move_line(self, line):
        _logger.info("=== _prepare_account_move_line called ===")
        res = super()._prepare_account_move_line(line)
        
        if self.session_id.config_id.analytic_distribution:
            analytic_distribution = {
                str(analytic.id): 100.0 / len(self.session_id.config_id.analytic_distribution)
                for analytic in self.session_id.config_id.analytic_distribution
            }
            res['analytic_distribution'] = analytic_distribution
            _logger.info("Added analytic distribution to move line: %s", analytic_distribution)
            
        return res

    def _prepare_balancing_line_vals(self, payment_method, amount, amount_converted):
        _logger.info("=== _prepare_balancing_line_vals called ===")
        res = super()._prepare_balancing_line_vals(payment_method, amount, amount_converted)
        
        if self.session_id.config_id.analytic_distribution:
            analytic_distribution = {
                str(analytic.id): 100.0 / len(self.session_id.config_id.analytic_distribution)
                for analytic in self.session_id.config_id.analytic_distribution
            }
            res['analytic_distribution'] = analytic_distribution
            _logger.info("Added analytic distribution to balancing line: %s", analytic_distribution)
        
        return res

    def _prepare_bank_statement_line_payment_values(self, pos_session, payment_lines):
        _logger.info("=== _prepare_bank_statement_line_payment_values called ===")
        res = super()._prepare_bank_statement_line_payment_values(pos_session, payment_lines)
        
        if pos_session.config_id.analytic_distribution:
            analytic_distribution = {
                str(analytic.id): 100.0 / len(pos_session.config_id.analytic_distribution)
                for analytic in pos_session.config_id.analytic_distribution
            }
            if 'line_ids' in res:
                for line in res['line_ids']:
                    if len(line) > 2 and isinstance(line[2], dict):
                        if line[2].get('account_id') and not self.env['account.account'].browse(line[2]['account_id']).internal_type in ['receivable', 'payable']:
                            line[2]['analytic_distribution'] = analytic_distribution
                            _logger.info("Added analytic distribution to bank statement line: %s", analytic_distribution)
        
        return res

    def _create_invoice(self, move_vals):
        _logger.info("=== Creating invoice for POS Order ID: %s ===", self.id)
        _logger.info("Move Values before: %s", move_vals)
        
        if self.session_id.config_id.analytic_distribution:
            analytic_distribution = {
                str(analytic.id): 100.0 / len(self.session_id.config_id.analytic_distribution)
                for analytic in self.session_id.config_id.analytic_distribution
            }
            if 'invoice_line_ids' in move_vals:
                for line in move_vals['invoice_line_ids']:
                    if len(line) > 2 and isinstance(line[2], dict):
                        line[2]['analytic_distribution'] = analytic_distribution
                        _logger.info("Added analytic distribution to invoice line: %s", analytic_distribution)
        
        invoice = super()._create_invoice(move_vals)
        _logger.info("Invoice created: %s", invoice)
        return invoice



