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

export interface PriceTimeSeriesQuery {
  keyword?: string;
  page?: number;
  pageSize?: number;
  platform?: string;
  status?: number;
}

export interface PriceTimeSeriesSummary {
  activePromotionCount: number;
  avgDiscountRate: number;
  lowestPriceSkuCount: number;
  totalSkuCount: number;
  totalSnapshotCount: number;
}

export interface PriceTimeSeriesListItem {
  averagePrice: number;
  brandName?: null | string;
  captureCount: number;
  currentPrice: number;
  id: number;
  latestCaptureAt: string;
  lowestPrice: number;
  highestPrice: number;
  mainImageUrl?: null | string;
  platform: string;
  productName: string;
  recentPromoText?: null | string;
  shopName?: null | string;
  skuId: string;
  status: number;
}

export interface PriceTimeSeriesListResponse {
  items: PriceTimeSeriesListItem[];
  page: number;
  pageSize: number;
  summary: PriceTimeSeriesSummary;
  total: number;
}

export interface PriceSnapshot {
  capturedAt: string;
  finalPrice: number;
  isHistoricalLow: boolean;
  listPrice: number;
  promoText?: null | string;
}

export interface PromotionRecord {
  couponAmount: number;
  capturedAt: string;
  finalPrice: number;
  formula: string;
  listPrice: number;
  otherDiscountAmount: number;
  promoText?: null | string;
  reductionAmount: number;
}

export interface PriceExtremes {
  averagePrice: number;
  currentPrice: number;
  highestPrice: number;
  highestPriceAt: string;
  lowestPrice: number;
  lowestPriceAt: string;
  priceSpan: number;
}

export interface PriceTimeSeriesDetail {
  priceExtremes: PriceExtremes;
  product: PriceTimeSeriesListItem;
  promotionRecords: PromotionRecord[];
  timeline: PriceSnapshot[];
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

interface PriceTimeSeriesSummaryDto {
  active_promotion_count: number;
  avg_discount_rate: number;
  lowest_price_sku_count: number;
  total_sku_count: number;
  total_snapshot_count: number;
}

interface PriceTimeSeriesListItemDto {
  average_price: number;
  brand_name?: null | string;
  capture_count: number;
  current_price: number;
  highest_price: number;
  id: number;
  latest_capture_at: string;
  lowest_price: number;
  main_image_url?: null | string;
  platform: string;
  product_name: string;
  recent_promo_text?: null | string;
  shop_name?: null | string;
  sku_id: string;
  status: number;
}

interface PriceTimeSeriesListResponseDto {
  items: PriceTimeSeriesListItemDto[];
  page: number;
  page_size: number;
  summary: PriceTimeSeriesSummaryDto;
  total: number;
}

interface PriceSnapshotDto {
  captured_at: string;
  final_price: number;
  is_historical_low: boolean;
  list_price: number;
  promo_text?: null | string;
}

interface PromotionRecordDto {
  captured_at: string;
  coupon_amount: number;
  final_price: number;
  formula: string;
  list_price: number;
  other_discount_amount: number;
  promo_text?: null | string;
  reduction_amount: number;
}

interface PriceExtremesDto {
  average_price: number;
  current_price: number;
  highest_price: number;
  highest_price_at: string;
  lowest_price: number;
  lowest_price_at: string;
  price_span: number;
}

interface PriceTimeSeriesDetailDto {
  price_extremes: PriceExtremesDto;
  product: PriceTimeSeriesListItemDto;
  promotion_records: PromotionRecordDto[];
  timeline: PriceSnapshotDto[];
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

function mapPriceSummary(summary: PriceTimeSeriesSummaryDto): PriceTimeSeriesSummary {
  return {
    activePromotionCount: summary.active_promotion_count,
    avgDiscountRate: summary.avg_discount_rate,
    lowestPriceSkuCount: summary.lowest_price_sku_count,
    totalSkuCount: summary.total_sku_count,
    totalSnapshotCount: summary.total_snapshot_count,
  };
}

function mapPriceListItem(item: PriceTimeSeriesListItemDto): PriceTimeSeriesListItem {
  return {
    averagePrice: item.average_price,
    brandName: item.brand_name,
    captureCount: item.capture_count,
    currentPrice: item.current_price,
    highestPrice: item.highest_price,
    id: item.id,
    latestCaptureAt: item.latest_capture_at,
    lowestPrice: item.lowest_price,
    mainImageUrl: item.main_image_url,
    platform: item.platform,
    productName: item.product_name,
    recentPromoText: item.recent_promo_text,
    shopName: item.shop_name,
    skuId: item.sku_id,
    status: item.status,
  };
}

function mapPriceSnapshot(snapshot: PriceSnapshotDto): PriceSnapshot {
  return {
    capturedAt: snapshot.captured_at,
    finalPrice: snapshot.final_price,
    isHistoricalLow: snapshot.is_historical_low,
    listPrice: snapshot.list_price,
    promoText: snapshot.promo_text,
  };
}

function mapPromotionRecord(record: PromotionRecordDto): PromotionRecord {
  return {
    capturedAt: record.captured_at,
    couponAmount: record.coupon_amount,
    finalPrice: record.final_price,
    formula: record.formula,
    listPrice: record.list_price,
    otherDiscountAmount: record.other_discount_amount,
    promoText: record.promo_text,
    reductionAmount: record.reduction_amount,
  };
}

function mapPriceExtremes(extremes: PriceExtremesDto): PriceExtremes {
  return {
    averagePrice: extremes.average_price,
    currentPrice: extremes.current_price,
    highestPrice: extremes.highest_price,
    highestPriceAt: extremes.highest_price_at,
    lowestPrice: extremes.lowest_price,
    lowestPriceAt: extremes.lowest_price_at,
    priceSpan: extremes.price_span,
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

export async function getPriceTimeSeriesListApi(params: PriceTimeSeriesQuery) {
  const data = await requestClient.get<PriceTimeSeriesListResponseDto>(
    '/sku-repository/price-time-series',
    {
      params,
    },
  );

  return {
    items: data.items.map(mapPriceListItem),
    page: data.page,
    pageSize: data.page_size,
    summary: mapPriceSummary(data.summary),
    total: data.total,
  } satisfies PriceTimeSeriesListResponse;
}

export async function getPriceTimeSeriesDetailApi(productId: number) {
  const data = await requestClient.get<PriceTimeSeriesDetailDto>(
    `/sku-repository/price-time-series/${productId}`,
  );

  return {
    priceExtremes: mapPriceExtremes(data.price_extremes),
    product: mapPriceListItem(data.product),
    promotionRecords: data.promotion_records.map(mapPromotionRecord),
    timeline: data.timeline.map(mapPriceSnapshot),
  } satisfies PriceTimeSeriesDetail;
}
