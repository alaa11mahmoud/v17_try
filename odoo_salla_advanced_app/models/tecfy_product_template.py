# import requests
# import logging
# from odoo import fields, models, exceptions, api
# from datetime import datetime

# _logger = logging.getLogger(__name__)

# class TecfyProductTemplate(models.Model):
#     _inherit = "product.template"

#     def _sync_with_salla(self, endpoint, product_id):
#         _logger.info(f"Starting sync with Salla for product ID {self.id} using endpoint: {endpoint} and product_id: {product_id}")
#         if not self.exists():
#             _logger.error(f"Product ID {self.id} does not exist in Odoo")
#             return
        
#         # Check if the template has variants
#         product_variants = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
#         _logger.info(f"Found {len(product_variants)} variants for product template ID: {self.id} ,, product_id : {product_id}")
#         # use_product_id = product_id if product_id else (product_variants[0].id if len(product_variants) == 1 else self.id)
#         # use_product_id = product_id if product_id else (self.id if len(product_variants) == 1 else self.id)
        
#         data = {
#             "productId": product_id,
#             "merchantId": int(self.env.user.company_id.tecfy_salla_merchant_id) if self.env.user.company_id.tecfy_salla_merchant_id else None,
#         }
#         _logger.info(f"Prepared data for Salla sync: {data}")
#         try:
#             _logger.info(f"Sending request to Salla API: https://salla.tecfy.co/api/salla/{endpoint}")
#             response = requests.post(
#                 f"https://salla.tecfy.co/api/salla/{endpoint}", 
#                 json=data
#             )
#             response.raise_for_status()
#             try:
#                 response_content = response.json()
#             except ValueError as e:
#                 _logger.error(f"Error parsing JSON response: {response.text}, Error: {str(e)}")
#                 self.message_post(
#                     body=f"Failed to parse Salla API response on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Response: {response.text}",
#                     message_type='notification',
#                     subtype_id=self.env.ref('mail.mt_note').id
#                 )
#                 return
#             if not response_content.get('success', False):
#                 error_message = response_content.get('message', 'Unknown error occurred')
#                 _logger.error(f"Salla API error: {error_message}")
#                 self.message_post(
#                     body=f"Failed to sync with Salla on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Error: {error_message}",
#                     message_type='notification',
#                     subtype_id=self.env.ref('mail.mt_note').id
#                 )
#             else:
#                 _logger.info(f"Salla API Response: {response_content}")
#                 self.message_post(
#                     body=f"Synchronized with Salla successfully on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
#                     message_type='notification',
#                     subtype_id=self.env.ref('mail.mt_note').id
#                 )
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Error syncing product with Salla: {e}")
#         except ValueError as e:
#             _logger.error(f"Error parsing JSON response: {e}")

#     @api.model
#     def create(self, vals):
#         _logger.info(f"Starting product creation with values: {vals}")
#         current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         _logger.info("Calling parent create method")
#         product = super(TecfyProductTemplate, self).create(vals)
#         _logger.info("Parent create method completed successfully")
#         if not product or not product.id:
#             _logger.error("Product creation failed in Odoo")
#             return product
#         self.env.cr.commit()
#         _logger.info(f"Committed product ID {product.id} to database")
#         product = self.browse(product.id)
#         if not product.exists():
#             _logger.error(f"Product ID {product.id} not found after commit")
#             return product
#         company = self.env.company
#         _logger.info(f"Checking company settings - Salla creation enabled: {company.tecfy_product_add_to_salla}")
#         if company.tecfy_product_add_to_salla:
#             _logger.info(f"Starting Salla sync for new product ID: {product.id}")
#             try:
#                 # Check if there are variants
#                 # variants = self.env['product.product'].search([('product_tmpl_id', '=', product.id)])
#                 # _logger.info(f"Found {len(variants)} variants for product ID: {product.id}")
#                 # product_id = variants[0].id if len(variants) == 1 else product.id
#                 product._sync_with_salla("createProductFromOdoo", product_id=product.id)
#                 # _logger.info(f"Salla sync completed for product ID: {product_id}")
#             except Exception as e:
#                 _logger.error(f"Error during Salla sync for product ID: {product.id}: {str(e)}")
#                 raise
#         _logger.info("Product creation process completed successfully")
#         return product

