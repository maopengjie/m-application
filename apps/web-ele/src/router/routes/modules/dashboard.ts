import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: "lucide:area-chart",
      order: 2,
      title: "数据分析",
    },
    name: "AnalyticsMenu",
    path: "/analytics",
    children: [
      {
        name: "Analytics",
        path: "",
        component: () => import("#/views/dashboard/analytics/index.vue"),
        meta: {
          affixTab: true,
          hideInMenu: true,
          title: "数据分析",
        },
      },
      {
        name: "CrawlerHealth",
        path: "/crawler-health",
        component: () => import("#/views/dashboard/crawler/index.vue"),
        meta: {
          icon: "lucide:activity",
          title: "爬虫治理看板",
        },
      },
      {
        name: "Workspace",
        path: "/workspace",
        component: () => import("#/views/dashboard/workspace/index.vue"),
        meta: {
          hideInMenu: true,
          icon: "carbon:workspace",
          title: "工作台",
        },
      },
    ],
  },
];

export default routes;
