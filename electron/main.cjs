const { app, BrowserWindow, ipcMain, globalShortcut } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1050,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.cjs'),
    },
    frame: true, // Native Windows title bar with close/minimize/maximize buttons
    backgroundColor: '#fdfdfd',
  });

  mainWindow.loadURL('http://localhost:3000');

  // Open DevTools in development to inspect any client-side issues
  // mainWindow.webContents.openDevTools({ mode: 'detach' });

  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Renderer Console] ${message} (${sourceId}:${line})`);
  });

  mainWindow.webContents.on('render-process-gone', (event, details) => {
    console.error('[Render process gone]', details);
  });

  // Ensure zoom starts at 100%
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents.setZoomLevel(0);
    mainWindow.webContents.setZoomFactor(1.0);
  });

  // Keyboard zoom shortcuts
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.control || input.meta) {
      if (input.key === '=' || input.key === '+') {
        const current = mainWindow.webContents.getZoomLevel();
        mainWindow.webContents.setZoomLevel(Math.min(current + 0.5, 5));
        event.preventDefault();
      } else if (input.key === '-') {
        const current = mainWindow.webContents.getZoomLevel();
        mainWindow.webContents.setZoomLevel(Math.max(current - 0.5, -3));
        event.preventDefault();
      } else if (input.key === '0') {
        mainWindow.webContents.setZoomLevel(0);
        event.preventDefault();
      }
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC handlers for zoom from renderer
ipcMain.on('zoom-in', () => {
  if (mainWindow) {
    const current = mainWindow.webContents.getZoomLevel();
    mainWindow.webContents.setZoomLevel(Math.min(current + 0.5, 5));
  }
});

ipcMain.on('zoom-out', () => {
  if (mainWindow) {
    const current = mainWindow.webContents.getZoomLevel();
    mainWindow.webContents.setZoomLevel(Math.max(current - 0.5, -3));
  }
});

ipcMain.on('zoom-reset', () => {
  if (mainWindow) {
    mainWindow.webContents.setZoomLevel(0);
  }
});

const { dialog } = require('electron');

ipcMain.handle('dialog-open-folder', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory', 'createDirectory']
  });
  if (result.canceled || !result.filePaths.length) {
    return null;
  }
  return result.filePaths[0];
});

function startPythonBackend() {
  const http = require('http');

  // Check if backend is already running on port 8088 to prevent [WinError 10048]
  const req = http.get('http://127.0.0.1:8088/api/system/status', (res) => {
    console.log('Detected existing Python backend already active on port 8088 (reusing).');
  });

  req.on('error', () => {
    // Port 8088 is free, spawn backend process
    const pythonExecutable = path.join(__dirname, '../.venv/Scripts/python.exe');
    const backendScript = path.join(__dirname, '../backend/api_server.py');
    const projectRoot = path.join(__dirname, '..');

    console.log('Starting Python backend...', backendScript);
    pythonProcess = spawn(pythonExecutable, [backendScript], {
      cwd: projectRoot,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      windowsHide: true,
    });

    pythonProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`Backend: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      console.log(`Backend exited with code ${code}`);
    });
  });
}

app.whenReady().then(() => {
  startPythonBackend();
  setTimeout(createWindow, 2000);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  if (pythonProcess) {
    console.log('Killing Python backend...');
    pythonProcess.kill();
  }
});

