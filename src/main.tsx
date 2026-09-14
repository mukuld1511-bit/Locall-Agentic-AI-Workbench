import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { loader } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

// Configure Monaco Environment with dedicated worker loaders for Vite
(self as any).MonacoEnvironment = {
  getWorkerUrl: function (_moduleId: any, label: string) {
    if (label === 'json') {
      return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
        self.MonacoEnvironment = { baseUrl: '${window.location.origin}/' };
        importScripts('${window.location.origin}/node_modules/monaco-editor/min/vs/language/json/json.worker.js');
      `)}`;
    }
    if (label === 'css' || label === 'scss' || label === 'less') {
      return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
        self.MonacoEnvironment = { baseUrl: '${window.location.origin}/' };
        importScripts('${window.location.origin}/node_modules/monaco-editor/min/vs/language/css/css.worker.js');
      `)}`;
    }
    if (label === 'html' || label === 'handlebars' || label === 'razor') {
      return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
        self.MonacoEnvironment = { baseUrl: '${window.location.origin}/' };
        importScripts('${window.location.origin}/node_modules/monaco-editor/min/vs/language/html/html.worker.js');
      `)}`;
    }
    if (label === 'typescript' || label === 'javascript') {
      return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
        self.MonacoEnvironment = { baseUrl: '${window.location.origin}/' };
        importScripts('${window.location.origin}/node_modules/monaco-editor/min/vs/language/typescript/ts.worker.js');
      `)}`;
    }
    return `data:text/javascript;charset=utf-8,${encodeURIComponent(`
      self.MonacoEnvironment = { baseUrl: '${window.location.origin}/' };
      importScripts('${window.location.origin}/node_modules/monaco-editor/min/vs/base/worker/workerMain.js');
    `)}`;
  },
  getWorker: function (_moduleId: any, _label: string) {
    // Return empty mock worker on fallback to prevent UI thread freezes and unhandled fetch errors
    const blob = new Blob(
      [`self.onmessage = function(e) { self.postMessage({ id: e.data.id, result: null }); };`],
      { type: 'application/javascript' }
    );
    return new Worker(URL.createObjectURL(blob));
  }
};

// Configure Monaco loader to use local bundle directly instead of external CDN
loader.config({ monaco });

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);



