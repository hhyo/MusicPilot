<template>
  <section class="placeholder-view">
    <header class="placeholder-view__header">
      <div>
        <p class="placeholder-view__eyebrow">Planned Module</p>
        <h2>{{ title }}</h2>
      </div>
      <el-tag type="warning" effect="plain">待后续接入</el-tag>
    </header>

    <p class="placeholder-view__description">{{ description }}</p>

    <div class="placeholder-grid">
      <article class="placeholder-card">
        <h3>当前状态</h3>
        <p>入口已保留，已明确模块边界，但当前页面仍不承载真实业务实现。</p>
      </article>
      <article class="placeholder-card">
        <h3>后续接入点</h3>
        <p>后续将从 `services/`、`types/` 和后端 API 契约开始补齐，不直接在页面内堆业务逻辑。</p>
      </article>
      <article class="placeholder-card">
        <h3>本轮约束</h3>
        <p>当前页面只保留模块入口与后续方向说明，不承担真实操作链路。</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const title = computed(() => String(route.meta.title ?? '占位页'));
const description = computed(() => String(route.meta.description ?? ''));
</script>

<style scoped lang="scss">
.placeholder-view {
  display: grid;
  gap: 1rem;
  padding: 1.5rem;
  border: 1px solid var(--mp-line);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 44px rgba(52, 37, 122, 0.08);
}

.placeholder-view__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.placeholder-view__eyebrow {
  margin: 0;
  color: var(--mp-accent);
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.placeholder-view__header h2 {
  margin: 0.3rem 0 0;
}

.placeholder-view__description {
  margin: 0;
  color: var(--mp-muted);
  line-height: 1.8;
}

.placeholder-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.placeholder-card {
  padding: 1.2rem;
  border: 1px solid var(--mp-line);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(248, 246, 255, 0.8), #fff);
}

.placeholder-card h3 {
  margin: 0 0 0.65rem;
}

.placeholder-card p {
  margin: 0;
  color: var(--mp-muted);
  line-height: 1.75;
}

@media (max-width: 960px) {
  .placeholder-grid {
    grid-template-columns: 1fr;
  }
}
</style>
