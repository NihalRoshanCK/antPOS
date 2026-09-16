<template>
    <article
        :class="[
            'lg:border-b lg:border-outline-gray-1 lg:rounded-none',
            'border rounded-xl lg:bg-transparent bg-surface-white',
            items.custom_open ? 'border-outline-gray-3 lg:bg-surface-gray-1' : 'border-outline-gray-1',
        ]"
    >
        <!-- Desktop: a real grid, so Qty/Rate/Amount line up down the column. -->
        <div class="hidden lg:grid grid-cols-[1fr_84px_96px_112px_32px] gap-3 px-4 py-3 items-center">
            <button
                type="button"
                class="min-w-0 text-left flex items-center gap-2 focus:outline-none focus-visible:underline"
                :aria-expanded="Boolean(items.custom_open)"
                @click="items.custom_open = !items.custom_open"
            >
                <FeatherIcon
                    :name="items.custom_open ? 'chevron-down' : 'chevron-right'"
                    class="w-4 h-4 shrink-0 text-ink-gray-5"
                />
                <span class="min-w-0">
                    <span class="block text-[14px] font-medium truncate">{{ items.item_name || items.item_code }}</span>
                    <span class="block text-[12px] text-ink-gray-5 num truncate">{{ lineMeta }}</span>
                </span>
            </button>
            <div class="text-right num text-[14px]">{{ items.qty }}</div>
            <div class="text-right num text-[14px]">{{ Number(items.rate || 0).toFixed(2) }}</div>
            <div class="text-right num text-[14px] font-semibold">{{ Number(items.amount || 0).toFixed(2) }}</div>
            <button
                type="button"
                class="justify-self-end text-ink-gray-5 hover:text-ink-red-4 focus:outline-none focus-visible:text-ink-red-4"
                :aria-label="`Remove ${items.item_code}`"
                @click="invoiceStore.items.splice(index, 1)"
            >
                <FeatherIcon name="trash-2" class="w-4 h-4" />
            </button>
        </div>

        <!-- Mobile: a card with a stepper. Columns do not fit, and the qty
             control has to be thumb-sized. -->
        <div class="lg:hidden p-3">
            <div class="flex items-start gap-3">
                <button
                    type="button"
                    class="flex-1 min-w-0 text-left focus:outline-none"
                    :aria-expanded="Boolean(items.custom_open)"
                    @click="items.custom_open = !items.custom_open"
                >
                    <span class="block text-[15px] font-medium leading-snug">{{ items.item_name || items.item_code }}</span>
                    <span class="block text-[12px] text-ink-gray-5 num mt-0.5 truncate">{{ lineMeta }}</span>
                </button>
                <span class="text-[16px] font-semibold num shrink-0">{{ Number(items.amount || 0).toFixed(2) }}</span>
            </div>
            <div class="flex items-center gap-2 mt-3">
                <div class="flex items-center border border-outline-gray-1 rounded-lg overflow-hidden bg-surface-white">
                    <button type="button" class="w-11 h-11 grid place-items-center text-ink-gray-6 active:bg-surface-gray-2"
                            aria-label="Decrease quantity" @click="step(-1)">
                        <FeatherIcon name="minus" class="w-4 h-4" />
                    </button>
                    <span class="w-12 text-center num text-[16px] font-medium">{{ items.qty }}</span>
                    <button type="button" class="w-11 h-11 grid place-items-center text-ink-gray-6 active:bg-surface-gray-2"
                            aria-label="Increase quantity" @click="step(1)">
                        <FeatherIcon name="plus" class="w-4 h-4" />
                    </button>
                </div>
                <span class="text-[13px] text-ink-gray-5 num">&times; {{ Number(items.rate || 0).toFixed(2) }}</span>
                <button type="button" class="ml-auto w-11 h-11 grid place-items-center text-ink-gray-5 active:text-ink-red-4"
                        :aria-label="`Remove ${items.item_code}`" @click="invoiceStore.items.splice(index, 1)">
                    <FeatherIcon name="trash-2" class="w-4 h-4" />
                </button>
            </div>
        </div>
        <div v-if="items.custom_open" class="space-y-3 border-t border-outline-gray-1 px-3 py-3 lg:px-4">
            <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <FormControl type="number" size="md" variant="subtle" label="Quantity"
                    v-model="items.qty" />
                <FormControl type="number" size="md" variant="subtle" label="Rate"
                    :disabled="!store.posProfileData?.allow_rate_change"
                    v-model="items.rate" />
                <FormControl type="number" size="md" variant="subtle" label="Discount (%)"
                    :disabled="store.posProfileData?.allow_discount_change === 0"
                    v-model="items.discount_percentage" />
                <div>
                    <p class="mb-1.5 text-base text-ink-gray-5">Discount amount</p>
                    <p class="num flex h-8 items-center text-base text-ink-gray-8">{{ Number(items.discount_amount || 0).toFixed(2) }}</p>
                </div>
            </div>

            <!-- Only for batch-tracked lines. These used to render on every item,
                 plain ones included, and the two info fields were editable. -->
            <div v-if="isBatched" class="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <div class="col-span-2">
                    <Autocomplete
                        :options="getbatchNo()"
                        label="Batch"
                        placeholder="Select batch"
                        :disabled="invoiceStore.invoice.is_return"
                        v-model="items.selected_batch_no"
                        :hideSearch="true"
                    />
                </div>
                <div>
                    <p class="mb-1.5 text-base text-ink-gray-5">Available</p>
                    <p class="num flex h-8 items-center text-base text-ink-gray-8">{{ items.stock_qty ?? '—' }}</p>
                </div>
                <div>
                    <p class="mb-1.5 text-base text-ink-gray-5">Expires</p>
                    <p class="num flex h-8 items-center text-base text-ink-gray-8">{{ items.expiry_date || '—' }}</p>
                </div>
            </div>

            <div v-if="isSerialised">
                <Autocomplete
                    :options="get_serial_no_options()"
                    label="Serial numbers"
                    placeholder="Select serial numbers"
                    :multiple="true"
                    v-model="items.selected_serial_no"
                />
                <p class="mt-1 text-xs text-ink-gray-5">
                    {{ (items.selected_serial_no || []).length }} selected of {{ serialNoQty || (items.serial_no_options || []).length }} in stock
                </p>
            </div>

            <p class="num text-xs text-ink-gray-5">
                Price list {{ Number(items.price_list_rate || 0).toFixed(2) }}
                <template v-if="items.item_group"> · {{ items.item_group }}</template>
            </p>
        </div>
    </article>
