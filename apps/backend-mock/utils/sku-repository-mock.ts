import { faker } from '@faker-js/faker';

type PlatformCode = 'jd' | 'pdd' | 'tmall';

interface ProductSeed {
  attributes: Array<{
    attr_group?: string;
    attr_name: string;
    attr_unit?: string;
    attr_value: string;
  }>;
  brand_name: string;
  category_id_3: number;
  category_level_1: string;
  category_level_2: string;
  category_level_3: string;
  main_image_base: number;
  platform: PlatformCode;
  price_band: [number, number];
  product_name: string;
  product_url: string;
  shop_name: string;
  sku_prefix: string;
  tags: string[];
}

interface MockTag {
  id: number;
  tag_code: string;
  tag_name: string;
  tag_type: string;
  tag_value?: string;
}

export interface MockSkuProduct {
  attributes: Array<{
    attr_group?: string;
    attr_name: string;
    attr_unit?: string;
    attr_value: string;
    id: number;
  }>;
  brand_name: string;
  category_id_3: number;
  category_level_1: string;
  category_level_2: string;
  category_level_3: string;
  id: number;
  main_image_url: string;
  normalized_name: string;
  platform: PlatformCode;
  price: number;
  product_name: string;
  product_url: string;
  shop_name: string;
  sku_id: string;
  status: number;
  tags: MockTag[];
  updated_at: string;
}

export interface MockPriceSnapshot {
  captured_at: string;
  coupon_amount: number;
  final_price: number;
  formula: string;
  is_historical_low: boolean;
  list_price: number;
  other_discount_amount: number;
  promo_text: string;
  reduction_amount: number;
}

const tagRegistry: Record<string, MockTag> = {
  HIGH_PROFIT: {
    id: 3,
    tag_code: 'HIGH_PROFIT',
    tag_name: '高利润',
    tag_type: 'business',
    tag_value: '毛利率>30%',
  },
  HOT_SALE: {
    id: 4,
    tag_code: 'HOT_SALE',
    tag_name: '热销',
    tag_type: 'marketing',
    tag_value: '近7日销量上升',
  },
  JD_SELF_OPERATED: {
    id: 1,
    tag_code: 'JD_SELF_OPERATED',
    tag_name: '京东自营',
    tag_type: 'platform',
    tag_value: '自营',
  },
  NEW_ARRIVAL: {
    id: 5,
    tag_code: 'NEW_ARRIVAL',
    tag_name: '新品',
    tag_type: 'marketing',
    tag_value: '30天内上架',
  },
  TMALL_FLAGSHIP: {
    id: 2,
    tag_code: 'TMALL_FLAGSHIP',
    tag_name: '天猫旗舰店',
    tag_type: 'platform',
    tag_value: '旗舰店',
  },
};

