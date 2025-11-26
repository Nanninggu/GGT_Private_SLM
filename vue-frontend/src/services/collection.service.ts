import { apiService } from './api'

export interface Collection {
  name: string
  description?: string
  type?: 'personal' | 'shared'
  user_id?: string
}

export class CollectionService {
  async getCollections(): Promise<{ success: boolean; collections?: Collection[] }> {
    return apiService.get('/api/collections')
  }

  async getActiveCollection(): Promise<{ success: boolean; collection_name?: string }> {
    return apiService.get('/api/collections/active')
  }

  async switchCollection(collectionName: string): Promise<{ success: boolean }> {
    return apiService.post('/api/collections/switch', { collection_name: collectionName })
  }

  async createCollection(name: string, description?: string, type: 'personal' | 'shared' = 'personal'): Promise<{ success: boolean }> {
    return apiService.post('/api/collections/create', { collection_name: name, description, type })
  }

  async deleteCollection(collectionName: string): Promise<{ success: boolean }> {
    return apiService.delete(`/api/collections/${collectionName}`)
  }

  async getCollectionInfo(collectionName: string): Promise<any> {
    return apiService.get(`/api/collections/info/${collectionName}`)
  }
}

export const collectionService = new CollectionService()

