from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo import http
from odoo.tools import pdf
from io import BytesIO
import base64
import xlsxwriter

class StockReportWizard(models.TransientModel):
    _name = 'tecfy.stock.report.wizard'
    _description = 'Stock Report Wizard'

    product_ids = fields.Many2many('product.product', string='Products', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def _get_report_data(self):
        domain = [('create_date', '>=', self.start_date), ('create_date', '<=', self.end_date)]
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.warehouse_id:
            domain.append(('company_id', '=', self.warehouse_id.company_id.id))
        
        return self.env['stock.valuation.layer'].search(domain, order='create_date')

    def action_export_pdf(self):
        products = []
        for product in self.product_ids:
            # استرجاع الحركات المتعلقة بالمنتج
            moves = self.env['stock.valuation.layer'].search([
                ('product_id', '=', product.id),
                ('create_date', '>=', self.start_date),
                ('create_date', '<=', self.end_date),
                ('company_id', '=', self.warehouse_id.company_id.id),
            ], order='create_date')

            # تجهيز بيانات المنتج
            total_in_quantity = 0
            total_in_unit_cost = 0
            total_out_quantity = 0
            total_out_unit_cost = 0
            
            product_data = {
                'name': product.name,
                'qty_available': product.qty_available,
                'standard_price': product.standard_price,
                'moves': [
                    {
                        'if_in': move.quantity > 0,
                        'value': move.value,
                        'unit_cost': move.unit_cost,
                        'quantity': move.quantity,
                        'description': move.description,
                        'company_name': self.warehouse_id.name,
                        'id': move.id,
                        'create_date': move.create_date,
                    }
                    for move in moves
                ]
            }
            
            for move in product_data['moves']:
                if move['if_in']:
                    total_in_quantity += move['quantity']
                    total_in_unit_cost += move['unit_cost']
                else:
                    total_out_quantity += move['quantity']
                    total_out_unit_cost += move['unit_cost']
            
            product_data['total_in_quantity'] = total_in_quantity
            product_data['total_in_unit_cost'] = total_in_unit_cost
            product_data['total_out_quantity'] = total_out_quantity
            product_data['total_out_unit_cost'] = total_out_unit_cost
            
            products.append(product_data)

        # تجهيز البيانات النهائية
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'products': products,
            'res_company': self.env.company,
        }

        return self.env.ref('tecfy_stock_report.action_report_stock_pdf').report_action(self, data=data)

    def action_export_excel(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('تقرير المخزون')

        # تنسيقات الخلايا
        top_header_format = workbook.add_format({'bold': True, 'align': 'right'})
        top_header_format_date = workbook.add_format({'bold': True, 'align': 'right','num_format': 'dd-mm-yyyy'})
        table_header_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1 ,'valign': 'vcenter','bg_color': '#a4c2f4' ,'border_color': '#000000' })
        table_cell_header_format = workbook.add_format({'bold': True, 'align': 'center', 'border': 1 ,'valign': 'vcenter','bg_color': '#ffffff' ,'border_color': '#000000' })
        date_format = workbook.add_format({'num_format': 'dd-mm-yyyy'})
        number_format = workbook.add_format({'num_format': '#,##0.00'})
        merge_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})

        # ضبط عرض الأعمدة
        worksheet.set_column('A:J', 15)

        # كتابة البيانات الرئيسية
        worksheet.write('J1', 'من تاريخ', top_header_format)
        worksheet.write_datetime('I1', self.start_date, top_header_format_date)
        worksheet.write('J2', 'الي تاريخ', top_header_format)
        worksheet.write_datetime('I2', self.end_date, top_header_format_date)

        row = 4
        for product in self.product_ids:
            # كتابة اسم المنتج
            worksheet.write(f'J{row}', 'المنتج', top_header_format)
            worksheet.merge_range(f'F{row}:I{row}', product.name, top_header_format)
            row += 1
            worksheet.write(f'J{row}', 'القيمة', top_header_format)
            worksheet.write(f'I{row}', product.qty_available, top_header_format)
            worksheet.write(f'J{row+1}', 'التكلفة', top_header_format)
            worksheet.write(f'I{row+1}',product.qty_available * product.standard_price, top_header_format)
            row += 2

            # كتابة العناوين
            start_sum = row+2
            worksheet.write_row(f'A{row+1}', ['القيمة', 'تكلفة الوحدة', 'الكمية', 'القيمة', 'تكلفة الوحدة', 'الكمية'], table_header_format)
            worksheet.merge_range(f'J{row}:J{row+1}', 'التاريخ', table_header_format)
            worksheet.merge_range(f'I{row}:I{row+1}', 'رقم المسند', table_header_format)
            worksheet.merge_range(f'H{row}:H{row+1}', 'بناء علي', table_header_format)
            worksheet.merge_range(f'G{row}:G{row+1}', 'المخزن', table_header_format)
            worksheet.merge_range(f'A{row}:C{row}', 'صرف', table_header_format)
            worksheet.merge_range(f'D{row}:F{row}', 'توريد', table_header_format)
            row += 2

            # الحصول على بيانات الحركات للمنتج
            valuation_layers = self.env['stock.valuation.layer'].search([
                ('product_id', '=', product.id),
                ('create_date', '>=', self.start_date),
                ('create_date', '<=', self.end_date),
                ('company_id', '<=', self.warehouse_id.company_id.id),
            ], order='create_date')

            total_in_qty = 0
            total_out_qty = 0
            total_in_value = 0
            total_out_value = 0

            for layer in valuation_layers:
                if layer.quantity > 0:  # توريد
                    worksheet.write_row(f'A{row}', ['', '', '', layer.unit_cost * layer.quantity, layer.unit_cost, layer.quantity, self.warehouse_id.name, layer.description or '', layer.id, layer.create_date.strftime('%d-%m-%Y')], table_cell_header_format)
                    # total_in_qty += layer.quantity
                    # total_in_value += layer.value
                else:  # صرف
                    worksheet.write_row(f'A{row}', [layer.unit_cost * abs(layer.quantity), layer.unit_cost, abs(layer.quantity), '', '', '', self.warehouse_id.name, layer.description or '', layer.id, layer.create_date.strftime('%d-%m-%Y')], table_cell_header_format)
                    # total_out_qty += -layer.quantity
                    # total_out_value += -layer.value
                row += 1

            # كتابة الإجمالي
            row_start = row
            worksheet.merge_range(f'G{row}:J{row}', 'الرصيد الاجمالي', table_header_format)
            worksheet.write_formula(f'A{row}', f'SUM(A{row-1}:A{start_sum})', table_header_format)
            worksheet.write_formula(f'B{row}', f'SUM(B{row-1}:B{start_sum})', table_header_format)
            worksheet.write_formula(f'C{row}', f'SUM(C{row-1}:C{start_sum})', table_header_format)
            worksheet.write_formula(f'D{row}', f'SUM(D{row-1}:D{start_sum})', table_header_format)
            worksheet.write_formula(f'E{row}', f'SUM(E{row-1}:E{start_sum})', table_header_format)
            worksheet.write_formula(f'F{row}', f'SUM(F{row-1}:F{start_sum})', table_header_format)
            
            row += 3  # إضافة صفين فارغين بين المنتجات

        workbook.close()
        output.seek(0)

        # إنشاء ملف مرفق
        attachment = self.env['ir.attachment'].create({
            'name': 'تقرير_المخزون.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'store_fname': 'تقرير_المخزون.xlsx',
            'res_model': 'tecfy.stock.report.wizard',
            'res_id': self.id,
        })

        # إرجاع رابط التحميل
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
