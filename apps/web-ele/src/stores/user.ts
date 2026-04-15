import { computed } from 'vue';
import { defineStore } from 'pinia';
import { updatePreferences, usePreferences } from '@vben/preferences';

export const useUserPreferenceStore = defineStore('user-preference', () => {
  const { isDark } = usePreferences();

  const isDarkMode = computed(() => isDark.value);

  function toggleTheme() {
    updatePreferences({
      theme: {
        mode: isDark.value ? 'light' : 'dark',
      },
    });
  }

  return {
    isDarkMode,
    toggleTheme,
  };
});
