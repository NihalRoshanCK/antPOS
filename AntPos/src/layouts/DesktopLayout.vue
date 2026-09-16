<template>
  <div class="flex w-full h-full min-h-0 select-none bg-pos-page">
    <ItemSelector />
    <ItemDetail />
  </div>
</template>

<script setup>
import ItemSelector from '@/components/ItemSelector.vue'
import ItemDetail from '@/components/ItemDetail.vue'
</script>
