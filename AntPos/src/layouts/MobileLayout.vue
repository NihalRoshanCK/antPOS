<template>
  <!-- Stacked: scan on top, cart in the middle, totals and Pay at the bottom.
       While paying, the payment panel takes the whole screen. -->
  <div class="flex h-full w-full min-h-0 select-none flex-col bg-surface-white">
    <Invoice v-if="paying" compact />
    <template v-else>
      <ItemSelector compact />
      <ItemDetail compact />
    </template>
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
