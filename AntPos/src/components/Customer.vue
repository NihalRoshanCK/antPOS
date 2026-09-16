<template>
  <div class="w-full">
    <Autocomplete
      :options="computedOptions"
      v-model="selectedCustomer"
      placeholder="Select Customer"
      @update:query="onQuery"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch, defineProps } from 'vue';
import emitter from '@/utils/emitter';
import Autocomplete from '@/components/custom_components/Autocomplete.vue';
import { createListResource, debounce } from 'frappe-ui';
import { createToast } from '@/utils';
import { usePosProfileStore } from '@/stores/posProfile';
import { useInvoiceStore } from '@/stores/pos';

const emit = defineEmits(['update:customer']);

const props = defineProps({
    // Not `required`: the parent legitimately holds {} before a customer is
    // picked, and the Autocomplete clear button hands back null.
    customer: {
        type: Object,
        default: () => ({}),
    },
});

const posProfileStore = usePosProfileStore();
const invoiceStore = useInvoiceStore();

// How many customers to pull per request. The list is searched server-side, so
// this is a page of results, not the whole table.
const PAGE_LENGTH = 20;

const customerGroups = computed(
  () => posProfileStore.posProfileData?.customer_groups?.map((item) => item.customer_group) || []
);

const toOption = (item) => ({
  label: item.name || 'Unnamed',
  value: item.name,
  name: item.name,
  mobile_no: item.mobile_no || '',
  customer_group: item.customer_group,
  territory: item.territory,
  is_internal_customer: item.is_internal_customer,
});

const buildFilters = (query) => {
  const filters = { disabled: false };

  // The POS Profile restricts which customer groups a cashier may sell to.
  // This was previously snapshotted at resource-creation time, before the
  // profile had loaded, so it was always empty and every customer was visible.
  if (customerGroups.value.length) {
    filters.customer_group = ['in', customerGroups.value];
  }

  if (query) {
    filters.name = ['like', `%${query}%`];
  }

  return filters;
};

const customerResource = createListResource({
  doctype: 'Customer',
  fields: ['name', 'mobile_no', 'customer_group', 'territory', 'is_internal_customer'],
  filters: buildFilters(''),
  orderBy: 'modified desc',
  pageLength: PAGE_LENGTH,
  auto: false,
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
  transform: (data) => data.map(toOption),
});

const search = (query) => {
  // Search by name or mobile number. Frappe ORs `orFilters` among themselves and
  // ANDs the result with `filters`, so the group restriction still applies.
  customerResource.update({
    filters: buildFilters(''),
    orFilters: query
      ? [
          ['name', 'like', `%${query}%`],
          ['mobile_no', 'like', `%${query}%`],
        ]
      : [],
  });
  customerResource.reload();
};

const onQuery = debounce(search, 300);

const computedOptions = computed(() => customerResource.data || []);

const refreshCustomerList = async (params) => {
  await customerResource.reload();
  selectedCustomer.value = toOption(params);
};

onMounted(() => {
  emitter.on('customerCreated', refreshCustomerList);
  customerResource.reload();
});

onUnmounted(() => {
  emitter.off('customerCreated', refreshCustomerList);
});

const selectedCustomer = computed({
  // The Autocomplete wants null for "nothing selected"; the stores want {}.
  // Translate at this boundary so a cleared customer can never reach a consumer
  // as null -- that is what blanked the Payments page (issue #57).
  get: () => (props.customer && props.customer.name ? props.customer : null),
  set: (newVal) => {
    if (invoiceStore.invoice.is_return) return;
      emit('update:customer', newVal || {});
      emitter.emit('calctotal');
      emitter.emit('clear', false);
  },
});

// Reload once the POS profile arrives: the customer-group restriction depends on
// it. The previous version passed the unwrapped boolean rather than a getter, so
// this never fired after the initial run.
watch(
  () => posProfileStore.hasNoData,
  () => customerResource.reload()
);

watch(customerGroups, () => search(''));
</script>
