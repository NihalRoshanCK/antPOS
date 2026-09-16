<template>
  <div class="shrink-0 bg-white border-b border-pos-line flex items-center gap-2 px-3 lg:px-4 h-14">
    <div class="flex-1 min-w-0">
      <Customer v-model:customer="model" />
    </div>
    <Button
      variant="subtle"
      theme="gray"
      class="!h-10 !w-10 shrink-0 !rounded-lg"
      aria-label="Create customer"
      @click="$emit('create')"
    >
      <FeatherIcon name="plus" class="w-4" />
    </Button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import Customer from '@/components/Customer.vue'

const props = defineProps({ customer: { type: Object, default: () => ({}) } })
const emit = defineEmits(['update:customer', 'create'])

const model = computed({
  get: () => props.customer,
  set: (v) => emit('update:customer', v),
})
</script>
