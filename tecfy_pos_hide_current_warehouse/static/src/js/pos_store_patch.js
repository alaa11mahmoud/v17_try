/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        if (this.config && this.config.picking_type_id) {

            let warehouse_id = this.config.picking_type_id[0];
            let warehouseData = await this.orm.call('stock.picking.type', 'web_read', [warehouse_id], {
                specification: {
                    "name": {},
                    "code": {},
                    "active": {},
                    "company_id": {
                        "fields": {
                            "display_name": {}
                        }
                    },
                    "hide_reservation_method": {},
                    "show_picking_type": {},
                    "sequence_id": {
                        "fields": {
                            "display_name": {}
                        }
                    },
                    "sequence_code": {},
                    "warehouse_id": {
                        "fields": {
                            "display_name": {}
                        }
                    },
                    "reservation_method": {},
                    "reservation_days_before": {},
                    "reservation_days_before_priority": {},
                    "return_picking_type_id": {
                        "fields": {
                            "display_name": {}
                        }
                    },
                    "default_location_return_id": {
                        "fields": {
                            "display_name": {}
                        }
                    },
                    "create_backorder": {},
                    "use_create_lots": {},
                    "use_existing_lots": {},
                    "default_location_src_id": {
                        "fields": {
                            "display_name": {}
                        }
                    },
                    "default_location_dest_id": {
                        "fields": {
                            "display_name": {}
                        }
                    },
                    "auto_print_delivery_slip": {},
                    "auto_print_return_slip": {},
                    "auto_print_product_labels": {},
                    "product_label_format": {},
                    "auto_print_lot_labels": {},
                    "lot_label_format": {},
                    "display_name": {}
                }
            });
            console.log(warehouseData);
            console.log(warehouse_id);
            this.config.warehouse_id = warehouseData[0].warehouse_id.id;
            this.config.warehouse_name = warehouseData[0].warehouse_id.display_name;
        }
    }
});
