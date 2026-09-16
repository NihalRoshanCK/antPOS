<template>
  <div class="shrink-0 bg-pos-readout text-white px-4 py-2.5 lg:py-3">
    <div class="flex items-end justify-between lg:justify-end gap-4 lg:gap-8">
      <dl class="flex gap-4 lg:gap-6 pb-0.5 lg:pb-1">
        <div>
          <dt class="text-[10px] lg:text-[11px] text-white/40">Items</dt>
          <dd class="text-[13px] lg:text-[15px] num text-white/80">{{ totalQty }}</dd>
        </div>
        <div>
          <dt class="text-[10px] lg:text-[11px] text-white/40">Net</dt>
          <dd class="text-[13px] lg:text-[15px] num text-white/80">{{ money(invoice.net_total) }}</dd>
        </div>
        <div class="hidden sm:block">
          <dt class="text-[10px] lg:text-[11px] text-white/40">Tax</dt>
          <dd class="text-[13px] lg:text-[15px] num text-white/80">{{ money(taxTotal) }}</dd>
        </div>
        <div v-if="discount" class="hidden sm:block">
          <dt class="text-[10px] lg:text-[11px] text-white/40">Discount</dt>
          <dd class="text-[13px] lg:text-[15px] num text-white/80">{{ money(discount) }}</dd>
        </div>
      </dl>

      <div class="text-right lg:border-l lg:border-white/15 lg:pl-8">
        <div class="text-[10px] lg:text-[11px] text-white/40">{{ isReturn ? 'Refund' : 'Total' }}</div>
        <div class="text-[30px] lg:text-[44px] leading-none lg:leading-[1.05] font-semibold num tracking-tight">
          {{ money(grandTotal) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useInvoiceStore } from '@/stores/pos'

const invoiceStore = useInvoiceStore()
const invoice = computed(() => invoiceStore.invoice || {})

const isReturn = computed(() => Boolean(invoice.value.is_return))
const grandTotal = computed(() => invoice.value.rounded_total || invoice.value.grand_total || 0)
const taxTotal = computed(() => invoice.value.total_taxes_and_charges || 0)
const discount = computed(() => invoice.value.discount_amount || 0)
const totalQty = computed(() => {
  const qty = invoice.value.total_qty
  return Number.isFinite(Number(qty)) ? Number(qty) : invoiceStore.items.length
})

function money(value) {
  return Number(value || 0).toFixed(2)
}
</script>
