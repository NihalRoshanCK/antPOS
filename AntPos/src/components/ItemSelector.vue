<template>
    <section
        :class="[
            'flex flex-col min-h-0 bg-white',
            compact
                ? 'shrink-0 border-b border-outline-gray-1'
                : 'w-[30%] min-w-[280px] max-w-[380px] shrink-0 rounded-xl border border-outline-gray-1 shadow-sm overflow-hidden',
        ]"
    >
        <div class="p-3" :class="compact ? '' : 'border-b border-outline-gray-1'">
            <FormControl
                ref="searchInput"
                type="text"
                v-model="debounceSearch"
                :placeholder="compact ? 'Scan or search' : 'Scan barcode or search items'"
                :size="compact ? 'md' : 'md'"
                variant="subtle"
                @keyup.enter="fetchSearchResource"
                :disabled="invoiceStore.invoice.is_return"
            >
                <template #prefix>
                    <FeatherIcon class="w-4 text-ink-gray-5" name="search" />
                </template>
            </FormControl>
        </div>

        <!-- Desktop only: the pane is otherwise empty, which is most of what the
             cashier looks at between scans. -->
        <div v-if="!compact" class="flex-1 overflow-y-auto pos-scroll min-h-0">
            <template v-if="recentScans.length">
                <p class="px-3 py-2 text-[11px] font-semibold text-ink-gray-5 border-b border-outline-gray-1">
                    Recent scans
                </p>
                <button
                    v-for="scan in recentScans"
                    :key="scan.key"
                    type="button"
                    class="w-full text-left px-3 py-2.5 border-b border-outline-gray-1 hover:bg-surface-gray-1 focus:outline-none focus-visible:bg-surface-gray-1 flex items-baseline gap-3"
                    @click="rescan(scan)"
                >
                    <span class="text-[14px] font-medium flex-1 truncate">{{ scan.item_name }}</span>
                    <span class="text-[12px] text-ink-gray-5 num shrink-0">{{ scan.item_code }}</span>
                    <span class="text-[14px] num font-medium shrink-0">{{ Number(scan.rate || 0).toFixed(2) }}</span>
                </button>
            </template>

            <div class="px-6 py-10 text-center">
                <svg class="mx-auto text-ink-gray-3" width="34" height="34" viewBox="0 0 24 24"
                     fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                    <path d="M3 5v14M7 5v14M11 5v14M15 5v14M19 5v14" />
                </svg>
                <p class="text-[13px] text-ink-gray-6 mt-3 leading-relaxed">
                    Scan a barcode, or type an item code,<br />serial or batch number.
                </p>
                <p class="text-[12px] text-ink-gray-5 mt-2">
                    Press
                    <kbd class="px-1.5 py-0.5 rounded border border-outline-gray-1 bg-surface-gray-1 font-sans">Enter</kbd>
                    to add
                </p>
            </div>
        </div>
    </section>
</template>

<script setup>
import { FormControl, FeatherIcon, createResource } from 'frappe-ui';
import { ref, onMounted } from 'vue';
import { createToast } from '@/utils';
import { showToast } from '@/utils'
import { usePosProfileStore } from '@/stores/posProfile';
import emitter from '@/utils/emitter';
import { useInvoiceStore } from '@/stores/pos';

defineProps({
    // Mobile stacks the scan box above the cart, so the panel chrome and the
    // recent-scan list are dropped -- there is no room for either.
    compact: { type: Boolean, default: false },
});

const store = usePosProfileStore();
const debounceSearch = ref('');
const invoiceStore = useInvoiceStore()

// A short history so the pane is useful between scans. Kept in memory only:
// it is a convenience, not a record.
const RECENT_LIMIT = 8;
const recentScans = ref([]);

const rememberScan = (item) => {
    if (!item?.item_code) return;
    const entry = {
        key: item.item_code,
        item_code: item.item_code,
        item_name: item.item_name || item.item_code,
        rate: item.price_list_rate ?? item.rate,
    };
    recentScans.value = [entry, ...recentScans.value.filter((s) => s.key !== entry.key)]
        .slice(0, RECENT_LIMIT);
};

const rescan = (scan) => {
    if (invoiceStore.invoice.is_return) return;
    debounceSearch.value = scan.item_code;
    fetchSearchResource();
};

const remove_invoice = ( include_customer = false ) => {
    invoiceStore.unmountAndRefresh(include_customer)
};

