<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { fetchPrivacySettings, updatePrivacySettings } from '../api/auth'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()
const saving = ref(false)
const saved = ref(false)
const privacySaving = ref(false)

const form = reactive({
  nickname: auth.user?.nickname || '',
  bio: auth.user?.bio || '',
  phone: auth.user?.phone || '',
  email: auth.user?.email || '',
  investment_tags: auth.user?.investment_tags || [],
  follow_markets: auth.user?.follow_markets || [],
})

// 可选的标签选项
const availableTags = [
  '价值投资', '成长投资', '量化交易', '技术分析',
  '长期持有', '短线交易', '股息策略', '定投策略',
  '宏观分析', '行业研究', '打新策略', '套利交易',
]

const availableMarkets = [
  { value: 'a_stock', label: 'A股' },
  { value: 'hk_stock', label: '港股' },
  { value: 'us_stock', label: '美股' },
  { value: 'fund', label: '基金' },
  { value: 'futures', label: '期货' },
  { value: 'bond', label: '债券' },
]

function toggleTag(tag) {
  const idx = form.investment_tags.indexOf(tag)
  if (idx >= 0) {
    form.investment_tags.splice(idx, 1)
  } else {
    form.investment_tags.push(tag)
  }
}

function toggleMarket(market) {
  const idx = form.follow_markets.indexOf(market)
  if (idx >= 0) {
    form.follow_markets.splice(idx, 1)
  } else {
    form.follow_markets.push(market)
  }
}

const privacy = reactive({
  profile_visibility: 'public',
  message_permission: 'everyone',
  show_investment_info: true,
  show_follow_lists: true,
  show_activity_status: true,
})

onMounted(loadPrivacy)

async function handleSave() {
  saving.value = true
  try {
    await auth.updateProfile({
      nickname: form.nickname,
      bio: form.bio,
      investment_tags: form.investment_tags,
      follow_markets: form.follow_markets,
    })
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch (err) {
    console.error('保存失败:', err.message)
  } finally {
    saving.value = false
  }
}

async function loadPrivacy() {
  try {
    Object.assign(privacy, await fetchPrivacySettings())
  } catch (err) {
    toast.error(err.message || '隐私设置加载失败')
  }
}

async function handlePrivacySave() {
  privacySaving.value = true
  try {
    Object.assign(privacy, await updatePrivacySettings(privacy))
    toast.success('隐私设置已保存')
  } catch (err) {
    toast.error(err.message || '保存失败')
  } finally {
    privacySaving.value = false
  }
}
</script>

<template>
    <header class="toolbar">
      <div>
        <h1>个人设置</h1>
        <p>管理您的个人资料和偏好</p>
      </div>
    </header>

    <div class="settings-card">
      <h2>个人资料</h2>
      <div class="form-field">
        <label>昵称</label>
        <input v-model="form.nickname" type="text" class="form-input" maxlength="20">
      </div>
      <div class="form-field">
        <label>个人简介</label>
        <textarea v-model="form.bio" class="form-input" rows="3" maxlength="500" placeholder="介绍一下自己..." />
      </div>
      <div class="form-field">
        <label>手机号</label>
        <input v-model="form.phone" type="text" class="form-input" disabled>
        <span class="form-hint">手机号暂不支持修改</span>
      </div>
      <button class="save-btn" :disabled="saving" @click="handleSave">
        {{ saved ? '✓ 已保存' : saving ? '保存中...' : '保存修改' }}
      </button>
    </div>

    <div class="settings-card">
      <h2>隐私设置</h2>
      <div class="form-field">
        <label>资料可见性</label>
        <select v-model="privacy.profile_visibility" class="form-input">
          <option value="public">所有人可见</option>
          <option value="followers_only">仅粉丝可见</option>
          <option value="private">仅自己可见</option>
        </select>
      </div>
      <div class="form-field">
        <label>谁可以给我发私信</label>
        <select v-model="privacy.message_permission" class="form-input">
          <option value="everyone">所有人</option>
          <option value="followers_only">仅粉丝</option>
          <option value="none">不接收私信</option>
        </select>
      </div>
      <label class="switch-row">
        <span>
          <strong>展示投资信息</strong>
          <small>公开风险偏好、投资标签等信息</small>
        </span>
        <input v-model="privacy.show_investment_info" type="checkbox">
      </label>
      <label class="switch-row">
        <span>
          <strong>展示关注/粉丝列表</strong>
          <small>允许别人查看你的关注和粉丝</small>
        </span>
        <input v-model="privacy.show_follow_lists" type="checkbox">
      </label>
      <label class="switch-row">
        <span>
          <strong>展示活跃状态</strong>
          <small>公开成就、影响力等活动信息</small>
        </span>
        <input v-model="privacy.show_activity_status" type="checkbox">
      </label>
      <button class="save-btn" :disabled="privacySaving" @click="handlePrivacySave">
        {{ privacySaving ? '保存中...' : '保存隐私设置' }}
      </button>
    </div>

    <!-- 投资偏好 -->
    <div class="settings-card">
      <h2>投资偏好</h2>

      <div class="form-field">
        <label>关注领域</label>
        <p class="form-hint">选择您关注的市场，将影响个性化推荐内容</p>
        <div class="chip-group">
          <button
            v-for="m in availableMarkets"
            :key="m.value"
            :class="['chip', { 'chip--active': form.follow_markets.includes(m.value) }]"
            @click="toggleMarket(m.value)"
          >
            {{ m.label }}
          </button>
        </div>
      </div>

      <div class="form-field">
        <label>投资经验标签</label>
        <p class="form-hint">选择与您投资经验相关的标签，帮助其他用户了解您</p>
        <div class="chip-group">
          <button
            v-for="tag in availableTags"
            :key="tag"
            :class="['chip', { 'chip--active': form.investment_tags.includes(tag) }]"
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </button>
        </div>
        <div v-if="form.investment_tags.length" class="selected-tags">
          <span v-for="tag in form.investment_tags" :key="tag" class="selected-tag">
            {{ tag }} <button class="selected-tag__remove" @click="toggleTag(tag)">&times;</button>
          </span>
        </div>
      </div>
    </div>

    <!-- 实名认证 -->
    <div class="settings-card">
      <h2>实名认证</h2>
      <p class="settings-card__desc">提交身份证信息完成实名认证，获得认证标识</p>
      <button class="cert-btn" @click="$router.push('/me/settings/certification')">
        去认证
      </button>
    </div>

    <!-- 专业认证 -->
    <div class="settings-card">
      <h2>专业认证</h2>
      <p class="settings-card__desc">上传从业资格、学历证明等材料，审核通过后获得 <strong style="color:var(--color-primary)">加V标识</strong></p>
      <button class="cert-btn cert-btn--pro" @click="$router.push('/me/settings/professional-certification')">
        申请专业认证
      </button>
    </div>

    <!-- 风险评估 -->
    <div class="settings-card">
      <h2>投资者风险评估</h2>
      <p class="settings-card__desc">完成风险评估问卷以获得个性化的内容推荐</p>
      <button class="cert-btn cert-btn--secondary" @click="$router.push('/me/settings/assessment')">
        进行评估
      </button>
    </div>
</template>

<style scoped>
.toolbar { margin-bottom: 24px; }
.toolbar h1 { font-size: 28px; margin: 0 0 8px; }
.toolbar p { color: var(--color-text-secondary); margin: 0; }

.settings-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 20px;
  padding: 24px;
}

