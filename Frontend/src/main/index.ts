import { app, shell, BrowserWindow, ipcMain, session, safeStorage } from 'electron'
import { join } from 'path'
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

// Simple encrypted-storage path for refresh token — uses app's userData directory
const dataDir = app.getPath('userData')
const tokenPath = join(dataDir, '.athenura_session')

function readStoredValue(key: string): string | null {
  try {
    if (!existsSync(tokenPath)) return null
    if (!safeStorage.isEncryptionAvailable()) return null
    const encryptedBuffer = readFileSync(tokenPath)
    const raw = safeStorage.decryptString(encryptedBuffer)
    const store = JSON.parse(raw) as Record<string, string>
    return store[key] ?? null
  } catch {
    return null
  }
}

function writeStoredValue(key: string, value: string): void {
  if (!safeStorage.isEncryptionAvailable()) {
    console.error('Encryption not available, cannot store secret safely.')
    return
  }
  let store: Record<string, string> = {}
  try {
    if (existsSync(tokenPath)) {
      const encryptedBuffer = readFileSync(tokenPath)
      const raw = safeStorage.decryptString(encryptedBuffer)
      store = JSON.parse(raw)
    }
  } catch { /* fresh store */ }
  store[key] = value
  if (!existsSync(dataDir)) mkdirSync(dataDir, { recursive: true })
  const newEncryptedBuffer = safeStorage.encryptString(JSON.stringify(store))
  writeFileSync(tokenPath, newEncryptedBuffer)
}

function deleteStoredValue(key: string): void {
  try {
    if (!existsSync(tokenPath)) return
    if (!safeStorage.isEncryptionAvailable()) return
    const encryptedBuffer = readFileSync(tokenPath)
    const raw = safeStorage.decryptString(encryptedBuffer)
    const store = JSON.parse(raw) as Record<string, string>
    delete store[key]
    const newEncryptedBuffer = safeStorage.encryptString(JSON.stringify(store))
    writeFileSync(tokenPath, newEncryptedBuffer)
  } catch { /* ignore */ }
}

// IPC handlers for secure token storage (exposed via preload contextBridge)
ipcMain.handle('store:get', (_event, key: string) => readStoredValue(key))
ipcMain.handle('store:set', (_event, key: string, value: string) => { writeStoredValue(key, value) })
ipcMain.handle('store:delete', (_event, key: string) => { deleteStoredValue(key) })

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 760,
    minWidth: 900,
    minHeight: 600,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true
    }
  })

  // Strict Content Security Policy
  // Allows only our backend origin for HTTP/WS. No unsafe-eval, no wildcard.
  const apiOrigin = process.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  const wsOrigin = apiOrigin.replace(/^http/, 'ws')

  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          `default-src 'self'; ` +
          `script-src 'self'; ` +
          `style-src 'self' 'unsafe-inline'; ` +
          `connect-src 'self' ${apiOrigin} ${wsOrigin}; ` +
          `img-src 'self' data:; ` +
          `font-src 'self'; ` +
          `frame-src 'none'; ` +
          `object-src 'none'`
        ]
      }
    })
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  // Block navigation to external URLs — open in default browser instead
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  mainWindow.webContents.on('will-navigate', (event, url) => {
    const parsedUrl = new URL(url)
    if (parsedUrl.protocol !== 'file:' && !is.dev) {
      event.preventDefault()
    }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.disableHardwareAcceleration()

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.athenura.desktop')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

