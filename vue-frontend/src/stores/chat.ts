import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatService, type ChatMessage } from '@/services/chat.service'
import { useAuthStore } from './auth'

// 세션별 설정 인터페이스
export interface SessionSettings {
  selectedCollection: string
  ragMode: string
  selectedModel: string
  useRag: boolean
}

// 기본 세션 설정
const DEFAULT_SESSION_SETTINGS: SessionSettings = {
  selectedCollection: '',
  ragMode: 'LangChain RAG',
  selectedModel: 'fast',
  useRag: true
}

export const useChatStore = defineStore('chat', () => {
  // localStorage에서 currentSessionId 복원
  const currentSessionId = ref<string | null>(
    localStorage.getItem('current_session_id')
  )
  const messages = ref<ChatMessage[]>([])
  const sessions = ref<string[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const streamingMetadata = ref<{
    sources?: Array<{
      filename: string
      similarity_score: number
      content_preview: string
      document_id: string
    }>
    accuracy?: {
      confidence_score: number
      context_count: number
      avg_similarity: number
      fallback_used: boolean
    }
    model_info?: Record<string, string>
  } | null>(null)
  
  // 현재 세션의 설정
  const currentSessionSettings = ref<SessionSettings>({ ...DEFAULT_SESSION_SETTINGS })

  // currentSessionId를 localStorage에 저장하는 헬퍼 함수
  function saveCurrentSessionId(sessionId: string | null) {
    if (sessionId) {
      localStorage.setItem('current_session_id', sessionId)
    } else {
      localStorage.removeItem('current_session_id')
    }
    currentSessionId.value = sessionId
  }

  // 세션별 설정 저장 키 생성
  function getSessionSettingsKey(sessionId: string): string {
    return `chat_session_settings_${sessionId}`
  }

  // 세션 설정 저장
  function saveSessionSettings(sessionId: string, settings: Partial<SessionSettings>) {
    try {
      const key = getSessionSettingsKey(sessionId)
      const existingSettings = loadSessionSettings(sessionId)
      const updatedSettings = { ...existingSettings, ...settings }
      localStorage.setItem(key, JSON.stringify(updatedSettings))
      console.log('[ChatStore] Session settings saved:', sessionId, updatedSettings)
    } catch (error) {
      console.error('[ChatStore] Failed to save session settings:', error)
    }
  }

  // 세션 설정 로드
  function loadSessionSettings(sessionId: string): SessionSettings {
    try {
      const key = getSessionSettingsKey(sessionId)
      const saved = localStorage.getItem(key)
      if (saved) {
        const parsed = JSON.parse(saved)
        console.log('[ChatStore] Session settings loaded:', sessionId, parsed)
        return { ...DEFAULT_SESSION_SETTINGS, ...parsed }
      }
    } catch (error) {
      console.error('[ChatStore] Failed to load session settings:', error)
    }
    return { ...DEFAULT_SESSION_SETTINGS }
  }

  // 현재 세션 설정 업데이트 및 저장
  function updateCurrentSessionSettings(settings: Partial<SessionSettings>) {
    if (currentSessionId.value) {
      currentSessionSettings.value = { ...currentSessionSettings.value, ...settings }
      saveSessionSettings(currentSessionId.value, currentSessionSettings.value)
    }
  }

  // 세션 설정 삭제 (세션 삭제 시 사용)
  function deleteSessionSettings(sessionId: string) {
    try {
      const key = getSessionSettingsKey(sessionId)
      localStorage.removeItem(key)
      console.log('[ChatStore] Session settings deleted:', sessionId)
    } catch (error) {
      console.error('[ChatStore] Failed to delete session settings:', error)
    }
  }

  async function createSession() {
    try {
      console.log('[ChatStore] Creating new session...')
      const response = await chatService.createSession()
      if (response.success && response.session_id) {
        const newSessionId = response.session_id
        console.log('[ChatStore] Session created successfully:', newSessionId)
        
        // 새 세션 ID를 세션 목록의 맨 앞에 추가 (중복 방지)
        if (!sessions.value.includes(newSessionId)) {
          sessions.value.unshift(newSessionId)
        }
        
        // 현재 세션 ID 저장
        saveCurrentSessionId(newSessionId)
        
        // 메시지 초기화
        messages.value = []
        
        console.log('[ChatStore] Current sessions:', sessions.value)
        return newSessionId
      } else {
        console.error('[ChatStore] Session creation failed: response not successful')
      }
    } catch (error) {
      console.error('[ChatStore] Failed to create session:', error)
    }
    return null
  }

  async function loadSessions() {
    const authStore = useAuthStore()
    // user.id (UUID)를 사용해야 함 (username이 아님)
    const userId = authStore.user?.id
    
    try {
      const response = await chatService.getSessions(userId)
      if (response.success) {
        sessions.value = response.sessions || []
        console.log('[ChatStore] Sessions loaded for user:', userId, 'count:', sessions.value.length)
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  async function loadChatHistory(sessionId: string) {
    try {
      console.log('[ChatStore] Loading chat history for session:', sessionId)
      const response = await chatService.getChatHistory(sessionId)
      console.log('[ChatStore] Response:', response)
      
      if (response.success) {
        const loadedMessages = response.messages || []
        
        // 중복 메시지 제거 (같은 ID 또는 같은 내용+타임스탬프 조합)
        const uniqueMessages: ChatMessage[] = []
        const seenIds = new Set<string>()
        const seenContentTime = new Set<string>()
        
        for (const msg of loadedMessages) {
          // ID 기준으로 중복 체크
          if (seenIds.has(msg.id)) {
            console.log('[ChatStore] Duplicate message found by ID, skipping:', msg.id)
            continue
          }
          
          // 내용과 타임스탬프 조합으로도 중복 체크 (ID가 다른 경우)
          const contentTimeKey = `${msg.role}:${msg.content.substring(0, 100)}:${msg.timestamp}`
          if (seenContentTime.has(contentTimeKey)) {
            console.log('[ChatStore] Duplicate message found by content+time, skipping:', msg.id)
            continue
          }
          
          seenIds.add(msg.id)
          seenContentTime.add(contentTimeKey)
          
          // 메시지 데이터를 명시적으로 구성하여 메타데이터가 제대로 포함되도록 함
          const formattedMessage: ChatMessage = {
            id: msg.id,
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp,
            // sources, accuracy, metadata가 명시적으로 할당되도록 보장
            sources: msg.sources || undefined,
            accuracy: msg.accuracy || undefined,
            metadata: msg.metadata || undefined
          }
          
          uniqueMessages.push(formattedMessage)
        }
        
        messages.value = uniqueMessages
        saveCurrentSessionId(sessionId)
        
        // 세션 설정도 함께 로드
        currentSessionSettings.value = loadSessionSettings(sessionId)
        console.log('[ChatStore] Session settings restored:', currentSessionSettings.value)
        
        console.log('[ChatStore] History loaded successfully, message count:', messages.value.length, '(removed', loadedMessages.length - uniqueMessages.length, 'duplicates)')
        
        // 로드된 메시지의 메타데이터 확인 로그
        const assistantMessages = messages.value.filter(m => m.role === 'assistant')
        console.log('[ChatStore] Assistant messages with metadata:', assistantMessages.map(m => ({
          id: m.id,
          hasSources: !!m.sources,
          hasAccuracy: !!m.accuracy,
          hasMetadata: !!m.metadata,
          sourcesCount: m.sources?.length || 0
        })))
      } else {
        console.error('[ChatStore] Failed to load chat history, response not successful:', response)
        throw new Error(response.error || 'Failed to load chat history')
      }
    } catch (error) {
      console.error('[ChatStore] Failed to load chat history:', error)
      // 세션 로드 실패 시 localStorage에서도 제거
      if (currentSessionId.value === sessionId) {
        saveCurrentSessionId(null)
      }
      throw error // 에러를 다시 throw하여 호출자가 처리할 수 있도록
    }
  }

  async function sendMessage(
    content: string,
    options?: {
      useRag?: boolean
      modelType?: string
      ragMode?: string
      collectionNames?: string[]
      onStream?: (chunk: string) => void
    }
  ) {
    // localStorage에서도 확인
    if (!currentSessionId.value) {
      const savedSessionId = localStorage.getItem('current_session_id')
      if (savedSessionId) {
        currentSessionId.value = savedSessionId
      } else {
        await createSession()
      }
    }

    isLoading.value = true
    // UUID 형식의 메시지 ID 생성 (백엔드와 호환성을 위해)
    const userMessageId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const userMessage: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    messages.value.push(userMessage)

    try {
      if (options?.onStream) {
        // 스트리밍 모드
        isStreaming.value = true
        streamingContent.value = ''
        streamingMetadata.value = null

        await chatService.streamMessage(
          {
            message: content,
            session_id: currentSessionId.value || undefined,
            use_rag: options.useRag ?? true,
            rag_mode: options.ragMode || 'LangChain RAG',
            model_type: options.modelType || 'fast',
            collection_names: options.collectionNames,
          },
          (chunk) => {
            streamingContent.value += chunk
            options.onStream?.(chunk)
          },
          async () => {
            isStreaming.value = false
            if (streamingContent.value && currentSessionId.value) {
              // UUID 형식의 메시지 ID 생성 (백엔드와 호환성을 위해)
              const assistantMessageId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now() + 1}-${Math.random().toString(36).substr(2, 9)}`
              
              // metadata 객체 구성 - model_info가 있으면 포함
              const messageMetadata: any = {}
              if (streamingMetadata.value?.model_info) {
                messageMetadata.model_info = streamingMetadata.value.model_info
              }
              
              const assistantMessage: ChatMessage = {
                id: assistantMessageId,
                role: 'assistant',
                content: streamingContent.value,
                timestamp: new Date().toISOString(),
                sources: streamingMetadata.value?.sources,
                accuracy: streamingMetadata.value?.accuracy,
                metadata: Object.keys(messageMetadata).length > 0 ? messageMetadata : undefined
              }
              messages.value.push(assistantMessage)
              
              // 스트리밍 완료 후 assistant 메시지를 명시적으로 백엔드에 저장
              // (백엔드 스트리밍에서 저장이 실패할 수 있으므로 프론트엔드에서 확실히 저장)
              try {
                console.log('[ChatStore] Saving assistant message to backend with metadata:', {
                  id: assistantMessage.id,
                  hasSources: !!assistantMessage.sources?.length,
                  hasAccuracy: !!assistantMessage.accuracy,
                  hasModelInfo: !!assistantMessage.metadata?.model_info,
                  modelInfo: assistantMessage.metadata?.model_info
                })
                await chatService.saveMessage(currentSessionId.value, assistantMessage)
                console.log('[ChatStore] Assistant message saved successfully')
              } catch (saveError) {
                console.error('[ChatStore] Failed to save assistant message:', saveError)
              }
              
              streamingContent.value = ''
              streamingMetadata.value = null
            }
            isLoading.value = false
          },
          (error) => {
            console.error('Stream error:', error)
            isStreaming.value = false
            isLoading.value = false
            streamingMetadata.value = null
          },
          (metadata) => {
            // 스트리밍 중 메타데이터 수신
            console.log('[ChatStore] Received streaming metadata:', metadata)
            
            // 항상 streamingMetadata를 업데이트 (어떤 필드든 있으면)
            if (metadata.sources || metadata.accuracy || metadata.model_info) {
              streamingMetadata.value = {
                sources: metadata.sources || streamingMetadata.value?.sources,
                accuracy: metadata.accuracy || streamingMetadata.value?.accuracy,
                model_info: metadata.model_info || streamingMetadata.value?.model_info
              }
              console.log('[ChatStore] Updated streamingMetadata:', streamingMetadata.value)
            }
          }
        )
      } else {
        // 일반 모드
        const response = await chatService.sendMessage({
          message: content,
          session_id: currentSessionId.value || undefined,
          use_rag: options?.useRag ?? true,
          rag_mode: options?.ragMode || 'LangChain RAG',
          model_type: options?.modelType || 'fast',
          collection_names: options?.collectionNames,
        })

        if (response.success && response.assistant_message) {
          const assistantMsg = { ...response.assistant_message }
          
          // 백엔드에서 직접 제공하는 sources와 accuracy를 우선 사용
          if (response.assistant_message.sources && response.assistant_message.sources.length > 0) {
            assistantMsg.sources = response.assistant_message.sources
          } else if (response.context && response.context.length > 0) {
            // fallback: context에서 sources 생성
            assistantMsg.sources = response.context.map((doc: any) => {
              const filename = doc.filename || doc.metadata?.filename || doc.metadata?.file_name || 'Unknown'
              const similarity = doc.similarity || 0
              const contentPreview = doc.content_preview || doc.content?.substring(0, 200) || ''
              const documentId = doc.id || doc.document_id || ''
              
              return {
                filename,
                similarity_score: similarity,
                content_preview: contentPreview,
                document_id: documentId
              }
            })
          }
          
          // 백엔드에서 직접 제공하는 accuracy를 우선 사용
          if (response.assistant_message.accuracy) {
            assistantMsg.accuracy = response.assistant_message.accuracy
          } else if (response.metadata) {
            // fallback: metadata에서 accuracy 생성
            const metadata = response.metadata
            const similarityScores = metadata.similarity_scores || []
            const avgSimilarity = metadata.similarity || metadata.avg_similarity || 
              (similarityScores.length > 0 ? similarityScores.reduce((a: number, b: number) => a + b, 0) / similarityScores.length : 0)
            
            if (metadata.context_count > 0 || similarityScores.length > 0) {
              assistantMsg.accuracy = {
                confidence_score: avgSimilarity,
                context_count: metadata.context_count || 0,
                avg_similarity: avgSimilarity,
                fallback_used: metadata.fallback_used || false
              }
            }
          }
          
          // metadata에 model_info 포함 (백엔드에서 제공하는 경우)
          if (response.assistant_message.metadata) {
            // 기존 metadata가 있으면 병합, 없으면 새로 생성
            assistantMsg.metadata = {
              ...(assistantMsg.metadata || {}),
              ...response.assistant_message.metadata
            }
          } else if (response.assistant_message.metadata?.model_info) {
            // metadata가 없지만 model_info만 있는 경우
            assistantMsg.metadata = {
              model_info: response.assistant_message.metadata.model_info
            }
          }
          
          messages.value.push(assistantMsg)
          
          // 백엔드의 /api/chat/message 엔드포인트에서 이미 user 메시지와 assistant 메시지를 저장하므로
          // 프론트엔드에서는 저장하지 않음 (중복 저장 방지)
          // 백엔드에서 생성한 메시지 ID와 프론트엔드에서 생성한 메시지 ID가 다르면 중복 저장이 발생하므로
          // 백업 저장을 제거하고 백엔드 저장에만 의존
          console.log('[ChatStore] Messages displayed in UI (backend has already saved with different IDs)')
        } else {
          // UUID 형식의 메시지 ID 생성 (백엔드와 호환성을 위해)
          const errorMessageId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now() + 1}-${Math.random().toString(36).substr(2, 9)}`
          const errorMessage: ChatMessage = {
            id: errorMessageId,
            role: 'assistant',
            content: response.error || '응답을 받을 수 없습니다.',
            timestamp: new Date().toISOString(),
          }
          messages.value.push(errorMessage)
          
          // 에러 메시지는 백엔드에 저장되지 않을 수 있으므로 명시적으로 저장 시도
          if (currentSessionId.value) {
            try {
              console.log('[ChatStore] Saving error messages (user message and error response)')
              await Promise.allSettled([
                chatService.saveMessage(currentSessionId.value, userMessage).catch(() => {}),
                chatService.saveMessage(currentSessionId.value, errorMessage).catch(() => {})
              ])
              console.log('[ChatStore] Error messages saved')
            } catch (error) {
              console.error('[ChatStore] Failed to save error messages:', error)
            }
          }
        }
        isLoading.value = false
      }
    } catch (error: any) {
      // UUID 형식의 메시지 ID 생성 (백엔드와 호환성을 위해)
      const errorMessageId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now() + 1}-${Math.random().toString(36).substr(2, 9)}`
      messages.value.push({
        id: errorMessageId,
        role: 'assistant',
        content: error.message || '메시지 전송에 실패했습니다.',
        timestamp: new Date().toISOString(),
      })
      isLoading.value = false
    }
  }

  async function deleteSession(sessionId: string) {
    try {
      await chatService.deleteSession(sessionId)
      // 세션 설정도 함께 삭제
      deleteSessionSettings(sessionId)
      
      if (currentSessionId.value === sessionId) {
        saveCurrentSessionId(null)
        messages.value = []
        currentSessionSettings.value = { ...DEFAULT_SESSION_SETTINGS }
      }
      await loadSessions()
    } catch (error) {
      console.error('Failed to delete session:', error)
    }
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    currentSessionId,
    messages,
    sessions,
    isLoading,
    isStreaming,
    streamingContent,
    currentSessionSettings,
    createSession,
    loadSessions,
    loadChatHistory,
    sendMessage,
    deleteSession,
    clearMessages,
    updateCurrentSessionSettings,
    loadSessionSettings,
    saveSessionSettings,
  }
})

