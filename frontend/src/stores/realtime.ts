import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export interface ImageItem {
  url: string
  thumbnail: string
  file: File
  loaded: boolean
}

export const useRealtimeStore = defineStore('realtime', () => {
  const images = ref<ImageItem[]>([])
  const pendingFiles = ref<File[]>([])
  const isProcessingFiles = ref(false)
  const selectedImageIndex = ref<number>(-1)
  const currentPage = ref(1)
  const pageSize = ref(50)
  const skippedFiles = ref(0)

  const totalPages = computed(() => Math.ceil(images.value.length / pageSize.value))

  const displayedImages = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return images.value.slice(start, end)
  })

  const selectedImage = computed(() => {
    if (selectedImageIndex.value >= 0 && selectedImageIndex.value < images.value.length) {
      return images.value[selectedImageIndex.value]
    }
    return null
  })

  const addImage = (image: ImageItem) => {
    images.value.push(image)
    if (images.value.length === 1) {
      selectedImageIndex.value = 0
    }
  }

  const selectImage = (index: number) => {
    selectedImageIndex.value = index
  }

  const clearImages = () => {
    images.value.forEach(image => {
      if (image.url && image.url.startsWith('blob:')) {
        URL.revokeObjectURL(image.url)
      }
    })
    images.value = []
    pendingFiles.value = []
    selectedImageIndex.value = -1
    currentPage.value = 1
  }

  const setPage = (page: number) => {
    currentPage.value = page
  }

  const addPendingFile = (file: File) => {
    pendingFiles.value.push(file)
  }

  const removePendingFile = () => {
    return pendingFiles.value.shift()
  }

  const setProcessingFiles = (value: boolean) => {
    isProcessingFiles.value = value
  }

  const incrementSkippedFiles = () => {
    skippedFiles.value++
  }

  const resetSkippedFiles = () => {
    skippedFiles.value = 0
  }

  return {
    images,
    pendingFiles,
    isProcessingFiles,
    selectedImageIndex,
    currentPage,
    pageSize,
    totalPages,
    displayedImages,
    selectedImage,
    addImage,
    selectImage,
    clearImages,
    setPage,
    addPendingFile,
    removePendingFile,
    setProcessingFiles,
    incrementSkippedFiles,
    resetSkippedFiles,
    skippedFiles,
  }
})
