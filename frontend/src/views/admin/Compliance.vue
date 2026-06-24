<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../../stores/toast'
import { fetchComplianceRules, addComplianceRule, deleteComplianceRule, checkCompliance } from '../../api/admin'
import Loading from '../../components/common/Loading.vue'

const toast = useToastStore()

// ── 规则管理 ──
const rules = ref([])
const loading = ref(true)
const showForm = ref(false)
const form = ref({ name: '', category: 'stock_recommendation', pattern: '', severity: 'review', description: '' })
const submitting = ref(false)

// ── 合规检查测试工具 ──
const testText = ref('')
const testResult = ref(null)
const testing = ref(false)

onMounted(loadRules)

async function loadRules() {
  loading.value = true
  try {
    rules.value = await fetchComplianceRules() || []
  } catch (err) {
    toast.error('加载合规规则失败: ' + err.message)
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!form.value.name.trim() || !form.value.pattern.trim()) return
  submitting.value = true
  try {
    await addComplianceRule({ ...form.value })
    toast.success('合规规则已添加')
    showForm.value = false
    form.value = { name: '', category: 'stock_recommendation', pattern: '', severity: 'review', description: '' }
    await loadRules()
  } catch (err) {
    toast.error(err.message || '添加失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteComplianceRule(id)
    toast.success('已删除')
    rules.value = rules.value.filter(r => r.id !== id)
  } catch (err) {
    toast.error(err.message || '删除失败')
  }
}

async function handleTestCheck() {
  if (!testText.value.trim()) return
  testing.value = true
  testResult.value = null
  try {
    testResult.value = await checkCompliance({ text: testText.value })
  } catch (err) {
    toast.error('检查失败: ' + err.message)
  } finally {
    testing.value = false
  }
}

const categoryLabel = (cat) => ({ stock_recommendation: '荐股检测', market_manipulation: '操纵市场' }[cat] || cat)
const severityLabel = (sev) => ({ block: '屏蔽', review: '审核', warn: '警告' }[sev] || sev)
</script>

<template>
    <header class="toolbar"><h1>管理后台 / 合规检查</h1></header>

    <div class="admin-nav">
      <router-link to="/admin" class="admin-nav__item">总览</router-link>
      <router-link to="/admin/review" class="admin-nav__item">审核队列</router-link>
      <router-link to="/admin/users" class="admin-nav__item">用户管理</router-link>
      <router-link to="/admin/certifications" class="admin-nav__item">认证审核</router-link>
      <router-link to="/admin/sensitive-words" class="admin-nav__item">敏感词</router-link>
      <router-link to="/admin/compliance" class="admin-nav__item admin-nav__item--active">合规检查</router-link>
      <router-link to="/admin/logs" class="admin-nav__item">操作日志</router-link>
      <router-link to="/admin/hot-topics" class="admin-nav__item">热门话题分析</router-link>
      <router-link to="/admin/engagement" class="admin-nav__item">用户参与度</router-link>
      <router-link to="/admin/categories" class="admin-nav__item">板块管理</router-link>
    </div>

    <!-- 添加规则按钮 -->
    <div class="section-actions">
      <button class="add-btn" @click="showForm = !showForm">
        {{ showForm ? '取消' : '+ 添加规则' }}
      </button>
    </div>

    <!-- 添加规则表单 -->
    <div v-if="showForm" class="add-form">
      <div class="form-row">
        <input v-model="form.name" class="form-input" placeholder="规则名称" maxlength="100" />
        <select v-model="form.category" class="form-select">
          <option value="stock_recommendation">荐股检测</option>
          <option value="market_manipulation">操纵市场</option>
        </select>
        <select v-model="form.severity" class="form-select">
          <option value="warn">警告</option>
          <option value="review">审核</option>
          <option value="block">屏蔽</option>
        </select>
      </div>
      <input v-model="form.pattern" class="form-input form-input--mono" placeholder="正则表达式模式，如：推荐买入|建议买入|强烈推荐" maxlength="500" />
      <input v-model="form.description" class="form-input" placeholder="规则说明（可选）" maxlength="255" />
      <button class="add-btn" :disabled="submitting || !form.name.trim() || !form.pattern.trim()" @click="handleAdd">
        {{ submitting ? '添加中...' : '确认添加' }}
      </button>
    </div>

    <Loading v-if="loading" variant="skeleton" :rows="2" />

    <div v-else-if="rules.length === 0" class="empty-state"><p>暂无合规规则，点击上方按钮添加</p></div>

    <!-- 规则列表 -->
    <table v-else class="rule-table">
      <thead>
        <tr>
          <th>规则名称</th>
          <th>类别</th>
          <th>正则模式</th>
          <th>严重级别</th>
          <th>说明</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rule in rules" :key="rule.id">
          <td class="col-name">{{ rule.name }}</td>
          <td><span :class="['cat-badge', rule.category === 'market_manipulation' ? 'cat-badge--manipulation' : 'cat-badge--recommendation']">{{ categoryLabel(rule.category) }}</span></td>
          <td><code class="pattern-code">{{ rule.pattern }}</code></td>
          <td><span :class="['level-badge', 'level-badge--' + rule.severity]">{{ severityLabel(rule.severity) }}</span></td>
          <td class="col-desc">{{ rule.description || '-' }}</td>
          <td><button class="del-btn" @click="handleDelete(rule.id)">删除</button></td>
        </tr>
      </tbody>
    </table>

    <!-- 合规检查测试工具 -->
    <section class="test-section">
      <h2>合规检查测试工具</h2>
      <p class="test-hint">粘贴内容文本，查看合规规则的匹配结果。</p>
      <textarea v-model="testText" class="test-textarea" rows="5" placeholder="在此粘贴需要检查的文本内容..." maxlength="10000"></textarea>
      <button class="add-btn" :disabled="testing || !testText.trim()" @click="handleTestCheck">
        {{ testing ? '检查中...' : '开始检查' }}
      </button>

      <div v-if="testResult" class="test-result">
        <div class="result-summary">
          <span class="result-label">检查结果：</span>
          <span v-if="!testResult.level" class="result-ok">✓ 未发现违规</span>
          <span v-else-if="testResult.should_block" class="result-block">✕ 违规（屏蔽）</span>
          <span v-else-if="testResult.should_review" class="result-review">! 违规（需审核）</span>
          <span v-else class="result-warn">⚠ 违规（警告）</span>
          <span v-if="testResult.categories && testResult.categories.length" class="result-cats">
            检测类别：{{ testResult.categories.map(categoryLabel).join('、') }}
          </span>
        </div>
        <div v-if="testResult.matches && testResult.matches.length" class="result-matches">
          <h4>匹配详情（{{ testResult.matches.length }} 条）：</h4>
          <div v-for="(match, i) in testResult.matches" :key="i" class="match-item">
            <span class="match-rule">{{ match.rule_name }}</span>
            <span :class="['level-badge', 'level-badge--' + match.severity]" style="margin-left:6px">{{ severityLabel(match.severity) }}</span>
            <span class="match-text">匹配："<strong>{{ match.matched_text }}</strong>"</span>
            <span v-if="match.description" class="match-desc">{{ match.description }}</span>
          </div>
        </div>
      </div>
    </section>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 24px; margin: 0; }

