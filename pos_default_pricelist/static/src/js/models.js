/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        let pricelist_id = this?.pos?.config?.pricelist_select_id[0] || null;
        if (pricelist_id) {
            const defaultPricelist = this.pos.pricelists.find(
                pl => pl.id === pricelist_id
            );
            if (defaultPricelist) {
                this.set_pricelist(defaultPricelist);
            }
        };
    },
     set_pricelist(pricelist) {

        var self = this;
        this.pricelist = pricelist;

        let pricelist_id = this?.pos?.config?.pricelist_select_id[0] || null;
        if (pricelist_id) {
            const defaultPricelist = this.pos.pricelists.find(
                pl => pl.id === pricelist_id
            );
            if (defaultPricelist) {
                this.pricelist = defaultPricelist;
            }
        };

        const orderlines = this.get_orderlines();

        const lines_to_recompute = orderlines.filter(
            (line) =>
                line.price_type === "original" && !(line.comboLines?.length || line.comboParent)
        );
        lines_to_recompute.forEach((line) => {
            line.set_unit_price(
                line.product.get_price(self.pricelist, line.get_quantity(), line.get_price_extra())
            );
            self.fix_tax_included_price(line);
        });
        const combo_parent_lines = orderlines.filter(
            (line) => line.price_type === "original" && line.comboLines?.length
        );
        const attributes_prices = {};
        combo_parent_lines.forEach((parentLine) => {
            attributes_prices[parentLine.id] = this.compute_child_lines(
                parentLine.product,
                parentLine.comboLines.map((childLine) => {
                    const comboLineCopy = { ...childLine.comboLine };
                    if (childLine.attribute_value_ids) {
                        comboLineCopy.configuration = {
                            attribute_value_ids: childLine.attribute_value_ids,
                        };
                    }
                    return comboLineCopy;
                }),
                pricelist
            );
        });
        const combo_children_lines = orderlines.filter(
            (line) => line.price_type === "original" && line.comboParent
        );
        combo_children_lines.forEach((line) => {
            line.set_unit_price(
                attributes_prices[line.comboParent.id].find(
                    (item) => item.comboLine.id === line.comboLine.id
                ).price
            );
            self.fix_tax_included_price(line);
        });
    }
});