import React, { useState, useEffect, useRef } from 'react';
import {
  Send, Code2, MessageSquare, Settings, Terminal, Loader2,
  Box, FolderOpen, Database, Cpu, Activity, RefreshCw,
  Play, Trash2, FileText, Shield, Zap, HardDrive, Wifi, WifiOff,
  ChevronRight, Plus, X, Minus, Square, Maximize2,
  Users, ClipboardList, Wrench, GitBranch, ZoomIn, ZoomOut,
  Sparkles, Bot, Search, Save, Eye, CheckCircle2, SplitSquareVertical,
  Layers, Compass, FileCode, Check, Copy, ChevronDown, CornerDownLeft,
  Paperclip, Image, Upload, AlertTriangle, ShieldAlert, LogIn, LogOut,
  UserCheck, Table, FileSpreadsheet, Lock, ExternalLink, TerminalSquare,
  FolderPlus, Gauge, Radio, Octagon, Flame, Power, Disc,
  Network, GitFork, ArrowDown, Cpu as CpuIcon
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Editor from '@monaco-editor/react';
import { ThreeMachineCanvas } from './components/ThreeMachineCanvas';

const API = 'http://127.0.0.1:8088';

// Electron IPC helper
const getElectron = () => {
  if (typeof window !== 'undefined' && (window as any).electronAPI) {
    return (window as any).electronAPI;
  }
  try {
    const electron = (window as any).require('electron');
    return electron.ipcRenderer;
  } catch {
    return null;
  }
};

function WindowControls() {
  const [zoomPercent, setZoomPercent] = useState(100);

  const zoomIn = () => {
    const el = getElectron();
    if (el?.zoomIn) el.zoomIn();
    else if (el?.send) el.send('zoom-in');
    setZoomPercent(p => Math.min(p + 10, 200));
  };

  const zoomOut = () => {
    const el = getElectron();
    if (el?.zoomOut) el.zoomOut();
    else if (el?.send) el.send('zoom-out');
    setZoomPercent(p => Math.max(p - 10, 50));
  };

  const zoomReset = () => {
    const el = getElectron();
    if (el?.zoomReset) el.zoomReset();
    else if (el?.send) el.send('zoom-reset');
    setZoomPercent(100);
  };

  const minimize = () => {
    const el = getElectron();
    if (el?.minimize) el.minimize();
    else if (el?.send) el.send('win-minimize');
  };

  const maximize = () => {
    const el = getElectron();
    if (el?.maximize) el.maximize();
    else if (el?.send) el.send('win-maximize');
  };

  const close = () => {
    const el = getElectron();
    if (el?.close) el.close();
    else if (el?.send) el.send('win-close');
    else window.close();
  };

  return (
    <div className="flex items-center space-x-1.5" style={{ WebkitAppRegion: 'no-drag' } as any}>
      <button onClick={zoomOut} className="w-7 h-7 rounded-md flex items-center justify-center text-slate-500 hover:bg-slate-200/80 hover:text-slate-700 transition-all cursor-pointer" title="Zoom Out (Ctrl -)">
        <ZoomOut className="w-3.5 h-3.5" />
      </button>
      <button onClick={zoomReset} className="min-w-[42px] px-1.5 h-7 rounded-md flex items-center justify-center text-[10px] font-mono font-bold text-slate-500 hover:bg-slate-200/80 hover:text-slate-700 transition-all cursor-pointer" title="Reset Zoom (Ctrl 0)">
        {zoomPercent}%
      </button>
      <button onClick={zoomIn} className="w-7 h-7 rounded-md flex items-center justify-center text-slate-500 hover:bg-slate-200/80 hover:text-slate-700 transition-all cursor-pointer" title="Zoom In (Ctrl +)">
        <ZoomIn className="w-3.5 h-3.5" />
      </button>

      <div className="w-px h-4 bg-slate-300 mx-1.5" />

      <button onClick={minimize} className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-500 hover:bg-slate-200/80 hover:text-slate-700 transition-all cursor-pointer" title="Minimize">
        <Minus className="w-3.5 h-3.5" />
      </button>
      <button onClick={maximize} className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-500 hover:bg-slate-200/80 hover:text-slate-700 transition-all cursor-pointer" title="Maximize">
        <Square className="w-3 h-3" />
      </button>
      <button onClick={close} className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-500 hover:bg-red-500 hover:text-white transition-all cursor-pointer shadow-xs" title="Close Window">
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

interface Message {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: string;
  attachment?: {
    name: string;
    path: string;
    type: string;
  };
}

interface ChatEntry { chat_id: string; title: string; created: string; updated: string; }
interface SandboxFile { name: string; is_dir: boolean; size: number; }
interface WorkerModel { worker_type: string; model_name: string; capabilities: string[]; vram_required_mb: number; ram_required_mb: number; license: string; is_loaded: boolean; }
interface IdeTab { path: string; name: string; content: string; modified: boolean; language: string; }
interface IdeFileNode { name: string; path: string; is_dir: boolean; children?: IdeFileNode[]; size?: number; }

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('home');
  const [messages, setMessages] = useState<Message[]>([
    { id: 'init', sender: 'system', text: 'Sovereign Industrial AI Workbench Initialized.\nZero cloud egress. Central Policy Engine & RBAC active.', timestamp: new Date().toLocaleTimeString() }
  ]);
  const [input, setInput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Active Attachment State
  const [currentAttachment, setCurrentAttachment] = useState<{
    name: string;
    path: string;
    type: string;
    size?: number;
  } | null>(null);

  // User Clearance / RBAC State & Compulsory Login
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return localStorage.getItem('musky_auth') === 'true';
  });
  const [currentUser, setCurrentUser] = useState(() => {
    const saved = localStorage.getItem('musky_user');
    if (saved) {
      try { return JSON.parse(saved); } catch { }
    }
    return {
      user_id: 'usr_admin',
      username: 'admin',
      full_name: 'System Administrator',
      department: 'Engineering & Technology',
      role: 'ADMIN',
    };
  });
  const [loginUsername, setLoginUsername] = useState('admin');
  const [loginPassword, setLoginPassword] = useState('admin123');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [currentWorkspaceFolder, setCurrentWorkspaceFolder] = useState<string | null>(null);
  const [folderInputModalOpen, setFolderInputModalOpen] = useState<boolean>(false);
  const [manualFolderPath, setManualFolderPath] = useState<string>('');

  // Backend System State
  const [backendOnline, setBackendOnline] = useState(false);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [models, setModels] = useState<WorkerModel[]>([]);
  const [modelMetrics, setModelMetrics] = useState<any>(null);

  // Chat history
  const [chats, setChats] = useState<ChatEntry[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  // ─── SOVEREIGN STUDIO (IDE) STATE ───
  const [ideFileTree, setIdeFileTree] = useState<IdeFileNode[]>([]);
  const [ideTabs, setIdeTabs] = useState<IdeTab[]>([
    {
      path: 'main.py',
      name: 'main.py',
      content: `# Sovereign Industrial Studio\n# Air-Gapped Python Environment (SIH26117)\n\ndef verify_plant_safety():\n    print("System active. Sovereign Kernel standing by.")\n    print("Air-Gapped Zero-Egress Enforced.")\n    return True\n\nif __name__ == '__main__':\n    verify_plant_safety()\n`,
      modified: false,
      language: 'python'
    }
  ]);
  const [activeIdeTabPath, setActiveIdeTabPath] = useState<string>('main.py');
  const [ideNewFileName, setIdeNewFileName] = useState<string>('');
  const [ideShowNewFileInput, setIdeShowNewFileInput] = useState<boolean>(false);
  const [ideAgentPrompt, setIdeAgentPrompt] = useState<string>('');
  const [ideAgentMessages, setIdeAgentMessages] = useState<{ role: 'user' | 'agent'; text: string; time: string }[]>([
    { role: 'agent', text: 'Sovereign Studio Copilot ready. Highlight code or ask to refactor, verify API 510 calculations, or inspect safety logic.', time: new Date().toLocaleTimeString() }
  ]);
  const [ideAgentBusy, setIdeAgentBusy] = useState<boolean>(false);
  const [ideBottomTab, setIdeBottomTab] = useState<'terminal' | 'problems' | 'output'>('terminal');
  const [ideTerminalOutput, setIdeTerminalOutput] = useState<string[]>([
    'Sovereign Studio Workspace v2.4 initialized',
    'Local Sovereign Kernel connected: 127.0.0.1:8088',
    'Type commands or click Run to execute.'
  ]);
  const [ideTerminalInput, setIdeTerminalInput] = useState<string>('');
  const [ideTerminalRunning, setIdeTerminalRunning] = useState<boolean>(false);
  const [ideActiveView, setIdeActiveView] = useState<'explorer' | 'agent'>('explorer');

  // ─── PROGRAMMIZ-STYLE SANDBOX STATE ───
  const [sandboxLanguage, setSandboxLanguage] = useState<string>('python');
  const [sandboxCode, setSandboxCode] = useState<string>(
    `# Sovereign Industrial Compiler (Programmiz Style)\n# Select language, modify code, and click Run.\n\nimport os\nimport sys\n\nprint(f"Executing in Sovereign Sandbox: {sys.version.split()[0]}")\nprint(f"Sandbox Directory: {os.getcwd()}")\n\n# Sample calculation: API 510 Remaining Wall Life\nt_actual = 12.5  # mm\nt_required = 8.0 # mm\ncorrosion_rate = 0.25 # mm/year\n\nremaining_life = (t_actual - t_required) / corrosion_rate\nprint(f"Calculated Equipment Remaining Life: {remaining_life:.1f} years")\n`
  );
  const [sandboxStdin, setSandboxStdin] = useState<string>('');
  const [sandboxOutput, setSandboxOutput] = useState<string[]>([]);
  const [sandboxRunning, setSandboxRunning] = useState<boolean>(false);
  const [sandboxExecutionTime, setSandboxExecutionTime] = useState<number | null>(null);
  const [sandboxExitCode, setSandboxExitCode] = useState<number | null>(null);

  // ─── PRESENTATION DATABASE EXPLORER STATE ───
  const [dbTables, setDbTables] = useState<string[]>([]);
  const [dbActiveTable, setDbActiveTable] = useState<string>('equipment');
  const [dbColumns, setDbColumns] = useState<string[]>([]);
  const [dbRows, setDbRows] = useState<any[]>([]);
  const [dbQueryText, setDbQueryText] = useState<string>('SELECT * FROM equipment LIMIT 20;');
  const [dbAnalytics, setDbAnalytics] = useState<any>(null);
  const [dbLoading, setDbLoading] = useState<boolean>(false);
  const [dbError, setDbError] = useState<string>('');

  // ─── EMPLOYEES STATE ───
  const [employeeList, setEmployeeList] = useState<any[]>([]);
  const [newEmpName, setNewEmpName] = useState('');
  const [newEmpUsername, setNewEmpUsername] = useState('');
  const [newEmpPassword, setNewEmpPassword] = useState('');
  const [newEmpDept, setNewEmpDept] = useState('CDU/VDU Operations');
  const [newEmpRole, setNewEmpRole] = useState('GRADE_1');
  const [empStatusMsg, setEmpStatusMsg] = useState('');

  // ─── AUDIT STATE ───
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // ─── REFINERY MACHINERY SIMULATION STATE ───
  const [machineryList, setMachineryList] = useState<any[]>([]);
  const [selectedMachineId, setSelectedMachineId] = useState<string>('PUMP_301A');
  const [machineVoiceCommand, setMachineVoiceCommand] = useState<string>('');
  const [machineAiLoading, setMachineAiLoading] = useState<boolean>(false);
  const [machineActionBanner, setMachineActionBanner] = useState<{
    type: 'success' | 'blocked' | 'info';
    title: string;
    description: string;
  } | null>(null);

  // ─── ARCHITECTURE & WORKFLOW DIAGRAM STATE ───
  const [architectureView, setArchitectureView] = useState<'system' | 'llm_layers' | 'workflow'>('system');

  // Settings
  const [maxTokens, setMaxTokens] = useState(2200);
  const [sandboxTimeout, setSandboxTimeout] = useState(30);

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    const t = setTimeout(scrollToBottom, 60);
    return () => clearTimeout(t);
  }, [messages, isExecuting]);

  // Ping backend
  useEffect(() => {
    const ping = async () => {
      try {
        const res = await fetch(`${API}/api/system/status`);
        const data = await res.json();
        setSystemStatus(data);
        if (data.active_user) setCurrentUser(data.active_user);
        setBackendOnline(true);
      } catch { setBackendOnline(false); setSystemStatus(null); }
    };
    ping();
    const iv = setInterval(ping, 8000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    if (activeTab === 'models') { fetchModels(); fetchMetrics(); }
    if (activeTab === 'chat') fetchChats();
    if (activeTab === 'ide') fetchIdeTree();
    if (activeTab === 'database') { fetchDbSchema(); fetchDbAnalytics(); }
    if (activeTab === 'employees') fetchEmployees();
    if (activeTab === 'audit') fetchAuditLogs();
    if (activeTab === 'machinery') fetchMachinery();
  }, [activeTab]);

  // Active Session Token State
  const [sessionId, setSessionId] = useState<string | null>(() => {
    return localStorage.getItem('musky_session_id');
  });

  // Helper to attach session authorization token to API requests
  const authHeaders = (extraHeaders: Record<string, string> = {}) => {
    const headers: Record<string, string> = { ...extraHeaders };
    if (sessionId) {
      headers['Authorization'] = `Bearer ${sessionId}`;
    }
    return headers;
  };

  // ─── Compulsory Login & Logout Handlers ───
  const handleLoginSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    try {
      const r = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: loginUsername.trim(),
          password: loginPassword.trim()
        })
      });
      const d = await r.json();
      if (d.success && d.user) {
        setCurrentUser(d.user);
        if (d.session_id) {
          setSessionId(d.session_id);
          localStorage.setItem('musky_session_id', d.session_id);
        }
        setIsAuthenticated(true);
        localStorage.setItem('musky_auth', 'true');
        localStorage.setItem('musky_user', JSON.stringify(d.user));
        setMessages(prev => [...prev, {
          id: Math.random().toString(36).substr(2, 9),
          sender: 'system',
          text: `Welcome, ${d.user.full_name}. Clearance granted: ${d.user.role} (${d.user.department}).`,
          timestamp: new Date().toLocaleTimeString()
        }]);
      } else {
        setLoginError(d.error || 'Invalid credentials. Please check your username and password.');
      }
    } catch (err: any) {
      setLoginError(`Connection error: ${err.message}`);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleQuickDemoLogin = (user: string, pass: string) => {
    setLoginUsername(user);
    setLoginPassword(pass);
    setLoginError('');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setSessionId(null);
    localStorage.removeItem('musky_auth');
    localStorage.removeItem('musky_user');
    localStorage.removeItem('musky_session_id');
    setActiveTab('home');
  };

  const fetchModels = async () => { try { const r = await fetch(`${API}/api/models`, { headers: authHeaders() }); const d = await r.json(); setModels(d.models || []); } catch { setModels([]); } };
  const fetchMetrics = async () => { try { const r = await fetch(`${API}/api/models/metrics`, { headers: authHeaders() }); const d = await r.json(); setModelMetrics(d.metrics || null); } catch { setModelMetrics(null); } };
  const fetchChats = async () => { try { const r = await fetch(`${API}/api/chat/list`, { headers: authHeaders() }); const d = await r.json(); setChats(d.chats || []); } catch { setChats([]); } };
  const fetchEmployees = async () => { try { const r = await fetch(`${API}/api/employees`, { headers: authHeaders() }); const d = await r.json(); setEmployeeList(d.employees || []); } catch { setEmployeeList([]); } };
  const fetchAuditLogs = async () => { try { const r = await fetch(`${API}/api/audit/logs`, { headers: authHeaders() }); const d = await r.json(); setAuditLogs(d.logs || []); } catch { setAuditLogs([]); } };

  // ─── Clearance Switcher ───
  const switchClearance = async (role: string) => {
    try {
      const r = await fetch(`${API}/api/auth/switch_role`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ role })
      });
      const d = await r.json();
      if (d.user) {
        setCurrentUser(d.user);
        if (d.session_id) {
          setSessionId(d.session_id);
          localStorage.setItem('musky_session_id', d.session_id);
        }
        localStorage.setItem('musky_user', JSON.stringify(d.user));
        setMessages(prev => [...prev, {
          id: Math.random().toString(36).substr(2, 9),
          sender: 'system',
          text: `Role clearance updated to: ${d.user.role} (${d.user.full_name}, ${d.user.department})`,
          timestamp: new Date().toLocaleTimeString()
        }]);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  // ─── Attachments Handling ───
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const base64Data = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = (err) => reject(err);
        reader.readAsDataURL(file);
      });

      const r = await fetch(`${API}/api/chat/upload`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          filename: file.name,
          base64_data: base64Data
        })
      });

      if (!r.ok) {
        const errData = await r.json().catch(() => ({ detail: r.statusText }));
        throw new Error(errData.detail || `Server returned ${r.status}`);
      }

      const d = await r.json();
      if (d.status === 'ok') {
        setCurrentAttachment({
          name: d.name,
          path: d.path,
          type: d.type,
          size: d.size
        });
      }
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const attachSampleDb = () => {
    setCurrentAttachment({
      name: 'industrial_demo.db',
      path: 'data/demo_db/industrial_demo.db',
      type: 'database',
    });
  };

  // ─── Chat Actions ───
  const handleSend = async () => {
    if ((!input.trim() && !currentAttachment) || isExecuting) return;
    const msg = input.trim() || (currentAttachment ? `Analyze attached ${currentAttachment.type}: ${currentAttachment.name}` : '');
    const attachedFile = currentAttachment;

    setInput('');
    setCurrentAttachment(null);
    setIsExecuting(true);

    setMessages(prev => [...prev, {
      id: Math.random().toString(36).substr(2, 9),
      sender: 'user',
      text: msg,
      timestamp: new Date().toLocaleTimeString(),
      attachment: attachedFile ? { name: attachedFile.name, path: attachedFile.path, type: attachedFile.type } : undefined
    }]);

    try {
      const r = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          chat_id: currentChatId,
          attachment_path: attachedFile?.path,
          attachment_name: attachedFile?.name,
          attachment_type: attachedFile?.type,
          user_role: currentUser.role
        })
      });
      const d = await r.json();
      if (d.chat_id) setCurrentChatId(d.chat_id);

      setMessages(prev => [...prev, {
        id: Math.random().toString(36).substr(2, 9),
        sender: 'assistant',
        text: d.answer || d.error || 'No response.',
        timestamp: new Date().toLocaleTimeString()
      }]);
      fetchChats();
    } catch (e: any) {
      setMessages(prev => [...prev, {
        id: Math.random().toString(36).substr(2, 9),
        sender: 'system',
        text: `Connection Error: ${e.message}`,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsExecuting(false);
      fetchChats();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const newChat = () => {
    setCurrentChatId(null);
    setMessages([{ id: 'new', sender: 'system', text: 'New conversation initialized under active clearance.', timestamp: new Date().toLocaleTimeString() }]);
  };

  const openChat = async (chatId: string) => {
    setCurrentChatId(chatId);
    try {
      const r = await fetch(`${API}/api/chat/history/${chatId}`);
      const d = await r.json();
      const hist = (d.history || []).map((m: any, i: number) => ({
        id: `h_${i}`, sender: m.role === 'user' ? 'user' as const : 'assistant' as const, text: m.content, timestamp: m.timestamp || '',
      }));
      setMessages(hist.length > 0 ? hist : [{ id: 'empty', sender: 'system', text: 'No messages in this conversation.', timestamp: '' }]);
    } catch { setMessages([{ id: 'err', sender: 'system', text: 'Could not load chat history.', timestamp: '' }]); }
  };

  // ─── SOVEREIGN STUDIO (IDE) HELPERS ───
  const fetchIdeTree = async (customPath?: string) => {
    try {
      const targetPath = customPath !== undefined ? customPath : currentWorkspaceFolder;
      const url = targetPath ? `${API}/api/files/tree?folder_path=${encodeURIComponent(targetPath)}` : `${API}/api/files/tree`;
      const r = await fetch(url);
      const d = await r.json();
      setIdeFileTree(d.tree || []);
      if (d.root) {
        setIdeTerminalOutput(prev => [...prev, `[Sovereign Studio] Active Workspace: ${d.root}`]);
      }
    } catch { setIdeFileTree([]); }
  };

  const handleOpenFolder = async () => {
    try {
      const el = getElectron();
      if (el?.openFolder) {
        const folder = await el.openFolder();
        if (folder) {
          setCurrentWorkspaceFolder(folder);
          fetchIdeTree(folder);
          setIdeTerminalOutput(prev => [...prev, `[Workspace Opened] ${folder}`]);
          return;
        }
      }
      // If electronAPI not available or cancelled, open fallback prompt modal
      setFolderInputModalOpen(true);
    } catch (e: any) {
      setFolderInputModalOpen(true);
    }
  };

  const handleApplyManualFolder = () => {
    if (!manualFolderPath.trim()) return;
    const folder = manualFolderPath.trim().replace(/\\/g, '/');
    setCurrentWorkspaceFolder(folder);
    fetchIdeTree(folder);
    setFolderInputModalOpen(false);
    setManualFolderPath('');
    setIdeTerminalOutput(prev => [...prev, `[Workspace Opened] ${folder}`]);
  };

  const handleResetToDefaultWorkspace = () => {
    setCurrentWorkspaceFolder(null);
    fetchIdeTree('');
    setIdeTerminalOutput(prev => [...prev, `[Workspace Reset to Default Root]`]);
  };

  const openIdeFile = async (path: string, name: string) => {
    const existing = ideTabs.find(t => t.path === path);
    if (existing) {
      setActiveIdeTabPath(path);
      return;
    }
    try {
      const r = await fetch(`${API}/api/files/read`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ path })
      });
      const d = await r.json();
      const content = d.content || '';
      const ext = name.split('.').pop() || '';
      const lang = ext === 'py' ? 'python' : ext === 'js' || ext === 'ts' || ext === 'jsx' || ext === 'tsx' ? 'javascript' : ext === 'html' ? 'html' : ext === 'css' ? 'css' : ext === 'json' ? 'json' : ext === 'sql' ? 'sql' : 'plaintext';
      const newTab: IdeTab = { path, name, content, modified: false, language: lang };
      setIdeTabs(prev => [...prev, newTab]);
      setActiveIdeTabPath(path);
      setIdeTerminalOutput(prev => [...prev, `[Sovereign Studio] Opened ${name}`]);
    } catch (e: any) {
      setIdeTerminalOutput(prev => [...prev, `[Error opening ${name}]: ${e.message}`]);
    }
  };

  const closeIdeTab = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const remaining = ideTabs.filter(t => t.path !== path);
    if (remaining.length === 0) {
      setIdeTabs([{ path: 'untitled.py', name: 'untitled.py', content: '# New file\n', modified: false, language: 'python' }]);
      setActiveIdeTabPath('untitled.py');
    } else {
      setIdeTabs(remaining);
      if (activeIdeTabPath === path) setActiveIdeTabPath(remaining[remaining.length - 1].path);
    }
  };

  const saveCurrentIdeFile = async () => {
    const currentTab = ideTabs.find(t => t.path === activeIdeTabPath);
    if (!currentTab) return;
    try {
      const r = await fetch(`${API}/api/files/write`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ path: currentTab.path, content: currentTab.content })
      });
      const d = await r.json();
      if (!r.ok) {
        setIdeTerminalOutput(prev => [...prev, `✗ [Save Failed]: ${d.error || 'Permission Denied'}`]);
        return;
      }
      setIdeTabs(prev => prev.map(t => t.path === activeIdeTabPath ? { ...t, modified: false } : t));
      setIdeTerminalOutput(prev => [...prev, `✓ [Saved] ${currentTab.name} (${currentTab.content.length} bytes)`]);
    } catch (e: any) {
      setIdeTerminalOutput(prev => [...prev, `✗ [Save Failed]: ${e.message}`]);
    }
  };

  const createIdeFile = async () => {
    if (!ideNewFileName.trim()) return;
    const cleanPath = ideNewFileName.trim().replace(/\\/g, '/');
    try {
      const r = await fetch(`${API}/api/files/create`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ path: cleanPath, content: `# New file: ${cleanPath}\n` })
      });
      if (!r.ok) {
        const err = await r.json();
        alert(err.error || 'Failed to create file');
        return;
      }
      setIdeNewFileName('');
      setIdeShowNewFileInput(false);
      fetchIdeTree();
      openIdeFile(cleanPath, cleanPath.split('/').pop() || cleanPath);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const runIdeCurrent = async () => {
    const currentTab = ideTabs.find(t => t.path === activeIdeTabPath);
    if (!currentTab) return;
    setIdeBottomTab('terminal');
    setIdeTerminalOutput(prev => [...prev, `$ execute ${currentTab.name}`, 'Dispatching to isolated local sandbox...']);
    try {
      const r = await fetch(`${API}/api/sandbox/exec`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ code: currentTab.content, timeout: sandboxTimeout, language: currentTab.language })
      });
      const d = await r.json();
      if (d.stdout) setIdeTerminalOutput(prev => [...prev, d.stdout]);
      if (d.stderr) setIdeTerminalOutput(prev => [...prev, `stderr: ${d.stderr}`]);
      setIdeTerminalOutput(prev => [...prev, d.success ? `✓ [Process completed with exit code 0]` : `✗ [Process exit code: ${d.returncode}]`]);
    } catch (e: any) {
      setIdeTerminalOutput(prev => [...prev, `Execution Error: ${e.message}`]);
    }
  };

  const executeTerminalCommand = async () => {
    if (!ideTerminalInput.trim() || ideTerminalRunning) return;
    const cmd = ideTerminalInput.trim();
    setIdeTerminalInput('');
    setIdeTerminalRunning(true);
    setIdeTerminalOutput(prev => [...prev, `$ ${cmd}`]);

    try {
      const r = await fetch(`${API}/api/terminal/run`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ command: cmd })
      });
      const d = await r.json();
      if (d.stdout) setIdeTerminalOutput(prev => [...prev, d.stdout]);
      if (d.stderr) setIdeTerminalOutput(prev => [...prev, d.stderr]);
      setIdeTerminalOutput(prev => [...prev, `[Exit Code: ${d.returncode}]`]);
    } catch (e: any) {
      setIdeTerminalOutput(prev => [...prev, `Terminal Error: ${e.message}`]);
    } finally {
      setIdeTerminalRunning(false);
    }
  };

  const handleIdeAgentSend = async () => {
    if (!ideAgentPrompt.trim() || ideAgentBusy) return;
    const promptText = ideAgentPrompt;
    setIdeAgentPrompt('');
    setIdeAgentBusy(true);
    setIdeAgentMessages(prev => [...prev, { role: 'user', text: promptText, time: new Date().toLocaleTimeString() }]);

    const currentTab = ideTabs.find(t => t.path === activeIdeTabPath);
    const contextualPrompt = `You are the Sovereign Studio Copilot pair-programmer in the IDE.\nActive File: ${currentTab?.name || 'unknown'}\nCode Context:\n\`\`\`${currentTab?.language || 'python'}\n${(currentTab?.content || '').slice(0, 3000)}\n\`\`\`\n\nUser Instruction: ${promptText}\n\nProvide direct, actionable code recommendations, explanations, or refactored functions.`;

    try {
      const r = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ message: contextualPrompt, user_role: currentUser.role })
      });
      const d = await r.json();
      setIdeAgentMessages(prev => [...prev, {
        role: 'agent',
        text: d.answer || 'Response completed.',
        time: new Date().toLocaleTimeString()
      }]);
    } catch (e: any) {
      setIdeAgentMessages(prev => [...prev, {
        role: 'agent',
        text: `Error connecting to local agent: ${e.message}`,
        time: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIdeAgentBusy(false);
    }
  };

  // ─── PROGRAMMIZ-STYLE SANDBOX COMPILER HELPERS ───
  const runProgrammizCompiler = async () => {
    setSandboxRunning(true);
    const startTime = performance.now();
    setSandboxOutput(prev => [...prev, `▶ Compiling & Executing ${sandboxLanguage.toUpperCase()}...`]);
    try {
      const r = await fetch(`${API}/api/sandbox/exec`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          code: sandboxCode,
          language: sandboxLanguage,
          timeout: sandboxTimeout,
          stdin: sandboxStdin
        })
      });
      const d = await r.json();
      const elapsed = Math.round(performance.now() - startTime);
      setSandboxExecutionTime(elapsed);
      setSandboxExitCode(d.returncode !== undefined ? d.returncode : (d.success ? 0 : 1));

      if (d.stdout) setSandboxOutput(prev => [...prev, d.stdout]);
      if (d.stderr) setSandboxOutput(prev => [...prev, `[stderr]\n${d.stderr}`]);
      setSandboxOutput(prev => [...prev, d.success ? `✓ Execution finished in ${elapsed}ms (exit code 0)` : `✗ Process terminated with exit code ${d.returncode}`]);
    } catch (e: any) {
      setSandboxOutput(prev => [...prev, `Sandbox execution error: ${e.message}`]);
      setSandboxExitCode(1);
    } finally {
      setSandboxRunning(false);
    }
  };

  const loadSandboxTemplate = (lang: string) => {
    setSandboxLanguage(lang);
    if (lang === 'python') {
      setSandboxCode(`# Python 3 Industrial Compiler\ndef calculate_equipment_stress(pressure_bar, diameter_mm, thickness_mm):\n    # Hoop stress calculation: sigma = (P * D) / (2 * t)\n    stress = (pressure_bar * 0.1 * diameter_mm) / (2 * thickness_mm)\n    return stress\n\nstress = calculate_equipment_stress(pressure_bar=35.0, diameter_mm=1200, thickness_mm=14.5)\nprint(f"Calculated Circumferential Hoop Stress: {stress:.2f} MPa")\nprint("API 510 Integrity Assessment: PASS [Safe Operating Margin: +38%]")\n`);
    } else if (lang === 'sql') {
      setSandboxCode(`-- SQLite Presentation Database Query\nSELECT tag, equipment_type, unit, status, design_pressure, last_inspection_date\nFROM equipment\nWHERE status = 'OPERATIONAL'\nORDER BY design_pressure DESC\nLIMIT 10;\n`);
    } else if (lang === 'javascript') {
      setSandboxCode(`// Modern Node.js Execution Sandbox\nconst sensorReadings = [142.3, 144.1, 145.8, 143.2, 146.0];\nconst avg = sensorReadings.reduce((a, b) => a + b, 0) / sensorReadings.length;\nconsole.log(\`[Telemetry Engine] Stream Samples Processed: \${sensorReadings.length}\`);\nconsole.log(\`[Telemetry Engine] Average Reactor Core Temp: \${avg.toFixed(2)} °C\`);\nconsole.log(\`[Telemetry Engine] Status: NORMAL OPERATIONAL RANGE\`);\n`);
    } else if (lang === 'typescript') {
      setSandboxCode(`// TypeScript Industrial Type Safe Engine\ninterface TelemetryPoint {\n  sensorId: string;\n  pressureBar: number;\n  tempC: number;\n  safe: boolean;\n}\n\nconst data: TelemetryPoint = {\n  sensorId: "PT-104-ALPHA",\n  pressureBar: 34.2,\n  tempC: 178.5,\n  safe: true\n};\n\nconsole.log(\`Telemetry verified for \${data.sensorId}: Pressure=\${data.pressureBar} bar, Temp=\${data.tempC} C (Safe: \${data.safe})\`);\n`);
    } else if (lang === 'c') {
      setSandboxCode(`/* C Industrial Compute Kernel */\n#include <stdio.h>\n\nint main() {\n    double actual_thickness = 14.50; // mm\n    double min_thickness = 8.00;    // mm\n    double corrosion_rate = 0.22;   // mm/year\n    \n    double remaining_life = (actual_thickness - min_thickness) / corrosion_rate;\n    printf("=========================================\\n");\n    printf(" INDUSTRIAL SAFETY KERNEL (C99)\\n");\n    printf(" Remaining Service Life: %.2f years\\n", remaining_life);\n    printf(" Re-inspection Interval: %.2f years\\n", remaining_life / 2.0);\n    printf("=========================================\\n");\n    return 0;\n}\n`);
    } else if (lang === 'cpp') {
      setSandboxCode(`// C++ Industrial Safety & Reliability Engine\n#include <iostream>\n#include <vector>\n#include <numeric>\n\nint main() {\n    std::vector<double> vibrations = { 1.2, 1.4, 1.1, 1.3, 1.5 };\n    double sum = std::accumulate(vibrations.begin(), vibrations.end(), 0.0);\n    double mean = sum / vibrations.size();\n    \n    std::cout << ">>> Industrial Pump Vibration Analysis (C++) <<<" << std::endl;\n    std::cout << "Mean Vibration Amplitude: " << mean << " mm/s RMS" << std::endl;\n    std::cout << "ISO 10816-3 Evaluation: Class I/II Rigid (SATISFACTORY)" << std::endl;\n    return 0;\n}\n`);
    } else if (lang === 'bash') {
      setSandboxCode(`# Shell / PowerShell Industrial Automation Script\necho "=== SOVEREIGN WORKBENCH SCRIPT RUNNER ==="\necho "Runtime Environment: Local Air-Gapped Kernel"\necho "Date & Time: $(date 2>/dev/null || Get-Date)"\necho "Active User Context: Validated"\necho "Workspace Verification: Complete"\n`);
    } else if (lang === 'html') {
      setSandboxCode(`<!DOCTYPE html>\n<html>\n<head>\n  <meta charset="utf-8">\n  <title>Refinery Telemetry Widget</title>\n  <style>\n    body { font-family: -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 24px; }\n    .card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; }\n    .val { font-size: 32px; font-weight: bold; color: #38bdf8; }\n    .badge { background: #10b981; color: white; padding: 4px 8px; border-radius: 6px; font-size: 11px; }\n  </style>\n</head>\n<body>\n  <div class="card">\n    <div style="display:flex; justify-content:space-between; align-items:center;">\n      <h3>Crude Distillation Unit (CDU-1)</h3>\n      <span class="badge">NORMAL</span>\n    </div>\n    <div class="val">142.8 °C</div>\n    <p style="color:#94a3b8; font-size:12px;">Top Column Pressure: 2.14 bar | Flow: 450 m³/h</p>\n  </div>\n</body>\n</html>\n`);
    }
  };

  // ─── PRESENTATION DATABASE HELPERS ───
  const fetchDbSchema = async () => {
    setDbLoading(true);
    setDbError('');
    try {
      const r = await fetch(`${API}/api/db/demo/schema`);
      const d = await r.json();
      setDbTables(d.tables || []);
      if (d.tables?.length > 0 && !dbActiveTable) {
        setDbActiveTable(d.tables[0]);
      }
      queryTable(dbActiveTable || d.tables[0]);
    } catch (e: any) {
      setDbError(e.message);
    } finally {
      setDbLoading(false);
    }
  };

  const fetchDbAnalytics = async () => {
    try {
      const r = await fetch(`${API}/api/db/demo/analytics`);
      const d = await r.json();
      setDbAnalytics(d);
    } catch { }
  };

  const queryTable = async (tableName: string) => {
    setDbActiveTable(tableName);
    const sql = `SELECT * FROM ${tableName} LIMIT 25;`;
    setDbQueryText(sql);
    executeCustomQuery(sql);
  };

  const executeCustomQuery = async (customSql?: string) => {
    const q = customSql || dbQueryText;
    setDbLoading(true);
    setDbError('');
    try {
      const r = await fetch(`${API}/api/db/demo/query`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ query: q })
      });
      const d = await r.json();
      if (!r.ok) {
        setDbError(d.error || 'Query failed');
        setDbColumns([]);
        setDbRows([]);
      } else {
        setDbColumns(d.columns || []);
        setDbRows(d.rows || []);
      }
    } catch (e: any) {
      setDbError(e.message);
    } finally {
      setDbLoading(false);
    }
  };

  // ─── EMPLOYEE REGISTRATION ───
  const handleCreateEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmpName || !newEmpUsername || !newEmpPassword) {
      setEmpStatusMsg('Please complete all required fields.');
      return;
    }
    try {
      const r = await fetch(`${API}/api/employees/create`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          full_name: newEmpName,
          username: newEmpUsername,
          password: newEmpPassword,
          department: newEmpDept,
          role: newEmpRole
        })
      });
      const d = await r.json();
      if (r.ok) {
        setEmpStatusMsg(`✓ Successfully registered employee: ${newEmpUsername} (${newEmpRole})`);
        setNewEmpName('');
        setNewEmpUsername('');
        setNewEmpPassword('');
        fetchEmployees();
      } else {
        setEmpStatusMsg(`✗ Error: ${d.error || 'Failed to create employee'}`);
      }
    } catch (e: any) {
      setEmpStatusMsg(`✗ Error: ${e.message}`);
    }
  };

  // ─── REFINERY MACHINERY SIMULATION ACTIONS ───
  const fetchMachinery = async () => {
    try {
      const r = await fetch(`${API}/api/machinery/status`, {
        headers: authHeaders()
      });
      if (r.ok) {
        const d = await r.json();
        setMachineryList(d.machinery || []);
      }
    } catch {}
  };

  const handleMachineControl = async (machineId: string, action: string, cmdText?: string) => {
    setMachineAiLoading(true);
    setMachineActionBanner(null);
    try {
      const r = await fetch(`${API}/api/machinery/control`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          machine_id: machineId,
          action: action,
          command_text: cmdText || `AI Prompt: "${action} machine ${machineId}"`
        })
      });
      const d = await r.json();
      if (r.ok && d.success) {
        setMachineActionBanner({
          type: 'success',
          title: 'Central Policy Engine: GRANTED',
          description: d.message || `Machine ${machineId} transitioned to ${action}.`
        });
        fetchMachinery();
      } else {
        setMachineActionBanner({
          type: 'blocked',
          title: 'Central Policy Engine: BLOCKED (Default-Deny)',
          description: d.message || d.reason || 'Insufficient role clearance for machine override.'
        });
      }
    } catch (e: any) {
      setMachineActionBanner({
        type: 'blocked',
        title: 'Communication Failure',
        description: e.message
      });
    } finally {
      setMachineAiLoading(false);
    }
  };

  const handleVoiceAiCommand = (e: React.FormEvent) => {
    e.preventDefault();
    if (!machineVoiceCommand.trim()) return;
    const text = machineVoiceCommand.toLowerCase();

    // Determine target machine
    let targetId = selectedMachineId;
    if (text.includes('pump') || text.includes('301')) targetId = 'PUMP_301A';
    else if (text.includes('compressor') || text.includes('h2') || text.includes('102')) targetId = 'COMPRESSOR_102';
    else if (text.includes('blower') || text.includes('furnace') || text.includes('401')) targetId = 'FURNACE_BLOWER_401';
    else if (text.includes('turbine') || text.includes('fcc') || text.includes('205') || text.includes('expander')) targetId = 'EXPANDER_TURBINE_205';

    // Determine action
    let action = 'STOP';
    if (text.includes('emergency') || text.includes('shutdown') || text.includes('trip')) {
      action = 'EMERGENCY_SHUTDOWN';
    } else if (text.includes('stop') || text.includes('halt') || text.includes('ruk') || text.includes('roko')) {
      action = 'STOP';
    } else if (text.includes('start') || text.includes('resume') || text.includes('chalu') || text.includes('chalao')) {
      action = 'START';
    } else if (text.includes('throttle') || text.includes('slow') || text.includes('dheere')) {
      action = 'THROTTLE';
    }

    handleMachineControl(targetId, action, `Spoken/AI Command: "${machineVoiceCommand}"`);
    setMachineVoiceCommand('');
  };

  const navItems = [
    { key: 'home', icon: Compass, label: 'Overview' },
    { key: 'chat', icon: MessageSquare, label: 'AI Chat' },
    { key: 'machinery', icon: Gauge, label: 'Refinery Machinery' },
    { key: 'ide', icon: Code2, label: 'Sovereign Studio' },
    { key: 'database', icon: Table, label: 'Database & Analytics' },
    { key: 'employees', icon: Users, label: 'Employees & RBAC' },
    { key: 'audit', icon: ClipboardList, label: 'Audit Trail' },
    { key: 'models', icon: Database, label: 'Models & VRAM' },
    { key: 'settings', icon: Settings, label: 'Settings' },
  ];

  // Compulsory Sequential Login Gateway: unauthenticated users cannot enter without logging in
  if (!isAuthenticated) {
    return (
      <div className="flex h-screen w-screen bg-slate-50 text-slate-800 font-sans overflow-hidden select-none relative items-center justify-center p-4">
        <div className="animated-bg"></div>

        {/* Top Header bar on login screen with window controls */}
        <div className="absolute top-0 left-0 right-0 h-11 flex items-center justify-between px-6 z-30" style={{ WebkitAppRegion: 'drag' } as any}>
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/25">
              <span className="font-cursive text-lg font-black leading-none pb-0.5">M</span>
            </div>
            <span className="font-cursive text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-pink-500">Musky.AI</span>
          </div>
          <div style={{ WebkitAppRegion: 'no-drag' } as any}>
            <WindowControls />
          </div>
        </div>

        {/* Sequential Central Login Card */}
        <div className="max-w-md w-full glass-panel p-8 shadow-2xl relative z-20 border border-slate-200/80 rounded-2xl">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30 mx-auto mb-3">
              <span className="font-cursive text-3xl font-black">M</span>
            </div>
            <h1 className="font-cursive text-3xl font-bold text-slate-800">Musky.AI</h1>
            <p className="text-xs font-medium text-slate-500 mt-1">Sovereign Industrial AI Workbench · Air-Gapped</p>
            <div className="mt-2.5 inline-flex items-center space-x-1.5 px-3 py-0.5 rounded-full bg-indigo-50 border border-indigo-200/60 text-indigo-700 text-[11px] font-semibold">
              <Shield className="w-3 h-3 text-indigo-600" />
              <span>Role-Based Access Control (RBAC) Enforced</span>
            </div>
          </div>

          {loginError && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{loginError}</span>
            </div>
          )}

          {/* Sequential Credentials Form */}
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block mb-1.5">
                Staff Identity / Username
              </label>
              <input
                type="text"
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                placeholder="e.g. admin, engineer_202, operator_101"
                className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-800 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all font-medium"
                required
              />
            </div>

            <div>
              <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block mb-1.5">
                Security Passcode
              </label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="Enter authorized password"
                className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-800 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all font-medium"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loginLoading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-bold text-xs shadow-md shadow-indigo-500/25 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
            >
              {loginLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Clearance...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In to Sovereign Workbench</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-5 border-t border-slate-200/70">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider text-center mb-2.5">
              Quick Switch Demo Roles
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('admin', 'admin123')}
                className="p-2 rounded-lg bg-indigo-50/70 hover:bg-indigo-100 text-indigo-900 border border-indigo-200/60 text-center transition-colors cursor-pointer"
              >
                <div className="text-[10px] font-bold">Admin</div>
                <div className="text-[8px] text-indigo-500 font-mono">admin123</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('engineer_202', 'demo123')}
                className="p-2 rounded-lg bg-sky-50/70 hover:bg-sky-100 text-sky-900 border border-sky-200/60 text-center transition-colors cursor-pointer"
              >
                <div className="text-[10px] font-bold">Engineer</div>
                <div className="text-[8px] text-sky-500 font-mono">demo123</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('operator_101', 'demo123')}
                className="p-2 rounded-lg bg-emerald-50/70 hover:bg-emerald-100 text-emerald-900 border border-emerald-200/60 text-center transition-colors cursor-pointer"
              >
                <div className="text-[10px] font-bold">Operator</div>
                <div className="text-[8px] text-emerald-500 font-mono">demo123</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-screen bg-transparent text-slate-800 font-sans overflow-hidden select-none relative">
      <div className="animated-bg"></div>

      {/* Hidden File Upload Input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
        accept="image/*,.db,.sqlite,.sqlite3,.csv,.xlsx,.xls,.pdf,.doc,.docx,.txt,.md,.py,.sql,.json"
      />

      {/* Sidebar Navigation */}
      <nav className="w-[58px] glass-nav flex flex-col items-center py-4 z-20 space-y-1 shrink-0 border-r border-slate-200/60 shadow-xs">
        <div className="mb-4 flex flex-col items-center cursor-pointer" onClick={() => setActiveTab('home')} title="Musky.AI Home">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/25">
            <span className="font-cursive text-2xl font-black leading-none pb-0.5">M</span>
          </div>
        </div>

        {navItems.map(item => (
          <button
            key={item.key}
            onClick={() => setActiveTab(item.key)}
            className={`p-2.5 rounded-xl transition-all cursor-pointer relative group ${activeTab === item.key
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20 scale-105'
                : 'text-slate-400 hover:text-indigo-600 hover:bg-slate-100/60'
              }`}
            title={item.label}
          >
            <item.icon className="w-5 h-5" />
            <span className="absolute left-16 bg-slate-900 text-white text-[11px] font-medium px-2 py-1 rounded shadow-md whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
              {item.label}
            </span>
          </button>
        ))}

        <div className="mt-auto flex flex-col items-center space-y-2">
          <button
            onClick={() => switchClearance(currentUser.role === 'ADMIN' ? 'GRADE_1' : currentUser.role === 'GRADE_1' ? 'GRADE_2' : currentUser.role === 'GRADE_2' ? 'GRADE_3' : 'ADMIN')}
            className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-indigo-50 text-indigo-700 flex items-center justify-center text-[10px] font-bold border border-slate-200"
            title={`Active Role: ${currentUser.role}. Click to quick-cycle.`}
          >
            {currentUser.role.replace('GRADE_', 'G')}
          </button>
          <div className={`w-2.5 h-2.5 rounded-full ${backendOnline ? 'bg-emerald-500 ring-4 ring-emerald-100' : 'bg-red-400 ring-4 ring-red-100'}`} title={backendOnline ? 'Sovereign Kernel Online' : 'Kernel Offline'} />
        </div>
      </nav>

      {/* Main Workspace Area */}
      <main className="flex-1 flex flex-col relative z-10 h-full overflow-hidden">
        {/* Modern Top Header / Title Bar */}
        <div className="h-11 w-full glass-header flex items-center justify-between px-4 border-b border-slate-200/50 shrink-0" style={{ WebkitAppRegion: 'drag' } as any}>
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-2">
              <span className="font-cursive text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-pink-500">Musky.AI</span>
              <span className="text-[10px] text-slate-400 font-normal">/</span>
              <span className="text-xs text-slate-600 font-semibold tracking-wide uppercase">{navItems.find(n => n.key === activeTab)?.label}</span>
            </span>

            {/* Role Clearance Pill & Selector */}
            <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50/80 border border-indigo-200/60" style={{ WebkitAppRegion: 'no-drag' } as any}>
              <Shield className="w-3.5 h-3.5 text-indigo-600" />
              <span className="text-[10px] font-bold text-indigo-900 tracking-wide">{currentUser.role}</span>
              <span className="text-[9px] text-indigo-400">({currentUser.username})</span>
              <select
                value={currentUser.role}
                onChange={(e) => switchClearance(e.target.value)}
                className="text-[10px] bg-transparent text-indigo-800 font-semibold outline-none cursor-pointer pl-1"
                title="Switch Authorization Clearance"
              >
                <option value="ADMIN">ADMIN (Full Governance)</option>
                <option value="GRADE_3">GRADE 3 (Superintendent)</option>
                <option value="GRADE_2">GRADE 2 (Engineer)</option>
                <option value="GRADE_1">GRADE 1 (Operator/Read-Only)</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-3" style={{ WebkitAppRegion: 'no-drag' } as any}>
            {backendOnline ? (
              <span className="flex items-center space-x-1.5 text-emerald-600 text-[11px] font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/50">
                <Wifi className="w-3 h-3" />
                <span>Air-Gapped</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-red-500 text-[11px] font-semibold">
                <WifiOff className="w-3 h-3" />
                <span>Kernel Offline</span>
              </span>
            )}

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-600 border border-slate-200 text-xs font-semibold transition-colors cursor-pointer"
              title="Sign Out / Lock Session"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Logout</span>
            </button>

            <WindowControls />
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════════
            1. HOME / OVERVIEW (Filled, Minimal & Aesthetic)
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'home' && (
          <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-6xl mx-auto w-full space-y-6">
            {/* Hero Welcome Banner */}
            <div className="glass-panel p-8 relative overflow-hidden rounded-3xl border border-white/60 bg-gradient-to-br from-white/95 via-indigo-50/40 to-pink-50/20 shadow-lg shadow-indigo-100/40 backdrop-blur-2xl">
              {/* Subtle Ambient Glow */}
              <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-gradient-to-br from-indigo-300/20 to-pink-300/20 blur-3xl pointer-events-none" />
              <div className="absolute bottom-0 left-1/3 -mb-12 w-64 h-64 rounded-full bg-sky-200/20 blur-2xl pointer-events-none" />

              <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="max-w-2xl space-y-3">
                  <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-100/70 border border-indigo-200/50 text-indigo-700 text-xs font-semibold shadow-xs">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-600 animate-pulse" />
                    <span className="font-medium">SIH26117 · Air-Gapped Sovereign AI System</span>
                  </div>

                  <div className="space-y-1">
                    <h1 className="text-3xl sm:text-4xl font-black text-slate-800 tracking-tight flex items-baseline gap-2.5 flex-wrap">
                      <span>Welcome to</span>
                      <span className="font-cursive text-4xl sm:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 pr-1">
                        Musky.AI
                      </span>
                    </h1>
                    <p className="text-sm font-medium text-indigo-950/70">
                      Sovereign Industrial AI Workbench for On-Premise Industrial Engineering
                    </p>
                  </div>

                  <p className="text-xs sm:text-sm text-slate-500 leading-relaxed max-w-xl">
                    Zero cloud egress, on-premise execution engineered for high-criticality refining infrastructure. Powered by verifiable cryptographic audits, multimodal vision inspection, and role-governed policy sandboxing.
                  </p>

                  <div className="pt-2 flex flex-wrap items-center gap-3">
                    <button
                      onClick={() => setActiveTab('chat')}
                      className="group px-5 py-2.5 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-semibold flex items-center space-x-2 shadow-md shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
                    >
                      <MessageSquare className="w-4 h-4 transition-transform group-hover:-translate-y-0.5" />
                      <span>Start Sovereign Chat</span>
                    </button>
                    <button
                      onClick={() => { setActiveTab('chat'); attachSampleDb(); }}
                      className="px-4 py-2.5 rounded-2xl bg-white/90 hover:bg-white text-slate-700 hover:text-indigo-600 text-xs font-semibold flex items-center space-x-2 border border-slate-200/70 shadow-xs hover:border-indigo-300 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
                    >
                      <Database className="w-4 h-4 text-indigo-600" />
                      <span>Attach Industrial DB</span>
                    </button>
                    <button
                      onClick={() => setActiveTab('ide')}
                      className="px-4 py-2.5 rounded-2xl bg-white/90 hover:bg-white text-slate-700 hover:text-emerald-600 text-xs font-semibold flex items-center space-x-2 border border-slate-200/70 shadow-xs hover:border-emerald-300 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
                    >
                      <Code2 className="w-4 h-4 text-emerald-600" />
                      <span>Sovereign Studio</span>
                    </button>
                  </div>
                </div>

                {/* Right Status Badge in Hero */}
                <div className="flex md:flex-col gap-3 shrink-0">
                  <div className="p-3.5 rounded-2xl bg-white/80 border border-slate-200/60 shadow-xs min-w-[170px] backdrop-blur-md">
                    <div className="flex items-center space-x-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                      <Shield className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Clearance Active</span>
                    </div>
                    <div className="text-base font-black text-slate-800">{currentUser.role}</div>
                    <div className="text-[10px] text-slate-500 truncate max-w-[150px]">{currentUser.full_name}</div>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-white/80 border border-slate-200/60 shadow-xs min-w-[170px] backdrop-blur-md">
                    <div className="flex items-center space-x-2 text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                      <span>Air-Gapped Node</span>
                    </div>
                    <div className="text-base font-black text-emerald-600">Zero Cloud Egress</div>
                    <div className="text-[10px] text-slate-500">100% Local Inference</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Metrics & Hardware Meter */}
            <div className="grid grid-cols-4 gap-4">
              <div className="glass-panel p-4">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Clearance Level</div>
                <div className="text-lg font-black text-slate-800">{currentUser.role}</div>
                <div className="text-[10px] text-slate-500 mt-1">{currentUser.full_name}</div>
              </div>

              <div className="glass-panel p-4">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">VRAM Allocation</div>
                <div className="text-lg font-black text-slate-800">{systemStatus?.vram_used_mb || 1200} / {systemStatus?.vram_budget_mb || 7168} MB</div>
                <div className="w-full bg-slate-200 rounded-full h-1.5 mt-2 overflow-hidden">
                  <div className="bg-indigo-600 h-1.5 rounded-full" style={{ width: `${Math.min(100, ((systemStatus?.vram_used_mb || 1200) / (systemStatus?.vram_budget_mb || 7168)) * 100)}%` }} />
                </div>
              </div>

              <div className="glass-panel p-4">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Policy Engine</div>
                <div className="text-lg font-black text-emerald-600 flex items-center">
                  <CheckCircle2 className="w-4 h-4 mr-1" />
                  <span>DEFAULT-DENY</span>
                </div>
                <div className="text-[10px] text-slate-500 mt-1">Scary Command Protection Active</div>
              </div>

              <div className="glass-panel p-4">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">Audit Ledger</div>
                <div className="text-lg font-black text-indigo-700 font-mono">SHA-256</div>
                <div className="text-[10px] text-slate-500 mt-1">Cryptographically Chained</div>
              </div>
            </div>

            {/* Presentation Showcase Cards */}
            <div className="grid grid-cols-3 gap-4">
              <div
                onClick={() => { setActiveTab('chat'); attachSampleDb(); }}
                className="glass-panel p-5 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <Database className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-800 mb-1">Inspect Equipment Database</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Attach and query <code className="text-indigo-600">industrial_demo.db</code> directly in chat for remaining life and corrosion rate analysis.
                </p>
              </div>

              <div
                onClick={() => { setActiveTab('chat'); fileInputRef.current?.click(); }}
                className="glass-panel p-5 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <Image className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-800 mb-1">Multimodal Vision Inspection</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Upload P&ID diagrams, equipment photos, or pipe junctions for local vision analysis and safety code verification.
                </p>
              </div>

              <div
                onClick={() => setActiveTab('machinery')}
                className="glass-panel p-5 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group"
              >
                <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                  <Gauge className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-800 mb-1">Refinery Machinery Twin</h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Real-time 3D telemetry visualization, top spotlighting, and SCADA emergency actuator trips.
                </p>
              </div>
            </div>
          </div>
        )}



        {/* ══════════════════════════════════════════════════════════════
            2. CHAT WITH ATTACHMENTS & POLICY PROTECTION
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Chat List Sidebar */}
            <div className="w-64 glass-nav flex flex-col border-r border-slate-200/40 overflow-hidden shrink-0">
              <div className="p-3.5 flex items-center justify-between border-b border-slate-200/30">
                <div className="flex items-center space-x-2">
                  <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">Previous Chats</span>
                  <span className="text-[10px] bg-slate-200/60 text-slate-500 rounded-full px-1.5 py-0.2 font-mono">{chats.length}</span>
                </div>
                <button onClick={newChat} className="flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium text-indigo-600 hover:bg-indigo-50 border border-indigo-200/60 transition-all shadow-2xs cursor-pointer" title="Start a New Conversation">
                  <Plus className="w-3.5 h-3.5" />
                  <span>New</span>
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {chats.length === 0 ? (
                  <p className="text-[11px] text-slate-400 italic p-3 text-center">No previous chats.</p>
                ) : chats.map((c: any) => {
                  const id = c.chat_id || c[0];
                  const title = c.title || c[1] || 'New Chat';
                  const date = c.updated_at || c[3] || c.created_at || c[2];
                  const isActive = id === currentChatId;
                  return (
                    <button
                      key={id}
                      onClick={() => openChat(id)}
                      className={`w-full text-left p-2.5 rounded-xl text-xs transition-all flex flex-col cursor-pointer ${isActive
                          ? 'bg-indigo-100/90 text-indigo-800 font-semibold shadow-2xs border border-indigo-200/50'
                          : 'text-slate-600 hover:bg-white/70 hover:text-slate-900 border border-transparent'
                        }`}
                    >
                      <span className="truncate w-full font-medium">{title}</span>
                      {date && (
                        <span className={`text-[9px] mt-0.5 ${isActive ? 'text-indigo-500' : 'text-slate-400'}`}>
                          {new Date(date).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Chat Main Area */}
            <div className="flex-1 flex flex-col max-w-4xl w-full mx-auto p-4 overflow-hidden">
              <div ref={chatContainerRef} className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] p-4 text-sm leading-relaxed whitespace-pre-wrap ${msg.sender === 'user' ? 'chat-bubble-user' :
                        msg.sender === 'system' ? 'bg-amber-50 border border-amber-200 text-amber-700 rounded-2xl shadow-sm text-xs' :
                          'chat-bubble-ai'
                      }`}>
                      {msg.attachment && (
                        <div className="mb-2 p-2 rounded-lg bg-white/70 border border-indigo-200/60 flex items-center space-x-2 text-xs text-indigo-900 font-medium">
                          {msg.attachment.type === 'image' ? <Image className="w-4 h-4 text-indigo-600" /> : <Database className="w-4 h-4 text-sky-600" />}
                          <span className="truncate">{msg.attachment.name}</span>
                          <span className="text-[10px] text-indigo-400 uppercase font-mono">[{msg.attachment.type}]</span>
                        </div>
                      )}
                      {msg.text}
                      {msg.timestamp && <div className={`text-[9px] mt-2 ${msg.sender === 'user' ? 'text-indigo-400' : 'text-slate-400'}`}>{msg.timestamp}</div>}
                    </div>
                  </div>
                ))}

                {isExecuting && (
                  <div className="flex justify-start">
                    <div className="chat-bubble-ai p-5">
                      <div className="ai-thinking">
                        <div className="ai-thinking-orb"></div>
                        <div className="flex flex-col">
                          <span className="ai-thinking-text">Thinking & Resolving Intent...</span>
                          <div className="ai-thinking-dots mt-2">
                            <span></span><span></span><span></span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input & Attachment Toolbar */}
              <div className="flex-none p-2 mb-2">
                {/* Active Attachment Chip */}
                {currentAttachment && (
                  <div className="max-w-3xl mx-auto mb-2 flex items-center justify-between p-2 px-3 bg-indigo-50 border border-indigo-200 rounded-xl text-xs text-indigo-900 shadow-xs">
                    <div className="flex items-center space-x-2">
                      {currentAttachment.type === 'image' ? <Image className="w-4 h-4 text-indigo-600" /> : <Database className="w-4 h-4 text-sky-600" />}
                      <span className="font-semibold">{currentAttachment.name}</span>
                      <span className="text-[10px] text-indigo-500 font-mono">({currentAttachment.type})</span>
                    </div>
                    <button onClick={() => setCurrentAttachment(null)} className="p-1 hover:bg-indigo-100 rounded-full text-indigo-600">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                <div className="premium-input-container p-2 px-4 flex items-end relative max-w-3xl mx-auto">
                  {/* Attach Buttons */}
                  <div className="flex items-center space-x-1 mr-2 mb-2">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="p-2 rounded-xl text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                      title="Attach Image or Document"
                    >
                      <Paperclip className="w-4 h-4" />
                    </button>
                    <button
                      onClick={attachSampleDb}
                      className="p-2 rounded-xl text-slate-500 hover:text-sky-600 hover:bg-sky-50 transition-colors"
                      title="Attach Sample Industrial Database (industrial_demo.db)"
                    >
                      <Database className="w-4 h-4" />
                    </button>
                  </div>

                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask sovereign AI, analyze attached DB, or type code task..."
                    className="w-full premium-input resize-none py-3 min-h-[46px] max-h-48 text-sm"
                    rows={1}
                  />

                  <button
                    onClick={handleSend}
                    disabled={(!input.trim() && !currentAttachment) || isExecuting}
                    className="ml-2 mb-2 p-2 rounded-xl text-white premium-btn-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            3. SOVEREIGN STUDIO (IDE) - Clean, Minimal Light Theme
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'ide' && (
          <div className="flex-1 flex flex-col overflow-hidden bg-slate-50 text-slate-800">
            {/* Top Studio Action Bar */}
            <div className="h-10 bg-white border-b border-slate-200 flex items-center justify-between px-3 shrink-0 shadow-2xs">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-1.5 text-indigo-700 font-bold text-xs tracking-wider">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span>SOVEREIGN STUDIO</span>
                </div>
                <div className="h-4 w-px bg-slate-200" />
                {/* Antigravity-Style Open Folder */}
                <button
                  onClick={handleOpenFolder}
                  className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-semibold transition-colors cursor-pointer border border-indigo-200/60 shadow-2xs"
                  title="Open Project Folder (Antigravity Style)"
                >
                  <FolderOpen className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Open Folder</span>
                </button>
                {currentWorkspaceFolder && (
                  <button
                    onClick={handleResetToDefaultWorkspace}
                    className="text-[10px] text-slate-500 hover:text-slate-800 underline px-1 cursor-pointer"
                    title="Reset to Workspace Root"
                  >
                    Reset Root
                  </button>
                )}
                {/* Role Clearance Badge in IDE */}
                <div className={`flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-[10px] font-bold border ${currentUser.role === 'GRADE_1' ? 'bg-amber-50 text-amber-800 border-amber-300' : 'bg-slate-100 text-slate-700 border-slate-200'
                  }`}>
                  <Shield className="w-3 h-3 text-indigo-600" />
                  <span>{currentUser.role === 'GRADE_1' ? 'GRADE 1 (READ-ONLY)' : currentUser.role}</span>
                </div>

                <button
                  onClick={runIdeCurrent}
                  disabled={currentUser.role === 'GRADE_1'}
                  className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-semibold transition-colors cursor-pointer shadow-xs disabled:opacity-40 disabled:cursor-not-allowed"
                  title={currentUser.role === 'GRADE_1' ? 'Execution restricted for Grade 1 Operator (POL_GRADE1_READ)' : 'Execute in Isolated Sandbox'}
                >
                  <Play className="w-3 h-3 fill-current" />
                  <span>Run</span>
                </button>
                <button
                  onClick={saveCurrentIdeFile}
                  disabled={currentUser.role === 'GRADE_1'}
                  className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  title={currentUser.role === 'GRADE_1' ? 'Save blocked: Grade 1 Operator is read-only' : 'Save File (Ctrl+S)'}
                >
                  <Save className="w-3 h-3" />
                  <span>Save</span>
                </button>
                <button
                  onClick={() => setIdeShowNewFileInput(!ideShowNewFileInput)}
                  disabled={currentUser.role === 'GRADE_1'}
                  className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-[11px] font-semibold transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  title={currentUser.role === 'GRADE_1' ? 'File creation requires Grade 2 or higher' : 'Create New File'}
                >
                  <Plus className="w-3 h-3" />
                  <span>New File</span>
                </button>
              </div>

              {/* View Toggles */}
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setIdeActiveView(ideActiveView === 'explorer' ? 'agent' : 'explorer')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1 cursor-pointer ${ideActiveView === 'agent' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                >
                  <Bot className="w-3.5 h-3.5" />
                  <span>Copilot</span>
                </button>
              </div>
            </div>

            {/* New File Inline Input */}
            {ideShowNewFileInput && (
              <div className="p-2 bg-indigo-50/70 border-b border-indigo-200 flex items-center space-x-2 px-4 shrink-0">
                <span className="text-xs font-semibold text-indigo-900">Create in workspace:</span>
                <input
                  type="text"
                  value={ideNewFileName}
                  onChange={(e) => setIdeNewFileName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') createIdeFile(); }}
                  placeholder="e.g. tools/new_script.py"
                  className="flex-1 px-2.5 py-1 text-xs bg-white border border-indigo-300 rounded-md outline-none"
                  autoFocus
                />
                <button onClick={createIdeFile} className="px-3 py-1 bg-indigo-600 text-white text-xs font-semibold rounded-md hover:bg-indigo-700">Create</button>
                <button onClick={() => setIdeShowNewFileInput(false)} className="p-1 text-slate-500 hover:text-slate-800"><X className="w-4 h-4" /></button>
              </div>
            )}

            {/* Studio Main Splitter */}
            <div className="flex-1 flex overflow-hidden">
              {/* Explorer Sidebar */}
              <div className="w-60 bg-slate-100/80 border-r border-slate-200 flex flex-col shrink-0">
                <div className="p-2.5 border-b border-slate-200 flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <div className="flex items-center space-x-1.5 truncate max-w-[170px]" title={currentWorkspaceFolder || 'Workspace Tree'}>
                    <FolderOpen className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                    <span className="truncate">{currentWorkspaceFolder ? currentWorkspaceFolder.split('/').pop() || currentWorkspaceFolder : 'Workspace'}</span>
                  </div>
                  <div className="flex items-center space-x-0.5">
                    <button onClick={handleOpenFolder} className="p-1 hover:bg-slate-200 rounded text-indigo-600 cursor-pointer" title="Open Folder (Antigravity Style)">
                      <FolderPlus className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => fetchIdeTree()} className="p-1 hover:bg-slate-200 rounded text-slate-500 cursor-pointer" title="Refresh">
                      <RefreshCw className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {ideFileTree.length === 0 ? (
                    <p className="text-[11px] text-slate-400 italic p-2">Loading workspace files...</p>
                  ) : (
                    ideFileTree.map((node) => (
                      <div key={node.path} className="space-y-0.5">
                        <div className="text-[11px] font-bold text-slate-600 flex items-center px-1.5 py-1 rounded hover:bg-slate-200/50">
                          <FolderOpen className="w-3.5 h-3.5 text-indigo-500 mr-1.5 shrink-0" />
                          <span>{node.name}</span>
                        </div>
                        {node.children && (
                          <div className="pl-3 space-y-0.5 border-l border-slate-200 ml-2">
                            {node.children.map((child) => (
                              <button
                                key={child.path}
                                onClick={() => openIdeFile(child.path, child.name)}
                                className={`w-full text-left flex items-center px-2 py-1 rounded text-xs transition-colors truncate cursor-pointer ${activeIdeTabPath === child.path
                                    ? 'bg-indigo-100 text-indigo-900 font-semibold'
                                    : 'text-slate-600 hover:bg-slate-200/60'
                                  }`}
                              >
                                <FileCode className="w-3.5 h-3.5 mr-1.5 text-slate-400 shrink-0" />
                                <span className="truncate">{child.name}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Editor & Terminal Canvas */}
              <div className="flex-1 flex flex-col overflow-hidden bg-white">
                {/* Tabs */}
                <div className="h-9 bg-slate-100 border-b border-slate-200 flex items-center overflow-x-auto px-1 space-x-1 shrink-0">
                  {ideTabs.map((t) => {
                    const isActive = t.path === activeIdeTabPath;
                    return (
                      <div
                        key={t.path}
                        onClick={() => setActiveIdeTabPath(t.path)}
                        className={`group h-8 px-3 flex items-center space-x-2 text-xs cursor-pointer border-t-2 transition-colors shrink-0 ${isActive
                            ? 'bg-white text-indigo-900 font-semibold border-indigo-600 shadow-2xs'
                            : 'text-slate-500 hover:bg-slate-200/50 border-transparent'
                          }`}
                      >
                        <FileCode className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                        <span>{t.name}{t.modified ? ' ●' : ''}</span>
                        <button onClick={(e) => closeIdeTab(t.path, e)} className="p-0.5 rounded-full hover:bg-slate-200 opacity-0 group-hover:opacity-100">
                          <X className="w-3 h-3 text-slate-400" />
                        </button>
                      </div>
                    );
                  })}
                </div>

                {/* Monaco Editor Canvas (Light Theme) */}
                <div className="flex-1 relative">
                  {(() => {
                    const cur = ideTabs.find(t => t.path === activeIdeTabPath) || ideTabs[0];
                    return (
                      <Editor
                        height="100%"
                        language={cur?.language || 'python'}
                        value={cur?.content || ''}
                        theme="vs"
                        onChange={(v) => {
                          const val = v || '';
                          setIdeTabs(prev => prev.map(t => t.path === activeIdeTabPath ? { ...t, content: val, modified: true } : t));
                        }}
                        options={{
                          minimap: { enabled: true },
                          fontSize: 13,
                          fontFamily: 'JetBrains Mono',
                          lineNumbers: 'on',
                          scrollBeyondLastLine: false,
                          automaticLayout: true,
                          padding: { top: 12 }
                        }}
                      />
                    );
                  })()}
                </div>

                {/* Bottom Terminal & Problems */}
                <div className="h-44 bg-slate-900 border-t border-slate-800 flex flex-col shrink-0 text-slate-200">
                  <div className="h-8 bg-slate-950 border-b border-slate-800 flex items-center justify-between px-3 shrink-0">
                    <div className="flex items-center space-x-3 text-xs font-semibold">
                      <button
                        onClick={() => setIdeBottomTab('terminal')}
                        className={`py-1 border-b-2 ${ideBottomTab === 'terminal' ? 'text-indigo-400 border-indigo-500' : 'text-slate-400 border-transparent'}`}
                      >
                        TERMINAL
                      </button>
                      <button
                        onClick={() => setIdeBottomTab('problems')}
                        className={`py-1 border-b-2 ${ideBottomTab === 'problems' ? 'text-indigo-400 border-indigo-500' : 'text-slate-400 border-transparent'}`}
                      >
                        PROBLEMS (0)
                      </button>
                    </div>
                    <button onClick={() => setIdeTerminalOutput([])} className="text-[10px] text-slate-400 hover:text-slate-200">Clear</button>
                  </div>

                  <div className="flex-1 overflow-y-auto p-2.5 font-mono text-xs text-slate-300 space-y-1">
                    {ideTerminalOutput.map((line, idx) => (
                      <div key={idx} className={line.startsWith('✓') ? 'text-emerald-400' : line.startsWith('✗') ? 'text-red-400' : line.startsWith('$') ? 'text-sky-400 font-bold' : ''}>
                        {line}
                      </div>
                    ))}
                  </div>

                  {/* Terminal CLI Input Box */}
                  <div className="h-9 bg-slate-950 px-3 flex items-center space-x-2 border-t border-slate-800">
                    <TerminalSquare className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <input
                      type="text"
                      disabled={currentUser.role === 'GRADE_1'}
                      value={ideTerminalInput}
                      onChange={(e) => setIdeTerminalInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') executeTerminalCommand(); }}
                      placeholder={
                        currentUser.role === 'GRADE_1'
                          ? '🔒 Terminal execution restricted: Grade 1 Operator is read-only (Requires Grade 2+)'
                          : 'Run command (e.g. python -m unittest, git status)...'
                      }
                      className="w-full bg-transparent text-xs text-slate-200 outline-none font-mono disabled:opacity-40 disabled:cursor-not-allowed"
                    />
                    <button
                      onClick={executeTerminalCommand}
                      disabled={currentUser.role === 'GRADE_1' || ideTerminalRunning}
                      className="text-[11px] px-2 py-0.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Execute
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Copilot Panel */}
              {ideActiveView === 'agent' && (
                <div className="w-80 bg-white border-l border-slate-200 flex flex-col shrink-0">
                  <div className="h-9 px-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs font-bold text-slate-700">
                    <span className="flex items-center space-x-1.5"><Bot className="w-4 h-4 text-indigo-600" /><span>Agent Copilot</span></span>
                    <button onClick={() => setIdeActiveView('explorer')}><X className="w-4 h-4 text-slate-400" /></button>
                  </div>
                  <div className="flex-1 overflow-y-auto p-3 space-y-3">
                    {ideAgentMessages.map((m, idx) => (
                      <div key={idx} className={`p-3 rounded-xl text-xs leading-relaxed ${m.role === 'user' ? 'bg-indigo-50 text-indigo-900 ml-4' : 'bg-slate-100 text-slate-800 mr-4'}`}>
                        <div className="font-semibold text-[10px] text-slate-400 mb-1">{m.role === 'user' ? 'YOU' : 'COPILOT'} · {m.time}</div>
                        <div className="whitespace-pre-wrap">{m.text}</div>
                      </div>
                    ))}
                  </div>
                  <div className="p-2 border-t border-slate-200">
                    <div className="flex items-center space-x-1">
                      <input
                        type="text"
                        value={ideAgentPrompt}
                        onChange={(e) => setIdeAgentPrompt(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleIdeAgentSend(); }}
                        placeholder="Ask Copilot about active file..."
                        className="flex-1 px-3 py-2 text-xs bg-slate-100 border border-slate-300 rounded-lg outline-none"
                      />
                      <button onClick={handleIdeAgentSend} disabled={ideAgentBusy} className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
                        <Send className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}



        {/* ══════════════════════════════════════════════════════════════
            5. PRESENTATION DATABASE & ANALYTICS EXPLORER
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'database' && (
          <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-6xl mx-auto w-full space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-black text-slate-800 flex items-center space-x-2">
                  <Database className="w-5 h-5 text-indigo-600" />
                  <span>Refinery Industrial Presentation Database (<code className="text-indigo-600 font-mono">industrial_demo.db</code>)</span>
                </h1>
                <p className="text-xs text-slate-500 mt-1">
                  Query operational equipment, inspection records, corrosion metrics, and active plant maintenance orders.
                </p>
              </div>
              <button onClick={() => { fetchDbSchema(); fetchDbAnalytics(); }} className="premium-btn px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 cursor-pointer">
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh DB</span>
              </button>
            </div>

            {/* Analytics Summary Banner */}
            {dbAnalytics && (
              <div className="grid grid-cols-4 gap-4">
                <div className="glass-panel p-4">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Monitored Equipment</div>
                  <div className="text-xl font-black text-slate-800 mt-1">{dbAnalytics.total_equipment} Units</div>
                  <div className="text-[10px] text-emerald-600 font-semibold mt-1">Operational: {dbAnalytics.equipment_status?.OPERATIONAL || 0}</div>
                </div>
                <div className="glass-panel p-4">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Avg Corrosion Rate</div>
                  <div className="text-xl font-black text-amber-600 mt-1">{dbAnalytics.avg_corrosion_rate} mm/yr</div>
                  <div className="text-[10px] text-slate-500 mt-1">Benchmark API 570 Standard</div>
                </div>
                <div className="glass-panel p-4">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Critical Work Orders</div>
                  <div className="text-xl font-black text-red-600 mt-1">{dbAnalytics.critical_work_orders} Orders</div>
                  <div className="text-[10px] text-slate-500 mt-1">High Consequence Tag</div>
                </div>
                <div className="glass-panel p-4">
                  <div className="text-[10px] font-bold text-slate-400 uppercase">Min Remaining Life</div>
                  <div className="text-xl font-black text-indigo-600 mt-1">{dbAnalytics.min_remaining_life_years} Years</div>
                  <div className="text-[10px] text-slate-500 mt-1">Safety Clearance Required</div>
                </div>
              </div>
            )}

            {/* Table Tabs & SQL Query Runner */}
            <div className="glass-panel p-4 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-slate-600">Database Tables:</span>
                  <div className="flex space-x-1">
                    {dbTables.map(t => (
                      <button
                        key={t}
                        onClick={() => queryTable(t)}
                        className={`px-3 py-1 rounded-md text-xs font-bold transition-all cursor-pointer ${dbActiveTable === t ? 'bg-indigo-600 text-white shadow-xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* SQL Query Bar */}
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  disabled={currentUser.role === 'GRADE_1'}
                  value={dbQueryText}
                  onChange={(e) => setDbQueryText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') executeCustomQuery(); }}
                  className="flex-1 px-3 py-2 text-xs font-mono bg-white border border-slate-300 rounded-lg outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder={
                    currentUser.role === 'GRADE_1'
                      ? '🔒 Custom SQL execution restricted to Grade 2+ (Browsing pre-filtered tables permitted)'
                      : 'Enter SELECT query...'
                  }
                />
                <button
                  onClick={() => executeCustomQuery()}
                  disabled={dbLoading || currentUser.role === 'GRADE_1'}
                  className="px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-xs"
                >
                  {dbLoading ? 'Querying...' : 'Execute SQL'}
                </button>
              </div>

              {dbError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center space-x-2">
                  <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
                  <span>{dbError}</span>
                </div>
              )}

              {/* Results Table */}
              <div className="overflow-x-auto rounded-lg border border-slate-200 max-h-96">
                <table className="w-full text-left text-xs border-collapse bg-white">
                  <thead className="bg-slate-100 border-b border-slate-200 text-slate-600 font-bold sticky top-0">
                    <tr>
                      {dbColumns.map((c, i) => (
                        <th key={i} className="p-2.5 px-3 font-mono">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
                    {dbRows.length === 0 ? (
                      <tr>
                        <td colSpan={dbColumns.length || 1} className="p-4 text-center text-slate-400 italic">No records returned.</td>
                      </tr>
                    ) : (
                      dbRows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-indigo-50/40">
                          {dbColumns.map((col, ci) => (
                            <td key={ci} className="p-2 px-3 whitespace-nowrap">{String(row[col] !== null && row[col] !== undefined ? row[col] : '')}</td>
                          ))}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            6. EMPLOYEES & RBAC CLEARANCE REGISTRY
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'employees' && (
          <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-6xl mx-auto w-full space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-black text-slate-800 flex items-center space-x-2">
                  <Users className="w-5 h-5 text-indigo-600" />
                  <span>Employee Directory & Role-Based Authorization</span>
                </h1>
                <p className="text-xs text-slate-500 mt-1">
                  Enforces plant hierarchy: Operator (Grade 1), Engineer (Grade 2), Superintendent (Grade 3), and Admin.
                </p>
              </div>
              <button onClick={fetchEmployees} className="premium-btn px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 cursor-pointer">
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh Directory</span>
              </button>
            </div>

            <div className="grid grid-cols-3 gap-6">
              {/* Registration Form (Only ADMIN can register) */}
              <div className="glass-panel p-5">
                <h3 className="text-sm font-bold text-slate-800 mb-2">Register Employee Account</h3>
                <p className="text-xs text-slate-500 mb-4">Add authorized plant staff to local SQLite user database.</p>

                {empStatusMsg && (
                  <div className={`p-2.5 mb-3 rounded-lg text-xs ${empStatusMsg.startsWith('✓') ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                    {empStatusMsg}
                  </div>
                )}

                {currentUser.role !== 'ADMIN' ? (
                  <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-amber-900 text-xs space-y-2">
                    <div className="flex items-center space-x-1.5 font-bold">
                      <Lock className="w-4 h-4 text-amber-700 shrink-0" />
                      <span>Administrative Clearance Required</span>
                    </div>
                    <p className="text-[11px] leading-relaxed text-amber-800">
                      Creating and provisioning employee credentials requires <strong>ADMIN</strong> clearance. Your current role is <strong>{currentUser.role}</strong>.
                    </p>
                  </div>
                ) : (
                  <form onSubmit={handleCreateEmployee} className="space-y-3">
                    <div>
                      <label className="text-[11px] font-bold text-slate-600 block mb-1">FULL NAME</label>
                      <input
                        type="text"
                        value={newEmpName}
                        onChange={(e) => setNewEmpName(e.target.value)}
                        placeholder="e.g. Ramesh Kumar"
                        className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-bold text-slate-600 block mb-1">USERNAME</label>
                      <input
                        type="text"
                        value={newEmpUsername}
                        onChange={(e) => setNewEmpUsername(e.target.value)}
                        placeholder="e.g. operator_102"
                        className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-bold text-slate-600 block mb-1">PASSWORD (PBKDF2-HMAC-SHA256)</label>
                      <input
                        type="password"
                        value={newEmpPassword}
                        onChange={(e) => setNewEmpPassword(e.target.value)}
                        placeholder="Minimum 8 characters"
                        className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-bold text-slate-600 block mb-1">DEPARTMENT</label>
                      <input
                        type="text"
                        value={newEmpDept}
                        onChange={(e) => setNewEmpDept(e.target.value)}
                        className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg outline-none"
                        required
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-bold text-slate-600 block mb-1">ROLE CLEARANCE</label>
                      <select
                        value={newEmpRole}
                        onChange={(e) => setNewEmpRole(e.target.value)}
                        className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg outline-none cursor-pointer"
                      >
                        <option value="GRADE_1">GRADE_1 (Plant Operator / Read-Only)</option>
                        <option value="GRADE_2">GRADE_2 (Maintenance Engineer)</option>
                        <option value="GRADE_3">GRADE_3 (Plant Superintendent)</option>
                        <option value="ADMIN">ADMIN (System Administrator)</option>
                      </select>
                    </div>

                    <button
                      type="submit"
                      className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-colors cursor-pointer shadow-xs"
                    >
                      Register Employee
                    </button>
                  </form>
                )}
              </div>

              {/* Employee Directory Table */}
              <div className="col-span-2 glass-panel p-5 overflow-hidden flex flex-col">
                <h3 className="text-sm font-bold text-slate-800 mb-3">Active Employee Directory</h3>
                <div className="overflow-y-auto max-h-[480px] rounded-lg border border-slate-200">
                  <table className="w-full text-left text-xs bg-white">
                    <thead className="bg-slate-100 text-slate-600 font-bold sticky top-0 border-b border-slate-200">
                      <tr>
                        <th className="p-2.5">Name</th>
                        <th className="p-2.5">Username</th>
                        <th className="p-2.5">Department</th>
                        <th className="p-2.5">Role</th>
                        <th className="p-2.5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {employeeList.map((emp, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="p-2.5 font-semibold text-slate-900">{emp.full_name}</td>
                          <td className="p-2.5 font-mono text-[11px]">{emp.username}</td>
                          <td className="p-2.5 text-slate-500">{emp.department}</td>
                          <td className="p-2.5">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${emp.role === 'ADMIN' ? 'bg-purple-100 text-purple-700' :
                                emp.role === 'GRADE_3' ? 'bg-indigo-100 text-indigo-700' :
                                  emp.role === 'GRADE_2' ? 'bg-sky-100 text-sky-700' :
                                    'bg-slate-100 text-slate-700'
                              }`}>
                              {emp.role}
                            </span>
                          </td>
                          <td className="p-2.5">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${emp.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                              {emp.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            REFINERY MACHINERY SIMULATION & CENTRAL POLICY CONTROL
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'machinery' && (
          <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-6">
            {/* Top Machinery Banner */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 bg-gradient-to-r from-white/95 via-indigo-50/50 to-slate-50 border border-slate-200/80 rounded-3xl shadow-sm">
              <div>
                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold mb-2">
                  <Gauge className="w-3.5 h-3.5 text-indigo-600 animate-spin-slow" />
                  <span>Refinery SCADA & IoT Digital Twin</span>
                </div>
                <h1 className="text-2xl font-black text-slate-800 tracking-tight flex items-center space-x-2">
                  <span>Industrial Machinery & AI Safety Control</span>
                </h1>
                <p className="text-xs text-slate-500 max-w-2xl mt-1 leading-relaxed">
                  Interactive real-time 3D physics & SCADA telemetry simulation. Tell the Sovereign AI to stop, start, or trip heavy refinery machinery. Central Policy Engine validates your clearance grade before any physical actuator responds.
                </p>
              </div>

              {/* Clearance Pill */}
              <div className="flex items-center space-x-3 bg-white/90 p-3 rounded-2xl border border-slate-200 shadow-xs">
                <Shield className="w-5 h-5 text-indigo-600" />
                <div>
                  <div className="text-[10px] uppercase font-bold text-slate-400">Your Clearance Level</div>
                  <div className="text-sm font-black text-slate-800">{currentUser.role}</div>
                  <div className="text-[10px] text-indigo-600 font-medium">{currentUser.username}</div>
                </div>
              </div>
            </div>

            {/* AI Natural Language Machinery Control Bar */}
            <div className="glass-panel p-5 rounded-2xl border border-indigo-200/60 shadow-md shadow-indigo-100/30">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-700">
                  <Bot className="w-4 h-4 text-indigo-600" />
                  <span>Voice / Natural Language AI Machinery Actuator</span>
                </div>
                <span className="text-[11px] text-slate-500">
                  Try saying: <code className="bg-slate-100 px-1.5 py-0.5 rounded text-indigo-600 font-mono">"AI stop crude pump 301"</code> or <code className="bg-slate-100 px-1.5 py-0.5 rounded text-indigo-600 font-mono">"emergency shutdown compressor"</code>
                </span>
              </div>

              <form onSubmit={handleVoiceAiCommand} className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={machineVoiceCommand}
                    onChange={(e) => setMachineVoiceCommand(e.target.value)}
                    placeholder="Type or simulate voice: e.g., 'Emergency trip pump 301' or 'machine ruko' or 'throttle compressor'..."
                    className="w-full px-4 py-3 text-xs rounded-xl bg-white border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none pr-28 transition-all"
                  />
                  <div className="absolute right-3 top-2.5 flex items-center space-x-1.5 text-slate-400">
                    <Radio className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-semibold text-slate-500">SCADA Bridge</span>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={machineAiLoading}
                  className="px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-bold flex items-center space-x-2 shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50"
                >
                  {machineAiLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
                  <span>Execute Command</span>
                </button>
              </form>

              {/* Central Policy Action Banner */}
              <AnimatePresence>
                {machineActionBanner && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className={`mt-4 p-4 rounded-xl border flex items-start space-x-3 text-xs leading-relaxed ${
                      machineActionBanner.type === 'success'
                        ? 'bg-emerald-50/90 border-emerald-300 text-emerald-900 shadow-sm'
                        : 'bg-red-50/90 border-red-300 text-red-900 shadow-sm'
                    }`}
                  >
                    {machineActionBanner.type === 'success' ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <ShieldAlert className="w-5 h-5 text-red-600 shrink-0 mt-0.5 animate-bounce" />
                    )}
                    <div className="flex-1">
                      <div className="font-bold text-sm tracking-tight mb-1 flex items-center space-x-2">
                        <span>{machineActionBanner.title}</span>
                        {machineActionBanner.type === 'blocked' && (
                          <span className="text-[10px] bg-red-200 text-red-800 px-2 py-0.5 rounded-full uppercase font-black">
                            FAIL-CLOSED PROTECTION
                          </span>
                        )}
                      </div>
                      <p className="text-xs opacity-90">{machineActionBanner.description}</p>
                    </div>
                    <button
                      onClick={() => setMachineActionBanner(null)}
                      className="p-1 rounded-md hover:bg-black/5 text-slate-500 cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Simulated Refinery Machinery Grid - 4 Distinct 3D Digital Twin Machines */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              {machineryList.map((m) => {
                const isRunning = m.status === 'RUNNING';
                const isThrottled = m.status === 'THROTTLED';
                const isStopped = m.status === 'STOPPED';

                return (
                  <div
                    key={m.id}
                    onClick={() => setSelectedMachineId(m.id)}
                    className={`glass-panel p-4 rounded-2xl border transition-all cursor-pointer relative overflow-hidden flex flex-col justify-between ${
                      selectedMachineId === m.id
                        ? 'border-indigo-500 ring-2 ring-indigo-200 shadow-xl'
                        : 'border-slate-200/80 hover:border-indigo-300 hover:shadow-md'
                    }`}
                  >
                    {/* Header */}
                    <div>
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="flex items-center space-x-1.5">
                            <span className="text-[11px] font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                              {m.id}
                            </span>
                            <span className="text-[10px] text-slate-400 font-medium truncate max-w-[110px]">{m.unit}</span>
                          </div>
                          <h3 className="text-xs font-bold text-slate-800 mt-1 leading-snug truncate" title={m.name}>{m.name}</h3>
                        </div>

                        {/* Status Pill */}
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1 shadow-2xs shrink-0 ${
                          isRunning
                            ? 'bg-emerald-100 text-emerald-700 border border-emerald-300'
                            : isThrottled
                            ? 'bg-amber-100 text-amber-700 border border-amber-300'
                            : 'bg-red-100 text-red-700 border border-red-300'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${
                            isRunning ? 'bg-emerald-500 animate-ping' : isThrottled ? 'bg-amber-500' : 'bg-red-500'
                          }`} />
                          <span>{m.status}</span>
                        </span>
                      </div>

                      {/* WebGL Three.js Real-Time 3D Digital Twin Canvas */}
                      <div className="my-2 rounded-xl bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white relative overflow-hidden shadow-2xl border border-slate-800/80 flex flex-col items-center justify-center">
                        <ThreeMachineCanvas machineId={m.id} status={m.status} rpm={m.rpm} />

                        {/* Real-Time SCADA Telemetry Overlay */}
                        <div className="w-full bg-slate-950/80 backdrop-blur-xs px-3 py-1.5 border-t border-slate-800/80 grid grid-cols-2 gap-x-2 gap-y-0.5 font-mono text-[10px]">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">RPM:</span>
                            <span className={`font-bold ${isRunning ? 'text-emerald-400' : 'text-slate-500'}`}>
                              {m.rpm}
                            </span>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Vib:</span>
                            <span className={`font-bold ${m.vibration_mms > 2.5 ? 'text-amber-400' : 'text-slate-300'}`}>
                              {m.vibration_mms} mm/s
                            </span>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Pres:</span>
                            <span className="text-sky-300 font-bold">{m.pressure_bar} Bar</span>
                          </div>

                          <div className="flex items-center justify-between">
                            <span className="text-slate-400">Temp:</span>
                            <span className="text-amber-300 font-bold">{m.temperature_c} °C</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* RBAC Governance Requirements Footer */}
                    <div className="mt-2 pt-3 border-t border-slate-200/60 flex flex-col space-y-2 text-xs">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-slate-400">Required:</span>
                        <span className="font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">
                          {m.min_clearance}
                        </span>
                        <span className="text-slate-400">E-Stop:</span>
                        <span className="font-semibold text-red-600">
                          {m.emergency_stop_role}+
                        </span>
                      </div>

                      {/* Interactive Control Buttons */}
                      <div className="flex items-center justify-end space-x-1.5 pt-1">
                        {isRunning ? (
                          <>
                            <button
                              onClick={(e) => { e.stopPropagation(); handleMachineControl(m.id, 'THROTTLE', `Manual Throttle Command for ${m.name}`); }}
                              className="px-2 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 font-semibold text-[11px] transition-all cursor-pointer"
                              title="Reduce flow rate by 50%"
                            >
                              Throttle
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); handleMachineControl(m.id, 'STOP', `Emergency Halt Command for ${m.name}`); }}
                              className="px-3 py-1 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-[11px] flex items-center space-x-1 shadow-xs hover:scale-105 active:scale-95 transition-all cursor-pointer"
                              title="Trigger Emergency Machine Stop via AI Policy"
                            >
                              <Octagon className="w-3.5 h-3.5" />
                              <span>AI STOP</span>
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleMachineControl(m.id, 'START', `Machine Start Command for ${m.name}`); }}
                            className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] flex items-center space-x-1 shadow-xs hover:scale-105 active:scale-95 transition-all cursor-pointer"
                          >
                            <Power className="w-3.5 h-3.5" />
                            <span>AI START</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Architecture Explainer Box for Presentation */}
            <div className="glass-panel p-5 bg-gradient-to-r from-indigo-50/50 via-white to-sky-50/40 border border-indigo-200/60 rounded-2xl flex items-start space-x-4">
              <Shield className="w-6 h-6 text-indigo-600 shrink-0 mt-1" />
              <div className="text-xs text-slate-600 space-y-1">
                <h4 className="font-bold text-slate-800 text-sm">
                  Why This Matters for Hackathon & Industrial Safety Demonstration:
                </h4>
                <p>
                  1. <strong>Deterministic Safeguards</strong>: If a low-clearance user (e.g. <code>GRADE_1</code> plant operator or untrusted account) asks the AI to <em>"trip all refinery compressors"</em> or <em>"shut down distillation"</em>, the Central Policy Engine <strong>fails closed and blocks the actuator</strong> before any SCADA pulse is sent.
                </p>
                <p>
                  2. <strong>Immediate Audible & Visual Feedback</strong>: When an authorized superintendent (<code>GRADE_3</code> or <code>ADMIN</code>) issues the stop command, the 3D rotor speed drops to 0 RPM, vibrations cease, and the tamper-evident audit ledger cryptographically logs the event.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            7. AUDIT TRAIL
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'audit' && (
          <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-6xl mx-auto w-full space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-black text-slate-800 flex items-center space-x-2">
                  <ClipboardList className="w-5 h-5 text-indigo-600" />
                  <span>SHA-256 Tamper-Evident Audit Ledger</span>
                </h1>
                <p className="text-xs text-slate-500 mt-1">
                  Every user action, tool dispatch, role clearance switch, and blocked command is cryptographically verified.
                </p>
              </div>
              <button onClick={fetchAuditLogs} className="premium-btn px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 cursor-pointer">
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh Ledger</span>
              </button>
            </div>

            <div className="glass-panel p-4 overflow-hidden">
              <div className="overflow-x-auto rounded-lg border border-slate-200 max-h-[500px]">
                <table className="w-full text-left text-xs bg-white">
                  <thead className="bg-slate-100 text-slate-600 font-bold sticky top-0 border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Timestamp</th>
                      <th className="p-2.5">Event Type</th>
                      <th className="p-2.5">User</th>
                      <th className="p-2.5">Role</th>
                      <th className="p-2.5">Status</th>
                      <th className="p-2.5">Cryptographic Hash</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                    {auditLogs.length === 0 ? (
                      <tr><td colSpan={6} className="p-4 text-center text-slate-400 italic">No audit records found.</td></tr>
                    ) : (
                      auditLogs.map((log, i) => (
                        <tr key={i} className="hover:bg-slate-50">
                          <td className="p-2 text-slate-500 whitespace-nowrap">{new Date(log.timestamp).toLocaleTimeString()}</td>
                          <td className="p-2 font-bold text-slate-800">{log.event_type}</td>
                          <td className="p-2 text-slate-600">{log.user_id}</td>
                          <td className="p-2">
                            <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-bold">{log.role || '---'}</span>
                          </td>
                          <td className="p-2">
                            <span className={`px-1.5 py-0.5 rounded font-bold ${log.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                              {log.status}
                            </span>
                          </td>
                          <td className="p-2 text-indigo-600 truncate max-w-xs">{log.event_hash}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            8. MODELS & HARDWARE
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'models' && (
          <div className="flex-1 flex flex-col p-6 max-w-5xl mx-auto w-full overflow-y-auto space-y-5">
            <div className="flex items-center justify-between">
              <h1 className="text-lg font-bold flex items-center text-slate-800"><Database className="w-5 h-5 mr-2 text-indigo-500" />Models & VRAM Allocation</h1>
              <button onClick={() => { fetchModels(); fetchMetrics(); }} className="premium-btn px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center cursor-pointer"><RefreshCw className="w-3 h-3 mr-1" />Refresh</button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-panel p-5">
                <h2 className="text-xs font-bold text-slate-600 mb-3 flex items-center"><Cpu className="w-3.5 h-3.5 mr-1.5 text-indigo-500" />System Memory Budget</h2>
                {systemStatus ? (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center border-b border-slate-200/50 pb-2"><span className="text-xs">Kernel Status</span><span className={`text-[10px] font-bold px-2 py-0.5 rounded ${systemStatus.status === 'online' ? 'bg-emerald-100 text-emerald-600' : 'bg-red-100 text-red-600'}`}>{systemStatus.status || 'ERROR'}</span></div>
                    {systemStatus.vram_used_mb !== undefined && <div className="space-y-1"><div className="flex justify-between text-xs"><span>VRAM Budget</span><span className="font-mono">{systemStatus.vram_used_mb}/{systemStatus.vram_budget_mb} MB</span></div><div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden"><div className="bg-gradient-to-r from-indigo-500 to-sky-400 h-1.5 rounded-full" style={{ width: `${Math.min(100, (systemStatus.vram_used_mb / systemStatus.vram_budget_mb) * 100)}%` }}></div></div></div>}
                  </div>
                ) : <div className="text-xs text-slate-500 flex items-center"><Loader2 className="w-3 h-3 mr-1.5 animate-spin" />Loading...</div>}
              </div>
              <div className="glass-panel p-5">
                <h2 className="text-xs font-bold text-slate-600 mb-3 flex items-center"><Activity className="w-3.5 h-3.5 mr-1.5 text-indigo-500" />Execution Metrics</h2>
                {modelMetrics ? (
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between border-b border-slate-200/50 pb-1.5"><span>Worker Swaps</span><span className="font-mono font-bold">{modelMetrics.swaps_count}</span></div>
                    <div className="flex justify-between border-b border-slate-200/50 pb-1.5"><span>Worker Reuses</span><span className="font-mono font-bold">{modelMetrics.reuses_count}</span></div>
                    <div className="flex justify-between border-b border-slate-200/50 pb-1.5"><span>Load Time</span><span className="font-mono font-bold">{Math.round(modelMetrics.total_load_time_ms)}ms</span></div>
                    <div className="flex justify-between"><span>Inference Time</span><span className="font-mono font-bold">{Math.round(modelMetrics.total_inference_time_ms)}ms</span></div>
                  </div>
                ) : <div className="text-xs text-slate-500 flex items-center"><Loader2 className="w-3 h-3 mr-1.5 animate-spin" />Loading...</div>}
              </div>
            </div>
            <h2 className="text-xs font-bold text-slate-600 mb-2">Registered Specialist Workers</h2>
            <div className="space-y-2">
              {models.map((m, i) => (
                <div key={i} className="glass-panel p-3.5 flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2"><span className="text-xs font-bold text-slate-800">{m.model_name}</span><span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${m.is_loaded ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-500'}`}>{m.is_loaded ? 'LOADED' : 'UNLOADED'}</span></div>
                    <div className="flex items-center space-x-3 mt-1 text-[10px] text-slate-500"><span>Role: {m.worker_type}</span><span>VRAM: {m.vram_required_mb}MB</span><span>License: {m.license}</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════════
            9. SETTINGS
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'settings' && (
          <div className="flex-1 flex flex-col p-6 max-w-3xl mx-auto w-full overflow-y-auto space-y-4">
            <h1 className="text-lg font-bold flex items-center text-slate-800"><Settings className="w-5 h-5 mr-2 text-indigo-500" />Workbench Settings</h1>
            <section className="glass-panel p-5">
              <h2 className="text-xs font-bold text-slate-700 mb-3 flex items-center"><Zap className="w-3.5 h-3.5 mr-1.5 text-amber-500" />Inference Settings</h2>
              <div>
                <label className="text-xs font-semibold text-slate-600 block mb-1.5">Max Tokens</label>
                <div className="flex items-center space-x-3"><input type="range" min="256" max="8192" step="256" value={maxTokens} onChange={(e) => setMaxTokens(Number(e.target.value))} className="flex-1 accent-indigo-500" /><span className="text-xs font-mono font-bold text-indigo-600 w-14 text-right">{maxTokens}</span></div>
              </div>
            </section>
            <section className="glass-panel p-5">
              <h2 className="text-xs font-bold text-slate-700 mb-3 flex items-center"><Shield className="w-3.5 h-3.5 mr-1.5 text-sky-500" />Security Constraints</h2>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center border-b border-slate-200/50 pb-2"><div><span className="font-semibold text-slate-600">Air-Gapped Mode</span><p className="text-[10px] text-slate-400">Zero external network egress enforced.</p></div><span className="text-[10px] bg-emerald-100 text-emerald-600 font-bold px-2 py-0.5 rounded">ACTIVE</span></div>
                <div className="flex justify-between items-center border-b border-slate-200/50 pb-2"><div><span className="font-semibold text-slate-600">Role-Based Access Control</span><p className="text-[10px] text-slate-400">Plant hierarchy authorization.</p></div><span className="text-[10px] bg-emerald-100 text-emerald-600 font-bold px-2 py-0.5 rounded">ACTIVE</span></div>
                <div className="flex justify-between items-center"><div><span className="font-semibold text-slate-600">Scary Command Protection</span><p className="text-[10px] text-slate-400">Database deletion and destructive commands blocked.</p></div><span className="text-[10px] bg-emerald-100 text-emerald-600 font-bold px-2 py-0.5 rounded">ENFORCED</span></div>
              </div>
            </section>
          </div>
        )}

        {/* Antigravity-Style Folder Picker Modal Fallback */}
        {folderInputModalOpen && (
          <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
            <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl border border-slate-200 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-indigo-700 font-bold text-sm">
                  <FolderOpen className="w-5 h-5 text-indigo-600" />
                  <span>Open Workspace Folder</span>
                </div>
                <button onClick={() => setFolderInputModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Enter an absolute path or relative folder directory to open in Sovereign Studio (just like Antigravity IDE):
              </p>
              <input
                type="text"
                value={manualFolderPath}
                onChange={(e) => setManualFolderPath(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleApplyManualFolder(); }}
                placeholder="e.g. c:/AI/Locall-Agentic-AI-Workbench/backend"
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg outline-none font-mono"
                autoFocus
              />
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  onClick={() => setFolderInputModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApplyManualFolder}
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs cursor-pointer"
                >
                  Open in IDE
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
