<template>
  <section class="page">
    <div class="page-header">
      <div>
        <span class="eyebrow">New Brief</span>
        <h1 class="page-title">创建商品营销项目</h1>
        <p class="page-description">填写商品信息并上传原图，后续 Agent 会自动完成分析、创意、生成和文案。</p>
      </div>
    </div>

    <div class="brief-layout">
      <el-form class="panel panel-pad brief-form" label-position="top" :model="form" @submit.prevent>
        <div class="section-kicker">Product context</div>
        <div class="form-grid">
          <el-form-item label="商品名称">
            <el-input v-model="form.product_name" placeholder="例如：手工香薰蜡烛" />
          </el-form-item>
          <el-form-item label="商品类别">
            <el-input v-model="form.product_category" placeholder="例如：家居香氛" />
          </el-form-item>
        </div>
        <el-form-item label="核心卖点">
          <el-input
            v-model="form.core_selling_points"
            type="textarea"
            :rows="5"
            placeholder="手工制作、香味舒缓、适合作为礼物"
          />
        </el-form-item>
        <div class="form-grid">
          <el-form-item label="目标平台">
            <el-select v-model="form.target_platform">
              <el-option label="小红书" value="小红书" />
              <el-option label="朋友圈" value="朋友圈" />
              <el-option label="淘宝" value="淘宝" />
              <el-option label="抖音" value="抖音" />
            </el-select>
          </el-form-item>
          <el-form-item label="风格偏好">
            <el-select v-model="form.preferred_style">
              <el-option label="小红书生活方式风" value="小红书生活方式风" />
              <el-option label="高级极简白底风" value="高级极简白底风" />
              <el-option label="节日礼物促销风" value="节日礼物促销风" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="目标人群">
          <el-input v-model="form.target_audience" placeholder="例如：年轻女性、租房独居人群、礼物购买者" />
        </el-form-item>
        <div class="form-divider"></div>
        <el-form-item label="商品图片">
          <el-upload
            drag
            :auto-upload="false"
            :show-file-list="false"
            accept=".jpg,.jpeg,.png,.webp"
            :on-change="handleFile"
          >
            <div class="upload-copy">点击或拖拽上传商品图</div>
            <div class="upload-subcopy">Agent 会保留原商品主体，再生成场景图与营销文案。</div>
            <template #tip>
              <div class="el-upload__tip">支持 JPG、PNG、WebP。创建项目后会上传到本地 uploads。</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-button class="orange-button" type="primary" size="large" :loading="loading" @click="submit">
          创建并进入工作流
        </el-button>
      </el-form>

      <aside class="panel panel-pad preview-panel">
        <div>
          <p class="section-kicker">Source image</p>
          <h2 class="section-title">原图预览</h2>
        </div>
        <div class="image-frame preview-frame">
          <img v-if="previewUrl" :src="previewUrl" alt="商品预览" />
          <div v-else class="empty-preview">
            <span>等待图片</span>
            <strong>上传后会在这里预览主体构图</strong>
          </div>
        </div>
        <div class="readiness-list">
          <div class="readiness-item">
            <span class="status-dot success"></span>
            <strong>Mock 生图可运行</strong>
            <p>没有真实图片生成 API 时，也可以完成演示链路。</p>
          </div>
          <div class="readiness-item">
            <span class="status-dot running"></span>
            <strong>Brief 驱动生成</strong>
            <p>商品信息会进入分析、方案、Prompt 和文案节点。</p>
          </div>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage, type UploadFile } from 'element-plus'
import { useRouter } from 'vue-router'
import { createProject, uploadAsset } from '../api/productshot'
import { errorMessage } from '../api/client'

const router = useRouter()
const loading = ref(false)
const selectedFile = ref<File | null>(null)
const previewUrl = ref('')
const form = reactive({
  product_name: '',
  product_category: '',
  core_selling_points: '',
  target_platform: '小红书',
  target_audience: '',
  preferred_style: '小红书生活方式风'
})

function handleFile(file: UploadFile) {
  selectedFile.value = file.raw || null
  previewUrl.value = selectedFile.value ? URL.createObjectURL(selectedFile.value) : ''
}

async function submit() {
  if (!form.product_name.trim()) {
    ElMessage.warning('请填写商品名称')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请上传商品图片')
    return
  }
  loading.value = true
  try {
    const project = await createProject(form)
    await uploadAsset(project.id, selectedFile.value)
    ElMessage.success('项目创建成功')
    router.push(`/workflow/${project.id}`)
  } catch (error) {
    ElMessage.error(errorMessage(error))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.brief-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 0.72fr);
  gap: 18px;
  align-items: start;
}

.brief-form {
  display: grid;
  gap: 2px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-divider {
  height: 1px;
  margin: 4px 0 10px;
  background: var(--ps-border);
}

.preview-panel {
  position: sticky;
  top: 98px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.preview-frame {
  min-height: 440px;
}

.empty-preview {
  display: grid;
  height: 440px;
  place-items: center;
  align-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--ps-muted);
  text-align: center;
}

.empty-preview span {
  color: var(--ps-accent-dark);
  font-size: 12px;
  font-weight: 800;
}

.empty-preview strong {
  max-width: 260px;
  color: var(--ps-primary);
  font-family: Georgia, "Times New Roman", "Songti SC", serif;
  font-size: 26px;
  font-weight: 650;
  line-height: 1.18;
}

.upload-copy {
  padding: 30px 0 8px;
  color: var(--ps-primary);
  font-weight: 800;
}

.upload-subcopy,
.readiness-item p {
  max-width: 360px;
  margin: 0 auto;
  color: var(--ps-muted);
  line-height: 1.7;
}

.readiness-list {
  display: grid;
  gap: 10px;
}

.readiness-item {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr);
  gap: 4px 10px;
  padding: 14px;
  border: 1px solid var(--ps-border);
  border-radius: var(--ps-radius);
  background: var(--ps-surface-quiet);
}

.readiness-item .status-dot {
  margin-top: 6px;
}

.readiness-item p {
  grid-column: 2;
  margin: 0;
}

@media (max-width: 700px) {
  .brief-layout,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .preview-panel {
    position: static;
  }
}
</style>
