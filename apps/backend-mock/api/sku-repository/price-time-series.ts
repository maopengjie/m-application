import { eventHandler, getQuery } from 'h3';

import { useResponseSuccess } from '~/utils/response';
import {
  findMockPriceTimeline,
  mockSkuProducts,
} from '~/utils/sku-repository-mock';

function roundValue(value: number) {
  return Math.round(value * 100) / 100;
}

function buildListItem(product: (typeof mockSkuProducts)[number]) {
  const timeline = findMockPriceTimeline(product.id);
  const finalPrices = timeline.map((item) => item.final_price);
  const latest = timeline.at(-1) ?? timeline[0]!;
  const averagePrice = roundValue(
    finalPrices.reduce((sum, price) => sum + price, 0) / finalPrices.length,
  );

  return {
    average_price: averagePrice,
    brand_name: product.brand_name,
    capture_count: timeline.length,
    current_price: latest.final_price,
    highest_price: Math.max(...finalPrices),
    id: product.id,
    latest_capture_at: latest.captured_at,
    lowest_price: Math.min(...finalPrices),
    main_image_url: product.main_image_url,
    platform: product.platform,
    product_name: product.normalized_name || product.product_name,
    recent_promo_text: latest.promo_text,
    shop_name: product.shop_name,
    sku_id: product.sku_id,
    status: product.status,
  };
}

export default eventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page || 1);
  const pageSize = Number(query.pageSize || 10);

  let filtered = mockSkuProducts;
  if (query.keyword) {
    const keyword = String(query.keyword).toLowerCase();
    filtered = filtered.filter((product) =>
      product.product_name.toLowerCase().includes(keyword) ||
      product.normalized_name.toLowerCase().includes(keyword) ||
      product.sku_id.toLowerCase().includes(keyword),
    );
  }
  if (query.platform) {
    filtered = filtered.filter((product) => product.platform === query.platform);
  }
  if (query.status !== undefined && query.status !== '') {
    filtered = filtered.filter((product) => product.status === Number(query.status));
  }

  const items = filtered.map(buildListItem);
  const snapshotCounts = items.map((item) => item.capture_count);
  const discountRates = filtered.flatMap((product) =>
    findMockPriceTimeline(product.id).map((item) =>
      item.list_price > 0
        ? ((item.list_price - item.final_price) / item.list_price) * 100
        : 0,
    ),
  );
  const summary = {
    active_promotion_count: filtered.flatMap((product) =>
      findMockPriceTimeline(product.id).filter((item) => item.promo_text !== '日常价'),
    ).length,
    avg_discount_rate:
      discountRates.length > 0
        ? roundValue(discountRates.reduce((sum, rate) => sum + rate, 0) / discountRates.length)
        : 0,
    lowest_price_sku_count: filtered.filter((product) => {
      const timeline = findMockPriceTimeline(product.id);
      const latest = timeline.at(-1) ?? timeline[0];
      return latest?.is_historical_low ?? false;
    }).length,
    total_sku_count: filtered.length,
    total_snapshot_count: snapshotCounts.reduce((sum, count) => sum + count, 0),
  };

  const offset = (page - 1) * pageSize;
  return useResponseSuccess({
    items: items.slice(offset, offset + pageSize),
    page,
    page_size: pageSize,
    summary,
    total: items.length,
  });
});
