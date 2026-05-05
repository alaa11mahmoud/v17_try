/** @odoo-module **/
console.log('looooooooooooooood');
let discountPercentage;
let active_set_discount_price;
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { DiscountButton } from "@pos_discount/overrides/components/discount_button/discount_button";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { Orderline } from "@point_of_sale/app/store/models";

patch(DiscountButton.prototype, {
    async click() {
        let self = this;
        const { confirmed, payload } = await this.popup.add(NumberPopup, {
            title: _t("Discount Percentage"),
            startingValue: this.pos.config.discount_pc,
            isInputSelected: true,
        });
        if (confirmed) {
            const val = Math.max(0, Math.min(100, parseFloat(payload)));
            let maxDiscount = this.pos.config.discount_pc
            if (val > maxDiscount) {
                await this.popup.add(ErrorPopup, {
                    title: _t("Discount Percentage"),
                    body: _t(
                        `You cannot add a discount greater than the available discount. ${maxDiscount}`,
                    ),
                    // cancelText: _t("No"),
                    confirmText: _t("Ok"),
                });
                return
            }
            await self.apply_discount(val);
        }
    },
});



patch(PosStore.prototype, {
    async after_load_server_data() {
        await super.after_load_server_data();
        let removeOrderlinesRecursively = () => {
            let order = this.get_order()
            if (order.orderlines.length > 0) {
                const orderline = order.orderlines[0];
                order.removeOrderline(orderline);
                removeOrderlinesRecursively();
            }
        }
        removeOrderlinesRecursively()
    },

    // async push_single_order(order) {
    //     const result = await super.push_single_order(order);
    //     await this.update_product_quantities(order);
    //     return result;
    // },

    // async update_product_quantities(order) {
    //     const lines = order.get_orderlines();
    //     for (let line of lines) {
    //         const productId = line.product.id;
    //         const warehouseId = this.config.warehouse_id[0];
    //         const warehouseData = await this.orm.searchRead('stock.warehouse', [['id', '=', warehouseId]], ['lot_stock_id']);
    //         if (warehouseData && warehouseData.length > 0) {
    //             const locationId = warehouseData[0].lot_stock_id[0];
    //             const productInfo = await this.orm.searchRead('stock.quant', [['product_id', '=', productId], ['location_id', '=', locationId]], ['quantity']);
    //             if (productInfo && productInfo.length > 0) {
    //                 line.product.pos_stock_quantity = productInfo[0].quantity;
    //             }
    //         } else {
    //             console.warn('لم يتم العثور على بيانات المخزن.');
    //         }
    //     }
    // },

    async addProductFromUi(...args) {
        try {
            const productId = args[0].id;
            const product = this.db.get_product_by_id(productId);
            const quantity = product?.pos_stock_quantity
        } catch (error) {
            console.log('error', error);
        }
        await super.addProductFromUi(...args)
    },
    // async addProductToCurrentOrder(...args) {
    //     var type = this.config.stock_type
    //     if (args['0'].pos_stock_quantity <= 0) {
    //         await this.popup.add(ErrorPopup, {
    //             title: _t("Product Out of Stock"),
    //             body: _t(
    //                 `Product is out of stock`,
    //             ),
    //             // cancelText: _t("No"),
    //             confirmText: _t("Ok"),
    //         });
    //     }
    //     else {
    //         await super.addProductToCurrentOrder(...args)
    //     }
    // },
});



