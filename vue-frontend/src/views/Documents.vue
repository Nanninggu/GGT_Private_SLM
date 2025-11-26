<template>
  <div class="h-full p-6">
    <div class="max-w-6xl mx-auto">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-2xl font-bold text-foreground">문서 관리</h2>
          <p class="text-sm text-muted-foreground mt-1">문서를 업로드하고 벡터 데이터셋에 추가하세요</p>
        </div>
        <div class="flex items-center gap-4">
          <el-tooltip
            content="벡터화를 활성화하면 RAG 검색에 활용할 수 있습니다. 비활성화하면 문서만 저장됩니다."
            placement="bottom"
            effect="dark"
          >
            <div class="flex items-center gap-2">
              <el-switch
                v-model="createEmbedding"
                active-text="벡터화"
                inactive-text="저장만"
                :active-value="true"
                :inactive-value="false"
              />
            </div>
          </el-tooltip>
          <el-tooltip
            content="문서를 업로드하여 RAG 검색에 활용할 수 있습니다. 지원 형식: TXT, PDF, DOCX, MD, JSON, CSV"
            placement="bottom"
            effect="dark"
          >
            <el-upload
              :action="uploadUrl"
              :headers="uploadHeaders"
              :data="uploadData"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :on-progress="handleUploadProgress"
              :before-upload="beforeUpload"
              :show-file-list="false"
              multiple
            >
              <el-button 
                type="primary" 
                :icon="isUploading ? Loading : Upload"
                :loading="isUploading"
              >
                {{ isUploading ? `업로드 중... (${uploadingCount}개)` : '문서 업로드' }}
              </el-button>
            </el-upload>
          </el-tooltip>
        </div>
      </div>

      <!-- Collection Selector and Filters -->
      <el-card class="mb-6 bg-card border-border">
        <div class="flex items-center gap-4 flex-wrap">
          <div class="flex items-center gap-2">
            <span class="text-sm text-muted-foreground">업로드할 데이터셋:</span>
            <el-select
              v-model="selectedCollection"
              placeholder="데이터셋 선택"
              style="width: 300px"
              @change="handleCollectionChange"
            >
              <el-option
                v-for="collection in collections"
                :key="collection.name"
                :label="`${collection.name} (${collection.document_count ?? 0}개 문서)`"
                :value="collection.name"
              />
            </el-select>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-muted-foreground">정렬:</span>
            <el-select
              v-model="orderBy"
              placeholder="정렬 기준"
              style="width: 150px"
              @change="loadDocuments"
            >
              <el-option label="업로드일" value="created_at" />
              <el-option label="수정일" value="updated_at" />
            </el-select>
            <el-select
              v-model="orderDirection"
              placeholder="정렬 방향"
              style="width: 120px"
              @change="loadDocuments"
            >
              <el-option label="최신순" value="desc" />
              <el-option label="오래된순" value="asc" />
            </el-select>
          </div>
          <el-button :icon="Refresh" @click="loadCollections">새로고침</el-button>
        </div>
      </el-card>

      <el-table
        :data="displayDocuments"
        v-loading="loading"
        class="bg-card"
        style="width: 100%"
        empty-text="데이터 없음"
      >
        <el-table-column prop="id" label="문서 ID" width="200">
          <template #default="{ row }">
            <span v-if="row.isUploading">-</span>
            <span v-else>{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="metadata.filename" label="파일명">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-icon v-if="row.isUploading" class="upload-icon">
                <Document />
              </el-icon>
              <span>{{ row.metadata?.filename || row.filename }}</span>
              <el-tag v-if="row.isUploading" type="warning" size="small" effect="dark">
                <span class="pulse-dot"></span>
                업로드 중
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="metadata.file_type" label="타입" width="100">
          <template #default="{ row }">
            <span v-if="row.isUploading">{{ getFileType(row.filename) }}</span>
            <span v-else>{{ row.metadata?.file_type || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="벡터화" width="120">
          <template #default="{ row }">
            <div v-if="row.isUploading" class="progress-container">
              <el-progress
                :percentage="row.progress"
                :status="row.status"
                :stroke-width="10"
                text-inside
                striped
                :striped-flow="row.status === 'uploading' || row.status === 'success'"
              />
              <div class="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <el-icon class="spinning" v-if="row.status === 'uploading' || row.status === 'success'">
                  <Loading />
                </el-icon>
                {{ row.status === 'success' ? '벡터화 중...' : '업로드 중...' }}
              </div>
            </div>
            <el-tooltip
              v-else
              :content="row.embedding ? '벡터화됨 - RAG 검색 가능' : '벡터화 안 됨 - RAG 검색 불가'"
              placement="top"
              effect="dark"
            >
              <el-tag :type="row.embedding ? 'success' : 'info'" size="small">
                {{ row.embedding ? '✓' : '✗' }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="업로드일" width="180">
          <template #default="{ row }">
            <span v-if="row.isUploading">-</span>
            <span v-else>{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="수정일" width="180">
          <template #default="{ row }">
            <span v-if="row.isUploading">-</span>
            <span v-else-if="row.updated_at">{{ formatDate(row.updated_at) }}</span>
            <span v-else class="text-muted-foreground">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_id" label="업로드자" width="120">
          <template #default="{ row }">
            <span v-if="row.isUploading">-</span>
            <span v-else-if="row.user_id" class="text-sm">{{ row.user_id.substring(0, 8) }}...</span>
            <span v-else class="text-muted-foreground">-</span>
          </template>
        </el-table-column>
        <el-table-column label="작업" width="150">
          <template #default="{ row }">
            <el-button
              v-if="!row.isUploading"
              size="small"
              type="danger"
              :icon="Delete"
              @click="handleDeleteDocument(row.id)"
            >
              삭제
            </el-button>
            <span v-else class="text-muted-foreground text-sm">처리 중...</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="mt-4 flex flex-col items-center gap-4" v-if="totalDocuments > 0">
        <div class="text-sm text-muted-foreground">
          전체 {{ totalDocuments }}개 문서 중 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalDocuments) }}개 표시
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalDocuments"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { documentService } from '@/services/document.service'
import { collectionService } from '@/services/collection.service'
import { Upload, Delete, Refresh, Loading, Document } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const documents = ref<any[]>([])
const uploadingFiles = ref<Map<string, any>>(new Map())
const collections = ref<any[]>([])
const loading = ref(false)
const selectedCollection = ref('documents')
const createEmbedding = ref(true)
const totalDocuments = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const orderBy = ref('created_at')
const orderDirection = ref('desc')

// 업로드 상태 계산
const isUploading = computed(() => uploadingFiles.value.size > 0)
const uploadingCount = computed(() => uploadingFiles.value.size)

const uploadUrl = computed(() => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9502'
  // 데이터셋 관리에서 만든 컬렉션은 모두 LangChain 컬렉션
  // 기본 'documents' 컬렉션이 아닌 경우 LangChain 엔드포인트 사용
  if (selectedCollection.value && selectedCollection.value !== 'documents') {
    return `${baseUrl}/api/langchain/upload`
  }
  return `${baseUrl}/api/upload`
})

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('auth_token')
  return {
    Authorization: `Bearer ${token}`,
  }
})

