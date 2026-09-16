<template>
  <!-- Stacked: scan on top where the caret lands, cart in the middle, totals and
       Pay pinned in the thumb zone. -->
  <div class="flex flex-col w-full h-full min-h-0 select-none bg-pos-page">
    <ItemSelector compact />
    <ItemDetail />
  </div>
</template>

<script setup>
import ItemSelector from '@/components/ItemSelector.vue'
import ItemDetail from '@/components/ItemDetail.vue'
</script>
