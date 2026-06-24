<template>
  <section class="page model-page">
    <div class="page-header settings-header">
      <div>
        <p class="eyebrow">Model API Layer</p>
        <h1 class="page-title">模型管理</h1>
        <p class="page-description">管理文字推理与文生图 Provider。密钥只从后端系统环境变量读取，前端不输入 secret。</p>
      </div>
      <div class="settings-actions">
        <el-button @click="loadSettings">刷新</el-button>
        <el-button :loading="testing" @click="testConnection">测试 LLM 连接</el-button>
        <el-button class="orange-button" type="primary" :loading="saving" @click="saveSettings">保存配置</el-button>
      </div>
    </div>

    <el-alert v-if="error" class="settings-alert" type="error" :title="error" :closable="false" show-icon />
    <el-alert
      v-if="settings && usesDashscope && !settings.dashscope_api_key_configured"
      class="settings-alert"
      type="warning"
      title="当前选择了 DashScope，但后端未检测到 DASHSCOPE_API_KEY。"
      :closable="false"
      show-icon
    />

    <div class="settings-shell">
      <aside class="settings-rail panel panel-pad">
        <p class="section-kicker">Configuration</p>
        <h2 class="section-title">Provider 状态</h2>
        <div class="status-stack">
          <div class="status-row">
            <span class="status-dot" :class="settings?.dashscope_api_key_configured ? 'success' : ''"></span>
            <div>
              <strong>DashScope API Key</strong>
              <small>{{ settings?.dashscope_api_key_configured ? '后端已配置' : '后端未配置' }}</small>
            </div>
          </div>
          <div class="status-row">
            <span class="status-dot" :class="settings?.dashscope_workspace_id_configured ? 'success' : ''"></span>
            <div>
              <strong>Workspace ID</strong>
              <small>{{ settings?.dashscope_workspace_id_configured ? '后端已配置' : '可选配置' }}</small>
            </div>
          </div>
          <div class="status-row">
            <span class="status-dot running"></span>
            <div>
              <strong>Secret policy</strong>
              <small>只读环境变量，不在浏览器保存密钥</small>
            </div>
          </div>
        </div>
      </aside>

      <main class="settings-main">
        <div class="settings-grid">
          <section class="panel panel-pad settings-panel">
            <div class="panel-heading">
              <div>
                <p class="section-kicker">Text reasoning</p>
                <h2>文字推理</h2>
                <p>分析、方案、Prompt、评审、文案和修改意图。</p>
              </div>
              <el-tag :type="settings?.dashscope_api_key_configured ? 'success' : 'info'" effect="plain">
                Key {{ settings?.dashscope_api_key_configured ? '已配置' : '未配置' }}
              </el-tag>
            </div>

            <el-skeleton v-if="loading" :rows="5" animated />
            <el-form v-else label-position="top" :model="form">
              <el-form-item label="Provider">
                <el-select v-model="form.text_provider">
                  <el-option v-for="provider in textProviders" :key="provider" :label="provider" :value="provider" />
                </el-select>
              </el-form-item>
              <el-form-item label="模型">
                <el-input v-model="form.text_model" placeholder="qwen3.7plus" />
              </el-form-item>
              <el-form-item label="DashScope Chat Base URL">
                <el-input v-model="form.dashscope_text_base_url" />
              </el-form-item>
            </el-form>
          </section>

          <section class="panel panel-pad settings-panel">
            <div class="panel-heading">
              <div>
                <p class="section-kicker">Image generation</p>
                <h2>文生图</h2>
                <p>生成商品营销图，本地 Mock 与百炼 Provider 使用同一接口。</p>
              </div>
              <el-tag :type="settings?.dashscope_workspace_id_configured ? 'success' : 'info'" effect="plain">
                Workspace {{ settings?.dashscope_workspace_id_configured ? '已配置' : '可选' }}
              </el-tag>
            </div>

            <el-skeleton v-if="loading" :rows="5" animated />
            <el-form v-else label-position="top" :model="form">
              <el-form-item label="Provider">
                <el-select v-model="form.image_provider">
                  <el-option v-for="provider in imageProviders" :key="provider" :label="provider" :value="provider" />
                </el-select>
              </el-form-item>
              <el-form-item label="模型">
                <el-input v-model="form.image_model" placeholder="wan2.6-t2i" />
              </el-form-item>
              <el-form-item label="DashScope Image Generation URL">
                <el-input v-model="form.dashscope_image_generation_url" />
              </el-form-item>
            </el-form>
          </section>
        </div>

        <section v-if="testResult" class="panel panel-pad test-panel">
          <div class="panel-heading">
            <div>
              <p class="section-kicker">Connection test</p>
              <h2>最近一次连接测试</h2>
              <p>{{ testResult.message }}</p>
            </div>
            <el-tag :type="testResult.status === 'success' ? 'success' : 'danger'" effect="plain">
              {{ testResult.status }}
            </el-tag>
          </div>
          <div class="test-grid">
            <div>
              <dt>Provider</dt>
              <dd>{{ testResult.provider }}</dd>
            </div>
            <div>
              <dt>模型</dt>
              <dd>{{ testResult.model }}</dd>
            </div>
            <div>
              <dt>耗时</dt>
              <dd>{{ testResult.latency_ms }}ms</dd>
            </div>
            <div>
              <dt>检测时间</dt>
              <dd>{{ new Date(testResult.checked_at).toLocaleString() }}</dd>
            </div>
          </div>
        </section>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { errorMessage } from '../api/client'
