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
  categoryId?: number;
  categoryLevel?: number;
}

export interface SkuTagUpsertPayload {
  tagCode: string;
  tagName?: string;
  tagValue?: string;
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
  anomalyReason?: null | string;
  capturedAt: string;
  finalPrice: number;
  isAnomalous: boolean;
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

export interface CategoryNode {
  id: number;
  platform: string;
  externalId?: string | null;
  name: string;
  level: number;
  parentId?: number | null;
  path?: string | null;
  sortOrder: number;
  children: CategoryNode[];
}

export interface CategoryImportNode {
  children?: CategoryImportNode[];
  externalId?: null | string;
  name: string;
  sortOrder?: number;
}

export interface CategoryTreeImportResponse {
  importedCount: number;
  platform: string;
}

export interface MappingRule {
  id: number;
  ruleType: string;
  platform?: string | null;
  categoryId?: number | null;
  pattern: string;
  unifiedLabel: string;
  isActive: number;
  priority: number;
  createdAt: string;
  updatedAt: string;
}

export interface MappingRuleListResponse {
  activeTotal: number;
  items: MappingRule[];
  total: number;
}

export interface SkuComparison {
  id: number;
  masterSkuId: number;
  linkedSkuId: number;
  matchReasons: string[];
  matchScore?: number | null;
  matchType: string;
  status: number;
  masterSku?: SkuProductListItem | null;
  linkedSku?: SkuProductListItem | null;
}

export interface ScrapeTaskRun {
  id: number;
  taskId?: null | string;
  taskName: string;
  triggerSource: string;
  platform?: null | string;
  requestedLimit?: null | number;
  requestedUrl?: null | string;
  status: string;
  processedCount: number;
  successCount: number;
  failureCount: number;
  startedAt?: null | string;
  finishedAt?: null | string;
  summaryMessage?: null | string;
  errorMessage?: null | string;
  failedItems: Array<Record<string, unknown>>;
  createdAt: string;
  updatedAt: string;
}

export interface ScrapeScheduleOverview {
  categorySyncEnabled: boolean;
  categorySyncHours: number;
  maintenanceIntervalMinutes: number;
  periodicScrapeEnabled: boolean;
  periodicScrapeIntervalMinutes: number;
  periodicScrapeLimit: number;
  periodicScrapePlatform?: null | string;
}

export interface ScrapeTaskOverview {
  latestProblemRun?: null | ScrapeTaskRun;
  latestRun?: null | ScrapeTaskRun;
  latestSuccessRun?: null | ScrapeTaskRun;
  openRunCount: number;
  schedule: ScrapeScheduleOverview;
  statusCounts: Record<string, number>;
  successRate: number;
  totalRuns: number;
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
  anomaly_reason?: null | string;
  captured_at: string;
  final_price: number;
  is_anomalous?: boolean;
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

interface CategoryNodeDto {
  children: CategoryNodeDto[];
  external_id?: null | string;
  id: number;
  level: number;
  name: string;
  parent_id?: null | number;
  path?: null | string;
  platform: string;
  sort_order: number;
}

interface MappingRuleDto {
  category_id?: null | number;
  created_at: string;
  id: number;
  is_active: number;
  pattern: string;
  platform?: null | string;
  priority: number;
  rule_type: string;
  unified_label: string;
  updated_at: string;
}

interface SkuComparisonDto {
  id: number;
  linked_sku?: null | SkuProductDto;
  linked_sku_id: number;
  match_reasons?: string[];
  master_sku?: null | SkuProductDto;
  master_sku_id: number;
  match_score?: null | number;
  match_type: string;
  status: number;
}

interface ScrapeTaskRunDto {
  created_at: string;
  error_message?: null | string;
  failed_items?: Array<Record<string, unknown>>;
  failure_count: number;
  finished_at?: null | string;
  id: number;
  platform?: null | string;
  processed_count: number;
  requested_limit?: null | number;
  requested_url?: null | string;
  started_at?: null | string;
  status: string;
  success_count: number;
  summary_message?: null | string;
  task_id?: null | string;
  task_name: string;
  trigger_source: string;
  updated_at: string;
}

interface ScrapeScheduleOverviewDto {
  category_sync_enabled: boolean;
  category_sync_hours: number;
  maintenance_interval_minutes: number;
  periodic_scrape_enabled: boolean;
  periodic_scrape_interval_minutes: number;
  periodic_scrape_limit: number;
  periodic_scrape_platform?: null | string;
}

interface ScrapeTaskOverviewDto {
  latest_problem_run?: null | ScrapeTaskRunDto;
  latest_run?: null | ScrapeTaskRunDto;
  latest_success_run?: null | ScrapeTaskRunDto;
  open_run_count: number;
  schedule: ScrapeScheduleOverviewDto;
  status_counts: Record<string, number>;
  success_rate: number;
  total_runs: number;
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
    anomalyReason: snapshot.anomaly_reason,
    capturedAt: snapshot.captured_at,
    finalPrice: snapshot.final_price,
    isAnomalous: Boolean(snapshot.is_anomalous),
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

function mapCategoryNode(node: CategoryNodeDto): CategoryNode {
  return {
    children: (node.children ?? []).map(mapCategoryNode),
    externalId: node.external_id,
    id: node.id,
    level: node.level,
    name: node.name,
    parentId: node.parent_id,
    path: node.path,
    platform: node.platform,
    sortOrder: node.sort_order,
  };
}

function mapMappingRule(rule: MappingRuleDto): MappingRule {
  return {
    categoryId: rule.category_id,
    createdAt: rule.created_at,
    id: rule.id,
    isActive: rule.is_active,
    pattern: rule.pattern,
    platform: rule.platform,
    priority: rule.priority,
    ruleType: rule.rule_type,
    unifiedLabel: rule.unified_label,
    updatedAt: rule.updated_at,
  };
}

function mapSkuComparison(c: SkuComparisonDto): SkuComparison {
  return {
    id: c.id,
    linkedSku: c.linked_sku ? mapProduct(c.linked_sku) : null,
    linkedSkuId: c.linked_sku_id,
    matchReasons: c.match_reasons ?? [],
    masterSku: c.master_sku ? mapProduct(c.master_sku) : null,
    masterSkuId: c.master_sku_id,
    matchScore: c.match_score,
    matchType: c.match_type,
    status: c.status,
  };
}

function mapScrapeTaskRun(run: ScrapeTaskRunDto): ScrapeTaskRun {
  return {
    createdAt: run.created_at,
    errorMessage: run.error_message,
    failedItems: run.failed_items ?? [],
    failureCount: run.failure_count,
    finishedAt: run.finished_at,
    id: run.id,
    platform: run.platform,
    processedCount: run.processed_count,
    requestedLimit: run.requested_limit,
    requestedUrl: run.requested_url,
    startedAt: run.started_at,
    status: run.status,
    successCount: run.success_count,
    summaryMessage: run.summary_message,
    taskId: run.task_id,
    taskName: run.task_name,
    triggerSource: run.trigger_source,
    updatedAt: run.updated_at,
  };
}

function mapScrapeOverview(overview: ScrapeTaskOverviewDto): ScrapeTaskOverview {
  return {
    latestProblemRun: overview.latest_problem_run
      ? mapScrapeTaskRun(overview.latest_problem_run)
      : null,
    latestRun: overview.latest_run ? mapScrapeTaskRun(overview.latest_run) : null,
    latestSuccessRun: overview.latest_success_run
      ? mapScrapeTaskRun(overview.latest_success_run)
      : null,
    openRunCount: overview.open_run_count,
    schedule: {
      categorySyncEnabled: overview.schedule.category_sync_enabled,
      categorySyncHours: overview.schedule.category_sync_hours,
      maintenanceIntervalMinutes: overview.schedule.maintenance_interval_minutes,
      periodicScrapeEnabled: overview.schedule.periodic_scrape_enabled,
      periodicScrapeIntervalMinutes: overview.schedule.periodic_scrape_interval_minutes,
      periodicScrapeLimit: overview.schedule.periodic_scrape_limit,
      periodicScrapePlatform: overview.schedule.periodic_scrape_platform,
    },
    statusCounts: overview.status_counts,
    successRate: overview.success_rate,
    totalRuns: overview.total_runs,
  };
}

function buildMappingRulePayload(rule: Partial<MappingRule>) {
  return {
    category_id: rule.categoryId,
    is_active: rule.isActive,
    pattern: rule.pattern,
    platform: rule.platform,
    priority: rule.priority,
    rule_type: rule.ruleType,
    unified_label: rule.unifiedLabel,
  };
}

function unwrapMappingRulePayload(data: MappingRuleDto | { rule: MappingRuleDto }) {
  return 'rule' in data ? data.rule : data;
}

function buildCategoryImportNodePayload(node: CategoryImportNode): Record<string, unknown> {
  return {
    children: (node.children ?? []).map(buildCategoryImportNodePayload),
    external_id: node.externalId,
    name: node.name,
    sort_order: node.sortOrder ?? 0,
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

export async function addSkuProductTagApi(productId: number, payload: SkuTagUpsertPayload) {
  const data = await requestClient.post<SkuTagDto[]>(
    `/sku-repository/products/${productId}/tags`,
    {
      tag_code: payload.tagCode,
      tag_name: payload.tagName,
      tag_value: payload.tagValue,
    },
  );
  return data.map(mapTag);
}

export async function deleteSkuProductTagApi(productId: number, tagId: number) {
  const data = await requestClient.delete<SkuTagDto[]>(
    `/sku-repository/products/${productId}/tags/${tagId}`,
  );
  return data.map(mapTag);
}

export async function getScrapeTaskRunsApi(params?: {
  limit?: number;
  platform?: string;
  status?: string;
}) {
  const data = await requestClient.get<ScrapeTaskRunDto[]>(
    '/sku-repository/scraping/runs',
    {
      params,
    },
  );
  return data.map(mapScrapeTaskRun);
}

export async function getScrapeTaskOverviewApi() {
  const data = await requestClient.get<ScrapeTaskOverviewDto>(
    '/sku-repository/scraping/overview',
  );
  return mapScrapeOverview(data);
}

export async function getScrapeTaskRunDetailApi(runId: number) {
  const data = await requestClient.get<ScrapeTaskRunDto>(
    `/sku-repository/scraping/runs/${runId}`,
  );
  return mapScrapeTaskRun(data);
}

export async function retryScrapeTaskRunApi(runId: number) {
  const data = await requestClient.post<{
    previous_run_id: number;
    run: ScrapeTaskRunDto;
    task_id: string;
  }>(`/sku-repository/scraping/runs/${runId}/retry`);
  return {
    previousRunId: data.previous_run_id,
    run: mapScrapeTaskRun(data.run),
    taskId: data.task_id,
  };
}

export async function triggerScrapeProductApi(url: string) {
  const data = await requestClient.post<{
    run: ScrapeTaskRunDto;
    task_id: string;
    url: string;
  }>('/sku-repository/scraping/trigger', {
    url,
  });
  return {
    run: mapScrapeTaskRun(data.run),
    taskId: data.task_id,
    url: data.url,
  };
}

export async function triggerBatchScrapeApi(payload: {
  limit: number;
  platform?: string;
}) {
  const data = await requestClient.post<{
    limit: number;
    platform?: null | string;
    run: ScrapeTaskRunDto;
    task_id: string;
  }>('/sku-repository/scraping/batch', {
    limit: payload.limit,
    platform: payload.platform,
  });
  return {
    limit: data.limit,
    platform: data.platform,
    run: mapScrapeTaskRun(data.run),
    taskId: data.task_id,
  };
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

export async function getCategoryTreeApi(platform: string = 'jd') {
  const data = await requestClient.get<CategoryNodeDto[]>(
    '/sku-repository/category-tree',
    {
      params: { platform },
    },
  );
  return data.map(mapCategoryNode);
}

export async function importCategoryTreeApi(payload: {
  nodes: CategoryImportNode[];
  platform?: string;
}) {
  const data = await requestClient.post<{
    imported_count: number;
    platform: string;
  }>('/sku-repository/category-tree/import', {
    nodes: payload.nodes.map(buildCategoryImportNodePayload),
    platform: payload.platform ?? 'jd',
  });
  return {
    importedCount: data.imported_count,
    platform: data.platform,
  } satisfies CategoryTreeImportResponse;
}

export async function syncJdCategoryTreeApi() {
  const data = await requestClient.post<{
    run: ScrapeTaskRunDto;
    task_id: string;
  }>('/sku-repository/category-tree/sync');
  return {
    run: mapScrapeTaskRun(data.run),
    taskId: data.task_id,
  };
}

export async function getMappingRulesApi(params: {
  keyword?: string;
  page?: number;
  pageSize?: number;
  platform?: string;
}) {
  const data = await requestClient.get<{
    active_total?: number;
    items: MappingRuleDto[];
    total: number;
  }>('/sku-repository/mapping-rules', {
    params,
  });
  return {
    activeTotal: data.active_total ?? 0,
    items: data.items.map(mapMappingRule),
    total: data.total,
  } satisfies MappingRuleListResponse;
}

export async function createMappingRuleApi(rule: Partial<MappingRule>) {
  const data = await requestClient.post<MappingRuleDto | { rule: MappingRuleDto }>(
    '/sku-repository/mapping-rules',
    buildMappingRulePayload(rule),
  );
  return mapMappingRule(unwrapMappingRulePayload(data));
}

export async function updateMappingRuleApi(ruleId: number, rule: Partial<MappingRule>) {
  const data = await requestClient.put<MappingRuleDto | { rule: MappingRuleDto }>(
    `/sku-repository/mapping-rules/${ruleId}`,
    buildMappingRulePayload(rule),
  );
  return mapMappingRule(unwrapMappingRulePayload(data));
}

export async function toggleMappingRuleStatusApi(ruleId: number, isActive: number) {
  const data = await requestClient.request<MappingRuleDto | { rule: MappingRuleDto }>(
    `/sku-repository/mapping-rules/${ruleId}/status`,
    {
      method: 'PATCH',
      params: {
        is_active: isActive,
      },
    },
  );
  return mapMappingRule(unwrapMappingRulePayload(data));
}

export async function deleteMappingRuleApi(ruleId: number) {
  return requestClient.delete<{ deleted_id: number }>(
    `/sku-repository/mapping-rules/${ruleId}`,
  );
}

export async function getSkuComparisonsApi(params: {
  page?: number;
  pageSize?: number;
}) {
  const data = await requestClient.get<{
    items: SkuComparisonDto[];
    total: number;
  }>('/sku-repository/sku-comparisons', {
    params,
  });
  return {
    items: data.items.map(mapSkuComparison),
    total: data.total,
  };
}

export async function batchApplyMappingRulesApi() {
  const data = await requestClient.post<{
    updated_count: number;
  }>('/sku-repository/mapping-rules/apply');
  return {
    updatedCount: data.updated_count,
  };
}

export async function triggerAutoMatchApi() {
  const data = await requestClient.post<{
    matched_count: number;
  }>('/sku-repository/sku-comparisons/auto-match');
  return {
    matchedCount: data.matched_count,
  };
}

export async function reviewSkuComparisonApi(comparisonId: number, approved: boolean) {
  return requestClient.request<{
    approved: boolean;
    comparison_id: number;
    status: number;
  }>(
    `/sku-repository/sku-comparisons/${comparisonId}/review`,
    {
      data: {
        approved,
      },
      method: 'PATCH',
    },
  );
}
