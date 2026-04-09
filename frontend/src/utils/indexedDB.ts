const DB_NAME = 'DenseVisDB'
const DB_VERSION = 1

interface DatasetRecord {
  id: string
  name: string
  description?: string
  createTime: string
  images: ImageItem[]
  labels: LabelItem[]
  yamlData: YamlData | null
}

interface ImageItem {
  id: string
  name: string
  url: string
  size: number
  uploadTime: string
  split: 'train' | 'test'
}

interface LabelItem {
  id: string
  name: string
  content: string
  size: number
  uploadTime: string
  split: 'train' | 'test'
}

interface YamlData {
  fileName: string
  classCount: number
  classes: string[]
  rawData: any
}

class IndexedDBStorage {
  private db: IDBDatabase | null = null
  private initPromise: Promise<void> | null = null

  async init(): Promise<void> {
    if (this.db) return
    
    if (this.initPromise) {
      return this.initPromise
    }

    this.initPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION)

      request.onerror = () => {
        console.error('IndexedDB 打开失败:', request.error)
        reject(request.error)
      }

      request.onsuccess = () => {
        this.db = request.result
        console.log('IndexedDB 连接成功')
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        
        if (!db.objectStoreNames.contains('datasets')) {
          db.createObjectStore('datasets', { keyPath: 'id' })
        }
        
        if (!db.objectStoreNames.contains('datasetList')) {
          db.createObjectStore('datasetList', { keyPath: 'id' })
        }
        
        console.log('IndexedDB 数据库结构创建完成')
      }
    })

    return this.initPromise
  }

  private async getStore(storeName: string, mode: IDBTransactionMode = 'readonly'): Promise<IDBObjectStore> {
    await this.init()
    if (!this.db) {
      throw new Error('数据库未初始化')
    }
    const transaction = this.db.transaction(storeName, mode)
    return transaction.objectStore(storeName)
  }

  async saveDataset(dataset: DatasetRecord): Promise<void> {
    try {
      const store = await this.getStore('datasets', 'readwrite')
      
      return new Promise((resolve, reject) => {
        const request = store.put(dataset)
        
        request.onsuccess = () => {
          console.log(`数据集 ${dataset.id} 已保存到 IndexedDB`)
          resolve()
        }
        
        request.onerror = () => {
          console.error('保存数据集失败:', request.error)
          reject(request.error)
        }
      })
    } catch (error) {
      console.error('保存数据集失败:', error)
      throw error
    }
  }

  async getDataset(id: string): Promise<DatasetRecord | null> {
    try {
      const store = await this.getStore('datasets')
      
      return new Promise((resolve, reject) => {
        const request = store.get(id)
        
        request.onsuccess = () => {
          resolve(request.result || null)
        }
        
        request.onerror = () => {
          reject(request.error)
        }
      })
    } catch (error) {
      console.error('获取数据集失败:', error)
      return null
    }
  }

  async deleteDataset(id: string): Promise<void> {
    try {
      const store = await this.getStore('datasets', 'readwrite')
      
      return new Promise((resolve, reject) => {
        const request = store.delete(id)
        
        request.onsuccess = () => {
          console.log(`数据集 ${id} 已从 IndexedDB 删除`)
          resolve()
        }
        
        request.onerror = () => {
          reject(request.error)
        }
      })
    } catch (error) {
      console.error('删除数据集失败:', error)
      throw error
    }
  }

  async getAllDatasets(): Promise<DatasetRecord[]> {
    try {
      const store = await this.getStore('datasets')
      
      return new Promise((resolve, reject) => {
        const request = store.getAll()
        
        request.onsuccess = () => {
          resolve(request.result || [])
        }
        
        request.onerror = () => {
          reject(request.error)
        }
      })
    } catch (error) {
      console.error('获取所有数据集失败:', error)
      return []
    }
  }

  async saveDatasetList(list: any[]): Promise<void> {
    try {
      await this.init()
      const objectStore = this.db!.transaction('datasetList', 'readwrite').objectStore('datasetList')
      
      await new Promise<void>((resolve, reject) => {
        const clearRequest = objectStore.clear()
        
        clearRequest.onsuccess = () => {
          let completed = 0
          const total = list.length
          
          if (total === 0) {
            resolve()
            return
          }
          
          list.forEach(item => {
            const addRequest = objectStore.add(item)
            addRequest.onsuccess = () => {
              completed++
              if (completed === total) {
                resolve()
              }
            }
            addRequest.onerror = () => {
              reject(addRequest.error)
            }
          })
        }
        
        clearRequest.onerror = () => {
          reject(clearRequest.error)
        }
      })
      
      console.log(`数据集列表已保存，共 ${list.length} 个`)
    } catch (error) {
      console.error('保存数据集列表失败:', error)
      throw error
    }
  }

  async getDatasetList(): Promise<any[]> {
    try {
      const store = await this.getStore('datasetList')
      
      return new Promise((resolve, reject) => {
        const request = store.getAll()
        
        request.onsuccess = () => {
          resolve(request.result || [])
        }
        
        request.onerror = () => {
          reject(request.error)
        }
      })
    } catch (error) {
      console.error('获取数据集列表失败:', error)
      return []
    }
  }

  async addToDatasetList(item: any): Promise<void> {
    try {
      const store = await this.getStore('datasetList', 'readwrite')
      
      return new Promise((resolve, reject) => {
        const request = store.put(item)
        
        request.onsuccess = () => {
          resolve()
        }
        
        request.onerror = () => {
          reject(request.error)
        }
      })
    } catch (error) {
      console.error('添加数据集到列表失败:', error)
      throw error
    }
  }

  async removeFromDatasetList(id: string): Promise<void> {
    try {
      const store = await this.getStore('datasetList', 'readwrite')
      
      return new Promise((resolve, reject) => {
        const request = store.delete(id)
        
        request.onsuccess = () => {
          resolve()
        }
        
        request.onerror = () => {
          reject(request.error)
        }
      })
    } catch (error) {
      console.error('从列表删除数据集失败:', error)
      throw error
    }
  }

  async getStorageEstimate(): Promise<{ usage: number; quota: number }> {
    if (navigator.storage && navigator.storage.estimate) {
      const estimate = await navigator.storage.estimate()
      return {
        usage: estimate.usage || 0,
        quota: estimate.quota || 0
      }
    }
    return { usage: 0, quota: 0 }
  }
}

export const dbStorage = new IndexedDBStorage()
export type { DatasetRecord, ImageItem, LabelItem, YamlData }