import {
  getModelSettings,
  type ModelConnectionTest,
  type ModelSettings,
  testTextModelConnection,
  updateModelSettings
} from '../api/productshot'

const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const error = ref('')
const settings = ref<ModelSettings | null>(null)
const testResult = ref<ModelConnectionTest | null>(null)
const form = reactive({
  text_provider: 'mock',
  text_model: '',
  image_provider: 'mock',
  image_model: '',
  dashscope_text_base_url: '',
  dashscope_image_generation_url: ''
})

const textProviders = computed(() => settings.value?.available_text_providers || ['mock', 'dashscope'])
const imageProviders = computed(() => settings.value?.available_image_providers || ['mock', 'dashscope', 'openai'])
const usesDashscope = computed(() => form.text_provider === 'dashscope' || form.image_provider === 'dashscope')

function syncForm(next: ModelSettings) {
  settings.value = next
  form.text_provider = next.text_provider
  form.text_model = next.text_model
  form.image_provider = next.image_provider
  form.image_model = next.image_model
  form.dashscope_text_base_url = next.dashscope_text_base_url
  form.dashscope_image_generation_url = next.dashscope_image_generation_url
}

async function loadSettings() {
  loading.value = true
  error.value = ''
  try {
    syncForm(await getModelSettings())
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  error.value = ''
  try {
    const next = await updateModelSettings({
      text_provider: form.text_provider,
      text_model: form.text_model,
      image_provider: form.image_provider,
      image_model: form.image_model,
      dashscope_text_base_url: form.dashscope_text_base_url,
      dashscope_image_generation_url: form.dashscope_image_generation_url
    })
    syncForm(next)
    ElMessage.success('模型配置已更新')
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  testing.value = true
  error.value = ''
  try {
    testResult.value = await testTextModelConnection()
    if (testResult.value.status === 'success') {
      ElMessage.success('LLM 连接测试通过')
    } else {
      ElMessage.warning(testResult.value.message)
    }
  } catch (err) {
    error.value = errorMessage(err)
  } finally {
    testing.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.model-page {
  max-width: 1280px;
}

.settings-header {
  align-items: flex-end;
}

.settings-alert {
  margin-bottom: 12px;
}

.settings-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.settings-shell {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.settings-rail {
  position: sticky;
  top: 22px;
  display: grid;
  gap: 14px;
}

.status-stack {
  display: grid;
  gap: 10px;
}

.status-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr);
  align-items: start;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  background: var(--ps-surface-quiet);
}

.status-row strong {
  display: block;
  color: var(--ps-heading);
  font-size: 13px;
}

.status-row small {
  display: block;
  margin-top: 4px;
  color: var(--ps-muted);
  font-size: 12px;
  line-height: 1.45;
}

.settings-main {
  display: grid;
  gap: 14px;
  min-width: 0;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.settings-panel {
  min-width: 0;
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.panel-heading h2 {
  margin: 0;
  color: var(--ps-heading);
  font-size: 20px;
}

.panel-heading p {
  margin: 7px 0 0;
  color: var(--ps-muted);
  line-height: 1.65;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

dt {
  color: var(--ps-primary);
  font-size: 12px;
  font-weight: 800;
}

dd {
  margin: 6px 0 0;
  color: var(--ps-muted-strong);
  line-height: 1.6;
  word-break: break-word;
}

@media (max-width: 1080px) {
  .settings-shell,
  .settings-grid,
  .test-grid {
    grid-template-columns: 1fr;
  }

  .settings-rail {
    position: static;
  }
}

@media (max-width: 720px) {
  .settings-header,
  .panel-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .settings-actions .el-button {
    flex: 1;
  }
}
</style>
