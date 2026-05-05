/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        
        // Debug: طباعة بيانات pricelist
        if (this.pricelists && this.pricelists.length > 0) {
            console.log('=== Tecfy POS Debug ===');
            console.log('Pricelists loaded:', this.pricelists.length);
            
            this.pricelists.forEach(pricelist => {
                if (pricelist.items && pricelist.items.length > 0) {
                    console.log(`Pricelist: ${pricelist.name}`);
                    console.log('Items:', pricelist.items);
                    
                    pricelist.items.forEach(item => {
                        console.log(`  Item ID: ${item.id}, Quantity: ${item.quantity}`);
                    });
                }
            });
            console.log('======================');
        }
    },
});