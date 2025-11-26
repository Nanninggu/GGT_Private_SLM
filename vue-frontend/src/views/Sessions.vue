<template>
  <div class="h-full p-6 bg-background">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-foreground">세션 관리</h2>
          <p class="text-sm text-muted-foreground mt-1">사용자별 채팅 세션을 관리하세요</p>
        </div>
        <el-tooltip content="새로운 채팅 세션을 생성합니다" placement="bottom" effect="dark">
          <el-button type="primary" :icon="Plus" @click="handleCreateSession">
            새 세션
          </el-button>
        </el-tooltip>
      </div>

      <!-- Current Session Info -->
      <el-card v-if="currentSession" class="mb-6 bg-card border-border border-primary/30" shadow="hover">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <el-icon class="text-primary text-2xl"><CircleCheck /></el-icon>
              <div>
                <div class="text-sm text-muted-foreground">현재 세션</div>
                <div class="text-lg font-semibold text-foreground mt-1">
                  {{ currentSession.session_id }}
                </div>
              </div>
            </div>
            <el-divider direction="vertical" />
            <div>
              <div class="text-sm text-muted-foreground">메시지 수</div>
              <div class="text-lg font-semibold text-foreground mt-1">
                {{ currentSession.message_count || 0 }}개
              </div>
            </div>
            <el-divider direction="vertical" />
            <div>
              <div class="text-sm text-muted-foreground">사용자</div>
              <div class="text-lg font-semibold text-foreground mt-1">
                {{ currentSession.user_id || 'default' }}
              </div>
            </div>
            <el-divider direction="vertical" />
            <div>
              <div class="text-sm text-muted-foreground">마지막 활동</div>
              <div class="text-lg font-semibold text-foreground mt-1">
                {{ currentSession.last_activity ? formatDate(currentSession.last_activity) : '없음' }}
              </div>
            </div>
          </div>
          <el-button type="primary" :icon="ChatLineRound" @click="handleLoadSession(currentSession.session_id)">
            세션으로 이동
          </el-button>
        </div>
      </el-card>

      <!-- Statistics -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.totalSessions }}</div>
            <div class="text-sm text-muted-foreground mt-1">총 세션 수</div>
          </div>
        </el-card>
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.totalMessages }}</div>
            <div class="text-sm text-muted-foreground mt-1">총 메시지 수</div>
          </div>
        </el-card>
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.recentSessions }}</div>
            <div class="text-sm text-muted-foreground mt-1">최근 7일 세션</div>
          </div>
        </el-card>
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.lastActivity || '없음' }}</div>
            <div class="text-sm text-muted-foreground mt-1">마지막 활동</div>
          </div>
        </el-card>
      </div>

      <!-- Search and Filter -->
      <el-card class="mb-6 bg-card border-border">
        <div class="flex items-center gap-4">
          <el-input
            v-model="searchQuery"
            placeholder="세션 검색 (세션 ID로 검색...)"
            :prefix-icon="Search"
            clearable
            class="flex-1"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          />
          <el-button type="primary" :icon="Search" @click="handleSearch">검색</el-button>
          <el-button :icon="Refresh" @click="handleRefresh">새로고침</el-button>
        </div>
      </el-card>

      <!-- Session List -->
      <el-card class="bg-card border-border">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-foreground font-semibold">세션 목록 ({{ filteredSessions.length }}개)</span>
            <div class="flex gap-2">
              <el-button size="small" :icon="View" @click="showStats = !showStats">
                {{ showStats ? '통계 숨기기' : '통계 보기' }}
              </el-button>
            </div>
          </div>
        </template>

        <!-- Statistics Panel -->
        <el-collapse-transition>
          <div v-show="showStats" class="mb-6 p-4 bg-muted/30 rounded-lg">
            <h3 class="text-lg font-semibold text-foreground mb-4">📊 상세 통계</h3>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <div class="text-sm text-muted-foreground">평균 메시지 수</div>
                <div class="text-xl font-bold text-foreground">{{ stats.avgMessages.toFixed(1) }}</div>
              </div>
              <div>
                <div class="text-sm text-muted-foreground">최대 메시지 수</div>
                <div class="text-xl font-bold text-foreground">{{ stats.maxMessages }}</div>
              </div>
              <div>
                <div class="text-sm text-muted-foreground">최소 메시지 수</div>
                <div class="text-xl font-bold text-foreground">{{ stats.minMessages }}</div>
              </div>
            </div>
          </div>
        </el-collapse-transition>

        <el-table
          :data="filteredSessions"
          v-loading="loading"
          class="bg-card"
          style="width: 100%"
          :row-class-name="getRowClassName"
        >
          <el-table-column prop="session_id" label="세션 ID" min-width="300">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <el-link
                  v-if="row.session_id"
                  @click="handleLoadSession(row.session_id)"
                  type="primary"
                >
                  {{ row.session_id }}
                </el-link>
                <span v-else class="text-muted-foreground">세션 ID 없음</span>
                <el-tag v-if="row.is_current" type="success" size="small">현재 세션</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="user_id" label="사용자" min-width="200">
            <template #default="{ row }">
              <el-tag type="info">{{ row.user_id || 'default' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message_count" label="메시지 수" width="120" align="center">
            <template #default="{ row }">
              <el-tag type="info">{{ row.message_count || 0 }}개</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="상태" width="120" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_current" type="success" effect="dark">활성</el-tag>
              <el-tag v-else type="info" effect="plain">대기</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="작업" width="250">
            <template #default="{ row }">
              <div class="flex gap-2">
                <el-tooltip content="이 세션으로 전환" placement="top" effect="dark">
                  <el-button
                    v-if="!row.is_current"
                    size="small"
                    :icon="Switch"
                    @click="handleSwitchSession(row.session_id)"
                  >
                    전환
                  </el-button>
                </el-tooltip>
                <el-tooltip content="세션 정보 보기" placement="top" effect="dark">
                  <el-button
                    size="small"
                    :icon="View"
                    @click="handleViewSession(row)"
                  >
                    보기
                  </el-button>
                </el-tooltip>
                <el-tooltip 
                  :content="row.is_current ? '현재 세션을 삭제합니다 (삭제 후 새 세션이 생성됩니다)' : '세션 삭제'" 
                  placement="top" 
                  effect="dark"
                >
                  <el-button
                    size="small"
                    type="danger"
                    :icon="Delete"
                    @click="handleDeleteSession(row.session_id, row.is_current)"
                  >
                    삭제
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="filteredSessions.length === 0" class="text-center py-12">
          <div class="text-muted-foreground/50 text-lg mb-2">
            {{ searchQuery ? '검색 결과가 없습니다' : '저장된 세션이 없습니다' }}
          </div>
          <div class="text-sm text-muted-foreground/80">
            {{ searchQuery ? '다른 검색어를 시도해보세요' : '새 채팅을 시작해보세요!' }}
          </div>
        </div>
      </el-card>

      <!-- View Session Dialog -->
      <el-dialog v-model="showViewDialog" title="세션 정보" width="600px">
        <div class="session-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="세션 ID">
              <el-text copyable>{{ viewingSession.session_id || 'N/A' }}</el-text>
            </el-descriptions-item>
            <el-descriptions-item label="설명">
              {{ viewingSession.description || '설명 없음' }}
            </el-descriptions-item>
            <el-descriptions-item label="메시지 수">
              {{ viewingSession.message_count || 0 }}개
            </el-descriptions-item>
            <el-descriptions-item label="생성일">
              {{ viewingSession.created_at ? formatDate(viewingSession.created_at) : 'N/A' }}
            </el-descriptions-item>
            <el-descriptions-item label="마지막 활동">
              {{ viewingSession.last_activity ? formatDate(viewingSession.last_activity) : 'N/A' }}
            </el-descriptions-item>
            <el-descriptions-item label="현재 세션">
              <el-tag v-if="viewingSession.is_current" type="success">예</el-tag>
              <el-tag v-else type="info">아니오</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="사용자 ID">
              {{ viewingSession.user_id || 'default' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        <template #footer>
          <el-button @click="showViewDialog = false">닫기</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { chatService } from '@/services/chat.service'
import { Plus, Delete, Search, Refresh, View, Switch, CircleCheck, ChatLineRound } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const chatStore = useChatStore()
const authStore = useAuthStore()

const sessions = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const showStats = ref(false)
const showViewDialog = ref(false)
const viewingSession = ref<any>({})
const currentSessionId = ref<string>('')

const currentUser = computed(() => authStore.user)

const stats = computed(() => {
  const totalSessions = sessions.value.length
  const totalMessages = sessions.value.reduce((sum, s) => sum + (s.message_count || 0), 0)
  const recentSessions = sessions.value.filter(s => {
    if (!s.last_activity) return false
    const date = new Date(s.last_activity)
    const weekAgo = new Date()
    weekAgo.setDate(weekAgo.getDate() - 7)
    return date > weekAgo
  }).length
  const lastActivity = sessions.value.length > 0
    ? sessions.value
        .map(s => s.last_activity)
        .filter(Boolean)
        .sort()
        .reverse()[0]
    : null

  const messageCounts = sessions.value.map(s => s.message_count || 0).filter(c => c > 0)
  const avgMessages = messageCounts.length > 0
    ? messageCounts.reduce((sum, c) => sum + c, 0) / messageCounts.length
    : 0
  const maxMessages = messageCounts.length > 0 ? Math.max(...messageCounts) : 0
  const minMessages = messageCounts.length > 0 ? Math.min(...messageCounts) : 0

  return {
    totalSessions,
    totalMessages,
    recentSessions,
    lastActivity: lastActivity ? formatDate(lastActivity) : '없음',
    avgMessages,
    maxMessages,
    minMessages
  }
})

const currentSession = computed(() => {
  return sessions.value.find(s => s.is_current) || null
})

const filteredSessions = computed(() => {
  if (!searchQuery.value.trim()) {
    return sessions.value
  }
  const query = searchQuery.value.toLowerCase()
  return sessions.value.filter(s => {
    const sessionId = (s.session_id || '').toLowerCase()
    const userId = (s.user_id || '').toLowerCase()
    return sessionId.includes(query) || userId.includes(query)
  })
})

const getRowClassName = ({ row }: { row: any }) => {
  return row.is_current ? 'current-session-row' : ''
}

onMounted(async () => {
  currentSessionId.value = chatStore.currentSessionId || ''
  await loadSessions()
})

const loadSessions = async () => {
  loading.value = true
  try {
    await chatStore.loadSessions()
    const sessionPromises = chatStore.sessions.map(async (id) => {
      try {
        const response = await chatService.getSession(id)
        const sessionData = response.session || response // API 응답 형식에 따라 처리
        const stats = await chatService.getSessionStats(id)
        return {
          ...sessionData,
          session_id: sessionData.session_id || sessionData.id || id,
          id: sessionData.id || id,
          user_id: currentUser.value?.username || sessionData.user_id || 'default', // user_id 포함
          description: sessionData.description || '', // 설명 포함
          message_count: stats.stats?.message_count || 0,
          last_activity: stats.stats?.last_activity || sessionData.updated_at,
          is_current: id === currentSessionId.value
        }
      } catch {
        return {
          session_id: id,
          id: id,
          user_id: currentUser.value?.username || 'default',
          description: '',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 0,
          is_current: id === currentSessionId.value
        }
      }
    })
    sessions.value = await Promise.all(sessionPromises)
  } catch (error) {
    ElMessage.error('세션 목록을 불러오는데 실패했습니다.')
  } finally {
    loading.value = false
  }
}

const formatDate = (date: string | null) => {
  if (!date) return '없음'
  try {
    const d = new Date(date)
    return d.toLocaleString('ko-KR', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return '알 수 없음'
  }
}

const handleCreateSession = async () => {
  try {
    loading.value = true
    console.log('[Sessions] Creating new session...')
    const newSessionId = await chatStore.createSession()
    
    if (newSessionId) {
      console.log('[Sessions] New session created:', newSessionId)
      ElMessage.success('새 세션이 생성되었습니다.')
      // 채팅 페이지로 이동
      router.push('/')
    } else {
      console.error('[Sessions] Failed to create new session')
      ElMessage.error('세션 생성에 실패했습니다.')
    }
  } catch (error) {
    console.error('[Sessions] Error creating new session:', error)
    ElMessage.error('세션 생성에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

const handleLoadSession = async (sessionId: string) => {
  if (!sessionId) {
    ElMessage.warning('세션 ID가 없습니다.')
    return
  }
  await chatStore.loadChatHistory(sessionId)
  router.push('/')
}

const handleSwitchSession = async (sessionId: string) => {
  if (!sessionId) {
    ElMessage.warning('세션 ID가 없습니다.')
    return
  }
  try {
    await chatStore.loadChatHistory(sessionId)
    currentSessionId.value = sessionId
    await loadSessions()
    ElMessage.success('세션으로 전환되었습니다!')
    router.push('/')
  } catch (error) {
    ElMessage.error('세션 전환에 실패했습니다.')
  }
}

const handleViewSession = (session: any) => {
  viewingSession.value = { ...session }
  showViewDialog.value = true
}


const handleDeleteSession = async (sessionId: string, isCurrent: boolean = false) => {
  if (!sessionId) {
    ElMessage.warning('세션 ID가 없습니다.')
    return
  }

  try {
    const confirmMessage = isCurrent 
      ? '현재 세션을 삭제하시겠습니까? 삭제 후 새 세션이 생성됩니다.'
      : '이 세션을 삭제하시겠습니까?'
    
    await ElMessageBox.confirm(confirmMessage, '세션 삭제 확인', {
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      type: 'warning',
    })
    
    const wasCurrent = isCurrent && sessionId === chatStore.currentSessionId
    
    await chatStore.deleteSession(sessionId)
    await loadSessions()
    
    if (wasCurrent) {
      // 현재 세션을 삭제한 경우 새 세션 생성
      await chatStore.createSession()
      ElMessage.success('세션이 삭제되었고 새 세션이 생성되었습니다.')
      router.push('/')
    } else {
    ElMessage.success('세션이 삭제되었습니다.')
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Failed to delete session:', error)
      ElMessage.error('세션 삭제에 실패했습니다.')
    }
    // 취소된 경우는 아무것도 하지 않음
  }
}

const handleSearch = () => {
  // 검색은 computed property로 자동 처리됨
}

const handleRefresh = async () => {
  await loadSessions()
  ElMessage.success('새로고침되었습니다.')
}
</script>

<style scoped>
.el-card {
  border: 1px solid hsl(var(--border));
}

:deep(.el-table) {
  background-color: hsl(var(--card));
  color: hsl(var(--foreground));
}

:deep(.el-table th) {
  background-color: hsl(var(--muted));
  color: hsl(var(--foreground));
}

:deep(.el-table td) {
  background-color: hsl(var(--card));
  color: hsl(var(--foreground));
}

:deep(.current-session-row) {
  background-color: hsl(var(--primary) / 0.1) !important;
}

:deep(.current-session-row:hover > td) {
  background-color: hsl(var(--primary) / 0.15) !important;
}
</style>
