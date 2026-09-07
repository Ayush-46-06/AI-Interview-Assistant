interface ElectronStore {
  get: (key: string) => Promise<string | null>
  set: (key: string, value: string) => Promise<void>
  delete: (key: string) => Promise<void>
}

declare interface Window {
  electronStore: ElectronStore
}

