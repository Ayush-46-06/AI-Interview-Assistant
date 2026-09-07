import { contextBridge, ipcRenderer } from 'electron'

// Expose a narrowly scoped API to the renderer.
// The renderer cannot call arbitrary IPC channels — only these defined methods.
contextBridge.exposeInMainWorld('electronStore', {
  get: (key: string): Promise<string | null> => ipcRenderer.invoke('store:get', key),
  set: (key: string, value: string): Promise<void> => ipcRenderer.invoke('store:set', key, value),
  delete: (key: string): Promise<void> => ipcRenderer.invoke('store:delete', key)
})
