<template>
  <div class="h-full p-6 bg-background">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-foreground">개발자 도구</h2>
        <p class="text-sm text-muted-foreground mt-1">시스템 설정 및 API 문서를 확인하세요</p>
      </div>

      <!-- Tabs -->
      <el-tabs v-model="activeTab" class="settings-tabs" @tab-change="handleTabChange">
        <el-tab-pane label="API 문서" name="swagger">
          <div class="mt-4">
            <el-card class="bg-card border-border" shadow="never">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <el-icon><Document /></el-icon>
                    <span class="font-semibold">Swagger UI</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <el-button
                      size="small"
                      :icon="Refresh"
                      @click="refreshSwagger"
                    >
                      새로고침
                    </el-button>
                    <el-button
                      size="small"
                      type="primary"
                      :icon="Link"
                      @click="openSwaggerInNewTab"
                    >
                      새 창에서 열기
                    </el-button>
                  </div>
                </div>
              </template>
              <div class="swagger-container">
                <iframe
                  ref="swaggerFrame"
                  :src="swaggerUrl"
                  class="swagger-iframe"
                  frameborder="0"
                  @load="onSwaggerLoad"
                ></iframe>
                <div v-if="swaggerLoading" class="swagger-loading">
                  <el-icon class="animate-spin"><Loading /></el-icon>
                  <span class="ml-2">Swagger UI 로딩 중...</span>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="ReDoc" name="redoc">
          <div class="mt-4">
            <el-card class="bg-card border-border" shadow="never">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <el-icon><Document /></el-icon>
                    <span class="font-semibold">ReDoc</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <el-button
                      size="small"
                      :icon="Refresh"
                      @click="refreshReDoc"
                    >
                      새로고침
                    </el-button>
                    <el-button
                      size="small"
                      type="primary"
                      :icon="Link"
                      @click="openReDocInNewTab"
                    >
                      새 창에서 열기
                    </el-button>
                  </div>
                </div>
              </template>
              <div class="swagger-container">
                <iframe
                  ref="redocFrame"
                  :src="redocUrl"
                  class="swagger-iframe"
                  frameborder="0"
                  @load="onReDocLoad"
                ></iframe>
                <div v-if="redocLoading" class="swagger-loading">
                  <el-icon class="animate-spin"><Loading /></el-icon>
                  <span class="ml-2">ReDoc 로딩 중...</span>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="OpenAPI JSON" name="openapi">
          <div class="mt-4">
            <el-card class="bg-card border-border" shadow="never">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <el-icon><Document /></el-icon>
                    <span class="font-semibold">OpenAPI JSON 스키마</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <el-button
                      size="small"
                      :icon="Refresh"
                      @click="loadOpenApiJson"
                    >
                      새로고침
                    </el-button>
                    <el-button
                      size="small"
                      :icon="Download"
                      @click="downloadOpenApiJson"
                    >
                      다운로드
                    </el-button>
                    <el-button
                      size="small"
                      type="primary"
                      :icon="Link"
                      @click="openOpenApiInNewTab"
                    >
                      새 창에서 열기
                    </el-button>
                  </div>
                </div>
              </template>
              <div class="openapi-json-container">
                <div v-if="openApiLoading" class="text-center py-12">
                  <el-icon class="animate-spin text-4xl text-muted-foreground"><Loading /></el-icon>
                  <p class="mt-4 text-muted-foreground">OpenAPI JSON 로딩 중...</p>
                </div>
                <div v-else-if="openApiError" class="text-center py-12">
                  <el-alert
                    :title="openApiError"
                    type="error"
                    :closable="false"
                    class="max-w-md mx-auto"
                  />
                </div>
                <pre v-else class="openapi-json-content">{{ openApiJson }}</pre>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <el-tab-pane label="API 정보" name="info">
          <div class="mt-4">
            <el-card class="bg-card border-border" shadow="never">
              <template #header>
                <div class="flex items-center gap-2">
                  <el-icon><InfoFilled /></el-icon>
                  <span class="font-semibold">API 정보</span>
                </div>
              </template>
              <div v-if="apiInfoLoading" class="text-center py-12">
                <el-icon class="animate-spin text-4xl text-muted-foreground"><Loading /></el-icon>
                <p class="mt-4 text-muted-foreground">API 정보 로딩 중...</p>
              </div>
              <div v-else-if="apiInfo" class="space-y-4">
                <div>
                  <div class="text-sm text-muted-foreground mb-1">애플리케이션 이름</div>
                  <div class="text-lg font-semibold text-foreground">{{ apiInfo.app_name }}</div>
                </div>
                <div>
                  <div class="text-sm text-muted-foreground mb-1">버전</div>
                  <div class="text-lg font-semibold text-foreground">{{ apiInfo.version }}</div>
                </div>
                <div>
                  <div class="text-sm text-muted-foreground mb-1">설명</div>
                  <div class="text-foreground">{{ apiInfo.description }}</div>
                </div>
                <div>
                  <div class="text-sm text-muted-foreground mb-2">주요 기능</div>
                  <div class="space-y-2">
                    <el-tag
                      v-for="(feature, idx) in apiInfo.features"
                      :key="idx"
                      class="mr-2 mb-2"
                      type="info"
                    >
                      {{ feature }}
                    </el-tag>
                  </div>
                </div>
                <div class="pt-4 border-t border-border">
                  <div class="text-sm text-muted-foreground mb-2">API 엔드포인트</div>
                  <div class="space-y-2 text-sm">
                    <div class="flex items-center gap-2">
                      <el-tag size="small" type="success">GET</el-tag>
                      <code class="text-xs bg-muted px-2 py-1 rounded">{{ baseUrl }}/docs</code>
                      <span class="text-muted-foreground">Swagger UI</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <el-tag size="small" type="success">GET</el-tag>
                      <code class="text-xs bg-muted px-2 py-1 rounded">{{ baseUrl }}/redoc</code>
                      <span class="text-muted-foreground">ReDoc</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <el-tag size="small" type="success">GET</el-tag>
                      <code class="text-xs bg-muted px-2 py-1 rounded">{{ baseUrl }}/openapi.json</code>
                      <span class="text-muted-foreground">OpenAPI JSON</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Document, Refresh, Link, Download, InfoFilled, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiService } from '@/services/api'

