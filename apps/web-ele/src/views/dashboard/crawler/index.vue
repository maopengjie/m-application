<script setup lang="ts">
import { onMounted, ref } from "vue";

import { Page } from "@vben/common-ui";

import {
  ElCard,
  ElCol,
  ElProgress,
  ElRow,
  ElTable,
  ElTableColumn,
  ElTag,
  ElTimeline,
  ElTimelineItem,
} from "element-plus";

import { requestClient } from "#/api/request";

const healthData = ref<any[]>([]);
const trends = ref<Record<string, any[]>>({});
const loading = ref(true);

const fetchHealth = async () => {
  loading.value = true;
  try {
    const res = await requestClient.get<any>("/crawler/platform-health");
    healthData.value = res.data;

    const trendRes = await requestClient.get<any>("/crawler/platform-health/trends");
    trends.value = trendRes.data;
  } catch (error) {
    console.error("Failed to fetch crawler health:", error);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchHealth);

const getStatusType = (status: string) => {
  switch (status) {
    case "critical": {
      return "danger";
    }
    case "degraded": {
      return "warning";
    }
    case "healthy": {
      return "success";
    }
    default: {
      return "info";
    }
  }
};

const getSuccessRate = (item: any) => {
  const total = item.success_count + item.failed_count;
  if (total === 0) return 0;
  return Math.round((item.success_count / total) * 100);
};
</script>

<template>
  <Page title="爬虫健康与治理看板" description="实时监控多平台抓取成功率、延迟及自适应治理策略。">
    <div v-loading="loading" class="p-4 space-y-6">
      <!-- Summary Cards -->
      <ElRow :gutter="20">
        <ElCol v-for="item in healthData" :key="item.platform" :span="6">
          <ElCard shadow="hover" class="!rounded-2xl border-none">
            <div class="flex items-center justify-between mb-4">
              <div class="flex items-center gap-2">
                <div
                  :class="item.platform === 'JD' ? 'bg-red-600' : 'bg-orange-500'"
                  class="w-2 h-6 rounded-full"
                ></div>
                <span class="text-lg font-black">{{ item.platform }}</span>
              </div>
              <ElTag
                :type="getStatusType(item.status)"
                size="small"
                effect="dark"
                class="!rounded-lg uppercase"
              >
                {{ item.status }}
              </ElTag>
            </div>

            <div class="space-y-4">
              <div>
                <div
                  class="flex justify-between text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-1"
                >
                  <span>抓取成功率</span>
                  <span>{{ getSuccessRate(item) }}%</span>
                </div>
                <ElProgress
                  :percentage="getSuccessRate(item)"
                  :status="getStatusType(item.status)"
                  :show-text="false"
                  :stroke-width="8"
                />
              </div>

              <div class="grid grid-cols-2 gap-4 pt-2">
                <div class="bg-zinc-50 dark:bg-zinc-800/50 p-3 rounded-xl">
                  <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-1">
                    平均延迟
                  </div>
                  <div class="text-sm font-black">{{ item.avg_latency_ms.toFixed(0) }}ms</div>
                </div>
                <div class="bg-zinc-50 dark:bg-zinc-800/50 p-3 rounded-xl">
                  <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-1">
                    当前间隔
                  </div>
                  <div class="text-sm font-black text-primary">
                    {{ item.current_interval.toFixed(1) }}s
                  </div>
                </div>
              </div>
            </div>
          </ElCard>
        </ElCol>
      </ElRow>

      <!-- Detailed Metrics -->
      <ElRow :gutter="20">
        <ElCol :span="16">
          <ElCard header="抓取趋势与错误分布" class="!rounded-2xl border-none">
            <ElTable :data="healthData" style="width: 100%">
              <ElTableColumn prop="platform" label="平台" width="100">
                <template #default="{ row }">
                  <span class="font-black">{{ row.platform }}</span>
                </template>
              </ElTableColumn>
              <ElTableColumn label="错误分解 (Error Breakdown)">
                <template #default="{ row }">
                  <div class="flex flex-wrap gap-2">
                    <template v-if="row.error_breakdown">
                      <ElTag
                        v-for="(count, code) in row.error_breakdown"
                        :key="code"
                        size="small"
                        type="info"
                        class="!rounded-md"
                      >
                        {{ code }}: {{ count }}
                      </ElTag>
                    </template>
                    <span v-else class="text-xs text-zinc-400">无异常记录</span>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn prop="timestamp" label="最后更新" width="180">
                <template #default="{ row }">
                  <span class="text-xs text-zinc-400 font-mono">{{
                    row.timestamp.replace("T", " ")
                  }}</span>
                </template>
              </ElTableColumn>
            </ElTable>
          </ElCard>
        </ElCol>

        <ElCol :span="8">
          <ElCard header="治理日志 (Governance Logs)" class="!rounded-2xl border-none">
            <ElTimeline>
              <ElTimelineItem
                v-for="log in healthData.filter((h) => h.status !== 'healthy')"
                :key="log.id"
                :timestamp="log.timestamp.split('T')[1].split('.')[0]"
                :type="getStatusType(log.status)"
              >
                <div class="text-xs font-black">
                  平台 {{ log.platform }} 进入 {{ log.status }} 状态
                </div>
                <div class="text-[10px] text-zinc-400 mt-1">
                  由于成功率波动，自适应间隔已调整至 {{ log.current_interval.toFixed(1) }}s
                </div>
              </ElTimelineItem>
              <ElTimelineItem
                v-if="healthData.every((h) => h.status === 'healthy')"
                timestamp="Just Now"
                type="success"
              >
                <div class="text-xs font-black">所有平台运行正常</div>
                <div class="text-[10px] text-zinc-400 mt-1">自适应引擎正以最佳频率运行。</div>
              </ElTimelineItem>
            </ElTimeline>
          </ElCard>
        </ElCol>
      </ElRow>
    </div>
  </Page>
</template>

<style scoped>
.tracking-widest {
  letter-spacing: 0.1em;
}
</style>
