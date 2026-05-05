/** @odoo-module */

import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useBus } from "@web/core/utils/hooks";

patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.pricelist_item_id = this.pricelist_item_id || null;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.pricelist_item_id = json.pricelist_item_id;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.pricelist_item_id = this.pricelist_item_id;
        return json;
    },

    set_unit_price(price) {
        const self = this;
        const product = this.get_product();

        // 1. إذا لم يكن هناك منتج، نفذ الكود الأصلي
        if (!product) {
            return super.set_unit_price(price);
        }

        // ============================================================
        // === FIX START: استثناء منتج الخصم من منطق قوائم الأسعار ===
        // ============================================================
        if (product.display_name === "Discount" || product.display_name.includes("on your order")) {
            // نمرر السعر مباشرة للكود الأصلي ونخرج فوراً دون تنفيذ لوجيك الموديل
            return super.set_unit_price(price);
        }
        // ============================================================
        // === FIX END ================================================
        // ============================================================

        // تحقق دائمًا من وجود الـ order قبل أي عملية
        if (!this.order || this.order.destroyed) {
            return super.set_unit_price(price);
        }

        if (this.pos?.mainScreen?.component?.name === 'TicketScreen') {
            return super.set_unit_price(price);
        }

        if (this?.quantity < 0) {
            return super.set_unit_price(price);
        }

        const pricelist = self.order.pricelist;
        if (!pricelist) {
            super.set_unit_price.call(self, price);
            return;
        }

        const pricelistItem = self._getPricelistItem(product, pricelist);
        if (!pricelistItem) {
            super.set_unit_price.call(self, price);
            self.price = product.get_price(self.order.pricelist, self.get_quantity(), 0, false);
            self.pricelist_item_id = null;
            if (self.order && typeof self.order.select_orderline === 'function') {
                self.order.select_orderline(self);
            }
            return;
        }

        // جلب البيانات من pricelist item
        return this._getPricelistItemData(pricelistItem.id).then((itemData) => {

            if (!self.order || self.order.destroyed) {
                self.pos.env.bus.trigger("tecfy_update_totals");
                return;
            }

            if (!itemData.enable_pricelist_qty_discount) {
                super.set_unit_price.call(self, price);
                self.price = (price !== undefined && price !== null)
                    ? price
                    : product.get_price(self.order.pricelist, 1, 0, false);
                self.pricelist_item_id = null;

                if (self.order && typeof self.order.select_orderline === 'function') {
                    self.order.select_orderline(self);
                }
                self.pos.env.bus.trigger("tecfy_update_totals");
                return;
            }

            if (!self.order || self.order.destroyed) {
                self.pos.env.bus.trigger("tecfy_update_totals");
                return;
            }

            if (itemData.quantity > 0) {
                super.set_unit_price.call(self, price);
                self.pricelist_item_id = pricelistItem.id;
                self.price = product.get_price(pricelist, self.get_quantity(), 0, false);
                if (self.order && typeof self.order.select_orderline === 'function') {
                    self.order.select_orderline(self);
                }
                self.pos.env.bus.trigger("tecfy_update_totals");
                return;
            }

            // الحالة الافتراضية
            super.set_unit_price.call(self, price);
            const defaultPricelistId = self.order.pos.config.pricelist_id?.[0] || null;
            const defaultPricelist = self.order.pos.pricelists.find(pl => pl.id === defaultPricelistId);

            self.price = product.get_price(defaultPricelist || pricelist, self.get_quantity(), 0, false);
            self.pricelist_item_id = null;

            if (self.order && typeof self.order.select_orderline === 'function') {
                self.order.select_orderline(self);
            }

            self.pos.env.bus.trigger("tecfy_update_totals");

        }).catch((err) => {
            console.warn("Discount check failed, falling back to normal price:", err);

            if (self.order && !self.order.destroyed) {
                try {
                    super.set_unit_price.call(self, price);
                    self.price = product.get_price(
                        self.order.pricelist || self.order.pos.config.pricelist_id,
                        self.get_quantity(),
                        0,
                        false
                    );
                    self.pricelist_item_id = null;

                    if (typeof self.order.select_orderline === 'function') {
                        self.order.select_orderline(self);
                    }
                } catch (e) {
                    console.error("Even fallback failed:", e);
                }
            }
            self.pos.env.bus.trigger("tecfy_update_totals");
            return; 
        });
    },

    _getPricelistItemData(itemId) {
        return this.pos.env.services.orm
            .call('product.pricelist.item', 'read', [[itemId], ['enable_pricelist_qty_discount', 'quantity']])
            .then(result => {
                return {
                    enable_pricelist_qty_discount: result[0]?.enable_pricelist_qty_discount || false,
                    quantity: result[0]?.quantity || 0
                };
            })
            .catch(error => {
                console.error('Error fetching pricelist item data:', error);
                return {
                    enable_pricelist_qty_discount: false,
                    quantity: 0
                };
            });
    },

    _getPricelistItem(product, pricelist) {
        const items = pricelist.items || [];

        let variantItem = null;
        let templateItem = null;
        let globalItem = null;

        for (const item of items) {
            if (item.product_id && item.product_id[0] === product.id) {
                variantItem = item;
            } else if (item.product_tmpl_id && item.product_tmpl_id[0] === product.product_tmpl_id) {
                templateItem = item;
            } else if (item.applied_on === '3_global') {
                globalItem = item;
            }
        }
        return variantItem || templateItem || globalItem || null;
    },
    
    // ... بقية الكود (can_be_merged_with) يبقى كما هو
    can_be_merged_with(other_line) {
        if (!other_line) return false;

        if (this.get_product().id !== other_line.get_product().id) {
            return false;
        }

        if (this.getNote() !== other_line.getNote()) {
            return false;
        }

        if (this.get_unit() && this.get_unit().id !== other_line.get_unit().id) {
            return false;
        }

        const thisTaxes = (this.get_product().taxes_id || []).map(t => t[0]).join(',');
        const otherTaxes = (other_line.get_product().taxes_id || []).map(t => t[0]).join(',');
        if (thisTaxes !== otherTaxes) {
            return false;
        }

        let hasSameAttributes =
            Object.keys(Object(other_line.attribute_value_ids)).length ===
            Object.keys(Object(this.attribute_value_ids)).length;
        if (hasSameAttributes && Object(this.attribute_value_ids)?.length) {
            hasSameAttributes = other_line.attribute_value_ids.every(
                (value, index) => value === this.attribute_value_ids[index]
            );
        }

        return (
            !this.skipChange &&
            this.is_pos_groupable() &&
            this.get_discount() === other_line.get_discount() &&
            !(
                this.product.tracking === "lot" &&
                (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)
            ) &&
            this.full_product_name === other_line.full_product_name &&
            other_line.get_customer_note() === this.get_customer_note() &&
            !this.refunded_orderline_id &&
            !this.isPartOfCombo() &&
            !other_line.isPartOfCombo() &&
            hasSameAttributes
        );
    }
});

patch(Order.prototype, {
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.lines = json.lines || [];
        return json;
    },
});

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        useBus(this.env.bus, "tecfy_update_totals", () => {
            this.render(true);
        });
    },
});