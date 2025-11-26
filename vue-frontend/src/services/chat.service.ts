import { apiService } from './api'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
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
  metadata?: any
}

export interface SendMessageRequest {
  message: string
  session_id?: string
  use_rag?: boolean
  use_search?: boolean
  rag_mode?: string
  model_type?: string
  collection_names?: string[]
  custom_params?: Record<string, any>
}

export interface ChatResponse {
  success: boolean
  user_message?: ChatMessage
  assistant_message?: ChatMessage
  context?: Array<{
    id?: string
    filename?: string
    metadata?: {
      filename?: string
      file_name?: string
    }
    similarity?: number
    content?: string
    content_preview?: string
  }>
  metadata?: {
    context_count?: number
    similarity_scores?: number[]
    similarity?: number
    avg_similarity?: number
    context_files?: string[]
    fallback_used?: boolean
  }
  error?: string
}

export class ChatService {
  async createSession(): Promise<{ success: boolean; session_id: string }> {
    return apiService.post('/api/chat/session')
  }

  async sendMessage(request: SendMessageRequest): Promise<ChatResponse> {
    return apiService.post<ChatResponse>('/api/chat/message', request)
  }

  async getChatHistory(sessionId: string, limit?: number): Promise<{ success: boolean; messages: ChatMessage[] }> {
    const params = limit ? { limit } : {}
    return apiService.get(`/api/chat/history/${sessionId}`, { params })
  }

  async getSessions(userId?: string): Promise<{ success: boolean; sessions: string[] }> {
    const params = userId ? { user_id: userId } : {}
    return apiService.get('/api/chat/sessions', { params })
  }

  async getSession(sessionId: string): Promise<any> {
    return apiService.get(`/api/chat/sessions/${sessionId}`)
  }

  async deleteSession(sessionId: string): Promise<{ success: boolean }> {
    return apiService.delete(`/api/chat/session/${sessionId}/delete`)
  }

  async clearSession(sessionId: string): Promise<{ success: boolean }> {
    return apiService.delete(`/api/chat/session/${sessionId}`)
  }

  async getSessionStats(sessionId: string): Promise<any> {
    return apiService.get(`/api/chat/session/${sessionId}/stats`)
  }

  async updateSessionTitle(sessionId: string, title: string, userId?: string): Promise<{ success: boolean }> {
    return apiService.put(`/api/chat/sessions/${sessionId}/title`, {
      title: title,
      user_id: userId || 'default'
    })
  }

  async updateSessionDescription(sessionId: string, description: string, userId?: string): Promise<{ success: boolean }> {
    return apiService.put(`/api/chat/sessions/${sessionId}/description`, {
      description: description,
      user_id: userId || 'default'
    })
  }

  async saveMessage(sessionId: string, message: ChatMessage): Promise<{ success: boolean }> {
    return apiService.post('/api/chat/save-message', {
      session_id: sessionId,
      message: {
        id: message.id,
        role: message.role,
        content: message.content,
        timestamp: message.timestamp,
        // Include sources, accuracy, and metadata for full message persistence
        sources: message.sources || [],
        accuracy: message.accuracy || null,
        metadata: message.metadata || {}
      }
    })
  }

  async streamMessage(
    request: SendMessageRequest,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void,
    onMetadata?: (metadata: { sources?: ChatMessage['sources'], accuracy?: ChatMessage['accuracy'], model_info?: Record<string, string> }) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${apiService['client'].defaults.baseURL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error('Stream request failed')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      let buffer = ''
      let currentEvent = 'message'

      // SSE 라인을 처리하는 헬퍼 함수
      const processLines = (lines: string[]) => {
        let eventType = currentEvent
        let eventData = ''
        let shouldComplete = false

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue

          if (trimmed.startsWith('event: ')) {
            eventType = trimmed.slice(7).trim()
          } else if (trimmed.startsWith('data: ')) {
            eventData = trimmed.slice(6)
            if (eventData === '[DONE]') {
              shouldComplete = true
              continue // [DONE] 이후에도 남은 라인 처리
            }

            try {
              const parsed = JSON.parse(eventData)

              // context 이벤트 처리 (메타데이터)
              if (eventType === 'context') {
                // sources 생성 - detailed_sources가 있으면 우선 사용
                let sources = []
                if (parsed.detailed_sources && parsed.detailed_sources.length > 0) {
                  sources = parsed.detailed_sources.map((doc: any) => ({
                    filename: doc.filename || 'Unknown',
                    similarity_score: doc.similarity_score || 0,
                    content_preview: doc.content_preview || '',
                    document_id: doc.document_id || ''
                  }))
                } else if (parsed.sources && parsed.sources.length > 0) {
                  // fallback: sources 배열에서 생성
                  const similarityScores = parsed.similarity_scores || []
                  sources = parsed.sources.map((filename: string, idx: number) => ({
                    filename,
                    similarity_score: similarityScores[idx] || 0,
                    content_preview: '',
                    document_id: ''
                  }))
                }

                // accuracy 생성 - parsed.accuracy가 있으면 우선 사용
                let accuracy = null
                if (parsed.accuracy) {
                  accuracy = parsed.accuracy
                } else {
                  const similarityScores = parsed.similarity_scores || []
                  const avgSimilarity = parsed.similarity || 
                    (similarityScores.length > 0 ? similarityScores.reduce((a: number, b: number) => a + b, 0) / similarityScores.length : 0)

                  if (parsed.context_count > 0 || similarityScores.length > 0) {
                    accuracy = {
                      confidence_score: avgSimilarity,
                      context_count: parsed.context_count || 0,
                      avg_similarity: avgSimilarity,
                      fallback_used: false
                    }
                  }
                }

                if (onMetadata) {
                  onMetadata({ sources, accuracy })
                }
              }

              // message 이벤트 처리 (content 및 completion)
              if (eventType === 'message') {
                if (parsed.content !== undefined && parsed.content !== '') {
                  onChunk(parsed.content)
                }
                // completion 이벤트 처리 (model_info 포함)
                if (parsed.finished === true && parsed.type === 'completion' && parsed.model_info && onMetadata) {
                  console.log('[ChatService] Received model_info:', parsed.model_info)
                  onMetadata({ model_info: parsed.model_info })
                }
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, 'Data:', eventData)
            }

            // 이벤트 처리 후 초기화
            eventType = 'message'
            eventData = ''
          }
        }

        return shouldComplete
      }

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          // 스트림 종료 시 버퍼에 남아있는 데이터 처리 (completion 이벤트 포함)
          if (buffer.trim()) {
            const remainingLines = buffer.split('\n')
            processLines(remainingLines)
          }
          onComplete()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 마지막 불완전한 라인은 버퍼에 보관

        const shouldComplete = processLines(lines)
        if (shouldComplete) {
          onComplete()
          return
        }
      }
    } catch (error) {
      onError(error as Error)
    }
  }
}

export const chatService = new ChatService()

