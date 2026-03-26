import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const STORAGE_KEY = 'logiswarm-theme'
  
  const THEMES = {
    LIGHT: 'light',
    DARK: 'dark',
    SYSTEM: 'system'
  }
  
  const preference = ref(THEMES.SYSTEM)
  const systemDark = ref(false)
  
  function getSystemPreference() {
    if (typeof window === 'undefined') return false
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  }
  
  function getStoredPreference() {
    if (typeof window === 'undefined') return THEMES.SYSTEM
    const stored = localStorage.getItem(STORAGE_KEY)
    return Object.values(THEMES).includes(stored) ? stored : THEMES.SYSTEM
  }
  
  function setStoredPreference(value) {
    if (typeof window === 'undefined') return
    localStorage.setItem(STORAGE_KEY, value)
  }
  
  function isDark() {
    if (preference.value === THEMES.DARK) return true
    if (preference.value === THEMES.LIGHT) return false
    return systemDark.value
  }
  
  function applyTheme() {
    if (typeof window === 'undefined') return
    
    const dark = isDark()
    const root = document.documentElement
    
    if (dark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }
  
  function setTheme(theme) {
    if (!Object.values(THEMES).includes(theme)) return
    preference.value = theme
    setStoredPreference(theme)
    applyTheme()
  }
  
  function toggleTheme() {
    const next = preference.value === THEMES.DARK 
      ? THEMES.LIGHT 
      : THEMES.DARK
    setTheme(next)
  }
  
  function cycleTheme() {
    const cycle = [THEMES.SYSTEM, THEMES.LIGHT, THEMES.DARK]
    const currentIndex = cycle.indexOf(preference.value)
    const nextIndex = (currentIndex + 1) % cycle.length
    setTheme(cycle[nextIndex])
  }
  
  function init() {
    preference.value = getStoredPreference()
    systemDark.value = getSystemPreference()
    applyTheme()
    
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      
      mediaQuery.addEventListener('change', (e) => {
        systemDark.value = e.matches
        applyTheme()
      })
    }
  }
  
  watch(preference, () => {
    applyTheme()
  })
  
  return {
    THEMES,
    preference,
    systemDark,
    isDark,
    setTheme,
    toggleTheme,
    cycleTheme,
    init
  }
})