const uploadData = computed(() => {
  // 항상 collection_name을 전달 (undefined 방지)
  // selectedCollection이 없으면 기본값 사용
  const collectionName = selectedCollection.value || (uploadUrl.value.includes('/langchain/') ? 'langchain_documents' : 'documents')
  
  return {
    collection_name: collectionName,
  create_embedding: createEmbedding.value.toString(),
  }
})

// 업로드 중인 파일과 기존 문서를 합친 목록
// 업로드 완료된 파일은 실제 문서 목록에 포함되므로 중복 제거
const displayDocuments = computed(() => {
  const uploadList = Array.from(uploadingFiles.value.values())
  const documentFilenames = new Set(
    documents.value.map(doc => {
      // 다양한 필드명으로 파일명 찾기
      return doc.metadata?.filename || doc.filename || doc.id
    }).filter(Boolean)
  )
  
  // 실제 문서 목록에 없는 업로드 중인 파일만 표시 (중복 방지)
  const uniqueUploads = uploadList.filter(upload => 
    !documentFilenames.has(upload.filename)
  )
  
  // 문서 목록을 업로드일 기준으로 정렬 (최신순)
  const sortedDocuments = [...documents.value].sort((a, b) => {
    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0
    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0
    return dateB - dateA // 최신순
  })
  
  return [...uniqueUploads, ...sortedDocuments]
})

const getFileType = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  return ext || 'unknown'
}

onMounted(async () => {
  await loadDocuments()
  await loadCollections()
  await loadActiveCollection()
})

