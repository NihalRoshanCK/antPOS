<template>
  <!-- Mirrors frappe-ui 0.1.278's Sidebar (header dropdown, ghost-button items,
       bg-surface-selected active state, fading labels, panel-right-open toggle).
       Ported rather than imported: the installed frappe-ui is 0.1.177, whose
       Sidebar is an older revision, and upgrading frappe-ui touches every
       component this app uses. -->
  <aside
    class="flex h-full flex-shrink-0 flex-col overflow-y-auto overflow-x-hidden border-r border-outline-gray-1 bg-surface-menu-bar p-2 transition-all duration-300 ease-in-out"
    :class="shouldCollapse ? 'w-12' : 'w-60'"
    aria-label="Main navigation"
  >
    <!-- Header -->
    <Dropdown :options="menuItems">
      <template v-slot="{ open }">
        <button
          type="button"
          class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
          :class="
            shouldCollapse
              ? 'w-auto px-0'
              : open
                ? 'w-[14rem] bg-surface-white px-2 shadow-sm'
                : 'w-[14rem] px-2 hover:bg-surface-gray-3'
          "
        >
          <div class="h-8 w-8 flex-shrink-0 overflow-hidden rounded">
            <img
              :src="brand.logo || '/assets/ant_pos/antPOS.png'"
              class="h-full w-full object-cover"
              alt=""
            />
          </div>
          <div
            class="flex flex-1 flex-col truncate text-left duration-300 ease-in-out"
            :class="shouldCollapse ? 'ml-0 w-0 overflow-hidden opacity-0' : 'ml-2 w-auto opacity-100'"
          >
            <div class="truncate text-base font-medium leading-none text-ink-gray-8">
              {{ brand.name || 'antPOS' }}
            </div>
            <div class="mt-1 truncate text-sm leading-none text-ink-gray-6">
              {{ currentUser.full_name }}
            </div>
          </div>
          <div
            class="duration-300 ease-in-out"
            :class="shouldCollapse ? 'ml-0 w-0 overflow-hidden opacity-0' : 'ml-2 w-auto opacity-100'"
          >
            <LucideChevronDown class="h-4 w-4 text-ink-gray-7" />
          </div>
        </button>
      </template>
    </Dropdown>

    <!-- Section -->
    <nav class="mt-2 flex flex-col space-y-0.5">
      <SidebarLink
        v-for="link in links"
        :key="link.route"
        :label="link.label"
        :icon="link.icon"
        :is-active="currentRoute === link.route"
        :is-collapsed="shouldCollapse"
        @click="router.push({ name: link.route })"
      />
    </nav>

    <!-- Footer -->
    <div v-if="!forceCollapse" class="mt-auto flex flex-col gap-2">
      <SidebarLink
        :label="shouldCollapse ? 'Expand' : 'Collapse'"
        :is-collapsed="shouldCollapse"
        @click="sidebarStore.toggleCollapsed()"
      >
        <template #icon>
          <LucidePanelRightOpen
            class="size-4 text-ink-gray-6 duration-300 ease-in-out"
            :class="{ 'rotate-180': shouldCollapse }"
          />
        </template>
      </SidebarLink>
    </div>
  </aside>
</template>

<script setup>
import { Dropdown } from 'frappe-ui'
import { useRouter } from 'vue-router'
import { inject, computed, markRaw } from 'vue'
import { getSettings } from '@/stores/settings'
import { usersStore } from '@/stores/users'
import { useSidebar } from '@/stores/sidebar'
import { usePermissionStore } from '@/stores/permission'
import { useSessionStore } from '@/stores/session'
import { useBreakpoint } from '@/composables/useBreakpoint'
import SidebarLink from '@/components/SidebarLink.vue'

import LucideChevronDown from '~icons/lucide/chevron-down'
import LucidePanelRightOpen from '~icons/lucide/panel-right-open'
import LucideMonitor from '~icons/lucide/monitor'
import LucideCreditCard from '~icons/lucide/credit-card'
import LucideFileMinus from '~icons/lucide/file-minus'
import LucideLayoutGrid from '~icons/lucide/layout-grid'
import LucideSettings from '~icons/lucide/settings'
import LucideLogOut from '~icons/lucide/log-out'

const sidebarStore = useSidebar()
const permissionStore = usePermissionStore()
const sessionStore = useSessionStore()
const router = useRouter()
const { brand } = getSettings()
const { loadComponent } = inject('dynamicComponent')
const { isDesktop } = useBreakpoint()

const currentRoute = computed(() => router.currentRoute.value.name)

const currentUser = computed(() => {
  if (!sessionStore.isLoggedIn) return { full_name: 'Guest' }
  return usersStore().getUser()
})

// frappe-ui collapses to the icon rail below `sm`. The POS switches to its
// stacked layout below `lg`, and a 240px sidebar leaves too little room for it
// there, so the rail is forced for the whole mobile layout.
const forceCollapse = computed(() => !isDesktop.value)
const shouldCollapse = computed(() => forceCollapse.value || sidebarStore.isSidebarCollapsed)

const links = computed(() => {
  const list = []
  if (permissionStore.salesInvoiceCanSubmit || permissionStore.salesInvoiceCanCreate || permissionStore.salesInvoiceCanPrint) {
    list.push({ route: 'Pos', label: 'Point of sale', icon: markRaw(LucideMonitor) })
  }
  if (permissionStore.paymentEntryCanSubmit || permissionStore.paymentEntryCanCreate || permissionStore.paymentEntryCanPrint) {
    list.push({ route: 'Payments', label: 'Payments', icon: markRaw(LucideCreditCard) })
  }
  return list
})

const menuItems = [
  { label: 'Close shift', icon: markRaw(LucideFileMinus), onClick: () => loadComponent('CloseShift') },
  { label: 'Go to desk', icon: markRaw(LucideLayoutGrid), onClick: () => { window.location.href = '/app' } },
  { label: 'Settings', icon: markRaw(LucideSettings), onClick: () => loadComponent('Settings') },
  { label: 'Log out', icon: markRaw(LucideLogOut), onClick: () => sessionStore.logout.fetch() },
]
</script>