const productSeeds: ProductSeed[] = [
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: 'Apple' },
      { attr_group: '主体', attr_name: '机身颜色', attr_value: '黑色' },
      { attr_group: '存储', attr_name: '存储容量', attr_unit: 'GB', attr_value: '128' },
      { attr_group: '网络', attr_name: '网络制式', attr_value: '5G全网通' },
    ],
    brand_name: 'Apple',
    category_id_3: 100101,
    category_level_1: '手机通讯',
    category_level_2: '手机',
    category_level_3: '智能手机',
    main_image_base: 31,
    platform: 'jd',
    price_band: [4599, 5999],
    product_name: 'Apple iPhone 15 128GB 黑色 国行 5G',
    product_url: 'https://item.jd.com/100012345678.html',
    shop_name: 'Apple 产品京东自营旗舰店',
    sku_prefix: 'IP15',
    tags: ['JD_SELF_OPERATED', 'HOT_SALE'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '华为' },
      { attr_group: '主体', attr_name: '机身颜色', attr_value: '雅丹黑' },
      { attr_group: '存储', attr_name: '运行内存', attr_unit: 'GB', attr_value: '12' },
      { attr_group: '存储', attr_name: '机身存储', attr_unit: 'GB', attr_value: '512' },
    ],
    brand_name: '华为',
    category_id_3: 100102,
    category_level_1: '手机通讯',
    category_level_2: '手机',
    category_level_3: '智能手机',
    main_image_base: 32,
    platform: 'tmall',
    price_band: [6199, 7299],
    product_name: '华为 Mate 60 Pro 12GB+512GB 雅丹黑',
    product_url: 'https://detail.tmall.com/item.htm?id=100012345679',
    shop_name: '华为官方旗舰店',
    sku_prefix: 'HW60',
    tags: ['TMALL_FLAGSHIP', 'HOT_SALE'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '小米' },
      { attr_group: '主体', attr_name: '机身颜色', attr_value: '岩石青' },
      { attr_group: '存储', attr_name: '运行内存', attr_unit: 'GB', attr_value: '12' },
      { attr_group: '存储', attr_name: '机身存储', attr_unit: 'GB', attr_value: '256' },
    ],
    brand_name: '小米',
    category_id_3: 100103,
    category_level_1: '手机通讯',
    category_level_2: '手机',
    category_level_3: '智能手机',
    main_image_base: 33,
    platform: 'pdd',
    price_band: [3599, 4299],
    product_name: '小米 14 12GB+256GB 岩石青 徕卡影像',
    product_url: 'https://mobile.yangkeduo.com/goods.html?goods_id=100012345680',
    shop_name: '小米品牌店',
    sku_prefix: 'MI14',
    tags: ['HOT_SALE', 'NEW_ARRIVAL'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '美的' },
      { attr_group: '规格', attr_name: '总容积', attr_unit: 'L', attr_value: '508' },
      { attr_group: '规格', attr_name: '能效等级', attr_value: '一级能效' },
      { attr_group: '规格', attr_name: '门款式', attr_value: '十字对开门' },
    ],
    brand_name: '美的',
    category_id_3: 200101,
    category_level_1: '家用电器',
    category_level_2: '冰箱',
    category_level_3: '多门冰箱',
    main_image_base: 41,
    platform: 'jd',
    price_band: [3299, 4699],
    product_name: '美的 508L 十字对开门一级能效冰箱',
    product_url: 'https://item.jd.com/100012345681.html',
    shop_name: '美的京东自营官方旗舰店',
    sku_prefix: 'MD508',
    tags: ['JD_SELF_OPERATED', 'HIGH_PROFIT'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '海尔' },
      { attr_group: '规格', attr_name: '洗涤容量', attr_unit: 'KG', attr_value: '10' },
      { attr_group: '规格', attr_name: '电机类型', attr_value: '直驱变频' },
      { attr_group: '规格', attr_name: '套装类型', attr_value: '洗烘套装' },
    ],
    brand_name: '海尔',
    category_id_3: 200102,
    category_level_1: '家用电器',
    category_level_2: '洗衣机',
    category_level_3: '滚筒洗衣机',
    main_image_base: 42,
    platform: 'tmall',
    price_band: [4199, 6999],
    product_name: '海尔 10KG 直驱变频滚筒洗烘套装',
    product_url: 'https://detail.tmall.com/item.htm?id=100012345682',
    shop_name: '海尔官方旗舰店',
    sku_prefix: 'HE10',
    tags: ['TMALL_FLAGSHIP', 'HIGH_PROFIT'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: 'Dyson' },
      { attr_group: '规格', attr_name: '型号', attr_value: 'V12 Detect Slim' },
      { attr_group: '规格', attr_name: '续航时间', attr_unit: '分钟', attr_value: '60' },
      { attr_group: '规格', attr_name: '清洁类型', attr_value: '无线吸尘' },
    ],
    brand_name: '戴森',
    category_id_3: 200201,
    category_level_1: '家用电器',
    category_level_2: '生活电器',
    category_level_3: '吸尘器',
    main_image_base: 43,
    platform: 'jd',
    price_band: [3199, 4599],
    product_name: 'Dyson V12 Detect Slim 无线吸尘器',
    product_url: 'https://item.jd.com/100012345683.html',
    shop_name: '戴林京东自营旗舰店',
    sku_prefix: 'DY12',
    tags: ['JD_SELF_OPERATED', 'HOT_SALE'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '苏泊尔' },
      { attr_group: '规格', attr_name: '容量', attr_unit: 'L', attr_value: '5' },
      { attr_group: '规格', attr_name: '加热方式', attr_value: 'IH加热' },
      { attr_group: '功能', attr_name: '预约功能', attr_value: '支持' },
    ],
    brand_name: '苏泊尔',
    category_id_3: 200301,
    category_level_1: '家用电器',
    category_level_2: '厨房电器',
    category_level_3: '电压力锅',
    main_image_base: 44,
    platform: 'pdd',
    price_band: [299, 599],
    product_name: '苏泊尔 5L IH 电压力锅 智能预约款',
    product_url: 'https://mobile.yangkeduo.com/goods.html?goods_id=100012345684',
    shop_name: '苏泊尔品牌特卖店',
    sku_prefix: 'SP5L',
    tags: ['HIGH_PROFIT'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '飞利浦' },
      { attr_group: '规格', attr_name: '系列', attr_value: 'Sonicare HX68' },
      { attr_group: '规格', attr_name: '清洁模式', attr_value: '洁净/敏感/亮白' },
      { attr_group: '续航', attr_name: '续航时长', attr_unit: '天', attr_value: '14' },
    ],
    brand_name: '飞利浦',
    category_id_3: 300101,
    category_level_1: '个护健康',
    category_level_2: '口腔护理',
    category_level_3: '电动牙刷',
    main_image_base: 45,
    platform: 'tmall',
    price_band: [359, 799],
    product_name: '飞利浦 Sonicare 电动牙刷 HX68 系列',
    product_url: 'https://detail.tmall.com/item.htm?id=100012345685',
    shop_name: '飞利浦官方旗舰店',
    sku_prefix: 'PH68',
    tags: ['TMALL_FLAGSHIP', 'NEW_ARRIVAL'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '维达' },
      { attr_group: '包装', attr_name: '层数', attr_value: '3层' },
      { attr_group: '包装', attr_name: '单包抽数', attr_value: '100抽' },
      { attr_group: '包装', attr_name: '整箱规格', attr_value: '24包' },
    ],
    brand_name: '维达',
    category_id_3: 400101,
    category_level_1: '家居家装',
    category_level_2: '生活日用',
    category_level_3: '抽纸',
    main_image_base: 46,
    platform: 'pdd',
    price_band: [49, 89],
    product_name: '维达 抽纸 3 层 100 抽 24 包整箱',
    product_url: 'https://mobile.yangkeduo.com/goods.html?goods_id=100012345686',
    shop_name: '维达百货专营店',
    sku_prefix: 'VD24',
    tags: ['HOT_SALE'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '蓝月亮' },
      { attr_group: '规格', attr_name: '单桶净含量', attr_unit: 'kg', attr_value: '3' },
      { attr_group: '规格', attr_name: '组合规格', attr_value: '3kg*2' },
      { attr_group: '功能', attr_name: '适用场景', attr_value: '机洗/手洗通用' },
    ],
    brand_name: '蓝月亮',
    category_id_3: 400102,
    category_level_1: '家居家装',
    category_level_2: '家庭清洁',
    category_level_3: '洗衣液',
    main_image_base: 47,
    platform: 'jd',
    price_band: [79, 139],
    product_name: '蓝月亮 深层洁净洗衣液 3kg*2 促销装',
    product_url: 'https://item.jd.com/100012345687.html',
    shop_name: '蓝月亮京东自营旗舰店',
    sku_prefix: 'LM32',
    tags: ['JD_SELF_OPERATED', 'HOT_SALE'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '元气森林' },
      { attr_group: '包装', attr_name: '口味', attr_value: '白桃味' },
      { attr_group: '包装', attr_name: '单瓶容量', attr_unit: 'ml', attr_value: '480' },
      { attr_group: '包装', attr_name: '整箱数量', attr_value: '15瓶' },
    ],
    brand_name: '元气森林',
    category_id_3: 500101,
    category_level_1: '食品饮料',
    category_level_2: '饮料冲调',
    category_level_3: '气泡水',
    main_image_base: 48,
    platform: 'tmall',
    price_band: [49, 79],
    product_name: '元气森林 气泡水 白桃味 480ml*15 瓶',
    product_url: 'https://detail.tmall.com/item.htm?id=100012345688',
    shop_name: '元气森林官方旗舰店',
    sku_prefix: 'YQ15',
    tags: ['TMALL_FLAGSHIP', 'HOT_SALE'],
  },
  {
    attributes: [
      { attr_group: '主体', attr_name: '品牌', attr_value: '安踏' },
      { attr_group: '规格', attr_name: '鞋面材质', attr_value: '织物+TPU' },
      { attr_group: '规格', attr_name: '适用场景', attr_value: '日常跑步/训练' },
      { attr_group: '规格', attr_name: '鞋底科技', attr_value: '缓震中底' },
    ],
    brand_name: '安踏',
    category_id_3: 600101,
    category_level_1: '服饰鞋包',
    category_level_2: '运动鞋',
    category_level_3: '跑步鞋',
    main_image_base: 49,
    platform: 'pdd',
    price_band: [169, 399],
    product_name: '安踏 男款缓震跑鞋 夏季透气轻便训练鞋',
    product_url: 'https://mobile.yangkeduo.com/goods.html?goods_id=100012345689',
    shop_name: '安踏运动专卖店',
    sku_prefix: 'ATRS',
    tags: ['NEW_ARRIVAL'],
  },
];

