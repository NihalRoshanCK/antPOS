import './index.css'
import { createApp, reactive } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import translationPlugin from './translation'
import { useDynamicComponent } from './utils/Dialog';
import { handleStaleBuild, isStaleBuildError } from './utils/staleBuild';
import mitt from 'mitt';

import {
  Button,
  Card,
  Input,
  setConfig,
  frappeRequest,
  resourcesPlugin,
} from 'frappe-ui'


const app = createApp(App)

const emitter = mitt();

const pinia = createPinia()

setConfig('resourceFetcher', frappeRequest)

app.use(router)
app.use(resourcesPlugin)
app.use(translationPlugin)

app.component('Button', Button)
app.component('Card', Card)
app.component('Input', Input)

app.use(pinia)

app.provide('dynamicComponent', useDynamicComponent());

// Provide emitter it globally
app.provide('emitter', emitter);

app.mount('#app')

// A lazily loaded page or dialog whose file is gone means this tab predates
// the current build (see utils/staleBuild.js). Vite reports failed preloads
// here; the router reports failed page loads through onError.
// The event is not cancelled, so the import still rejects and the caller's
// own error handling runs as before.
window.addEventListener('vite:preloadError', () => handleStaleBuild())
router.onError((error) => {
  if (isStaleBuildError(error)) handleStaleBuild()
})
// Offline shell. The worker lives under /assets/ant_pos/antPOS/, so claiming the
// /antPOS/ scope needs the Service-Worker-Allowed header (docs/DEPLOYMENT.md).
// Without it the browser refuses the registration; the app works normally, it
// just has no offline shell, so there is nothing to surface to the cashier.
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/assets/ant_pos/antPOS/sw.js', { scope: '/antPOS/' })
      .catch((error) => {
        console.info('antPOS: offline mode unavailable -', error.message)
      })
  })
}
