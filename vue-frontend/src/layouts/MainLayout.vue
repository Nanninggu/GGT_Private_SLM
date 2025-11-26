<template>
  <el-container class="h-screen">
    <el-aside width="260px" class="bg-background border-r border-border">
      <div class="h-full flex flex-col">
        <!-- Logo -->
        <div class="p-4 border-b border-border flex justify-between items-center">
          <h1 class="text-xl font-bold text-foreground">Hi-Chat</h1>
          <ThemeToggle />
        </div>

        <!-- Navigation -->
        <el-menu
          :default-active="activeMenu"
          class="flex-1 border-0"
          :collapse="false"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/">
            <el-icon><ChatDotRound /></el-icon>
            <span>채팅</span>
          </el-menu-item>
          <el-menu-item index="/sessions">
            <el-icon><Document /></el-icon>
            <span>세션</span>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon><FolderOpened /></el-icon>
            <span>문서</span>
          </el-menu-item>
          <el-menu-item index="/collections">
            <el-icon><Collection /></el-icon>
            <span>데이터셋</span>
          </el-menu-item>
          <el-menu-item index="/web-search">
            <el-icon><Search /></el-icon>
            <span>웹 검색</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>개발자 도구</span>
          </el-menu-item>
        </el-menu>

        <!-- User Info -->
        <div class="p-4 border-t border-border">
          <el-tooltip content="사용자 메뉴" placement="top" effect="dark">
            <el-dropdown @command="handleCommand">
              <div class="flex items-center cursor-pointer">
                <el-avatar :size="32" :src="userAvatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <div class="ml-2 flex-1 min-w-0">
                <p class="text-sm font-medium text-foreground truncate">
                  {{ userInfo?.username || '사용자' }}
                </p>
                <p class="text-xs text-muted-foreground truncate">
                  {{ userInfo?.email || '' }}
                </p>
                </div>
                <el-icon class="ml-2"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="my-page">
                    <el-icon><User /></el-icon>
                    마이페이지
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    로그아웃
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-tooltip>
        </div>
      </div>
    </el-aside>

    <el-main class="p-0 bg-muted/30">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ThemeToggle.vue';
import {
  ChatDotRound,
  Document,
  FolderOpened,
  Collection,
  Search,
  User,
  ArrowDown,
  SwitchButton,
  Setting,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  // 중첩 라우트의 경우 정확한 경로 반환
  const path = route.path
  // /sessions, /documents, /collections, /web-search, /settings, /my-page 경로 정확히 매칭
  if (path.startsWith('/sessions')) return '/sessions'
  if (path.startsWith('/documents')) return '/documents'
  if (path.startsWith('/collections')) return '/collections'
  if (path.startsWith('/web-search')) return '/web-search'
  if (path.startsWith('/settings')) return '/settings'
  if (path.startsWith('/my-page')) return '/my-page'
  return '/'
})
const userInfo = computed(() => authStore.user)
const userAvatar = computed(() => userInfo.value?.avatar || '')

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
  } else if (command === 'my-page') {
    router.push('/my-page')
  }
}

const handleMenuSelect = (index: string) => {
  router.push(index)
}
</script>

<style scoped>
:deep(.el-menu) {
  background-color: transparent;
  --el-menu-text-color: hsl(var(--foreground));
  --el-menu-hover-bg-color: hsl(var(--muted));
}

:deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
}

:deep(.el-menu-item.is-active) {
  background-color: hsl(var(--accent));
  color: hsl(var(--accent-foreground));
  --el-menu-active-color: hsl(var(--accent-foreground));
}

:deep(.el-menu-item:hover) {
  background-color: hsl(var(--muted));
}
</style>

