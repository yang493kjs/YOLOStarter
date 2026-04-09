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
  showThreshold?: boolean
  warningThreshold?: number
  dangerThreshold?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '浓度趋势图',
  height: '400px',
  showThreshold: true,
  warningThreshold: 60,
  dangerThreshold: 80,
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

  const times = chartData.value.map(d => dayjs(d.timestamp).format('HH:mm:ss'))
  const values = chartData.value.map(d => d.value)

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
      formatter: (params: any) => {
        const data = params[0]
        const item = chartData.value[params[0].dataIndex]
        return `
          <div style="padding: 8px;">
            <div style="font-weight: 600; margin-bottom: 8px;">${data.axisValue}</div>
            <div>浓度值: <span style="color: #409eff; font-weight: 600;">${data.value}</span> mg/L</div>
            <div>状态: <span style="color: ${item?.status === 'danger' ? '#f56c6c' : item?.status === 'warning' ? '#e6a23c' : '#67c23a'}">${item?.status === 'danger' ? '危险' : item?.status === 'warning' ? '警告' : '正常'}</span></div>
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
      boundaryGap: false,
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
      min: 0,
      max: 100,
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
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: {
          width: 2,
          color: '#409eff',
        },
        itemStyle: {
          color: '#409eff',
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' },
          ]),
        },
      },
    ],
  }

  // 添加阈值线
  if (props.showThreshold) {
    (option.series as any[])[0].markLine = {
      silent: true,
      symbol: 'none',
      data: [
        {
          yAxis: props.warningThreshold,
          name: '警告阈值',
          lineStyle: {
            color: '#e6a23c',
            type: 'dashed',
          },
          label: {
            show: true,
            position: 'end',
            formatter: '警告阈值',
            color: '#e6a23c',
          },
        },
        {
          yAxis: props.dangerThreshold,
          name: '危险阈值',
          lineStyle: {
            color: '#f56c6c',
            type: 'dashed',
          },
          label: {
            show: true,
            position: 'end',
            formatter: '危险阈值',
            color: '#f56c6c',
          },
        },
      ],
    }
  }

  chart.setOption(option)
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

// 监听阈值变化
watch([() => props.warningThreshold, () => props.dangerThreshold], () => {
  updateChart()
})

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
