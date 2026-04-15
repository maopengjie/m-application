import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: 'lucide:trending-up',
      order: 1,
      title: '价格监测',
    },
    name: 'PriceMonitor',
    path: '/price-monitor',
    children: [
      {
        name: 'PriceMonitorHome',
        path: 'home',
        component: () => import('#/views/HomeView.vue'),
        meta: {
          icon: 'lucide:home',
          title: '主页',
        },
      },
      {
        name: 'PriceSearch',
        path: 'search',
        component: () => import('#/views/SearchView.vue'),
        meta: {
          icon: 'lucide:search',
          title: '行情搜索',
        },
      },
      {
        name: 'ProductDetail',
        path: 'detail',
        component: () => import('#/views/ProductDetailView.vue'),
        meta: {
          icon: 'lucide:info',
          title: '产品详情',
          hideInMenu: true,
        },
      },
      {
        name: 'PriceAlert',
        path: 'alert',
        component: () => import('#/views/AlertView.vue'),
        meta: {
          icon: 'lucide:bell',
          title: '价格告警',
        },
      },
    ],
  },
];

export default routes;