#     def write(self, vals):
#         _logger.info(f"Starting product update for IDs {self.ids} with values: {vals}")
#         current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         _logger.info("Calling parent write method")
#         result = super(TecfyProductTemplate, self).write(vals)
#         _logger.info("Parent write method completed successfully")
#         self.env.cr.commit()
#         _logger.info("Committed product updates to database")
#         synced_fields = [
#             'name', 'description_sale', 'description', 'list_price', 
#             'standard_price', 'barcode', 'qty_available', 'type', 
#             'attribute_line_ids','image_1920', 'image_1024', 'image_512', 'image_256', 'image_128'
#         ]
#         if 'skip_salla_sync' not in self.env.context and any(field in vals for field in synced_fields):
#             company = self.env.company
#             _logger.info(f"Checking company settings - Salla update enabled: {company.tecfy_product_update_to_salla}")
#             if company.tecfy_product_update_to_salla:
#                 _logger.info(f"Starting Salla sync for {len(self)} products (relevant fields changed)")
#                 for index, product in enumerate(self, 1):
#                     _logger.info(f"Processing product {index}/{len(self)} - ID: {product.id}, Name: {product.name}")
#                     try:
#                         # Check if there are variants
#                         # variants = self.env['product.product'].search([('product_tmpl_id', '=', product.id)])
#                         # _logger.info(f"Found {len(variants)} variants for product ID: {product.id}")
#                         # product_id = variants[0].id if len(variants) == 1 else product.id
#                         product._sync_with_salla("createProductFromOdoo", product_id=product.id)
#                         # _logger.info(f"Salla sync completed for product ID: {product_id}")
#                     except Exception as e:
#                         _logger.error(f"Error during Salla sync for product ID: {product.id}: {str(e)}")
#                         raise
#         else:
#             _logger.info("Skipping sync and update logging: No relevant fields changed or sync skipped via context")
#         _logger.info("Product update process completed successfully")
#         return result

# class TecfyProductProduct(models.Model):
#     _inherit = "product.product"

#     @api.depends('write_date', 'product_tmpl_id.write_date')
#     def _compute_write_date(self):
#         for record in self:
#             variant_write_date = record.write_date or self.env.cr.now()
#             template_write_date = record.product_tmpl_id.write_date or datetime(1970, 1, 1)
#             record.write_date = max(variant_write_date, template_write_date)

#     def write(self, vals):
#         _logger.info(f"Starting variant update for IDs {self.ids} with values: {vals}")
#         current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         _logger.info("Calling parent write method")
#         result = super(TecfyProductProduct, self).write(vals)
#         _logger.info("Parent write method completed successfully")
#         self.env.cr.commit()
#         _logger.info("Committed variant updates to database")
#         variant_synced_fields = [
#             'name', 'description' , 'categ_id','barcode', 'default_code', 'lst_price', 'standard_price', 
#             'weight', 'volume'
#         ]
#         if 'skip_salla_sync' not in self.env.context and any(field in vals for field in variant_synced_fields):
#             for variant in self:
#                 variant.message_post(
#                     body=f"Variant updated on {current_time}.",
#                     message_type='notification',
#                     subtype_id=self.env.ref('mail.mt_note').id
#                 )
#             templates = self.mapped('product_tmpl_id')
#             if not templates:
#                 _logger.warning("No parent templates found for updated variants")
#                 return result
#             company = self.env.company
#             _logger.info(f"Checking company settings - Salla update enabled: {company.tecfy_product_update_to_salla}")
#             if company.tecfy_product_update_to_salla:
#                 _logger.info(f"Starting Salla sync for {len(templates)} parent templates (due to variant changes)")
#                 for index, template in enumerate(templates, 1):
#                     _logger.info(f"Processing template {index}/{len(templates)} - ID: {template.id}, Name: {template.name}")
#                     try:
#                         # Check if there are variants
#                         # variants = self.env['product.product'].search([('product_tmpl_id', '=', template.id)])
#                         # _logger.info(f"Found {len(variants)} variants for template ID: {template.id}")
#                         # product_id = variants[0].id if len(variants) == 1 else template.id
#                         template._sync_with_salla("createProductFromOdoo", product_id=template.id)
#                         # _logger.info(f"Salla sync completed for template ID: {product_id}")
#                     except Exception as e:
#                         _logger.error(f"Error during Salla sync for template ID: {template.id}: {str(e)}")
#                         raise
#         else:
#             _logger.info("Skipping sync and update logging: No relevant fields changed or sync skipped via context")
#         _logger.info("Variant update process completed successfully")
#         return result

# حل المشكلة بعد الاستغناء عن self.env.cr.commit()

# import requests
# import logging
# from odoo import fields, models, api
# from datetime import datetime

# _logger = logging.getLogger(__name__)

# class TecfyProductTemplate(models.Model):
#     _inherit = "product.template"

#     def _sync_with_salla(self, endpoint, product_id):
#         _logger.info(f"Starting sync with Salla for product ID {self.id} using endpoint: {endpoint} and product_id: {product_id}")
#         if not self.exists():
#             _logger.error(f"Product ID {self.id} does not exist in Odoo")
#             return

#         product_variants = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
#         _logger.info(f"Found {len(product_variants)} variants for product template ID: {self.id} ,, product_id : {product_id}")

#         data = {
#             "productId": product_id,
#             "merchantId": int(self.env.user.company_id.tecfy_salla_merchant_id) if self.env.user.company_id.tecfy_salla_merchant_id else None,
#         }

