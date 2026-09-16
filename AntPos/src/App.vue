<template>
  <div>
    <FrappeUIProvider>
      <div class="w-screen h-screen flex overflow-hidden select-none bg-surface-gray-1">
        <div v-if="currentComponent">
          <component :is="currentComponent" @switchComponent="loadComponent" />
        </div>
        <Sidebar />
        <!-- min-w-0 / min-h-0 let the panes inside actually scroll; the previous
             h-[94%] left a 6% gap and clipped the action bar at some heights. -->
        <div class="flex-1 flex flex-col min-w-0 min-h-0">
          <Navbar />
          <main class="flex-1 min-h-0 overflow-hidden">
            <router-view />
          </main>
        </div>
      </div>
    </FrappeUIProvider>
  </div>
</template>

<script setup>
import { FrappeUIProvider } from 'frappe-ui'
import { inject, watch, onMounted, onUnmounted } from 'vue';
import { useTheme } from '@/composables/useTheme';
import { usePosProfileStore } from '@/stores/posProfile';
import { usePageMeta } from 'frappe-ui';
import { getSettings } from '@/stores/settings';
import { useSessionStore } from '@/stores/session';
import Navbar from '@/components/Navbar.vue';
import Sidebar from '@/components/Sidebar.vue';

const { brand } = getSettings()
const { currentComponent, loadComponent } = inject('dynamicComponent');
const posProfileStore = usePosProfileStore();
const sessionStore = useSessionStore();
const { toggleTheme } = useTheme();

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
