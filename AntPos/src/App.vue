<template>
  <div>
    <FrappeUIProvider>
      <div class="flex h-[100dvh] w-screen overflow-hidden select-none bg-surface-gray-1">
        <div v-if="currentComponent">
          <component :is="currentComponent" @switchComponent="loadComponent" />
        </div>
        <!-- Desktop keeps the sidebar and navbar. Phones and tablets get a top bar
             and bottom tabs instead, so the content keeps the full width. -->
        <Sidebar v-if="isDesktop" />
        <div class="flex min-h-0 min-w-0 flex-1 flex-col">
          <Navbar v-if="isDesktop" />
          <MobileTopBar v-else />
          <main class="min-h-0 flex-1 overflow-hidden">
            <router-view />
          </main>
          <MobileTabBar v-if="!isDesktop && showTabBar" />
        </div>
        <MoreSheet v-if="!isDesktop" />
      </div>
    </FrappeUIProvider>
  </div>
</template>

<script setup>
import { FrappeUIProvider } from 'frappe-ui'
import { computed, inject, watch, onMounted, onUnmounted } from 'vue';
import { useTheme } from '@/composables/useTheme';
import { usePosProfileStore } from '@/stores/posProfile';
import { usePageMeta } from 'frappe-ui';
import { getSettings } from '@/stores/settings';
import { useSessionStore } from '@/stores/session';
import Navbar from '@/components/Navbar.vue';
import Sidebar from '@/components/Sidebar.vue';
import MobileTopBar from '@/components/mobile/MobileTopBar.vue';
import MobileTabBar from '@/components/mobile/MobileTabBar.vue';
import MoreSheet from '@/components/mobile/MoreSheet.vue';
import { useBreakpoint } from '@/composables/useBreakpoint';
import { useInvoiceStore } from '@/stores/pos';
import { useMobileView } from '@/stores/mobile';
import { useRoute } from 'vue-router';

const { brand } = getSettings()
const { currentComponent, loadComponent } = inject('dynamicComponent');
const posProfileStore = usePosProfileStore();
const sessionStore = useSessionStore();
const { toggleTheme } = useTheme();
const { isDesktop } = useBreakpoint();
const route = useRoute();
const invoiceStore = useInvoiceStore();
const mobile = useMobileView();

// The cart and payment screens have their own bottom actions (Pay, Submit) and
// a back arrow; the tabs would only compete with them.
const showTabBar = computed(() => {
  if (route.name !== 'Pos') return true;
  return mobile.view === 'items' && !invoiceStore.invoice?.docstatus;
});

// Ctrl/Cmd+Shift+G switches between light and dark, as in the desk.
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'g') {
    e.preventDefault();
    toggleTheme();
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown));
onUnmounted(() => window.removeEventListener('keydown', onKeydown));

usePageMeta(() => {
  return {
    icon: brand.favicon ? brand.favicon : '/assets/ant_pos/antPOS.png',
  }
})

watch(
  () => posProfileStore.hasNoData,
  (val) => {

    if (val && sessionStore.isLoggedIn) {
      loadComponent('OpenShift')
    } 
  }
)
</script>
