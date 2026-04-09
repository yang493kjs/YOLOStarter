<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import type { ConcentrationData } from '@/types'
import dayjs from 'dayjs'

interface Props {
  data: ConcentrationData[]
  title?: string
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '浓度柱状图',
  height: '350px',
})

const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

// 处理数据
const chartData = computed(() => {
  return props.data
    .slice()
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
})

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chart) return

  const times = chartData.value.map(d => dayjs(d.timestamp).format('HH:mm'))
  const values = chartData.value.map(d => d.value)
  const colors = chartData.value.map(d => {
    if (d.status === 'danger') return '#f56c6c'
    if (d.status === 'warning') return '#e6a23c'
    return '#67c23a'
  })

  const option: echarts.EChartsOption = {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal',
      },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter: (params: any) => {
        const data = params[0]
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 4px;">${data.axisValue}</div>
            <div>浓度值: <span style="color: #409eff; font-weight: 600;">${data.value}</span> mg/L</div>
          </div>
        `
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: {
        lineStyle: {
          color: '#dcdfe6',
        },
      },
      axisLabel: {
        color: '#606266',
        rotate: 30,
      },
    },
    yAxis: {
      type: 'value',
      name: '浓度 (mg/L)',
      axisLine: {
        show: true,
        lineStyle: {
          color: '#dcdfe6',
        },
      },
      axisLabel: {
        color: '#606266',
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0',
        },
      },
    },
    series: [
      {
        name: '浓度值',
        type: 'bar',
        data: values.map((value, index) => ({
          value,
          itemStyle: {
            color: colors[index],
          },
        })),
        barWidth: '60%',
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }

  chart.setOption(option)
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

// 窗口大小变化时重绘
const handleResize = () => {
  chart?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: v-bind(height);
}
</style>
