import { eventHandler, getRouterParam } from 'h3';
import { useResponseSuccess } from '~/utils/response';
import { findMockSkuProduct } from '~/utils/sku-repository-mock';

export default eventHandler((event) => {
  const id = getRouterParam(event, 'id');
  const product = findMockSkuProduct(Number(id));

  return useResponseSuccess(product);
});
