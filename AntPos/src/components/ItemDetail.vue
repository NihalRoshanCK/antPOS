<template>
    <section class="flex-1 flex flex-col min-w-0 min-h-0 bg-white">

        <CustomerBar
            v-model:customer="invoiceStore.invoiceCustomer"
            @create="loadComponent('CustomerForm')"
        />

        <!-- Return mode is destructive and easy to miss; say so plainly. -->
        <p v-if="invoiceStore.invoice.is_return"
           class="shrink-0 bg-amber-50 border-b border-amber-200 text-pos-warn text-[13px] px-4 py-2">
            Return &mdash; quantities are negative and this will credit the customer.
        </p>

        <!-- Cart column header. Desktop only: on mobile each line is a card. -->
        <div class="hidden lg:grid shrink-0 grid-cols-[1fr_84px_96px_112px_32px] gap-3 px-4 py-2
                    border-b border-pos-line text-[11px] font-semibold text-pos-ink3">
            <div>Item</div>
            <div class="text-right">Qty</div>
            <div class="text-right">Rate</div>
            <div class="text-right">Amount</div>
            <div><span class="sr-only">Remove</span></div>
        </div>

        <div class="flex-1 overflow-y-auto pos-scroll min-h-0"
             :class="invoiceStore.items.length ? 'lg:bg-white bg-pos-page' : ''">
            <div v-if="!invoiceStore.items.length" class="px-6 py-16 text-center">
                <p class="text-[14px] text-pos-ink2">No items yet</p>
                <p class="text-[13px] text-pos-ink3 mt-1">
                    {{ invoiceStore.invoiceCustomer?.name ? 'Scan a barcode to start the sale.' : 'Choose a customer, then scan a barcode.' }}
                </p>
            </div>

            <div v-else class="lg:space-y-0 space-y-2 lg:p-0 p-3">
                <Item
                    v-for="(item, key) in invoiceStore.items"
                    :key="item.custom_id"
                    :items="item"
                    :index="key"
                />
            </div>
        </div>

        <!-- The only total-level field the cashier edits. Kept adjacent to the
             readout so cause and effect are visible together. -->
        <div v-if="invoiceStore.items.length && store.posProfileData?.allow_discount_change"
             class="shrink-0 border-t border-pos-line bg-white px-4 py-2 flex items-center gap-3">
            <label for="pos-discount" class="text-[12px] text-pos-ink2 shrink-0">
                {{ usePercentDiscount ? 'Discount %' : `Discount (${store.posProfileData?.currency || ''})` }}
            </label>
            <input
                id="pos-discount"
                v-if="usePercentDiscount"
                v-model="invoiceStore.invoice._additional_discount_percentage"
                type="number"
                inputmode="decimal"
                placeholder="0"
                class="num ml-auto w-28 h-9 px-2.5 rounded-md bg-pos-page border border-pos-line
                       text-[14px] text-right focus:outline-none focus:border-pos-ink focus:bg-white"
            />
            <input
                id="pos-discount"
                v-else
                v-model="invoiceStore.invoice._discount_amount"
                type="number"
                inputmode="decimal"
                placeholder="0.00"
                class="num ml-auto w-28 h-9 px-2.5 rounded-md bg-pos-page border border-pos-line
                       text-[14px] text-right focus:outline-none focus:border-pos-ink focus:bg-white"
            />
        </div>

        <TotalsReadout />

        <!-- Actions. Pay is the widest target and sits furthest right (or, on
             mobile, fills the thumb zone). -->
        <div class="shrink-0 bg-white border-t border-pos-line p-3
                    flex items-center gap-2 overflow-x-auto pos-scroll"
             style="padding-bottom: calc(0.75rem + env(safe-area-inset-bottom))">

            <Button variant="outline" theme="gray" class="!h-12 !px-4 shrink-0"
                    @click="loadComponent('Held')">
                Held
            </Button>
            <Button variant="outline" theme="gray" class="!h-12 !px-4 shrink-0 !text-pos-ret"
                    @click="loadComponent('Return')">
                Return
            </Button>

            <div class="ml-auto flex items-center gap-2 shrink-0">
                <Button
                    v-if="permissionStore.salesInvoiceCanCreate"
                    variant="outline" theme="gray" class="!h-12 !px-4"
                    @click="sales_invoice.fetch({ action: 'Save', status: 'save_new' })"
                >
                    Hold this sale
                </Button>
                <Button
                    v-if="permissionStore.salesInvoiceCanPrint && permissionStore.salesInvoiceCanCreate"
                    variant="outline" theme="gray" class="!h-12 !px-4 hidden sm:inline-flex"
                    @click="sales_invoice.fetch({ action: 'Save', status: 'print' })"
                >
                    Save &amp; print
                </Button>
                <button
                    v-if="permissionStore.salesInvoiceCanSubmit"
                    type="button"
                    class="h-12 px-6 lg:px-7 rounded-lg bg-pos-pay hover:bg-pos-pay-hover text-white
                           text-[15px] font-semibold flex items-baseline gap-2
                           focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-pos-pay
                           disabled:opacity-40 disabled:cursor-not-allowed"
                    :disabled="!invoiceStore.items.length"
                    @click="sales_invoice.fetch({ action: 'Save', status: 'pay' })"
                >
                    Pay
                    <span class="num text-[17px]">{{ payableTotal }}</span>
                </button>
            </div>
        </div>
    </section>
</template>

