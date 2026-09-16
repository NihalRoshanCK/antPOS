<template>
    <!-- Desktop: invoices and the payment form side by side, each scrolling.
         Phones: one scrolling column with the submit button pinned below. -->
    <div class="flex h-full w-full min-h-0 flex-col bg-surface-gray-1 lg:flex-row lg:gap-3 lg:p-3">
        <!-- The resize handle between the two panes is also the gap. -->
        <div class="min-h-0 flex-1 overflow-y-auto pos-scroll lg:flex lg:min-w-0 lg:flex-row lg:overflow-hidden">

            <!-- Customer and invoices -->
            <section class="flex flex-col bg-surface-white lg:min-h-0 lg:min-w-0 lg:flex-1 lg:overflow-hidden lg:rounded-xl lg:border lg:border-outline-gray-1 lg:shadow-sm">
                <div class="space-y-3 border-b border-outline-gray-1 p-3">
                    <Customer v-model:customer="paymentStore.paymentCustomer" />
                    <TabButtons
                        class="w-full"
                        :buttons="[
                            { label: 'Settle invoices', value: 'credit' },
                            { label: 'Advance payment', value: 'advanced' },
                        ]"
                        v-model="currentTab"
                    />
                    <TextInput
                        v-if="currentTab === 'credit' && paymentStore.paymentCustomer?.name"
                        type="text"
                        size="md"
                        variant="subtle"
                        v-model="searchQuery"
                        placeholder="Search invoices"
                    >
                        <template #prefix><FeatherIcon class="w-4 text-ink-gray-5" name="search" /></template>
                    </TextInput>
                </div>

                <div class="p-3 lg:min-h-0 lg:flex-1 lg:overflow-y-auto lg:pos-scroll">
                    <div v-if="!paymentStore.paymentCustomer?.name" class="px-4 py-10 text-center">
                        <p class="text-base font-medium text-ink-gray-8">Choose a customer</p>
                        <p class="mt-1 text-sm text-ink-gray-5">
                            {{ currentTab === 'credit' ? 'Their unpaid invoices will appear here.' : 'Then enter the amount they are paying in advance.' }}
                        </p>
                    </div>

                    <template v-else-if="currentTab === 'credit'">
                        <label
                            v-if="filteredInvoices.length"
                            class="mb-2 flex cursor-pointer items-center gap-3 px-3 py-1 text-sm text-ink-gray-6"
                        >
                            <input
                                type="checkbox"
                                class="h-4 w-4 rounded-sm text-ink-gray-9 focus:ring-0"
                                :checked="selectAll"
                                @change="toggleAllSelection"
                            />
                            <span class="flex-1">Select all</span>
                            <span class="num">{{ filteredInvoices.length }} unpaid</span>
                        </label>

                        <ul v-if="filteredInvoices.length" class="space-y-2">
                            <li v-for="invoice in filteredInvoices" :key="invoice.name">
                                <label
                                    class="flex min-h-[3.75rem] cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors"
                                    :class="invoice.selected
                                        ? 'border-outline-gray-4 bg-surface-gray-1'
                                        : 'border-outline-gray-1 hover:border-outline-gray-3'"
                                >
                                    <input
                                        type="checkbox"
                                        class="h-4 w-4 shrink-0 rounded-sm text-ink-gray-9 focus:ring-0"
                                        :checked="invoice.selected"
                                        @change="toggleSelection(invoice)"
                                    />
                                    <span class="min-w-0 flex-1">
                                        <span class="num block truncate text-sm font-medium text-ink-gray-9">{{ invoice.name }}</span>
                                        <span class="num block text-sm text-ink-gray-5">
                                            of {{ Number(invoice.grand_total || 0).toFixed(2) }}
                                        </span>
                                    </span>
                                    <span class="shrink-0 text-right">
                                        <span class="num block text-base font-semibold text-ink-gray-9">
                                            {{ Number(invoice.outstanding_amount || 0).toFixed(2) }}
                                        </span>
                                        <span class="block text-xs text-ink-gray-5">due</span>
                                    </span>
                                </label>
                            </li>
                        </ul>

                        <div v-else-if="!invoices.loading" class="px-4 py-10 text-center">
                            <p class="text-sm text-ink-gray-5">This customer has no unpaid invoices.</p>
                        </div>

                        <div v-if="invoices.hasNextPage && filteredInvoices.length" class="pt-3 text-center">
                            <Button variant="ghost" :loading="invoices.loading" @click="invoices.next()">Load more</Button>
                        </div>
                    </template>

                    <p v-else class="px-1 text-sm text-ink-gray-6">
                        Record money received from
                        <span class="font-medium text-ink-gray-8">{{ paymentStore.paymentCustomer.name }}</span>
                        ahead of an invoice. It is available to use against their future sales.
                    </p>
                </div>
            </section>

            <!-- Payment -->
            <PaneResizer
                v-if="isDesktop"
                v-model="paymentWidth"
                storage-key="payments-panel"
                side="right"
                :default="380"
                :min="320"
                :min-other="420"
                label="Resize payment panel"
            />
            <section
                class="border-t border-outline-gray-1 bg-surface-white lg:flex lg:min-h-0 lg:shrink-0 lg:flex-col lg:overflow-y-auto lg:rounded-xl lg:border lg:shadow-sm"
                :style="isDesktop ? { width: `${paymentWidth}px` } : {}"
            >
                <div class="space-y-4 p-3">
                    <div v-if="currentTab === 'credit'" class="rounded-lg bg-surface-gray-1 p-3">
                        <FormControl
                            type="number"
                            size="md"
                            variant="subtle"
                            placeholder="0.00"
                            label="Amount to settle"
                            v-model="paymentStore.payment.paymentAmount"
                            @change="calculateAmountTotal"
                        />
                        <p class="mt-1 text-xs text-ink-gray-5">Filled from the invoices you select. You can lower it for a part payment.</p>
                    </div>

                    <div>
                        <h3 class="mb-2 text-sm font-medium text-ink-gray-7">Payment method</h3>
                        <div class="space-y-2">
                            <div v-for="(mode, index) in modes" :key="mode.mode_of_payment" class="flex items-end gap-2">
                                <div class="min-w-0 flex-1">
                                    <FormControl
                                        type="number"
                                        size="md"
                                        variant="subtle"
                                        placeholder="0.00"
                                        :label="mode.mode_of_payment"
                                        v-model="mode.amount"
                                    />
                                </div>
                                <Button
                                    v-if="currentTab === 'credit'"
                                    variant="subtle"
                                    size="md"
                                    class="shrink-0"
                                    @click="changemode(index)"
                                >
                                    Use full amount
                                </Button>
                            </div>
                        </div>
                    </div>

                    <div
                        v-if="currentTab === 'credit' && Math.abs(Number(paymentStore.payment.diff || 0)) >= 0.005"
                        class="flex items-center justify-between rounded-lg bg-surface-gray-1 px-3 py-2 text-sm"
                    >
                        <span class="text-ink-gray-6">
                            {{ Number(paymentStore.payment.diff) > 0 ? 'Not yet allocated' : 'More than selected' }}
                        </span>
                        <span class="num font-semibold" :class="Number(paymentStore.payment.diff) > 0 ? 'text-ink-amber-3' : 'text-ink-red-4'">
                            {{ Math.abs(Number(paymentStore.payment.diff)).toFixed(2) }}
                        </span>
                    </div>
                </div>

                <div class="hidden border-t border-outline-gray-1 p-3 lg:mt-auto lg:block">
                    <button
                        type="button"
                        class="inline-flex h-10 w-full items-center justify-center rounded-md text-lg font-semibold transition-colors focus:outline-none focus-visible:ring focus-visible:ring-outline-green-2 disabled:cursor-not-allowed"
                        :class="hasSelectedInvoice ? 'bg-surface-green-3 text-ink-white hover:bg-green-700' : 'bg-surface-gray-2 text-ink-gray-4'"
                        :disabled="!hasSelectedInvoice"
                        @click="createpayment"
                    >
                        Record payment
                    </button>
                </div>
            </section>
        </div>

        <!-- Phones: the action stays in reach while the list scrolls. -->
        <div class="shrink-0 border-t border-outline-gray-1 bg-surface-white p-3 lg:hidden">
            <button
                type="button"
                class="inline-flex h-12 w-full items-center justify-center rounded-md text-lg font-semibold transition-colors focus:outline-none focus-visible:ring focus-visible:ring-outline-green-2 disabled:cursor-not-allowed"
                :class="hasSelectedInvoice ? 'bg-surface-green-3 text-ink-white active:bg-green-800' : 'bg-surface-gray-2 text-ink-gray-4'"
                :disabled="!hasSelectedInvoice"
                @click="createpayment"
            >
                Record payment
            </button>
        </div>
    </div>
