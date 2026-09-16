import { onMounted, onUnmounted, watch } from 'vue';
import { createResource } from 'frappe-ui';
import { createToast } from '@/utils';
import emitter from '@/utils/emitter';
import { useInvoiceStore } from '@/stores/pos';
import { usePosProfileStore } from '@/stores/posProfile';

// Server-side totals for the open sale, owned by the POS page.
//
// This used to live in ItemSelector and was only triggered by cart line
// components. On mobile the cart lines are not mounted while browsing items,
// so totals never updated there, and each ItemSelector remount added another
// set of emitter listeners. Call this once, from the always-mounted page.
export function useInvoiceRecalc() {
    const invoiceStore = useInvoiceStore();
    const store = usePosProfileStore();

    const remove_invoice = (include_customer = false) => {
        invoiceStore.unmountAndRefresh(include_customer);
    };

    // Totals are recalculated on every cart edit (scan, qty, serial, batch,
    // discount). If that call is failing, every edit used to raise another
    // "Internal Server Error" toast. Show one explanatory message, then stay quiet
    // while the same failure keeps repeating.
    const RECALC_ERROR_COOLDOWN_MS = 60 * 1000;
    let lastRecalcError = { key: '', at: 0 };

    const notifyRecalcError = (error) => {
        let serverMessage = Array.isArray(error?.messages) ? error.messages[0] : error?.messages;
        // frappe-ui substitutes this literal when the server crashed without a
        // message; it tells the cashier nothing.
        if (serverMessage === 'Internal Server Error') serverMessage = '';
        const key = serverMessage || error?.exc_type || error?.message || 'unknown';
        const now = Date.now();
        if (key === lastRecalcError.key && now - lastRecalcError.at < RECALC_ERROR_COOLDOWN_MS) {
            lastRecalcError.at = now;
            return;
        }
        lastRecalcError = { key, at: now };

        createToast({
            title: 'Totals could not be updated',
            // A validation message from the server is actionable; a crash is not,
            // so say what it means for the cashier instead of echoing the status.
            message: serverMessage
                || 'The server failed to calculate this invoice. Items are kept, but totals and taxes may be wrong. Ask your administrator to check the server error log.',
            icon: 'alert-triangle',
            iconClasses: 'bg-surface-red-5 text-ink-white rounded-md p-px',
            position: 'top-center',
            timeout: 8,
        });
    };

    // Fields a totals recalculation must never overwrite: identity and document
    // state belong to the saved draft, and items are merged separately below.
    const RECALC_SKIP_KEYS = new Set([
        'items', 'name', 'docstatus', 'doctype', 'status', 'owner', 'creation',
        'modified', 'modified_by', 'amended_from', '__islocal', '__unsaved',
    ]);

    const runDocMethod = createResource({
        url: 'ant_pos.ant_pos.api.sales_invoice.calculate_invoice_item_taxes',
        method: 'POST',
        auto: false,
        debounce: 500,
        makeParams(params) {
            return {
                ...params
            };   
        },
        transform(data){
            if (data && data.items && data.items.length > 0) {
                data.items.forEach(item => {
                    if (item.serial_no) {
                        item.selected_serial_no = item.serial_no.trim().split('\n').map(serial => ({
                            label: serial,
                            value: serial
                        }));
                        
                    }
                    if (item.batch_no) {
                        
                        item.selected_batch_no = {
                            label: item.batch_no,
                            value: item.batch_no
                        };
                    } else {
                        item.selected_batch_no = null;
                    }
                    
                });
                
            }
            return data
        },

        onSuccess(data){
            // A recalculation that lands after Pay is stale: the draft is already
            // saved and is the source of truth. Applying it used to reset
            // docstatus/name, which closed the payment panel and detached the
            // screen from the saved draft (the next Pay then created a duplicate).
            if (invoiceStore.invoice.docstatus) return;

            for (const key in data) {
                if (RECALC_SKIP_KEYS.has(key)) continue;

                const existingValue = invoiceStore.invoice[key];
                const newValue = data[key];

                // Check for changes or new keys
                if (JSON.stringify(existingValue) !== JSON.stringify(newValue)) {
                    invoiceStore.invoice[key] = newValue;
                }
            }
            data.items.forEach(n => {
                const e = invoiceStore.items.find(b => b.custom_id === n.custom_id);
                if (!e) return;
                for (const k in n) {
                    if (k !== 'custom_id' && e[k] !== n[k]) {
                        if (JSON.stringify(e[k]) !== JSON.stringify(n[k])) {
                            e[k] = n[k];
                        }
                    }
                }
            });
        },
        onError(error) {
            notifyRecalcError(error);
        }
    });


    const calculateAmountTotal = async () => {
        if (invoiceStore.items.length === 0 ) {
            remove_invoice(false);
            return;
        }
        await runDocMethod.fetch({doc: JSON.stringify({
            ...invoiceStore.invoice,
            doctype: 'Sales Invoice',
            is_pos: invoiceStore.invoice.is_return ? invoiceStore.invoice.is_pos : 1,
            pos_profile: store.posProfileData.name,
            company: store.posProfileData.company,
            selling_price_list: store.posProfileData.selling_price_list,
            items: invoiceStore.items,
            customer: invoiceStore.invoiceCustomer?.name,
            update_stock: 1,
            additional_discount_percentage: invoiceStore.invoice._additional_discount_percentage ? Number(invoiceStore.invoice._additional_discount_percentage) : 0 ,
            discount_amount: invoiceStore.invoice._discount_amount ? Number(invoiceStore.invoice._discount_amount) : 0,
            base_total: invoiceStore.invoice.base_total || 0,
            custom_ant_opening: store.openingShift.name,
            apply_discount_on: store.posProfileData.apply_discount_on,
        })});
    }



    // Cart lines trigger a recalculation when mounted, but lines added or changed
    // while the cart is not on screen (mobile item grid) need one too. The
    // resource is debounced, so the overlap with the line components is free.
    watch(
        () => invoiceStore.items
            .map((l) => [l.item_code, l.qty, l.rate, l.uom, l.batch_no, l.discount_percentage].join('|'))
            .join(';'),
        (now, before) => {
            // An empty cart is reset by whoever emptied it; recalculating here
            // would refetch the blank invoice a second time.
            if (!now || now === before || invoiceStore.invoice.docstatus) return;
            calculateAmountTotal();
        }
    );

    const onCalcTotal = () => calculateAmountTotal();
    const onRemoveInvoice = (include_customer) => remove_invoice(include_customer);

    onMounted(() => {
        emitter.on('calctotal', onCalcTotal);
        emitter.on('remove_invoice', onRemoveInvoice);
    });

    onUnmounted(() => {
        emitter.off('calctotal', onCalcTotal);
        emitter.off('remove_invoice', onRemoveInvoice);
    });

    return { calculateAmountTotal };
}
