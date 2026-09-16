<template>
  <div>
    <div v-if="layout.loading && !layout.sections.length" class="grid gap-3" :class="gridClass(columnsHint)" aria-busy="true">
      <div v-for="n in columnsHint" :key="n" class="space-y-2">
        <div class="h-3 w-1/3 animate-pulse rounded bg-surface-gray-2" />
        <div class="h-8 animate-pulse rounded bg-surface-gray-2" />
      </div>
    </div>

    <div v-else-if="layout.error && !layout.sections.length" class="flex items-center justify-between gap-2 text-sm text-ink-red-4">
      <span>The form could not be loaded.</span>
      <Button size="sm" variant="subtle" @click="layout.load()">Try again</Button>
    </div>

    <div v-else class="space-y-4">
      <section v-for="(section, s) in layout.sections" :key="s" :aria-label="section.label || undefined">
        <h4 v-if="section.label" class="mb-2 text-sm font-medium text-ink-gray-7">{{ section.label }}</h4>
        <!-- Each layout column is a stack of fields; columns sit side by side
             and wrap on narrow screens. -->
        <div class="grid gap-x-4 gap-y-3" :class="gridClass(section.columns.length)">
          <div v-for="(column, c) in section.columns" :key="c" class="min-w-0 space-y-3">
            <FieldControl
              v-for="field in column"
              :key="field.fieldname"
              :field="field"
              :doc="doc"
              :override="overrides[field.fieldname] || {}"
              :show-errors="showErrors"
              :id-prefix="idPrefix"
            />
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import FieldControl from '@/components/form/FieldControl.vue'

// Renders a server-driven layout (see utils/formLayout.js) against `doc`.
defineProps({
  layout: { type: Object, required: true },
  doc: { type: Object, required: true },
  overrides: { type: Object, default: () => ({}) },
  showErrors: { type: Boolean, default: false },
  idPrefix: { type: String, default: 'f' },
  // Skeleton columns while the layout loads.
  columnsHint: { type: Number, default: 2 },
})

// Written out in full so Tailwind keeps them.
const GRID = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 sm:grid-cols-2',
  3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-2 lg:grid-cols-4',
}
function gridClass(n) {
  return GRID[Math.min(Math.max(n, 1), 4)] || GRID[4]
}
</script>
