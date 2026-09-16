<template>
    <section
        :class="[
            'flex-1 flex flex-col min-w-0 min-h-0 bg-surface-white',
            compact ? '' : 'rounded-xl border border-outline-gray-1 shadow-sm overflow-hidden',
        ]"
    >
        <CustomerBar
            v-model:customer="invoiceStore.invoiceCustomer"
            @create="loadComponent('CustomerForm')"
        />

        <p v-if="invoiceStore.invoice.is_return"
           class="shrink-0 border-b border-outline-amber-1 bg-surface-amber-1 px-4 py-2 text-sm text-ink-amber-3">
            Return: quantities are negative and the customer will be credited.
        </p>

        <div class="hidden lg:grid shrink-0 grid-cols-[1fr_84px_96px_112px_32px] gap-3 px-4 py-2
                    border-b border-outline-gray-1 bg-surface-gray-1 text-sm font-medium text-ink-gray-5">
            <div>Item</div>
            <div class="text-right">Qty</div>
            <div class="text-right">Rate</div>
            <div class="text-right">Amount</div>
            <div><span class="sr-only">Remove</span></div>
        </div>

        <div class="flex-1 overflow-y-auto pos-scroll min-h-0"
             :class="compact && invoiceStore.items.length ? 'bg-surface-gray-1' : ''">
            <div v-if="!invoiceStore.items.length" class="flex h-full flex-col items-center justify-center px-6 py-12 text-center">
                <div class="grid h-12 w-12 place-items-center rounded-full bg-surface-gray-2 text-ink-gray-5">
                    <FeatherIcon name="shopping-cart" class="h-5 w-5" />
                </div>
                <p class="mt-3 text-base font-medium text-ink-gray-8">Cart is empty</p>
                <p class="mt-1 text-sm text-ink-gray-5">
                    {{ invoiceStore.invoiceCustomer?.name ? 'Scan a barcode to add the first item.' : 'Choose a customer, then scan a barcode.' }}
                </p>
            </div>

            <div v-else :class="compact ? 'space-y-2 p-3' : ''">
                <!-- inert while paying: edits here would not reach the saved
                     draft, so the list would disagree with the invoice. -->
                <Item
                    v-for="(item, key) in invoiceStore.items"
                    :key="item.custom_id"
                    :items="item"
                    :index="key"
                    :inert="paying"
                    :class="paying ? 'opacity-70' : ''"
                />
            </div>
        </div>

        <footer class="shrink-0 border-t border-outline-gray-1 bg-surface-white"
                style="padding-bottom: env(safe-area-inset-bottom)">
            <div class="space-y-3 px-4 pt-3 pb-3">
                <div v-if="!paying && invoiceStore.items.length && store.posProfileData?.allow_discount_change"
                     class="flex items-center gap-3">
                    <label for="pos-discount" class="text-sm text-ink-gray-6">
                        {{ usePercentDiscount ? 'Additional discount (%)' : `Additional discount (${store.posProfileData?.currency || ''})` }}
                    </label>
                    <input
                        id="pos-discount"
                        v-if="usePercentDiscount"
                        v-model="invoiceStore.invoice._additional_discount_percentage"
                        type="number" inputmode="decimal" placeholder="0"
                        class="pos-input num ml-auto w-28 text-right"
                    />
                    <input
                        id="pos-discount"
                        v-else
                        v-model="invoiceStore.invoice._discount_amount"
                        type="number" inputmode="decimal" placeholder="0.00"
                        class="pos-input num ml-auto w-28 text-right"
                    />
                </div>

                <TotalsReadout />
            </div>

            <p v-if="paying" class="border-t border-outline-gray-1 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">
                Taking payment. Use <span class="font-medium text-ink-gray-8">Back to cart</span> to change items.
            </p>

            <!-- Mobile: four equal secondary actions, Pay full width in the thumb zone. -->
            <div v-else-if="compact" class="space-y-2 border-t border-outline-gray-1 bg-surface-gray-1 px-3 py-3">
                <div class="grid grid-cols-4 gap-2">
                    <button v-for="action in mobileActions" :key="action.label" type="button"
                        class="flex h-14 flex-col items-center justify-center gap-1 rounded-md text-xs font-medium
                               focus:outline-none focus-visible:ring focus-visible:ring-outline-gray-3
                               disabled:cursor-not-allowed disabled:opacity-50"
                        :class="action.class"
                        :disabled="action.disabled"
                        @click="action.run()">
                        <FeatherIcon :name="action.icon" class="h-4 w-4" />
                        {{ action.label }}
                    </button>
                </div>
                <button
                    v-if="permissionStore.salesInvoiceCanSubmit"
                    type="button"
                    class="flex h-12 w-full items-center justify-center gap-2 rounded-md text-lg font-semibold
                           focus:outline-none focus-visible:ring focus-visible:ring-outline-green-2 disabled:cursor-not-allowed"
                    :class="invoiceStore.items.length
                        ? 'bg-surface-green-3 text-ink-white active:bg-green-800'
                        : 'bg-surface-gray-2 text-ink-gray-4'"
                    :disabled="!invoiceStore.items.length"
                    @click="sales_invoice.fetch({ action: 'Save', status: 'pay' })"
                >
                    Pay <span class="num">{{ payableTotal }}</span>
                </button>
            </div>

            <div v-else class="flex items-center gap-2 border-t border-outline-gray-1 bg-surface-gray-1 px-3 py-3">
                <Button variant="subtle" theme="blue" size="lg" @click="loadComponent('Held')">
                    <template #prefix><FeatherIcon name="clock" class="h-4 w-4" /></template>
                    Held
                </Button>
                <Button variant="subtle" theme="red" size="lg" @click="loadComponent('Return')">
                    <template #prefix><FeatherIcon name="corner-up-left" class="h-4 w-4" /></template>
                    Return
                </Button>

                <div class="ml-auto flex items-center gap-2">
                    <Button
                        v-if="permissionStore.salesInvoiceCanCreate"
                        variant="outline" theme="gray" size="lg"
                        :disabled="!invoiceStore.items.length"
                        @click="sales_invoice.fetch({ action: 'Save', status: 'save_new' })"
                    >
                        Hold sale
                    </Button>
                    <Button
                        v-if="permissionStore.salesInvoiceCanPrint && permissionStore.salesInvoiceCanCreate"
                        variant="solid" theme="gray" size="lg"
                        :disabled="!invoiceStore.items.length"
                        @click="sales_invoice.fetch({ action: 'Save', status: 'print' })"
                    >
                        <template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>
                        Save &amp; print
                    </Button>
                    <button
                        v-if="permissionStore.salesInvoiceCanSubmit"
                        type="button"
                        class="inline-flex h-10 min-w-[9rem] items-center justify-center gap-2 rounded-md px-5 text-lg font-semibold
                               transition-colors focus:outline-none focus-visible:ring focus-visible:ring-outline-green-2
                               disabled:cursor-not-allowed"
                        :class="invoiceStore.items.length
                            ? 'bg-surface-green-3 text-ink-white hover:bg-green-700 active:bg-green-800'
                            : 'bg-surface-gray-2 text-ink-gray-4'"
                        :disabled="!invoiceStore.items.length"
                        @click="sales_invoice.fetch({ action: 'Save', status: 'pay' })"
                    >
                        Pay <span class="num">{{ payableTotal }}</span>
                    </button>
                </div>
            </div>
        </footer>
    </section>
