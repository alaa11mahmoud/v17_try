/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";

patch(ClosePosPopup.prototype, {
    async confirm() {
        let total_cash = this.props.default_cash_details.amount;
        let cashDifference = this.getDifference(this.props.default_cash_details.id);
        console.log('cashDifference', cashDifference);
        let total_bank = this.props.other_payment_methods.filter(pm => pm.type === 'bank')[0].amount;
        let bankDifference = this.getDifference(this.props.other_payment_methods.filter(pm => pm.type === 'bank')[0].id);
        console.log('bankDifference', bankDifference);
        let pos_session_name = this.pos.pos_session.name;

        // Function to create and download a PDF
        const createPDFThenDowenloadIt = (cashDiff, bankDiff) => {
            // Calculate Counted values
            const cashCounted = total_cash + cashDiff;
            const bankCounted = total_bank + bankDiff;

            // Create a new jsPDF instance
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();

            // Set font and add title
            doc.setFont("helvetica", "normal");
            doc.setFontSize(18);
            doc.text(`Point of Sale Closing Report - ${pos_session_name}`, 20, 20);

            // Add date
            doc.setFontSize(12);
            doc.text(`Date: ${new Date().toLocaleString()}`, 20, 30);

            // Add table using autoTable
            doc.autoTable({
                startY: 40,
                head: [['Payment Method', 'Expected', 'Counted', 'Difference']],
                body: [
                    ['Cash', Number(total_cash.toFixed(3)), Number(cashCounted.toFixed(3)), Number(cashDiff.toFixed(3))],
                    ['Bank', Number(total_bank.toFixed(3)), Number(bankCounted.toFixed(3)), Number(bankDiff.toFixed(3))],
                ],
                styles: { fontSize: 10, cellPadding: 2 },
                headStyles: { fillColor: [200, 200, 200], textColor: [0, 0, 0] },
                margin: { top: 40 },
            });

            // Save the PDF
            doc.save(`POS_Closing_Difference ${pos_session_name}.pdf`);
        };

        const createAndDownloadPDF = (cashDiff, bankDiff) => {
            // Calculate Counted values
            const cashCounted = total_cash + cashDiff;
            const bankCounted = total_bank + bankDiff;

            // Create HTML content with a table
            const htmlContent = `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Point of Sale Closing Report ${pos_session_name}</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1 { font-size: 18px; }
                        p { font-size: 14px; }
                        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                    </style>
                </head>
                <body>
                    <h1>Point of Sale Closing Report : ${pos_session_name}</h1>
                    <p>Date: ${new Date().toLocaleString()}</p>
                    <table>
                        <tr>
                            <th>Payment Method</th>
                            <th>Expected</th>
                            <th>Counted</th>
                            <th>Difference</th>
                        </tr>
                        <tr>
                            <td>Cash</td>
                            <td>${Number(total_cash.toFixed(3))}</td>
                            <td>${Number(cashCounted.toFixed(3))}</td>
                            <td>${Number(cashDiff.toFixed(3))}</td>
                        </tr>
                        <tr>
                            <td>Bank</td>
                            <td>${Number(total_bank.toFixed(3))}</td>
                            <td>${Number(bankCounted.toFixed(3))}</td>
                            <td>${Number(bankDiff.toFixed(3))}</td>
                        </tr>
                    </table>
                </body>
                </html>
            `;

            // Create a data URL for the HTML content
            const dataUri = 'data:text/html;charset=utf-8,' + encodeURIComponent(htmlContent);

            // Create a temporary link to trigger download
            // const link = document.createElement('a');
            // link.setAttribute('href', dataUri);
            // link.setAttribute('download', 'POS_Closing_Difference.html');
            // document.body.appendChild(link);
            // link.click();
            // document.body.removeChild(link);
            createPDFThenDowenloadIt(cashDiff, bankDiff);

            // Trigger print dialog to allow saving as PDF
            const printWindow = window.open('', '_blank');
            printWindow.document.write(htmlContent);
            printWindow.document.close();
            printWindow.print();
        };

        // Load jsPDF and autoTable dynamically
        const loadJsPDF = () => {
            return new Promise((resolve, reject) => {
                if (window.jspdf) {
                    resolve();
                } else {
                    const script = document.createElement('script');
                    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
                    script.onload = () => {
                        const autoTableScript = document.createElement('script');
                        autoTableScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.23/jspdf.plugin.autotable.min.js';
                        autoTableScript.onload = resolve;
                        autoTableScript.onerror = reject;
                        document.head.appendChild(autoTableScript);
                    };
                    script.onerror = reject;
                    document.head.appendChild(script);
                }
            });
        };

        // Load jsPDF and create PDF


        if (!this.pos.config.cash_control || this.env.utils.floatIsZero(this.getMaxDifference())) {
            await this.closeSession();
            alert(`Cash Difference: ${Number(cashDifference.toFixed(3))}, Bank Difference: ${Number(bankDifference.toFixed(3))}`);
            await loadJsPDF().then(() => {
                createAndDownloadPDF(cashDifference, bankDifference);
            }).catch(err => {
                console.error('Failed to load jsPDF:', err);
                alert('Error generating PDF. Please try again.');
            });
            return;
        }

        if (this.hasUserAuthority()) {
            await this.closeSession();
            alert(`Cash Difference: ${Number(cashDifference.toFixed(3))}, Bank Difference: ${Number(bankDifference.toFixed(3))}`);
            await loadJsPDF().then(() => {
                createAndDownloadPDF(cashDifference, bankDifference);
            }).catch(err => {
                console.error('Failed to load jsPDF:', err);
                // alert('Error generating PDF. Please try again.');
            });
            return;
        }

        await this.popup.add(ConfirmPopup, {
            title: _t("Payments Difference"),
            body: _t(
                "The maximum difference allowed is %s.\nPlease contact your manager to accept the closing difference.",
                this.env.utils.formatCurrency(this.props.amount_authorized_diff)
            ),
            confirmText: _t("OK"),
        });
    },

    getInitialState() {
        const initialState = { notes: "", payments: {} };
        if (this.pos.config.cash_control) {
            initialState.payments[this.props.default_cash_details.id] = {
                counted: "0",
            };
        }
        this.props.other_payment_methods.forEach((pm) => {
            if (pm.type === "bank") {
                initialState.payments[pm.id] = {
                    counted: "0",
                };
            }
        });
        return initialState;
    }
});