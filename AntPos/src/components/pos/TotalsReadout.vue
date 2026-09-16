<template>
  <div class="flex items-end justify-between gap-4">
    <dl class="flex min-w-0 flex-wrap gap-x-5 gap-y-1 text-sm">
      <div>
        <dt class="text-ink-gray-5">Items</dt>
        <dd class="num text-base font-medium text-ink-gray-8">{{ totalQty }}</dd>
      </div>
      <div>
        <dt class="text-ink-gray-5">Net</dt>
        <dd class="num text-base font-medium text-ink-gray-8">{{ money(invoice.net_total) }}</dd>
      </div>
      <div>
        <dt class="text-ink-gray-5">Tax</dt>
        <dd class="num text-base font-medium text-ink-gray-8">{{ money(taxTotal) }}</dd>
      </div>
      <div v-if="discount">
        <dt class="text-ink-gray-5">Discount</dt>
        <dd class="num text-base font-medium text-ink-green-3">&minus;{{ money(discount) }}</dd>
      </div>
    </dl>

    <div class="shrink-0 text-right">
      <div class="text-sm text-ink-gray-5">{{ isReturn ? 'Refund' : 'Total' }}</div>
      <div
        class="num text-3xl font-semibold leading-tight tracking-tight lg:text-4xl"
        :class="isReturn ? 'text-ink-red-4' : 'text-ink-gray-9'"
      >
        <span class="mr-1 text-lg font-medium text-ink-gray-5 lg:text-xl">{{ currency }}</span>{{ money(grandTotal) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useInvoiceStore } from '@/stores/pos'
import { usePosProfileStore } from '@/stores/posProfile'

const invoiceStore = useInvoiceStore()
const profileStore = usePosProfileStore()
const invoice = computed(() => invoiceStore.invoice || {})

const currency = computed(() => invoice.value.currency || profileStore.posProfileData?.currency || '')
const isReturn = computed(() => Boolean(invoice.value.is_return))
const grandTotal = computed(() => invoice.value.rounded_total || invoice.value.grand_total || 0)
const taxTotal = computed(() => invoice.value.total_taxes_and_charges || 0)
const discount = computed(() => invoice.value.discount_amount || 0)
const totalQty = computed(() => {
  const qty = Number(invoice.value.total_qty)
  return Number.isFinite(qty) && qty ? qty : invoiceStore.items.length
})

function money(value) {
  return Number(value || 0).toFixed(2)
}
</script>
