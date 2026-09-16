<template>
    <section
        :class="[
            'flex min-h-0 flex-col bg-surface-white',
            compact
                ? 'flex-1'
                : 'w-[38%] min-w-[300px] max-w-[520px] shrink-0 overflow-hidden rounded-xl border border-outline-gray-1 shadow-sm',
        ]"
        aria-label="Payment"
    >
        <header class="flex h-12 shrink-0 items-center justify-between gap-2 border-b border-outline-gray-1 px-4">
            <h2 class="text-base font-semibold text-ink-gray-9">
                {{ invoiceStore.invoice.is_return ? 'Refund' : 'Payment' }}
            </h2>
            <span class="num truncate text-sm text-ink-gray-5">{{ invoiceStore.invoice.name }}</span>
        </header>

        <div class="min-h-0 flex-1 space-y-5 overflow-y-auto pos-scroll p-4">
            <!-- What is owed, what has been entered, and the difference. -->
            <div class="rounded-lg bg-surface-gray-1 p-3">
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <p class="text-sm text-ink-gray-5">To pay</p>
                        <p class="num text-2xl font-semibold text-ink-gray-9">{{ money(toPay) }}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-sm text-ink-gray-5">Paid</p>
                        <p class="num text-2xl font-semibold text-ink-gray-9">{{ money(paid) }}</p>
                    </div>
                </div>
                <div
                    v-if="Math.abs(balance) >= 0.005"
                    class="mt-3 flex items-center justify-between border-t border-outline-gray-2 pt-2 text-sm"
                >
                    <span class="text-ink-gray-6">{{ balance > 0 ? 'Change to give' : 'Still to pay' }}</span>
                    <span class="num font-semibold" :class="balance > 0 ? 'text-ink-green-3' : 'text-ink-amber-3'">
                        {{ money(Math.abs(balance)) }}
                    </span>
                </div>
            </div>

            <div>
                <h3 class="mb-2 text-sm font-medium text-ink-gray-7">Payment method</h3>
                <div class="space-y-2">
                    <div
                        v-for="(payment, index) in invoiceStore.invoice.payments || []"
                        :key="payment.mode_of_payment"
                        class="flex items-end gap-2"
                    >
                        <div class="min-w-0 flex-1">
                            <FormControl
                                type="number"
                                size="md"
                                variant="subtle"
                                placeholder="0.00"
                                :label="payment.mode_of_payment"
                                v-model="payment.amount"
                                @change="changePaymentAmount($event)"
                            />
                        </div>
                        <Button variant="subtle" size="md" class="shrink-0" @click="changemode(index)">
                            Pay full amount
                        </Button>
                    </div>
                    <p v-if="!(invoiceStore.invoice.payments || []).length" class="text-sm text-ink-gray-5">
                        No payment methods are set up on this POS Profile.
                    </p>
                </div>
            </div>

            <div v-if="(invoiceStore.invoice.advances || []).length">
                <h3 class="mb-2 text-sm font-medium text-ink-gray-7">Customer credit</h3>
                <div class="space-y-2">
                    <div
                        v-for="credit in invoiceStore.invoice.advances"
                        :key="credit.reference_name"
                        class="flex items-end gap-2"
                    >
                        <div class="min-w-0 flex-1">
                            <p class="truncate text-sm text-ink-gray-8">{{ credit.reference_name }}</p>
                            <p class="num text-xs text-ink-gray-5">{{ money(credit.advance_amount) }} available</p>
                        </div>
                        <div class="w-32 shrink-0">
                            <FormControl
                                type="number"
                                size="md"
                                variant="subtle"
                                placeholder="0.00"
                                label="Use"
                                v-model="credit.allocated_amount"
                                @change="changePaymentAmount($event)"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div v-if="store.posProfileData?.custom_set_sales_order" class="max-w-xs">
                <DatePicker size="md" variant="subtle" label="Delivery date" placeholder="Delivery date" v-model="deliveryDate" />
            </div>

            <dl class="space-y-1.5 text-sm">
                <div v-for="row in summary" :key="row.label" class="flex justify-between gap-2">
                    <dt class="text-ink-gray-5">{{ row.label }}</dt>
                    <dd class="num text-ink-gray-8" :class="row.strong ? 'font-semibold' : ''">{{ money(row.value) }}</dd>
                </div>
            </dl>
        </div>

        <footer class="shrink-0 space-y-2 border-t border-outline-gray-1 p-3" style="padding-bottom: calc(0.75rem + env(safe-area-inset-bottom))">
            <div class="grid grid-cols-2 gap-2">
                <button
                    type="button"
                    class="inline-flex h-10 items-center justify-center rounded-md bg-surface-green-3 px-4 text-lg font-semibold text-ink-white transition-colors hover:bg-green-700 active:bg-green-800 focus:outline-none focus-visible:ring focus-visible:ring-outline-green-2 disabled:cursor-not-allowed disabled:opacity-60"
                    :disabled="submitting"
                    @click="run(() => submitInvoice())"
                >
                    Submit
                </button>
                <Button variant="solid" theme="gray" size="lg" :disabled="submitting" @click="run(() => submitInvoice('print'))">
                    <template #prefix><FeatherIcon name="printer" class="h-4 w-4" /></template>
                    Submit &amp; print
                </Button>
            </div>
            <div class="flex items-center justify-between gap-2">
                <Button variant="ghost" size="md" :disabled="submitting" @click="backToCart">
                    <template #prefix><FeatherIcon name="arrow-left" class="h-4 w-4" /></template>
                    Back to cart
                </Button>
                <Button variant="ghost" theme="red" size="md" :disabled="submitting" @click="cancelSale">
                    Cancel sale
                </Button>
            </div>
        </footer>
    </section>