function formatDate(date: Date) {
  return date.toISOString().replace('T', ' ').split('.')[0]!;
}

function buildTagList(tagCodes: string[]) {
  return tagCodes.map((tagCode) => tagRegistry[tagCode]!).filter(Boolean);
}

function buildVariantStatus(index: number) {
  if (index % 9 === 0) return 0;
  if (index % 17 === 0) return -1;
  return 1;
}

function buildNormalizedName(name: string) {
  return name.replaceAll(' ', '');
}

export const mockSkuProducts: MockSkuProduct[] = Array.from({ length: 48 }).map((_, index) => {
  const seed = productSeeds[index % productSeeds.length]!;
  const variantIndex = Math.floor(index / productSeeds.length) + 1;
  const price = Number(
    faker.commerce.price({
      dec: 2,
      max: seed.price_band[1],
      min: seed.price_band[0],
    }),
  );
  const extraTag = index % 5 === 0 ? ['HIGH_PROFIT'] : [];
  const tags = Array.from(new Set([...seed.tags, ...extraTag]));
  const updatedAt = new Date(Date.now() - index * 3 * 60 * 60 * 1000);

  return {
    attributes: seed.attributes.map((attribute, attrIndex) => ({
      ...attribute,
      id: index * 10 + attrIndex + 1,
    })),
    brand_name: seed.brand_name,
    category_id_3: seed.category_id_3,
    category_level_1: seed.category_level_1,
    category_level_2: seed.category_level_2,
    category_level_3: seed.category_level_3,
    id: index + 1,
    main_image_url: `https://picsum.photos/id/${seed.main_image_base + variantIndex}/200/200`,
    normalized_name: buildNormalizedName(seed.product_name),
    platform: seed.platform,
    price,
    product_name:
      variantIndex === 1 ? seed.product_name : `${seed.product_name} ${variantIndex}期促销款`,
    product_url: seed.product_url,
    shop_name: seed.shop_name,
    sku_id: `${seed.sku_prefix}${String(index + 1).padStart(8, '0')}`,
    status: buildVariantStatus(index + 1),
    tags: buildTagList(tags),
    updated_at: formatDate(updatedAt),
  };
});

