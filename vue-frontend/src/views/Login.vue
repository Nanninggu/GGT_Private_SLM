<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
    <el-card class="w-full max-w-md shadow-xl">
      <template #header>
        <div class="text-center">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">로그인</h1>
          <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">계정에 로그인하세요</p>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item label="사용자명" prop="username">
          <el-input
            v-model="form.username"
            placeholder="사용자명을 입력하세요"
            size="large"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item label="비밀번호" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="비밀번호를 입력하세요"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="w-full"
            :loading="loading"
            @click="handleLogin"
          >
            로그인
          </el-button>
        </el-form-item>
      </el-form>

      <div class="text-center mt-4">
        <el-link type="primary" @click="$router.push('/register')">
          계정이 없으신가요? 회원가입
        </el-link>
      </div>

      <el-alert
        v-if="error"
        :title="error"
        type="error"
        :closable="false"
        class="mt-4"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { User, Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '사용자명을 입력하세요', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '비밀번호를 입력하세요', trigger: 'blur' },
    { min: 6, message: '비밀번호는 최소 6자 이상이어야 합니다', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      error.value = ''

      const result = await authStore.login({
        username: form.username,
        password: form.password,
      })

      loading.value = false

      if (result.success) {
        router.push('/')
      } else {
        error.value = result.error || '로그인에 실패했습니다.'
      }
    }
  })
}
</script>

<style scoped>
:deep(.el-card__body) {
  padding: 2rem;
}
</style>

