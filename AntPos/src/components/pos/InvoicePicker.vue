<template>
  <div class="flex h-[min(65vh,36rem)] flex-col">
    <TextInput
      :model-value="search"
      type="text"
      size="md"
      variant="subtle"
      placeholder="Search by invoice or customer"
      @update:model-value="$emit('update:search', $event)"
    >
      <template #prefix><FeatherIcon class="w-4 text-ink-gray-5" name="search" /></template>
    </TextInput>

    <div
      class="-mx-1 mt-3 min-h-0 flex-1 overflow-y-auto pos-scroll px-1"
      role="radiogroup"
      :aria-label="ariaLabel"
    >
      <div v-if="loading && !invoices.length" class="space-y-2" aria-busy="true">
        <div v-for="n in 4" :key="n" class="h-16 animate-pulse rounded-lg bg-surface-gray-2" />
      </div>

      <div v-else-if="!invoices.length" class="grid h-full place-items-center px-6 text-center">
        <p class="text-sm text-ink-gray-5">{{ emptyText }}</p>
      </div>

      <ul v-else class="space-y-2">
        <li v-for="invoice in invoices" :key="invoice.name">
          <label
            class="flex min-h-[3.75rem] cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors"
            :class="modelValue === invoice.name
              ? 'border-outline-gray-4 bg-surface-gray-1'
              : 'border-outline-gray-1 hover:border-outline-gray-3'"
            @dblclick="$emit('confirm', invoice.name)"
          >
            <input
              type="radio"
              class="h-4 w-4 shrink-0 accent-[currentColor] text-ink-gray-9"
              :value="invoice.name"
              :checked="modelValue === invoice.name"
              @change="$emit('update:modelValue', invoice.name)"
            />
            <span class="min-w-0 flex-1">
              <span class="num block truncate text-sm font-medium text-ink-gray-9">{{ invoice.name }}</span>
              <span class="block truncate text-sm text-ink-gray-5">
                {{ invoice.customer }}<template v-if="invoice.posting_date"> · {{ invoice.posting_date }}</template>
              </span>
            </span>
            <span class="num shrink-0 text-base font-semibold text-ink-gray-9">
              {{ Number(invoice.grand_total || 0).toFixed(2) }}
            </span>
          </label>
        </li>
      </ul>
    </div>

    <div v-if="invoices.length && hasMore" class="pt-2 text-center">
      <Button variant="ghost" :loading="loading" @click="$emit('load-more')">Load more</Button>
    </div>
  </div>
</template>

<script setup>
import { Button, FeatherIcon, TextInput } from 'frappe-ui'

defineProps({
  invoices: { type: Array, default: () => [] },
  modelValue: { type: String, default: null },
  search: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: false },
  emptyText: { type: String, default: 'No invoices found.' },
  ariaLabel: { type: String, default: 'Invoices' },
})
defineEmits(['update:modelValue', 'update:search', 'confirm', 'load-more'])
</script>
