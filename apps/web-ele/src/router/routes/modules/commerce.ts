import type { RouteRecordRaw } from "vue-router";

import { BasicLayout } from "#/layouts";

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: "lucide:shopping-bag",
      order: -1,
      title: "购物决策中心",
    },
    name: "SmartCommerce",
    path: "/commerce",
    children: [
      {
        name: "CommerceInsights",
        path: "insights",
        component: () => import("#/views/InsightView.vue"),
        meta: {
          icon: "lucide:sparkles",
          title: "今日异动",
        },
      },
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
          tabByPath: false,
          activePath: "/commerce/search",
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
        name: "CommerceFollows",
        path: "follows",
        component: () => import("#/views/FollowView.vue"),
        meta: {
          icon: "lucide:heart",
          title: "关注商品",
        },
      },
    ],
  },
  {
    component: BasicLayout,
    meta: {
      icon: "lucide:database",
      order: 10,
      title: "数据运营中心",
      authority: ["admin"],
    },
    name: "AdminSystems",
    path: "/admin",
    children: [
      {
        name: "AdminTasks",
        path: "crawler",
        component: () => import("#/views/tools/tasks/index.vue"),
        meta: {
          icon: "lucide:server",
          title: "爬虫任务管理",
        },
      },
      {
        name: "AdminCoupons",
        path: "coupons",
        component: () => import("#/views/CouponView.vue"),
        meta: {
          icon: "lucide:ticket-percent",
          title: "优惠策略分析",
        },
      },
      {
        name: "AdminRisk",
        path: "risk",
        component: () => import("#/views/RiskView.vue"),
        meta: {
          icon: "lucide:shield-alert",
          title: "风险评估后台",
        },
      },
    ],
  },
];

export default routes;
