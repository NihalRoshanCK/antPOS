import { createDocumentResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

const settings = ref({})
const brand = reactive({})

const setting = createDocumentResource({
  doctype: 'AntPOS Settings',
  name: 'AntPOS Settings',
  onSuccess: (data) => {
    console.log("jjjfjfj");
    
    settings.value = data
    getSettings().setupBrand()
    return data
  },
   transform(doc) {
    console.log("wkfiewijfeij");
    
    return doc
  },
})

export function getSettings() {
  function setupBrand() {
    brand.name = settings.value?.brand_name
    brand.logo = settings.value?.brand_logo
    brand.favicon = settings.value?.favicon
  }

  return {
    setting,
    settings,
    brand,
    setupBrand,
  }
}