const activeTab = ref('swagger')
const swaggerLoading = ref(true)
const redocLoading = ref(true)
const openApiLoading = ref(false)
const openApiError = ref('')
const openApiJson = ref('')
const apiInfoLoading = ref(false)
const apiInfo = ref<any>(null)
const swaggerFrame = ref<HTMLIFrameElement>()
const redocFrame = ref<HTMLIFrameElement>()

const baseUrl = computed(() => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:9502'
})

const swaggerUrl = computed(() => `${baseUrl.value}/docs`)
const redocUrl = computed(() => `${baseUrl.value}/redoc`)
const openApiUrl = computed(() => `${baseUrl.value}/openapi.json`)

onMounted(async () => {
  await loadApiInfo()
})

const onSwaggerLoad = () => {
  swaggerLoading.value = false
}

const onReDocLoad = () => {
  redocLoading.value = false
}

const refreshSwagger = () => {
  if (swaggerFrame.value) {
    swaggerLoading.value = true
    swaggerFrame.value.src = swaggerFrame.value.src
  }
}

const refreshReDoc = () => {
  if (redocFrame.value) {
    redocLoading.value = true
    redocFrame.value.src = redocFrame.value.src
  }
}

const openSwaggerInNewTab = () => {
  window.open(swaggerUrl.value, '_blank')
}

const openReDocInNewTab = () => {
  window.open(redocUrl.value, '_blank')
}

const openOpenApiInNewTab = () => {
  window.open(openApiUrl.value, '_blank')
}

const loadOpenApiJson = async () => {
  openApiLoading.value = true
  openApiError.value = ''
  try {
    const response = await fetch(openApiUrl.value)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    const data = await response.json()
    openApiJson.value = JSON.stringify(data, null, 2)
  } catch (error: any) {
    openApiError.value = error.message || 'OpenAPI JSON을 불러오는데 실패했습니다.'
    ElMessage.error('OpenAPI JSON 로딩 실패')
  } finally {
    openApiLoading.value = false
  }
}

const downloadOpenApiJson = async () => {
  try {
    if (!openApiJson.value) {
      await loadOpenApiJson()
    }
    const blob = new Blob([openApiJson.value], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'openapi.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('OpenAPI JSON이 다운로드되었습니다.')
  } catch (error) {
    ElMessage.error('다운로드에 실패했습니다.')
  }
}

const loadApiInfo = async () => {
  apiInfoLoading.value = true
  try {
    const response = await apiService.get('/info')
    apiInfo.value = response
  } catch (error) {
    console.error('Failed to load API info:', error)
  } finally {
    apiInfoLoading.value = false
  }
}

// 탭 변경 시 OpenAPI JSON 로드
const handleTabChange = (tabName: string) => {
  if (tabName === 'openapi' && !openApiJson.value && !openApiLoading.value) {
    loadOpenApiJson()
  }
}
</script>

<style scoped>
.settings-tabs {
  background: transparent;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
  background: hsl(var(--card));
  padding: 0 1rem;
  border-radius: 0.5rem 0.5rem 0 0;
  border: 1px solid hsl(var(--border));
  border-bottom: none;
}

:deep(.el-tabs__content) {
  background: transparent;
}

:deep(.el-tab-pane) {
  background: transparent;
}

.swagger-container {
  position: relative;
  width: 100%;
  height: calc(100vh - 300px);
  min-height: 600px;
  border: 1px solid hsl(var(--border));
  border-radius: 0.5rem;
  overflow: hidden;
  background: hsl(var(--card));
}

.swagger-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

.swagger-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  color: hsl(var(--muted-foreground));
  font-size: 0.875rem;
}

.openapi-json-container {
  max-height: calc(100vh - 300px);
  min-height: 400px;
  overflow: auto;
  border: 1px solid hsl(var(--border));
  border-radius: 0.5rem;
  background: hsl(var(--muted));
}

.openapi-json-content {
  margin: 0;
  padding: 1.5rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
  color: hsl(var(--foreground));
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.openapi-json-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.openapi-json-container::-webkit-scrollbar-track {
  background: hsl(var(--muted));
  border-radius: 4px;
}

.openapi-json-container::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 4px;
}

.openapi-json-container::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.5);
}
</style>

