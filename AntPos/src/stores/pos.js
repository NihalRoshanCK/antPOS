import { defineStore } from 'pinia';
import { reactive } from 'vue';
import { generateTempName, createDoctypeResource } from '@/utils';

export const useInvoiceStore = defineStore('salesInvoice', () => {
  const invoice = reactive({});
  const items = reactive([]);
  const invoiceCustomer = reactive({});

  const invoiceResource = createDoctypeResource('Sales Invoice', (data) => {
    Object.assign(invoice, {
      ...data,
      name: generateTempName(data.doctype),
    });
  });

  function unmount() {
    Object.keys(invoice).forEach(key => delete invoice[key]);
    items.length = 0;
    Object.keys(invoiceCustomer).forEach(key => delete invoiceCustomer[key]);
    console.log(invoice,"lllll");
    
  }

  async function unmountAndRefresh(includeCustomer) {
    unmount();
    await invoiceResource.fetch();
    if (includeCustomer) {
      Object.keys(invoiceCustomer).forEach(key => delete invoiceCustomer[key]);
    }
  }

  async function updateInvoice(incomingInvoice) {
    for (const key in incomingInvoice) {
      const existingValue = invoice[key];
      const newValue = incomingInvoice[key];

      if (JSON.stringify(existingValue) !== JSON.stringify(newValue)) {
        invoice[key] = newValue;
      }
    }
  }

  return {
    invoice,
    items,
    invoiceCustomer,
    invoiceResource,
    unmount,
    unmountAndRefresh,
    updateInvoice,
  };
});