const loadCollections = async () => {
  try {
    const response = await collectionService.getCollections()
    if (response.success) {
      collections.value = response.collections || []
      // getCollections()가 이미 document_count를 반환하므로,
      // 기존 값이 있으면 유지하고, 없거나 0인 경우에만 추가 조회
      const infoPromises = collections.value.map(async (collection) => {
        // 이미 document_count가 있고 0이 아니면 유지 (추가 호출 불필요)
        const existingCount = collection.document_count
        if (existingCount !== undefined && existingCount !== null && existingCount > 0) {
          return // 이미 정확한 값이 있으므로 추가 호출 불필요
        }
        
        // 값이 없거나 0인 경우에만 상세 정보 조회
        try {
          const info = await collectionService.getCollectionInfo(collection.name)
          if (info.success && info.collection) {
            // 기존 값이 없거나 0인 경우에만 업데이트 (절대 덮어쓰지 않음)
            if (existingCount === undefined || existingCount === null || existingCount === 0) {
              collection.document_count = info.collection.document_count ?? 0
            }
          }
        } catch (error: any) {
          // 404 오류는 데이터셋이 존재하지 않거나 문서가 없는 경우이므로 무시
          if (error.response?.status !== 404) {
            console.error(`Failed to load info for collection ${collection.name}:`, error)
          }
          // 에러 발생 시 기존 document_count 값 유지 (절대 덮어쓰지 않음)
          if (existingCount === undefined || existingCount === null) {
            collection.document_count = 0
          }
        }
      })
      // 모든 정보를 병렬로 가져오기
      await Promise.all(infoPromises)
    }
  } catch (error) {
    console.error('Failed to load collections:', error)
  }
}

const loadActiveCollection = async () => {
  try {
    const response = await collectionService.getActiveCollection()
    if (response.success && response.collection_name) {
      selectedCollection.value = response.collection_name
    }
  } catch (error) {
    console.error('Failed to load active collection:', error)
  }
}

const handleCollectionChange = async () => {
  // 데이터셋 변경 시 문서 목록 새로고침
  await loadDocuments()
  ElMessage.info(`데이터셋 "${selectedCollection.value}"의 문서 목록을 불러왔습니다.`)
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await documentService.getDocuments({
      collection_name: selectedCollection.value || undefined,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value,
      order_by: orderBy.value,
      order_direction: orderDirection.value
    })
    if (response.success) {
      documents.value = response.documents || []
      totalDocuments.value = response.total || 0
    }
  } catch (error) {
    ElMessage.error('문서 목록을 불러오는데 실패했습니다.')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadDocuments()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadDocuments()
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('ko-KR')
}

const beforeUpload = (file: File) => {
  const isValidType = ['.txt', '.pdf', '.docx', '.md', '.json', '.csv'].some((ext) =>
    file.name.endsWith(ext)
  )
  if (!isValidType) {
    ElMessage.error('지원하지 않는 파일 형식입니다.')
    return false
  }
  
  // 업로드 시작 시 파일을 목록에 추가
  const fileId = `${Date.now()}_${file.name}`
  uploadingFiles.value.set(fileId, {
    id: fileId,
    filename: file.name,
    isUploading: true,
    progress: 0,
    status: 'uploading' as const,
    metadata: {
      filename: file.name,
      file_type: getFileType(file.name)
    }
  })
  
  return true
}

const handleUploadProgress = (event: any, file: File, fileList: File[]) => {
  // 업로드 진행률 업데이트
  const fileId = Array.from(uploadingFiles.value.keys()).find(key => 
    uploadingFiles.value.get(key)?.filename === file.name
  )
  
  if (fileId) {
    const uploadItem = uploadingFiles.value.get(fileId)
    if (uploadItem) {
      uploadItem.progress = Math.round(event.percent || 0)
      uploadItem.status = uploadItem.progress < 100 ? 'uploading' : 'success'
      uploadingFiles.value.set(fileId, uploadItem)
    }
  }
}