.settings-card h2 { font-size: 18px; margin: 0 0 16px; }
.settings-card__desc { color: var(--color-text-secondary); font-size: 14px; margin: 0 0 12px; }

.form-field { display: grid; gap: 6px; margin-bottom: 16px; }
.form-field label { color: var(--color-text-body); font-size: 14px; font-weight: 500; }

.form-input {
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  padding: 10px 12px;
  width: 100%;
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

.form-hint { color: var(--color-text-muted); font-size: 12px; }

.switch-row {
  align-items: center;
  border-top: 1px solid var(--color-border-light);
  cursor: pointer;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 14px 0;
}

.switch-row strong {
  color: var(--color-text-body);
  display: block;
  font-size: 14px;
}

.switch-row small {
  color: var(--color-text-muted);
  display: block;
  font-size: 12px;
  margin-top: 4px;
}

.switch-row input {
  height: 18px;
  width: 18px;
}

.save-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 10px 24px;
}

.save-btn:hover { background: var(--color-primary-hover); }

.cert-btn {
  background: var(--color-primary);
  border: 0;
  border-radius: 6px;
  color: var(--color-bg-card);
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  padding: 8px 20px;
}

.cert-btn--pro {
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
}

.cert-btn--pro:hover { background: var(--color-primary-light); }

.cert-btn--secondary {
  background: var(--color-bg-card);
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
}

.cert-btn--secondary:hover { background: var(--color-primary-light); }

/* ===== 偏好标签选择 ===== */
.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  background: var(--color-bg-hover);
  border: 1px solid var(--color-border-input);
  border-radius: 20px;
  color: var(--color-text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 6px 14px;
  transition: all 0.15s;
}

.chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.chip--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-bg-card);
}

.chip--active:hover {
  background: var(--color-primary-hover);
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.selected-tag {
  background: var(--color-primary-light);
  border-radius: 4px;
  color: var(--color-primary);
  font-size: 12px;
  padding: 4px 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.selected-tag__remove {
  background: none;
  border: 0;
  color: var(--color-primary);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}
</style>
