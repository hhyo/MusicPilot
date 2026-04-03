<template>
  <div class="home-view">
    <section class="hero-panel">
      <div class="hero-panel__content">
        <p class="hero-panel__eyebrow">MusicPilot Home</p>
        <h2>你的音乐工作台</h2>
        <p class="hero-panel__description">
          当前仓库已进入 Phase 2。搜索模块已打通本地 seed metadata 的最小闭环，
          其余榜单、订阅、下载、整理仍保持占位边界，待后续阶段继续接入。
        </p>
        <div class="hero-panel__actions">
          <RouterLink class="hero-panel__action hero-panel__action--primary" to="/search">
            查看搜索入口
          </RouterLink>
          <RouterLink class="hero-panel__action" to="/downloads">
            查看任务入口
          </RouterLink>
        </div>
      </div>
      <div class="hero-panel__grid">
        <article v-for="item in dashboardStats" :key="item.label" class="stat-card">
          <span class="stat-card__label">{{ item.label }}</span>
          <strong class="stat-card__value">{{ item.value }}</strong>
          <p class="stat-card__note">{{ item.note }}</p>
        </article>
      </div>
    </section>

    <section class="section">
      <header class="section__header">
        <div>
          <p class="section__eyebrow">Phase 2 Scope</p>
          <h3>当前模块状态</h3>
        </div>
        <el-tag type="success" effect="plain">搜索最小闭环已接通</el-tag>
      </header>

      <div class="module-grid">
        <ModuleEntryCard
          v-for="module in featureModules"
          :key="module.key"
          :module="module"
        />
      </div>
    </section>

    <section class="section section--compact">
      <header class="section__header">
        <div>
          <p class="section__eyebrow">Phase 2 Notes</p>
          <h3>当前边界说明</h3>
        </div>
      </header>

      <div class="notes-grid">
        <article class="note-card">
          <h4>已完成</h4>
          <ul>
            <li>App Shell 与基础路由。</li>
            <li>本地 seed metadata 搜索与详情页最小闭环。</li>
            <li>前端服务、类型、状态管理扩展位。</li>
          </ul>
        </article>
        <article class="note-card">
          <h4>待后续接入</h4>
          <ul>
            <li>真实第三方 metadata provider。</li>
            <li>真实 PT 搜索、下载、整理链路。</li>
            <li>订阅调度、查询构建与规则决策。</li>
          </ul>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink } from 'vue-router';

import ModuleEntryCard from '@/components/ModuleEntryCard.vue';
import { navigationModules } from '@/types/module';

const dashboardStats = [
  { label: 'Metadata Provider', value: '1', note: '当前为本地 seed / mock provider。' },
  { label: '可搜索实体', value: '3', note: 'Artist / Album / Track 已接通统一搜索页。' },
  { label: '最近订阅', value: '0', note: '占位完成，待接四类订阅模型。' },
  { label: '待下载决策', value: '0', note: '本轮不实现 PT 搜索与下载派发。' },
];

const featureModules = computed(() => navigationModules.filter((item) => item.key !== 'home'));
</script>

<style scoped lang="scss">
.home-view {
  display: grid;
  gap: 1.5rem;
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 0.8fr);
  gap: 1.25rem;
  padding: 1.5rem;
  border: 1px solid var(--mp-line);
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(126, 94, 248, 0.18), transparent 34%),
    rgba(255, 255, 255, 0.82);
  box-shadow: 0 20px 44px rgba(52, 37, 122, 0.08);
}

.hero-panel__content h2 {
  margin: 0.3rem 0 0.8rem;
  font-size: clamp(1.8rem, 3vw, 2.5rem);
}

.hero-panel__eyebrow,
.section__eyebrow {
  margin: 0;
  color: var(--mp-accent);
  font-size: 0.84rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-panel__description {
  max-width: 62ch;
  margin: 0;
  color: var(--mp-muted);
  line-height: 1.8;
}

.hero-panel__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 1.5rem;
}

.hero-panel__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.82rem 1.1rem;
  border: 1px solid var(--mp-line);
  border-radius: 14px;
  background: #fff;
  color: var(--mp-text);
  font-weight: 700;
  text-decoration: none;
}

.hero-panel__action--primary {
  border-color: transparent;
  background: var(--mp-accent);
  color: #fff;
}

.hero-panel__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.stat-card,
.note-card {
  padding: 1.1rem;
  border: 1px solid var(--mp-line);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
}

.stat-card__label {
  color: var(--mp-muted);
  font-size: 0.88rem;
}

.stat-card__value {
  display: block;
  margin-top: 0.45rem;
  font-size: 1.8rem;
}

.stat-card__note {
  margin: 0.7rem 0 0;
  color: var(--mp-muted);
  line-height: 1.65;
}

.section {
  display: grid;
  gap: 1rem;
  padding: 1.4rem;
  border: 1px solid var(--mp-line);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 18px 40px rgba(52, 37, 122, 0.06);
}

.section--compact {
  padding-bottom: 1.2rem;
}

.section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.section__header h3 {
  margin: 0.35rem 0 0;
  font-size: 1.35rem;
}

.module-grid,
.notes-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.note-card h4 {
  margin: 0 0 0.7rem;
}

.note-card ul {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--mp-muted);
  line-height: 1.8;
}

@media (max-width: 960px) {
  .hero-panel,
  .module-grid,
  .notes-grid {
    grid-template-columns: 1fr;
  }
}
</style>