</template>
<script setup>
import { FeatherIcon, FormControl, Autocomplete, createResource, createListResource,debounce } from 'frappe-ui';
import { watch, defineProps, onMounted, onUnmounted, computed } from 'vue';
import { showToast } from '@/utils'
import emitter from '@/utils/emitter';
import { usePosProfileStore } from '@/stores/posProfile';
import { useInvoiceStore } from '@/stores/pos';

const store = usePosProfileStore();
const invoiceStore = useInvoiceStore()

    
const props = defineProps({
    items: {
        type: Object,
        required: true,
    },
    index: {
        type: Number,
        required: true,
    },
});

const SERIAL_NO_PAGE_LENGTH = 500;

const serialNoQty = computed(() => props.items?.serial_no_options?.length || 0);

// One quiet line under the item name carrying whatever identifies this line:
// code, UOM, batch, expiry, serial. Beats five separate read-only fields.
const lineMeta = computed(() => {
    const item = props.items || {};
    const parts = [item.item_code];

    if (item.uom && item.uom !== item.item_code) parts.push(item.uom);
    if (item.batch_no) parts.push(`Batch ${item.batch_no}`);
    if (item.expiry_date) parts.push(`exp ${item.expiry_date}`);

    const serials = (item.selected_serial_no || []).map((s) => s.value ?? s);
    if (serials.length === 1) parts.push(`SN ${serials[0]}`);
    else if (serials.length > 1) parts.push(`${serials.length} serials`);

    return parts.filter(Boolean).join(' \u00b7 ');
});

// Held drafts and returns come back from the server without the has_* flags,
// so fall back to whether the line already carries a batch or serial.
const isBatched = computed(() => Boolean(props.items.has_batch_no || props.items.batch_no));
const isSerialised = computed(() => Boolean(props.items.has_serial_no || props.items.serial_no));

const step = (delta) => {
    const next = Number(props.items.qty || 0) + delta;
    // Returns carry negative quantities; never let a stepper cross zero.
    if (invoiceStore.invoice.is_return) {
        if (next > -1) return;
    } else if (next < 1) {
        return;
    }
    props.items.qty = next;
};

