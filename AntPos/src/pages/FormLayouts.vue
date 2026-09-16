<template>
  <!-- Phones scroll the whole page; desktop keeps panes that scroll inside. -->
  <div class="flex h-full min-h-0 min-w-0 flex-col gap-3 overflow-y-auto p-3 pos-scroll lg:overflow-hidden lg:p-4">
    <div v-if="!allowed" class="grid flex-1 place-items-center text-center">
      <div>
        <p class="text-base font-medium text-ink-gray-8">Only a System Manager can change form layouts.</p>
        <Button class="mt-3" @click="router.push({ name: 'Pos' })">Back to point of sale</Button>
      </div>
    </div>

    <template v-else>
      <!-- Which form, its state, and the actions. -->
      <div class="flex flex-wrap items-center gap-2">
        <TabButtons
          v-if="forms.data?.length"
          :buttons="forms.data.map((f) => ({ label: f.title, value: formKey(f) }))"
          :model-value="selectedKey"
          @update:model-value="selectForm"
        />
        <Badge
          v-if="selected"
          :label="selected.customised ? 'Customised' : 'Built-in'"
          :theme="selected.customised ? 'blue' : 'gray'"
          variant="subtle"
        />
        <Badge v-if="dirty" label="Unsaved changes" theme="orange" variant="subtle" />

        <div class="ml-auto flex flex-wrap items-center gap-2">
          <Button v-if="selected?.customised" :loading="reset.loading" @click="confirmReset">
            <template #prefix><LucideRotateCcw class="h-4 w-4" /></template>
            Reset to built-in
          </Button>
          <Button :disabled="!dirty" @click="discard">Discard</Button>
          <Button variant="solid" :disabled="!dirty" :loading="save.loading" @click="save.submit()">
            <template #prefix><LucideSave class="h-4 w-4" /></template>
            Save
          </Button>
        </div>
      </div>
      <p v-if="selected" class="-mt-1 text-sm text-ink-gray-5">
        {{ selected.description }}
        <template v-if="selected.type === 'Quick Entry'">Fields the document requires are added automatically.</template>
      </p>

      <!-- Phones: one pane at a time. -->
      <TabButtons
        v-if="!isDesktop && selected"
        class="self-start"
        :buttons="[{ label: 'Design', value: 'design' }, { label: 'Preview', value: 'preview' }]"
        v-model="pane"
      />

      <div v-if="editor.loading && !editor.data" class="grid flex-1 place-items-center text-sm text-ink-gray-5">Loading…</div>
      <div v-else-if="editor.error" class="grid flex-1 place-items-center text-sm text-ink-red-4">
        {{ errorText(editor.error) }}
      </div>

      <div v-else-if="editor.data" class="flex min-w-0 flex-1 flex-col gap-3 lg:min-h-0 lg:flex-row">
        <LayoutBuilder
          v-show="isDesktop || pane === 'design'"
          v-model="draft"
          :fields="editor.data.fields"
        />

        <!-- Live preview: the unsaved layout, resolved by the server exactly
             as the POS will receive it. -->
        <aside
          v-show="isDesktop || pane === 'preview'"
          class="flex min-h-0 w-full shrink-0 flex-col rounded-xl border border-outline-gray-1 bg-surface-white lg:w-[22rem] xl:w-[26rem]"
          aria-label="Preview"
        >
          <div class="flex items-center justify-between border-b border-outline-gray-1 px-3 py-2">
            <h3 class="text-sm font-semibold text-ink-gray-8">Preview</h3>
            <span class="text-xs text-ink-gray-5">{{ preview.loading ? 'Updating…' : 'As the cashier sees it' }}</span>
          </div>
          <div class="min-h-0 flex-1 overflow-y-auto p-4 pos-scroll">
            <p v-if="previewError" class="text-sm text-ink-red-4">{{ previewError }}</p>
            <template v-else>
              <h4 class="mb-3 text-base font-semibold text-ink-gray-9">{{ selected?.type === 'Quick Entry' ? 'New customer' : 'Sample item' }}</h4>
              <LayoutForm
                :layout="previewLayout"
                :doc="sampleDoc"
                :overrides="previewOverrides"
                id-prefix="preview"
                :columns-hint="2"
              />
            </template>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { Badge, Button, TabButtons, createResource, debounce } from 'frappe-ui'
import LucideSave from '~icons/lucide/save'
import LucideRotateCcw from '~icons/lucide/rotate-ccw'
import LayoutBuilder from '@/components/layout-builder/LayoutBuilder.vue'
import LayoutForm from '@/components/form/LayoutForm.vue'
import { usePermissionStore } from '@/stores/permission'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { LOCKED_LINE_FIELDS, applyDefaults, refreshFormLayouts } from '@/utils/formLayout'
import { createToast } from '@/utils'

