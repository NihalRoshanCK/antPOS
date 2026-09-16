<template>
  <!-- Same markup and classes as frappe-ui 0.1.278's SidebarItem. -->
  <Button
    variant="ghost"
    class="!w-full focus:outline-none focus-visible:ring-0"
    :class="isActive ? '!bg-surface-selected shadow-sm' : 'hover:bg-surface-gray-2'"
    :label="label"
    :aria-current="isActive ? 'page' : undefined"
    @click="$emit('click')"
  >
    <template #icon>
      <div class="flex w-full items-center justify-between px-2 py-1 transition-all ease-in-out">
        <div class="flex items-center truncate">
          <Tooltip :text="label" placement="right" :disabled="!isCollapsed">
            <span class="grid flex-shrink-0 place-items-center">
              <slot name="icon">
                <component :is="icon" v-if="icon" class="size-4 text-ink-gray-6" />
              </slot>
            </span>
          </Tooltip>
          <span
            class="flex-1 flex-shrink-0 truncate text-sm text-ink-gray-8 transition-all ease-in-out"
            :class="isCollapsed ? 'ml-0 w-0 overflow-hidden opacity-0' : 'ml-2 w-auto opacity-100'"
          >
            {{ label }}
          </span>
        </div>
        <div
          class="transition-all ease-in-out"
          :class="isCollapsed ? 'ml-0 w-0 overflow-hidden opacity-0' : 'ml-auto w-auto opacity-100'"
        >
          <slot name="suffix">
            <span v-if="suffix" class="text-sm text-ink-gray-4">{{ suffix }}</span>
          </slot>
        </div>
      </div>
    </template>
  </Button>
</template>

<script setup>
import { Button, Tooltip } from 'frappe-ui'

defineProps({
  label: { type: String, required: true },
  icon: { type: [Object, Function], default: null },
  suffix: { type: String, default: '' },
  isActive: { type: Boolean, default: false },
  isCollapsed: { type: Boolean, default: false },
})
defineEmits(['click'])
</script>
