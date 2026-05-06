import { requestClient } from '#/api/request';

export interface EtlLog {
  id: number;
  eventType: string;
  platform?: string;
  productId?: number;
  skuId?: string;
  fieldName?: string;
  originalValue?: string;
  cleanedValue?: string;
  message?: string;
  createdAt: string;
}

export interface AnomalyAlert {
  id: number;
  alertType: string;
  platform: string;
  skuId: string;
  productId?: number | null;
  alertValue: string;
  threshold?: string;
  isVerified: number;
  verificationResult?: string;
  message?: string;
  createdAt: string;
}

export interface EfficiencyRecord {
  id: number;
  platform: string;
  targetApi: string;
  responseTimeMs: number;
  statusCode: number;
  capturedAt: string;
}

export interface CleaningStats {
  totalCleaned: number;
  totalAnomalies: number;
  avgResponseTime: number;
  successRate: number;
}

export interface VerifyAnomalyPayload {
  isVerified: number;
  verificationResult?: string;
}

export interface RetryAnomalyScrapeResult {
  anomalyId: number;
  runId: number;
  taskId?: string | null;
  url: string;
}

export interface RelatedScrapeRun {
  id: number;
  taskName: string;
  status: string;
  successCount: number;
  failureCount: number;
  summaryMessage?: string;
  createdAt: string;
  finishedAt?: string | null;
}

export interface AnomalyContext {
  anomalyId: number;
  productId?: number | null;
  productName?: string | null;
  productUrl?: string | null;
  recentRuns: RelatedScrapeRun[];
}

export interface DataCenterNotification {
  date: string;
  id: string;
  isRead: boolean;
  link: string;
  message: string;
  query?: Record<string, string>;
  title: string;
  type: string;
}

export interface AnomalyQuery {
  alertType?: string;
  endAt?: string;
  isVerified?: number;
  limit?: number;
  platform?: string;
  product_id?: number;
  skuId?: string;
  startAt?: string;
}

interface EtlLogDto {
  id: number;
  event_type: string;
  platform?: string;
  product_id?: number;
  sku_id?: string;
  field_name?: string;
  original_value?: string;
  cleaned_value?: string;
  message?: string;
  created_at: string;
}

interface AnomalyAlertDto {
  id: number;
  alert_type: string;
  platform: string;
  sku_id: string;
  product_id?: number | null;
  alert_value: string;
  threshold?: string;
  is_verified: number;
  verification_result?: string;
  message?: string;
  created_at: string;
}

interface EfficiencyRecordDto {
  id: number;
  platform: string;
  target_api: string;
  response_time_ms: number;
  status_code: number;
  captured_at: string;
}

interface CleaningStatsDto {
  total_cleaned: number;
  total_anomalies: number;
  avg_response_time: number;
  success_rate: number;
}

interface RelatedScrapeRunDto {
  id: number;
  task_name: string;
  status: string;
  success_count: number;
  failure_count: number;
  summary_message?: string;
  created_at: string;
  finished_at?: string | null;
}

interface AnomalyContextDto {
  anomaly_id: number;
  product_id?: number | null;
  product_name?: string | null;
  product_url?: string | null;
  recent_runs: RelatedScrapeRunDto[];
}

interface DataCenterNotificationDto {
  date: string;
  id: string;
  is_read: boolean;
  link: string;
  message: string;
  query?: Record<string, string>;
  title: string;
  type: string;
}

interface RetryAnomalyScrapeResultDto {
  anomaly_id: number;
  run_id: number;
  task_id?: string | null;
  url: string;
}

function mapEtlLog(dto: EtlLogDto): EtlLog {
  return {
    id: dto.id,
    eventType: dto.event_type,
    platform: dto.platform,
    productId: dto.product_id,
    skuId: dto.sku_id,
    fieldName: dto.field_name,
    originalValue: dto.original_value,
    cleanedValue: dto.cleaned_value,
    message: dto.message,
    createdAt: dto.created_at,
  };
}

function mapAnomalyAlert(dto: AnomalyAlertDto): AnomalyAlert {
  return {
    id: dto.id,
    alertType: dto.alert_type,
    platform: dto.platform,
    skuId: dto.sku_id,
    productId: dto.product_id,
    alertValue: dto.alert_value,
    threshold: dto.threshold,
    isVerified: dto.is_verified,
    verificationResult: dto.verification_result,
    message: dto.message,
    createdAt: dto.created_at,
  };
}

