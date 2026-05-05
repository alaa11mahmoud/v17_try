import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.session'

    def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        _logger.info("=== _create_account_move called ===")

        # Call the original method to create the move and related lines
        data = super()._create_account_move(balancing_account, amount_to_balance, bank_payment_method_diffs)
        _logger.info("Data returned by the parent method: %s", data)

        # Retrieve the created account.move record
        move = self.move_id
        if not move:
            _logger.error("No account.move record found after calling the original method. Exiting.")
            return data

        # Check if analytic distribution is configured for the session
        if self.config_id.analytic_distribution:
            analytic_distribution = {
                str(analytic.id): 100.0 / len(self.config_id.analytic_distribution)
                for analytic in self.config_id.analytic_distribution
            }

            # Apply analytic distribution to each move line (excluding receivable/payable accounts)
            for line in move.line_ids:
                if not line.account_id:
                    _logger.warning("Move line %s has no account_id.", line.id)
                    continue

                line.analytic_distribution = analytic_distribution
                _logger.info("Added analytic distribution to move line: %s", line.id)

        return data
