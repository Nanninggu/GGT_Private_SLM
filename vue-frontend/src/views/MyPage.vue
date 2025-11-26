<template>
  <div class="h-full p-6 bg-background">
    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-foreground">마이페이지</h2>
        <p class="text-sm text-muted-foreground mt-1">내 정보를 확인하고 관리하세요</p>
      </div>

      <!-- User Profile Card -->
      <el-card class="mb-6 bg-card border-border" shadow="never">
        <template #header>
          <div class="flex items-center gap-3">
            <el-avatar :size="64" :src="userInfo?.avatar">
              <el-icon class="text-3xl"><User /></el-icon>
            </el-avatar>
            <div>
              <h3 class="text-xl font-semibold text-foreground">
                {{ userInfo?.username || '사용자' }}
              </h3>
              <p class="text-sm text-muted-foreground">
                {{ userInfo?.email || '이메일 정보 없음' }}
              </p>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <!-- User Information -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="info-item">
              <label class="text-sm font-medium text-muted-foreground">사용자명</label>
              <p class="text-base text-foreground mt-1">{{ userInfo?.username || '-' }}</p>
            </div>
            <div class="info-item">
              <label class="text-sm font-medium text-muted-foreground">이메일</label>
              <p class="text-base text-foreground mt-1">{{ userInfo?.email || '-' }}</p>
            </div>
            <div class="info-item" v-if="userInfo?.created_at">
              <label class="text-sm font-medium text-muted-foreground">가입일</label>
              <p class="text-base text-foreground mt-1">{{ formatDate(userInfo.created_at) }}</p>
            </div>
            <div class="info-item" v-if="userInfo?.user_id">
              <label class="text-sm font-medium text-muted-foreground">사용자 ID</label>
              <p class="text-base text-foreground mt-1 font-mono text-sm">{{ userInfo.user_id }}</p>
            </div>
          </div>

          <!-- Statistics -->
          <div v-if="statistics" class="mt-6 pt-6 border-t border-border">
            <h4 class="text-lg font-semibold text-foreground mb-4">활동 통계</h4>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="stat-card">
                <div class="flex items-center gap-2 mb-2">
                  <el-icon class="text-blue-500"><ChatDotRound /></el-icon>
                  <span class="text-sm text-muted-foreground">총 채팅 세션</span>
                </div>
                <p class="text-2xl font-bold text-foreground">{{ statistics.totalSessions || 0 }}</p>
              </div>
              <div class="stat-card">
                <div class="flex items-center gap-2 mb-2">
                  <el-icon class="text-green-500"><Document /></el-icon>
                  <span class="text-sm text-muted-foreground">업로드 문서</span>
                </div>
                <p class="text-2xl font-bold text-foreground">{{ statistics.totalDocuments || 0 }}</p>
              </div>
              <div class="stat-card">
                <div class="flex items-center gap-2 mb-2">
                  <el-icon class="text-purple-500"><Collection /></el-icon>
                  <span class="text-sm text-muted-foreground">데이터셋</span>
                </div>
                <p class="text-2xl font-bold text-foreground">{{ statistics.totalCollections || 0 }}</p>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Account Actions -->
      <el-card class="bg-card border-border" shadow="never">
        <template #header>
          <div class="flex items-center gap-2">
            <el-icon><Setting /></el-icon>
            <span class="font-semibold">계정 관리</span>
          </div>
        </template>

        <div class="space-y-3">
          <el-button
            type="danger"
            :icon="SwitchButton"
            @click="handleLogout"
            class="w-full md:w-auto"
          >
            로그아웃
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { collectionService } from '@/services/collection.service'
import {
  User,
  ChatDotRound,
  Document,
  Collection,
  Setting,
  SwitchButton,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const userInfo = computed(() => authStore.user)
const statistics = ref<{
  totalSessions: number
  totalDocuments: number
  totalCollections: number
} | null>(null)

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  } catch {
    return dateString
  }
}

const loadStatistics = async () => {
  try {
    // 세션 수 로드
    await chatStore.loadSessions()
    const totalSessions = chatStore.sessions.length

    // 데이터셋 수 로드
    const collectionsResponse = await collectionService.getCollections()
    const totalCollections = collectionsResponse.success 
      ? (collectionsResponse.collections?.length || 0)
      : 0

    // 문서 수는 백엔드 API가 있으면 추가
    const totalDocuments = 0

    statistics.value = {
      totalSessions,
      totalDocuments,
      totalCollections
    }
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('로그아웃되었습니다.')
}

onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.info-item {
  padding: 0.75rem;
  background-color: hsl(var(--muted) / 0.3);
  border-radius: 0.5rem;
}

.stat-card {
  padding: 1rem;
  background-color: hsl(var(--muted) / 0.3);
  border-radius: 0.5rem;
  border: 1px solid hsl(var(--border));
  transition: background-color 0.2s;
}

.stat-card:hover {
  background-color: hsl(var(--muted) / 0.5);
}
</style>

