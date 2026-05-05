# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import io
import base64
try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class StockCardLineExport(models.TransientModel):
    _inherit = 'stock.card.line'

    def action_export_xlsx(self):
        if not xlsxwriter:
            raise UserError(_("The xlsxwriter library is not installed."))

        # 1. Get records to export
        # If records are selected, use them. Otherwise, use the context domain.
        records = self
        if not records:
            domain = self._context.get('active_domain', [])
            records = self.search(domain)

        if not records:
            return

        # 2. Setup Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Stock Card')

        # Formats
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1, 'align': 'center'})
        group_format = workbook.add_format({'bold': True, 'bg_color': '#F0F0F0', 'border': 1})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        num_format = workbook.add_format({'num_format': '#,##0.00'})
        bold_num_format = workbook.add_format({'num_format': '#,##0.00', 'bold': True, 'bg_color': '#F0F0F0'})

        # Headers
        headers = [
            _('Date'), _('Reference'), _('Created By'), _('Product'),
            _('Unit Cost'), _('From'), _('To'), _('In'), _('Out'),
            _('Total Cost'), _('Balance')
        ]
        
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)
            sheet.set_column(col, col, 15)

        # 3. Group records by Product (to match UI)
        grouped_data = {}
        for rec in records.sorted(key=lambda r: (r.product_id.display_name, r.date or '', r.id)):
            product_name = rec.product_id.display_name or _('Unknown')
            if product_name not in grouped_data:
                grouped_data[product_name] = []
            grouped_data[product_name].append(rec)

        # 4. Write data
        row = 1
        for product_name, lines in grouped_data.items():
            # Calculate group totals (to show in group header)
            # For Balance, we take the LAST line's balance
            last_line = lines[-1]
            group_balance = last_line.balance
            group_qty_in = sum(l.qty_in for l in lines)
            group_qty_out = sum(l.qty_out for l in lines)
            group_total_cost = sum(l.value for l in lines)

            # Write Group Header
            sheet.write(row, 0, f"{product_name} ({len(lines)})", group_format)
            sheet.write(row, 1, "", group_format)
            sheet.write(row, 2, "", group_format)
            sheet.write(row, 3, "", group_format)
            sheet.write(row, 4, "", group_format)
            sheet.write(row, 5, "", group_format)
            sheet.write(row, 6, "", group_format)
            sheet.write(row, 7, group_qty_in, bold_num_format)
            sheet.write(row, 8, group_qty_out, bold_num_format)
            sheet.write(row, 9, group_total_cost, bold_num_format)
            sheet.write(row, 10, group_balance, bold_num_format) # The MAGIC: Last balance
            
            row += 1

            # Write individual lines
            for line in lines:
                sheet.write(row, 0, line.date or '', date_format)
                sheet.write(row, 1, line.reference or '')
                sheet.write(row, 2, line.created_by_id.name or '')
                sheet.write(row, 3, line.product_id.display_name or '')
                sheet.write(row, 4, line.unit_cost, num_format)
                sheet.write(row, 5, line.location_from_id.display_name or '')
                sheet.write(row, 6, line.location_to_id.display_name or '')
                sheet.write(row, 7, line.qty_in, num_format)
                sheet.write(row, 8, line.qty_out, num_format)
                sheet.write(row, 9, line.value, num_format)
                sheet.write(row, 10, line.balance, num_format)
                row += 1

        workbook.close()
        output.seek(0)
        
        # 5. Create attachment and return action
        file_name = 'Stock_Card_Report.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        output.close()

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
