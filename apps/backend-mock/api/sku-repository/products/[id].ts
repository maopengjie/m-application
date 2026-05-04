import { faker } from '@faker-js/faker';
import { eventHandler, getRouterParam } from 'h3';
import { useResponseSuccess } from '~/utils/response';

export default eventHandler((event) => {
  const id = getRouterParam(event, 'id');
  
  const product = {
    id: Number(id),
    sku_id: faker.string.numeric(12),
    platform: faker.helpers.arrayElement(['jd', 'tmall', 'pdd']),
    product_name: faker.commerce.productName(),
    normalized_name: faker.commerce.productName(),
    brand_name: faker.company.name(),
    main_image_url: `https://picsum.photos/id/${id}/200/200`,
    category_level_1: '家用电器',
    category_level_2: '冰箱',
    category_level_3: '三门冰箱',
    category_id_3: 1001,
    shop_name: faker.company.name() + '官方旗舰店',
    product_url: 'https://item.jd.com/100012345678.html',
    status: 1,
    updated_at: faker.date.recent().toISOString().replace('T', ' ').split('.')[0],
    tags: [
      {
        id: 1,
        tag_code: 'JD_SELF_OPERATED',
        tag_name: '京东自营',
        tag_type: 'platform',
        tag_value: '自营',
      },
    ],
    attributes: [
      { id: 1, attr_group: '主体', attr_name: '品牌', attr_value: '美的 (Midea)' },
      { id: 2, attr_group: '主体', attr_name: '型号', attr_value: 'BCD-215FT' },
      { id: 3, attr_group: '规格', attr_name: '总容积', attr_value: '215', attr_unit: 'L' },
      { id: 4, attr_group: '规格', attr_name: '能效等级', attr_value: '一级' },
    ],
  };

  return useResponseSuccess(product);
});
