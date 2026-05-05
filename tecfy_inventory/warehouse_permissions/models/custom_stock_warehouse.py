from odoo import models, fields, api

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    admin_ids = fields.Many2many(
        'res.users',
        'stock_warehouse_admin_rel',
        'warehouse_id', 'user_id',
        string='Warehouse Admins',
        store =True,
    )
    user_ids = fields.Many2many(
        'res.users',
        'stock_warehouse_user_rel',
        'warehouse_id', 'user_id',
        string='Warehouse Users',
        store =True,
    )
    
    def write(self, vals):
        res = super(StockWarehouse, self).write(vals)
        if 'admin_ids' in vals or 'user_ids' in vals:
            self._update_security_groups()
        return res
    
    def _update_security_groups(self):
        """Update security groups when admin_ids or user_ids change"""
        try:
            warehouse_admin_group = self.env.ref('warehouse_permissions.group_warehouse_admin')
            warehouse_user_group = self.env.ref('warehouse_permissions.group_warehouse_user')
            
            for warehouse in self:
                # Add warehouse admins to the admin group
                for admin in warehouse.admin_ids:
                    if warehouse_admin_group not in admin.groups_id:
                        admin.groups_id = [(4, warehouse_admin_group.id)]
                
                # Add warehouse users to the user group (but not admin group)
                for user in warehouse.user_ids:
                    if warehouse_user_group not in user.groups_id:
                        user.groups_id = [(4, warehouse_user_group.id)]
                    # Remove from admin group if they're not in admin_ids
                    if user not in warehouse.admin_ids and warehouse_admin_group in user.groups_id:
                        user.groups_id = [(3, warehouse_admin_group.id)]
                        
        except Exception as e:
            # Log error but don't break the process
            pass
    
    @api.model
    def create(self, vals):
        warehouse = super(StockWarehouse, self).create(vals)
        if 'admin_ids' in vals or 'user_ids' in vals:
            warehouse._update_security_groups()
        return warehouse