.admin-nav { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; display: flex; gap: 0; margin-bottom: 24px; overflow: hidden; flex-wrap: wrap; }
.admin-nav__item { border-bottom: 2px solid transparent; color: var(--color-text-secondary); font-size: 14px; font-weight: 500; padding: 14px 24px; text-decoration: none; }
.admin-nav__item:hover { color: var(--color-text-body); }
.admin-nav__item--active { border-bottom-color: var(--color-primary); color: var(--color-primary); }

.section-actions { margin-bottom: 16px; }

.add-btn {
  background: var(--color-primary); border: 0; border-radius: 6px; color: #fff;
  cursor: pointer; font: inherit; padding: 8px 20px; white-space: nowrap;
}
.add-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.add-form {
  background: var(--color-bg-card); border: 1px solid var(--color-border);
  border-radius: 8px; display: flex; flex-direction: column; gap: 10px;
  margin-bottom: 24px; padding: 20px;
}
.form-row { display: flex; gap: 10px; }

.form-input, .form-select {
  border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit;
  font-size: 14px; padding: 8px 12px;
}
.form-input:focus, .form-select:focus { border-color: var(--color-primary); outline: none; }
.form-input--mono { font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace; font-size: 13px; }

.rule-table {
  background: var(--color-bg-card); border: 1px solid var(--color-border);
  border-radius: 8px; width: 100%; border-collapse: collapse; overflow: hidden;
}
.rule-table th, .rule-table td {
  padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--color-border-light); font-size: 14px;
}
.rule-table th { background: var(--color-bg-hover); font-weight: 600; }
.col-name { font-weight: 500; white-space: nowrap; }
.col-desc { color: var(--color-text-secondary); max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.cat-badge { border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px; white-space: nowrap; }
.cat-badge--recommendation { background: #fff7ed; color: #ea580c; }
.cat-badge--manipulation { background: #fef2f2; color: #dc2626; }

.level-badge { border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px; }
.level-badge--warn { background: var(--color-warning-light); color: var(--color-warning); }
.level-badge--review { background: var(--color-bg-info); color: var(--color-info); }
.level-badge--block { background: var(--color-danger-light); color: var(--color-danger); }

.pattern-code {
  background: var(--color-bg-hover); border-radius: 4px; font-size: 12px;
  max-width: 200px; overflow: hidden; padding: 2px 6px; text-overflow: ellipsis;
  white-space: nowrap; display: inline-block;
}

.del-btn { background: none; border: 1px solid var(--color-danger); border-radius: 4px; color: var(--color-danger); cursor: pointer; font: inherit; font-size: 13px; padding: 4px 12px; }
.del-btn:hover { background: var(--color-danger); color: #fff; }

.empty-state { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; padding: 40px; text-align: center; color: var(--color-text-muted); }

/* ── 测试工具 ── */
.test-section { background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 8px; margin-top: 32px; padding: 24px; }
.test-section h2 { font-size: 18px; margin: 0 0 4px; }
.test-hint { color: var(--color-text-muted); font-size: 13px; margin: 0 0 16px; }
.test-textarea {
  border: 1px solid var(--color-border-input); border-radius: 6px; font: inherit;
  font-size: 14px; padding: 12px; width: 100%; box-sizing: border-box;
  resize: vertical; line-height: 1.6; margin-bottom: 12px;
}
.test-textarea:focus { border-color: var(--color-primary); outline: none; }
.test-result { margin-top: 16px; }
.result-summary { font-size: 15px; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.result-label { color: var(--color-text-body); }
.result-ok { color: var(--color-success); }
.result-block { color: var(--color-danger); }
.result-review { color: var(--color-info); }
.result-warn { color: var(--color-warning); }
.result-cats { font-weight: 400; font-size: 13px; color: var(--color-text-secondary); }
.result-matches { border-top: 1px solid var(--color-border-light); padding-top: 12px; }
.result-matches h4 { font-size: 14px; margin: 0 0 8px; color: var(--color-text-body); }
.match-item { background: var(--color-bg-hover); border-radius: 6px; font-size: 13px; margin-bottom: 6px; padding: 8px 12px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.match-rule { font-weight: 600; }
.match-text { color: var(--color-text-secondary); }
.match-desc { color: var(--color-text-muted); font-size: 12px; }

@media (max-width: 780px) {
  .admin-nav__item { padding: 10px 14px; font-size: 13px; }
  .add-form { padding: 16px; }
  .form-row { flex-direction: column; }
  .rule-table { font-size: 13px; }
  .rule-table th, .rule-table td { padding: 8px 10px; }
}
</style>