const searchResource = createResource({
    url: 'ant_pos.ant_pos.api.item.scan_barcode',
    method: 'GET',
    debounce: 300,
    makeParams() {
        return {
            search_value: debounceSearch.value,
            search_itemname:store.posProfileData.custom_allow_item_name_in_in_item_search
        };
    },
    validate(params) {
        if (!invoiceStore.invoiceCustomer?.name) {
            return 'Customer is required'
        }    
        if (!params.search_value) {
            return 'Search value is required';
        }
    },
    onSuccess(data) {
        if (data.serial_no) {
            data.selected_serial_no = [data.serial_no];
        }
        if (!addItemIfExists(data)) {            
            addItemsResource.fetch({ search_value: JSON.stringify(data) });
        }
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

const addItemsResource = createResource({
    url: 'ant_pos.ant_pos.api.item.items',
    method: 'GET',
    makeParams(params) {
        return {
            pos_profile: store.posProfileData.name,
            search_value: params.search_value,
            customer: invoiceStore.invoiceCustomer?.name,
        };
    },
    validate(params) {
        if (!params.search_value) {
            return 'Search value is required';
        }
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
    onSuccess(data) {
        addItem(data);
        rememberScan(data);
    },
    transform(data){
        if (data.selected_serial_no && data.selected_serial_no.length > 0 ){
            data.selected_serial_no = data.selected_serial_no.map(serial=>({
                label:serial,
                value:serial
            }))
        }
        let  date=null
        let qty=0
        if (data.batch_no && data.batch_no.length > 0 && data.has_batch_no) {
            const batch = data.batch_nos.find(b => b.batch_no ===data.selected_batch_no);
            qty = batch ? batch.stock_qty : 0;
            date = batch ? batch.expiry_date : null;
            data.selected_batch_no = {
                label: data.batch_no,
                value: data.batch_no
            }
            
        }
        data.custom_id = Date.now() + Math.random();
        data.stock_qty = qty;
        data.expiry_date = date;
        data.net_rate = data.price_list_rate || 0
    }
});

const fetchSearchResource = () => {
    searchResource.fetch();
};

const addItem = (data) => {
    data.doctype = "Sales Invoice Item";
    data.parenttype = "Sales Invoice";
    data.custom_id = Date.now() + Math.random();
    if (!addItemIfExists(data)) {
        if (data.has_batch_no && data.batch_no) {
            data.serial_no_options = data.serial_no_options
                .filter(serial_no => data.batch_no && serial_no.batch_no === data.batch_no)
                .map(serial_no => ({
                    label: serial_no.serial_no,
                    value: serial_no.serial_no,
                }));
            data.use_serial_batch_fields=1;
        }
        addNewLine(data);
    }
};

const addItemIfExists = (data) => {
    let found = false;
    if (!store.posProfileData.custom_new_items_on_new_line) {
        invoiceStore.items.forEach((element, index) => {     
            if (!element.is_return && data.item_code === element.item_code &&
            ((data.has_batch_no && element.batch_no && data.batch_no === (element.batch_no.value || element.batch_no)) || !data.has_batch_no)) {
                found = true;
                
                if (data.has_serial_no && data.selected_serial_no && data.selected_serial_no.length > 0) {

                    for (let serial of data.selected_serial_no) {                        
                        let selected = element.selected_serial_no.map(serial=>serial.value)
                        if (selected.includes(serial)) {
                            showToast('warning', 'Serial-no Already added')
                            return found;
                        }
                    }
                    element.selected_serial_no.push({label:data.serial_no,value:data.serial_no})                    
                }
                if (element.serial_no  && !data.serial_no) {
                    showToast('warning', 'Batch already entered')
                    return found
                }
                invoiceStore.items[index].qty += 1;
                debounceSearch.value = '';
            }
        });
    }
    return found;
};

const addNewLine = async (data) => {
    invoiceStore.items.push(data);
    debounceSearch.value = '';
};

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
        for (const key in data) {
            if (key === 'items') continue;

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



onMounted(() => {
    emitter.on('fetchSearchResource', (params) => {
        searchResource.fetch(params)
    });

    emitter.on('calctotal', () => {
        calculateAmountTotal();
    });
    
    emitter.on('remove_invoice', (include_customer) => {
        remove_invoice(include_customer);
    });
})

</script> 