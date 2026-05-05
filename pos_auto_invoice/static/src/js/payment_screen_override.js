/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        console.log('🔧 POS Auto Invoice: PaymentScreen setup() called');
        super.setup();

        if (this.currentOrder) {
            console.log('📋 Current order before auto-invoice:', this.currentOrder.to_invoice);
            this.currentOrder.set_to_invoice(true);
            console.log('✅ Set to_invoice to true:', this.currentOrder.to_invoice);
        } else {
            console.log('❌ No current order found in setup');
        }

        onMounted(() => {
            console.log('🎯 PaymentScreen mounted - checking invoice button');
            const invoiceButton = document.querySelector('.js_invoice');
            if (invoiceButton && !invoiceButton.classList.contains('highlight')) {
                invoiceButton.click();
                console.log('✅ Clicked invoice button');
            } else if (invoiceButton) {
                console.log('ℹ️ Invoice button already checked');
            } else {
                console.log('❌ Invoice button not found');
            }
        });
    },

    toggleIsToInvoice() {
        console.log('🔄 toggleIsToInvoice called, to_invoice before:', this.currentOrder?.to_invoice);
        super.toggleIsToInvoice();
        if (this.currentOrder) {
            this.currentOrder.set_to_invoice(true);
            console.log('✅ Forced to_invoice = true:', this.currentOrder.to_invoice);
        }
    },

    shouldDownloadInvoice() {
        console.log('🖨️ shouldDownloadInvoice overridden to return false');
        return false;
    }
});
