<template>
  <Dialog v-model="open" :options="{ title: 'Switch Theme', size: 'xl' }">
    <template #body-content>
      <div
        role="radiogroup"
        aria-label="Theme"
        class="grid grid-cols-1 gap-4 sm:grid-cols-3"
        @keydown.left.prevent="move(-1)"
        @keydown.right.prevent="move(1)"
        @keydown.enter.prevent="open = false"
      >
        <button
          v-for="(theme, i) in themes"
          :key="theme.mode"
          ref="cards"
          type="button"
          role="radio"
          :aria-checked="mode === theme.mode"
          :tabindex="mode === theme.mode ? 0 : -1"
          :title="theme.info"
          class="group flex flex-col justify-start rounded-lg text-left focus:outline-none"
          @click="choose(theme.mode, i)"
        >
          <!-- Preview. Each half carries its own data-theme so the card renders
               in that scheme regardless of the page's current one. -->
          <div
            class="relative overflow-hidden rounded-lg border-2 transition-colors"
            :class="mode === theme.mode
              ? 'border-outline-gray-5'
              : 'border-outline-gray-1 group-hover:border-outline-gray-3 group-focus-visible:border-outline-gray-3'"
          >
            <div class="flex h-28">
              <ThemePreview :scheme="theme.mode === 'automatic' ? 'light' : theme.mode"
                :class="theme.mode === 'automatic' ? 'w-1/2' : 'w-full'" />
              <ThemePreview v-if="theme.mode === 'automatic'" scheme="dark" class="w-1/2" />
            </div>
            <span
              v-if="mode === theme.mode"
              class="absolute right-2 top-2 grid h-5 w-5 place-items-center rounded-full bg-surface-gray-7 text-ink-white"
            >
              <LucideCheck class="h-3 w-3" />
            </span>
          </div>
          <p class="mt-2 text-center text-base font-medium text-ink-gray-8">{{ theme.label }}</p>
          <p class="text-center text-sm text-ink-gray-5">{{ theme.info }}</p>
        </button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { Dialog, toast } from 'frappe-ui'
import LucideCheck from '~icons/lucide/check'
import ThemePreview from '@/components/Dialog/ThemePreview.vue'
import { useTheme } from '@/composables/useTheme'

const open = ref(true)
const cards = ref([])
const { mode, setTheme } = useTheme()

// Labels match the desk's switcher.
const themes = [
  { mode: 'light', label: 'Frappe Light', info: 'Light theme' },
  { mode: 'dark', label: 'Timeless Night', info: 'Dark theme' },
  { mode: 'automatic', label: 'Automatic', info: 'Matches your device' },
]

async function choose(next, index) {
  if (next === mode.value) return
  cards.value[index]?.focus()
  try {
    await setTheme(next)
    toast.create({ title: 'Theme changed', position: 'top-center', timeout: 3 })
  } catch {
    toast.create({
      title: 'Theme applied here only',
      message: 'It could not be saved to your account, so the desk keeps its own setting.',
      position: 'top-center',
      timeout: 6,
    })
  }
}

function move(step) {
  const i = themes.findIndex((t) => t.mode === mode.value)
  const next = themes[i + step]
  if (next) choose(next.mode, i + step)
}

onMounted(async () => {
  await nextTick()
  const i = themes.findIndex((t) => t.mode === mode.value)
  cards.value[i]?.focus()
})
</script>