function mapRelatedScrapeRun(dto: RelatedScrapeRunDto): RelatedScrapeRun {
  return {
    id: dto.id,
    taskName: dto.task_name,
    status: dto.status,
    successCount: dto.success_count,
    failureCount: dto.failure_count,
    summaryMessage: dto.summary_message,
    createdAt: dto.created_at,
    finishedAt: dto.finished_at,
  };
}

function mapAnomalyContext(dto: AnomalyContextDto): AnomalyContext {
  return {
    anomalyId: dto.anomaly_id,
    productId: dto.product_id,
    productName: dto.product_name,
    productUrl: dto.product_url,
    recentRuns: dto.recent_runs.map(mapRelatedScrapeRun),
  };
}

function mapEfficiency(dto: EfficiencyRecordDto): EfficiencyRecord {
  return {
    id: dto.id,
    platform: dto.platform,
    targetApi: dto.target_api,
    responseTimeMs: dto.response_time_ms,
    statusCode: dto.status_code,
    capturedAt: dto.captured_at,
  };
}

function mapStats(dto: CleaningStatsDto): CleaningStats {
  return {
    totalCleaned: dto.total_cleaned,
    totalAnomalies: dto.total_anomalies,
    avgResponseTime: dto.avg_response_time,
    successRate: dto.success_rate,
  };
}

export async function getEtlLogsApi(params?: any) {
  const data = await requestClient.get<EtlLogDto[]>('/data-cleaning/logs', { params });
  return data.map(mapEtlLog);
}

export async function getAuditLogsApi(params?: { limit?: number }) {
  const data = await requestClient.get<EtlLogDto[]>('/data-cleaning/audit-logs', {
    params,
  });
  return data.map(mapEtlLog);
}

export async function getAnomaliesApi(params?: any) {
  const data = await requestClient.get<AnomalyAlertDto[]>('/data-cleaning/anomalies', { params });
  return data.map(mapAnomalyAlert);
}

export async function getEfficiencyApi(params?: any) {
  const data = await requestClient.get<EfficiencyRecordDto[]>('/data-cleaning/efficiency', { params });
  return data.map(mapEfficiency);
}

export async function getCleaningStatsApi() {
  const data = await requestClient.get<CleaningStatsDto>('/data-cleaning/stats');
  return mapStats(data);
}

export async function getDataCenterNotificationsApi(params?: { limit?: number }) {
  const data = await requestClient.get<DataCenterNotificationDto[]>(
    '/data-cleaning/notifications',
    {
      params: {
        limit: params?.limit ?? 10,
      },
    },
  );
  return data.map((item) => ({
    date: item.date,
    id: item.id,
    isRead: item.is_read,
    link: item.link,
    message: item.message,
    query: item.query,
    title: item.title,
    type: item.type,
  }));
}

export async function verifyAnomalyApi(anomalyId: number, payload: VerifyAnomalyPayload) {
  const data = await requestClient.put<AnomalyAlertDto | { anomaly: AnomalyAlertDto }>(`/data-cleaning/anomalies/${anomalyId}`, {
    is_verified: payload.isVerified,
    verification_result: payload.verificationResult,
  });
  return mapAnomalyAlert('anomaly' in data ? data.anomaly : data);
}

export async function retryAnomalyScrapeApi(anomalyId: number): Promise<RetryAnomalyScrapeResult> {
  const data = await requestClient.post<RetryAnomalyScrapeResultDto>(
    `/data-cleaning/anomalies/${anomalyId}/retry-scrape`,
  );
  return {
    anomalyId: data.anomaly_id,
    runId: data.run_id,
    taskId: data.task_id,
    url: data.url,
  };
}

export async function getAnomalyContextApi(anomalyId: number) {
  const data = await requestClient.get<AnomalyContextDto>(
    `/data-cleaning/anomalies/${anomalyId}/context`,
  );
  return mapAnomalyContext(data);
}

export function buildAnomaliesExportUrl(params?: AnomalyQuery) {
  const searchParams = new URLSearchParams();
  if (params?.alertType) searchParams.set('alert_type', params.alertType);
  if (params?.endAt) searchParams.set('end_at', params.endAt);
  if (params?.isVerified !== undefined) searchParams.set('is_verified', String(params.isVerified));
  if (params?.limit !== undefined) searchParams.set('limit', String(params.limit));
  if (params?.platform) searchParams.set('platform', params.platform);
  if (params?.skuId) searchParams.set('sku_id', params.skuId);
  if (params?.startAt) searchParams.set('start_at', params.startAt);
  const queryString = searchParams.toString();
  return queryString
    ? `/api/data-cleaning/anomalies/export?${queryString}`
    : '/api/data-cleaning/anomalies/export';
}
