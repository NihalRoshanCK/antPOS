<template>
  <!-- Mobile backdrop -->
  <Transition
    enter-active-class="transition-opacity duration-150"
    leave-active-class="transition-opacity duration-150"
    enter-from-class="opacity-0"
    leave-to-class="opacity-0"
  >
    <div
      v-if="sidebarStore.isMobileOpen"
      class="fixed inset-0 z-40 bg-black/30 lg:hidden"
      aria-hidden="true"
      @click="sidebarStore.closeMobile()"
    />
  </Transition>

  <aside
    :class="[
      'z-50 flex h-full flex-col border-r border-outline-gray-1 bg-surface-menu-bar',
      'fixed inset-y-0 left-0 w-64 transition-transform duration-200 ease-out',
      sidebarStore.isMobileOpen ? 'translate-x-0 shadow-xl' : '-translate-x-full',
      'lg:static lg:translate-x-0 lg:shadow-none lg:transition-[width]',
      sidebarStore.isSidebarCollapsed ? 'lg:w-14' : 'lg:w-56',
    ]"
    aria-label="Main navigation"
  >
    <div class="p-2">
      <Dropdown :options="option" class="w-full">
        <template #default>
          <button
            type="button"
            class="flex w-full items-center gap-2 rounded-md p-1.5 hover:bg-surface-gray-3 focus:outline-none focus-visible:ring focus-visible:ring-outline-gray-3"
            :class="collapsed ? 'justify-center' : ''"
          >
            <img
              :src="brand.logo || '/assets/ant_pos/antPOS.png'"
              alt=""
              class="h-8 w-8 shrink-0 rounded-md object-contain"
            />
            <span v-if="!collapsed" class="min-w-0 flex-1 text-left">
              <span class="block truncate text-base font-semibold text-ink-gray-9">
                {{ brand.name || 'antPOS' }}
              </span>
              <span class="block truncate text-sm text-ink-gray-5">{{ currentUser.full_name }}</span>
            </span>
            <FeatherIcon v-if="!collapsed" name="chevron-down" class="h-4 w-4 shrink-0 text-ink-gray-5" />
          </button>
        </template>
      </Dropdown>
    </div>

    <nav class="flex flex-col gap-0.5 px-2 pt-2">
      <button
        v-for="link in links"
        :key="link.route"
        type="button"
        :title="collapsed ? link.label : undefined"
        class="flex h-9 items-center gap-2.5 rounded-md px-2.5 text-base focus:outline-none focus-visible:ring focus-visible:ring-outline-gray-3"
        :class="[
          currentRoute === link.route
            ? 'bg-surface-white text-ink-gray-9 font-medium shadow-sm'
            : 'text-ink-gray-6 hover:bg-surface-gray-3',
          collapsed ? 'justify-center' : '',
        ]"
        @click="go(link.route)"
      >
        <FeatherIcon :name="link.icon" class="h-4 w-4 shrink-0" />
        <span v-if="!collapsed">{{ link.label }}</span>
      </button>
    </nav>

    <div class="mt-auto hidden p-2 lg:block">
      <button
        type="button"
        class="flex h-8 w-full items-center gap-2 rounded-md px-2.5 text-sm text-ink-gray-5 hover:bg-surface-gray-3 focus:outline-none focus-visible:ring focus-visible:ring-outline-gray-3"
        :class="collapsed ? 'justify-center' : ''"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="sidebarStore.toggleCollapsed()"
      >
        <FeatherIcon :name="collapsed ? 'chevrons-right' : 'chevrons-left'" class="h-4 w-4" />
        <span v-if="!collapsed">Collapse</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { FeatherIcon, Dropdown } from 'frappe-ui';
import { useRouter } from 'vue-router';
import { inject, h, computed } from 'vue';
import { getSettings } from '@/stores/settings'
import { usersStore } from '@/stores/users';
import { useSidebar } from '@/stores/sidebar';
import { usePermissionStore } from '@/stores/permission';
import { useSessionStore } from '@/stores/session';

const sidebarStore = useSidebar()
const permissionStore = usePermissionStore();
const sessionStore = useSessionStore();
const router = useRouter();
const { brand } = getSettings()
const currentRoute = computed(() => router.currentRoute.value.name)
const { loadComponent } = inject('dynamicComponent');
const currentUser = computed(() => {
  if (!sessionStore.isLoggedIn) {
    return { full_name: 'Guest' }
  }
  return usersStore().getUser()
})

// The icon rail is a desktop affordance; the mobile drawer is always full width.
const collapsed = computed(() => sidebarStore.isSidebarCollapsed && !sidebarStore.isMobileOpen)

const links = computed(() => {
  const list = []
  if (permissionStore.salesInvoiceCanSubmit || permissionStore.salesInvoiceCanCreate || permissionStore.salesInvoiceCanPrint) {
    list.push({ route: 'Pos', label: 'Point of sale', icon: 'monitor' })
  }
  if (permissionStore.paymentEntryCanSubmit || permissionStore.paymentEntryCanCreate || permissionStore.paymentEntryCanPrint) {
    list.push({ route: 'Payments', label: 'Payments', icon: 'credit-card' })
  }
  return list
})

const go = (name) => {
  router.push({ name })
  sidebarStore.closeMobile()
}

const option=[
  {
    label: 'Close Shift',
    icon: () => h(FeatherIcon, { name: 'file-minus' }),
    onClick: () => {
      sidebarStore.closeMobile()
      loadComponent('CloseShift')
    },
  },
  {
    label: 'Desk',
    icon: () => h(FeatherIcon, { name: 'home' }),
    onClick: () => {
       window.location.href = '/app'
    },
  },
  {
    label: 'Settings',
    icon: () => h(FeatherIcon, { name: 'settings' }),
    onClick: () => {
      sidebarStore.closeMobile()
      loadComponent('Settings')
    },
  },  
  {
    label: 'Logout',
    icon: () => h(FeatherIcon, { name: 'log-out' }),
    onClick: () => {
      sessionStore.logout.fetch()
    },
  },
]

</script>

<style scoped>
  .adjust ::v-deep > div > div >div {
    width: 100%;
  }
</style>
