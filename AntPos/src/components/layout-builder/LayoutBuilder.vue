<template>
  <div class="flex min-w-0 flex-1 flex-col gap-3 lg:min-h-0 lg:flex-row">
    <!-- Palette: fields not on the form yet. -->
    <aside
      class="flex shrink-0 flex-col rounded-xl border border-outline-gray-1 bg-surface-white lg:w-64"
      aria-label="Available fields"
    >
      <div class="space-y-2 border-b border-outline-gray-1 p-3">
        <div class="flex items-center justify-between gap-2">
          <h3 class="text-sm font-semibold text-ink-gray-8">Fields</h3>
          <span class="num text-xs text-ink-gray-5">{{ available.length }}</span>
        </div>
        <TextInput v-model="search" type="search" size="sm" variant="subtle" placeholder="Search fields">
          <template #prefix><LucideSearch class="h-3.5 w-3.5 text-ink-gray-5" /></template>
        </TextInput>
        <p class="text-xs text-ink-gray-5">Drag a field into a column, or tap <span class="font-medium">+</span>.</p>
      </div>
      <div
        :key="`palette-${renderKey}`"
        v-sortable="paletteOptions"
        class="flex max-h-48 flex-col gap-1.5 overflow-y-auto p-2 pos-scroll lg:max-h-none lg:flex-1"
      >
        <div
          v-for="f in available"
          :key="f.fieldname"
          :data-field="f.fieldname"
          class="group flex cursor-grab items-center gap-2 rounded-lg border border-outline-gray-1 bg-surface-white px-2 py-1.5 hover:border-outline-gray-3 active:cursor-grabbing"
          :title="f.fieldname"
        >
          <LucideGripVertical class="h-3.5 w-3.5 shrink-0 text-ink-gray-4" />
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm text-ink-gray-8">
              {{ f.label }}<span v-if="f.reqd" class="text-ink-red-4"> *</span>
            </span>
            <span class="block truncate text-xs text-ink-gray-5">{{ f.fieldtype }}</span>
          </span>
          <button
            type="button"
            class="grid h-6 w-6 shrink-0 place-items-center rounded text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            :aria-label="`Add ${f.label}`"
            @click="addField(f.fieldname)"
          >
            <LucidePlus class="h-3.5 w-3.5" />
          </button>
        </div>
        <p v-if="!available.length" class="p-2 text-center text-xs text-ink-gray-5">
          {{ search ? 'No fields match.' : 'Every field is on the form.' }}
        </p>
      </div>
    </aside>

    <!-- Canvas -->
    <div class="flex min-w-0 flex-1 flex-col gap-3 lg:min-h-0 lg:overflow-y-auto pos-scroll">
      <div v-if="!sections.length" class="grid flex-1 place-items-center rounded-xl border border-dashed border-outline-gray-2 p-8 text-center">
        <div>
          <p class="text-base font-medium text-ink-gray-8">This form is empty</p>
          <p class="mt-1 text-sm text-ink-gray-5">Add a section, then drag fields into it.</p>
          <Button class="mt-3" variant="solid" @click="addSection">
            <template #prefix><LucidePlus class="h-4 w-4" /></template>
            Add section
          </Button>
        </div>
      </div>

      <div v-else :key="`canvas-${renderKey}`" ref="canvas" v-sortable="sectionOptions" class="flex flex-col gap-3">
        <section
          v-for="(section, s) in sections"
          :key="section.id"
          :data-section="section.id"
          class="rounded-xl border border-outline-gray-1 bg-surface-white"
        >
          <header class="flex flex-wrap items-center gap-2 border-b border-outline-gray-1 px-3 py-2">
            <button
              type="button"
              class="section-handle grid h-7 w-7 cursor-grab place-items-center rounded text-ink-gray-5 hover:bg-surface-gray-2 active:cursor-grabbing"
              aria-label="Drag to reorder section"
            >
              <LucideGripVertical class="h-4 w-4" />
            </button>
            <input
              v-model="section.label"
              class="pos-input h-7 min-w-0 flex-1 text-sm sm:max-w-xs"
              placeholder="Section title (optional)"
              :aria-label="`Section ${s + 1} title`"
              @change="emitChange"
            />
            <div class="ml-auto flex items-center gap-1">
              <Button size="sm" variant="ghost" :disabled="section.columns.length >= MAX_COLUMNS" @click="addColumn(s)">
                <template #prefix><LucideColumns2 class="h-3.5 w-3.5" /></template>
                Column
              </Button>
              <Button size="sm" variant="ghost" :aria-label="`Remove section ${s + 1}`" @click="removeSection(s)">
                <LucideTrash2 class="h-3.5 w-3.5" />
              </Button>
            </div>
          </header>

          <div class="grid gap-2 p-2" :class="COLUMN_GRID[section.columns.length]">
            <div
              v-for="(column, c) in section.columns"
              :key="column.id"
              class="flex min-w-0 flex-col rounded-lg bg-surface-gray-1"
            >
              <div class="flex items-center justify-between px-2 pt-1.5 text-xs text-ink-gray-5">
                <span>Column {{ c + 1 }}</span>
                <button
                  v-if="section.columns.length > 1"
                  type="button"
                  class="rounded px-1 hover:bg-surface-gray-3 hover:text-ink-gray-8"
                  @click="removeColumn(s, c)"
                >
                  Remove
                </button>
              </div>
              <div
                v-sortable="columnOptions"
                :data-column="column.id"
                class="relative flex min-h-[4.5rem] flex-1 flex-col gap-1.5 p-2"
              >
                <div
                  v-for="fieldname in column.fields"
                  :key="fieldname"
                  :data-field="fieldname"
                  class="group flex cursor-grab items-start gap-2 rounded-lg border bg-surface-white px-2 py-1.5 active:cursor-grabbing"
                  :class="overrides[fieldname]?.hidden ? 'border-dashed border-outline-gray-2 opacity-70' : 'border-outline-gray-1 hover:border-outline-gray-3'"
                >
                  <LucideGripVertical class="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-gray-4" />
                  <button
                    type="button"
                    class="min-w-0 flex-1 text-left focus:outline-none focus-visible:underline"
                    :aria-label="`${displayLabel(fieldname)}: settings`"
                    @click="editField(fieldname)"
                  >
                    <span class="block truncate text-sm text-ink-gray-8">{{ displayLabel(fieldname) }}</span>
                    <span class="num block truncate text-xs text-ink-gray-5">{{ fieldname }} · {{ meta[fieldname]?.fieldtype }}</span>
                    <span v-if="badges(fieldname).length" class="mt-1 flex flex-wrap gap-1">
                      <span
                        v-for="badge in badges(fieldname)"
                        :key="badge.label"
                        class="rounded px-1 text-[11px] leading-4"
                        :class="badge.class"
                      >{{ badge.label }}</span>
                    </span>
                  </button>
                  <button
                    type="button"
                    class="grid h-6 w-6 shrink-0 place-items-center rounded text-ink-gray-4 hover:bg-surface-gray-2 hover:text-ink-red-4 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                    :aria-label="`Remove ${displayLabel(fieldname)}`"
                    @click="removeField(fieldname)"
                  >
                    <LucideX class="h-3.5 w-3.5" />
                  </button>
                </div>
                <p
                  v-if="!column.fields.length"
                  class="pointer-events-none grid flex-1 place-items-center rounded-md border border-dashed border-outline-gray-2 text-xs text-ink-gray-4"
                >
                  Drop fields here
                </p>
              </div>
            </div>
          </div>
        </section>

        <Button class="self-start" @click="addSection">
          <template #prefix><LucidePlus class="h-4 w-4" /></template>
          Add section
        </Button>
      </div>
    </div>

    <FieldSettings
      v-model="settingsOpen"
      :field="editing ? meta[editing] : null"
      :override="editing ? overrides[editing] : {}"
      @apply="applySettings"
    />
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, TextInput } from 'frappe-ui'
import LucideSearch from '~icons/lucide/search'
import LucidePlus from '~icons/lucide/plus'
import LucideX from '~icons/lucide/x'
import LucideTrash2 from '~icons/lucide/trash-2'
import LucideGripVertical from '~icons/lucide/grip-vertical'
import LucideColumns2 from '~icons/lucide/columns-2'
import FieldSettings from '@/components/layout-builder/FieldSettings.vue'
import { vSortable } from '@/utils/sortable'

