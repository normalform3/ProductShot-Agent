<template>
  <div class="workflow-stepper panel panel-pad">
    <div v-for="(step, index) in steps" :key="step.key" class="workflow-step">
      <div class="step-index" :class="step.status">
        <span>{{ index + 1 }}</span>
      </div>
      <div>
        <div class="step-title">
          {{ step.title }}
          <span class="status-dot" :class="step.status"></span>
        </div>
        <p>{{ step.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WorkflowStep } from '../stores/project'

defineProps<{
  steps: WorkflowStep[]
}>()
</script>

<style scoped>
.workflow-stepper {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0;
  overflow: hidden;
  padding: 0;
}

.workflow-step {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 18px;
  border-right: 1px solid var(--ps-border);
}

.workflow-step:last-child {
  border-right: 0;
}

.step-index {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border: 1px solid var(--ps-border);
  border-radius: 999px;
  color: var(--ps-muted);
  background: var(--ps-surface-quiet);
  font-weight: 800;
}

.step-index.success {
  color: #fff;
  background: var(--ps-primary);
}

.step-index.running {
  color: #fff;
  border-color: var(--ps-accent);
  background: var(--ps-accent);
}

.step-index.failed {
  color: #fff;
  border-color: var(--ps-danger);
  background: var(--ps-danger);
}

.step-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 800;
}

p {
  margin: 5px 0 0;
  color: var(--ps-muted);
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 1000px) {
  .workflow-stepper {
    grid-template-columns: 1fr;
  }

  .workflow-step {
    grid-template-columns: 42px minmax(0, 1fr);
    border-right: 0;
    border-bottom: 1px solid var(--ps-border);
  }

  .workflow-step:last-child {
    border-bottom: 0;
  }
}
</style>
