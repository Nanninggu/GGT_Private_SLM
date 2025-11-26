<template>
  <div class="h-full p-6">
    <div class="max-w-6xl mx-auto">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">웹 검색</h2>

      <!-- Search Form -->
      <el-card class="mb-6">
        <el-form :model="searchForm" label-width="120px">
          <el-form-item label="검색어">
            <el-input
              v-model="searchForm.query"
              placeholder="검색어를 입력하세요"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-tooltip content="웹에서 정보를 검색합니다" placement="top" effect="dark">
                  <el-button :icon="Search" @click="handleSearch" :loading="searching">
                    검색
                  </el-button>
                </el-tooltip>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="결과 수">
            <el-tooltip content="가져올 검색 결과의 개수를 설정합니다 (1-50)" placement="top" effect="dark">
              <el-input-number v-model="searchForm.num_results" :min="1" :max="50" />
            </el-tooltip>
          </el-form-item>
          <el-form-item label="검색 엔진">
            <el-tooltip content="사용할 검색 엔진을 선택합니다" placement="top" effect="dark">
              <el-select v-model="searchForm.search_engine" style="width: 200px">
                <el-option label="DuckDuckGo" value="duckduckgo" />
                <el-option label="Google" value="google" />
              </el-select>
            </el-tooltip>
          </el-form-item>
          <el-form-item label="컬렉션에 저장">
            <el-tooltip content="검색 결과를 자동으로 벡터 컬렉션에 저장하여 RAG 검색에 활용할 수 있습니다" placement="top" effect="dark">
              <el-checkbox v-model="saveToCollection">검색 결과를 컬렉션에 저장</el-checkbox>
            </el-tooltip>
          </el-form-item>
          <el-form-item v-if="saveToCollection" label="컬렉션 선택">
            <el-select v-model="selectedCollection" filterable placeholder="컬렉션 선택">
              <el-option
                v-for="collection in collections"
                :key="collection"
                :label="collection"
                :value="collection"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- Results -->
      <div v-if="results.length > 0" class="space-y-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          검색 결과 ({{ results.length }}개)
        </h3>
        <el-card
          v-for="(result, index) in results"
          :key="index"
          class="mb-4"
          shadow="hover"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                <el-link :href="result.url" target="_blank" type="primary">
                  {{ result.title }}
                </el-link>
              </h4>
              <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">{{ result.snippet }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-500">{{ result.domain }}</p>
            </div>
            <el-link :href="result.url" target="_blank" :icon="Link">
              링크
            </el-link>
          </div>
        </el-card>
      </div>

      <div v-else-if="!searching" class="text-center py-12">
        <el-icon class="text-6xl text-gray-300 dark:text-gray-600 mb-4">
          <Search />
        </el-icon>
        <p class="text-gray-500 dark:text-gray-400">검색어를 입력하고 검색 버튼을 클릭하세요</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { webSearchService } from '@/services/web-search.service'
import { collectionService } from '@/services/collection.service'
import { Search, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const searchForm = ref({
  query: '',
  num_results: 10,
  search_engine: 'duckduckgo',
})

const saveToCollection = ref(false)
const selectedCollection = ref('')
const collections = ref<string[]>([])
const results = ref<any[]>([])
const searching = ref(false)

onMounted(async () => {
  await loadCollections()
})

const loadCollections = async () => {
  try {
    const response = await collectionService.getCollections()
    if (response.success && response.collections) {
      collections.value = response.collections.map((c: any) => c.name)
    }
  } catch (error) {
    console.error('Failed to load collections:', error)
  }
}

const handleSearch = async () => {
  if (!searchForm.value.query.trim()) {
    ElMessage.warning('검색어를 입력하세요.')
    return
  }

  searching.value = true
  results.value = []

  try {
    let response
    if (saveToCollection.value && selectedCollection.value) {
      response = await webSearchService.searchAndSave({
        ...searchForm.value,
        collection_name: selectedCollection.value,
        auto_save: true,
      })
      ElMessage.success('검색 결과가 컬렉션에 저장되었습니다.')
    } else {
      response = await webSearchService.search(searchForm.value)
    }

    if (response.success) {
      results.value = response.results || []
    } else {
      ElMessage.error(response.message || '검색에 실패했습니다.')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '검색 중 오류가 발생했습니다.')
  } finally {
    searching.value = false
  }
}
</script>