const handleUploadSuccess = async (response: any, file: File) => {
  // 업로드 완료된 파일 처리
  const fileId = Array.from(uploadingFiles.value.keys()).find(key =>
    uploadingFiles.value.get(key)?.filename === file.name
  )

  if (fileId) {
    // 벡터화 중 상태로 변경
    const uploadItem = uploadingFiles.value.get(fileId)
    if (uploadItem) {
      uploadItem.progress = 100
      uploadItem.status = 'success'
      uploadItem.statusText = createEmbedding.value ? '벡터화 완료' : '저장 완료'
      uploadingFiles.value.set(fileId, uploadItem)
    }
  }

  // 실제 문서 목록 새로고침 (업로드된 파일이 포함되도록)
  // DB 트랜잭션이 완료될 시간을 주기 위해 약간의 딜레이 추가
  setTimeout(async () => {
    await loadDocuments()
  }, 1000) // 1초 딜레이

  // 컬렉션 정보(문서 수) 새로고침
  setTimeout(async () => {
    await loadCollections()
  }, 1500) // 1.5초 딜레이
  
  // 업로드된 문서가 리스트에 있는지 확인
  let matchedDoc = null
  if (response.document_id) {
    // document_id로 매칭 시도
    matchedDoc = documents.value.find(doc => doc.id === response.document_id)
  }
  
  if (!matchedDoc) {
    // 파일명으로 매칭 시도
    matchedDoc = documents.value.find(doc => 
      doc.metadata?.filename === file.name || doc.filename === file.name
    )
  }
  
  // 업로드 중인 항목 제거 (실제 문서로 전환되었으므로)
  if (fileId) {
    setTimeout(() => {
      uploadingFiles.value.delete(fileId)
    }, 1000) // 1초 후 제거하여 완료 상태를 사용자가 볼 수 있도록
  }
  
  // 사용자에게 상세한 결과 안내
  if (response.success) {
    const collectionName = selectedCollection.value || 'documents'
    const embeddingStatus = response.embedding_created 
      ? '벡터화 완료 - RAG 검색 가능' 
      : '벡터화 없음 - RAG 검색 불가'
    
    if (matchedDoc) {
      ElMessage.success({
        message: `문서 "${file.name}" 업로드 완료!\n데이터셋: ${collectionName}\n상태: ${embeddingStatus}`,
        duration: 5000,
        showClose: true
      })
    } else {
      ElMessage.success({
        message: `문서 "${file.name}" 업로드 완료!\n데이터셋: ${collectionName}\n상태: ${embeddingStatus}\n(문서 목록 새로고침 중...)`,
        duration: 5000,
        showClose: true
      })
      // 문서가 아직 목록에 없으면 다시 새로고침
      setTimeout(async () => {
        await loadDocuments()
      }, 2000)
    }
  } else {
    ElMessage.error(`문서 "${file.name}" 업로드에 실패했습니다.`)
        }
  
  // 경고 메시지 처리
  if (response.warning) {
    ElMessage.warning({
      message: response.warning,
      duration: 5000,
      showClose: true
    })
  } else if (response.embedding_created === false && createEmbedding.value) {
    ElMessage.warning({
      message: `문서 "${file.name}"는 저장되었지만 벡터화에 실패했습니다.\nRAG 검색에는 사용할 수 없습니다.`,
      duration: 5000,
      showClose: true
    })
  }
}

const handleUploadError = (error: any, file: File) => {
  // 업로드 실패한 파일을 목록에서 제거
  const fileId = Array.from(uploadingFiles.value.keys()).find(key => 
    uploadingFiles.value.get(key)?.filename === file.name
  )
  
  if (fileId) {
    uploadingFiles.value.delete(fileId)
  }
  
  ElMessage.error('문서 업로드에 실패했습니다.')
}

const handleDeleteDocument = async (docId: string) => {
  try {
    await ElMessageBox.confirm('이 문서를 삭제하시겠습니까?', '확인', {
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      type: 'warning',
    })
    await documentService.deleteDocument(docId)
    await loadDocuments()
    ElMessage.success('문서가 삭제되었습니다.')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('문서 삭제에 실패했습니다.')
    }
  }
}
</script>

<style scoped>
/* 회전 애니메이션 */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.upload-icon {
  transition: transform 0.2s ease;
}

.upload-icon.spinning {
  animation: spin 1s linear infinite;
}

/* 펄스 애니메이션 */
.pulse-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
  animation: pulse 1.5s ease-in-out infinite;
  margin-right: 4px;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

/* 진행률 바 컨테이너 스타일 */
.progress-container {
  width: 100%;
  max-width: 100%;
  overflow: hidden;
}

/* 진행률 바 내부 텍스트가 칸을 벗어나지 않도록 스타일 조정 */
:deep(.el-progress-bar__innerText) {
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  padding: 0 2px;
  box-sizing: border-box;
  display: inline-block;
  line-height: 1;
}

/* 진행률 바 컨테이너 너비 제한 */
:deep(.el-progress) {
  width: 100%;
  max-width: 100%;
  overflow: hidden;
}

:deep(.el-progress-bar__outer) {
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  height: 10px;
}

:deep(.el-progress-bar__inner) {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 10px;
  min-height: 10px;
}

/* 진행률 바 스트라이프 애니메이션 */
:deep(.el-progress-bar__inner.is-striped) {
  background-image: linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.15) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.15) 50%,
    rgba(255, 255, 255, 0.15) 75%,
    transparent 75%,
    transparent
  );
  background-size: 1em 1em;
}

:deep(.el-progress-bar__inner.is-striped.is-striped-flow) {
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 1em 0;
  }
}
</style>

