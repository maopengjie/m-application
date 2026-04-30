<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";

import { Page } from "@vben/common-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@vben-core/shadcn-ui";

import { BarChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import {
  ElButton,
  ElDialog,
  ElEmpty,
  ElMessage,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
} from "element-plus";
import { Activity, Clock, PlayCircle, Server } from "lucide-vue-next";

import {
  getCrawlerTasksApi,
  getHealthTrendsApi,
  getPlatformHealthApi,
  getScraperResultsApi,
  getSmokeStatusApi,
  triggerPriceUpdateApi,
} from "#/api/crawler";

echarts.use([GridComponent, TooltipComponent, LegendComponent, BarChart, CanvasRenderer]);

const tasks = ref<any[]>([]);
const platformHealth = ref<any[]>([]);
const healthTrends = ref<any>({});
const smokeStatus = ref<any>({ is_all_healthy: true });
const extractedData = ref<any[]>([]);
const activeView = ref("tasks");
const loading = ref(true);
const statsLoading = ref(true);
const error = ref<null | string>(null);

const detailVisible = ref(false);
const currentTask = ref<any>(null);

const latencyChartRef = ref<HTMLElement | null>(null);
let myChart: echarts.ECharts | null = null;

const initChart = () => {
  if (!latencyChartRef.value) return;
  myChart = echarts.init(latencyChartRef.value);
  updateChart();
};

const updateChart = () => {
  if (!myChart || Object.keys(healthTrends.value).length === 0) return;

  const platforms = Object.keys(healthTrends.value);
  const latencies = platforms.map((p) => {
    const records = healthTrends.value[p];
    return Math.round(records[records.length - 1].latency);
  });

  const option = {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: "{b}: <b>{c} ms</b>",
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      top: "15%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: platforms,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#ccc", opacity: 0.3 } },
    },
    yAxis: {
      type: "value",
      name: "延迟 (ms)",
      nameTextStyle: { fontSize: 10, color: "#999" },
      splitLine: {
        lineStyle: { type: "dashed", opacity: 0.1 },
      },
    },
    series: [
      {
        name: "平均延迟",
        type: "bar",
        barWidth: "45%",
        data: latencies,
        itemStyle: {
          color: (params: any) => {
            const colors = [
              ["#ef4444", "#f87171"], // Red
              ["#3b82f6", "#60a5fa"], // Blue
              ["#10b981", "#34d399"], // Green
            ];
            const idx = params.dataIndex % colors.length;
            return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: colors[idx][0] },
              { offset: 1, color: colors[idx][1] },
            ]);
          },
          borderRadius: [6, 6, 0, 0],
        },
        showBackground: true,
        backgroundStyle: {
          color: "rgba(180, 180, 180, 0.1)",
          borderRadius: [6, 6, 0, 0],
        },
      },
    ],
  };

  myChart.setOption(option);
};

watch(
  healthTrends,
  () => {
    nextTick(() => {
      if (myChart) {updateChart();}
      else {initChart();}
    });
  },
  { deep: true },
);

const fetchResults = async () => {
  try {
    const data = await getScraperResultsApi();
    extractedData.value = data;
  } catch (error_) {
    console.error("Results fetch failed", error_);
  }
};

const fetchHealth = async () => {
  statsLoading.value = true;
  try {
    const [health, smoke, trends] = await Promise.all([
      getPlatformHealthApi(),
      getSmokeStatusApi(),
      getHealthTrendsApi(3),
    ]);
    platformHealth.value = health;
    smokeStatus.value = smoke;
    healthTrends.value = trends;
  } catch (error_) {
    console.error("Health fetch failed", error_);
  } finally {
    statsLoading.value = false;
  }
};

const fetchTasks = async () => {
  loading.value = true;
  try {
    tasks.value = await getCrawlerTasksApi();
  } catch (error_: any) {
    error.value = error_.message || "获取任务列表失败";
  } finally {
    loading.value = false;
  }
};

const viewTaskDetails = (task: any) => {
  currentTask.value = task;
  detailVisible.value = true;
};

const handleTriggerUpdate = async () => {
  try {
    await triggerPriceUpdateApi();
    ElMessage.success("更新任务已触发趋势刷新");
    void fetchTasks();
    void fetchHealth();
    void fetchResults();
  } catch {
    ElMessage.error("触发失败");
  }
};

const handleResize = () => myChart?.resize();