export function findMockSkuProduct(productId: number) {
  return mockSkuProducts.find((item) => item.id === productId) ?? mockSkuProducts[0]!;
}

function roundPrice(value: number) {
  return Math.round(value * 100) / 100;
}

function buildPromotionText(
  reductionAmount: number,
  couponAmount: number,
  otherDiscountAmount: number,
) {
  const chunks: string[] = [];
  if (reductionAmount > 0) {
    chunks.push(`满减 -${reductionAmount}`);
  }
  if (couponAmount > 0) {
    chunks.push(`券 -${couponAmount}`);
  }
  if (otherDiscountAmount > 0) {
    chunks.push(`平台补贴 -${otherDiscountAmount}`);
  }
  return chunks.length > 0 ? chunks.join('，') : '日常价';
}

function buildFormula(
  capturedAt: string,
  listPrice: number,
  reductionAmount: number,
  couponAmount: number,
  otherDiscountAmount: number,
  finalPrice: number,
) {
  const segments = [`${capturedAt}`, `标价 ${listPrice}`];
  if (reductionAmount > 0) {
    segments.push(`满减 -${reductionAmount}`);
  }
  if (couponAmount > 0) {
    segments.push(`券 -${couponAmount}`);
  }
  if (otherDiscountAmount > 0) {
    segments.push(`补贴 -${otherDiscountAmount}`);
  }
  segments.push(`到手 ${finalPrice}`);
  return segments.join('，');
}

