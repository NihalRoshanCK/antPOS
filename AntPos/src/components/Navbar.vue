<template>
  <header class="flex h-12 shrink-0 items-center gap-3 border-b border-outline-gray-1 bg-surface-white px-3 lg:px-4">


    <h1 class="truncate text-lg font-semibold text-ink-gray-9">{{ title }}</h1>

    <div class="ml-auto flex min-w-0 items-center gap-2">
      <Badge
        v-if="currentRoute === 'Pos' && badgeComponent"
        :label="badgeComponent.label"
        :theme="badgeComponent.theme"
        variant="subtle"
        size="md"
      />
      <Badge
        v-if="store.posProfileData"
        variant="outline"
        theme="gray"
        size="md"
        class="hidden max-w-[14rem] truncate sm:inline-flex"
      >
        {{ store.posProfileData?.name }}
      </Badge>
    </div>
  </header>
</template>
  
<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { Badge } from 'frappe-ui';
import { useSaleMode } from '@/composables/useSaleMode';
import { usePosProfileStore } from '@/stores/posProfile';
import { useInvoiceStore } from '@/stores/pos';

const store = usePosProfileStore();
const router = useRouter();
const invoiceStore = useInvoiceStore()
const { asSalesOrder } = useSaleMode()

const currentRoute = computed(() => router.currentRoute.value.name)

const title = computed(() => ({ Pos: 'Point of sale', Payments: 'Payments', FormLayouts: 'Form layouts' }[currentRoute.value] || currentRoute.value))

const badgeComponent = computed(() => {
  if (invoiceStore.invoice?.is_return) return { label: 'Return', theme: 'orange' };
  if (!invoiceStore.items.length) return { label: asSalesOrder.value ? 'New order' : 'New sale', theme: 'green' };
  // A temp name (new-...) means the sale has never been saved. The status
  // alone is not enough: a fresh invoice already has status "Draft".
  const saved = !String(invoiceStore.invoice?.name || '').startsWith('new-');
  const kind = asSalesOrder.value ? 'Order' : '';
  if (saved) return { label: kind ? `${kind} · Draft` : 'Draft', theme: 'blue' };
  return { label: kind ? `${kind} · Not saved` : 'Not saved', theme: 'gray' };
});

</script>
  