onMounted(() => {
  void fetchTasks();
  void fetchHealth();
  void fetchResults();

  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  myChart?.dispose();
});

const getStatusBadgeClass = (status: string) => {
  switch (status?.toLowerCase()) {
    case "critical":
    case "failed": {
      return "bg-destructive/10 text-destructive border-destructive/20";
    }
    case "degraded": {
      return "bg-orange-500/10 text-orange-500 border-orange-500/20";
    }
    case "healthy":
    case "success": {
      return "bg-green-500/10 text-green-500 border-green-500/20";
    }
    case "running": {
      return "bg-primary/10 text-primary border-primary/20";
    }
    default: {
      return "bg-muted text-muted-foreground border-muted-foreground/20";
    }
  }
};

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    critical: "严重异常",
    degraded: "亚健康",
    failed: "失败",
    healthy: "健康",
    running: "执行中",
    success: "成功",
  };
  return map[status?.toLowerCase()] || status;
};
</script>

<template>
  <Page
    title="数据引擎监控中心"
    description="多平台抓取生命周期监控，包含实时健康状态、成功率趋势及异常审计。"
  >
    <!-- 全局状态栏 -->
    <div class="grid gap-4 md:grid-cols-4 mb-6">
      <Card
        v-for="p in platformHealth"
        :key="p.platform"
        class="border-l-4 shadow-sm transition-all hover:translate-y-[-2px]"
        :class="p.status === 'healthy' ? 'border-l-green-500' : 'border-l-orange-500'"
      >
        <CardHeader class="flex flex-row items-center justify-between pb-2 space-y-0 text-xs">
          <CardTitle class="font-bold">{{ p.platform }}</CardTitle>
          <span
            class="px-2 py-0.5 rounded-full text-[10px] font-bold"
            :class="getStatusBadgeClass(p.status)"
          >
            {{ getStatusLabel(p.status) }}
          </span>
        </CardHeader>
        <CardContent>
          <div class="text-xl font-bold font-mono">{{ p.avg_latency_ms || 0 }}ms</div>
          <div class="flex justify-between items-center mt-2">
            <p class="text-[10px] text-muted-foreground">
              成功/失败: {{ p.success_count }}/{{ p.failed_count }}
            </p>
            <div
              v-if="p.error_breakdown && Object.keys(p.error_breakdown).length > 0"
              class="text-[10px] text-destructive font-bold"
            >
              {{ Object.keys(p.error_breakdown)[0] }}...
            </div>
          </div>
        </CardContent>
      </Card>

      <Card
        class="bg-primary/10 border-primary/20 shadow-lg animate-pulse"
        v-if="!smokeStatus.is_all_healthy"
      >
        <CardHeader class="pb-2">
          <CardTitle class="text-xs font-bold text-destructive">异常检测</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="text-lg font-bold text-destructive">
            警报: {{ smokeStatus.critical_platforms?.join(",") }}
          </div>
          <p class="text-[10px]">反爬风控激增，建议检查代理池</p>
        </CardContent>
      </Card>
    </div>

    <!-- 趋势与状态概览 -->
    <div class="grid gap-6 md:grid-cols-2 mb-8" v-if="Object.keys(healthTrends).length > 0">
      <Card class="shadow-sm">
        <CardHeader class="pb-3 border-b">
          <CardTitle class="text-[14px] flex items-center gap-2">
            <Activity class="h-4 w-4 text-primary" /> 平台稳定性趋势 (最近 5 次)
          </CardTitle>
        </CardHeader>
        <CardContent class="pt-4">
          <div class="space-y-4">
            <div v-for="(records, platform) in healthTrends" :key="platform">
              <div class="flex justify-between text-xs mb-1 font-bold">
                <span>{{ platform }}</span>
                <span
                  :class="
                    records[records.length - 1].success /
                      (records[records.length - 1].success + records[records.length - 1].failed ||
                        1) >
                    0.8
                      ? 'text-green-500'
                      : 'text-destructive'
                  "
                >
                  {{
                    Math.round(
                      (records[records.length - 1].success /
                        (records[records.length - 1].success + records[records.length - 1].failed ||
                          1)) *
                        100,
                    )
                  }}%
                </span>
              </div>
              <div class="flex gap-1 h-3">
                <div
                  v-for="(r, idx) in records.slice(-5)"
                  :key="idx"
                  class="flex-1 rounded-sm transition-all hover:opacity-80 cursor-help"
                  :class="r.status === 'healthy' ? 'bg-green-500/80' : 'bg-orange-500/80'"
                  :title="`TS: ${r.ts}, Success: ${r.success}, Fail: ${r.failed}`"
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card class="shadow-sm">
        <CardHeader class="pb-3 border-b">
          <CardTitle class="text-[14px] flex items-center gap-2">
            <Clock class="h-4 w-4 text-primary" /> 采集平均耗时对比 (ms)
          </CardTitle>
        </CardHeader>
        <CardContent class="pt-4 h-48 relative">
          <div ref="latencyChartRef" class="w-full h-full"></div>
        </CardContent>
      </Card>
    </div>

    <div class="mt-8">
      <ElTabs v-model="activeView" class="crawler-tabs" v-if="!loading">
        <!-- Tab 1: 审计日志 -->
        <ElTabPane name="tasks">
          <template #label>
            <span class="flex items-center gap-2">
              <Server class="h-4 w-4" /> 审计日志 (Audit Logs)
            </span>
          </template>

          <Card class="shadow-sm">
            <CardHeader class="flex flex-row items-center justify-between border-b pb-4">
              <div class="flex items-center gap-2">
                <PlayCircle class="h-5 w-5 text-primary" />
                <CardTitle class="text-lg">任务引擎流水线</CardTitle>
              </div>
              <button
                @click="handleTriggerUpdate"
                class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-bold hover:opacity-90 transition-all shadow-lg active:scale-95"
              >
                <Activity class="h-4 w-4" />
                立即执行全量同步
              </button>
            </CardHeader>
            <CardContent class="p-0">
              <div v-if="error" class="flex flex-col items-center justify-center py-20">
                <ElEmpty :description="error">
                  <template #extra>
                    <ElButton type="primary" @click="fetchTasks">重新加载</ElButton>
                  </template>
                </ElEmpty>
              </div>

              <div
                v-else-if="tasks.length === 0"
                class="flex flex-col items-center justify-center py-20 text-muted-foreground"
              >
                <ElEmpty description="暂无任务记录" />
              </div>

              <div v-else class="overflow-x-auto">
                <table class="w-full text-sm text-left">
                  <thead class="bg-muted/50 text-muted-foreground uppercase text-xs font-semibold">
                    <tr>
                      <th class="px-6 py-4">任务ID</th>
                      <th class="px-6 py-4">类型</th>
                      <th class="px-6 py-4">状态</th>
                      <th class="px-6 py-4">进度 (成功/失败/总计)</th>
                      <th class="px-6 py-4">执行时间/耗时</th>
                      <th class="px-6 py-4">操作</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y">
                    <tr
                      v-for="task in tasks"
                      :key="task.id"
                      class="hover:bg-muted/30 transition-colors"
                    >
                      <td class="px-6 py-4 font-mono">#{{ task.id }}</td>
                      <td class="px-6 py-4">
                        <span class="px-2 py-1 rounded text-xs font-medium border bg-muted/50">
                          {{ task.task_type === "price_update" ? "全量价格更新" : "单一商品抓取" }}
                        </span>
                      </td>
                      <td class="px-6 py-4">
                        <div class="flex items-center gap-2">
                          <span
                            class="px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase"
                            :class="[getStatusBadgeClass(task.status)]"
                          >
                            {{ getStatusLabel(task.status) }}
                          </span>
                        </div>
                      </td>
                      <td class="px-6 py-4">
                        <div class="flex flex-col gap-1 w-40">
                          <div
                            class="flex justify-between text-[10px] text-muted-foreground font-mono"
                          >
                            <span>
                              <span class="text-green-500">{{ task.success_count }}</span> /
                              <span class="text-destructive">{{ task.failed_count }}</span> /
                              {{ task.total_count }}
                            </span>
                            <span>{{
                                Math.round((task.success_count / (task.total_count || 1)) * 100)
                              }}%</span>
                          </div>
                          <div class="h-1.5 w-full bg-muted rounded-full overflow-hidden flex">
                            <div
                              class="h-full bg-green-500"
                              :style="{
                                width: `${(task.success_count / (task.total_count || 1)) * 100}%`,
                              }"
                            ></div>
                            <div
                              class="h-full bg-destructive"
                              :style="{
                                width: `${(task.failed_count / (task.total_count || 1)) * 100}%`,
                              }"
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td class="px-6 py-4 text-muted-foreground text-[12px]">
                        <div class="flex flex-col">
                          <div class="flex items-center gap-1">
                            <Clock class="h-3 w-3" />
                            {{ new Date(task.start_time).toLocaleString() }}
                          </div>
                          <div
                            v-if="task.metadata_json?.summary?.duration_seconds"
                            class="text-[10px] text-primary font-bold"
                          >
                            耗时: {{ task.metadata_json.summary.duration_seconds }}s
                          </div>
                        </div>
                      </td>
                      <td class="px-6 py-4">
                        <ElButton
                          type="primary"
                          link
                          @click="viewTaskDetails(task)"
                          class="font-bold"
                        >
                          审计详情
                        </ElButton>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </ElTabPane>

        <!-- Tab 2: 采集成果 -->
        <ElTabPane name="results">
          <template #label>
            <span class="flex items-center gap-2">
              <Activity class="h-4 w-4" /> 采集成果 (Extracted Data)
            </span>
          </template>

          <Card class="shadow-sm">
            <CardHeader class="border-b pb-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <Server class="h-5 w-5 text-primary" />
                  <CardTitle class="text-lg">已提取 SKU 实时快照</CardTitle>
                </div>
                <ElButton type="primary" link @click="fetchResults">
                  <Activity class="h-4 w-4 mr-1" /> 刷新数据
                </ElButton>
              </div>
            </CardHeader>
            <CardContent class="p-0">
              <ElTable :data="extractedData" stripe style="width: 100%" height="500">
                <ElTableColumn prop="platform" label="平台" width="100">
                  <template #default="{ row }">
                    <span class="px-2 py-0.5 rounded border bg-muted/50 text-[10px] font-bold">{{
                      row.platform
                    }}</span>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="title" label="商品描述" min-width="250" show-overflow-tooltip>
                  <template #default="{ row }">
                    <span class="text-sm font-medium">{{ row.title }}</span>
                    <div class="text-[10px] text-muted-foreground font-mono">
                      ID: {{ row.platform_sku_id }}
                    </div>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="price" label="当前价格" width="140">
                  <template #default="{ row }">
                    <span class="text-md font-mono font-bold text-primary">¥{{ row.price }}</span>
                    <div
                      v-if="row.original_price"
                      class="text-[10px] text-muted-foreground line-through decoration-muted-foreground/30"
                    >
                      ¥{{ row.original_price }}
                    </div>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="stock_status" label="库存状态" width="120">
                  <template #default="{ row }">
                    <span
                      class="px-2 py-1 rounded-full text-[10px] font-bold"
                      :class="
                        row.stock_status === 'in_stock'
                          ? 'bg-green-500/10 text-green-500 border border-green-500/20'
                          : 'bg-destructive/10 text-destructive border border-destructive/20'
                      "
                    >
                      {{ row.stock_status === "in_stock" ? "有货" : "无货/下架" }}
                    </span>
                  </template>
                </ElTableColumn>
                <ElTableColumn prop="updated_at" label="最后同步" width="180">
                  <template #default="{ row }">
                    <div class="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock class="h-3 w-3" />
                      {{ new Date(row.updated_at).toLocaleString() }}
                    </div>
                  </template>
                </ElTableColumn>
              </ElTable>
            </CardContent>
          </Card>
        </ElTabPane>
      </ElTabs>

      <div v-else class="flex justify-center items-center py-40">
        <span
          class="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"
        ></span>
      </div>
    </div>

    <ElDialog v-model="detailVisible" title="任务引擎稳定性报告" width="750" destroy-on-close>
      <div class="space-y-6" v-if="currentTask">
        <div
          v-if="currentTask.metadata_json?.summary"
          class="grid grid-cols-4 gap-4 bg-muted/30 p-4 rounded-lg border"
        >
          <div class="text-center">
            <div class="text-[10px] text-muted-foreground uppercase font-bold">平均延迟</div>
            <div class="text-md font-mono">
              {{ currentTask.metadata_json.summary.avg_latency_ms || 0 }}ms
            </div>
          </div>
          <div class="text-center border-x">
            <div class="text-[10px] text-muted-foreground uppercase font-bold">重试次数</div>
            <div class="text-md font-mono text-orange-500">
              {{ currentTask.metadata_json.summary.total_retries || 0 }}次
            </div>
          </div>
          <div class="text-center border-r">
            <div class="text-[10px] text-muted-foreground uppercase font-bold">成功率</div>
            <div class="text-md font-mono text-primary">
              {{ currentTask.metadata_json.summary.success_rate }}%
            </div>
          </div>
          <div class="text-center">
            <div class="text-[10px] text-muted-foreground uppercase font-bold">状态</div>
            <div
              class="text-md font-bold"
              :class="currentTask.status === 'success' ? 'text-green-500' : 'text-orange-500'"
            >
              {{ getStatusLabel(currentTask.status) }}
            </div>
          </div>
        </div>

        <div
          v-if="currentTask.metadata_json?.summary?.error_breakdown"
          class="flex flex-wrap gap-2 items-center"
        >
          <span class="text-[10px] font-bold text-muted-foreground uppercase mr-2">错误分布:</span>
          <template
            v-if="Object.keys(currentTask.metadata_json.summary.error_breakdown).length === 0"
          >
            <span class="text-[10px] text-muted-foreground italic">无异常发生</span>
          </template>
          <template v-else>
            <span
              v-for="(count, code) in currentTask.metadata_json.summary.error_breakdown"
              :key="code"
              class="px-2 py-0.5 rounded-full bg-destructive/10 text-destructive border border-destructive/20 text-[10px] font-bold"
            >
              {{ code }}: {{ count }}
            </span>
          </template>
        </div>

        <div v-if="currentTask.metadata_json?.summary?.platforms" class="flex items-center gap-2">
          <span class="text-[10px] font-bold text-muted-foreground uppercase mr-2">涉及平台:</span>
          <span
            v-for="p in currentTask.metadata_json.summary.platforms"
            :key="p"
            class="px-2 py-0.5 rounded bg-muted border text-[10px]"
          >
            {{ p }}
          </span>
        </div>

        <div>
          <h4 class="text-sm font-bold mb-2 flex items-center gap-2">
            <Activity class="h-4 w-4" />元数据 (Audit Metadata)
          </h4>
          <pre class="p-4 bg-muted rounded text-[12px] overflow-auto max-h-40">{{
            JSON.stringify(currentTask.metadata_json, null, 2) || "无元数据"
          }}</pre>
        </div>
        <div v-if="currentTask.metadata_json?.results?.length">
          <h4 class="text-sm font-bold mb-2">抓取结果 (Crawl Results)</h4>
          <div class="border rounded-lg overflow-hidden max-h-80 overflow-y-auto">
            <table class="w-full text-[12px] text-left">
              <thead class="bg-muted">
                <tr>
                  <th class="px-3 py-2">商品/SKU</th>
                  <th class="px-3 py-2">平台</th>
                  <th class="px-3 py-2">原价/现状</th>
                  <th class="px-3 py-2 text-primary">新价格</th>
                </tr>
              </thead>
              <tbody class="divide-y">
                <tr v-for="res in currentTask.metadata_json.results" :key="res.sku_id">
                  <td class="px-3 py-2">
                    <div class="font-medium max-w-[200px] truncate" :title="res.title">
                      {{ res.title }}
                    </div>
                    <div class="text-[10px] text-muted-foreground flex items-center gap-1">
                      {{ res.shop }}
                    </div>
                  </td>
                  <td class="px-3 py-2">
                    <span class="px-1.5 py-0.5 rounded border bg-muted/50 text-[10px]">
                      {{ res.platform }}
                    </span>
                  </td>
                  <td class="px-3 py-2">
                    <div class="text-muted-foreground line-through decoration-muted-foreground/30">
                      ¥{{ res.orig || "-" }}
                    </div>
                    <div
                      class="text-[10px]"
                      :class="res.stock === 'in_stock' ? 'text-green-500' : 'text-destructive'"
                    >
                      {{ res.stock === "in_stock" ? "有货" : "无货/下架" }}
                    </div>
                  </td>
                  <td class="px-3 py-2 font-bold text-primary">¥{{ res.new }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-if="currentTask.metadata_json?.errors?.length">
          <h4 class="text-sm font-bold mb-2 text-destructive">错误审计 (Error Audit)</h4>
          <pre
            class="p-4 bg-destructive/10 text-destructive rounded text-[12px] whitespace-pre-wrap max-h-40 overflow-auto"
            >{{ currentTask.metadata_json.errors.join("\n") }}</pre>
        </div>
      </div>
    </ElDialog>
  </Page>
</template>
