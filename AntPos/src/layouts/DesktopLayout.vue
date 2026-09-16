<template>
  <div class="flex h-full w-full min-h-0 select-none gap-3 bg-surface-gray-1 p-3">
    <!-- Pay saves the invoice as a draft and flags it for payment; the left pane
         then switches from the item list to the payment panel. -->
    <Invoice v-if="paying" />
    <ItemSelector v-else />
    <ItemDetail :paying="paying" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ItemSelector from '@/components/ItemSelector.vue'
import ItemDetail from '@/components/ItemDetail.vue'
import Invoice from '@/components/Invoice.vue'
import { useInvoiceStore } from '@/stores/pos'

const invoiceStore = useInvoiceStore()
const paying = computed(() => Boolean(invoiceStore.invoice?.docstatus))
</script>
