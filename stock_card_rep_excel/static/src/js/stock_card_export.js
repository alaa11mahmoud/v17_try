/** @odoo-module **/

import { registry } from "@web/core/registry";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class StockCardExportItem extends Component {
    static template = "stock_card_rep_excel.StockCardExportItem";
    static components = { DropdownItem };

    setup() {
        this.actionService = useService("action");
    }

    async onClick() {
        // Trigger the server action with current view domain
        // This allows exporting all records matching the current filters
        await this.actionService.doAction("stock_card_rep_excel.action_server_stock_card_export_xlsx", {
            additionalContext: {
                active_domain: this.env.searchModel.domain,
            },
        });
    }
}

const cogMenuRegistry = registry.category("cogMenu");

cogMenuRegistry.add("stock-card-export-xlsx", {
    Component: StockCardExportItem,
    groupNumber: 20,
    isDisplayed: (env) => env.config.resModel === "stock.card.line" && env.config.viewType === "list",
}, { sequence: 10 });
