<template>
    <Dialog :options="{ title: 'Return an invoice', size: 'xl' }" v-model="dialogVisible">
        <template #body-content>
            <InvoicePicker
                v-model="selectedInvoice"
                v-model:search="searchQuery"
                :invoices="invoices.data || []"
                :loading="invoices.loading"
                :has-more="invoices.hasNextPage"
                empty-text="No submitted invoices to return."
                aria-label="Invoices to return"
                @confirm="(name) => { selectedInvoice = name; submitInvoice() }"
                @load-more="invoices.next()"
            />
        </template>
        <template #actions>
            <div class="flex flex-row-reverse gap-2">
                <Button
                    variant="solid"
                    size="md"
                    class="flex-1 sm:flex-none"
                    :disabled="!selectedInvoice"
                    :loading="loadingSelection"
                    @click="submitInvoice"
                >
                    Start return
                </Button>
                <Button size="md" class="flex-1 sm:flex-none" @click="handleDialogClose">Cancel</Button>
            </div>
        </template>
    </Dialog>
</template>

<script setup>
import { Dialog, Button, createListResource, createResource, debounce } from 'frappe-ui';
import InvoicePicker from '@/components/pos/InvoicePicker.vue';
import { ref, computed, watch } from 'vue';
import { createToast } from '@/utils';
import { usePosProfileStore } from '@/stores/posProfile';
import { usePermissionStore } from '@/stores/permission';
import { usersStore } from '@/stores/users';
import { useInvoiceStore } from '@/stores/pos';
import { generateTempName } from '@/utils';

const store = usePosProfileStore();
const dialogVisible = ref(true);
const selectedInvoice = ref(null);
const searchQuery = ref("");
const selectedPageLength = ref(20);
const handleDialogClose = () => { dialogVisible.value = false; };
const permissionStore = usePermissionStore();
const invoiceStore = useInvoiceStore()
const user = usersStore().getUser();

const setPageLength = (size) => {
    if (selectedPageLength.value !== size) {
        selectedPageLength.value = size;
        invoices.update({ pageLength: size, start: 0 }); 
        invoices.reload();
    }
};

const submitInvoice = () => {
    salesInvoice.fetch({ name: selectedInvoice.value });
};

const runDoCMethod = createResource({
    url: 'run_doc_method',
    makeParams(params) {
        return {...params}
    },
    transform(data){
        if (data.docs[0] && data.docs[0].items && data.docs[0].items.length > 0) {
            data.docs[0].items.forEach(item => {
                if (item.serial_no) {
                    item.selected_serial_no = item.serial_no.trim().split('\n').map(serial => ({
                        label: serial,
                        value: serial
                    }));
                    
                }
                if (item.serial_no){
                    item._serial=item.serial_no.trim().split('\n');
                }
                if (item.batch_no) {
                    
                    item.selected_batch_no = {
                        label: item.batch_no,
                        value: item.batch_no
                    };
                } else {
                    item.selected_batch_no = null;
                }
                if (!item.custom_id) {
                    item.custom_id = Date.now() + Math.random();
                }
            });    
        }
        return data
    },
    onSuccess(data){
        addvalues();    
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

let salesInvoice = createResource({
    url: 'frappe.model.mapper.make_mapped_doc',
    makeParams(params) {
        return {
            method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
            source_name: params.name,
            selected_children:{},
            args:""
        };
    },
    onSuccess: async (data) => {
        await runDoCMethod.fetch({ for_validate: true, docs: data, method: 'set_missing_values', args: { "for_validate": true } });
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

function returnFilters() {
    const filters = {
        docstatus: 1,
        pos_profile: store.posProfileData.name,
        is_return: 0,
        status: ['!=', 'Credit Note Issued'],
    };
    if (permissionStore.salesInvoiceCanOnlyOwn) filters.owner = user.name;
    return filters;
}

const loadingSelection = computed(() => Boolean(salesInvoice.loading || runDoCMethod.loading || get_value.loading));

const invoices = createListResource({
    doctype: 'Sales Invoice',
    fields: ['name', 'customer', 'grand_total', 'posting_date'],
    orderBy: 'creation desc',
    filters: returnFilters(),
    orFilters: [],
    pageLength: 20,
    auto: true
});

const filteredInvoices = computed(() => {
    if (!searchQuery.value) return invoices.data || [];
        return (invoices.data || []).filter(invoice =>
            invoice.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        invoice.customer.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
});

async function splitSerialNumbers(serialString = "") {
    if (typeof serialString !== "string" || !serialString.trim()) return [];
    
    return serialString
        .trim()
        .split("\n")
        .map(line => line.trim())
        .filter(line => line !== "")
        .map(serial => ({
            label: serial,
            value: serial
        }));
}

const  addvalues = async ()=>{
    invoiceStore.invoice =  { ...runDoCMethod.data.docs[0], status: null, name: generateTempName('Sales Invoice') }
    invoiceStore.items = runDoCMethod.data.docs[0].items || [];
    invoiceStore.invoice._discount_amount =  runDoCMethod.data.docs[0].discount_amount;
    invoiceStore.invoice._additional_discount_percentage =  runDoCMethod.data.docs[0].additional_discount_percentage;
    invoiceStore.invoice._total =  runDoCMethod.data.docs[0].net_total;
    await get_value.fetch({
        doctype: "Customer",
        filters: { "name": runDoCMethod.data.docs[0].customer },
        fieldname: ['name', 'mobile_no', 'customer_group', 'territory', 'is_internal_customer'],
    });
    invoiceStore.invoiceCustomer = get_value.data || {};
    searchQuery.value='';
    handleDialogClose()
}

const get_value = createResource({
    url:'frappe.client.get_value',
    makeParams(params) {
        return { ...params }
    },
    transform: (data) => {        
        return {
            label: data.name,
            value: data.name,
            mobile_no: data.mobile_no,
            name: data.name,
            customer_group: data.customer_group,
            territory: data.territory,
            is_internal_customer: data.is_internal_customer,
        }
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

})

const updateInvoices = debounce((newQuery) => {
  invoices.update({
    // Must keep every base filter: this used to drop `owner` and the
    // "not already returned" condition as soon as the cashier searched.
    filters: returnFilters(),
    orFilters: newQuery
      ? [
          ['name', 'like', `%${newQuery}%`],
          ['customer', 'like', `%${newQuery}%`]
        ]
      : []
  });
  invoices.reload();
}, 300); 

watch(searchQuery, updateInvoices);

</script>
