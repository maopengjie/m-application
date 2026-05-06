import type { RouteRecordRaw } from 'vue-router';

import { $t } from '#/locales';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:database',
      order: -1,
      title: $t('page.dataCenter.title'),
    },
    name: 'DataCenter',
    path: '/data-center',
    children: [
      {
        name: 'CoreDashboard',
        path: '/data-center/core-dashboard',
        component: () => import('#/views/data-center/core-dashboard/index.vue'),
        meta: {
          affixTab: true,
          icon: 'lucide:layout-dashboard',
          title: $t('page.dataCenter.coreDashboard'),
        },
      },
      {
        name: 'SkuRepository',
        path: '/data-center/sku-repository',
        component: () => import('#/views/data-center/sku-repository/index.vue'),
        meta: {
          icon: 'lucide:box',
          title: $t('page.dataCenter.skuRepository'),
        },
      },
      {
        name: 'PriceTimeSeries',
        path: '/data-center/price-time-series',
        component: () => import('#/views/data-center/price-time-series/index.vue'),
        meta: {
          icon: 'lucide:trending-up',
          title: $t('page.dataCenter.priceTimeSeries'),
        },
      },
      {
        name: 'MappingCenter',
        path: '/data-center/mapping-center',
        component: () => import('#/views/data-center/mapping-center/index.vue'),
        meta: {
          icon: 'lucide:git-branch',
          title: $t('page.dataCenter.mappingCenter'),
        },
      },
      {
        name: 'DataCleaning',
        path: '/data-center/data-cleaning',
        component: () => import('#/views/data-center/data-cleaning/index.vue'),
        meta: {
          icon: 'lucide:clipboard-list',
          title: $t('page.dataCenter.dataCleaning'),
        },
      },
    ],
  },
];

export default routes;
