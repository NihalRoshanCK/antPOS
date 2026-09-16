<template>
  <div class="flex h-full w-full min-h-0 select-none gap-3 bg-surface-gray-1 p-3">
    <ItemSelector />
    <ItemDetail />
  </div>
</template>

<script setup>
import ItemSelector from '@/components/ItemSelector.vue'
import ItemDetail from '@/components/ItemDetail.vue'
</script>
