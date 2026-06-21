<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToastStore } from '../stores/toast'
import { getRiskQuestions, submitRiskAssessment } from '../api/auth'
import AppLayout from '../components/layout/AppLayout.vue'
import Loading from '../components/common/Loading.vue'

const router = useRouter()
const toast = useToastStore()

const questions = ref([])
const answers = ref({})
const loading = ref(true)
const submitting = ref(false)

onMounted(async () => {
  try {
    questions.value = await getRiskQuestions()
  } catch (err) {
    toast.error('加载问卷失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
})

function selectOption(questionId, optionId, score) {
  answers.value[questionId] = { option_id: optionId, score }
}

async function handleSubmit() {
  const qs = questions.value
  if (Object.keys(answers.value).length < qs.length) {
    toast.warning(`请回答全部 ${qs.length} 道题目`)
    return
  }
  submitting.value = true
  try {
    const answerList = qs.map(q => answers.value[q.id])
    await submitRiskAssessment(answerList)
    toast.success('评估完成')
    router.push('/me/settings')
  } catch (err) {
    toast.error(err.message || '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppLayout>
    <header class="toolbar">
      <button class="back-btn" @click="router.back()">&larr; 返回设置</button>
      <h1>投资者风险评估</h1>
      <p>请根据您的实际情况回答以下问题</p>
    </header>

    <Loading v-if="loading" variant="skeleton" :rows="3" />

    <div v-else class="assessment-card">
      <div v-for="(q, idx) in questions" :key="q.id" class="question-block">
        <h3 class="question-title">{{ idx + 1 }}. {{ q.question }}</h3>
        <div class="options-group">
          <label
            v-for="opt in q.options"
            :key="opt.id"
            :class="['option-label', { 'option-label--active': answers[q.id]?.option_id === opt.id }]"
          >
            <input
              type="radio"
              :name="'q_' + q.id"
              :value="opt.id"
              class="option-radio"
              @change="selectOption(q.id, opt.id, opt.score)"
            />
            <span class="option-text">{{ opt.label }}</span>
          </label>
        </div>
      </div>

      <button class="submit-btn" :disabled="submitting || Object.keys(answers).length < questions.length" @click="handleSubmit">
        {{ submitting ? '提交中...' : '提交评估' }}
      </button>
    </div>
  </AppLayout>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 8px 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }
.back-btn { background: none; border: 0; color: var(--color-text-secondary); cursor: pointer; font: inherit; font-size: 14px; padding: 4px 0; }
.back-btn:hover { color: var(--color-primary); }
.assessment-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  max-width: 640px;
  padding: 24px;
}
.question-block { margin-bottom: 28px; }
.question-title { font-size: 16px; margin: 0 0 12px; }
.options-group { display: grid; gap: 8px; }
.option-label {
  align-items: center;
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  gap: 10px;
  padding: 10px 14px;
  transition: border-color 0.15s, background 0.15s;
}
.option-label:hover { border-color: var(--color-primary); }
.option-label--active { background: var(--color-primary-light); border-color: var(--color-primary); }
.option-radio { accent-color: var(--color-primary); }
.option-text { font-size: 14px; }
.submit-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 15px;
  margin-top: 12px;
  padding: 12px 24px;
  width: 100%;
}
.submit-btn:hover { background: var(--color-primary-hover); }
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
