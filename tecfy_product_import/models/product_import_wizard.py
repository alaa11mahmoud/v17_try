from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import pandas as pd
import io
from datetime import datetime
import requests
import certifi
import urllib3
import logging
import re

_logger = logging.getLogger(__name__)


class ProductImportWizard(models.TransientModel):
    _name = 'product.import.wizard'
    _description = 'Product Import Wizard'

    file = fields.Binary(string="Upload Excel File", required=False)
    unique_product_names = fields.Text(string="Unique Product Names", readonly=True)
    image_added = fields.Binary("Image (1920x1920)",
                                compute='_update_product_variant', store=True)

    def _validate_barcode(self, barcode, product_name):
        """Helper method to validate barcode uniqueness."""
        if not barcode:
            return True

        # Search for existing products with this barcode
        existing_products = self.env['product.product'].search([('barcode', '=', barcode)])
        if existing_products:
            product_names = ', '.join(existing_products.mapped('display_name'))
            raise ValidationError(_(
                "Barcode '%s' for product '%s' is already assigned to the following product(s): %s"
            ) % (barcode, product_names))
        return True

    def import_products(self):
        try:
            data = base64.b64decode(self.file)
            df = pd.read_excel(io.BytesIO(data), sheet_name=None)
        except Exception as e:
            raise UserError(_("Error reading the Excel file: %s") % str(e))

        # Initialize a set to keep track of unique product names
        unique_product_names_set = set()

        if 'Variants' in df and not df['Variants'].empty:
            self._process_variants(df['Variants'])

        if 'Products' not in df:
            raise UserError(_("The 'Products' sheet is missing in the uploaded file."))
        self._process_products(df['Products'], unique_product_names_set)

        # Store unique product names as a string in the field
        self.unique_product_names = ', '.join(unique_product_names_set)

        self._update_product_variants(unique_product_names_set)

    def _process_variants(self, variants_df):
        """Process the Variants sheet to update product.attribute and product.attribute.value."""
        required_columns = ['Variant Name', 'Variant Value']

        for col in required_columns:
            if col not in variants_df.columns:
                raise UserError(_("The 'Variants' sheet must contain the columns: %s") % ', '.join(required_columns))

        if variants_df.empty or variants_df[required_columns].dropna(how='all').empty:
            return

        for _, row in variants_df.iterrows():
            variant_name = row['Variant Name'].strip() if pd.notna(row['Variant Name']) else ''
            variant_values = [value.strip() for value in row['Variant Value'].split(',')] if pd.notna(
                row['Variant Value']) else []

            if not variant_name or not variant_values:
                continue

            variant_name = variant_name.lower()
            variant_values = [value.lower() if isinstance(value, str) else value for value in variant_values]

            attribute = self.env['product.attribute'].search([('name', '=', variant_name)], limit=1)
            if not attribute:
                attribute = self.env['product.attribute'].create({'name': variant_name})

            for value in variant_values:
                existing_value = self.env['product.attribute.value'].search([
                    ('name', '=', value),
                    ('attribute_id', '=', attribute.id)
                ], limit=1)
                if not existing_value:
                    self.env['product.attribute.value'].create({
                        'name': value,
                        'attribute_id': attribute.id
                    })

    def _process_products(self, products_df, unique_product_names_set):
        """Process the Products sheet to update or create products, including setting images."""
        required_columns = [
            'Product Name', 'Product Type', 'Unit of Measure', 'Product Category', 'Is POS Product', 'POS Category',
            'Variant Value', 'Barcode', 'Internal Reference', 'Sales Price', 'Cost', 'Weight', 'Description',
            'Image URL'
        ]
        for col in required_columns:
            if col not in products_df.columns:
                raise UserError(_("The 'Products' sheet must contain the columns: %s") % ', '.join(required_columns))

        for _, row in products_df.iterrows():

            product_name = row.get('Product Name')

            if pd.isna(product_name) or not str(product_name).strip():
                raise UserError("Product Name cannot be null")

            product_name = str(product_name).strip()
            unique_product_names_set.add(product_name)

            variant_raw = row.get('Variant Value', '')

            variant_values = []
            if pd.notna(variant_raw) and str(variant_raw).strip():
                variant_values = [
                    str(value).strip()
                    for value in str(variant_raw).split(',')
                    if str(value).strip()
                ]

            if pd.isna(row['Barcode']) or not str(row['Barcode']).strip():
                raise UserError("Barcode cannot be null.")
            else:
                barcode = row.get('Barcode', '')

            if pd.isna(row['Internal Reference']) or not str(row['Internal Reference']).strip():
                raise UserError("Internal Reference cannot be null.")
            else:
                internal_ref = row.get('Internal Reference', '')

            if pd.isna(row['Sales Price']) or not str(row['Sales Price']).strip():
                sales_price = 0.0
            else:
                sales_price = row.get('Sales Price', 0.0)

            if pd.isna(row['Cost']) or not str(row['Cost']).strip():
                cost = 0.0
            else:
                cost = row.get('Cost', 0.0)

            if pd.isna(row['Weight']) or not str(row['Weight']).strip():
                weight = 0.0
            else:
                weight = row.get('Weight', 0.0)

            if not pd.isna(row.get('Description')) and str(row.get('Description')).strip():
                description = str(row.get('Description')).strip()
            else:
                description = False

                # Process Product Category
            product_category_name = str(row.get('Product Category')).strip() if pd.notna(
                row.get('Product Category')) else "All"

            # Search for the category or create it
            product_category = self.env['product.category'].search([('name', '=', product_category_name)], limit=1)
            if not product_category:
                product_category = self.env['product.category'].create({'name': product_category_name})

            if str(row.get('Is POS Product')).strip().lower() in ['true', 'yes', 'set', 'checked']:
                pos_product = True
            else:
                pos_product = False

            # Process POS Categories only if the product is marked as a POS product
            pos_category_ids = []
            if pos_product and pd.notna(row.get('POS Category')):
                pos_categories = [
                    cat.strip() for cat in str(row.get('POS Category')).split(',') if cat.strip()
                ]
                for pos_category_name in pos_categories:
                    pos_category = self.env['pos.category'].search([('name', '=', pos_category_name)], limit=1)
                    if not pos_category:
                        pos_category = self.env['pos.category'].create({'name': pos_category_name})
                    pos_category_ids.append(pos_category.id)

            
            product_type_value = row.get('Product Type', 'storable')
            product_type_raw = str(product_type_value).strip().lower() if pd.notna(product_type_value) else "product"
            # product_type_raw = row.get('Product Type', 'storable').strip().lower()
            product_type = {
                'storable': 'product',
                'consumable': 'consu',
                'service': 'service'
            }.get(product_type_raw, 'product')

            
            product_unit_value = row.get('Unit of Measure', 'Unit')
            product_unit = str(product_unit_value).strip() if pd.notna(product_unit_value) else "Unit"
            # product_unit = row.get('Unit of Measure', 'Unit').strip()
            uom_record = self.env['uom.uom'].search([('name', '=', product_unit)], limit=1)
            if not uom_record:
                raise UserError("Unit of Measure '%s' not found." % product_unit)

            product_template = self.env['product.template'].search([('name', '=', product_name)], limit=1)
            if not product_template:
                product_template = self.env['product.template'].create({
                    'name': product_name,
                    'type': product_type,
                    'uom_id': uom_record.id,
                    'uom_po_id': uom_record.id,
                    'categ_id': product_category.id,
                    'description': description,
                    'available_in_pos': pos_product,
                    'pos_categ_ids': [(6, 0, pos_category_ids)],
                })

            else:
                product_template.write({
                    'description': description,
                    'categ_id': product_category.id,
                    'available_in_pos': pos_product,
                    'pos_categ_ids': [(6, 0, pos_category_ids)] if pos_category_ids else False,
                })

            if variant_values:
                self._create_product_attributes(product_template, variant_values)

            domain = [('product_tmpl_id', '=', product_template.id)]
            for variant_value in variant_values:
                domain.append(('product_template_attribute_value_ids.name', '=', variant_value))

            variant = self.env['product.product'].search(domain, limit=1)
            if not variant:
                product_template._create_variant_ids()
                # Try to find again based on the variant values
                variant = self.env['product.product'].search(domain, limit=1)
            
            # Fallback to get any variant from the template if no match
            if not variant:
                variant = self.env['product.product'].search([('product_tmpl_id', '=', product_template.id)], limit=1)
            
            # If still no variant exists, create one manually (rare edge case)
            if not variant:
                variant = self.env['product.product'].create({
                    'product_tmpl_id': product_template.id,
                    'barcode': barcode,
                    'default_code': internal_ref,
                    'lst_price': sales_price,
                    'standard_price': cost,
                    'weight': weight,
                })

            if variant:
                self._update_product_variant(
                    variant=variant,
                    barcode=barcode,
                    internal_ref=internal_ref,
                    sales_price=sales_price,
                    cost=cost,
                    weight=weight
                )

                # Process Image URL
                image_url = row.get('Image URL')
                if image_url and pd.notna(image_url):
                    try:
                        image_data = self._fetch_image_from_url(image_url)
                        variant.image_1920 = image_data
                    except Exception as e:
                        raise UserError(_("Failed to fetch image from URL '%s': %s") % (image_url, str(e)))

    def _fetch_image_from_url(self, url):
        """Fetch and return image content from a URL."""
        import requests
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise UserError(_("Failed to fetch image from URL. HTTP status code: %s") % response.status_code)
        return base64.b64encode(response.content)

    def _update_product_variant(self, variant, barcode, internal_ref, sales_price, cost, weight):
        """Update the product variant without modifying specific fields unless they change."""
        if variant.barcode != barcode:
            variant.barcode = barcode
        if variant.default_code != internal_ref:
            variant.default_code = internal_ref
        if variant.lst_price != sales_price:
            variant.lst_price = sales_price
        if variant.standard_price != cost:
            variant.standard_price = cost
        if variant.weight != weight:
            variant.weight = weight

    def _create_product_attributes(self, product_template, variant_values):
        """Create product attributes dynamically based on the Variant Value column
        from the Products sheet and link them to the product template.
        """
        for variant in variant_values:
            value_obj = self.env['product.attribute.value'].search([('name', '=', variant)], limit=1)
            if not value_obj:
                raise UserError(_("Attribute value '%s' not found.") % variant)

            attribute_name = value_obj.attribute_id.name

            attribute = self.env['product.attribute'].search([('name', '=', attribute_name)], limit=1)
            if not attribute:
                attribute = self.env['product.attribute'].create({'name': attribute_name})

            if attribute.id not in product_template.attribute_line_ids.mapped('attribute_id').ids:
                product_template.attribute_line_ids = [(0, 0, {
                    'attribute_id': attribute.id,
                    'value_ids': [(4, value_obj.id)],
                })]
            else:
                attribute_line = product_template.attribute_line_ids.filtered(
                    lambda line: line.attribute_id.id == attribute.id
                )
                if value_obj.id not in attribute_line.value_ids.ids:
                    attribute_line.value_ids = [(4, value_obj.id)]

    def _update_product_variants(self, unique_product_names_set):
        """Update the variants of the products in unique_product_names."""
        for product_name in unique_product_names_set:
            product_template = self.env['product.template'].search([('name', '=', product_name)], limit=1)
            if product_template:
                variants = self.env['product.product'].search([('product_tmpl_id', '=', product_template.id)])

                for variant in variants:
                    self._update_product_variant(variant, variant.barcode, variant.default_code, variant.lst_price,
                                                 variant.standard_price, variant.weight)

    def extract_id(self, raw_id):
        """Extracts numeric ID from exported Odoo ID format."""
        if isinstance(raw_id, str) and raw_id.startswith("__export__."):
            match = re.search(r'product_product_(\d+)', raw_id)
            if match:
                return int(match.group(1))
        return int(raw_id) if pd.notna(raw_id) else None


    def update_products_with_ids(self):
        """Function to process the update file"""
        if not self.update_file:
            return

        try:
            file_content = base64.b64decode(self.update_file)
            df = pd.read_excel(io.BytesIO(file_content))

            required_columns = {"ID", "Internal Reference", "Barcode", "Name", "Weight", "Sales Price", "Cost",
                                "Product Category"}
            if not required_columns.issubset(df.columns):
                raise ValueError("Missing required columns in the update file.")

            for _, row in df.iterrows():
                domain = []

                if pd.notna(row.get("ID")):
                    odoo_id = self.extract_id(row.get("ID"))
                    if odoo_id:
                        domain.append(("id", "=", odoo_id))
                    else:
                        domain.append(("id", "=", str(row["ID"])))

                if not domain:
                    continue  # Skip if no valid identifier

                product = self.env["product.product"].search(domain, limit=1)
                if product:
                    product.write({
                        "default_code": row["Internal Reference"] if pd.notna(
                            row["Internal Reference"]) else product.default_code,
                        "barcode": row["Barcode"] if pd.notna(row["Barcode"]) else product.barcode,
                        "name": row["Name"] if pd.notna(row["Name"]) else product.name,
                        "weight": row["Weight"] if pd.notna(row["Weight"]) else product.weight,
                        "list_price": row["Sales Price"] if pd.notna(row["Sales Price"]) else product.list_price,
                        "standard_price": row["Cost"] if pd.notna(row["Cost"]) else product.standard_price,
                        "categ_id": self.env["product.category"].search([("name", "=", row["Product Category"])],
                                                                        limit=1).id if pd.notna(
                            row["Product Category"]) else product.categ_id.id,
                    })
        except Exception as e:
            raise ValueError(f"Error processing update file: {str(e)}")


    def download_sample_file(self):
        """Generate a sample Excel file with two sheets: Products and Variants."""
        products_sample_data = [
            {
                'Product Name': 'T-shirt',
                'Product Type': 'Consumable',
                'Unit of Measure': 'Unit',
                'Product Category': 'All',
                'Is POS Product': 'Yes',
                'POS Category': 'Apparel, Summer',
                'Variant Value': 's,blue',
                'Barcode': '1234567890123',
                'Internal Reference': 'SP001',
                'Sales Price': 55.0,
                'Cost': 50.0,
                'Weight': 1.5,
                'Image URL': '',
                'Description': 'Hello From Odoo'
            },
            {
                'Product Name': 'T-shirt',
                'Product Type': 'Consumable',
                'Unit of Measure': 'Unit',
                'Product Category': 'Expenses',
                'Is POS Product': 'Yes',
                'POS Category': 'Apparel, Summer',
                'Variant Value': 's,red',
                'Barcode': '12345656454',
                'Internal Reference': 'SP002',
                'Sales Price': 58.0,
                'Cost': 40.0,
                'Weight': 2.5,
                'Image URL': '',
                'Description': ''
            },
            {
                'Product Name': 'T-shirt 2',
                'Product Type': 'Storable',
                'Unit of Measure': 'Unit',
                'Product Category': '',
                'Is POS Product': 'No',
                'POS Category': '',
                'Variant Value': 'm,green',
                'Barcode': '98734509',
                'Internal Reference': 'SP003',
                'Sales Price': 66.0,
                'Cost': 54.0,
                'Weight': 3,
                'Image URL': '',
                'Description': ''
            },
        ]

        variants_sample_data = [
            {'Variant Name': 'Size', 'Variant Value': 's, m, l, xl'},
            {'Variant Name': 'Color', 'Variant Value': 'blue, red, green'}
        ]

        df_products = pd.DataFrame(products_sample_data)
        df_variants = pd.DataFrame(variants_sample_data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_products.to_excel(writer, index=False, sheet_name='Products')
            df_variants.to_excel(writer, index=False, sheet_name='Variants')

        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        today_date = datetime.today().strftime('%Y-%m-%d')
        filename = f"product_import_template_{today_date}.xlsx"

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'store_fname': filename,
            'res_model': 'product.import.wizard',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def download_update_product_with_ids_sample_file(self):
        """Generate a sample Excel file for the user to download"""
        sample_data = {
            "ID": [""],
            "Internal Reference": [""],
            "Barcode": [""],
            "Name": ["Sample Product"],
            "Weight": ["1.0"],
            "Sales Price": ["100.0"],
            "Cost": ["50.0"],
            "Product Category": ["All"]
        }
        df = pd.DataFrame(sample_data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='xlsxwriter')
        output.seek(0)
        sample_file = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'product_update_sample.xlsx',
            'datas': sample_file,
            'res_model': 'product.import.wizard',
            'res_id': self.id,
            'type': 'binary'
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
