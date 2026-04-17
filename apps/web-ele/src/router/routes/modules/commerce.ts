import type { RouteRecordRaw } from "vue-router";

import { BasicLayout } from "#/layouts";

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: "lucide:shopping-cart",
      order: -1,
      title: "购物决策中心",
    },
    name: "SmartCommerce",
    path: "/commerce",
    children: [
      {
        name: "CommerceHome",
        path: "home",
        component: () => import("#/views/HomeView.vue"),
        meta: {
          icon: "lucide:home",
          title: "首页",
        },
      },
      {
        name: "CommerceSearch",
        path: "search",
        component: () => import("#/views/SearchView.vue"),
        meta: {
          icon: "lucide:search",
          title: "全网搜索",
        },
      },
      {
        name: "CommerceDetail",
        path: "detail/:id",
        component: () => import("#/views/ProductDetailView.vue"),
        meta: {
          icon: "lucide:info",
          title: "商品详情",
          hideInMenu: true,
        },
      },
      {
        name: "CommerceAlerts",
        path: "alerts",
        component: () => import("#/views/AlertView.vue"),
        meta: {
          icon: "lucide:bell",
          title: "降价提醒",
        },
      },
      {
        name: "CommerceCoupons",
        path: "coupons",
        component: () => import("#/views/CouponView.vue"),
        meta: {
          icon: "lucide:ticket-percent",
          title: "优惠计算",
        },
      },
      {
        name: "CommerceRisk",
        path: "risk-analysis",
        component: () => import("#/views/RiskView.vue"),
        meta: {
          icon: "lucide:shield-alert",
          title: "避雷分析",
        },
      },
      {
        name: "CommerceTasks",
        path: "crawler-tasks",
        component: () => import("#/views/tools/tasks/index.vue"),
        meta: {
          icon: "lucide:server",
          title: "爬虫任务",
        },
      },
    ],
  },
];

export default routes;