#         _logger.info(f"Prepared data for Salla sync: {data}")
#         try:
#             _logger.info(f"Sending request to Salla API: https://salla.tecfy.co/api/salla/{endpoint}")
#             response = requests.post(
#                 f"https://salla.tecfy.co/api/salla/{endpoint}",
#                 json=data
#             )
#             response.raise_for_status()
#             try:
#                 response_content = response.json()
#             except ValueError as e:
#                 _logger.error(f"Error parsing JSON response: {response.text}, Error: {str(e)}")
#                 self.message_post(
#                     body=f"Failed to parse Salla API response on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Response: {response.text}",
#                     message_type='notification',
#                     subtype_id=self.env.ref('mail.mt_note').id
#                 )
#                 return

#             if not response_content.get('success', False):
#                 error_message = response_content.get('message', 'Unknown error occurred')
#                 _logger.error(f"Salla API error: {error_message}")
#                 self.message_post(
#                     body=f"Failed to sync with Salla on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. Error: {error_message}",
#                     message_type='notification',
#                     subtype_id=self.env.ref('mail.mt_note').id
#                 )
#             else:
#                 _logger.info(f"Salla API Response: {response_content}")
#                 self.message_post(
#                     body=f"Synchronized with Salla successfully on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
#                     message_type='notification',
#                     subtype_id=self.env.ref('mail.mt_note').id
#                 )
#         except requests.exceptions.RequestException as e:
#             _logger.error(f"Error syncing product with Salla: {e}")
#         except ValueError as e:
#             _logger.error(f"Error parsing JSON response: {e}")

#     @api.model
#     def create(self, vals):
#         _logger.info(f"Starting product creation with values: {vals}")
#         product = super(TecfyProductTemplate, self).create(vals)
#         _logger.info("Parent create method completed successfully")

#         company = self.env.company
#         if company.tecfy_product_add_to_salla:
#             def _sync_after_commit():
#                 try:
#                     _logger.info(f"[postcommit] Syncing product {product.id} with Salla after creation")
#                     product._sync_with_salla("createProductFromOdoo", product_id=product.id)
#                 except Exception as e:
#                     _logger.error(f"[postcommit] Error syncing product {product.id} after create: {str(e)}")

#             self.env.cr.postcommit.add(_sync_after_commit)

#         _logger.info("Product creation process completed successfully")
#         return product

#     def write(self, vals):
#         _logger.info(f"Starting product update for IDs {self.ids} with values: {vals}")
#         result = super(TecfyProductTemplate, self).write(vals)
#         _logger.info("Parent write method completed successfully")

#         synced_fields = [
#             'name', 'description_sale', 'description', 'list_price',
#             'standard_price', 'barcode', 'qty_available', 'type',
#             'attribute_line_ids','image_1920', 'image_1024', 'image_512', 'image_256', 'image_128'
#         ]

#         if 'skip_salla_sync' not in self.env.context and any(field in vals for field in synced_fields):
#             company = self.env.company
#             if company.tecfy_product_update_to_salla:
#                 def _sync_after_commit():
#                     for product in self:
#                         try:
#                             _logger.info(f"[postcommit] Syncing product {product.id} with Salla after update")
#                             product._sync_with_salla("createProductFromOdoo", product_id=product.id)
#                         except Exception as e:
#                             _logger.error(f"[postcommit] Error syncing product {product.id} after write: {str(e)}")

#                 self.env.cr.postcommit.add(_sync_after_commit)
#         else:
#             _logger.info("Skipping sync and update logging: No relevant fields changed or sync skipped via context")

#         _logger.info("Product update process completed successfully")
#         return result


# class TecfyProductProduct(models.Model):
#     _inherit = "product.product"

#     @api.depends('write_date', 'product_tmpl_id.write_date')
#     def _compute_write_date(self):
#         for record in self:
#             variant_write_date = record.write_date or self.env.cr.now()
#             template_write_date = record.product_tmpl_id.write_date or datetime(1970, 1, 1)
#             record.write_date = max(variant_write_date, template_write_date)

#     def write(self, vals):
#         _logger.info(f"Starting variant update for IDs {self.ids} with values: {vals}")
#         result = super(TecfyProductProduct, self).write(vals)
#         _logger.info("Parent write method completed successfully")

#         variant_synced_fields = [
#             'name', 'description' , 'categ_id','barcode', 'default_code', 'lst_price', 'standard_price',
#             'weight', 'volume'
#         ]
#         if 'skip_salla_sync' not in self.env.context and any(field in vals for field in variant_synced_fields):
#             templates = self.mapped('product_tmpl_id')
#             company = self.env.company
#             if company.tecfy_product_update_to_salla and templates:
#                 def _sync_after_commit():
#                     for template in templates:
#                         try:
#                             _logger.info(f"[postcommit] Syncing template {template.id} with Salla after variant update")
#                             template._sync_with_salla("createProductFromOdoo", product_id=template.id)
#                         except Exception as e:
#                             _logger.error(f"[postcommit] Error syncing template {template.id} after variant write: {str(e)}")

#                 self.env.cr.postcommit.add(_sync_after_commit)
#         else:
#             _logger.info("Skipping sync and update logging: No relevant fields changed or sync skipped via context")

#         _logger.info("Variant update process completed successfully")
#         return result