</template>

<script setup>
import { Button, FeatherIcon, createResource, debounce } from 'frappe-ui';
import { inject, watch, computed } from 'vue';
import CustomerBar from '@/components/pos/CustomerBar.vue';
import TotalsReadout from '@/components/pos/TotalsReadout.vue';
import { createToast, showToast } from '@/utils';
import { usePosProfileStore } from '@/stores/posProfile';
import { usePermissionStore } from '@/stores/permission';
import { useInvoiceStore } from '@/stores/pos';
import emitter from '@/utils/emitter';
import { openInvoicePrint } from '@/utils/print';
import Item from '@/components/Item.vue';

const props = defineProps({
    // Mobile layout: no card frame, cart lines render as cards, Pay goes full width.
    compact: { type: Boolean, default: false },
    // The payment panel is open: the draft is saved, so saving it again from
    // here would conflict. The sale is finished from the payment panel.
    paying: { type: Boolean, default: false },
});

const store = usePosProfileStore();
const permissionStore = usePermissionStore();
const invoiceStore = useInvoiceStore()
const { loadComponent } = inject('dynamicComponent');
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
            openInvoicePrint(data.docs[0].name, store.posProfileData);
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
   
// Payment rows are sent with zero amounts. The cart's own total can still be
// the value from before the last scan was recalculated, and saving it here put
// a stale amount on the default mode. The payment panel fills the default mode
// from the total the server computes when it saves the draft.
const getPayments = () =>
    (invoiceStore.invoice.payments || []).map((p) => ({ ...p, amount: 0, base_amount: 0 }));

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

const mobileActions = computed(() => {
    const empty = !invoiceStore.items.length;
    const list = [
        { label: 'Held', icon: 'clock', class: 'bg-surface-blue-1 text-ink-blue-3', run: () => loadComponent('Held') },
        { label: 'Return', icon: 'corner-up-left', class: 'bg-surface-red-1 text-ink-red-4', run: () => loadComponent('Return') },
    ];
    if (permissionStore.salesInvoiceCanCreate) {
        list.push({ label: 'Hold', icon: 'pause', disabled: empty, class: 'bg-surface-white border border-outline-gray-2 text-ink-gray-8',
            run: () => sales_invoice.fetch({ action: 'Save', status: 'save_new' }) });
    }
    if (permissionStore.salesInvoiceCanPrint && permissionStore.salesInvoiceCanCreate) {
        list.push({ label: 'Print', icon: 'printer', disabled: empty, class: 'bg-surface-gray-7 text-ink-white',
            run: () => sales_invoice.fetch({ action: 'Save', status: 'print' }) });
    }
    return list;
});

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