const API = 'ant_pos.ant_pos.api.form_layout'
const router = useRouter()
const permissions = usePermissionStore()
const { isDesktop } = useBreakpoint()
const allowed = computed(() => permissions.canManageLayouts)

const formKey = (f) => `${f.doctype}|${f.type}`
const selectedKey = ref('')
const pane = ref('design')

const forms = createResource({
  url: `${API}.get_editable_forms`,
  auto: false,
  onSuccess(list) {
    if (!selectedKey.value && list.length) selectedKey.value = formKey(list[0])
  },
})
watch(allowed, (ok) => ok && !forms.data && forms.fetch(), { immediate: true })

const selected = computed(() => forms.data?.find((f) => formKey(f) === selectedKey.value) || null)

// ---- editing ---------------------------------------------------------------

const draft = ref([])
const saved = ref('[]')
const dirty = computed(() => JSON.stringify(draft.value) !== saved.value)

const editor = createResource({
  url: `${API}.get_layout_for_editing`,
  makeParams: () => ({ doctype: selected.value.doctype, type: selected.value.type }),
  onSuccess(data) {
    draft.value = data.sections
    saved.value = JSON.stringify(data.sections)
  },
})
watch(selected, (form, before) => {
  if (form && formKey(form) !== (before && formKey(before))) editor.fetch()
})

function selectForm(key) {
  if (key === selectedKey.value) return
  if (dirty.value && !window.confirm('Discard the unsaved changes to this form?')) return
  selectedKey.value = key
}

function discard() {
  draft.value = JSON.parse(saved.value)
}

const save = createResource({
  url: `${API}.save_form_layout`,
  makeParams: () => ({ doctype: selected.value.doctype, type: selected.value.type, layout: JSON.stringify(draft.value) }),
  onSuccess(data) {
    draft.value = data.sections
    saved.value = JSON.stringify(data.sections)
    forms.reload()
    // This tab uses the new layout straight away; others on their next focus.
    refreshFormLayouts()
    createToast({ title: 'Layout saved', message: 'Cashiers see it the next time they open the form.', type: 'success' })
  },
  onError: (error) => createToast({ title: 'Could not save', message: errorText(error), type: 'error' }),
})

const reset = createResource({
  url: `${API}.reset_form_layout`,
  makeParams: () => ({ doctype: selected.value.doctype, type: selected.value.type }),
  onSuccess(data) {
    draft.value = data.sections
    saved.value = JSON.stringify(data.sections)
    forms.reload()
    refreshFormLayouts()
    createToast({ title: 'Back to the built-in layout', type: 'success' })
  },
  onError: (error) => createToast({ title: 'Could not reset', message: errorText(error), type: 'error' }),
})

function confirmReset() {
  if (window.confirm('Remove the custom layout and use the built-in one?')) reset.submit()
}

onBeforeRouteLeave(() => !dirty.value || window.confirm('Leave without saving the layout?'))

// ---- preview ---------------------------------------------------------------

const previewLayout = reactive({ sections: [], loading: false, error: null, load: () => runPreview() })
const previewError = ref('')
const sampleDoc = reactive({})

const preview = createResource({
  url: `${API}.preview_form_layout`,
  makeParams: () => ({
    doctype: selected.value.doctype,
    type: selected.value.type,
    parent_doctype: selected.value.parent_doctype,
    layout: JSON.stringify(draft.value),
  }),
  onSuccess(data) {
    previewError.value = ''
    previewLayout.sections = data.sections
    resetSample()
  },
  onError: (error) => (previewError.value = errorText(error)),
})

const runPreview = debounce(() => selected.value && preview.submit(), 300)
watch(draft, runPreview, { deep: true })

// A plausible record to render against, so the preview is not all blanks.
function resetSample() {
  for (const key of Object.keys(sampleDoc)) delete sampleDoc[key]
  if (selected.value?.doctype === 'Sales Invoice Item') {
    Object.assign(sampleDoc, {
      item_code: 'ITEM-001', item_name: 'Sample item', qty: 1, rate: 100, price_list_rate: 100,
      discount_percentage: 0, discount_amount: 0, amount: 100, uom: 'Nos', warehouse: 'Stores',
    })
  }
  applyDefaults(previewLayout.sections, sampleDoc)
}

// Cart lines lock these in the POS (components/Item.vue).
const previewOverrides = computed(() =>
  selected.value?.doctype === 'Sales Invoice Item'
    ? Object.fromEntries(LOCKED_LINE_FIELDS.map((f) => [f, { readOnly: true }]))
    : {}
)

function errorText(error) {
  const m = error?.messages
  return (Array.isArray(m) ? m[0] : m) || error?.message || 'Something went wrong.'
}
</script>
