import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '#/layouts';

const routes: RouteRecordRaw[] = [
  {
    component: BasicLayout,
    meta: {
      icon: 'lucide:shopping-cart',
      order: 2,
      title: '购物决策',
    },
    name: 'Commerce',
    path: '/commerce',
    children: [
      {
        name: 'CommerceSearch',
        path: 'search',
        component: () => import('#/views/SearchView.vue'),
        meta: {
          title: '商品搜索',
        },
      },
      {
        name: 'CommerceDetail',
        path: 'detail/:id',
        component: () => import('#/views/ProductDetailView.vue'),
        meta: {
          hideInMenu: true,
          title: '商品详情',
        },
      },
      {
        name: 'CommerceAlerts',
        path: 'alerts',
        component: () => import('#/views/AlertView.vue'),
        meta: {
          title: '降价提醒',
        },
      },
    ],
  },
];

export default routes;
