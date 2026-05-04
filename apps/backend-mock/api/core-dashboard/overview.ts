import { faker } from '@faker-js/faker';
import { eventHandler } from 'h3';

import { useResponseSuccess } from '~/utils/response';

interface CatalogItem {
  brand: string;
  category: string;
  platform: '京东' | '天猫' | '拼多多';
  productName: string;
  shopName: string;
  skuPrefix: string;
  priceRange: [number, number];
}

const productCatalog: CatalogItem[] = [
  {
    brand: 'Apple',
    category: '手机数码',
    platform: '京东',
    productName: 'Apple iPhone 15 128GB 黑色 国行 5G',
    shopName: 'Apple 产品京东自营旗舰店',
    skuPrefix: 'IP15',
    priceRange: [4599, 5999],
  },
  {
    brand: '华为',
    category: '手机数码',
    platform: '天猫',
    productName: '华为 Mate 60 Pro 12GB+512GB 雅丹黑',
    shopName: '华为官方旗舰店',
    skuPrefix: 'HW60',
    priceRange: [6199, 7299],
  },
  {
    brand: '小米',
    category: '手机数码',
    platform: '拼多多',
    productName: '小米 14 12GB+256GB 岩石青 徕卡影像',
    shopName: '小米品牌店',
    skuPrefix: 'MI14',
    priceRange: [3599, 4299],
  },
  {
    brand: '美的',
    category: '大家电',
    platform: '京东',
    productName: '美的 508L 十字对开门一级能效冰箱',
    shopName: '美的京东自营官方旗舰店',
    skuPrefix: 'MD508',
    priceRange: [3299, 4699],
  },
  {
    brand: '海尔',
    category: '大家电',
    platform: '天猫',
    productName: '海尔 10KG 直驱变频滚筒洗烘套装',
    shopName: '海尔官方旗舰店',
    skuPrefix: 'HE10',
    priceRange: [4199, 6999],
  },
  {
    brand: '戴森',
    category: '生活电器',
    platform: '京东',
    productName: 'Dyson V12 Detect Slim 无线吸尘器',
    shopName: '戴森京东自营旗舰店',
    skuPrefix: 'DY12',
    priceRange: [3199, 4599],
  },
  {
    brand: '苏泊尔',
    category: '厨房电器',
    platform: '拼多多',
    productName: '苏泊尔 5L IH 电压力锅 智能预约款',
    shopName: '苏泊尔品牌特卖店',
    skuPrefix: 'SP5L',
    priceRange: [299, 599],
  },
  {
    brand: '飞利浦',
    category: '个护健康',
    platform: '天猫',
    productName: '飞利浦 Sonicare 电动牙刷 HX68 系列',
    shopName: '飞利浦官方旗舰店',
    skuPrefix: 'PH68',
    priceRange: [359, 799],
  },
  {
    brand: '维达',
    category: '日用快消',
    platform: '拼多多',
    productName: '维达 抽纸 3 层 100 抽 24 包整箱',
    shopName: '维达百货专营店',
    skuPrefix: 'VD24',
    priceRange: [49, 89],
  },
  {
    brand: '蓝月亮',
    category: '日用快消',
    platform: '京东',
    productName: '蓝月亮 深层洁净洗衣液 3kg*2 促销装',
    shopName: '蓝月亮京东自营旗舰店',
    skuPrefix: 'LM32',
    priceRange: [79, 139],
  },
  {
    brand: '元气森林',
    category: '食品饮料',
    platform: '天猫',
    productName: '元气森林 气泡水 白桃味 480ml*15 瓶',
    shopName: '元气森林官方旗舰店',
    skuPrefix: 'YQ15',
    priceRange: [49, 79],
  },
  {
    brand: '安踏',
    category: '服饰鞋包',
    platform: '拼多多',
    productName: '安踏 男款缓震跑鞋 夏季透气轻便训练鞋',
    shopName: '安踏运动专卖店',
    skuPrefix: 'ATRS',
    priceRange: [169, 399],
  },
];

