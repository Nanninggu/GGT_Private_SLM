<template>
  <div class="h-full p-6 bg-background">
    <div class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-foreground">데이터셋 관리</h2>
          <p class="text-sm text-muted-foreground mt-1">벡터 데이터셋을 관리하고 문서를 그룹화하세요</p>
        </div>
        <el-tooltip
          content="새로운 벡터 데이터셋을 생성하여 문서를 그룹화할 수 있습니다"
          placement="bottom"
          effect="dark"
        >
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            새 데이터셋
          </el-button>
        </el-tooltip>
      </div>

      <!-- Statistics -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.totalCollections }}</div>
            <div class="text-sm text-muted-foreground mt-1">총 데이터셋 수</div>
          </div>
        </el-card>
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.totalDocuments }}</div>
            <div class="text-sm text-muted-foreground mt-1">총 문서 수</div>
          </div>
        </el-card>
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.activeCollection || '없음' }}</div>
            <div class="text-sm text-muted-foreground mt-1">활성 데이터셋</div>
          </div>
        </el-card>
        <el-card class="bg-card border-border">
          <div class="text-center">
            <div class="text-2xl font-bold text-foreground">{{ stats.avgDocuments.toFixed(1) }}</div>
            <div class="text-sm text-muted-foreground mt-1">평균 문서 수</div>
          </div>
        </el-card>
      </div>

      <!-- Collection List -->
      <el-card class="bg-card border-border">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="text-foreground font-semibold">데이터셋 목록 ({{ collections.length }}개)</span>
            <el-button :icon="Refresh" @click="handleRefresh">새로고침</el-button>
          </div>
        </template>

        <el-table
          :data="collections"
          v-loading="loading"
          class="bg-card"
          style="width: 100%"
        >
          <el-table-column prop="name" label="데이터셋명" min-width="200">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <span class="font-semibold text-foreground">{{ row.name }}</span>
                <el-tag v-if="activeCollection === row.name" type="success" size="small">
                  활성
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="문서 수" width="120">
            <template #default="{ row }">
              <el-tooltip
                :content="`이 데이터셋에 ${row.document_count || 0}개의 문서가 저장되어 있습니다`"
                placement="top"
                effect="dark"
              >
                <span class="text-foreground font-semibold">{{ row.document_count || 0 }}개</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="type" label="타입" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'shared' ? 'success' : 'primary'">
                {{ row.type === 'shared' ? '공유' : '개인' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="생성일" width="180">
            <template #default="{ row }">
              <span v-if="row.name === 'documents' || row.name === 'langchain_documents'">
                기본 데이터셋
              </span>
              <span v-else>
              {{ formatDate(row.created_at) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="작업" width="250">
            <template #default="{ row }">
              <div class="flex gap-2">
                <el-tooltip
                  v-if="activeCollection !== row.name"
                  content="이 데이터셋을 활성화합니다"
                  placement="top"
                  effect="dark"
                >
                  <el-button
                    size="small"
                    :icon="Check"
                    @click="handleSwitchCollection(row.name)"
                  >
                    선택
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="데이터셋 상세 정보를 확인합니다"
                  placement="top"
                  effect="dark"
                >
                  <el-button
                    size="small"
                    :icon="View"
                    @click="handleViewInfo(row)"
                  >
                    정보
                  </el-button>
                </el-tooltip>
                <el-tooltip
                  content="데이터셋을 삭제합니다 (주의: 되돌릴 수 없습니다)"
                  placement="top"
                  effect="dark"
                >
                  <el-button
                    size="small"
                    type="danger"
                    :icon="Delete"
                    @click="handleDeleteCollection(row.name)"
                    :disabled="row.name === 'langchain_documents' || row.name === 'documents'"
                  >
                    삭제
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div v-if="collections.length === 0" class="text-center py-12">
          <div class="text-muted-foreground/50 text-lg mb-2">데이터셋이 없습니다</div>
          <div class="text-sm text-muted-foreground/80">새 데이터셋을 생성하여 문서를 그룹화하세요</div>
        </div>
      </el-card>

      <!-- Create Collection Dialog -->
      <el-dialog v-model="showCreateDialog" title="새 데이터셋" width="500px">
        <el-form :model="newCollection" label-width="100px">
          <el-form-item label="데이터셋명">
            <el-input v-model="newCollection.name" placeholder="데이터셋명을 입력하세요" />
          </el-form-item>
          <el-form-item label="타입">
            <el-radio-group v-model="newCollection.type">
              <el-radio label="personal">
                <span>개인</span>
                <el-tooltip content="해당 계정에서만 사용 가능한 데이터셋입니다" placement="right" effect="dark">
                  <el-icon class="ml-1"><QuestionFilled /></el-icon>
                </el-tooltip>
              </el-radio>
              <el-radio label="shared">
                <span>공유</span>
                <el-tooltip content="모든 사용자가 사용할 수 있는 데이터셋입니다" placement="right" effect="dark">
                  <el-icon class="ml-1"><QuestionFilled /></el-icon>
                </el-tooltip>
              </el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="설명">
            <el-input
              v-model="newCollection.description"
              type="textarea"
              :rows="3"
              placeholder="데이터셋 설명을 입력하세요"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showCreateDialog = false">취소</el-button>
          <el-button type="primary" @click="handleCreateCollection">생성</el-button>
        </template>
      </el-dialog>

      <!-- Collection Info Dialog -->
      <el-dialog v-model="showInfoDialog" title="데이터셋 정보" width="600px">
        <div v-if="selectedCollection" class="space-y-4">
          <div>
            <div class="text-sm text-muted-foreground mb-1">데이터셋명</div>
            <div class="text-lg font-semibold text-foreground">{{ selectedCollection.name }}</div>
          </div>
          <div>
            <div class="text-sm text-muted-foreground mb-1">문서 수</div>
            <div class="text-lg font-semibold text-foreground">{{ selectedCollection.document_count || 0 }}개</div>
          </div>
          <div>
            <div class="text-sm text-muted-foreground mb-1">타입</div>
            <el-tag :type="selectedCollection.type === 'shared' ? 'success' : 'primary'">
              {{ selectedCollection.type === 'shared' ? '공유' : '개인' }}
            </el-tag>
          </div>
          <div v-if="selectedCollection.description">
            <div class="text-sm text-muted-foreground mb-1">설명</div>
            <div class="text-foreground">{{ selectedCollection.description }}</div>
          </div>
          <div>
            <div class="text-sm text-muted-foreground mb-1">생성일</div>
            <div class="text-foreground">
              <span v-if="selectedCollection.name === 'documents' || selectedCollection.name === 'langchain_documents'">
                기본 데이터셋
              </span>
              <span v-else>
                {{ formatDate(selectedCollection.created_at) }}
              </span>
            </div>
          </div>
          <div v-if="selectedCollection.metadata">
            <div class="text-sm text-muted-foreground mb-1">메타데이터</div>
            <pre class="text-xs bg-muted p-3 rounded overflow-auto max-h-40">{{ JSON.stringify(selectedCollection.metadata, null, 2) }}</pre>
          </div>
        </div>
        <template #footer>
          <el-button @click="showInfoDialog = false">닫기</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { collectionService } from '@/services/collection.service'
import { Plus, Delete, Check, Refresh, View, QuestionFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const collections = ref<any[]>([])
const activeCollection = ref<string>('')
const loading = ref(false)
const showCreateDialog = ref(false)
const showInfoDialog = ref(false)
const selectedCollection = ref<any>(null)
const newCollection = ref({
  name: '',
  description: '',
  type: 'personal' as 'personal' | 'shared',
})

const stats = computed(() => {
  const totalCollections = collections.value.length
  const totalDocuments = collections.value.reduce((sum, c) => sum + (c.document_count || 0), 0)
  const avgDocuments = totalCollections > 0 ? totalDocuments / totalCollections : 0

  return {
    totalCollections,
    totalDocuments,
    activeCollection: activeCollection.value || '없음',
    avgDocuments
  }
})

onMounted(async () => {
  await loadCollections()
  await loadActiveCollection()
})

const loadCollections = async () => {
  loading.value = true
  try {
    const response = await collectionService.getCollections()
    if (response.success) {
      collections.value = response.collections || []
      // 각 컬렉션의 추가 정보를 가져오기 (문서 수는 getCollections에서 이미 정확한 값을 받음)
      for (const collection of collections.value) {
        try {
          // 기존 document_count 값을 보존
          const existingDocCount = collection.document_count || 0
          
          const info = await collectionService.getCollectionInfo(collection.name)
          if (info.success && info.collection) {
            collection.metadata = info.collection.metadata || {}
            
            // 생성일 정보 업데이트 (상세 정보에서 가져온 값 사용)
            if (info.collection.created_at) {
              collection.created_at = info.collection.created_at
            }
            
            // document_count는 getCollections()에서 받은 값이 더 정확하므로,
            // getCollectionInfo()가 더 큰 값을 반환할 때만 업데이트
            // (getCollectionInfo가 잘못된 테이블을 조회하여 0을 반환하는 문제 방지)
            const infoDocCount = info.collection.document_count || 0
            if (infoDocCount > existingDocCount) {
              collection.document_count = infoDocCount
            } else {
              // 기존 값 유지
              collection.document_count = existingDocCount
            }
          }
        } catch (error) {
          console.error(`Failed to load info for collection ${collection.name}:`, error)
        }
      }
    }
  } catch (error) {
    ElMessage.error('데이터셋 목록을 불러오는데 실패했습니다.')
  } finally {
    loading.value = false
  }
}

const loadActiveCollection = async () => {
  try {
    const response = await collectionService.getActiveCollection()
    if (response.success) {
      activeCollection.value = response.collection_name || ''
    }
  } catch (error) {
    console.error('Failed to load active collection:', error)
  }
}

const handleCreateCollection = async () => {
  if (!newCollection.value.name.trim()) {
    ElMessage.warning('데이터셋명을 입력하세요.')
    return
  }

  try {
    await collectionService.createCollection(
      newCollection.value.name,
      newCollection.value.description,
      newCollection.value.type
    )
    ElMessage.success('데이터셋이 생성되었습니다.')
    showCreateDialog.value = false
    newCollection.value = { name: '', description: '', type: 'personal' }
    await loadCollections()
  } catch (error: any) {
    ElMessage.error(error.message || '데이터셋 생성에 실패했습니다.')
  }
}

const handleSwitchCollection = async (collectionName: string) => {
  try {
    await collectionService.switchCollection(collectionName)
    activeCollection.value = collectionName
    ElMessage.success(`데이터셋 "${collectionName}"이(가) 선택되었습니다.`)
    await loadCollections()
  } catch (error: any) {
    ElMessage.error(error.message || '데이터셋 전환에 실패했습니다.')
  }
}

const handleViewInfo = async (collection: any) => {
  try {
    const response = await collectionService.getCollectionInfo(collection.name)
    if (response.success) {
      selectedCollection.value = response.collection || collection
      showInfoDialog.value = true
    } else {
      ElMessage.error('데이터셋 정보를 불러오는데 실패했습니다.')
    }
  } catch (error: any) {
    ElMessage.error('컬렉션 정보를 불러오는데 실패했습니다.')
  }
}

const handleDeleteCollection = async (collectionName: string) => {
  if (collectionName === 'langchain_documents' || collectionName === 'documents') {
    ElMessage.warning('기본 데이터셋은 삭제할 수 없습니다.')
    return
  }

  try {
    await ElMessageBox.confirm(
      `'${collectionName}' 데이터셋을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`,
      '확인',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )
    await collectionService.deleteCollection(collectionName)
    await loadCollections()
    if (activeCollection.value === collectionName) {
      activeCollection.value = ''
    }
    ElMessage.success('데이터셋이 삭제되었습니다.')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('데이터셋 삭제에 실패했습니다.')
    }
  }
}

const handleRefresh = async () => {
  await loadCollections()
  await loadActiveCollection()
  ElMessage.success('새로고침되었습니다.')
}

const formatDate = (date: string | null) => {
  if (!date) return '알 수 없음'
  try {
    return new Date(date).toLocaleString('ko-KR')
  } catch {
    return '알 수 없음'
  }
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
</style>
