import { defineStore } from 'pinia';
import { ref } from 'vue';
import { generateTempName, createDoctypeResource } from '@/utils';

export const useInvoiceStore = defineStore('salesInvoice', () => {
  const invoice = ref({});
  const items = ref([]);
  const invoiceCustomer = ref({});
  // This sale's "sales order" choice; null means use the POS Profile default.
  // Kept here rather than on the profile so it does not carry over to the
  // next sale (see composables/useSaleMode.js).
  const salesOrderChoice = ref(null);

  const invoiceResource = createDoctypeResource('Sales Invoice', (data) => {
    invoice.value = {
      ...data,
      name: generateTempName(data.doctype),
    };
  });

  function unmount() {
    invoice.value = {};
    items.value = [];
    invoiceCustomer.value = {};
    salesOrderChoice.value = null;
  }

  async function unmountAndRefresh(includeCustomer) {    
    invoice.value = {};
    items.value = [];
    salesOrderChoice.value = null;
    await invoiceResource.fetch();

    if (includeCustomer) {
      invoiceCustomer.value = {};
    }
  }

  return {
    invoice,
    items,
    invoiceCustomer,
    salesOrderChoice,
    invoiceResource,
    unmount,
    unmountAndRefresh,
  };
});
