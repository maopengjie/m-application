import { faker } from '@faker-js/faker';
import { eventHandler, getQuery } from 'h3';
import { usePageResponseSuccess } from '~/utils/response';

function generateMockProducts(count: number) {
  const products = [];
  const platforms = ['jd', 'tmall', 'pdd'];
  const categories = [
    ['家用电器', '冰箱', '三门冰箱'],
    ['家用电器', '洗衣机', '滚筒洗衣机'],
    ['手机通讯', '手机', '智能手机'],
    ['电脑办公', '电脑整机', '笔记本'],
  ];

  for (let i = 0; i < count; i++) {
    const platform = faker.helpers.arrayElement(platforms);
    const cat = faker.helpers.arrayElement(categories);
    const tags = [
      {
        id: 1,
        tag_code: 'JD_SELF_OPERATED',
        tag_name: '京东自营',
        tag_type: 'platform',
      },
    ];

    products.push({
      id: i + 1,
      sku_id: faker.string.numeric(12),
      platform,
      product_name: faker.commerce.productName(),
      normalized_name: faker.commerce.productName(),
      brand_name: faker.company.name(),
      main_image_url: `https://picsum.photos/id/${i + 10}/200/200`,
      category_level_1: cat[0],
      category_level_2: cat[1],
      category_level_3: cat[2],
      shop_name: faker.company.name() + '官方旗舰店',
      status: faker.helpers.arrayElement([1, 0, -1]),
      updated_at: faker.date.recent().toISOString().replace('T', ' ').split('.')[0],
      tags: faker.datatype.boolean() ? tags : [],
    });
  }
  return products;
}

const allProducts = generateMockProducts(50);

export default eventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page || 1);
  const pageSize = Number(query.pageSize || 10);

  // Simple filtering
  let filtered = allProducts;
  if (query.keyword) {
    const k = String(query.keyword).toLowerCase();
    filtered = filtered.filter(p => 
      p.product_name.toLowerCase().includes(k) || 
      p.sku_id.includes(k)
    );
  }
  if (query.platform) {
    filtered = filtered.filter(p => p.platform === query.platform);
  }

  // We need to return the structure expected by SkuProductListResponseDto
  // items, page, page_size, total
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