patch(Orderline.prototype, {
   async set_quantity(...args) {
        // تخطي الحسابات إذا كان العلم 'do not recompute unit price' موجوداً
        if (args[1] == 'do not recompute unit price') {
            const result = await super.set_quantity(...args)
            return result;
        }

        // دالة حساب الخصم (كما هي في الكود الأصلي)
        let calc_discount = (order_line_product, order_line_new_quantity, order_lines, hasDiscountLine, is_new_quantity) => {

            if (!hasDiscountLine) {
                discountPercentage = 0;
            }

            if (
                hasDiscountLine &&
                order_line_product.display_name != "Discount" &&
                order_lines?.length > 0
            ) {
                let totalAmount = 0;
                let totalDiscount = 0;
                let discount = 0;
                for (let line of order_lines) {
                    if (line.product.display_name !== "Discount") {
                        let p = line.get_unit_display_price();
                        let q;
                        if (is_new_quantity) {
                            if (order_line_product.display_name == line.product.display_name && discountPercentage) {
                                q = order_line_new_quantity;
                            } else {
                                q = line.get_quantity();
                            }
                        } else {
                            q = line.get_quantity();
                        }

                        // تأكد من أن الكمية رقم صحيح للعمليات الحسابية
                        if (q === "" || isNaN(q)) q = 0;
                        
                        totalAmount += p * q;
                    }
                    if (line.product.display_name == "Discount") {
                        totalDiscount = line.get_display_price();
                    }
                }
                
                // حساب نسبة الخصم إذا لم تكن موجودة
                if (!discountPercentage && is_new_quantity && totalAmount > 0) {
                    discountPercentage = Math.round(Math.abs((totalDiscount / totalAmount) * 100));
                }

                // تطبيق الخصم الجديد
                if (totalAmount > 0) {
                     discount = totalAmount * (discountPercentage / 100);
                     this.order.get_orderlines().forEach((line) => {
                         if (line.product.display_name === "Discount") {
                             active_set_discount_price = true
                             line.set_unit_price(-discount / 1.15);
                         }
                     });
                }
            }
        };

        const order_line_product = this.product;
        const order_line_new_quantity = args[0];
        const order_lines = this.order.get_orderlines();
        
        let hasDiscountLine = false;
        for (let line of order_lines) {
            if (line.product.display_name === "Discount") {
                hasDiscountLine = true;
                break;
            }
        }

        // منع تعديل كمية سطر الخصم يدوياً
        if ((order_line_product.display_name == "Discount" || order_line_product.display_name.includes("on your order")) && hasDiscountLine && order_line_new_quantity != "") {
            await this.pos.popup.add(ErrorPopup, {
                title: _t("Global Discount"),
                body: _t(`You cannot change discount quantity`),
                confirmText: _t("Ok"),
            });
            return;
        }

        // التحقق من أن الكمية عدد صحيح
        if (!Number.isInteger(Number(order_line_new_quantity)) && order_line_new_quantity !== "") {
            await this.pos.popup.add(ErrorPopup, {
                title: _t("Quantity Error"),
                body: _t(
                    `You cannot enter a decimal value for the quantity.`
                ),
                confirmText: _t("Ok"),
            });
            return;
        }

        // الحساب المسبق (للحفاظ على المنطق القديم)
        calc_discount(order_line_product, order_line_new_quantity, order_lines, hasDiscountLine, true);
        active_set_discount_price = false

        // --- تنفيذ التحديث الأساسي للكمية ---
        const result = await super.set_quantity(...args);

        // --- كود التعديل الجديد (بداية) ---
        // 1. جلب الخطوط الحالية بعد التحديث
        const currentLines = this.order.get_orderlines();
        
        // 2. البحث عن سطر الخصم
        const discountLine = currentLines.find(line => line.product.display_name === "Discount");
        
        // 3. التحقق مما إذا كان هناك أي منتجات عادية (غير الخصم) لها كمية أكبر من 0
        let hasActiveProducts = false;
        for (let line of currentLines) {
            if (line.product.display_name !== "Discount") {
                const qty = line.get_quantity();
                // نعتبر المنتج نشطاً إذا كانت كميته ليست فارغة وليست صفر
                if (qty !== "" && Number(qty) !== 0) {
                    hasActiveProducts = true;
                    break;
                }
            }
        }

        // 4. إذا لم توجد منتجات نشطة ووجد سطر خصم، قم بحذفه
        if (!hasActiveProducts && discountLine) {
            this.order.removeOrderline(discountLine);
            discountPercentage = 0; // تصفير نسبة الخصم
            return result; // الخروج لأننا حذفنا الخصم ولا داعي لإعادة حسابه
        }
        // --- كود التعديل الجديد (نهاية) ---


        // إعادة حساب قيمة الخصم بناءً على الكميات الجديدة (تحديث الخصم)
        const order_lines2 = this.order.get_orderlines();
        let hasDiscountLine2 = false;
        for (let line of order_lines2) {
            if (line.product.display_name === "Discount") {
                hasDiscountLine2 = true;
                break;
            }
        }
        
        // استدعاء الدالة لتحديث السعر
        calc_discount(this.product, args[0], order_lines2, hasDiscountLine2, false);
        active_set_discount_price = false
        
        return result;
    },
    async set_unit_price(...args) {
        const order_line_product = this.product;
        const order_lines = this.order?.get_orderlines() ?? [];
        let hasDiscountLine = false;
        for (let line of order_lines) {
            if (line.product.display_name === "Discount") {
                hasDiscountLine = true;
                break;
            }
        }
        if ((order_line_product.display_name == "Discount" || order_line_product.display_name.includes("on your order")) && !active_set_discount_price && hasDiscountLine) {
            await this.pos.popup.add(ErrorPopup, {
                title: _t("Global Discount"),
                body: _t(`You cannot change discount price`),
                confirmText: _t("Ok"),
            });
            return;
        }
        const result = await super.set_unit_price(...args);
        return result;
    },
    async set_discount(...args) {
        const order_line_product = this.product;
        const order_lines = this.order?.get_orderlines() ?? [];
        let hasDiscountLine = false;
        for (let line of order_lines) {
            if (line.product.display_name === "Discount") {
                hasDiscountLine = true;
                break;
            }
        }
        if ((order_line_product.display_name == "Discount" || order_line_product.display_name.includes("on your order")) && !active_set_discount_price && hasDiscountLine) {
            await this.pos.popup.add(ErrorPopup, {
                title: _t("Global Discount"),
                body: _t(`You cannot change discount percentage`),
                confirmText: _t("Ok"),
            });
            return;
        }
        const result = await super.set_discount(...args);
        return result;
    },
});