function buildPriceSnapshots(product: MockSkuProduct, index: number): MockPriceSnapshot[] {
  const snapshotCount = 12 + (index % 5);
  const baseDate = new Date('2026-04-18T10:00:00+08:00');
  const basePrice = product.price;

  return Array.from({ length: snapshotCount }).map((_, snapshotIndex) => {
    const capturedAt = new Date(baseDate.getTime() + snapshotIndex * 36 * 60 * 60 * 1000);
    const seasonalSwing = ((snapshotIndex % 4) - 1.5) * basePrice * 0.018;
    const trendAdjust = (snapshotCount - snapshotIndex) * basePrice * 0.004;
    const listPrice = roundPrice(Math.max(9.9, basePrice + seasonalSwing + trendAdjust));

    const reductionAmount =
      snapshotIndex % 3 === 0 ? roundPrice(Math.max(0, Math.round(listPrice * 0.06))) : 0;
    const couponAmount =
      snapshotIndex % 4 === 1 ? roundPrice(Math.max(0, Math.round(listPrice * 0.03))) : 0;
    const otherDiscountAmount =
      snapshotIndex % 5 === 2 ? roundPrice(Math.max(0, Math.round(listPrice * 0.02))) : 0;
    const finalPrice = roundPrice(
      Math.max(1, listPrice - reductionAmount - couponAmount - otherDiscountAmount),
    );
    const timestamp = formatDate(capturedAt);
    const promoText = buildPromotionText(
      reductionAmount,
      couponAmount,
      otherDiscountAmount,
    );

    return {
      captured_at: timestamp,
      coupon_amount: couponAmount,
      final_price: finalPrice,
      formula: buildFormula(
        timestamp,
        listPrice,
        reductionAmount,
        couponAmount,
        otherDiscountAmount,
        finalPrice,
      ),
      is_historical_low: false,
      list_price: listPrice,
      other_discount_amount: otherDiscountAmount,
      promo_text: promoText,
      reduction_amount: reductionAmount,
    };
  });
}

export const mockPriceTimeSeriesByProductId: Record<number, MockPriceSnapshot[]> = Object.fromEntries(
  mockSkuProducts.map((product, index) => {
    const snapshots = buildPriceSnapshots(product, index);
    const lowestPrice = Math.min(...snapshots.map((item) => item.final_price));
    return [
      product.id,
      snapshots.map((item) => ({
        ...item,
        is_historical_low: item.final_price === lowestPrice,
      })),
    ];
  }),
);

export function findMockPriceTimeline(productId: number) {
  return mockPriceTimeSeriesByProductId[productId] ?? mockPriceTimeSeriesByProductId[1] ?? [];
}
