import { defineStore } from 'pinia'
import { ref } from 'vue'

function readCollapsed() {
	try {
		return JSON.parse(localStorage.getItem('isSidebarCollapsed')) === true
	} catch {
		return false
	}
}

export const useSidebar = defineStore('sidebar', () => {
	// Desktop only: narrow icon rail vs full sidebar. Persisted per browser.
	const isSidebarCollapsed = ref(readCollapsed())

	// Mobile only: the off-canvas drawer. Never persisted -- it must start
	// closed. Sharing isSidebarCollapsed for this is what left the sidebar
	// pinned open over the whole app on phones.
	const isMobileOpen = ref(false)

	function toggleCollapsed() {
		isSidebarCollapsed.value = !isSidebarCollapsed.value
		try {
			localStorage.setItem('isSidebarCollapsed', JSON.stringify(isSidebarCollapsed.value))
		} catch {
			// storage unavailable (private mode); the toggle still works for this session
		}
	}

	function openMobile() {
		isMobileOpen.value = true
	}

	function closeMobile() {
		isMobileOpen.value = false
	}

	return { isSidebarCollapsed, isMobileOpen, toggleCollapsed, openMobile, closeMobile }
})