</template>

<script setup>
import { Button, FeatherIcon, FormControl, createResource, DatePicker, dayjsLocal } from 'frappe-ui'
import { ref, onMounted , watch, computed } from 'vue'
import { createToast } from '@/utils';
import { showToast } from '@/utils'
import emitter from '@/utils/emitter';
import { openInvoicePrint } from '@/utils/print';
import { usePosProfileStore } from '@/stores/posProfile';
import { useInvoiceStore } from '@/stores/pos';


defineProps({
    // Phones show the payment panel full screen instead of in the side pane.
    compact: { type: Boolean, default: false },
});

let doc = ref({})
const store = usePosProfileStore();
const invoiceStore = useInvoiceStore()
const addPayments = () => {
    const inv = invoiceStore.invoice
    const due = Number(inv.rounded_total || inv.grand_total || 0)
    if (!Array.isArray(inv.payments)) inv.payments = []

    const allowed = (store.posProfileData?.payments || []).filter(
        (mode) => !inv.is_return || mode.allow_in_returns
    )
    for (const mode of allowed) {
        if (!inv.payments.some((p) => p.mode_of_payment === mode.mode_of_payment)) {
            inv.payments.push({ mode_of_payment: mode.mode_of_payment, default: mode.default, amount: 0, base_amount: 0 })
        }
    }

    // Pre-fill the default mode with the amount due unless something was
    // already entered. This used to depend on the cart's background total
    // recalculation having finished before Pay was pressed; when it had not,
    // the server saved every row at 0 and nothing was pre-filled, while "Paid"
    // was still set to the full total.
    const entered =
        inv.payments.some((p) => Number(p.amount)) ||
        (inv.advances || []).some((a) => Number(a.allocated_amount))
    if (!entered && due) {
        const defaultMode = allowed.find((m) => Number(m.default))?.mode_of_payment
        const row = inv.payments.find((p) => p.mode_of_payment === defaultMode) || inv.payments[0]
        if (row) {
            row.amount = due
            row.base_amount = due
        }
    }

    changePaymentAmount()
}

const changemode = (index) => {
    invoiceStore.invoice.payments.forEach((element, i) => {
        if (i === index) {
            element.amount = invoiceStore.invoice.base_rounded_total
        } else {
            element.amount = 0
        }
    })
    invoiceStore.invoice.paid_amount = invoiceStore.invoice.base_rounded_total
}

const money = (value) => Number(value || 0).toFixed(2)
const toPay = computed(() => Number(invoiceStore.invoice.rounded_total || invoiceStore.invoice.grand_total || 0))
const paid = computed(() => Number(invoiceStore.invoice.paid_amount || 0))
// Positive: change is due. Negative: part of the bill is still unpaid.
const balance = computed(() => paid.value - toPay.value)

