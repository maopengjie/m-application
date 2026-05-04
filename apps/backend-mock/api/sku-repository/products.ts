import { eventHandler, getQuery } from 'h3';
import { mockSkuProducts } from '~/utils/sku-repository-mock';

export default eventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page || 1);
  const pageSize = Number(query.pageSize || 10);

  let filtered = mockSkuProducts;
  if (query.keyword) {
    const k = String(query.keyword).toLowerCase();
    filtered = filtered.filter((p) =>
      p.product_name.toLowerCase().includes(k) ||
      p.sku_id.toLowerCase().includes(k) ||
      p.brand_name.toLowerCase().includes(k),
    );
  }
  if (query.platform) {
    filtered = filtered.filter((p) => p.platform === query.platform);
  }
  if (query.brandName) {
    const brandName = String(query.brandName).toLowerCase();
    filtered = filtered.filter((p) => p.brand_name.toLowerCase().includes(brandName));
  }
  if (query.status !== undefined && query.status !== '') {
    filtered = filtered.filter((p) => p.status === Number(query.status));
  }
  if (query.tagCode) {
    const tagCode = String(query.tagCode);
    filtered = filtered.filter((p) => p.tags.some((tag) => tag.tag_code === tagCode));
  }

  const offset = (page - 1) * pageSize;
  const items = filtered.slice(offset, offset + pageSize);

  return {
    code: 0,
    data: {
      items,
      total: filtered.length,
      page,
      page_size: pageSize,
    },
    message: 'ok',
  };
});
