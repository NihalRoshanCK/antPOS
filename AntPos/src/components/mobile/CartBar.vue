<template>
  <div class="shrink-0 border-t border-outline-gray-1 bg-surface-white px-3 py-2">
    <button
      type="button"
      class="flex h-12 w-full items-center gap-3 rounded-lg px-4 text-left transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      :class="count
        ? 'bg-surface-gray-7 text-ink-white active:opacity-90'
        : 'cursor-default bg-surface-gray-2 text-ink-gray-5'"
      :disabled="!count"
      :aria-label="count ? `View cart, ${count} ${count === 1 ? 'item' : 'items'}, total ${total}` : 'Cart is empty'"
      @click="mobile.showCart()"
    >
      <span class="relative">
        <LucideShoppingCart class="h-5 w-5" />
        <span
          v-if="count"
          :key="count"
          class="num absolute -right-2.5 -top-2 grid h-4 min-w-4 place-items-center rounded-full bg-surface-green-3 px-1 text-[10px] font-semibold text-ink-white animate-[pos-pop_200ms_ease-out]"
        >
          {{ count }}
        </span>
      </span>
      <span class="flex-1 text-base font-medium">
        {{ count ? (count === 1 ? '1 item' : `${count} items`) : 'Cart is empty' }}
      </span>
      <span v-if="count" class="num text-base font-semibold">{{ total }}</span>
      <LucideChevronRight v-if="count" class="h-5 w-5 opacity-70" />
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import LucideShoppingCart from '~icons/lucide/shopping-cart'
import LucideChevronRight from '~icons/lucide/chevron-right'
import { useInvoiceStore } from '@/stores/pos'
import { useMobileView } from '@/stores/mobile'

const invoiceStore = useInvoiceStore()
const mobile = useMobileView()

// Units, not lines: two of the same item count as two.
const count = computed(() =>
  invoiceStore.items.reduce((sum, line) => sum + Math.abs(Number(line.qty) || 0), 0)
)
// The server total (with taxes and rounding) arrives a moment after each
// change. Until it reflects the current lines, show the lines' own sum rather
// than a stale or zero figure.
const total = computed(() => {
  const inv = invoiceStore.invoice || {}
  const serverTotal = Number(inv.rounded_total || inv.grand_total || 0)
  const serverQty = Math.abs(Number(inv.total_qty) || 0)
  if (serverTotal && serverQty === count.value) return serverTotal.toFixed(2)
  const lines = invoiceStore.items.reduce((sum, line) => sum + Math.abs(lineAmount(line)), 0)
  return lines.toFixed(2)
})

// `amount` is filled by the cart line or the server; a line added from the
// item grid has neither yet.
function lineAmount(line) {
  const amount = Number(line.amount)
  if (amount) return amount
  return (Number(line.qty) || 0) * (Number(line.rate ?? line.price_list_rate) || 0)
}
</script>