</template>

<script setup>

import { Button, createListResource, TextInput, FormControl, FeatherIcon, createResource, TabButtons } from 'frappe-ui';
import { ref, computed, watch, onBeforeMount, onMounted } from 'vue';
import Customer from '@/components/Customer.vue';
import PaneResizer from '@/components/PaneResizer.vue';
import { useBreakpoint } from '@/composables/useBreakpoint';
import { createToast } from '@/utils';
import { usePosProfileStore } from '@/stores/posProfile';
import { usePaymentStore } from '@/stores/payment'
import emitter from '@/utils/emitter'; 

const { isDesktop } = useBreakpoint();
const paymentWidth = ref(380);
const store = usePosProfileStore();
const paymentStore = usePaymentStore();
const searchQuery = ref("");
const currentTab = ref('credit');
const selectAll = ref(false);
const selectedPageLength = ref(20);
const modes = ref([]);

const setPageLength = (size) => {
    if (selectedPageLength.value !== size) {
        selectedPageLength.value = size;
        invoices.update({ pageLength: size, start: 0 }); 
        invoices.reload();
    }
};
const buildInvoiceFilters = (customer) => ({
    outstanding_amount: ['>', 0],
    docstatus: 1,
    is_return: 0,
    customer: customer || paymentStore.paymentCustomer?.name,
});