const platformMix = [
  { label: '京东', ratio: 0.47 },
  { label: '天猫', ratio: 0.31 },
  { label: '拼多多', ratio: 0.22 },
] as const;

function randomInt(min: number, max: number) {
  return faker.number.int({ max, min });
}

function randomFloat(min: number, max: number, fractionDigits = 1) {
  return faker.number.float({ fractionDigits, max, min });
}

function randomPrice(min: number, max: number) {
  return Number(faker.commerce.price({ max, min, dec: 2 }));
}

function formatTime(date: Date, withSeconds = false) {
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    hour12: false,
    minute: '2-digit',
    second: withSeconds ? '2-digit' : undefined,
  });
  return formatter.format(date);
}

function buildCaptureTimeline(now: Date) {
  const baseActive = randomInt(2600, 3600);
  const baseSuccess = randomFloat(95.4, 97.8);
  const pulseOffsets = [1180, 860, 420, 0, 360, 1280, 1710, 1420, 920, 680, 510, 760];
  const successOffsets = [0.9, 1.4, 0.8, 0.5, 0.4, 1.7, 1.9, 1.5, -0.1, -0.5, -0.3, 0.6];

  return Array.from({ length: 12 }).map((_, index) => {
    const timestamp = new Date(now.getTime() - (11 - index) * 5 * 60 * 1000);
    return {
      active_sku_count: baseActive + pulseOffsets[index]!,
      success_rate: Number((baseSuccess + successOffsets[index]!).toFixed(1)),
      timestamp: formatTime(timestamp),
    };
  });
}

function buildAlertItems(now: Date) {
  return productCatalog
    .map((item, index) => {
      const previousPrice = randomPrice(item.priceRange[0], item.priceRange[1]);
      const dropBand =
        item.category === '日用快消' || item.category === '食品饮料'
          ? [7.2, 13.8]
          : item.category === '手机数码' || item.category === '大家电'
            ? [8.5, 19.6]
            : [6.5, 15.2];
      const dropPercent = Number(randomFloat(dropBand[0], dropBand[1]).toFixed(1));
      const currentPrice = Number((previousPrice * (1 - dropPercent / 100)).toFixed(2));

      return {
        current_price: currentPrice,
        detected_at: formatTime(new Date(now.getTime() - index * 6 * 60 * 1000), true),
        drop_percent: dropPercent,
        platform: item.platform,
        previous_price: previousPrice,
        product_name: item.productName,
        sku_id: `${item.skuPrefix}${faker.string.numeric(8)}`,
      };
    })
    .sort((a, b) => b.drop_percent - a.drop_percent)
    .slice(0, 10);
}

export default eventHandler(() => {
  const now = new Date();
  const totalSkuCount = randomInt(132_000, 168_000);
  const totalPriceRecords = totalSkuCount * randomInt(34, 48);
  const captureTimeline = buildCaptureTimeline(now);
  const latestCapture = captureTimeline.at(-1)!;
  const successRate = latestCapture.success_rate;
  const activeSkuCount = latestCapture.active_sku_count;
  const alertItems = buildAlertItems(now);

  const jdCount = Math.round(totalSkuCount * platformMix[0].ratio);
  const tmallCount = Math.round(totalSkuCount * platformMix[1].ratio);
  const pddCount = totalSkuCount - jdCount - tmallCount;

  return useResponseSuccess({
    active_sku_count: activeSkuCount,
    alert_items: alertItems,
    capture_timeline: captureTimeline,
    platform_breakdown: [
      {
        platform: '京东',
        sku_count: jdCount,
      },
      {
        platform: '天猫',
        sku_count: tmallCount,
      },
      {
        platform: '拼多多',
        sku_count: pddCount,
      },
    ],
    success_rate: successRate,
    total_price_records: totalPriceRecords,
    total_sku_count: totalSkuCount,
  });
});