<script setup>
import { Button, createResource, debounce } from 'frappe-ui';
import { inject, watch, computed } from 'vue';
import CustomerBar from '@/components/pos/CustomerBar.vue';
import TotalsReadout from '@/components/pos/TotalsReadout.vue';
import { createToast, showToast } from '@/utils';
import { usePosProfileStore } from '@/stores/posProfile';
import { usePermissionStore } from '@/stores/permission';
import { useInvoiceStore } from '@/stores/pos';
import emitter from '@/utils/emitter'; 
import Item from '@/components/Item.vue';

const store = usePosProfileStore();
const permissionStore = usePermissionStore();
const invoiceStore = useInvoiceStore()
const { loadComponent } = inject('dynamicComponent');
const baseurl = createResource({url: 'ant_pos.ant_pos.utils.get_domain_url'});
let status = '';
let sales_invoice = createResource({
    url: 'frappe.desk.form.save.savedocs',
    makeParams(params) {
        invoiceStore.items.forEach((item) => {                
            if (item.has_serial_no && item.selected_serial_no.length !== item.qty) {
                createToast({
                    title: 'error',
                    message: 'Serial number is required',
                    iconClasses: 'bg-surface-red-5 text-ink-white rounded-md p-px',
                    position: 'top-center',
                    timeout: 5,
                });
            }
        });
        status = params.status
        return {
            doc: JSON.stringify({
                ...invoiceStore.invoice,
                doctype: 'Sales Invoice',
                is_pos: invoiceStore.invoice.is_return ? invoiceStore.invoice.is_pos : 1,
                pos_profile: store.posProfileData.name,
                company: store.posProfileData.company,
                conversion_rate: 1,
                selling_price_list: store.posProfileData.selling_price_list,
                items: invoiceStore.items,
                customer: invoiceStore.invoiceCustomer?.name,
                update_stock: 1,
                additional_discount_percentage: Number(invoiceStore.invoice._additional_discount_percentage) || 0,
                discount_amount: Number(invoiceStore.invoice._discount_amount) || 0,
                base_total: invoiceStore.invoice.base_total && invoiceStore.invoice.base_total,
                custom_ant_opening: store.openingShift.name,
                apply_discount_on: store.posProfileData.apply_discount_on,
                payments:getPayments(),
                advances:getAdvances()
            }),
            action:params.action,
        };
    },
    async onSuccess (data) {
        if ( status == 'pay'){
            invoiceStore.invoice = { ...data.docs[0] ,docstatus:1 }
            return

        }else if (status == 'print'){
            await baseurl.fetch()
            window.open(
                `${baseurl.data}/printview?doctype=Sales+Invoice&name=${
                    data.docs[0].name
                }&format=${encodeURIComponent(store.posProfileData.print_format)}&trigger_print=1&no_letterhead=${store.posProfileData.letter_head ? 1 :0 }
                &letterhead=${store.posProfileData.letter_head}`,
                "_blank"
            );
        }
        showToast('success', 'Sales Invoice Drafted Successfully')
        emitter.emit('remove_invoice', true);
    },
    onError(error) {
        createToast({
            title: 'error',
            message: Array.isArray(error?.messages) ? error.messages[0] : error?.messages || error || 'An error occurred',
            icon: 'x-circle',
            iconClasses: 'bg-surface-red-5 text-ink-white rounded-md p-px',
            position: 'top-center',
            timeout: 5,
        });
    },
});
   
const getPayments = () => {
    const total = invoiceStore.invoice.is_return ? -Math.abs(invoiceStore.invoice.rounded_total) : invoiceStore.invoice.rounded_total;
    const payments = invoiceStore.invoice.payments.map(p => {
        const amount = p.default ? total : 0;
        return {
            ...p,
            amount,
            base_amount: amount
        };
    });
    return payments;
};

const getAdvances = () => {
    if (!invoiceStore.invoice.advances) return [];
    if (invoiceStore.invoice.is_return) return [];
    return invoiceStore.invoice.advances;
};

const calculateDiscount = () => {
    let amount = store.posProfileData?.apply_discount_on === 'Grand Total' ? invoiceStore.invoice.base_grand_total : invoiceStore.invoice.base_net_total;

    if (store.posProfileData?.custom_use_percentage_discount) {
        invoiceStore.invoice._discount_amount= (( amount + invoiceStore.invoice?.discount_amount ) * 100) / invoiceStore.invoice._additional_discount_percentage;
    } else {
        invoiceStore.invoice._additional_discount_percentage = invoiceStore.invoice._discount_amount * (100 / ( amount + invoiceStore.invoice?.discount_amount ));
    }
};

const debouncedDiscount = debounce(calculateDiscount, 300);

const usePercentDiscount = computed(
    () => Boolean(store.posProfileData?.custom_use_percentage_discount)
);

const payableTotal = computed(() => {
    const invoice = invoiceStore.invoice || {};
    return Number(invoice.rounded_total || invoice.grand_total || 0).toFixed(2);
});

watch(
    () => invoiceStore.invoice._discount_amount,
    (newVal,oldVal) => {
        if (!store.posProfileData?.custom_use_percentage_discount && newVal !== oldVal) {
            calculateDiscount();
            emitter.emit('calctotal');
        }
    },
    { flush: 'post' }
);

watch(
  [() => invoiceStore.invoice.grand_total, () => invoiceStore.invoice.net_total],
  (newValues, oldValues) => {
    const [newGrand, newNet] = newValues;
    const [oldGrand, oldNet] = oldValues;

    if (newGrand !== oldGrand || newNet !== oldNet) {
      debouncedDiscount();
    }
  }
);


</script>
