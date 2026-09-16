import { createDocumentResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

const settings = ref({})
const brand = reactive({})

// Created lazily. This module is imported (via App.vue) before main.js calls
// setConfig('resourceFetcher', frappeRequest), so a resource created at import
// time used frappe-ui's default fetcher, requested the relative URL
// /antPOS/frappe.client.get, got the SPA's HTML back, and the brand settings
// never loaded.
let setting = null

function setupBrand() {
  brand.name = settings.value?.brand_name
  brand.logo = settings.value?.brand_logo
  brand.favicon = settings.value?.favicon
}

function ensureResource() {
  if (!setting) {
    setting = createDocumentResource({
      doctype: 'AntPOS Settings',
      name: 'AntPOS Settings',
      onSuccess: (data) => {
        settings.value = data
        setupBrand()
        return data
      },
    })
  }
  return setting
}

export function getSettings() {
  return {
    setting: ensureResource(),
    settings,
    brand,
    setupBrand,
  }
}