const get_batch = createResource({
    url: 'ant_pos.ant_pos.api.item.get_batches_list',
    method: 'POST',
    auto: false,
    makeParams(params) {
        return {
            ...params
        }
    }
});


const get_serial_no = createListResource({
    url: 'frappe.client.get_list',
    method: 'POST',
    auto: false,
    doctype: 'Serial No',
    fields: ['name as serial_no', 'batch_no'],
    filters: {
        warehouse: store.posProfileData.warehouse,
        item_code: props.items.item_code,
    },
    // A single POS line never needs more serials than this; fetching the whole
    // Serial No table per cart row was the single worst query in the app.
    pageLength: SERIAL_NO_PAGE_LENGTH,
    onSuccess(data) {            
        props.items.serial_no_options = data.map((serial_no) => ({
            label: serial_no.serial_no,
            value: serial_no.serial_no,
            batch_no: serial_no.batch_no
        }));
    },
});

const get_serial_no_options = () => {
    let serials = []
    const { has_batch_no, batch_no } = props.items;
    if (invoiceStore.invoice.is_return){
        serials=props.items._serial || []
        return serials.map(serial_no => ({
            label: serial_no,
            value: serial_no,
        }));
    }
    serials = get_serial_no.data || [];

    if (props.items.batch_no != null && !invoiceStore.invoice.is_return) {
        serials = serials.filter(serial_no => serial_no.batch_no === props.items.batch_no);
    }
    
    return serials.map(serial_no => ({
        label: serial_no.serial_no,
        value: serial_no.serial_no,
    }));
};

const validateInvoice = () => {
    emitter.emit('calctotal');
}

const getbatchNo =  () => {
    if (invoiceStore.invoice.is_return) {
        return [{
            label: props.items.batch_no,
            value: props.items.batch_no,
        }];
    }    
    return (get_batch.data || []).map((batch) => ({
        label: batch.batch_no,
        value: batch.batch_no,
    }));
};

watch(
    () => props.items.selected_batch_no,
    (newBatchNo, oldBatchNo) => {        
        
        if (newBatchNo && (newBatchNo.value !== oldBatchNo?.value) || !oldBatchNo) {
            
            let find = validateitems();
            const option = get_serial_no_options();
            if (!find && option.length > 0) {
                props.items.selected_serial_no = [];
                props.items.serial_no_options = props.items.serial_no_options.filter((serial_no) => serial_no.batch_no == newBatchNo)
                    .map((serial_no) => ({
                        label: serial_no.serial_no,
                        value: serial_no.serial_no,
                    }));
                add_serial_no();
            }

            const batch = (get_batch.data || []).find(b => b.batch_no === newBatchNo);
            props.items.stock_qty = batch ? batch.stock_qty : 0;
            props.items.expiry_date = batch ? batch.expiry_date : null;
            props.items.batch_no = typeof newBatchNo === 'object' ? newBatchNo?.value : newBatchNo;
            validateInvoice();
        
        }
    }
);

const validateitems = () => {
    if (!store.posProfileData.custom_new_items_on_new_line) {
        let find = false;
        for (let index = 0; index < invoiceStore.items.length; index++) {
            if (props.index !== index && invoiceStore.items[props.index].item_code === invoiceStore.items[index].item_code &&
                ((invoiceStore.items[props.index].has_batch_no && invoiceStore.items[props.index].batch_no === invoiceStore.items[index].batch_no && !invoiceStore.items[props.index].is_return) || 
                !invoiceStore.items[props.index].has_batch_no)) { 
                    invoiceStore.items.selected_serial_no= mergeSerial_no(invoiceStore.items[props.index].selected_serial_no,invoiceStore.items[index].selected_serial_no)
                    invoiceStore.items.splice(props.index, 1);
                    find = true;
                    return find;
            }
        }
        return find;
    }
};

const mergeSerial_no = (left, right) => {
    const leftValues = left.map(sn => sn.value);
    const rightValues = right.map(sn => sn.value);
    const mergedValues = [...new Set([...leftValues, ...rightValues])];
    return mergedValues.map(serial => ({ label: serial, value: serial }));
};

const calculateAmountTotal = () => {
    props.items.amount = Math.abs(props.items.qty) * props.items.rate
};


const validateQty = () => {
    if (props.items.serial_no_options) {
        const options = get_serial_no_options()
        if (options.length > 0 && props.items.qty > options.length) {
            showToast('warning', 'Qty is greater than available serial no', 'alert-circle', '#ffcc00','#ffffff')
            props.items.qty = invoiceStore.invoice.is_return ?  -Math.abs(options.length) : options.length;
        }   
    }
    return;
};

