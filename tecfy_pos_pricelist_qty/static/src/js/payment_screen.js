/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        for (const line of order.get_orderlines()) {
            if (line.pricelist_item_id) {
                // جلب البيانات من pricelist item (enable_pricelist_qty_discount و quantity معاً)
                const itemData = await this._getPricelistItemData(line.pricelist_item_id);
                
                if (itemData.enable_pricelist_qty_discount) {
                    const product = line.get_product();

                    if (itemData.quantity > 0 && line.get_quantity() > itemData.quantity) {
                        this.popup.add(ErrorPopup, {
                            title: _t("Insufficient Quantity"),
                            body: _t(
                                "Cannot sell more than available quantity (%s) for product %s",
                                itemData.quantity,
                                product.display_name
                            ),
                        });
                        return;
                    }
                }
            }
        }

        return await super.validateOrder(...arguments);
    },

    // دالة واحدة لجلب كل البيانات المطلوبة من pricelist item
    async _getPricelistItemData(itemId) {
        try {
            const result = await this.env.services.orm.call(
                'product.pricelist.item',
                'read',
                [[itemId], ['enable_pricelist_qty_discount', 'quantity']]
            );
            return {
                enable_pricelist_qty_discount: result[0]?.enable_pricelist_qty_discount || false,
                quantity: result[0]?.quantity || 0
            };
        } catch (error) {
            console.error('Error fetching pricelist item data:', error);
            return {
                enable_pricelist_qty_discount: false,
                quantity: 0
            };
        }
    },

    _findPricelistItem(pricelist, itemId) {
        if (!pricelist || !pricelist.items) return null;
        return pricelist.items.find(item => item.id === itemId);
    },
});