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