// Drag-and-drop editor for a server-driven form layout
// (see ant_pos/api/form_layout.py for the format).
const props = defineProps({
  // [{ fieldname, label, fieldtype, reqd, read_only, default }]
  fields: { type: Array, required: true },
  // [{ label, columns: [[fieldname | { fieldname, ...overrides }]] }]
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const MAX_COLUMNS = 4
const COLUMN_GRID = {
  1: 'grid-cols-1',
  2: 'grid-cols-1 sm:grid-cols-2',
  3: 'grid-cols-1 sm:grid-cols-3',
  4: 'grid-cols-1 sm:grid-cols-2 xl:grid-cols-4',
}

const meta = computed(() => Object.fromEntries(props.fields.map((f) => [f.fieldname, f])))

let nextId = 0
const uid = (prefix) => `${prefix}${++nextId}`

const sections = ref([])
const overrides = reactive({})
const search = ref('')
// Changing this re-creates the lists after a drag, so Vue owns the DOM again.
const renderKey = ref(0)
const canvas = ref(null)
let lastEmitted = null

function load(layout) {
  for (const key of Object.keys(overrides)) delete overrides[key]
  const seen = new Set()
  sections.value = (layout || []).map((section) => ({
    id: uid('s'),
    label: section.label || '',
    columns: (section.columns?.length ? section.columns : [[]]).map((column) => ({
      id: uid('c'),
      fields: column
        .map((entry) => {
          const { fieldname, ...rest } = typeof entry === 'string' ? { fieldname: entry } : entry
          if (!fieldname || !meta.value[fieldname] || seen.has(fieldname)) return null
          seen.add(fieldname)
          if (Object.keys(rest).length) overrides[fieldname] = rest
          return fieldname
        })
        .filter(Boolean),
    })),
  }))
  renderKey.value++
}

function toLayout() {
  return sections.value
    .map((section) => ({
      label: section.label.trim(),
      columns: section.columns.map((column) =>
        column.fields.map((fieldname) => {
          const o = overrides[fieldname]
          return o && Object.keys(o).length ? { fieldname, ...o } : fieldname
        })
      ),
    }))
    .filter((section) => section.label || section.columns.some((c) => c.length))
}

function emitChange() {
  lastEmitted = JSON.stringify(toLayout())
  emit('update:modelValue', JSON.parse(lastEmitted))
}

// Reload when the parent swaps the layout (another form, reset, discard),
// but not for the value this editor just emitted.
watch(
  () => [props.modelValue, props.fields],
  ([layout]) => {
    if (JSON.stringify(layout) === lastEmitted) return
    load(layout)
  },
  { immediate: true, deep: true }
)

const used = computed(() => new Set(sections.value.flatMap((s) => s.columns.flatMap((c) => c.fields))))

const available = computed(() => {
  const q = search.value.trim().toLowerCase()
  return props.fields.filter(
    (f) => !used.value.has(f.fieldname) && (!q || f.label.toLowerCase().includes(q) || f.fieldname.includes(q))
  )
})

function displayLabel(fieldname) {
  return overrides[fieldname]?.label || meta.value[fieldname]?.label || fieldname
}

function badges(fieldname) {
  const f = meta.value[fieldname] || {}
  const o = overrides[fieldname] || {}
  const list = []
  if (o.reqd || f.reqd) list.push({ label: 'Required', class: 'bg-surface-red-1 text-ink-red-4' })
  if (o.read_only || f.read_only) list.push({ label: 'Read only', class: 'bg-surface-gray-2 text-ink-gray-6' })
  if (o.hidden) list.push({ label: 'Hidden', class: 'bg-surface-amber-1 text-ink-amber-3' })
  if (o.default !== undefined && o.default !== '') list.push({ label: `= ${o.default}`, class: 'bg-surface-blue-1 text-ink-blue-3' })
  return list
}

// ---- drag and drop -------------------------------------------------------

// Rebuild state from the order Sortable left in the DOM.
function syncFromDom() {
  const byId = Object.fromEntries(sections.value.map((s) => [s.id, s]))
  const columnsById = Object.fromEntries(sections.value.flatMap((s) => s.columns.map((c) => [c.id, c])))
  const next = []
  for (const sectionEl of canvas.value?.querySelectorAll(':scope > [data-section]') || []) {
    const section = byId[sectionEl.dataset.section]
    if (!section) continue
    const columns = [...sectionEl.querySelectorAll('[data-column]')].map((columnEl) => ({
      ...columnsById[columnEl.dataset.column],
      fields: [...columnEl.querySelectorAll(':scope > [data-field]')].map((el) => el.dataset.field),
    }))
    next.push({ ...section, columns })
  }
  sections.value = next
  renderKey.value++
  emitChange()
}

const paletteOptions = {
  group: { name: 'layout-fields', pull: 'clone', put: false },
  sort: false,
  onEnd: (evt) => {
    if (evt.from !== evt.to) syncFromDom()
  },
}
const columnOptions = {
  group: { name: 'layout-fields', pull: true, put: true },
  draggable: '[data-field]',
  ghostClass: 'opacity-40',
  filter: 'button:not(:first-of-type)',
  preventOnFilter: false,
  onEnd: (evt) => {
    if (evt.from === evt.to && evt.oldIndex === evt.newIndex) return
    syncFromDom()
  },
}
const sectionOptions = {
  handle: '.section-handle',
  draggable: '[data-section]',
  onEnd: (evt) => {
    if (evt.oldIndex !== evt.newIndex) syncFromDom()
  },
}

// ---- buttons ---------------------------------------------------------------

function addSection() {
  sections.value.push({ id: uid('s'), label: '', columns: [{ id: uid('c'), fields: [] }] })
  renderKey.value++
  emitChange()
}

function removeSection(index) {
  sections.value.splice(index, 1)
  renderKey.value++
  emitChange()
}

function addColumn(index) {
  const section = sections.value[index]
  if (section.columns.length >= MAX_COLUMNS) return
  section.columns.push({ id: uid('c'), fields: [] })
  renderKey.value++
  emitChange()
}

function removeColumn(sectionIndex, columnIndex) {
  const columns = sections.value[sectionIndex].columns
  const [removed] = columns.splice(columnIndex, 1)
  // Keep its fields: they move to the neighbouring column.
  columns[Math.max(columnIndex - 1, 0)].fields.push(...removed.fields)
  renderKey.value++
  emitChange()
}

// "+" in the palette: into the last column of the last section.
function addField(fieldname) {
  if (!sections.value.length) addSection()
  const section = sections.value[sections.value.length - 1]
  section.columns[section.columns.length - 1].fields.push(fieldname)
  renderKey.value++
  emitChange()
}

function removeField(fieldname) {
  for (const section of sections.value) {
    for (const column of section.columns) column.fields = column.fields.filter((f) => f !== fieldname)
  }
  delete overrides[fieldname]
  renderKey.value++
  emitChange()
}

// ---- field settings --------------------------------------------------------

const editing = ref(null)
const settingsOpen = ref(false)

function editField(fieldname) {
  editing.value = fieldname
  settingsOpen.value = true
}

function applySettings(next) {
  if (Object.keys(next).length) overrides[editing.value] = next
  else delete overrides[editing.value]
  emitChange()
}
</script>
