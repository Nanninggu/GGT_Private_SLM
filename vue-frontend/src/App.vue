<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from './stores/theme';

const authStore = useAuthStore()
const themeStore = useThemeStore();

onMounted(() => {
  themeStore.initializeTheme();
  // 토큰이 있으면 자동 갱신 시도
  if (authStore.token && authStore.refreshToken) {
    // 토큰 만료 체크 및 갱신 로직은 필요시 구현
  }
})
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>
