// Custom logging utility
import logger from '@/common/helpers/logger';

// Import core libraries and app structure
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "@/App.vue";
import router from "@/router";

// Import custom global components
import components from '@/common/components/index.js';

// Vuetify styles and initialization
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import * as vuetifyComponents from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Create Vuetify instance with components and directives
const vuetify = createVuetify({
  components: vuetifyComponents,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
})

// Create Vue app instance
const app = createApp(App);

// Create and use Pinia store
const pinia = createPinia();
app.use(pinia);

// Use Vue Router for navigation
app.use(router);

// Use Vuetify UI framework
app.use(vuetify);

// Register custom global components
Object.entries(components).forEach(([name, component]) => {
  app.component(name, component);
});

// Mount the app to the DOM
app.mount("#app");

// Log environment variables for debugging
logger.info(`Loaded environment variables:`, import.meta.env);

router.afterEach((to) => {
  const defaultTitle = 'HyperspectRus'
  document.title = (to.meta.title ? `${to.meta.title} | ` : '') + defaultTitle

})
