<script lang="ts" setup>
import type {
  WorkbenchProjectItem,
  WorkbenchQuickNavItem,
  WorkbenchTodoItem,
  WorkbenchTrendItem,
} from '@vben/common-ui';

import { ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  AnalysisChartCard,
  WorkbenchHeader,
  WorkbenchProject,
  WorkbenchQuickNav,
  WorkbenchTodo,
  WorkbenchTrends,
} from '@vben/common-ui';
import { preferences } from '@vben/preferences';
import { useUserStore } from '@vben/stores';
import { openWindow } from '@vben/utils';

import AnalyticsVisitsSource from '../analytics/analytics-visits-source.vue';

const userStore = useUserStore();

const projectItems: WorkbenchProjectItem[] = [
  {
    color: '#2563eb',
    content: '聚焦本周最重要的功能，优先把核心闭环做完整。',
    date: '2026-04-30',
    group: '产品节奏',
    icon: 'lucide:target',
    title: '本周目标',
    url: '/dashboard/analytics',
  },
  {
    color: '#0f766e',
    content: '把关键指标、趋势和来源统一收敛到一个观察面板。',
    date: '2026-04-30',
    group: '数据看板',
    icon: 'lucide:chart-column',
    title: '分析页',
    url: '/dashboard/analytics',
  },
  {
    color: '#7c3aed',
    content: '整理待办、关键变更和最近动作，保持项目推进节奏。',
    date: '2026-04-30',
    group: '工作台',
    icon: 'lucide:briefcase-business',
    title: '工作台',
    url: '/dashboard/workspace',
  },
  {
    color: '#ea580c',
    content: '维护登录态、权限和个人资料等基础能力，保证可持续迭代。',
    date: '2026-04-30',
    group: '基础设施',
    icon: 'lucide:shield-check',
    title: '账户中心',
    url: '/profile',
  },
  {
    color: '#4f46e5',
    content: '把产品说明、部署方式和开发约定沉淀成可回看的文档。',
    date: '2026-04-30',
    group: '项目文档',
    icon: 'carbon:logo-github',
    title: '仓库主页',
    url: 'https://github.com/maopengjie',
  },
];

const quickNavItems: WorkbenchQuickNavItem[] = [
  {
    color: '#1fdaca',
    icon: 'ion:home-outline',
    title: '首页',
    url: '/',
  },
  {
    color: '#bf0c2c',
    icon: 'ion:grid-outline',
    title: '仪表盘',
    url: '/dashboard/workspace',
  },
  {
    color: '#e18525',
    icon: 'ion:bar-chart-outline',
    title: '趋势分析',
    url: '/analytics',
  },
  {
    color: '#3fb27f',
    icon: 'ion:settings-outline',
    title: '个人设置',
    url: '/profile',
  },
  {
    color: '#4daf1bc9',
    icon: 'ion:reader-outline',
    title: '项目文档',
    url: 'https://github.com/maopengjie',
  },
  {
    color: '#00d8ff',
    icon: 'ion:checkmark-done-outline',
    title: '待办检查',
    url: '/dashboard/workspace',
  },
];

const todoItems = ref<WorkbenchTodoItem[]>([
  {
    completed: false,
    content: `定义唯一主线功能，避免项目继续停留在“底座很多、产品不清晰”的状态。`,
    date: '2026-04-30 11:00:00',
    title: '确认核心产品方向',
  },
  {
    completed: false,
    content: `把一个最关键的数据实体接到真实存储或真实 API，替代纯 mock 展示。`,
    date: '2026-04-30 14:00:00',
    title: '接入真实数据链路',
  },
  {
    completed: false,
    content: `整理环境变量、README 和部署说明，降低未来回看和继续开发的成本。`,
    date: '2026-05-01 10:00:00',
    title: '补全文档和环境说明',
  },
  {
    completed: false,
    content: `给登录、工作台和核心业务流补最小可用验证，避免后续改动失控。`,
    date: '2026-05-02 16:00:00',
    title: '补关键链路验证',
  },
  {
    completed: false,
    content: `部署一个自己会每天打开使用的版本，让项目进入真实反馈循环。`,
    date: '2026-05-03 18:00:00',
    title: '发布可持续使用版本',
  },
]);
const trendItems: WorkbenchTrendItem[] = [
  {
    avatar: 'svg:avatar-1',
    content: `整理了工作台入口，移除了和主产品方向无关的演示页面。`,
    date: '刚刚',
    title: '项目助手',
  },
  {
    avatar: 'svg:avatar-2',
    content: `确认下一阶段重点是把 mock 数据替换成真实业务链路。`,
    date: '1个小时前',
    title: '产品节奏',
  },
  {
    avatar: 'svg:avatar-3',
    content: `更新了首页内容，让项目更像产品控制台，而不是技术模板。`,
    date: '1天前',
    title: '工作台',
  },
  {
    avatar: 'svg:avatar-4',
    content: `开始梳理部署说明、环境变量和长期维护所需的最小文档。`,
    date: '2天前',
    title: '工程整理',
  },
  {
    avatar: 'svg:avatar-1',
    content: `完成了一轮项目分析，明确“少做框架，多做闭环”的推进原则。`,
    date: '3天前',
    title: '产品复盘',
  },
  {
    avatar: 'svg:avatar-2',
    content: `预留了分析页和个人设置入口，作为后续真实功能承载区。`,
    date: '1周前',
    title: '基础能力',
  },
  {
    avatar: 'svg:avatar-3',
    content: `准备把核心指标、待办和项目文档集中到一个统一视图。`,
    date: '1周前',
    title: '看板规划',
  },
  {
    avatar: 'svg:avatar-4',
    content: `建立了 monorepo 工程基础，方便后续继续沿主线演进。`,
    date: '2026-04-24 20:00',
    title: '项目基础',
  },
];

const router = useRouter();

function navTo(nav: WorkbenchProjectItem | WorkbenchQuickNavItem) {
  if (nav.url?.startsWith('http')) {
    openWindow(nav.url);
    return;
  }
  if (nav.url?.startsWith('/')) {
    router.push(nav.url).catch((error) => {
      console.error('Navigation failed:', error);
    });
  } else {
    console.warn(`Unknown URL for navigation item: ${nav.title} -> ${nav.url}`);
  }
}
</script>

<template>
  <div class="p-5">
    <WorkbenchHeader
      :avatar="userStore.userInfo?.avatar || preferences.app.defaultAvatar"
    >
      <template #title>
        欢迎回来，{{ userStore.userInfo?.realName || '创作者' }}，继续推进你的产品。
      </template>
      <template #description>
        今天的重点是缩小范围、完成闭环，并让项目更接近真实可用。
      </template>
    </WorkbenchHeader>

    <div class="mt-5 flex flex-col lg:flex-row">
      <div class="mr-4 w-full lg:w-3/5">
        <WorkbenchProject :items="projectItems" title="项目" @click="navTo" />
        <WorkbenchTrends :items="trendItems" class="mt-5" title="最新动态" />
      </div>
      <div class="w-full lg:w-2/5">
        <WorkbenchQuickNav
          :items="quickNavItems"
          class="mt-5 lg:mt-0"
          title="快捷导航"
          @click="navTo"
        />
        <WorkbenchTodo :items="todoItems" class="mt-5" title="待办事项" />
        <AnalysisChartCard class="mt-5" title="访问来源">
          <AnalyticsVisitsSource />
        </AnalysisChartCard>
      </div>
    </div>
  </div>
</template>