const summary = computed(() => {
    const inv = invoiceStore.invoice
    const rows = [
        { label: 'Net total', value: inv.net_total },
        { label: 'Taxes and charges', value: inv.total_taxes_and_charges },
    ]
    if (Number(inv.discount_amount)) rows.push({ label: 'Discount', value: inv.discount_amount })
    rows.push({ label: 'Grand total', value: inv.grand_total })
    if (Number(inv.rounding_adjustment)) rows.push({ label: 'Rounding', value: inv.rounding_adjustment })
    rows.push({ label: 'Rounded total', value: inv.rounded_total, strong: true })
    return rows
})

// Guard against double submission while the save/submit round trips run.
const submitting = ref(false)
const run = async (action) => {
    if (submitting.value) return
    submitting.value = true
    try {
        await action()
    } finally {
        submitting.value = false
    }
}

// The invoice is already saved as a draft; editing it and pressing Pay again
// updates that same draft.
const backToCart = () => {
    invoiceStore.invoice.docstatus = 0
}

// Discards the sale on this screen. The draft stays in Sales Invoice.
const cancelSale = () => {
    emitter.emit('remove_invoice', true)
}

const deliveryDate = computed({
  get() {
    if (!invoiceStore.invoice.delivery_date) {
      const today = dayjsLocal().format('YYYY-MM-DD')
      invoiceStore.invoice.delivery_date = today
    }
    return invoiceStore.invoice.delivery_date
  },
  set(value) {
    invoiceStore.invoice.delivery_date = value
  }
})

const createSaveResource = createResource({
    url: 'frappe.desk.form.save.savedocs',
    makeParams(params) {
        return {
            doc: JSON.stringify(params.doc),
            action: params.action
        };
    },
    onSuccess(data) {
        doc.value.doc = data.docs[0];
    },
    onError(error) {
        createToast({
            title: 'error',
            message: Array.isArray(error?.messages) ? error.messages[0] : error?.messages || 'An error occurred',
            icon: 'x-circle',
            iconClasses: 'bg-surface-red-5 text-ink-white rounded-md p-px',
            position: 'top-center',
            timeout: 5,
        });
    }
});

const changePaymentAmount = () => {
    invoiceStore.invoice.paid_amount = 0;
    invoiceStore.invoice.payments.forEach((element) => {
        element.amount = Number(element.amount);
        invoiceStore.invoice.paid_amount += element.amount;
    });

    if (Array.isArray(invoiceStore.invoice.advances)) {
        invoiceStore.invoice.advances.forEach((element) => {
            if (element.allocated_amount > 0) {
                element.allocated_amount = Number(element.allocated_amount);
                invoiceStore.invoice.paid_amount += element.allocated_amount;
            }
        });
    }
};

const saveAndSubmit = async (doc) => {
    await createSaveResource.fetch({ action: 'Save', doc: doc.value.doc });
    // A failed Save leaves doc.value.doc on the client-side temp name; submitting
    // it would create a second document instead of submitting the first.
    if (!doc.value.doc?.name || doc.value.doc.name.startsWith('new-')) {
        return false;
    }
    await createSaveResource.fetch({ action: 'Submit', doc: doc.value.doc });
    return true;
}

const submitInvoice = async (action = null) => {
    if(!store.posProfileData.custom_allow_credit){
        if (invoiceStore.invoice.paid_amount< invoiceStore.invoice.rounded_total) return showToast('warning', 'Credit Not Allowed', 'alert-circle', '#ffcc00','#ffffff');
    }
    if(!store.posProfileData.custom_allow_partial_payments){
        if ((invoiceStore.invoice.paid_amount - invoiceStore.invoice.rounded_total) > 0 ) return showToast('warning', 'Partial payment  Not Allowed', 'alert-circle', '#ffcc00','#ffffff');
    }
    let invoice = { ...invoiceStore.invoice };
    if (await validatePaymentBeforeSave()) {
        if (store.posProfileData.custom_set_sales_order) {
            const salesOrder = {
                ...invoiceStore.invoice,
                doctype: 'Sales Order',
                name: '',
                naming_series: ''
            };

            doc.value = { doc: salesOrder };
            if (!await saveAndSubmit(doc)) return;
            const orderName = doc.value.doc.name;
            invoiceStore.invoice.items.forEach((item, index) => {
                item.so_detail = doc.value.doc.items?.[index]?.name || "";
                item.sales_order = orderName;
            });
        }
        doc.value = {
            doc: invoiceStore.invoice
        }
        if (!await saveAndSubmit(doc)) return;

        // `invoice` was snapshotted before the save, so it still carries the
        // client-side temp name. Everything downstream needs the name the server
        // assigned.
        const saved = doc.value.doc;
        invoice.name = saved.name;
        invoice.due_date = saved.due_date ?? invoice.due_date;

        emitter.emit('remove_invoice',true);
        await createPayments(invoice);
        showToast('success','Invoice submitted successfully', 'check-circle', 'green');
        if (action !== null) {
            createPrint(saved.name);
        }
    }
};

