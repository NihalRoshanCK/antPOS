<template>
  <!-- Stacked: scan on top, cart in the middle, totals and Pay at the bottom. -->
  <div class="flex h-full w-full min-h-0 select-none flex-col bg-surface-white">
    <ItemSelector compact />
    <ItemDetail compact />
  </div>
</template>

<script setup>
import ItemSelector from '@/components/ItemSelector.vue'
import ItemDetail from '@/components/ItemDetail.vue'
</script>
