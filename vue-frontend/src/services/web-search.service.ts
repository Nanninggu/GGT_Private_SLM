import { apiService } from './api'

export interface WebSearchRequest {
  query: string
  num_results?: number
  collection_name?: string
  search_engine?: string
}

export interface WebSearchResult {
  title: string
  url: string
  snippet: string
  content?: string
  domain?: string
}

export interface WebSearchResponse {
  success: boolean
  message: string
  results: WebSearchResult[]
  collection_name?: string
}

export class WebSearchService {
  async search(request: WebSearchRequest): Promise<WebSearchResponse> {
    return apiService.post<WebSearchResponse>('/api/web-search/search', request)
  }

  async searchAndSave(request: WebSearchRequest & { auto_save?: boolean }): Promise<WebSearchResponse> {
    return apiService.post<WebSearchResponse>('/api/web-search/search-and-save', {
      ...request,
      auto_save: request.auto_save ?? true,
    })
  }

  async getCollections(): Promise<{ success: boolean; collections?: string[] }> {
    return apiService.get('/api/web-search/collections')
  }
}

export const webSearchService = new WebSearchService()

