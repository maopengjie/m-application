import { requestClient } from '#/api/request';

export interface SkuTag {
  id: number;
  tagCode: string;
  tagName: string;
  tagType: string;
  sourceType?: string | null;
  tagValue?: string | null;
}

export interface SkuAttribute {
  id: number;
  attrGroup?: null | string;
  attrName: string;
  attrUnit?: null | string;
  attrValue: string;
}

export interface SkuProductListItem {
  id: number;
  platform: string;
  skuId: string;
  productName: string;
  normalizedName?: null | string;
  brandName?: null | string;
  mainImageUrl?: null | string;
  categoryLevel1?: null | string;
  categoryLevel2?: null | string;
  categoryLevel3?: null | string;
  shopName?: null | string;
  status: number;
  updatedAt: string;
  tags: SkuTag[];
}

export interface SkuProductDetail extends SkuProductListItem {
  categoryId3?: null | number;
  productUrl?: null | string;
  attributes: SkuAttribute[];
}

export interface SkuProductListResponse {
  items: SkuProductListItem[];
  total: number;
  page: number;
  pageSize: number;
}

export interface SkuProductQuery {
  brandName?: string;
  keyword?: string;
  page?: number;
  pageSize?: number;
  platform?: string;
  status?: number;
  tagCode?: string;
}

interface SkuTagDto {
  id: number;
  source_type?: null | string;
  tag_code: string;
  tag_name: string;
  tag_type: string;
  tag_value?: null | string;
}

interface SkuAttributeDto {
  attr_group?: null | string;
  attr_name: string;
  attr_unit?: null | string;
  attr_value: string;
  id: number;
}

interface SkuProductDto {
  brand_name?: null | string;
  category_id_3?: null | number;
  category_level_1?: null | string;
  category_level_2?: null | string;
  category_level_3?: null | string;
  id: number;
  main_image_url?: null | string;
  normalized_name?: null | string;
  platform: string;
  product_name: string;
  product_url?: null | string;
  shop_name?: null | string;
  sku_id: string;
  status: number;
  tags: SkuTagDto[];
  updated_at: string;
  attributes?: SkuAttributeDto[];
}

interface SkuProductListResponseDto {
  items: SkuProductDto[];
  page: number;
  page_size: number;
  total: number;
}

function mapTag(tag: SkuTagDto): SkuTag {
  return {
    id: tag.id,
    sourceType: tag.source_type,
    tagCode: tag.tag_code,
    tagName: tag.tag_name,
    tagType: tag.tag_type,
    tagValue: tag.tag_value,
  };
}

function mapAttribute(attribute: SkuAttributeDto): SkuAttribute {
  return {
    attrGroup: attribute.attr_group,
    attrName: attribute.attr_name,
    attrUnit: attribute.attr_unit,
    attrValue: attribute.attr_value,
    id: attribute.id,
  };
}

function mapProduct(product: SkuProductDto): SkuProductListItem {
  return {
    id: product.id,
    skuId: product.sku_id,
    platform: product.platform,
    productName: product.product_name,
    normalizedName: product.normalized_name,
    brandName: product.brand_name,
    mainImageUrl: product.main_image_url,
    categoryLevel1: product.category_level_1,
    categoryLevel2: product.category_level_2,
    categoryLevel3: product.category_level_3,
    shopName: product.shop_name,
    status: product.status,
    updatedAt: product.updated_at,
    tags: product.tags.map(mapTag),
  };
}

export async function getSkuProductsApi(params: SkuProductQuery) {
  const data = await requestClient.get<SkuProductListResponseDto>(
    '/sku-repository/products',
    {
      params,
    },
  );
  return {
    items: data.items.map(mapProduct),
    page: data.page,
    pageSize: data.page_size,
    total: data.total,
  } satisfies SkuProductListResponse;
}

export async function getSkuProductDetailApi(productId: number) {
  const data = await requestClient.get<SkuProductDto>(`/sku-repository/products/${productId}`);
  return {
    ...mapProduct(data),
    categoryId3: data.category_id_3,
    productUrl: data.product_url,
    attributes: (data.attributes ?? []).map(mapAttribute),
  } satisfies SkuProductDetail;
}

export async function getSkuTagsApi() {
  const data = await requestClient.get<SkuTagDto[]>('/sku-repository/tags');
  return data.map(mapTag);
}