const createPayments = async (invoice) =>{
    if ((invoice.advances || []).some((element) => element.allocated_amount > 0)) {
        for (const element of invoice.payments) {
            if (element.amount > 0) {
                await makepayment.fetch({ payments: element, invoice: invoice, method: 'Submit', change: true });
            }
        }
    }
};

const createPrint = (name) => openInvoicePrint(name, store.posProfileData)

createResource({
    url: 'run_doc_method',
    auto: true,
    makeParams(params) {        
        return {
            docs: { ...invoiceStore.invoice, is_pos: false, custom_ant_opening:store.openingShift.name },
            method: 'set_advances'
        }
    },
    onSuccess(data) {
        for (const key in data.docs[0]) {
           
            const existingValue = invoiceStore.invoice[key];
            const newValue = data.docs[0][key];

            // Check for changes or new keys
            if (key !== 'is_pos' && key !== 'docstatus' && JSON.stringify(existingValue) !== JSON.stringify(newValue)) {
                invoiceStore.invoice[key] = newValue;
            }
        }
        addPayments()
    },
    onError(error) {
        createToast({
            title: 'error',
            message: Array.isArray(error?.messages) ? error.messages[0] : error?.messages  || 'An error occurred',
            icon: 'x-circle',
            iconClasses: 'bg-surface-red-5 text-ink-white rounded-md p-px',
            position: 'top-center',
            timeout: 5,
        });
    },
});

const makepayment = createResource({
    url: 'frappe.desk.form.save.savedocs',
    makeParams(params) {
        return {
            doc: JSON.stringify({
                ...params.payments,
                doctype: 'Payment Entry',
                payment_type: 'Receive',
                party_type: 'Customer',
                party: params.invoice.customer,
                paid_amount: params.payments.amount,
                received_amount: params.payments.amount,
                name: '',
                references: [
                    {
                        reference_doctype: 'Sales Invoice',
                        reference_name: params.invoice.name,
                        due_date: params.invoice.due_date,
                        allocated_amount: params.payments.amount
                    }
                ],
                target_exchange_rate: 1,
                company: params.invoice.company,
                cost_center: params.invoice.cost_center,
                branch: params.invoice.branch,
                // Ant Closing Shift collects payments by reference_no; without
                // this, advance payments never appear in the shift totals.
                reference_no: store.openingShift.name,
                reference_date: params.invoice.posting_date,
            }),
            action: params.method
        }
    },
    onError(error) {
        createToast({
            title: 'error',
            message: Array.isArray(error?.messages) ? error.messages[0] : error?.messages  || 'An error occurred',
            icon: 'x-circle',
            iconClasses: 'bg-surface-red-5 text-ink-white rounded-md p-px',
            position: 'top-center',
            timeout: 5,
        });
    },
});

const validatePaymentBeforeSave = async () => {
    let advance = 0
    let payment = 0
    
    ;(invoiceStore.invoice.advances || []).forEach((element) => {
        element.allocated_amount = Number(element.allocated_amount)
        advance += element.allocated_amount
    })

    ;(invoiceStore.invoice.payments || []).forEach((element) => {
        payment += Number(element.amount)
    })

    if (advance > 0) {
        if (invoiceStore.invoice.paid_amount > invoiceStore.invoice.rounded_total) {
            showToast('warning', 'Paid amount is greater than rounded total', 'alert-circle', '#ffcc00','#ffffff');
            return false;
        }
        invoiceStore.invoice.payments = []
        invoiceStore.invoice.is_pos = false
    }

    return true;
}

watch(
    () => {
        const advances = invoiceStore.invoice?.advances;
        return Array.isArray(advances) ? advances.map(advance => advance.allocated_amount) : [];
    },
    (newValues, oldValues) => {
        changePaymentAmount();
    },
    { deep: true }
);

onMounted(() => {
    addPayments()
})
</script>