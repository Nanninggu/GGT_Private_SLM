import { apiService } from './api'

export interface Document {
  id: string
  content: string
  metadata?: Record<string, any>
}

export class DocumentService {
  async uploadFile(file: File, collectionName?: string): Promise<{ success: boolean; message?: string }> {
    const formData = new FormData()
    formData.append('file', file)
    if (collectionName) {
      formData.append('collection_name', collectionName)
    }

    return apiService.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000, // 10분
    })
  }

  async uploadMultipleFiles(files: File[], collectionName?: string): Promise<{ success: boolean; message?: string }> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    if (collectionName) {
      formData.append('collection_name', collectionName)
    }

    return apiService.post('/api/upload/multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000,
    })
  }

  async uploadFileLangChain(file: File, collectionName?: string): Promise<{ success: boolean; message?: string }> {
    const formData = new FormData()
    formData.append('file', file)
    if (collectionName) {
      formData.append('collection_name', collectionName)
    }

    return apiService.post('/api/langchain/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000, // 10분
    })
  }

  async getDocuments(params?: {
    collection_name?: string
    limit?: number
    offset?: number
    order_by?: string
    order_direction?: string
  }): Promise<{ success: boolean; documents?: any[]; total?: number; limit?: number; offset?: number }> {
    return apiService.get('/api/documents', { params })
  }

  async getDocument(docId: string): Promise<any> {
    return apiService.get(`/api/documents/${docId}`)
  }

  async deleteDocument(docId: string): Promise<{ success: boolean }> {
    return apiService.delete(`/api/documents/${docId}`)
  }
}

export const documentService = new DocumentService()