const add_serial_no = () =>{  
    props.items.serial_no = props.items.selected_serial_no.map(sn => sn.value).join('\n');
}

watch(
    () => props.items.selected_serial_no,
    (newValue, oldValue) => {
        if (((props.items.serial_no_options && newValue !== oldValue) || !oldValue)) {
            add_serial_no()
            adjustQtyNumbers(props.items.qty)
        }
    }
);

watch(
    () => props.items.price_list_rate,
    (newValue, oldValue) => {
        if (props.items.price_list_rate && newValue !== oldValue) {
            props.items.rate = props.items.price_list_rate -  (props.items.price_list_rate * props.items.discount_percentage)/100;
        }
    }
);

watch(
    () => props.items.qty,
    (newValue, oldValue)=>  {
        if (newValue !== oldValue)  {
            // Keep the line amount right locally; it previously only updated on
            // a rate change and otherwise waited for the server recalculation.
            calculateAmountTotal();
            const option= get_serial_no_options()
            if (option.length > 0){
                adjustSerialNumbers(newValue);
                validateQty()
                add_serial_no()
            }
            validateInvoice();
        }
    }
);

const adjustQtyNumbers = () =>{
    const options = get_serial_no_options();
    if (options.length < 0 ) return;
    const qty = props.items.qty
    const serialLength = props.items.selected_serial_no.length
    if (qty!=serialLength){
        props.items.qty = invoiceStore.invoice.is_return ?  -Math.abs(serialLength) : serialLength;
    }    
}

const adjustSerialNumbers = (newQty) => {
    const options = get_serial_no_options();
    if (options.length < 0 ) return;
    const selected = props.items.selected_serial_no;
    const selectedLength = selected.length;
    if (Math.abs(selectedLength) === Math.abs(newQty))return;     
    if (Math.abs(selectedLength) > Math.abs(newQty)) {
        props.items.selected_serial_no = selected.slice(0, newQty);
    }
    else if (Math.abs(selectedLength) < Math.abs(newQty)) {
        const selectedValues = new Set(selected.map(sn => sn.value));        
        const needed = newQty - selectedLength;
        const additional = [];
        for (let i = 0; i < options.length && additional.length < needed; i++) {
            const opt = options[i];
            if (!selectedValues.has(opt.value)) {
                additional.push(opt);
            }
        }
        props.items.selected_serial_no = JSON.parse(JSON.stringify([...selected, ...additional]));
    }
};

watch(
    () => props.items.discount_percentage,
    (newValue, oldValue) => {
        if (Number(newValue) !== Number(oldValue) || !oldValue) {
            discountCalculation();
        }
    }
);

const discountCalculation =() => {
    props.items.rate = rateCalculation(props.items);
    validateInvoice();
}

const  rateCalculation =  (item) => {
    const rate =  Number(item.price_list_rate) ;
    const discount = Number(item.discount_percentage) || 0;
    return rate - (rate * (discount / 100));
};

watch(
    () => props.items.rate,
    (newValue, oldValue) => {
        if (Number(newValue) !== Number(oldValue)) {
            props.items.base_rate = Number(newValue)
            props.items.margin_rate_or_amount = 0
            calculateRateTotal();
        }
    }
);

const calculateRateTotal = () => {
    calculateAmountTotal();
    props.items.discount_amount = props.items.price_list_rate - props.items.rate
    validateInvoice();
}

onMounted( async () => {
    calculateRateTotal();
    validateQty(props.items.qty);
    if(props.items.selected_serial_no) adjustSerialNumbers(props.items.selected_serial_no.length); 
    if(props.items.selected_serial_no) add_serial_no();

    // Only ask for batches and serials when the item is actually tracked. This
    // ran unconditionally for every cart line, so a 20-line sale fired 40
    // requests, nearly all of them for data that cannot exist.
    const lookups = [];
    if (isBatched.value) {
        lookups.push(get_batch.fetch({
            item_code: props.items.item_code,
            warehouse: store.posProfileData.warehouse,
        }));
    }
    if (isSerialised.value) {
        lookups.push(get_serial_no.fetch());
    }
    if (lookups.length) await Promise.all(lookups);

    validateInvoice();
});
 
onUnmounted(() => {    
    calculateAmountTotal();
    validateInvoice();
});

</script>
