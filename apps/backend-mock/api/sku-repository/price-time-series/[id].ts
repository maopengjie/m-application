import { eventHandler, getRouterParam } from 'h3';

import { useResponseSuccess } from '~/utils/response';
import {
  findMockPriceTimeline,
  findMockSkuProduct,
} from '~/utils/sku-repository-mock';

function roundValue(value: number) {
  return Math.round(value * 100) / 100;
}

export default eventHandler((event) => {
  const id = Number(getRouterParam(event, 'id'));
  const product = findMockSkuProduct(id);
  const timeline = findMockPriceTimeline(id);
  const finalPrices = timeline.map((item) => item.final_price);
  const lowest = timeline.reduce((prev, current) =>
    current.final_price < prev.final_price ? current : prev,
  );
  const highest = timeline.reduce((prev, current) =>
    current.final_price > prev.final_price ? current : prev,
  );
  const latest = timeline.at(-1) ?? timeline[0]!;

  return useResponseSuccess({
    price_extremes: {
      average_price: roundValue(
        finalPrices.reduce((sum, price) => sum + price, 0) / finalPrices.length,
      ),
      current_price: latest.final_price,
      highest_price: highest.final_price,
      highest_price_at: highest.captured_at,
      lowest_price: lowest.final_price,
      lowest_price_at: lowest.captured_at,
      price_span: roundValue(highest.final_price - lowest.final_price),
    },
    product: {
      average_price: roundValue(
        finalPrices.reduce((sum, price) => sum + price, 0) / finalPrices.length,
      ),
      brand_name: product.brand_name,
      capture_count: timeline.length,
      current_price: latest.final_price,
      highest_price: highest.final_price,
      id: product.id,
      latest_capture_at: latest.captured_at,
      lowest_price: lowest.final_price,
      main_image_url: product.main_image_url,
      platform: product.platform,
      product_name: product.normalized_name || product.product_name,
      recent_promo_text: latest.promo_text,
      shop_name: product.shop_name,
      sku_id: product.sku_id,
      status: product.status,
    },
    promotion_records: timeline
      .filter((item) => item.promo_text !== '日常价')
      .slice()
      .reverse(),
    timeline,
  });
});
