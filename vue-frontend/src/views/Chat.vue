<template>
  <div class="h-full flex flex-col bg-background">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-border bg-card">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-foreground">채팅</h2>
          <p class="text-sm text-muted-foreground mt-1">
            {{ chatStore.currentSessionId ? `세션: ${chatStore.currentSessionId}` : '새 대화' }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <el-tooltip
            content="RAG 모드를 선택하세요. 기본 RAG는 빠른 응답, LangChain RAG는 고급 기능을 제공합니다"
            placement="bottom"
            effect="dark"
          >
            <el-select
              v-model="ragMode"
              size="small"
              style="width: 160px"
              placeholder="RAG 모드"
            >
              <el-option value="기본 RAG">
                <template #default>
                  <div class="flex items-center gap-2">
                    <el-icon><Timer /></el-icon>
                    <span>기본 RAG</span>
                  </div>
                </template>
              </el-option>
              <el-option value="LangChain RAG">
                <template #default>
                  <div class="flex items-center gap-2">
                    <el-icon><Connection /></el-icon>
                    <span>LangChain RAG</span>
                  </div>
                </template>
              </el-option>
            </el-select>
          </el-tooltip>
          <el-tooltip
            content="응답 속도와 품질에 따라 모델을 선택하세요"
            placement="bottom"
            effect="dark"
          >
            <el-select
              v-model="selectedModel"
              size="small"
              style="width: 150px"
              placeholder="모델 선택"
            >
              <el-option value="fast">
                <template #default>
                  <div class="flex items-center gap-2">
                    <el-icon><Timer /></el-icon>
                    <span>빠른 응답</span>
                  </div>
                </template>
              </el-option>
              <el-option value="quality">
                <template #default>
                  <div class="flex items-center gap-2">
                    <el-icon><Star /></el-icon>
                    <span>고품질</span>
                  </div>
                </template>
              </el-option>
              <el-option value="complex">
                <template #default>
                  <div class="flex items-center gap-2">
                    <el-icon><DataAnalysis /></el-icon>
                    <span>복잡한 작업</span>
                  </div>
                </template>
              </el-option>
              <el-option value="tynyllm">
                <template #default>
                  <div class="flex items-center gap-2">
                    <el-icon><Promotion /></el-icon>
                    <span>경량 다국어 (Qwen2)</span>
                  </div>
                </template>
              </el-option>
            </el-select>
          </el-tooltip>
          <el-tooltip
            content="새로운 대화를 시작합니다"
            placement="bottom"
            effect="dark"
          >
            <el-button
              size="small"
              :icon="Refresh"
              @click="handleNewSession"
            >
              새 대화
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto px-4 md:px-6 py-6"
    >
      <div v-if="chatStore.messages.length === 0" ref="emptyStateRef" class="flex items-center justify-center h-full">
        <div class="text-center">
          <el-icon class="text-6xl text-muted-foreground/50 mb-4">
            <ChatDotRound />
          </el-icon>
          <p class="text-muted-foreground">메시지를 입력하여 대화를 시작하세요</p>
        </div>
      </div>

      <div
        v-for="(message, index) in chatStore.messages"
        :key="message.id"
        :ref="el => setMessageRef(el, message.id)"
        class="flex items-start gap-3 mb-6"
        :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- User Message (Simple) -->
        <template v-if="message.role === 'user'">
          <div class="flex items-end gap-2 ml-auto" style="max-width: min(100%, 48rem);">
            <div class="flex-1"></div>
            <div class="user-message-bubble rounded-2xl px-5 py-3.5 shadow-lg border-2 border-blue-200 hover:shadow-xl transition-all duration-200" :style="{ backgroundColor: '#ffffff', maxWidth: '100%', overflowX: 'hidden' }">
              <div class="prose prose-sm max-w-none user-message-content text-gray-900" style="max-width: 100%; overflow-x: hidden;">
                <div style="max-width: 100%; overflow-x: hidden;" v-html="formatMessage(message.content)"></div>
              </div>
              <div class="mt-2 pt-2 border-t border-blue-100 text-xs text-gray-500 font-medium">
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
            <div 
              ref="userAvatarRef"
              class="user-avatar flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-sm font-semibold shadow-md"
            >
              {{ getUserInitial() }}
            </div>
          </div>
        </template>

        <!-- Assistant Message (Structured) -->
        <template v-else>
          <div class="flex items-start gap-2 w-full" style="max-width: min(100%, 48rem);">
            <div 
              ref="aiAvatarRef"
              class="ai-avatar flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-sm font-semibold shadow-md"
            >
              AI
            </div>
            <div 
              ref="assistantBubbleRef"
              class="flex-1 assistant-message-bubble rounded-2xl bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-xl transition-shadow duration-200 relative" 
              :style="{ backgroundColor: '#ffffff', maxWidth: '100%', overflowX: 'hidden' }"
            >
              <!-- Copy Button -->
              <div class="absolute top-3 right-3">
                <el-tooltip content="답변 복사" placement="top" effect="dark">
                  <el-button
                    :icon="copiedMessages.has(message.id) ? Check : DocumentCopy"
                    circle
                    size="small"
                    class="copy-message-btn"
                    @click="copyMessage(message)"
                  />
                </el-tooltip>
              </div>
              <div class="p-5 box-border" style="max-width: 100%; overflow-x: hidden;">
                <!-- Main Content -->
                <div class="prose prose-sm dark:prose-invert max-w-none break-words overflow-wrap-anywhere box-border assistant-content text-gray-900 dark:text-gray-100" style="max-width: 100%; overflow-x: hidden;">
                  <div class="box-border" style="max-width: 100%; overflow-x: hidden;" v-html="formatMessage(parsedContent(message.content).mainContent)"></div>
                </div>

                <!-- 메타데이터 정보 바 (아이콘으로 표시) - 항상 표시 -->
                <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div class="flex items-center gap-4 flex-wrap">
                    <!-- 참조 문서 아이콘 -->
                    <div v-if="message.sources && message.sources.length > 0" class="flex items-center gap-1.5">
                      <el-tooltip :content="`${message.sources.length}개의 참조 문서`" placement="top" effect="dark">
                        <div class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors">
                          <el-icon class="text-blue-600 dark:text-blue-400"><Document /></el-icon>
                          <span class="text-xs font-medium text-blue-700 dark:text-blue-300">{{ message.sources.length }}</span>
                        </div>
                      </el-tooltip>
                    </div>
                    <div v-else class="flex items-center gap-1.5">
                      <el-tooltip content="참조 문서 없음" placement="top" effect="dark">
                        <div class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800 cursor-not-allowed opacity-50">
                          <el-icon class="text-gray-400 dark:text-gray-500"><Document /></el-icon>
                          <span class="text-xs font-medium text-gray-500 dark:text-gray-400">0</span>
                        </div>
                      </el-tooltip>
                    </div>

                    <!-- 신뢰도 아이콘 -->
                    <div v-if="message.accuracy" class="flex items-center gap-1.5">
                      <el-tooltip :content="`신뢰도: ${(message.accuracy.confidence_score * 100).toFixed(1)}%`" placement="top" effect="dark">
                        <div class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 cursor-pointer hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors">
                          <el-icon class="text-green-600 dark:text-green-400"><CircleCheck /></el-icon>
                          <span class="text-xs font-medium text-green-700 dark:text-green-300">{{ (message.accuracy.confidence_score * 100).toFixed(0) }}%</span>
                        </div>
                      </el-tooltip>
                    </div>
                    <div v-else class="flex items-center gap-1.5">
                      <el-tooltip content="신뢰도 정보 없음" placement="top" effect="dark">
                        <div class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800 cursor-not-allowed opacity-50">
                          <el-icon class="text-gray-400 dark:text-gray-500"><CircleCheck /></el-icon>
                          <span class="text-xs font-medium text-gray-500 dark:text-gray-400">-</span>
                        </div>
                      </el-tooltip>
                    </div>

                    <!-- AI 모델 정보 아이콘 -->
                    <div v-if="getModelInfo(message)" class="flex items-center gap-1.5">
                      <el-tooltip content="AI 모델 정보" placement="top" effect="dark">
                        <div class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 cursor-pointer hover:bg-purple-100 dark:hover:bg-purple-900/30 transition-colors">
                          <el-icon class="text-purple-600 dark:text-purple-400"><InfoFilled /></el-icon>
                        </div>
                      </el-tooltip>
                    </div>
                    <div v-else class="flex items-center gap-1.5">
                      <el-tooltip content="AI 모델 정보 없음" placement="top" effect="dark">
                        <div class="flex items-center gap-1.5 px-2 py-1 rounded-md bg-gray-50 dark:bg-gray-900/20 border border-gray-200 dark:border-gray-800 cursor-not-allowed opacity-50">
                          <el-icon class="text-gray-400 dark:text-gray-500"><InfoFilled /></el-icon>
                        </div>
                      </el-tooltip>
                    </div>

                    <!-- 타임스탬프 아이콘 (항상 표시) -->
                    <div class="flex items-center gap-1.5 ml-auto">
                      <el-icon class="text-gray-400 dark:text-gray-500"><Timer /></el-icon>
                      <span class="text-xs text-gray-500 dark:text-gray-400">{{ formatTime(message.timestamp) }}</span>
                    </div>
                  </div>
                </div>

                <!-- 통합 메타데이터 섹션 (접을 수 있음) -->
                <div v-if="hasMetadata(message)" class="mt-3">
                  <el-collapse v-model="expandedSections[message.id]" class="metadata-collapse">
                    <el-collapse-item name="metadata">
                      <template #title>
                        <div class="flex items-center gap-2 text-xs font-medium text-gray-600 dark:text-gray-400">
                          <el-icon><ArrowDown /></el-icon>
                          <span>상세 정보 보기</span>
                        </div>
                      </template>

                      <div class="space-y-4 pt-2">
                        <!-- AI 모델 정보 -->
                        <div v-if="getModelInfo(message)" class="metadata-section">
                          <div class="flex items-center gap-2 mb-2">
                            <el-icon class="text-purple-600 dark:text-purple-400"><InfoFilled /></el-icon>
                            <span class="text-xs font-semibold text-gray-700 dark:text-gray-300">AI 모델 정보</span>
                          </div>
                          <div class="space-y-1.5 text-xs bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg">
                            <div v-for="(value, key) in getModelInfo(message)" :key="key" class="flex justify-between items-start gap-2">
                              <span class="text-gray-500 dark:text-gray-400 min-w-[100px]">{{ key }}:</span>
                              <span class="text-gray-900 dark:text-gray-100 flex-1 text-left">{{ value }}</span>
                            </div>
                          </div>
                        </div>

                        <!-- 신뢰도 상세 -->
                        <div v-if="message.accuracy" class="metadata-section">
                          <div class="flex items-center gap-2 mb-2">
                            <el-icon class="text-green-600 dark:text-green-400"><CircleCheck /></el-icon>
                            <span class="text-xs font-semibold text-gray-700 dark:text-gray-300">신뢰도 분석</span>
                          </div>
                          <div class="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg space-y-2">
                            <div class="flex items-center justify-between mb-2">
                              <span class="text-xs text-gray-600 dark:text-gray-400">신뢰도 점수</span>
                              <span class="text-xs font-bold" :class="getConfidenceColorClass(message.accuracy.confidence_score)">
                                {{ (message.accuracy.confidence_score * 100).toFixed(1) }}%
                              </span>
                            </div>
                            <el-progress 
                              :percentage="message.accuracy.confidence_score * 100" 
                              :color="getConfidenceColor(message.accuracy.confidence_score)"
                              :stroke-width="8"
                              :show-text="false"
                            />
                            <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mt-2">
                              <span>컨텍스트: {{ message.accuracy.context_count }}개</span>
                              <span>평균 유사도: {{ (message.accuracy.avg_similarity * 100).toFixed(1) }}%</span>
                            </div>
                          </div>
                        </div>

                        <!-- 참조 문서 상세 -->
                        <div v-if="message.sources && message.sources.length > 0" class="metadata-section">
                          <div class="flex items-center gap-2 mb-2">
                            <el-icon class="text-blue-600 dark:text-blue-400"><Document /></el-icon>
                            <span class="text-xs font-semibold text-gray-700 dark:text-gray-300">참조 문서 ({{ message.sources.length }})</span>
                          </div>
                          <div class="space-y-2">
                            <div
                              v-for="(source, idx) in message.sources"
                              :key="idx"
                              class="source-item bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 transition-colors"
                            >
                              <div class="flex items-start justify-between mb-2">
                                <div class="flex items-center gap-2 flex-1 min-w-0">
                                  <el-icon class="text-blue-600 dark:text-blue-400 flex-shrink-0"><Document /></el-icon>
                                  <p class="text-xs font-medium text-gray-900 dark:text-gray-100 truncate">{{ source.filename }}</p>
                                </div>
                                <el-tag size="small" type="info" class="flex-shrink-0">
                                  {{ (source.similarity_score * 100).toFixed(1) }}%
                                </el-tag>
                              </div>
                              <el-progress 
                                :percentage="source.similarity_score * 100" 
                                :stroke-width="4"
                                :show-text="false"
                                color="#3b82f6"
                                class="mb-2"
                              />
                              <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">{{ source.content_preview }}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Streaming message -->
      <div 
        v-if="chatStore.isStreaming" 
        ref="streamingMessageRef"
        class="flex items-start gap-3 mb-6 justify-start"
      >
        <div class="flex items-start gap-2 w-full" style="max-width: min(100%, 48rem);">
          <div class="ai-avatar-streaming flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white text-sm font-semibold shadow-md relative">
            <div class="absolute inset-0 rounded-full bg-gradient-to-br from-purple-400 to-indigo-500 animate-ping opacity-75"></div>
            <div class="relative z-10 flex items-center justify-center">
              <el-icon class="animate-spin"><Loading /></el-icon>
            </div>
          </div>
          <div class="flex-1 assistant-message-bubble rounded-2xl bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-xl transition-shadow duration-200 relative" :style="{ backgroundColor: '#ffffff', maxWidth: '100%', overflowX: 'hidden' }">
            <!-- Copy Button for Streaming -->
            <div class="absolute top-3 right-3">
              <el-tooltip content="답변 복사" placement="top" effect="dark">
                <el-button
                  :icon="DocumentCopy"
                  circle
                  size="small"
                  class="copy-message-btn"
                  :disabled="chatStore.isStreaming"
                  @click="copyStreamingMessage"
                />
              </el-tooltip>
            </div>
            <div class="p-5 box-border" style="max-width: 100%; overflow-x: hidden;">
              <div class="prose prose-sm dark:prose-invert max-w-none break-words overflow-wrap-anywhere box-border assistant-content text-gray-900 dark:text-gray-100" style="max-width: 100%; overflow-x: hidden;">
                <div class="box-border" style="max-width: 100%; overflow-x: hidden;" v-html="formatMessage(chatStore.streamingContent)"></div>
              </div>
              <div class="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <div class="flex items-center gap-1">
                  <span class="typing-dot"></span>
                  <span class="typing-dot" style="animation-delay: 0.2s;"></span>
                  <span class="typing-dot" style="animation-delay: 0.4s;"></span>
                </div>
                <span class="typing-text">답변 생성 중</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="px-6 py-4 border-t border-border bg-card">
      <div class="flex items-end gap-2">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          placeholder="메시지를 입력하세요..."
          :disabled="chatStore.isLoading || chatStore.isStreaming"
          @keydown.ctrl.enter="handleSend"
          @keydown.meta.enter="handleSend"
        />
        <el-tooltip
          content="메시지를 전송합니다 (Ctrl/Cmd + Enter)"
          placement="top"
          effect="dark"
        >
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="chatStore.isLoading || chatStore.isStreaming"
            @click="handleSend"
            size="large"
          >
            전송
          </el-button>
        </el-tooltip>
      </div>
      <div class="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <div class="flex items-center gap-4">
          <el-tooltip
            content="RAG(Retrieval-Augmented Generation)를 활성화하면 문서 검색을 통해 더 정확한 답변을 제공합니다"
            placement="top"
            effect="dark"
          >
            <el-checkbox v-model="useRag" size="small">RAG 사용</el-checkbox>
          </el-tooltip>
          <el-tooltip
            v-if="ragMode === 'LangChain RAG' && useRag"
            content="LangChain RAG 모드에서는 데이터셋을 선택할 수 있습니다"
            placement="top"
            effect="dark"
          >
            <div class="flex items-center gap-2">
              <el-select
                v-model="tempSelectedCollection"
                size="small"
                style="width: 200px"
                placeholder="데이터셋 선택"
                clearable
              >
                <el-option
                  v-for="collection in collections"
                  :key="collection.name"
                  :label="collection.name"
                  :value="collection.name"
                />
              </el-select>
              <el-button
                type="primary"
                size="small"
                :icon="Check"
                :disabled="tempSelectedCollection === selectedCollection"
                @click="handleConfirmCollection"
              >
                확인
              </el-button>
              <el-tag
                v-if="selectedCollection"
                type="success"
                size="small"
                effect="dark"
              >
                {{ selectedCollection }}
              </el-tag>
            </div>
          </el-tooltip>
          <el-tooltip
            content="키보드 단축키로 빠르게 메시지를 전송할 수 있습니다"
            placement="top"
            effect="dark"
          >
            <span class="cursor-help">Ctrl/Cmd + Enter로 전송</span>
          </el-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { collectionService } from '@/services/collection.service'
import { Promotion, Refresh, ChatDotRound, CircleCheck, Loading, InfoFilled, QuestionFilled, DocumentCopy, Check, Document, DataAnalysis, Timer, ArrowDown, Star, Connection } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { useAuthStore } from '@/stores/auth'
import { useMotion } from '@vueuse/motion'
import { ElMessage } from 'element-plus'

const chatStore = useChatStore()
const authStore = useAuthStore()
const route = useRoute()

const inputMessage = ref('')
// 세션별 설정은 chatStore에서 관리하고, 로컬 ref는 동기화용으로 사용
const selectedModel = ref('fast')
const useRag = ref(true)
const ragMode = ref('LangChain RAG')
const selectedCollection = ref<string>('') // 실제 적용된 데이터셋
const tempSelectedCollection = ref<string>('') // 임시 선택 상태
const collections = ref<any[]>([])
const messagesContainer = ref<HTMLElement>()

// 세션 설정 동기화 함수
const syncSettingsFromStore = () => {
  const settings = chatStore.currentSessionSettings
  selectedModel.value = settings.selectedModel || 'fast'
  useRag.value = settings.useRag !== undefined ? settings.useRag : true
  ragMode.value = settings.ragMode || 'LangChain RAG'
  selectedCollection.value = settings.selectedCollection || ''
  tempSelectedCollection.value = settings.selectedCollection || ''
  console.log('[Chat] Settings synced from store:', settings)
}

// 세션 설정 저장 함수
const saveCurrentSettings = () => {
  chatStore.updateCurrentSessionSettings({
    selectedModel: selectedModel.value,
    useRag: useRag.value,
    ragMode: ragMode.value,
    selectedCollection: selectedCollection.value
  })
}
const emptyStateRef = ref<HTMLElement>()
const copiedCodeBlocks = ref<Set<string>>(new Set())
const copiedMessages = ref<Set<string>>(new Set())
// expandedSections를 localStorage에서 복원하여 탭 전환 후에도 유지
const expandedSections = ref<Record<string, string[]>>(() => {
  try {
    const saved = localStorage.getItem('chat_expanded_sections')
    return saved ? JSON.parse(saved) : {}
  } catch {
    return {}
  }
})
const messageRefs = ref<Map<string, HTMLElement>>(new Map())
const messageMotions = ref<Map<string, any>>(new Map())
const streamingMessageRef = ref<HTMLElement>()
const sendButtonRef = ref<HTMLElement>()

// 메시지 ref 설정 및 모션 적용
const setMessageRef = (el: HTMLElement | null, messageId: string) => {
  if (el && !messageRefs.value.has(messageId)) {
    messageRefs.value.set(messageId, el)
    
    // 모션 적용
    const motion = useMotion(el, {
      initial: { 
        opacity: 0, 
        y: 20,
        scale: 0.95
      },
      enter: { 
        opacity: 1, 
        y: 0,
        scale: 1,
        transition: {
          duration: 300,
          ease: [0.4, 0, 0.2, 1]
        }
      }
    })
    
    messageMotions.value.set(messageId, motion)
    
    // 즉시 애니메이션 트리거
    nextTick(() => {
      motion.apply('enter')
    })
  }
}

// 빈 상태 모션
watch(() => chatStore.messages.length, (newLength) => {
  if (newLength === 0 && emptyStateRef.value) {
    nextTick(() => {
      useMotion(emptyStateRef.value!, {
        initial: { opacity: 0, scale: 0.9 },
        enter: { 
          opacity: 1, 
          scale: 1,
          transition: {
            duration: 400,
            ease: [0.4, 0, 0.2, 1]
          }
        }
      }).apply('enter')
    })
  }
}, { immediate: true })

// 메시지 추가 시 애니메이션 트리거
watch(() => chatStore.messages.length, (newLength, oldLength) => {
  if (newLength > oldLength) {
    // 새 메시지가 추가되었을 때
    nextTick(() => {
      const lastMessage = chatStore.messages[chatStore.messages.length - 1]
      if (lastMessage && messageRefs.value.has(lastMessage.id)) {
        const motion = messageMotions.value.get(lastMessage.id)
        if (motion) {
          motion.apply('enter')
        }
      }
    })
  }
})

// 스트리밍 메시지 모션
watch(() => chatStore.isStreaming, (isStreaming) => {
  if (isStreaming && streamingMessageRef.value) {
    nextTick(() => {
      useMotion(streamingMessageRef.value!, {
        initial: { opacity: 0, y: 20, scale: 0.95 },
        enter: { 
          opacity: 1, 
          y: 0,
          scale: 1,
          transition: {
            duration: 300,
            ease: [0.4, 0, 0.2, 1]
          }
        }
      }).apply('enter')
    })
  }
})

// 스트리밍 메시지 모션
watch(() => chatStore.isStreaming, (isStreaming) => {
  if (isStreaming && streamingMessageRef.value) {
    nextTick(() => {
      useMotion(streamingMessageRef.value!, {
        initial: { opacity: 0, y: 20, scale: 0.95 },
        enter: { 
          opacity: 1, 
          y: 0,
          scale: 1,
          transition: {
            duration: 300,
            ease: [0.4, 0, 0.2, 1]
          }
        }
      }).apply('enter')
    })
  }
})

// 전송 버튼 모션 (호버 효과)
onMounted(() => {
  if (sendButtonRef.value) {
    useMotion(sendButtonRef.value, {
      initial: { scale: 1 },
      hovered: {
        scale: 1.05,
        transition: {
          duration: 200,
          ease: [0.4, 0, 0.2, 1]
        }
      },
      tapped: {
        scale: 0.95,
        transition: {
          duration: 100
        }
      }
    })
  }
})

// 로딩 중복 방지 플래그
let isLoadingHistory = false

// 채팅 히스토리를 로드하는 함수
const loadChatHistory = async (forceReload = false) => {
  // 중복 로드 방지
  if (isLoadingHistory) {
    console.log('[Chat] Already loading history, skipping...')
    return
  }
  
  // 이미 메시지가 있고 현재 세션이 유효하면 재로드하지 않음 (강제 재로드가 아닌 경우)
  if (!forceReload && chatStore.messages.length > 0 && chatStore.currentSessionId) {
    console.log('[Chat] Messages already loaded, skipping reload. Message count:', chatStore.messages.length)
    // 설정만 동기화
    syncSettingsFromStore()
    return
  }
  
  isLoadingHistory = true
  console.log('[Chat] Loading chat history...')
  console.log('[Chat] Current session ID:', chatStore.currentSessionId)
  
  try {
    // 먼저 세션 목록을 로드
    await chatStore.loadSessions()
    console.log('[Chat] Sessions loaded:', chatStore.sessions)
    
    // localStorage에서 currentSessionId 확인
    const savedSessionId = localStorage.getItem('current_session_id')
    console.log('[Chat] Saved session ID from localStorage:', savedSessionId)
    
    // 현재 세션이 있으면 해당 세션의 히스토리를 로드
    const sessionIdToLoad = chatStore.currentSessionId || savedSessionId
    
    if (sessionIdToLoad) {
      // 세션 목록에 없어도 직접 히스토리 로드 시도 (user_id 필터링으로 인해 목록에 없을 수 있음)
      try {
        console.log('[Chat] Loading history for session:', sessionIdToLoad)
        await chatStore.loadChatHistory(sessionIdToLoad)
        // 세션 설정 동기화
        syncSettingsFromStore()
        console.log('[Chat] History loaded successfully, message count:', chatStore.messages.length)
        return // 성공적으로 로드했으면 종료
      } catch (error) {
        console.error('[Chat] Failed to load session:', sessionIdToLoad, error)
        // 세션 로드 실패 시 localStorage에서 제거하고 계속 진행
        localStorage.removeItem('current_session_id')
        chatStore.currentSessionId = null
      }
    }
    
    // 현재 세션이 없거나 로드 실패한 경우
    if (chatStore.sessions.length > 0) {
      // 첫 번째 세션 로드
      console.log('[Chat] No current session, loading first session:', chatStore.sessions[0])
      try {
        await chatStore.loadChatHistory(chatStore.sessions[0])
        // 세션 설정 동기화
        syncSettingsFromStore()
        console.log('[Chat] First session loaded successfully, message count:', chatStore.messages.length)
      } catch (error) {
        console.error('[Chat] Failed to load first session:', error)
        // 첫 번째 세션도 로드 실패하면 새 세션 생성
        await chatStore.createSession()
      }
    } else {
      // 세션이 없으면 새 세션 생성
      console.log('[Chat] No sessions found, creating new session')
      await chatStore.createSession()
    }
  } finally {
    isLoadingHistory = false
  }
}

onMounted(async () => {
  console.log('[Chat] Component mounted')
  // 1. 채팅 히스토리 및 세션 설정 로드 (최초 마운트 시에만 강제 로드)
  await loadChatHistory(true)
  // 2. 컬렉션 목록 로드
  await loadCollections()
  // 3. 세션에 저장된 컬렉션이 없는 경우에만 active collection 로드
  await loadActiveCollection()
  
  console.log('[Chat] Initial settings:', {
    selectedModel: selectedModel.value,
    ragMode: ragMode.value,
    useRag: useRag.value,
    selectedCollection: selectedCollection.value
  })
  
  nextTick(() => {
    setupCodeBlockListeners()
    
    // 전송 버튼 모션 (호버 효과)
    if (sendButtonRef.value) {
      useMotion(sendButtonRef.value, {
        initial: { scale: 1 },
        hovered: {
          scale: 1.05,
          transition: {
            duration: 200,
            ease: [0.4, 0, 0.2, 1]
          }
        },
        tapped: {
          scale: 0.95,
          transition: {
            duration: 100
          }
        }
      })
    }
  })
})

// expandedSections 변경 시 localStorage에 저장하여 탭 전환 후에도 유지
watch(expandedSections, (newValue) => {
  try {
    localStorage.setItem('chat_expanded_sections', JSON.stringify(newValue))
  } catch (error) {
    console.error('Failed to save expanded sections:', error)
  }
}, { deep: true })

// 설정 변경 시 자동 저장 (세션이 존재할 때만)
watch([selectedModel, useRag, ragMode, selectedCollection], () => {
  if (chatStore.currentSessionId) {
    saveCurrentSettings()
    console.log('[Chat] Settings auto-saved')
  }
}, { deep: true })

// 세션 변경 감지하여 설정 동기화
watch(() => chatStore.currentSessionId, (newSessionId, oldSessionId) => {
  if (newSessionId && newSessionId !== oldSessionId) {
    console.log('[Chat] Session changed, syncing settings:', newSessionId)
    syncSettingsFromStore()
  }
})

// keep-alive 사용 시를 대비한 활성화 훅
onActivated(async () => {
  console.log('[Chat] Component activated')
  await loadChatHistory()
  nextTick(() => {
    setupCodeBlockListeners()
  })
})

// 라우트 변경 감지 - 채팅 화면으로 돌아올 때 히스토리 로드
watch(
  () => route.name,
  async (newName, oldName) => {
    // 채팅 화면으로 돌아올 때만 히스토리 로드
    if (newName === 'Chat' && oldName !== 'Chat') {
      console.log('[Chat] Route changed to Chat, reloading history')
      await loadChatHistory()
    }
  },
  { immediate: false }
)

const loadCollections = async () => {
  try {
    const response = await collectionService.getCollections()
    if (response.success) {
      collections.value = response.collections || []
    }
  } catch (error) {
    console.error('Failed to load collections:', error)
  }
}

const loadActiveCollection = async () => {
  try {
    // 세션에 저장된 데이터셋이 있으면 그것을 우선 사용
    if (selectedCollection.value) {
      console.log('[Chat] Using session-saved collection:', selectedCollection.value)
      tempSelectedCollection.value = selectedCollection.value
      return
    }
    
    // 세션에 저장된 데이터셋이 없으면 active collection 로드
    const response = await collectionService.getActiveCollection()
    if (response.success && response.collection_name) {
      selectedCollection.value = response.collection_name
      tempSelectedCollection.value = response.collection_name
      // 새로 로드한 컬렉션을 세션 설정에 저장
      if (chatStore.currentSessionId) {
        saveCurrentSettings()
      }
    }
  } catch (error) {
    console.error('Failed to load active collection:', error)
  }
}

const handleConfirmCollection = () => {
  if (tempSelectedCollection.value === selectedCollection.value) {
    return
  }
  
  selectedCollection.value = tempSelectedCollection.value
  // 설정 저장은 watch에서 자동으로 처리됨
  ElMessage.success({
    message: `데이터셋 "${selectedCollection.value || '(없음)'}"이(가) 선택되었습니다.`,
    duration: 2000
  })
}

watch(
  () => chatStore.messages.length,
  () => {
    nextTick(() => {
      scrollToBottom()
      setupCodeBlockListeners()
    })
  }
)

watch(
  () => chatStore.streamingContent,
  () => {
    nextTick(() => {
      scrollToBottom()
      setupCodeBlockListeners()
    })
  }
)

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (content: string) => {
  // 코드 블록 처리를 개선하기 위해 marked 옵션 설정
  let html = marked(content, { 
    breaks: true,
    gfm: true, // GitHub Flavored Markdown 활성화
    headerIds: false,
    mangle: false
  })
  
  // 코드 블록에 복사 버튼과 언어 라벨 추가
  html = html.replace(/<pre><code(?: class="language-(\w+)")?>([\s\S]*?)<\/code><\/pre>/g, (match, lang, code) => {
    const blockId = `code-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const language = lang || 'text'
    // 코드는 이미 marked에서 이스케이프되어 있으므로 그대로 사용
    return `<div class="code-block-wrapper" data-block-id="${blockId}">
        <div class="code-block-header">
          <span class="code-language">${language}</span>
          <button class="code-copy-btn" data-copy-id="${blockId}" title="코드 복사">
            <svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect width="14" height="14" x="8" y="8" rx="2" ry="2"></rect>
              <path d="M4 16c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2h8c1.1 0 2 .9 2 2"></path>
            </svg>
            <svg class="check-icon hidden" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </button>
        </div>
        <pre><code class="language-${language}">${code}</code></pre>
      </div>`
  })
  
  return html
}

const copyCodeBlock = async (blockId: string) => {
  const wrapper = document.querySelector(`[data-block-id="${blockId}"]`)
  if (!wrapper) return
  
  const codeElement = wrapper.querySelector('code')
  if (!codeElement) return
  
  const code = codeElement.textContent || ''
  
  try {
    await navigator.clipboard.writeText(code)
    copiedCodeBlocks.value.add(blockId)
    
    const copyBtn = wrapper.querySelector('.code-copy-btn')
    const copyIcon = wrapper.querySelector('.copy-icon')
    const checkIcon = wrapper.querySelector('.check-icon')
    
    if (copyIcon && checkIcon) {
      copyIcon.classList.add('hidden')
      checkIcon.classList.remove('hidden')
    }
    
    setTimeout(() => {
      copiedCodeBlocks.value.delete(blockId)
      if (copyIcon && checkIcon) {
        copyIcon.classList.remove('hidden')
        checkIcon.classList.add('hidden')
      }
    }, 2000)
  } catch (err) {
    console.error('코드 복사 실패:', err)
  }
}

// 코드 블록 복사 버튼 이벤트 리스너 설정
const setupCodeBlockListeners = () => {
  nextTick(() => {
    const copyButtons = document.querySelectorAll('.code-copy-btn')
    copyButtons.forEach(btn => {
      const blockId = btn.getAttribute('data-copy-id')
      if (blockId && !btn.hasAttribute('data-listener-attached')) {
        btn.setAttribute('data-listener-attached', 'true')
        btn.addEventListener('click', () => copyCodeBlock(blockId || ''))
      }
    })
  })
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

const getUserInitial = () => {
  const username = authStore.user?.username
  if (username && username.length > 0) {
    // 한글인 경우 첫 글자, 영문인 경우 첫 글자 대문자
    return username.charAt(0).toUpperCase()
  }
  return '사' // 기본값
}

const getModelInfo = (message: any) => {
  // 1. metadata에서 model_info를 우선 사용
  if (message.metadata && message.metadata.model_info) {
    return message.metadata.model_info
  }
  
  // 2. metadata에서 model_name, model_type 등의 개별 필드를 사용
  if (message.metadata && (message.metadata.model_name || message.metadata.model_type)) {
    const info: Record<string, string> = {}
    if (message.metadata.model_name) info['모델'] = message.metadata.model_name
    if (message.metadata.model_type) info['모델 타입'] = message.metadata.model_type
    if (message.metadata.rag_mode) info['RAG 모드'] = message.metadata.rag_mode
    if (Object.keys(info).length > 0) return info
  }
  
  // 3. fallback: content에서 파싱
  const parsed = parsedContent(message.content)
  if (parsed.modelInfo) {
    return parsed.modelInfo
  }
  
  // 4. 기본 모델 정보 반환 (assistant 메시지인 경우)
  if (message.role === 'assistant') {
    return {
      '모델': 'exaone3.5:2.4b',
      '모델 타입': 'fast',
      'RAG 모드': 'LangChain RAG'
    }
  }
  
  return null
}

const hasMetadata = (message: any) => {
  const hasSources = message.sources && message.sources.length > 0
  const hasAccuracy = message.accuracy
  const hasModelInfo = getModelInfo(message)
  
  return hasSources || hasAccuracy || hasModelInfo
}

const getConfidenceColor = (score: number) => {
  if (score >= 0.8) return '#10b981' // green
  if (score >= 0.6) return '#3b82f6' // blue
  if (score >= 0.4) return '#f59e0b' // amber
  return '#ef4444' // red
}

const getConfidenceColorClass = (score: number) => {
  if (score >= 0.8) return 'text-green-600 dark:text-green-400'
  if (score >= 0.6) return 'text-blue-600 dark:text-blue-400'
  if (score >= 0.4) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

const copyMessage = async (message: any) => {
  try {
    // HTML 태그를 제거하고 순수 텍스트만 추출
    const content = parsedContent(message.content).mainContent
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = content
    const textContent = tempDiv.textContent || tempDiv.innerText || ''
    
    // 클립보드에 복사
    await navigator.clipboard.writeText(textContent.trim())
    
    // 복사 성공 표시
    copiedMessages.value.add(message.id)
    
    // 2초 후 아이콘 원래대로
    setTimeout(() => {
      copiedMessages.value.delete(message.id)
    }, 2000)
  } catch (err) {
    console.error('메시지 복사 실패:', err)
    // 폴백: 텍스트 영역 선택 방식
    try {
      const content = parsedContent(message.content).mainContent
      const tempDiv = document.createElement('div')
      tempDiv.innerHTML = content
      const textContent = tempDiv.textContent || tempDiv.innerText || ''
      
      const textArea = document.createElement('textarea')
      textArea.value = textContent.trim()
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      
      copiedMessages.value.add(message.id)
      setTimeout(() => {
        copiedMessages.value.delete(message.id)
      }, 2000)
    } catch (fallbackErr) {
      console.error('폴백 복사 실패:', fallbackErr)
    }
  }
}

const copyStreamingMessage = async () => {
  if (chatStore.isStreaming) return
  
  try {
    const content = chatStore.streamingContent
    const tempDiv = document.createElement('div')
    tempDiv.innerHTML = content
    const textContent = tempDiv.textContent || tempDiv.innerText || ''
    
    await navigator.clipboard.writeText(textContent.trim())
    
    // 성공 피드백 (간단한 토스트 메시지 대신 아이콘 변경)
    const streamingCopyBtn = document.querySelector('.copy-message-btn')
    if (streamingCopyBtn) {
      // 임시로 체크 아이콘 표시는 복잡하므로 간단히 처리
      console.log('스트리밍 메시지 복사 완료')
    }
  } catch (err) {
    console.error('스트리밍 메시지 복사 실패:', err)
  }
}

// 응답 내용을 파싱하여 메인 콘텐츠와 AI 모델 정보를 분리
const parsedContent = (content: string) => {
  // AI 모델 정보 섹션 찾기 (--- 구분선 이후)
  const separator = '---'
  const separatorIndex = content.indexOf(separator)
  
  if (separatorIndex === -1) {
    // 구분선이 없으면 전체를 메인 콘텐츠로
    return {
      mainContent: content,
      modelInfo: null
    }
  }
  
  // 메인 콘텐츠 (구분선 이전)
  let mainContent = content.substring(0, separatorIndex).trim()
  
  // 참고 문서 정보 섹션 제거 (이미 별도로 표시되므로)
  mainContent = mainContent.replace(/\*\*📚 참고 문서 정보\*\*[\s\S]*?$/m, '').trim()
  
  // AI 모델 정보 파싱 (구분선 이후)
  const modelInfoSection = content.substring(separatorIndex + separator.length).trim()
  const modelInfo: Record<string, string> = {}
  
  // **AI 모델 정보** 제목 제거
  let infoText = modelInfoSection.replace(/^\*\*AI 모델 정보\*\*\s*/i, '')
  
  // 참고 문서 정보 섹션 제거 (이미 별도로 표시되므로)
  infoText = infoText.replace(/\*\*📚 참고 문서 정보\*\*[\s\S]*?(?=\*이 답변이|$)/m, '').trim()
  
  // 마지막 문장 제거 (도움이 되었나요? 부분)
  infoText = infoText.replace(/\*이 답변이.*$/s, '').trim()
  
  // 각 줄을 파싱하여 키-값 추출
  const lines = infoText.split('\n').filter(line => line.trim())
  for (const line of lines) {
    // - 키: 값 형식 파싱
    const match = line.match(/^[-•]\s*\*\*?([^:：]+)[:：]\*\*?\s*(.+)$/)
    if (match) {
      const key = match[1].trim()
      const value = match[2].trim()
      modelInfo[key] = value
    }
  }
  
  return {
    mainContent,
    modelInfo: Object.keys(modelInfo).length > 0 ? modelInfo : null
  }
}

const handleSend = async () => {
  if (!inputMessage.value.trim() || chatStore.isLoading || chatStore.isStreaming) {
    return
  }

  const message = inputMessage.value.trim()
  inputMessage.value = ''

  let streamingContent = ''
  await chatStore.sendMessage(message, {
    useRag: useRag.value,
    modelType: selectedModel.value,
    ragMode: ragMode.value,
    collectionNames: selectedCollection.value ? [selectedCollection.value] : undefined,
    onStream: (chunk) => {
      streamingContent += chunk
      scrollToBottom()
    },
  })
}

const handleNewSession = async () => {
  try {
    console.log('[Chat] Creating new session...')
    const newSessionId = await chatStore.createSession()
    
    if (newSessionId) {
      console.log('[Chat] New session created:', newSessionId)
      ElMessage.success('새 대화가 시작되었습니다.')
    } else {
      console.error('[Chat] Failed to create new session')
      ElMessage.error('새 대화를 시작하는데 실패했습니다.')
    }
  } catch (error) {
    console.error('[Chat] Error creating new session:', error)
    ElMessage.error('새 대화를 시작하는데 실패했습니다.')
  }
}
</script>

<style scoped>
:deep(.el-textarea__inner) {
  resize: none;
}

/* 구조화된 메시지 스타일 */
.prose {
  color: #1f2937; /* 검정색에 가까운 진한 회색 */
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  max-width: 100%;
  box-sizing: border-box;
  overflow-x: hidden;
}

.dark .prose {
  color: #f3f4f6; /* 다크 모드에서는 밝은 회색 */
}

.prose * {
  max-width: 100%;
  box-sizing: border-box;
  word-break: break-word;
  overflow-wrap: break-word;
  overflow-x: hidden;
}

.prose > *:first-child {
  margin-top: 0;
}

.prose > *:last-child {
  margin-bottom: 0;
}

.prose h1, .prose h2, .prose h3, .prose h4 {
  color: #111827; /* 더 진한 검정색 */
  font-weight: 700;
  margin-top: 1.75em;
  margin-bottom: 0.75em;
  word-wrap: break-word;
  line-height: 1.4;
}

.dark .prose h1, .dark .prose h2, .dark .prose h3, .dark .prose h4 {
  color: #f9fafb; /* 다크 모드에서는 더 밝은 색 */
}

.prose h1 {
  font-size: 1.75em;
  border-bottom: 3px solid hsl(var(--border));
  padding-bottom: 0.75em;
  margin-top: 0;
}

.prose h2 {
  font-size: 1.5em;
  margin-top: 1.5em;
  border-bottom: 2px solid hsl(var(--border));
  padding-bottom: 0.5em;
}

.prose h3 {
  font-size: 1.25em;
  margin-top: 1.25em;
  font-weight: 600;
}

.prose h4 {
  font-size: 1.1em;
  margin-top: 1em;
  font-weight: 600;
}

/* 인라인 코드 */
.prose code:not(pre code) {
  background-color: hsl(var(--muted));
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
  word-break: break-all;
  white-space: pre-wrap;
  max-width: 100%;
  overflow-x: hidden;
  overflow-wrap: break-word;
}

/* 코드 블록 래퍼 */
.code-block-wrapper {
  position: relative;
  margin: 1.5em 0;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(148, 163, 184, 0.2);
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
}

.dark .code-block-wrapper {
  border-color: rgba(148, 163, 184, 0.3);
}

/* 코드 블록 헤더 */
.code-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.dark .code-block-header {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.code-language {
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
}

.code-copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.375rem 0.5rem;
  background: rgba(148, 163, 184, 0.1);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #cbd5e1;
}

.code-copy-btn:hover {
  background: rgba(148, 163, 184, 0.2);
  border-color: rgba(148, 163, 184, 0.3);
  color: #ffffff;
}

.code-copy-btn .copy-icon,
.code-copy-btn .check-icon {
  width: 1rem;
  height: 1rem;
}

.code-copy-btn .hidden {
  display: none;
}

.code-copy-btn .check-icon {
  color: #10b981;
}

/* 코드 블록 */
.prose pre {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  padding: 1.25rem;
  border-radius: 0;
  overflow-x: auto;
  overflow-y: hidden;
  border: none;
  margin: 0;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
  position: relative;
  box-shadow: none;
}

.prose pre::-webkit-scrollbar {
  height: 6px;
}

.prose pre::-webkit-scrollbar-track {
  background: rgba(148, 163, 184, 0.1);
  border-radius: 3px;
}

.prose pre::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.prose pre::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

.dark .prose pre {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.code-block-wrapper pre {
  margin: 0;
  border-radius: 0;
}

.prose pre::-webkit-scrollbar {
  height: 8px;
}

.prose pre::-webkit-scrollbar-track {
  background: hsl(var(--muted));
  border-radius: 4px;
}

.prose pre::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 4px;
}

.prose pre::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}

.prose pre code {
  background-color: transparent;
  padding: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
  font-size: 0.9em;
  line-height: 1.7;
  display: block;
  white-space: pre;
  word-wrap: normal;
  word-break: normal;
  color: #e2e8f0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  max-width: 100%;
  overflow-x: auto;
}

.dark .prose pre code {
  color: #cbd5e1;
}

.prose ul, .prose ol {
  margin: 1.25em 0;
  padding-left: 1.75em;
  word-wrap: break-word;
}

.prose ul {
  list-style-type: disc;
}

.prose ol {
  list-style-type: decimal;
}

.prose li {
  margin: 0.625em 0;
  word-wrap: break-word;
  line-height: 1.7;
  padding-left: 0.25em;
  color: #1f2937; /* 검정색에 가까운 진한 회색 */
}

.dark .prose li {
  color: #f3f4f6; /* 다크 모드에서는 밝은 회색 */
}

.prose li::marker {
  color: hsl(var(--primary));
  font-weight: 600;
}

.prose p {
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
  margin: 1em 0;
  line-height: 1.75;
  font-size: 15px;
  max-width: 100%;
  overflow-x: hidden;
}

.prose blockquote {
  border-left: 4px solid hsl(var(--primary));
  padding: 1em 1.5em;
  margin: 1.5em 0;
  background: hsl(var(--muted) / 0.3);
  border-radius: 0.5rem;
  color: #1f2937; /* 검정색에 가까운 진한 회색 */
  font-style: italic;
  position: relative;
}

.dark .prose blockquote {
  color: #f3f4f6; /* 다크 모드에서는 밝은 회색 */
}

.prose blockquote::before {
  content: '"';
  font-size: 3em;
  position: absolute;
  left: 0.5em;
  top: 0.25em;
  color: hsl(var(--primary) / 0.3);
  font-family: serif;
  line-height: 1;
}

.prose table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.prose th, .prose td {
  border: 1px solid hsl(var(--border));
  padding: 0.5em;
  text-align: left;
}

.prose th {
  background-color: hsl(var(--muted));
  font-weight: 600;
}

/* 카드 스타일 개선 */
:deep(.el-card) {
  border: 1px solid hsl(var(--border));
  max-width: 100%;
  box-sizing: border-box;
}

:deep(.el-card__header) {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid hsl(var(--border));
  background-color: hsl(var(--muted) / 0.3);
}

:deep(.el-card__body) {
  padding: 1rem;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 메시지 컨테이너 내부 요소들이 칸 안에 맞도록 */
.prose img {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
}

.prose table {
  display: block;
  overflow-x: auto;
  white-space: nowrap;
  max-width: 100%;
  width: 100%;
  table-layout: auto;
}

.prose table::-webkit-scrollbar {
  height: 6px;
}

.prose table::-webkit-scrollbar-track {
  background: hsl(var(--muted));
  border-radius: 3px;
}

.prose table::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 3px;
}

.prose table::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}

/* 사용자 메시지 스타일 */
.user-message-bubble {
  background-color: #ffffff !important;
  color: #1f2937;
  border: 2px solid #bfdbfe; /* 파란색 테두리 */
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1), 0 2px 4px -1px rgba(59, 130, 246, 0.06);
  position: relative;
  transition: all 0.3s ease;
  max-width: 100%;
  overflow-x: hidden;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
}

.user-message-bubble:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.15), 0 4px 6px -1px rgba(59, 130, 246, 0.1);
  border-color: #93c5fd;
}

.user-message-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 0.75rem 0.75rem 0 0;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.user-message-bubble:hover::before {
  opacity: 1;
}

.user-message-content {
  color: #1f2937; /* 검정색에 가까운 진한 회색 */
  font-size: 15px;
}

.user-message-content :deep(p) {
  color: #1f2937;
  margin: 0.5em 0;
  line-height: 1.7;
  font-size: 15px;
}

.user-message-content :deep(code:not(pre code)) {
  background-color: rgba(59, 130, 246, 0.1);
  color: #2563eb;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  border: 1px solid rgba(59, 130, 246, 0.2);
  font-weight: 500;
}

.user-avatar {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
  transition: all 0.2s ease;
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
}

/* AI 메시지 스타일 */
.assistant-message-bubble {
  transition: all 0.3s ease;
  position: relative;
  background-color: #ffffff !important; /* 강제로 흰색 배경 */
  max-width: 100%;
  overflow-x: hidden;
  word-wrap: break-word;
  overflow-wrap: break-word;
  word-break: break-word;
}

.dark .assistant-message-bubble {
  background-color: #1f2937 !important; /* 다크 모드에서는 어두운 회색 */
}

.assistant-message-bubble:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.15), 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.assistant-message-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #8b5cf6 0%, #6366f1 100%);
  border-radius: 0.75rem 0.75rem 0 0;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.assistant-message-bubble:hover::before {
  opacity: 1;
}

/* 메시지 복사 버튼 */
.copy-message-btn {
  background-color: rgba(255, 255, 255, 0.9) !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
  color: #6b7280 !important;
  transition: all 0.2s ease;
}

.copy-message-btn:hover {
  background-color: rgba(255, 255, 255, 1) !important;
  border-color: rgba(0, 0, 0, 0.2) !important;
  color: #2563eb !important;
  transform: scale(1.1);
}

.copy-message-btn .el-icon {
  color: inherit;
}

.dark .copy-message-btn {
  background-color: rgba(31, 41, 55, 0.9) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #9ca3af !important;
}

.dark .copy-message-btn:hover {
  background-color: rgba(31, 41, 55, 1) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
  color: #60a5fa !important;
}

.assistant-content {
  color: #1f2937; /* 검정색에 가까운 진한 회색 */
  max-width: 100%;
  overflow-x: hidden;
  word-break: break-word;
  overflow-wrap: break-word;
  font-size: 15px;
}

.dark .assistant-content {
  color: #f3f4f6; /* 다크 모드에서는 밝은 회색 */
}

.assistant-content :deep(p) {
  margin: 0.875em 0;
  line-height: 1.8;
  font-size: 15px;
  color: #1f2937; /* 검정색에 가까운 진한 회색 */
  max-width: 100%;
  overflow-x: hidden;
  word-break: break-word;
  overflow-wrap: break-word;
}

.dark .assistant-content :deep(p) {
  color: #f3f4f6; /* 다크 모드에서는 밝은 회색 */
}

.assistant-content :deep(ul), .assistant-content :deep(ol) {
  margin: 0.75em 0;
  padding-left: 1.5em;
}

.assistant-content :deep(li) {
  margin: 0.5em 0;
  line-height: 1.6;
}

.ai-avatar {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3);
}

/* 인라인 코드 스타일 개선 */
.prose code:not(pre code) {
  background-color: hsl(var(--muted));
  padding: 0.2rem 0.4rem;
  border-radius: 0.375rem;
  font-size: 0.875em;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
  word-break: break-all;
  white-space: pre-wrap;
  border: 1px solid hsl(var(--border));
  color: #e11d48;
  font-weight: 500;
}

.dark .prose code:not(pre code) {
  background-color: hsl(var(--muted));
  color: #f87171;
  border-color: hsl(var(--border));
}

.assistant-content :deep(code:not(pre code)) {
  background-color: rgba(59, 130, 246, 0.1);
  color: #2563eb;
  border-color: rgba(59, 130, 246, 0.2);
}

.dark .assistant-content :deep(code:not(pre code)) {
  background-color: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border-color: rgba(139, 92, 246, 0.3);
}

/* 스트리밍 중 AI 아바타 애니메이션 */
.ai-avatar-streaming {
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3), 0 0 0 0 rgba(139, 92, 246, 0.7);
  }
  50% {
    box-shadow: 0 2px 4px rgba(139, 92, 246, 0.3), 0 0 0 4px rgba(139, 92, 246, 0);
  }
}

/* 타이핑 애니메이션 */
.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #6b7280;
  display: inline-block;
  animation: typing 1.4s infinite ease-in-out;
}

.dark .typing-dot {
  background-color: #9ca3af;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

.typing-text {
  animation: typing-text 1.5s infinite;
}

@keyframes typing-text {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 메타데이터 섹션 스타일 */
.metadata-collapse {
  border: none;
}

.metadata-collapse :deep(.el-collapse-item__header) {
  padding: 0.5rem 0;
  border: none;
  background: transparent;
  font-size: 0.75rem;
}

.metadata-collapse :deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

.metadata-collapse :deep(.el-collapse-item__content) {
  padding: 0.5rem 0;
}

.metadata-section {
  padding-bottom: 0.75rem;
}

.metadata-section:not(:last-child) {
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}

.dark .metadata-section:not(:last-child) {
  border-bottom-color: rgba(55, 65, 81, 0.5);
}

.source-item {
  transition: all 0.2s ease;
}

.source-item:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.dark .source-item:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>