const invoices = createListResource({
    doctype: 'Sales Invoice',
    fields: ['name', 'customer', 'grand_total', 'outstanding_amount'],
    filters: buildInvoiceFilters(),
    orderBy: 'creation asc',
    // The page-size buttons and "Load more" below drive this; it must not be
    // Infinity. (There used to be a second pageLength key here that silently
    // overrode the first.)
    pageLength: 20,
    transform(data) {
        for (let d of data) {
            d.selected= false
        }
        return data
    },
});

const filteredInvoices = computed(() => {
    if (!invoices.data || !paymentStore.paymentCustomer?.name) {
        return [];
    }
    if (!searchQuery.value) {
        return invoices.data;
    }
    return invoices.data.filter(invoice =>
        invoice.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        invoice.customer.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
});

const hasSelectedInvoice = computed(() => {
    if (currentTab.value === 'credit') return invoices.data?.some(inv => inv.selected);
    else if (currentTab.value === 'advanced') return paymentStore.paymentCustomer?.name && modes.value.some(mode => mode.amount > 0);
    else return false;
});

const calculateAmountTotal = () => {
    let total = invoices.data.reduce((sum, invoice) => {
        return invoice.selected ? sum + invoice.outstanding_amount : sum;
    }, 0);
    paymentStore.payment.paymentAmount = total;
};

const toggleAllSelection = (event) => {
    if (event && event.stopPropagation) {
        event.stopPropagation();
    }
    selectAll.value = event.target.checked;
    invoices.data.forEach(invoice => {
        invoice.selected = selectAll.value;
    });

    calculateAmountTotal();
};

const toggleSelection = (invoice) => {
    if (selectAll.value) {
        selectAll.value = false;
    }
    invoice.selected = !invoice.selected;
    selectAll.value = invoices.data.every(inv => inv.selected);
    calculateAmountTotal();
};

const addPayments = () => {
    store.posProfileData?.payments?.forEach(element => {
        modes.value.push({
            "mode_of_payment": element.mode_of_payment,
            "amount": 0.00,
            "base_amount": 0.00,
        })
    })
    paymentStore.payment.paid_amount=0;
    paymentStore.payment.diff=0;
};

const clearPayments = async (params) => {
    paymentStore.unmountAndRefresh(params)
    modes?.value?.forEach(mode => {
        mode.amount = 0;
    });
    invoices?.data?.forEach(invoice => {
        invoice.selected = false;
    });
    await invoices.reload()
    selectAll.value = false;
    invoices.reload();
};

const changemode = (index) => {
    modes.value.forEach((element, i) => {
        if (i === index) {
            element.amount = paymentStore.payment.paymentAmount;
        } else {
            element.amount = 0;
        }
    });
    paymentStore.payment.paid_amount = paymentStore.payment.paymentAmount;
};

const now = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

const createpayment = async () => {
    if (currentTab.value === 'credit'){
        const sortedModes = [...modes.value].sort((a, b) => b.amount - a.amount);
        const selectedInvoices = filteredInvoices.value.filter(inv => inv.selected);
        let i = 0;
        while (i < sortedModes.length) {
            const currentMode = sortedModes[i];
            let totalToSpend = currentMode.amount;
            const invoiceDetails = [];
            for (let invoice of selectedInvoices) {
                if (totalToSpend <= 0) break;
                if (invoice.outstanding_amount <= 0) continue;
                const allocated = Math.min(totalToSpend, invoice.outstanding_amount);
                invoice.outstanding_amount -= allocated;
                totalToSpend -= allocated;
                
                invoiceDetails.push({
                    reference_doctype: "Sales Invoice",
                    reference_name: invoice.name,
                    allocated_amount: allocated,
                    outstanding_amount: invoice.outstanding_amount
                });
            }
            if ((currentMode.amount - totalToSpend) > 0 && invoiceDetails.length > 0) {
                await save.fetch({
                    action: 'Submit',
                    references: invoiceDetails,
                    mode: currentMode.mode_of_payment,
                    amount: currentMode.amount - totalToSpend
                });
            }    
            i++;
        }
        clearPayments();
    } else {
        const totalAmount = modes.value.reduce((sum, mode) => sum + (mode.amount || 0), 0);
        if (totalAmount > 0) {
            for (const mode of modes.value) {
                if (mode.amount > 0) {
                    await save.fetch({
                        action: 'Submit',
                        references: [],
                        mode: mode.mode_of_payment,
                        amount: mode.amount || 0
                    });
                }
            }
            clearPayments();
        } else {
            createToast({
                title: 'Error',
                message: 'Please enter a valid amount for the payment method.',
                icon: 'x-circle',
                iconClasses: 'bg-surface-red-5 text-ink-white rounded-md p-px',
                position: 'top-center',
                timeout: 5,
            });
        }
    }
};


    
let save = createResource({
    url: 'frappe.desk.form.save.savedocs',
    makeParams(params) {
        return {
            doc: JSON.stringify(
                {
                    doctype: "Payment Entry",
                    payment_type: "Receive",
                    posting_date: now(),
                    party_type: 'Customer',
                    mode_of_payment: params.mode,
                    party: paymentStore.paymentCustomer?.name,
                    company: store.posProfileData?.company,
                    cost_center: store.posProfileData?.cost_center,
                    // paid_from / paid_to and their currencies are company-specific
                    // and are resolved server-side in ant_pos.ant_pos.api.payment_entry.validate
                    paid_amount: params.amount,
                    base_paid_amount: params.amount,
                    received_amount: params.amount,
                    base_received_amount: params.amount,
                    references: params.references.length > 0 ?  params.references : [],
                    reference_no: store.openingShift.name,
                    reference_date: now(),
                },
            ),
            action: params.action
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

watch(
    // Watch the name, not the object: the old watcher fired on every identity
    // change and dereferenced newValue.name, which threw the moment the customer
    // was cleared and took the whole page down with it (issue #57).
    () => paymentStore.paymentCustomer?.name || null,
    (customer, previous) => {
        if (customer === previous) return;

        if (!customer) {
            // Clearing the customer must clear their invoices too, otherwise the
            // previous customer's outstanding list stays on screen.
            invoices.data = [];
            selectAll.value = false;
            paymentStore.payment.paymentAmount = 0;
            modes.value.forEach((mode) => { mode.amount = 0; });
            return;
        }

        invoices.update({ filters: buildInvoiceFilters(customer), start: 0 });
        invoices.reload();
    },
    { immediate: true }
);

watch(
    () => modes.value.map(mode => mode.amount),
    (newAmounts) => {
        const total = newAmounts.reduce((sum, val) => sum + Number(val || 0), 0);
        paymentStore.payment.diff =   Number(paymentStore.payment.paymentAmount || 0) - total;
    },
    { immediate: true }
);

watch(searchQuery, (newQuery) => {
  invoices.update({
    filters: buildInvoiceFilters(),
    orFilters: newQuery
      ? [
          ['name', 'like', `%${newQuery}%`],
        ]
      : []
  });
  invoices.reload();
});

onMounted(()=>{
    emitter.on('clear', (params) => {
            clearPayments(params)
        });

})

onBeforeMount(() => {
    addPayments();
});
   
</script>
