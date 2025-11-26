<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
    <el-card class="w-full max-w-md shadow-xl">
      <template #header>
        <div class="text-center">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">회원가입</h1>
          <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">새 계정을 만드세요</p>
        </div>
      </template>

      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleRegister" label-position="top">
        <el-form-item label="사용자명" prop="username" class="form-item-custom">
          <el-input
            v-model="form.username"
            placeholder="사용자명을 입력하세요"
            size="large"
            :prefix-icon="User"
            clearable
            class="w-full"
          />
        </el-form-item>

        <el-form-item label="이메일" prop="email" class="form-item-custom">
          <el-input
            v-model="form.email"
            type="email"
            placeholder="이메일을 입력하세요"
            size="large"
            :prefix-icon="Message"
            clearable
            class="w-full"
          />
        </el-form-item>

        <el-form-item label="비밀번호" prop="password" class="form-item-custom">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="비밀번호를 입력하세요"
            size="large"
            :prefix-icon="Lock"
            show-password
            class="w-full"
          />
        </el-form-item>

        <el-form-item label="비밀번호 확인" prop="confirm_password" class="form-item-custom">
          <el-input
            v-model="form.confirm_password"
            type="password"
            placeholder="비밀번호를 다시 입력하세요"
            size="large"
            :prefix-icon="Lock"
            show-password
            class="w-full"
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="w-full"
            :loading="loading"
            @click="handleRegister"
          >
            회원가입
          </el-button>
        </el-form-item>
      </el-form>

      <div class="text-center mt-4">
        <el-link type="primary" @click="$router.push('/login')">
          이미 계정이 있으신가요? 로그인
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
import { User, Lock, Message } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirm_password: '',
})

const validatePassword = (rule: any, value: string, callback: Function) => {
  if (value !== form.password) {
    callback(new Error('비밀번호가 일치하지 않습니다'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '사용자명을 입력하세요', trigger: 'blur' },
    { min: 3, message: '사용자명은 최소 3자 이상이어야 합니다', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '이메일을 입력하세요', trigger: 'blur' },
    { type: 'email', message: '올바른 이메일 형식을 입력하세요', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '비밀번호를 입력하세요', trigger: 'blur' },
    { min: 6, message: '비밀번호는 최소 6자 이상이어야 합니다', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '비밀번호 확인을 입력하세요', trigger: 'blur' },
    { validator: validatePassword, trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      error.value = ''

      const result = await authStore.register(form)

      loading.value = false

      if (result.success) {
        router.push('/')
      } else {
        error.value = result.error || '회원가입에 실패했습니다.'
      }
    }
  })
}
</script>

<style scoped>
:deep(.el-card__body) {
  padding: 2rem;
}

:deep(.el-form-item) {
  margin-bottom: 1.5rem;
}

:deep(.el-form-item:last-of-type) {
  margin-bottom: 0;
}

:deep(.el-form-item__label) {
  padding-bottom: 0.5rem;
  font-weight: 500;
  color: #606266;
  line-height: 1.5;
}

:deep(.el-form-item__content) {
  width: 100%;
}

:deep(.el-input) {
  width: 100%;
}

:deep(.el-form-item__error) {
  padding-top: 0.25rem;
  font-size: 0.875rem;
}

.form-item-custom {
  margin-bottom: 1.5rem;
}
</style>

