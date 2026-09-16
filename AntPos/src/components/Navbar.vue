<template>
  <header class="flex h-12 shrink-0 items-center gap-3 border-b border-outline-gray-1 bg-surface-white px-3 lg:px-4">
    <button
      type="button"
      class="-ml-1 grid h-9 w-9 place-items-center rounded-md text-ink-gray-7 hover:bg-surface-gray-2 lg:hidden"
      aria-label="Open menu"
      @click="sidebarStore.openMobile()"
    >
      <FeatherIcon name="menu" class="h-5 w-5" />
    </button>

    <h1 class="truncate text-lg font-semibold text-ink-gray-9">{{ title }}</h1>

    <div class="ml-auto flex min-w-0 items-center gap-2">
      <Switch
        v-if="currentRoute === 'Pos' && store.posProfileData?.custom_create_sales_order"
        size="sm"
        label="Sales order"
        class="hidden sm:flex"
        v-model="createSalesOrder"
      />
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
import { Switch, Badge, FeatherIcon } from 'frappe-ui';
import { usePosProfileStore } from '@/stores/posProfile';
import { useInvoiceStore } from '@/stores/pos';

const store = usePosProfileStore();
const router = useRouter();
const invoiceStore = useInvoiceStore()

const currentRoute = computed(() => router.currentRoute.value.name)
import { useSidebar } from '@/stores/sidebar';
let sidebarStore = useSidebar()

const createSalesOrder = computed({
  get() {
    return store.posProfileData?.custom_set_sales_order === 1;
  },
  set(value) {
    if (store.posProfileData) {
      store.posProfileData.custom_set_sales_order = value ? 1 : 0;
    }
  },
});

const title = computed(() => ({ Pos: 'Point of sale', Payments: 'Payments' }[currentRoute.value] || currentRoute.value))

const badgeComponent = computed(() => {
  if (invoiceStore.invoice?.is_return) return { label: 'Return', theme: 'orange' };
  if (!invoiceStore.items.length) return { label: 'New sale', theme: 'green' };
  if (invoiceStore.invoice?.status) return { label: 'Draft', theme: 'blue' };
  return { label: 'Not saved', theme: 'gray' };
});

</script>
  