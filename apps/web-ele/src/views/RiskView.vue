<script setup lang="ts">
import { onMounted, ref } from "vue";

import { Page } from "@vben/common-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@vben-core/shadcn-ui";

import { ElButton, ElEmpty, ElMessage } from "element-plus";
import { AlertTriangle, Info, Search, ShieldAlert, ShieldCheck } from "lucide-vue-next";

import { getRisksApi, scanProductRiskApi } from "#/api/risk";

const risks = ref<any[]>([]);
const loading = ref(true);
const error = ref<null | string>(null);

// Scan state
const scanUrl = ref("");
const scanning = ref(false);

const fetchRisks = async () => {
  loading.value = true;
  error.value = null;
  try {
    risks.value = await getRisksApi();
  } catch (error_: any) {
    error.value = error_.message || "风险中心加载失败";
    console.error("Failed to fetch risks", error_);
  } finally {
    loading.value = false;
  }
};

const handleScan = async () => {
  if (!scanUrl.value) {
    ElMessage.warning("请先粘贴商品链接");
    return;
  }

  scanning.value = true;
  try {
    const result = await scanProductRiskApi(scanUrl.value);
    risks.value.unshift(result);
    scanUrl.value = "";
    ElMessage.success({
      message: "AI 智能扫描完成",
      type: "success",
      plain: true,
    });
  } catch (error_: any) {
    ElMessage.error(error_.message || "扫描失败，请重试");
  } finally {
    scanning.value = false;
  }
};

onMounted(() => {
  void fetchRisks();
});

const getRiskStatus = (score: number) => {
  if (score < 50) return "danger";
  if (score < 80) return "warning";
  return "success";
};
</script>

<template>
  <Page
    title="避雷分析"
    description="利用 AI 模型分析商品评价、店铺信誉及价格走势，助您规避购物陷阱。"
  >
    <div class="mb-8">
      <div class="relative flex items-center max-w-2xl mx-auto">
        <Search class="absolute left-3 h-5 w-5 text-muted-foreground" />
        <input
          v-model="scanUrl"
          type="text"
          placeholder="粘贴商品链接进行深度扫描..."
          class="w-full h-12 pl-10 pr-24 rounded-xl border bg-background shadow-sm focus:ring-2 focus:ring-primary outline-none transition-all disabled:opacity-50"
          :disabled="scanning"
          @keyup.enter="handleScan"
        />
        <ElButton
          type="primary"
          class="absolute right-2 h-8 !rounded-lg font-medium shadow-lg"
          :loading="scanning"
          @click="handleScan"
        >
          开始扫描
        </ElButton>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center items-center py-40">
      <span
        class="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"
      ></span>
    </div>

    <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
      <ElEmpty :description="error">
        <template #extra>
          <ElButton type="primary" @click="fetchRisks">重试分析</ElButton>
        </template>
      </ElEmpty>
    </div>

    <div v-else-if="risks.length === 0" class="flex flex-col items-center justify-center py-20">
      <ElEmpty description="暂未发现显著风险商品" />
    </div>
    <div v-else class="grid gap-6">
      <Card
        v-for="risk in risks"
        :key="risk.id"
        class="border-l-4"
        :class="{
          'border-l-destructive': getRiskStatus(risk.score) === 'danger',
          'border-l-yellow-500': getRiskStatus(risk.score) === 'warning',
          'border-l-green-500': getRiskStatus(risk.score) === 'success',
        }"
      >
        <CardHeader class="flex flex-row items-center justify-between py-4">
          <div class="flex items-center gap-3">
            <div
              class="p-2 rounded-lg"
              :class="[
                getRiskStatus(risk.score) === 'danger'
                  ? 'bg-destructive/10 text-destructive'
                  : getRiskStatus(risk.score) === 'warning'
                    ? 'bg-yellow-500/10 text-yellow-500'
                    : 'bg-green-500/10 text-green-500',
              ]"
            >
              <ShieldAlert v-if="getRiskStatus(risk.score) === 'danger'" class="h-5 w-5" />
              <AlertTriangle v-else-if="getRiskStatus(risk.score) === 'warning'" class="h-5 w-5" />
              <ShieldCheck v-else class="h-5 w-5" />
            </div>
            <div>
              <CardTitle class="text-lg font-bold">{{ risk.sku_title }}</CardTitle>
              <span class="text-xs font-medium uppercase text-muted-foreground">
                {{ risk.platform }} | 评分: {{ risk.score }} | 更新时间: {{ risk.updated_at }}
              </span>
            </div>
          </div>
          <Info class="h-5 w-5 text-muted-foreground cursor-help" />
        </CardHeader>
        <CardContent class="pb-6">
          <ul class="text-sm text-muted-foreground list-disc pl-5 space-y-1">
            <li v-if="risk.comment_abnormal">评价内容疑似异常 (AI 识别)</li>
            <li v-if="risk.sales_abnormal">销量波动显著异常</li>
            <li v-if="!risk.comment_abnormal && !risk.sales_abnormal">各项指标表现正常</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  </Page>
</template>
