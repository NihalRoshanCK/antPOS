<template>
  <!-- A miniature of the POS in one scheme: sidebar, navbar, two panels and
       the green Pay button. -->
  <div :data-theme="scheme" class="flex h-full bg-surface-gray-1">
    <div class="w-4 shrink-0 border-r border-outline-gray-1 bg-surface-menu-bar"></div>
    <div class="flex min-w-0 flex-1 flex-col">
      <div class="h-3 shrink-0 border-b border-outline-gray-1 bg-surface-white"></div>
      <div class="flex flex-1 gap-1 p-1">
        <div class="w-1/3 rounded-sm border border-outline-gray-1 bg-surface-white p-1">
          <div class="h-1.5 rounded-sm bg-surface-gray-2"></div>
        </div>
        <div class="flex flex-1 flex-col rounded-sm border border-outline-gray-1 bg-surface-white p-1">
          <div class="h-1.5 w-2/3 rounded-sm bg-surface-gray-3"></div>
          <div class="mt-1 h-1.5 w-1/2 rounded-sm bg-surface-gray-2"></div>
          <div class="mt-auto ml-auto h-2 w-1/3 rounded-sm bg-surface-green-3"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ scheme: { type: String, required: true } })
</script>
