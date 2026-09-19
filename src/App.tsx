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
  Network, GitFork, ArrowDown, Cpu as CpuIcon,
  RotateCcw, SlidersHorizontal, TrendingUp, TrendingDown, Wind,
  Download, Filter
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
  const [dbQueryText, setDbQueryText] = useState<string>('SELECT * FROM equipment LIMIT 25;');
  const [dbAnalytics, setDbAnalytics] = useState<any>(null);
  const [dbLoading, setDbLoading] = useState<boolean>(false);
  const [dbError, setDbError] = useState<string>('');
  const [dbSearchQuery, setDbSearchQuery] = useState<string>('');
  const [dbSelectedRow, setDbSelectedRow] = useState<any | null>(null);


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
  const [isMachineChatOpen, setIsMachineChatOpen] = useState<boolean>(true);
  const [machineActionBanner, setMachineActionBanner] = useState<{
    type: 'success' | 'blocked' | 'info';
    title: string;
    description: string;
  } | null>(null);
  const [machineChatHistory, setMachineChatHistory] = useState<Array<{
    sender: 'user' | 'ai';
    text: string;
    timestamp: string;
    status?: 'granted' | 'blocked';
  }>>([
    {
      sender: 'ai',
      text: '🤖 Sovereign SCADA Actuator initialized. Ask me to monitor, throttle, start, or emergency trip refinery machinery. Central Policy Engine validates your clearance grade before any physical actuator responds.',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);

  // ─── ADVANCED MACHINERY FEATURES STATE ───
  const [activeMachineModal, setActiveMachineModal] = useState<'none' | 'diagnostics' | 'replay' | 'work_order'>('none');
  const [machineDiagnosticsData, setMachineDiagnosticsData] = useState<any>(null);
  const [machineReplayData, setMachineReplayData] = useState<any>(null);
  const [isDiagnosticsLoading, setIsDiagnosticsLoading] = useState<boolean>(false);
  const [workOrderDescription, setWorkOrderDescription] = useState<string>('');
  const [workOrderPriority, setWorkOrderPriority] = useState<string>('HIGH');
  const [workOrderResult, setWorkOrderResult] = useState<any>(null);

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
    if (activeTab === 'machinery') {
      fetchMachinery();
      const machInterval = setInterval(() => {
        fetchMachinery();
      }, 2500);
      return () => clearInterval(machInterval);
    }
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

  const attachDemoPidBlueprint = () => {
    setCurrentAttachment({
      name: 'pid_crude_cdu301_blueprint.png',
      path: 'data/demo_showcase/pid_crude_cdu301_blueprint.png',
      type: 'image',
    });
  };

  const attachDemoNdtSurvey = () => {
    setCurrentAttachment({
      name: 'refinery_corrosion_ndt_survey.csv',
      path: 'data/demo_showcase/refinery_corrosion_ndt_survey.csv',
      type: 'csv',
    });
  };

  const attachDemoVibrationStream = () => {
    setCurrentAttachment({
      name: 'pump301a_vibration_accelerometer_stream.csv',
      path: 'data/demo_showcase/pump301a_vibration_accelerometer_stream.csv',
      type: 'csv',
    });
  };

  const attachDemoIncidentReport = () => {
    setCurrentAttachment({
      name: 'osha_psm_critical_incident_investigation.txt',
      path: 'data/demo_showcase/osha_psm_critical_incident_investigation.txt',
      type: 'document',
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

  const exportDbToCsv = () => {
    if (!dbRows || dbRows.length === 0 || !dbColumns || dbColumns.length === 0) return;
    const header = dbColumns.join(',');
    const rows = dbRows.map(row =>
      dbColumns.map(col => {
        const val = row[col];
        if (val === null || val === undefined) return '""';
        const str = String(val).replace(/"/g, '""');
        return `"${str}"`;
      }).join(',')
    );
    const csvContent = 'data:text/csv;charset=utf-8,' + [header, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${dbActiveTable || 'query_export'}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportDbToJson = () => {
    if (!dbRows || dbRows.length === 0) return;
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(dbRows, null, 2))}`;
    const link = document.createElement('a');
    link.setAttribute('href', jsonString);
    link.setAttribute('download', `${dbActiveTable || 'query_export'}_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

  const handleMachineControl = async (machineId: string, action: string, cmdText?: string, params?: Record<string, any>) => {
    setMachineAiLoading(true);
    setMachineActionBanner(null);
    const userPrompt = cmdText || `Command: ${action} machine ${machineId}`;
    const timestamp = new Date().toLocaleTimeString();

    // Append user command into machine chat stream
    setMachineChatHistory(prev => [
      ...prev,
      { sender: 'user', text: userPrompt, timestamp }
    ]);

    try {
      const r = await fetch(`${API}/api/machinery/control`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          machine_id: machineId,
          action: action,
          command_text: userPrompt,
          parameters: params
        })
      });
      const d = await r.json();
      if (r.ok && d.success) {
        const msg = d.message || `Machine ${machineId} transitioned to ${action} status. SCADA relay tripped.`;
        setMachineActionBanner({
          type: 'success',
          title: 'Central Policy Engine: GRANTED',
          description: msg
        });
        setMachineChatHistory(prev => [
          ...prev,
          { sender: 'ai', text: `✓ GRANTED: ${msg}`, timestamp: new Date().toLocaleTimeString(), status: 'granted' }
        ]);
        fetchMachinery();
      } else {
        const errMsg = d.message || d.reason || 'Insufficient role clearance for machine override.';
        setMachineActionBanner({
          type: 'blocked',
          title: 'Central Policy Engine: BLOCKED (Default-Deny)',
          description: errMsg
        });
        setMachineChatHistory(prev => [
          ...prev,
          { sender: 'ai', text: `⚠️ BLOCKED (Fail-Closed): ${errMsg}`, timestamp: new Date().toLocaleTimeString(), status: 'blocked' }
        ]);
      }
    } catch (e: any) {
      setMachineActionBanner({
        type: 'blocked',
        title: 'Communication Failure',
        description: e.message
      });
      setMachineChatHistory(prev => [
        ...prev,
        { sender: 'ai', text: `✗ Communication error: ${e.message}`, timestamp: new Date().toLocaleTimeString(), status: 'blocked' }
      ]);
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

    // Determine action & parameters
    let action = 'STOP';
    let params: Record<string, any> | undefined = undefined;

    if (text.includes('emergency') || text.includes('shutdown') || text.includes('trip') || text.includes('esd') || text.includes('khatra')) {
      action = 'EMERGENCY_SHUTDOWN';
    } else if (text.includes('purge') || text.includes('relief') || text.includes('depressurize') || text.includes('valve') || text.includes('pressure relief') || text.includes('hawa nikal')) {
      action = 'PURGE_VALVE';
    } else if (text.includes('lube') || text.includes('lubricat') || text.includes('oil') || text.includes('tel')) {
      action = 'LUBE_CIRCULATE';
    } else if (text.includes('cool') || text.includes('cooling') || text.includes('flush') || text.includes('water') || text.includes('thanda')) {
      action = 'COOLING_FLUSH';
    } else if (text.includes('boost') || text.includes('badhao') || text.includes('increase') || text.includes('tez') || text.includes('speed up') || text.includes('accelerate') || text.includes('overdrive') || text.includes('badao')) {
      action = 'BOOST';
    } else if (text.includes('stop') || text.includes('halt') || text.includes('ruk') || text.includes('roko') || text.includes('band') || text.includes('pause') || text.includes('off') || text.includes('thapp')) {
      action = 'STOP';
    } else if (text.includes('start') || text.includes('resume') || text.includes('chalu') || text.includes('chalao') || text.includes('run') || text.includes('on') || text.includes('activate')) {
      action = 'START';
    } else if (text.includes('throttle') || text.includes('slow') || text.includes('dheere') || text.includes('kam') || text.includes('decelerate') || text.includes('ghatao')) {
      action = 'THROTTLE';
    }

    handleMachineControl(targetId, action, machineVoiceCommand, params);
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

        {/* Strict Brutal Central Login Card */}
        <div className="max-w-md w-full bg-white p-8 relative z-20 border-[3px] border-black shadow-[8px_8px_0px_#000000]">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="w-14 h-14 bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 border-2 border-black flex items-center justify-center text-white shadow-[4px_4px_0px_#000000] mx-auto mb-3">
              <span className="font-cursive text-3xl font-black leading-none pb-0.5">M</span>
            </div>
            <h1 className="font-cursive text-4xl font-bold text-black tracking-tight">Musky.AI</h1>
            <p className="text-xs font-bold font-mono text-black mt-1 uppercase tracking-wider">SOVEREIGN INDUSTRIAL WORKBENCH · AIR-GAPPED</p>
            <div className="mt-3 inline-flex items-center space-x-1.5 px-3 py-1 bg-[#ffe600] border-2 border-black text-black text-[11px] font-bold uppercase shadow-[2px_2px_0px_#000000]">
              <Shield className="w-3.5 h-3.5 text-black" />
              <span>RBAC CLEARANCE GATEWAY</span>
            </div>
          </div>

          {loginError && (
            <div className="mb-4 p-3 bg-[#ff3366] text-white border-2 border-black text-xs font-bold shadow-[3px_3px_0px_#000000] flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-white" />
              <span>{loginError}</span>
            </div>
          )}

          {/* Sequential Credentials Form */}
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="text-[11px] font-black text-black uppercase tracking-wider block mb-1 font-mono">
                {'[>]'} OPERATOR ID / USERNAME
              </label>
              <input
                type="text"
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                placeholder="e.g. admin, engineer_202, operator_101"
                className="w-full px-3.5 py-2.5 bg-white border-2 border-black text-xs text-black outline-none font-mono font-bold shadow-[3px_3px_0px_#000000] focus:bg-[#ffe600]/20 transition-all"
                required
              />
            </div>

            <div>
              <label className="text-[11px] font-black text-black uppercase tracking-wider block mb-1 font-mono">
                {'[>]'} SECURITY PASSCODE
              </label>
              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="ENTER AUTHORIZED PASSCODE"
                className="w-full px-3.5 py-2.5 bg-white border-2 border-black text-xs text-black outline-none font-mono font-bold shadow-[3px_3px_0px_#000000] focus:bg-[#ffe600]/20 transition-all"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loginLoading}
              className="w-full py-3 bg-black hover:bg-[#ffe600] text-white hover:text-black font-black text-xs uppercase tracking-wider border-2 border-black shadow-[4px_4px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#000000] flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
            >
              {loginLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-black" />
                  <span>VERIFYING CLEARANCE...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>AUTHENTICATE & ENTER</span>
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials */}
          <div className="mt-6 pt-4 border-t-2 border-black">
            <div className="text-[10px] font-black font-mono text-black uppercase tracking-wider text-center mb-2.5">
              PRESET DEMO CLEARANCES
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('admin', 'admin123')}
                className="p-2 bg-white hover:bg-[#ffe600] text-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 text-center transition-all cursor-pointer"
              >
                <div className="text-[10px] font-black uppercase">Admin</div>
                <div className="text-[9px] text-black font-mono font-bold">admin123</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('engineer_202', 'demo123')}
                className="p-2 bg-white hover:bg-[#00f0ff] text-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 text-center transition-all cursor-pointer"
              >
                <div className="text-[10px] font-black uppercase">Engineer</div>
                <div className="text-[9px] text-black font-mono font-bold">demo123</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('operator_101', 'demo123')}
                className="p-2 bg-white hover:bg-[#00e676] text-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 text-center transition-all cursor-pointer"
              >
                <div className="text-[10px] font-black uppercase">Operator</div>
                <div className="text-[9px] text-black font-mono font-bold">demo123</div>
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

      {/* Strict Brutalist Sidebar Navigation */}
      <nav className="w-[66px] bg-white flex flex-col items-center py-4 z-20 space-y-2 shrink-0 border-r-[3px] border-black shadow-[4px_0px_0px_#000000]">
        <div className="mb-2 flex flex-col items-center cursor-pointer group" onClick={() => setActiveTab('home')} title="Musky.AI Home">
          <div className="w-11 h-11 bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 border-2 border-black flex items-center justify-center text-white shadow-[3px_3px_0px_#000000] group-hover:translate-x-0.5 group-hover:translate-y-0.5 transition-all">
            <span className="font-cursive text-2xl font-black leading-none pb-0.5">M</span>
          </div>
        </div>

        <div className="w-10 h-0.5 bg-black mb-1" />

        {navItems.map(item => {
          const isActive = activeTab === item.key;
          return (
            <button
              key={item.key}
              onClick={() => setActiveTab(item.key)}
              className={`w-11 h-11 border-2 border-black transition-all duration-100 cursor-pointer relative group flex items-center justify-center ${
                isActive
                  ? 'bg-black text-[#ffe600] shadow-[3px_3px_0px_#ffe600] translate-x-0.5'
                  : 'bg-white text-black hover:bg-[#ffe600] hover:shadow-[3px_3px_0px_#000000]'
              }`}
              title={item.label}
            >
              <item.icon className="w-5 h-5" />

              {/* Strict Brutalist Tooltip */}
              <span className="absolute left-[72px] bg-black text-[#ffe600] text-[11px] font-mono font-bold px-3 py-1 border-2 border-black shadow-[3px_3px_0px_#000000] whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 uppercase tracking-wider">
                {item.label}
              </span>
            </button>
          );
        })}

        <div className="mt-auto flex flex-col items-center space-y-2 pt-2 border-t-2 border-black w-full">
          <button
            onClick={() => switchClearance(currentUser.role === 'ADMIN' ? 'GRADE_1' : currentUser.role === 'GRADE_1' ? 'GRADE_2' : currentUser.role === 'GRADE_2' ? 'GRADE_3' : 'ADMIN')}
            className="w-10 h-10 bg-[#00f0ff] hover:bg-[#ffe600] text-black flex items-center justify-center text-[11px] font-black font-mono border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer uppercase"
            title={`Clearance: ${currentUser.role}. Click to cycle.`}
          >
            {currentUser.role.replace('GRADE_', 'G')}
          </button>
          <div
            className={`w-3 h-3 border border-black transition-all ${backendOnline ? 'bg-[#00e676]' : 'bg-[#ff3366]'}`}
            title={backendOnline ? 'Sovereign Kernel Online' : 'Kernel Offline'}
          />
        </div>
      </nav>

      {/* Main Workspace Area */}
      <main className="flex-1 flex flex-col relative z-10 h-full overflow-hidden bg-[#f5f4ef]">
        {/* Strict Brutalist Header Bar */}
        <div className="h-12 w-full bg-white flex items-center justify-between px-4 border-b-[3px] border-black shadow-[0px_3px_0px_#000000] shrink-0" style={{ WebkitAppRegion: 'drag' } as any}>
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-2">
              <span className="font-cursive text-2xl font-black text-black tracking-wide pr-1">Musky.AI</span>
              <span className="text-black font-black font-mono">/</span>
              <span className="text-xs text-black font-black tracking-wider uppercase font-mono">{navItems.find(n => n.key === activeTab)?.label}</span>
            </span>

            {/* Role Clearance Pill & Selector */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 bg-white border-2 border-black shadow-[2px_2px_0px_#000000]" style={{ WebkitAppRegion: 'no-drag' } as any}>
              <Shield className="w-3.5 h-3.5 text-black" />
              <span className="text-[10px] font-black font-mono text-black uppercase tracking-wider">{currentUser.role}</span>
              <span className="text-[9px] font-mono text-slate-600">({currentUser.username})</span>
              <select
                value={currentUser.role}
                onChange={(e) => switchClearance(e.target.value)}
                className="text-[10px] font-mono bg-white text-black font-bold outline-none cursor-pointer pl-1 border-l border-black ml-1"
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
              <span className="flex items-center space-x-1.5 text-black text-[10px] font-black font-mono bg-[#00e676] px-2.5 py-1 border border-black shadow-[2px_2px_0px_#000000] uppercase">
                <Wifi className="w-3 h-3 text-black" />
                <span>AIR-GAPPED NODE</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-white text-[10px] font-black font-mono bg-[#ff3366] px-2.5 py-1 border border-black shadow-[2px_2px_0px_#000000] uppercase">
                <WifiOff className="w-3 h-3" />
                <span>OFFLINE</span>
              </span>
            )}

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="flex items-center space-x-1 px-3 py-1 bg-white hover:bg-[#ff3366] text-black hover:text-white border-2 border-black text-xs font-black font-mono uppercase shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer"
              title="Sign Out / Lock Session"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>LOCK</span>
            </button>

            <WindowControls />
          </div>
        </div>

        {/* ══════════════════════════════════════════════════════════════
            1. HOME / OVERVIEW (Filled, Minimal & Aesthetic)
        ══════════════════════════════════════════════════════════════ */}
        {/* ══════════════════════════════════════════════════════════════
            1. HOME / OVERVIEW (Strict Brutalism Architecture)
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'home' && (
          <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-6xl mx-auto w-full space-y-6">
            {/* Strict Brutal Hero Banner */}
            <div className="bg-white p-8 relative overflow-hidden border-[3px] border-black shadow-[8px_8px_0px_#000000]">
              {/* Industrial Hazard Corner Stripe */}
              <div className="absolute top-0 right-0 w-32 h-6 hazard-stripe border-b-2 border-l-2 border-black" />

              <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="max-w-2xl space-y-3">
                  <div className="inline-flex items-center space-x-2 px-3 py-1 bg-[#ffe600] border-2 border-black text-black text-xs font-black font-mono shadow-[3px_3px_0px_#000000] uppercase">
                    <Sparkles className="w-3.5 h-3.5 text-black" />
                    <span>SIH26117 · AIR-GAPPED SOVEREIGN AI SYSTEM</span>
                  </div>

                  <div className="space-y-1">
                    <h1 className="text-3xl sm:text-4xl font-black text-black tracking-tight flex items-baseline gap-2.5 flex-wrap">
                      <span className="font-mono uppercase">Welcome to</span>
                      <span className="font-cursive text-4xl sm:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-500 pr-1">
                        Musky.AI
                      </span>
                    </h1>
                    <p className="text-xs font-bold font-mono text-black uppercase tracking-wider bg-[#00f0ff] inline-block px-2 py-0.5 border border-black mt-1">
                      HIGH-CRITICALITY REFINERY ENGINEERING & SCADA ACTUATOR CONTROL
                    </p>
                  </div>

                  <p className="text-xs sm:text-sm text-black font-medium leading-relaxed max-w-xl font-mono">
                    Zero cloud egress on-premise execution engineered for high-criticality refining infrastructure. Powered by verifiable cryptographic audits, multimodal vision inspection, and role-governed policy sandboxing.
                  </p>

                  <div className="pt-2 flex flex-wrap items-center gap-3">
                    <button
                      onClick={() => setActiveTab('chat')}
                      className="px-5 py-2.5 bg-black hover:bg-[#ffe600] text-white hover:text-black text-xs font-black font-mono uppercase tracking-wider flex items-center space-x-2 border-2 border-black shadow-[4px_4px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>START SOVEREIGN CHAT</span>
                    </button>
                    <button
                      onClick={() => { setActiveTab('chat'); attachSampleDb(); }}
                      className="px-4 py-2.5 bg-white hover:bg-[#00f0ff] text-black text-xs font-black font-mono uppercase tracking-wider flex items-center space-x-2 border-2 border-black shadow-[4px_4px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer"
                    >
                      <Database className="w-4 h-4" />
                      <span>ATTACH INDUSTRIAL DB</span>
                    </button>
                    <button
                      onClick={() => setActiveTab('ide')}
                      className="px-4 py-2.5 bg-white hover:bg-[#00e676] text-black text-xs font-black font-mono uppercase tracking-wider flex items-center space-x-2 border-2 border-black shadow-[4px_4px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer"
                    >
                      <Code2 className="w-4 h-4" />
                      <span>SOVEREIGN STUDIO</span>
                    </button>
                  </div>
                </div>

                {/* Right Status Badge in Hero */}
                <div className="flex md:flex-col gap-3 shrink-0">
                  <div className="p-4 bg-white border-2 border-black shadow-[4px_4px_0px_#000000] min-w-[180px]">
                    <div className="flex items-center space-x-2 text-[10px] font-black text-black font-mono uppercase tracking-wider mb-1">
                      <Shield className="w-3.5 h-3.5 text-black" />
                      <span>CLEARANCE LEVEL</span>
                    </div>
                    <div className="text-lg font-black font-mono text-black uppercase">{currentUser.role}</div>
                    <div className="text-[10px] font-mono font-bold text-slate-700 truncate max-w-[150px]">{currentUser.full_name}</div>
                  </div>

                  <div className="p-4 bg-[#00e676] border-2 border-black shadow-[4px_4px_0px_#000000] min-w-[180px]">
                    <div className="flex items-center space-x-2 text-[10px] font-black text-black font-mono uppercase tracking-wider mb-1">
                      <div className="w-2.5 h-2.5 bg-black" />
                      <span>AIR-GAPPED NODE</span>
                    </div>
                    <div className="text-base font-black font-mono text-black uppercase">ZERO CLOUD EGRESS</div>
                    <div className="text-[10px] font-mono font-bold text-black uppercase">100% LOCAL INFERENCE</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Metrics & Hardware Meter */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white p-4 border-[2.5px] border-black shadow-[4px_4px_0px_#000000]">
                <div className="text-[10px] font-black font-mono text-black uppercase tracking-wider mb-1 flex items-center justify-between">
                  <span>CLEARANCE</span>
                  <Shield className="w-3.5 h-3.5 text-black" />
                </div>
                <div className="text-xl font-black font-mono text-black uppercase">{currentUser.role}</div>
                <div className="text-[11px] font-mono text-slate-700 mt-0.5 truncate">{currentUser.full_name}</div>
              </div>

              <div className="bg-white p-4 border-[2.5px] border-black shadow-[4px_4px_0px_#000000]">
                <div className="text-[10px] font-black font-mono text-black uppercase tracking-wider mb-1 flex items-center justify-between">
                  <span className="flex items-center space-x-1">
                    <span>VRAM ALLOCATION</span>
                  </span>
                  <div className="flex items-center space-x-1">
                    <span className="inline-flex items-center px-1.5 py-0.5 bg-[#00e676] border border-black text-[9px] font-mono font-black text-black leading-none">
                      <svg className="w-2.5 h-2.5 mr-1 inline-block" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M7.4 3C4.4 3 2 5.4 2 8.4v7.2C2 18.6 4.4 21 7.4 21h9.2c3 0 5.4-2.4 5.4-5.4V8.4C22 5.4 19.6 3 16.6 3H7.4zm0 2h9.2c1.9 0 3.4 1.5 3.4 3.4v7.2c0 1.9-1.5 3.4-3.4 3.4H7.4C5.5 19 4 17.5 4 15.6V8.4C4 6.5 5.5 5 7.4 5zM9 8v8l7-4-7-4z"/>
                      </svg>
                      RTX GPU
                    </span>
                    <HardDrive className="w-3.5 h-3.5 text-black" />
                  </div>
                </div>
                <div className="text-xl font-black text-black font-mono">
                  {systemStatus?.vram_used_mb || 1200} <span className="text-xs text-black font-normal">/ {systemStatus?.vram_budget_mb || 7168} MB</span>
                </div>
                <div className="w-full bg-slate-200 h-2 mt-2 border border-black">
                  <div className="bg-black h-full transition-all" style={{ width: `${Math.min(100, ((systemStatus?.vram_used_mb || 1200) / (systemStatus?.vram_budget_mb || 7168)) * 100)}%` }} />
                </div>
                <div className="mt-2 flex items-center justify-between text-[9px] font-mono text-black">
                  <span className="font-bold">DRIVER: CUDA 12.4</span>
                  <span className="bg-[#ffe600] px-1 border border-black font-black">LOCAL ON-PREM</span>
                </div>
              </div>

              <div className="bg-[#ffe600] p-4 border-[2.5px] border-black shadow-[4px_4px_0px_#000000]">
                <div className="text-[10px] font-black font-mono text-black uppercase tracking-wider mb-1 flex items-center justify-between">
                  <span>POLICY ENGINE</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-black" />
                </div>
                <div className="text-xl font-black font-mono text-black uppercase">DEFAULT-DENY</div>
                <div className="text-[11px] font-mono text-black font-bold mt-0.5 uppercase">SCADA GATE ACTIVE</div>
              </div>

              <div className="bg-white p-4 border-[2.5px] border-black shadow-[4px_4px_0px_#000000]">
                <div className="text-[10px] font-black font-mono text-black uppercase tracking-wider mb-1 flex items-center justify-between">
                  <span>AUDIT LEDGER</span>
                  <ClipboardList className="w-3.5 h-3.5 text-black" />
                </div>
                <div className="text-xl font-black text-black font-mono">SHA-256</div>
                <div className="text-[11px] font-mono text-slate-700 mt-0.5 uppercase">CRYPTOGRAPHIC CHAIN</div>
              </div>
            </div>

            {/* Presentation Showcase Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div
                onClick={() => { setActiveTab('chat'); attachSampleDb(); }}
                className="bg-white p-5 border-[2.5px] border-black shadow-[5px_5px_0px_#000000] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[7px_7px_0px_#000000] transition-all cursor-pointer group"
              >
                <div className="w-11 h-11 bg-[#ffe600] border-2 border-black text-black flex items-center justify-center mb-3.5 shadow-[2px_2px_0px_#000000]">
                  <Database className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-black text-black mb-1 font-mono uppercase">INSPECT REFINERY DATABASE</h3>
                <p className="text-xs text-black font-mono leading-relaxed">
                  Query industrial SQLite database directly in chat for API 510 remaining life and ASME corrosion statistics.
                </p>
                <div className="mt-3.5 pt-3 border-t-2 border-black flex items-center text-xs font-black font-mono text-black space-x-1 uppercase group-hover:translate-x-1 transition-transform">
                  <span>LAUNCH DB QUERY</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>

              <div
                onClick={() => { setActiveTab('chat'); attachDemoPidBlueprint(); }}
                className="bg-white p-5 border-[2.5px] border-black shadow-[5px_5px_0px_#000000] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[7px_7px_0px_#000000] transition-all cursor-pointer group"
              >
                <div className="w-11 h-11 bg-[#00f0ff] border-2 border-black text-black flex items-center justify-center mb-3.5 shadow-[2px_2px_0px_#000000]">
                  <Image className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-black text-black mb-1 font-mono uppercase">MULTIMODAL P&ID BLUEPRINT</h3>
                <p className="text-xs text-black font-mono leading-relaxed">
                  Analyze high-res P&ID diagrams with automated ISA 5.1 tag extraction and ASME B31.3 wall defect flags.
                </p>
                <div className="mt-3.5 pt-3 border-t-2 border-black flex items-center text-xs font-black font-mono text-black space-x-1 uppercase group-hover:translate-x-1 transition-transform">
                  <span>INSPECT P&ID BLUEPRINT</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>

              <div
                onClick={() => setActiveTab('machinery')}
                className="bg-white p-5 border-[2.5px] border-black shadow-[5px_5px_0px_#000000] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[7px_7px_0px_#000000] transition-all cursor-pointer group"
              >
                <div className="w-11 h-11 bg-[#00e676] border-2 border-black text-black flex items-center justify-center mb-3.5 shadow-[2px_2px_0px_#000000]">
                  <Gauge className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-black text-black mb-1 font-mono uppercase">REFINERY MACHINERY TWIN</h3>
                <p className="text-xs text-black font-mono leading-relaxed">
                  3D SCADA telemetry twin with real-time ISO 10816 diagnostics, 200 Hz trip replay, and SIL-3 interlocks.
                </p>
                <div className="mt-3.5 pt-3 border-t-2 border-black flex items-center text-xs font-black font-mono text-black space-x-1 uppercase group-hover:translate-x-1 transition-transform">
                  <span>LAUNCH 3D TWIN</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>
            </div>
          </div>
        )}



        {/* ══════════════════════════════════════════════════════════════
            2. CHAT WITH ATTACHMENTS & POLICY PROTECTION (Strict Brutalism)
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'chat' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Strict Brutal Chat List Sidebar */}
            <div className="w-64 bg-white flex flex-col border-r-[3px] border-black shadow-[4px_0px_0px_#000000] overflow-hidden shrink-0">
              <div className="p-3 flex items-center justify-between border-b-2 border-black bg-[#f5f4ef]">
                <div className="flex items-center space-x-2">
                  <span className="text-[11px] font-black font-mono text-black uppercase tracking-wider">SESSION LOGS</span>
                  <span className="text-[10px] bg-black text-[#ffe600] font-mono px-1.5 py-0.2 font-bold">{chats.length}</span>
                </div>
                <button onClick={newChat} className="flex items-center space-x-1 px-2.5 py-1 bg-white hover:bg-[#ffe600] text-xs font-black font-mono text-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer" title="Start a New Conversation">
                  <Plus className="w-3.5 h-3.5" />
                  <span>NEW</span>
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
                {chats.length === 0 ? (
                  <p className="text-[11px] font-mono text-slate-500 uppercase p-3 text-center">[ NO STORED CHATS ]</p>
                ) : chats.map((c: any) => {
                  const id = c.chat_id || c[0];
                  const title = c.title || c[1] || 'New Chat';
                  const date = c.updated_at || c[3] || c.created_at || c[2];
                  const isActive = id === currentChatId;
                  return (
                    <button
                      key={id}
                      onClick={() => openChat(id)}
                      className={`w-full text-left p-2.5 text-xs font-mono transition-all flex flex-col cursor-pointer border-2 border-black ${isActive
                          ? 'bg-[#ffe600] text-black font-black shadow-[3px_3px_0px_#000000] translate-x-0.5'
                          : 'bg-white text-black hover:bg-[#f5f4ef] hover:shadow-[2px_2px_0px_#000000]'
                        }`}
                    >
                      <span className="truncate w-full font-bold uppercase">{title}</span>
                      {date && (
                        <span className="text-[9px] mt-0.5 text-slate-700 font-bold">
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
                    <div className={`max-w-[80%] p-4 text-sm leading-relaxed whitespace-pre-wrap font-mono ${msg.sender === 'user' ? 'chat-bubble-user' :
                        msg.sender === 'system' ? 'bg-[#ffe600] border-2 border-black text-black shadow-[4px_4px_0px_#000000] text-xs font-bold' :
                          'chat-bubble-ai'
                      }`}>
                      {msg.attachment && (
                        <div className="mb-2 p-2 bg-[#00f0ff] border-2 border-black flex items-center space-x-2 text-xs text-black font-black shadow-[2px_2px_0px_#000000]">
                          {msg.attachment.type === 'image' ? <Image className="w-4 h-4 text-black" /> : <Database className="w-4 h-4 text-black" />}
                          <span className="truncate uppercase font-mono">{msg.attachment.name}</span>
                          <span className="text-[10px] bg-black text-white px-1 uppercase font-mono">[{msg.attachment.type}]</span>
                        </div>
                      )}
                      {msg.text}
                      {msg.timestamp && <div className={`text-[9px] mt-2 font-mono font-bold ${msg.sender === 'user' ? 'text-[#00f0ff]' : 'text-slate-600'}`}>[{msg.timestamp}]</div>}
                    </div>
                  </div>
                ))}

                {isExecuting && (
                  <div className="flex justify-start">
                    <div className="chat-bubble-ai p-5">
                      <div className="ai-thinking">
                        <div className="ai-thinking-orb"></div>
                        <div className="flex flex-col">
                          <span className="ai-thinking-text">[ INFERENCE IN PROGRESS - ZERO CLOUD EGRESS ]</span>
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
                  <div className="max-w-3xl mx-auto mb-2 flex items-center justify-between p-2 px-3 bg-[#00f0ff] border-2 border-black text-xs text-black font-mono font-bold shadow-[3px_3px_0px_#000000]">
                    <div className="flex items-center space-x-2">
                      {currentAttachment.type === 'image' ? <Image className="w-4 h-4 text-black" /> : <Database className="w-4 h-4 text-black" />}
                      <span className="font-black uppercase">{currentAttachment.name}</span>
                      <span className="text-[10px] bg-black text-white px-1 font-mono">({currentAttachment.type})</span>
                    </div>
                    <button onClick={() => setCurrentAttachment(null)} className="p-1 hover:bg-black hover:text-white border border-black cursor-pointer">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {/* Quick Demo Showcase Bar */}
                <div className="max-w-3xl mx-auto mb-2 flex items-center flex-wrap gap-2 px-1">
                  <span className="text-[10px] font-black font-mono text-black uppercase tracking-wider mr-1 flex items-center bg-[#ffe600] px-1.5 py-0.5 border border-black shadow-[2px_2px_0px_#000000]">
                    <Sparkles className="w-3 h-3 text-black mr-1" /> SHOWCASE FILES:
                  </span>
                  <button
                    onClick={attachDemoPidBlueprint}
                    className="px-2.5 py-1 bg-white hover:bg-[#ffe600] text-black text-[11px] font-mono font-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center space-x-1 cursor-pointer uppercase"
                    title="Load P&ID Blueprint of Crude Distillation Overhead Train"
                  >
                    <Image className="w-3 h-3 text-black" />
                    <span>P&ID BLUEPRINT (CDU-301)</span>
                  </button>
                  <button
                    onClick={attachDemoNdtSurvey}
                    className="px-2.5 py-1 bg-white hover:bg-[#00f0ff] text-black text-[11px] font-mono font-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center space-x-1 cursor-pointer uppercase"
                    title="Load Ultrasonic Thickness NDT Survey (ASME B31G)"
                  >
                    <Table className="w-3 h-3 text-black" />
                    <span>NDT SURVEY (ASME B31G)</span>
                  </button>
                  <button
                    onClick={attachDemoVibrationStream}
                    className="px-2.5 py-1 bg-white hover:bg-[#ff3366] hover:text-white text-black text-[11px] font-mono font-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center space-x-1 cursor-pointer uppercase"
                    title="Load High-Speed Vibration FFT Telemetry (ISO 10816)"
                  >
                    <Activity className="w-3 h-3" />
                    <span>VIBRATION STREAM (ISO 10816)</span>
                  </button>
                  <button
                    onClick={attachDemoIncidentReport}
                    className="px-2.5 py-1 bg-white hover:bg-[#ffe600] text-black text-[11px] font-mono font-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center space-x-1 cursor-pointer uppercase"
                    title="Load OSHA 1910 PSM Investigation Dossier"
                  >
                    <FileText className="w-3 h-3 text-black" />
                    <span>OSHA PSM DOSSIER</span>
                  </button>
                  <button
                    onClick={attachSampleDb}
                    className="px-2.5 py-1 bg-white hover:bg-[#00e676] text-black text-[11px] font-mono font-black border-2 border-black shadow-[2px_2px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all flex items-center space-x-1 cursor-pointer uppercase"
                    title="Load Industrial SQLite Database"
                  >
                    <Database className="w-3 h-3 text-black" />
                    <span>REFINERY DB</span>
                  </button>
                </div>

                <div className="premium-input-container p-2 px-4 flex items-end relative max-w-3xl mx-auto">
                  {/* Attach Buttons */}
                  <div className="flex items-center space-x-1 mr-2 mb-2">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="p-2 bg-white hover:bg-[#ffe600] border-2 border-black text-black shadow-[2px_2px_0px_#000000] transition-colors cursor-pointer"
                      title="Attach Any Local File"
                    >
                      <Paperclip className="w-4 h-4" />
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
        {activeTab === 'database' && (() => {
          // Pre-set safe analytical query templates
          const presetQueries = [
            { label: '🔥 High-Risk Equipment (API 510/570)', sql: "SELECT tag, equipment_type, unit, status, criticality, operating_pressure, metallurgy FROM equipment WHERE criticality = 'CRITICAL' ORDER BY operating_pressure DESC;" },
            { label: '⚠️ Accelerated Corrosion (>0.2 mm/yr)', sql: "SELECT i.inspection_id, e.tag, e.unit, i.inspection_type, i.corrosion_rate_mm_year, i.remaining_life_years, i.governing_code, i.status FROM inspections i JOIN equipment e ON i.equipment_id = e.equipment_id WHERE i.corrosion_rate_mm_year > 0.2 ORDER BY i.corrosion_rate_mm_year DESC;" },
            { label: '🚨 Open Critical Work Orders', sql: "SELECT w.wo_number, e.tag, e.unit, emp.name AS technician, w.priority, w.category, w.due_date, w.description, w.status FROM work_orders w JOIN equipment e ON w.equipment_id = e.equipment_id LEFT JOIN employees emp ON w.assigned_to = emp.employee_id WHERE w.priority = 'CRITICAL' AND w.status != 'CLOSED';" },
            { label: '🏭 Active Plant Sectors & Capacity', sql: "SELECT unit_code, unit_name, refinery_zone, capacity_bpsd, operating_license, lead_engineer FROM plant_units ORDER BY capacity_bpsd DESC;" },
            { label: '🧪 Critical Chemical Inventory', sql: "SELECT chemical_name, cas_number, unit, storage_tank, quantity_metric_tons, reorder_threshold_tons, hazard_classification FROM chemical_inventory ORDER BY quantity_metric_tons DESC;" },
            { label: '🛡️ Safety Incidents & Near Misses', sql: "SELECT incident_code, unit, incident_date, severity, incident_type, description, corrective_action, status FROM safety_incidents ORDER BY incident_date DESC;" },
          ];

          // Filter rows client-side if dbSearchQuery is set
          const filteredRows = dbRows.filter(row => {
            if (!dbSearchQuery.trim()) return true;
            const q = dbSearchQuery.toLowerCase();
            return Object.values(row).some(v => String(v).toLowerCase().includes(q));
          });

          return (
            <div className="flex-1 flex flex-col p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-5">
              {/* Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 glass-panel p-4 bg-gradient-to-r from-white/95 via-indigo-50/40 to-slate-50 border border-slate-200/80 rounded-2xl shadow-xs">
                <div>
                  <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold mb-1">
                    <Database className="w-3.5 h-3.5 text-indigo-600" />
                    <span>SQL Presentation Engine (SQLite 3.42)</span>
                  </div>
                  <h1 className="text-xl font-black text-slate-800 tracking-tight flex items-center space-x-2">
                    <span>Industrial Database Explorer & Analytics</span>
                    <span className="text-xs font-mono font-normal text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                      data/demo_db/industrial_demo.db
                    </span>
                  </h1>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={exportDbToCsv}
                    disabled={dbRows.length === 0}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 shadow-2xs cursor-pointer transition-all disabled:opacity-40"
                    title="Export currently loaded query rows to CSV"
                  >
                    <Download className="w-3.5 h-3.5 text-emerald-600" />
                    <span>CSV</span>
                  </button>
                  <button
                    onClick={exportDbToJson}
                    disabled={dbRows.length === 0}
                    className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 shadow-2xs cursor-pointer transition-all disabled:opacity-40"
                    title="Export currently loaded query rows to JSON"
                  >
                    <FileCode className="w-3.5 h-3.5 text-indigo-600" />
                    <span>JSON</span>
                  </button>
                  <button
                    onClick={() => { fetchDbSchema(); fetchDbAnalytics(); }}
                    className="premium-btn px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 cursor-pointer shadow-xs"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${dbLoading ? 'animate-spin' : ''}`} />
                    <span>Refresh</span>
                  </button>
                </div>
              </div>

              {/* Analytics Summary Banner (6 Interactive KPI Cards) */}
              {dbAnalytics && (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div
                    onClick={() => executeCustomQuery("SELECT * FROM equipment WHERE status = 'OPERATIONAL';")}
                    className="glass-panel p-3.5 bg-white/90 border-slate-200/80 hover:border-indigo-400 cursor-pointer transition-all shadow-2xs hover:shadow-xs group"
                  >
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Monitored Assets</div>
                    <div className="text-xl font-black text-slate-800 mt-0.5 group-hover:text-indigo-600">{dbAnalytics.total_equipment} Units</div>
                    <div className="text-[10px] text-emerald-600 font-semibold mt-0.5 flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>{dbAnalytics.equipment_status?.OPERATIONAL || 0} Operational</span>
                    </div>
                  </div>

                  <div
                    onClick={() => executeCustomQuery("SELECT * FROM plant_units;")}
                    className="glass-panel p-3.5 bg-white/90 border-slate-200/80 hover:border-indigo-400 cursor-pointer transition-all shadow-2xs hover:shadow-xs group"
                  >
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Plant Units</div>
                    <div className="text-xl font-black text-indigo-600 mt-0.5 group-hover:text-indigo-700">{dbAnalytics.total_units} Sectors</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">Crude, FCCU, HGU, SRU</div>
                  </div>

                  <div
                    onClick={() => executeCustomQuery("SELECT * FROM inspections ORDER BY corrosion_rate_mm_year DESC;")}
                    className="glass-panel p-3.5 bg-white/90 border-slate-200/80 hover:border-amber-400 cursor-pointer transition-all shadow-2xs hover:shadow-xs group"
                  >
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Avg Corrosion</div>
                    <div className="text-xl font-black text-amber-600 mt-0.5 group-hover:text-amber-700">{dbAnalytics.avg_corrosion_rate} mm/yr</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">API 570 Code Benchmark</div>
                  </div>

                  <div
                    onClick={() => executeCustomQuery("SELECT * FROM inspections ORDER BY remaining_life_years ASC;")}
                    className="glass-panel p-3.5 bg-white/90 border-slate-200/80 hover:border-purple-400 cursor-pointer transition-all shadow-2xs hover:shadow-xs group"
                  >
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Min Life Span</div>
                    <div className="text-xl font-black text-purple-600 mt-0.5 group-hover:text-purple-700">{dbAnalytics.min_remaining_life_years} Yrs</div>
                    <div className="text-[10px] text-amber-600 font-semibold mt-0.5">Impeller Wear Alert</div>
                  </div>

                  <div
                    onClick={() => executeCustomQuery("SELECT * FROM work_orders WHERE priority = 'CRITICAL';")}
                    className="glass-panel p-3.5 bg-white/90 border-slate-200/80 hover:border-red-400 cursor-pointer transition-all shadow-2xs hover:shadow-xs group"
                  >
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Critical Work Orders</div>
                    <div className="text-xl font-black text-red-600 mt-0.5 group-hover:text-red-700">{dbAnalytics.critical_work_orders} Orders</div>
                    <div className="text-[10px] text-red-500 font-semibold mt-0.5">Immediate Attention</div>
                  </div>

                  <div
                    onClick={() => executeCustomQuery("SELECT * FROM chemical_inventory;")}
                    className="glass-panel p-3.5 bg-white/90 border-slate-200/80 hover:border-sky-400 cursor-pointer transition-all shadow-2xs hover:shadow-xs group"
                  >
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Chemical Storage</div>
                    <div className="text-xl font-black text-sky-600 mt-0.5 group-hover:text-sky-700">{dbAnalytics.total_chemical_tons} Tons</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{dbAnalytics.total_chemicals} Monitored Fluids</div>
                  </div>
                </div>
              )}

              {/* Table Switcher Tabs */}
              <div className="glass-panel p-4 bg-white shadow-xs space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-3">
                  <div className="flex items-center space-x-2">
                    <Table className="w-4 h-4 text-indigo-600" />
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Refinery Tables ({dbTables.length}):</span>
                  </div>

                  {/* Table Selection Pills */}
                  <div className="flex flex-wrap gap-1.5">
                    {dbTables.map(t => {
                      const isActive = dbActiveTable === t;
                      return (
                        <button
                          key={t}
                          onClick={() => {
                            setDbSearchQuery('');
                            queryTable(t);
                          }}
                          className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center space-x-1.5 shadow-2xs ${
                            isActive
                              ? 'bg-indigo-600 text-white shadow-xs ring-2 ring-indigo-200'
                              : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200/80'
                          }`}
                        >
                          <span>{t}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Pre-set Safe Queries Quick Chips */}
                <div className="space-y-1.5">
                  <div className="text-[11px] font-bold text-slate-500 flex items-center space-x-1">
                    <Sparkles className="w-3 h-3 text-amber-500" />
                    <span>Quick Analytical Presets (One-Click Insight):</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {presetQueries.map((pq, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setDbQueryText(pq.sql);
                          setDbSearchQuery('');
                          executeCustomQuery(pq.sql);
                        }}
                        className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-indigo-50/80 hover:bg-indigo-100/90 text-indigo-700 border border-indigo-200/80 transition-all cursor-pointer shadow-2xs text-left"
                      >
                        {pq.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* SQL Query Bar & Search Filter */}
                <div className="space-y-2 pt-2 border-t border-slate-100">
                  <div className="flex items-center space-x-2">
                    <div className="relative flex-1">
                      <input
                        type="text"
                        disabled={currentUser.role === 'GRADE_1'}
                        value={dbQueryText}
                        onChange={(e) => setDbQueryText(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') executeCustomQuery(); }}
                        className="w-full pl-3 pr-24 py-2.5 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl focus:border-indigo-500 focus:bg-white outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        placeholder={
                          currentUser.role === 'GRADE_1'
                            ? '🔒 Custom SQL execution restricted to Grade 2+ (Browsing pre-filtered tables permitted)'
                            : 'Enter SELECT SQL query...'
                        }
                      />
                      <button
                        type="button"
                        onClick={() => setDbQueryText(`SELECT * FROM ${dbActiveTable} LIMIT 25;`)}
                        className="absolute right-2 top-2 px-2 py-0.5 text-[10px] font-semibold text-slate-500 hover:text-indigo-600 bg-white border border-slate-200 rounded cursor-pointer"
                        title="Reset to default table query"
                      >
                        Reset
                      </button>
                    </div>

                    <button
                      onClick={() => executeCustomQuery()}
                      disabled={dbLoading || currentUser.role === 'GRADE_1'}
                      className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs font-bold rounded-xl disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-xs transition-all flex items-center space-x-1.5 shrink-0"
                    >
                      {dbLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                      <span>Execute Query</span>
                    </button>
                  </div>

                  {/* Fast In-Table Text Search Filter Bar */}
                  <div className="flex items-center justify-between text-xs pt-1">
                    <div className="relative flex-1 max-w-sm">
                      <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        value={dbSearchQuery}
                        onChange={(e) => setDbSearchQuery(e.target.value)}
                        placeholder={`Filter loaded records (${filteredRows.length}/${dbRows.length})...`}
                        className="w-full pl-8 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg outline-none focus:border-indigo-400 transition-all"
                      />
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Showing <strong>{filteredRows.length}</strong> of <strong>{dbRows.length}</strong> records &bull; Click row to inspect details
                    </div>
                  </div>
                </div>

                {dbError && (
                  <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center space-x-2">
                    <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
                    <span className="font-semibold">{dbError}</span>
                  </div>
                )}

                {/* Results Table with hover & clickable inspection */}
                <div className="overflow-x-auto rounded-xl border border-slate-200 max-h-[440px] shadow-2xs">
                  <table className="w-full text-left text-xs border-collapse bg-white">
                    <thead className="bg-slate-50/95 border-b border-slate-200 text-slate-700 font-bold sticky top-0 backdrop-blur-xs z-10">
                      <tr>
                        <th className="p-2.5 px-3 w-10 text-center text-slate-400 text-[10px]">#</th>
                        {dbColumns.map((c, i) => (
                          <th key={i} className="p-2.5 px-3 font-mono text-[11px] text-slate-800 whitespace-nowrap">
                            {c}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-mono text-[11px] text-slate-700">
                      {filteredRows.length === 0 ? (
                        <tr>
                          <td colSpan={(dbColumns.length || 1) + 1} className="p-8 text-center text-slate-400 italic">
                            {dbLoading ? 'Loading records...' : 'No records match current query / filter.'}
                          </td>
                        </tr>
                      ) : (
                        filteredRows.map((row, idx) => (
                          <tr
                            key={idx}
                            onClick={() => setDbSelectedRow(row)}
                            className="hover:bg-indigo-50/50 cursor-pointer transition-colors"
                          >
                            <td className="p-2 px-3 text-center text-slate-400 text-[10px] select-none font-sans">
                              {idx + 1}
                            </td>
                            {dbColumns.map((col, ci) => {
                              const val = row[col];
                              const isNull = val === null || val === undefined;
                              const valStr = isNull ? 'NULL' : String(val);
                              // Highlight critical keywords
                              const isCritical = ['CRITICAL', 'WARNING', 'FAIL'].includes(valStr);
                              const isPass = ['PASS', 'OPERATIONAL', 'CLOSED', 'RESOLVED'].includes(valStr);

                              return (
                                <td key={ci} className="p-2 px-3 whitespace-nowrap">
                                  {isCritical ? (
                                    <span className="px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-bold text-[10px]">
                                      {valStr}
                                    </span>
                                  ) : isPass ? (
                                    <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 font-bold text-[10px]">
                                      {valStr}
                                    </span>
                                  ) : isNull ? (
                                    <span className="text-slate-300 italic">NULL</span>
                                  ) : (
                                    <span>{valStr}</span>
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Record Detail Modal / Drawer */}
              <AnimatePresence>
                {dbSelectedRow && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50"
                    onClick={() => setDbSelectedRow(null)}
                  >
                    <motion.div
                      initial={{ scale: 0.95, y: 10 }}
                      animate={{ scale: 1, y: 0 }}
                      exit={{ scale: 0.95, y: 10 }}
                      onClick={(e) => e.stopPropagation()}
                      className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden"
                    >
                      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
                        <div className="flex items-center space-x-2">
                          <FileSpreadsheet className="w-4 h-4 text-indigo-600" />
                          <h3 className="text-sm font-bold text-slate-800">Record Field Inspector</h3>
                          <span className="text-[10px] font-mono bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-bold">
                            {dbActiveTable}
                          </span>
                        </div>
                        <button
                          onClick={() => setDbSelectedRow(null)}
                          className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 cursor-pointer"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="p-5 overflow-y-auto space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                          {Object.entries(dbSelectedRow).map(([key, val]) => (
                            <div key={key} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                              <div className="text-[10px] font-mono font-bold text-slate-400 uppercase">{key}</div>
                              <div className="text-xs font-semibold text-slate-800 mt-0.5 break-words font-sans">
                                {val !== null && val !== undefined ? String(val) : <em className="text-slate-300">null</em>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="p-3.5 border-t border-slate-100 bg-slate-50 flex items-center justify-end space-x-2">
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(JSON.stringify(dbSelectedRow, null, 2));
                            setDbSelectedRow(null);
                          }}
                          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-700 text-xs font-bold hover:bg-slate-50 flex items-center space-x-1 cursor-pointer"
                        >
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy JSON</span>
                        </button>
                        <button
                          onClick={() => setDbSelectedRow(null)}
                          className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 cursor-pointer shadow-2xs"
                        >
                          Close
                        </button>
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })()}


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
                        placeholder="e.g. J. Doe, PE (Lead Engineer)"
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
        {/* ══════════════════════════════════════════════════════════════
            REFINERY MACHINERY SIMULATION & CENTRAL POLICY CONTROL
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'machinery' && (() => {
          const selectedMachine = machineryList.find(m => m.id === selectedMachineId) || machineryList[0] || {
            id: 'PUMP_301A',
            name: 'Crude Feed Charge Pump (CDU-301A)',
            unit: 'Crude Distillation Unit',
            status: 'RUNNING',
            rpm: 2950,
            vibration_mms: 1.4,
            pressure_bar: 18.2,
            temperature_c: 68.4,
            min_clearance: 'GRADE_1',
            emergency_stop_role: 'GRADE_2'
          };
          const isSelectedRunning = selectedMachine.status === 'RUNNING';
          const isSelectedThrottled = selectedMachine.status === 'THROTTLED';

          return (
            <div className="flex-1 flex flex-col p-5 overflow-y-auto max-w-[1600px] mx-auto w-full space-y-4">
              {/* Top Machinery Banner */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 glass-panel p-4 bg-gradient-to-r from-white/95 via-indigo-50/50 to-slate-50 border border-slate-200/80 rounded-2xl shadow-xs">
                <div>
                  <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold mb-1">
                    <Gauge className="w-3.5 h-3.5 text-indigo-600 animate-spin-slow" />
                    <span>Refinery SCADA & IoT Digital Twin</span>
                  </div>
                  <h1 className="text-xl font-black text-slate-800 tracking-tight flex items-center space-x-2">
                    <span>Industrial Machinery & AI Safety Control</span>
                  </h1>
                </div>

                {/* Right Actions & Clearance */}
                <div className="flex items-center space-x-2.5">
                  <button
                    onClick={async () => {
                      try {
                        const r = await fetch(`${API}/api/machinery/reports/export`);
                        const d = await r.json();
                        const blob = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `Sovereign_SCADA_Shift_Report_${new Date().toISOString().slice(0, 10)}.json`;
                        a.click();
                      } catch (e: any) {
                        alert(`Export error: ${e.message}`);
                      }
                    }}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/90 hover:bg-indigo-50 text-indigo-700 border border-slate-200 shadow-2xs text-xs font-bold transition-all cursor-pointer"
                    title="Export OSHA 1910 / API 510 Shift Handover Dossier"
                  >
                    <Download className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Export Shift Report</span>
                  </button>

                  <button
                    onClick={async () => {
                      if (!window.confirm('⚠️ CONFIRM PLANT EMERGENCY SHUTDOWN (ESD)? All refinery machinery will be tripped fail-closed.')) return;
                      try {
                        const r = await fetch(`${API}/api/machinery/emergency-fleet-trip`, {
                          method: 'POST',
                          headers: authHeaders({ 'Content-Type': 'application/json' })
                        });
                        const d = await r.json();
                        if (d.success) {
                          setMachineActionBanner({
                            type: 'blocked',
                            title: '🚨 PLANT-WIDE ESD TRIPPED',
                            description: d.message
                          });
                          fetchMachinery();
                        } else {
                          setMachineActionBanner({
                            type: 'blocked',
                            title: 'Central Policy Blocked Plant ESD',
                            description: d.message || 'Requires Grade 3 or Admin clearance.'
                          });
                        }
                      } catch (e: any) {
                        alert(`ESD Trip Error: ${e.message}`);
                      }
                    }}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white shadow-xs text-xs font-bold transition-all cursor-pointer"
                    title="Plant-Wide Emergency Shutdown (Requires Grade 3 or Admin)"
                  >
                    <Octagon className="w-3.5 h-3.5 text-white" />
                    <span>PLANT ESD (Trip All)</span>
                  </button>

                  {/* Clearance Pill */}
                  <div className="flex items-center space-x-3 bg-white/90 px-3 py-1.5 rounded-xl border border-slate-200 shadow-2xs">
                    <Shield className="w-4 h-4 text-indigo-600" />
                    <div>
                      <div className="text-[9px] uppercase font-bold text-slate-400">Clearance Grade</div>
                      <div className="text-xs font-black text-slate-800">{currentUser.role}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Central Policy Action Banner */}
              <AnimatePresence>
                {machineActionBanner && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    className={`p-3.5 rounded-xl border flex items-start space-x-3 text-xs leading-relaxed ${
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
                      <div className="font-bold text-sm tracking-tight mb-0.5 flex items-center space-x-2">
                        <span>{machineActionBanner.title}</span>
                        {machineActionBanner.type === 'blocked' && (
                          <span className="text-[10px] bg-red-200 text-red-800 px-2 py-0.2 rounded-full uppercase font-black">
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

              {/* ═══ 2-COLUMN BALANCED INDUSTRIAL LAYOUT: LEFT (UNITS + PERMANENT SCADA AI CHAT) & RIGHT (3D DIGITAL TWIN + CONTROLS) ═══ */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
                {/* ─── LEFT COLUMN: MACHINE SELECTOR + PERMANENT SCADA AI CHAT (5 COLS) ─── */}
                <div className="lg:col-span-5 space-y-4">
                  {/* 1. Machine Units Quick Selector (Accordion / Compact Cards) */}
                  <div className="glass-panel p-3.5 rounded-2xl border border-slate-200/80 bg-white shadow-2xs space-y-2.5">
                    <div className="flex items-center justify-between pb-1 border-b border-slate-100">
                      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                        <Cpu className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Refinery Units ({machineryList.length})</span>
                      </span>
                      <span className="text-[10px] text-slate-400">Click unit to sync twin & chat</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      {machineryList.map((m) => {
                        const isRunning = m.status === 'RUNNING';
                        const isThrottled = m.status === 'THROTTLED';
                        const isSelected = selectedMachineId === m.id;

                        return (
                          <div
                            key={m.id}
                            onClick={() => setSelectedMachineId(m.id)}
                            className={`p-2.5 rounded-xl border transition-all cursor-pointer relative overflow-hidden ${
                              isSelected
                                ? 'border-indigo-600 ring-2 ring-indigo-200 bg-indigo-50/40 shadow-xs'
                                : 'border-slate-200 bg-slate-50/50 hover:bg-white hover:border-indigo-300'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                                isSelected ? 'bg-indigo-600 text-white' : 'bg-white text-indigo-700 border border-slate-200'
                              }`}>
                                {m.id}
                              </span>
                              <span className={`w-2 h-2 rounded-full ${
                                isRunning ? 'bg-emerald-500 animate-pulse' : isThrottled ? 'bg-amber-500' : 'bg-red-500'
                              }`} />
                            </div>
                            <h4 className="text-[11px] font-bold text-slate-800 truncate mt-1">{m.name}</h4>
                            <div className="flex justify-between items-center text-[9px] font-mono text-slate-500 mt-1">
                              <span>{m.rpm} RPM</span>
                              <span className="font-bold text-amber-600">{m.temperature_c}°C</span>
                            </div>
                            <div className="flex justify-between items-center text-[8px] font-mono text-slate-400 mt-0.5 pt-0.5 border-t border-slate-100">
                              <span className="text-indigo-600 font-bold">H: {m.health_index || 92}%</span>
                              <span>{m.vibration_mms} mm/s</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* 2. Permanent SCADA AI Chat & Actuator on Left Side */}
                  <div className="glass-panel p-4 rounded-2xl border border-slate-200 bg-white shadow-md flex flex-col h-[490px]">
                    {/* Chat Header */}
                    <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
                      <div className="flex items-center space-x-2">
                        <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs">
                          <Bot className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                            <span>SCADA AI Actuator</span>
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          </div>
                          <span className="text-[10px] text-slate-400">Target: {selectedMachine.id}</span>
                        </div>
                      </div>
                      <span className="text-[9px] uppercase font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-md">
                        {currentUser.role}
                      </span>
                    </div>

                    {/* Chat Message Stream */}
                    <div className="flex-1 overflow-y-auto py-3 space-y-2.5 text-xs pr-1 font-sans">
                      {machineChatHistory.map((item, idx) => (
                        <div
                          key={idx}
                          className={`flex ${item.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[88%] p-2.5 rounded-2xl leading-relaxed whitespace-pre-wrap ${
                              item.sender === 'user'
                                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-br-xs shadow-xs'
                                : item.status === 'blocked'
                                ? 'bg-red-50 text-red-900 border border-red-200 rounded-bl-xs'
                                : item.status === 'granted'
                                ? 'bg-emerald-50 text-emerald-900 border border-emerald-200 rounded-bl-xs'
                                : 'bg-slate-100 text-slate-700 rounded-bl-xs'
                            }`}
                          >
                            <div className="text-[11px]">{item.text}</div>
                            <div className={`text-[9px] mt-1 flex items-center justify-between ${item.sender === 'user' ? 'text-indigo-200' : 'text-slate-400'}`}>
                              <span>{item.timestamp}</span>
                              {item.status && (
                                <span className={`font-mono text-[8px] uppercase px-1 rounded font-bold ${
                                  item.status === 'granted' ? 'bg-emerald-200 text-emerald-800' : 'bg-red-200 text-red-800'
                                }`}>
                                  {item.status}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Quick Action Chips */}
                    <div className="py-1.5 flex items-center space-x-1.5 overflow-x-auto text-[10px] border-t border-slate-100">
                      <span className="text-slate-400 font-bold shrink-0">Quick:</span>
                      <button
                        type="button"
                        onClick={() => setMachineVoiceCommand(`emergency trip ${selectedMachine.id}`)}
                        className="px-2 py-0.5 rounded-full bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 shrink-0 cursor-pointer font-semibold"
                      >
                        ⚡ Trip
                      </button>
                      <button
                        type="button"
                        onClick={() => setMachineVoiceCommand(`increase speed ${selectedMachine.id} by 20%`)}
                        className="px-2 py-0.5 rounded-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 shrink-0 cursor-pointer font-semibold"
                      >
                        🚀 Speed +20%
                      </button>
                      <button
                        type="button"
                        onClick={() => setMachineVoiceCommand(`purge relief valve on ${selectedMachine.id}`)}
                        className="px-2 py-0.5 rounded-full bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 shrink-0 cursor-pointer font-semibold"
                      >
                        💨 Purge
                      </button>
                      <button
                        type="button"
                        onClick={() => setMachineVoiceCommand(`lube circulate on ${selectedMachine.id}`)}
                        className="px-2 py-0.5 rounded-full bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 shrink-0 cursor-pointer font-semibold"
                      >
                        🛢️ Lube Boost
                      </button>
                      <button
                        type="button"
                        onClick={() => setMachineVoiceCommand(`cooling flush ${selectedMachine.id}`)}
                        className="px-2 py-0.5 rounded-full bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border border-cyan-200 shrink-0 cursor-pointer font-semibold"
                      >
                        ❄️ Cool Flush
                      </button>
                      <button
                        type="button"
                        onClick={() => setMachineVoiceCommand(`halt ${selectedMachine.id}`)}
                        className="px-2 py-0.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 shrink-0 cursor-pointer font-semibold"
                      >
                        🛑 Halt
                      </button>
                      <button
                        type="button"
                        onClick={() => setMachineVoiceCommand(`start sequence ${selectedMachine.id}`)}
                        className="px-2 py-0.5 rounded-full bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 shrink-0 cursor-pointer font-semibold"
                      >
                        🟢 Start
                      </button>
                    </div>

                    {/* Chat Input Form */}
                    <form onSubmit={handleVoiceAiCommand} className="pt-2 border-t border-slate-100 flex items-center space-x-2">
                      <div className="relative flex-1">
                        <input
                          type="text"
                          value={machineVoiceCommand}
                          onChange={(e) => setMachineVoiceCommand(e.target.value)}
                          placeholder={`Ask AI to control ${selectedMachine.id}...`}
                          className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 border border-slate-200 focus:border-indigo-500 focus:bg-white outline-none pr-8 transition-all"
                        />
                        <button
                          type="button"
                          onClick={() => setMachineVoiceCommand(`AI stop ${selectedMachine.id}`)}
                          className="absolute right-2 top-2 p-0.5 text-slate-400 hover:text-indigo-600 cursor-pointer"
                          title="Auto-fill stop prompt"
                        >
                          <Zap className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <button
                        type="submit"
                        disabled={machineAiLoading || !machineVoiceCommand.trim()}
                        className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs font-bold flex items-center space-x-1 shadow-sm transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        {machineAiLoading ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Send className="w-3.5 h-3.5" />
                        )}
                        <span>Send</span>
                      </button>
                    </form>
                  </div>

                  {/* Policy Info Card */}
                  <div className="glass-panel p-3 bg-gradient-to-br from-indigo-50/40 via-white to-sky-50/30 border border-indigo-200/60 rounded-xl flex items-start space-x-2.5 text-xs text-slate-600">
                    <Shield className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-bold text-slate-800 text-[11px]">Deterministic Safety Gate</h4>
                      <p className="text-[10px] text-slate-500 mt-0.5 leading-snug">
                        Actions undergo central RBAC clearance validation before triggering physical 3D twin actuators.
                      </p>
                    </div>
                  </div>
                </div>

                {/* ─── RIGHT COLUMN: 3D DIGITAL TWIN & REAL-TIME PARAMETERS (7 COLS) ─── */}
                <div className="lg:col-span-7 space-y-4">
                  {/* 1. Large 3D Digital Twin Canvas Card */}
                  <div className="glass-panel p-4 rounded-3xl border border-slate-200 bg-white shadow-lg overflow-hidden flex flex-col">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded-md">
                            {selectedMachine.id}
                          </span>
                          <span className="text-xs font-bold text-slate-800">{selectedMachine.name}</span>
                        </div>
                        <span className="text-[10px] text-slate-400 mt-0.5 block">{selectedMachine.unit} · Drag mouse to orbit 3D view</span>
                      </div>

                      <div className="flex items-center space-x-2">
                        {/* ISO Diagnostics Action */}
                        <button
                          onClick={async () => {
                            setIsDiagnosticsLoading(true);
                            setActiveMachineModal('diagnostics');
                            try {
                              const r = await fetch(`${API}/api/machinery/diagnostics/${selectedMachine.id}`);
                              const d = await r.json();
                              setMachineDiagnosticsData(d);
                            } catch (e: any) {
                              alert(`Diagnostics error: ${e.message}`);
                            } finally {
                              setIsDiagnosticsLoading(false);
                            }
                          }}
                          className="px-2.5 py-1 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-bold flex items-center space-x-1 cursor-pointer transition-all shadow-2xs"
                          title="View ISO 10816-3 FFT Spectrum & RUL Analytics"
                        >
                          <Activity className="w-3.5 h-3.5 text-indigo-600" />
                          <span>ISO Diagnostics</span>
                        </button>

                        {/* Trip Replay Action */}
                        <button
                          onClick={async () => {
                            setActiveMachineModal('replay');
                            try {
                              const r = await fetch(`${API}/api/machinery/trip-replay/${selectedMachine.id}`);
                              const d = await r.json();
                              setMachineReplayData(d);
                            } catch (e: any) {
                              alert(`Replay error: ${e.message}`);
                            }
                          }}
                          className="px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-bold flex items-center space-x-1 cursor-pointer transition-all shadow-2xs"
                          title="Open 200 Hz Blackbox Trip Replay & Forensics"
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-slate-600" />
                          <span>Trip Replay</span>
                        </button>

                        {/* CMMS Work Order Action */}
                        <button
                          onClick={() => {
                            setWorkOrderDescription(`Mechanical vibration inspection and shaft alignment verification for ${selectedMachine.name} (${selectedMachine.unit}).`);
                            setWorkOrderResult(null);
                            setActiveMachineModal('work_order');
                          }}
                          className="px-2.5 py-1 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 text-xs font-bold flex items-center space-x-1 cursor-pointer transition-all shadow-2xs"
                          title="Generate SAP/Maximo CMMS Work Order"
                        >
                          <Wrench className="w-3.5 h-3.5 text-amber-600" />
                          <span>CMMS Order</span>
                        </button>

                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold flex items-center space-x-1.5 ${
                          isSelectedRunning ? 'bg-emerald-100 text-emerald-700 border border-emerald-300' :
                          isSelectedThrottled ? 'bg-amber-100 text-amber-700 border border-amber-300' :
                          'bg-red-100 text-red-700 border border-red-300'
                        }`}>
                          <span className={`w-2 h-2 rounded-full ${
                            isSelectedRunning ? 'bg-emerald-500 animate-ping' : isSelectedThrottled ? 'bg-amber-500' : 'bg-red-500'
                          }`} />
                          <span>{selectedMachine.status}</span>
                        </span>
                      </div>
                    </div>

                    {/* WebGL 3D Canvas Box (Expanded full viewport height) */}
                    <div className="my-3 rounded-2xl bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white relative overflow-hidden shadow-2xl border border-slate-800/90 flex flex-col items-center justify-center">
                      <ThreeMachineCanvas machineId={selectedMachine.id} status={selectedMachine.status} rpm={selectedMachine.rpm} height={360} />

                      {/* Live SCADA Telemetry Bar (6 Essential Sensor Channels) */}
                      <div className="w-full bg-slate-950/85 backdrop-blur-md px-4 py-2 border-t border-slate-800/80 grid grid-cols-3 md:grid-cols-6 gap-2 font-mono text-[11px]">
                        <div>
                          <span className="text-slate-400 text-[10px] block">RPM SHAFT</span>
                          <span className={`font-bold ${isSelectedRunning ? 'text-emerald-400' : 'text-slate-500'}`}>{selectedMachine.rpm}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">VIBRATION</span>
                          <span className={`font-bold ${selectedMachine.vibration_mms > 2.5 ? 'text-amber-400' : 'text-slate-300'}`}>{selectedMachine.vibration_mms} mm/s</span>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">CASING PRES</span>
                          <span className="text-sky-300 font-bold">{selectedMachine.pressure_bar} Bar</span>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">CORE TEMP</span>
                          <span className="text-amber-300 font-bold">{selectedMachine.temperature_c} °C</span>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">LUBE OIL</span>
                          <span className="text-indigo-300 font-bold">{selectedMachine.lube_oil_pressure_bar || 3.8} Bar</span>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] block">HEALTH / GAS</span>
                          <span className="text-emerald-300 font-bold">{selectedMachine.health_index || 92}% <span className="text-slate-400 font-normal text-[9px]">({selectedMachine.gas_detector_ppm || 1.2} ppm)</span></span>
                        </div>
                      </div>
                    </div>

                    {/* Interactive Parameter Control Dashboard */}
                    <div className="mt-2 p-3 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider flex items-center space-x-1.5">
                          <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-600" />
                          <span>Live Parameter Tuning & SCADA Actuators</span>
                        </span>
                        <span className="text-[10px] text-slate-400">Requires Grade 2+ Clearance</span>
                      </div>

                      {/* Interactive Sliders Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {/* RPM Slider */}
                        <div className="bg-white p-2.5 rounded-xl border border-slate-200/70 shadow-2xs">
                          <div className="flex justify-between items-center text-[10px] font-semibold mb-1">
                            <span className="text-slate-500">Shaft RPM</span>
                            <span className="font-mono font-bold text-indigo-600">{selectedMachine.rpm} RPM</span>
                          </div>
                          <input
                            type="range"
                            min="0"
                            max={selectedMachine.id.includes('COMPRESSOR') ? 14000 : 5000}
                            step="50"
                            value={selectedMachine.rpm}
                            onChange={(e) => {
                              const newRpm = parseInt(e.target.value);
                              handleMachineControl(selectedMachine.id, 'SET_PARAM', `Set ${selectedMachine.id} RPM to ${newRpm}`, { rpm: newRpm });
                            }}
                            className="w-full accent-indigo-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg appearance-none"
                          />
                        </div>

                        {/* Pressure Slider */}
                        <div className="bg-white p-2.5 rounded-xl border border-slate-200/70 shadow-2xs">
                          <div className="flex justify-between items-center text-[10px] font-semibold mb-1">
                            <span className="text-slate-500">Casing Pressure</span>
                            <span className="font-mono font-bold text-sky-600">{selectedMachine.pressure_bar} Bar</span>
                          </div>
                          <input
                            type="range"
                            min="1"
                            max={selectedMachine.id.includes('COMPRESSOR') ? 200 : 50}
                            step="0.5"
                            value={selectedMachine.pressure_bar}
                            onChange={(e) => {
                              const newP = parseFloat(e.target.value);
                              handleMachineControl(selectedMachine.id, 'SET_PARAM', `Adjust ${selectedMachine.id} pressure to ${newP} Bar`, { pressure_bar: newP });
                            }}
                            className="w-full accent-sky-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg appearance-none"
                          />
                        </div>
                      </div>

                      {/* Multi-Parameter Actuator Buttons */}
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        {isSelectedRunning ? (
                          <>
                            <button
                              onClick={() => handleMachineControl(selectedMachine.id, 'BOOST', `Overdrive Boost (+25% RPM) on ${selectedMachine.name}`)}
                              className="px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-bold text-xs flex items-center space-x-1.5 transition-all cursor-pointer shadow-2xs"
                              title="Increase RPM and flow by 25%"
                            >
                              <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                              <span>Speed Boost (+25%)</span>
                            </button>

                            <button
                              onClick={() => handleMachineControl(selectedMachine.id, 'THROTTLE', `Throttle 50% on ${selectedMachine.name}`)}
                              className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 font-bold text-xs flex items-center space-x-1.5 transition-all cursor-pointer shadow-2xs"
                              title="Reduce flow and speed by 50%"
                            >
                              <TrendingDown className="w-3.5 h-3.5 text-amber-600" />
                              <span>Throttle (50%)</span>
                            </button>

                            <button
                              onClick={() => handleMachineControl(selectedMachine.id, 'PURGE_VALVE', `Emergency Pressure Relief & Vent for ${selectedMachine.name}`)}
                              className="px-3 py-1.5 rounded-xl bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 font-bold text-xs flex items-center space-x-1.5 transition-all cursor-pointer shadow-2xs"
                              title="Vent pressure safely through relief line"
                            >
                              <Wind className="w-3.5 h-3.5 text-sky-600" />
                              <span>Purge Relief</span>
                            </button>

                            <button
                              onClick={() => handleMachineControl(selectedMachine.id, 'LUBE_CIRCULATE', `Auxiliary Lube Circulation Pump for ${selectedMachine.name}`)}
                              className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 font-bold text-xs flex items-center space-x-1.5 transition-all cursor-pointer shadow-2xs"
                              title="Boost lubrication oil header pressure and bearing cooling"
                            >
                              <Activity className="w-3.5 h-3.5 text-amber-600" />
                              <span>Lube Boost (+1.2 Bar)</span>
                            </button>

                            <button
                              onClick={() => handleMachineControl(selectedMachine.id, 'COOLING_FLUSH', `Jacket Cooling Flush for ${selectedMachine.name}`)}
                              className="px-3 py-1.5 rounded-xl bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border border-cyan-200 font-bold text-xs flex items-center space-x-1.5 transition-all cursor-pointer shadow-2xs"
                              title="Engage secondary heat exchanger flush to suppress core temperature"
                            >
                              <RefreshCw className="w-3.5 h-3.5 text-cyan-600" />
                              <span>Coolant Flush (-14°C)</span>
                            </button>

                            <button
                              onClick={() => handleMachineControl(selectedMachine.id, 'STOP', `Emergency Halt for ${selectedMachine.name}`)}
                              className="px-3.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center space-x-1.5 shadow-sm transition-all cursor-pointer"
                              title="Trip machine instantly via policy engine"
                            >
                              <Octagon className="w-3.5 h-3.5" />
                              <span>Emergency Trip (Stop)</span>
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => handleMachineControl(selectedMachine.id, 'START', `Startup command for ${selectedMachine.name}`)}
                              className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center space-x-1.5 shadow-sm transition-all cursor-pointer"
                            >
                              <Power className="w-3.5 h-3.5" />
                              <span>Start Machine</span>
                            </button>
                            <span className="text-[11px] text-slate-400 italic">Machine halted. Click Start or use AI prompt to spin up.</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              {/* ═══ REAL INDUSTRIAL MODALS: DIAGNOSTICS, TRIP REPLAY, CMMS ═══ */}
              <AnimatePresence>
                {activeMachineModal === 'diagnostics' && (
                  <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
                    <motion.div
                      initial={{ scale: 0.95, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.95, opacity: 0 }}
                      className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto"
                    >
                      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                        <div className="flex items-center space-x-2.5">
                          <div className="w-9 h-9 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-500/20">
                            <Activity className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-bold text-slate-800 text-base">ISO 10816-3 Machinery Health & FFT Spectrum</h3>
                            <p className="text-xs text-slate-400">{selectedMachine.name} ({selectedMachine.id})</p>
                          </div>
                        </div>
                        <button onClick={() => setActiveMachineModal('none')} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer">
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {isDiagnosticsLoading || !machineDiagnosticsData ? (
                        <div className="py-12 flex flex-col items-center justify-center space-y-2 text-slate-400 text-xs">
                          <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
                          <span>Computing fast Fourier transform (FFT) harmonics...</span>
                        </div>
                      ) : (
                        <div className="space-y-4 text-xs">
                          {/* Overall Health Score & ISO Category */}
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div className="p-3 rounded-2xl bg-indigo-50/70 border border-indigo-200/60">
                              <span className="text-[10px] uppercase font-bold text-indigo-500">Asset Health Score</span>
                              <div className="text-xl font-black text-indigo-900 mt-0.5">{machineDiagnosticsData.health_score}%</div>
                              <span className="text-[9px] text-indigo-400">Dynamic Reliability Index</span>
                            </div>
                            <div className="p-3 rounded-2xl bg-emerald-50/70 border border-emerald-200/60">
                              <span className="text-[10px] uppercase font-bold text-emerald-600">ISO Severity</span>
                              <div className="text-xs font-black text-emerald-900 mt-1">{machineDiagnosticsData.iso_10816?.severity_zone}</div>
                              <span className="text-[9px] text-emerald-500">{machineDiagnosticsData.iso_10816?.measured_velocity_mms} mm/s RMS</span>
                            </div>
                            <div className="p-3 rounded-2xl bg-sky-50/70 border border-sky-200/60">
                              <span className="text-[10px] uppercase font-bold text-sky-600">Estimated RUL</span>
                              <div className="text-xl font-black text-sky-900 mt-0.5">{machineDiagnosticsData.rul_projection?.estimated_remaining_days} Days</div>
                              <span className="text-[9px] text-sky-400">API 670 Bearing Life</span>
                            </div>
                            <div className="p-3 rounded-2xl bg-amber-50/70 border border-amber-200/60">
                              <span className="text-[10px] uppercase font-bold text-amber-600">Lube Interval</span>
                              <div className="text-xl font-black text-amber-900 mt-0.5">720 Hrs</div>
                              <span className="text-[9px] text-amber-500">ISO VG-46 Synthetic</span>
                            </div>
                          </div>

                          {/* Spectral Harmonics Breakdown */}
                          <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2">
                            <div className="font-bold text-slate-700 flex items-center justify-between">
                              <span>Spectral Harmonic Decomposition (1X, 2X, 3X, Bearing Pass)</span>
                              <span className="text-[10px] text-slate-400 font-mono">Sample: 2.5 kHz Piezo</span>
                            </div>
                            <div className="space-y-2 font-mono">
                              {machineDiagnosticsData.vibration_fft_spectrum?.map((item: any, idx: number) => (
                                <div key={idx} className="bg-white p-2.5 rounded-xl border border-slate-200/60 flex items-center justify-between text-[11px]">
                                  <div>
                                    <span className="font-bold text-indigo-700">{item.frequency_hz} Hz</span>
                                    <span className="text-slate-400 ml-2 text-[10px]">({item.order})</span>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <div className="w-24 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                      <div className="bg-indigo-600 h-1.5 rounded-full" style={{ width: `${Math.min(100, item.amplitude_mms * 30)}%` }} />
                                    </div>
                                    <span className="font-bold text-slate-700">{item.amplitude_mms} mm/s</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Action Button */}
                          <div className="flex justify-end pt-2">
                            <button
                              onClick={() => {
                                setActiveMachineModal('none');
                                setWorkOrderDescription(`Preventive maintenance triggered from ISO 10816 Diagnostics for ${selectedMachine.name}. Current vibration: ${selectedMachine.vibration_mms} mm/s.`);
                                setActiveMachineModal('work_order');
                              }}
                              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center space-x-1.5 cursor-pointer shadow-xs"
                            >
                              <Wrench className="w-3.5 h-3.5" />
                              <span>Create Preventive Work Order</span>
                            </button>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  </div>
                )}

                {activeMachineModal === 'replay' && (
                  <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
                    <motion.div
                      initial={{ scale: 0.95, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.95, opacity: 0 }}
                      className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto"
                    >
                      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                        <div className="flex items-center space-x-2.5">
                          <div className="w-9 h-9 rounded-xl bg-slate-800 text-white flex items-center justify-center shadow-md">
                            <RotateCcw className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-bold text-slate-800 text-base">200 Hz Blackbox Trip Replay & Forensics</h3>
                            <p className="text-xs text-slate-400">{selectedMachine.name} · Triconex SIS Recorder</p>
                          </div>
                        </div>
                        <button onClick={() => setActiveMachineModal('none')} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer">
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {machineReplayData && (
                        <div className="space-y-4 text-xs">
                          <div className="p-3 rounded-2xl bg-red-50 border border-red-200 text-red-900">
                            <div className="font-bold text-xs">Root Cause Trigger</div>
                            <p className="text-[11px] text-red-700 mt-0.5">{machineReplayData.trip_cause}</p>
                            <div className="text-[10px] text-red-500 font-semibold mt-1">Recommended Action: {machineReplayData.resolution_action}</div>
                          </div>

                          <div className="space-y-2">
                            <span className="font-bold text-slate-700">Forensic Chronological Trace (T-5.0s to T+5.0s):</span>
                            <div className="space-y-1.5 font-mono text-[11px]">
                              {machineReplayData.recorded_frames?.map((f: any, idx: number) => (
                                <div key={idx} className={`p-2 rounded-xl border flex items-center justify-between ${
                                  f.event.includes('TRIP') ? 'bg-red-50 border-red-300 text-red-900 font-bold' : 'bg-slate-50 border-slate-200/70 text-slate-700'
                                }`}>
                                  <div className="flex items-center space-x-3">
                                    <span className="font-bold text-indigo-600">{f.t_offset_sec > 0 ? `+${f.t_offset_sec}` : f.t_offset_sec}s</span>
                                    <span>{f.event}</span>
                                  </div>
                                  <div className="flex items-center space-x-3 text-[10px]">
                                    <span>{f.rpm} RPM</span>
                                    <span>{f.vibration_mms} mm/s</span>
                                    <span>{f.casing_temp} °C</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  </div>
                )}

                {activeMachineModal === 'work_order' && (
                  <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
                    <motion.div
                      initial={{ scale: 0.95, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.95, opacity: 0 }}
                      className="bg-white rounded-3xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-4"
                    >
                      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                        <div className="flex items-center space-x-2.5">
                          <div className="w-9 h-9 rounded-xl bg-amber-600 text-white flex items-center justify-center shadow-md">
                            <Wrench className="w-5 h-5" />
                          </div>
                          <div>
                            <h3 className="font-bold text-slate-800 text-base">Generate SAP/Maximo CMMS Work Order</h3>
                            <p className="text-xs text-slate-400">Target: {selectedMachine.name} ({selectedMachine.id})</p>
                          </div>
                        </div>
                        <button onClick={() => setActiveMachineModal('none')} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 cursor-pointer">
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {workOrderResult ? (
                        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-2 text-xs">
                          <div className="font-bold flex items-center space-x-1.5 text-sm">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            <span>Work Order Successfully Dispatched</span>
                          </div>
                          <p className="font-mono text-xs">ID: {workOrderResult.work_order_id} ({workOrderResult.priority})</p>
                          <p className="text-[11px] text-emerald-700">Assigned: {workOrderResult.assigned_crew} · Downtime: ~{workOrderResult.estimated_downtime_hours} hrs</p>
                          <div className="text-[10px] text-emerald-600 font-medium">Requisitioned parts: {workOrderResult.required_spare_parts?.join(', ')}</div>
                          <button
                            onClick={() => setActiveMachineModal('none')}
                            className="mt-3 w-full py-2 rounded-xl bg-emerald-600 text-white font-bold text-xs cursor-pointer"
                          >
                            Done
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-3 text-xs">
                          <div>
                            <label className="block text-slate-600 font-bold mb-1">Priority Classification</label>
                            <select
                              value={workOrderPriority}
                              onChange={(e) => setWorkOrderPriority(e.target.value)}
                              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs bg-slate-50 outline-none focus:border-indigo-500 font-medium"
                            >
                              <option value="CRITICAL">CRITICAL (Immediate Plant Safety Hazard)</option>
                              <option value="HIGH">HIGH (Bearing Deviation / Vibration Spike)</option>
                              <option value="MEDIUM">MEDIUM (Scheduled Preventative Overhaul)</option>
                              <option value="LOW">LOW (Cosmetic / Lubricant Top-up)</option>
                            </select>
                          </div>

                          <div>
                            <label className="block text-slate-600 font-bold mb-1">Scope of Maintenance</label>
                            <textarea
                              rows={3}
                              value={workOrderDescription}
                              onChange={(e) => setWorkOrderDescription(e.target.value)}
                              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs bg-slate-50 outline-none focus:border-indigo-500 font-medium resize-none"
                            />
                          </div>

                          <button
                            onClick={async () => {
                              try {
                                const r = await fetch(`${API}/api/machinery/work-order/create`, {
                                  method: 'POST',
                                  headers: authHeaders({ 'Content-Type': 'application/json' }),
                                  body: JSON.stringify({
                                    machine_id: selectedMachine.id,
                                    priority: workOrderPriority,
                                    description: workOrderDescription
                                  })
                                });
                                const d = await r.json();
                                setWorkOrderResult(d);
                              } catch (e: any) {
                                alert(`Error creating work order: ${e.message}`);
                              }
                            }}
                            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs flex items-center justify-center space-x-2 cursor-pointer shadow-xs"
                          >
                            <Wrench className="w-3.5 h-3.5" />
                            <span>Dispatch Work Order to Field Crew</span>
                          </button>
                        </div>
                      )}
                    </motion.div>
                  </div>
                )}
              </AnimatePresence>
            </div>
          );
        })()}

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
        {/* ══════════════════════════════════════════════════════════════
            8. MODELS & HARDWARE (STRICT BRUTALISM WITH BRAND LOGOS)
        ══════════════════════════════════════════════════════════════ */}
        {activeTab === 'models' && (
          <div className="flex-1 flex flex-col p-6 max-w-6xl mx-auto w-full overflow-y-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b-[3px] border-black pb-4">
              <div>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-[#ffe600] border-2 border-black flex items-center justify-center shadow-[3px_3px_0px_#000000]">
                    <Database className="w-5 h-5 text-black" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-black font-mono text-black uppercase tracking-tight">MODELS & VRAM ALLOCATION</h1>
                    <p className="text-xs font-mono text-black font-semibold uppercase">Hardware Memory Budget, LLM Swapping Engine & Specialist Registry</p>
                  </div>
                </div>
              </div>
              <button
                onClick={() => { fetchModels(); fetchMetrics(); }}
                className="px-4 py-2 bg-black hover:bg-[#ffe600] text-white hover:text-black text-xs font-black font-mono uppercase tracking-wider flex items-center space-x-2 border-2 border-black shadow-[3px_3px_0px_#000000] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1" />
                <span>REFRESH KERNEL</span>
              </button>
            </div>

            {/* Hardware & VRAM Overview Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* System VRAM Budget Card */}
              <div className="bg-white p-5 border-[3px] border-black shadow-[6px_6px_0px_#000000] relative">
                <div className="flex items-center justify-between border-b-2 border-black pb-3 mb-4">
                  <div className="flex items-center space-x-2">
                    {/* NVIDIA Logo Badge */}
                    <div className="px-2 py-0.5 bg-[#76B900] text-black font-mono font-black text-xs border border-black flex items-center space-x-1 shadow-[2px_2px_0px_#000000]">
                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M7.4 3C4.4 3 2 5.4 2 8.4v7.2C2 18.6 4.4 21 7.4 21h9.2c3 0 5.4-2.4 5.4-5.4V8.4C22 5.4 19.6 3 16.6 3H7.4zm0 2h9.2c1.9 0 3.4 1.5 3.4 3.4v7.2c0 1.9-1.5 3.4-3.4 3.4H7.4C5.5 19 4 17.5 4 15.6V8.4C4 6.5 5.5 5 7.4 5zM9 8v8l7-4-7-4z"/>
                      </svg>
                      <span>NVIDIA CUDA</span>
                    </div>
                    <span className="font-mono font-black text-xs uppercase text-black">GPU VRAM BUDGET</span>
                  </div>
                  <span className={`text-[10px] font-black font-mono px-2 py-0.5 border border-black uppercase ${systemStatus?.status === 'online' ? 'bg-[#00e676] text-black' : 'bg-[#ff3366] text-white'}`}>
                    KERNEL: {systemStatus?.status || 'ONLINE'}
                  </span>
                </div>

                {systemStatus ? (
                  <div className="space-y-4 font-mono">
                    <div>
                      <div className="flex justify-between items-baseline mb-1.5">
                        <span className="text-xs font-bold text-black uppercase">Allocated VRAM</span>
                        <span className="text-lg font-black text-black">
                          {systemStatus.vram_used_mb || 1200} <span className="text-xs font-normal text-slate-600">/ {systemStatus.vram_budget_mb || 7168} MB</span>
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 h-4 border-2 border-black p-0.5">
                        <div
                          className="bg-black h-full transition-all duration-300"
                          style={{ width: `${Math.min(100, ((systemStatus.vram_used_mb || 1200) / (systemStatus.vram_budget_mb || 7168)) * 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-[10px] text-slate-600 mt-1">
                        <span>0 MB</span>
                        <span className="font-bold text-black">{Math.round(((systemStatus.vram_used_mb || 1200) / (systemStatus.vram_budget_mb || 7168)) * 100)}% UTILIZED</span>
                        <span>{systemStatus.vram_budget_mb || 7168} MB LIMIT</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-2 border-t-2 border-black text-xs">
                      <div className="p-2 bg-[#f5f4ef] border border-black">
                        <span className="text-[10px] text-slate-500 uppercase block font-bold">Safety Margin</span>
                        <span className="text-sm font-black text-black">1,024 MB</span>
                      </div>
                      <div className="p-2 bg-[#f5f4ef] border border-black">
                        <span className="text-[10px] text-slate-500 uppercase block font-bold">Eviction Policy</span>
                        <span className="text-sm font-black text-black">LRU SWAP</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs font-mono text-black flex items-center py-4">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin text-black" />
                    <span>READING GPU MEMORY CONTROLLER...</span>
                  </div>
                )}
              </div>

              {/* Execution & Swap Metrics Card */}
              <div className="bg-white p-5 border-[3px] border-black shadow-[6px_6px_0px_#000000]">
                <div className="flex items-center justify-between border-b-2 border-black pb-3 mb-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 bg-[#00f0ff] border border-black flex items-center justify-center">
                      <Activity className="w-3.5 h-3.5 text-black" />
                    </div>
                    <span className="font-mono font-black text-xs uppercase text-black">DYNAMIC SWAP ENGINE METRICS</span>
                  </div>
                  <span className="text-[10px] font-black font-mono px-2 py-0.5 bg-[#ffe600] border border-black text-black uppercase">
                    0ms RESIDENT REUSE
                  </span>
                </div>

                {modelMetrics ? (
                  <div className="space-y-3 font-mono text-xs">
                    <div className="flex justify-between items-center p-2 bg-[#f5f4ef] border border-black">
                      <span className="font-bold uppercase text-black">Worker Model Swaps</span>
                      <span className="font-black text-base text-black bg-white px-2 py-0.5 border border-black">{modelMetrics.swaps_count || 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-2 bg-[#f5f4ef] border border-black">
                      <span className="font-bold uppercase text-black">Resident Worker Reuses</span>
                      <span className="font-black text-base text-emerald-700 bg-white px-2 py-0.5 border border-black">{modelMetrics.reuses_count || 0}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 bg-[#f5f4ef] border border-black">
                        <span className="text-[10px] text-slate-500 uppercase block font-bold">Total Load Latency</span>
                        <span className="text-sm font-black text-black">{Math.round(modelMetrics.total_load_time_ms || 0)} ms</span>
                      </div>
                      <div className="p-2 bg-[#f5f4ef] border border-black">
                        <span className="text-[10px] text-slate-500 uppercase block font-bold">Inference Compute</span>
                        <span className="text-sm font-black text-black">{Math.round(modelMetrics.total_inference_time_ms || 0)} ms</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-xs font-mono text-black flex items-center py-4">
                    <Loader2 className="w-4 h-4 mr-2 animate-spin text-black" />
                    <span>FETCHING METRICS TELEMETRY...</span>
                  </div>
                )}
              </div>
            </div>

            {/* Registered Specialist Workers Section with High-Fidelity Logos */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-black font-mono text-black uppercase tracking-wider flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-black" />
                  <span>REGISTERED SPECIALIST WORKERS & LOGOS</span>
                </h2>
                <span className="text-xs font-mono text-black font-bold uppercase bg-[#ffe600] px-2 py-0.5 border border-black">
                  AIR-GAPPED OPEN-WEIGHT LOCAL ARTIFACTS
                </span>
              </div>

              <div className="space-y-3">
                {models.map((m, i) => {
                  // Determine provider logo and badge
                  const nameLower = (m.model_name || '').toLowerCase();
                  const workerLower = (m.worker_type || '').toLowerCase();

                  let providerBadge = {
                    name: 'ALIBABA CLOUD',
                    bg: 'bg-[#ff6600]',
                    color: 'text-white',
                    logoType: 'qwen'
                  };

                  if (nameLower.includes('organizer') || workerLower.includes('organizer')) {
                    providerBadge = {
                      name: 'MUSKY SOVEREIGN',
                      bg: 'bg-black',
                      color: 'text-[#ffe600]',
                      logoType: 'musky'
                    };
                  } else if (nameLower.includes('gemma') || nameLower.includes('google')) {
                    providerBadge = {
                      name: 'GOOGLE DEEPMIND',
                      bg: 'bg-[#4285F4]',
                      color: 'text-white',
                      logoType: 'google'
                    };
                  } else if (nameLower.includes('meta') || nameLower.includes('llama')) {
                    providerBadge = {
                      name: 'META AI',
                      bg: 'bg-[#0081FB]',
                      color: 'text-white',
                      logoType: 'meta'
                    };
                  } else if (nameLower.includes('qwen')) {
                    providerBadge = {
                      name: 'ALIBABA QWEN',
                      bg: 'bg-[#615ced]',
                      color: 'text-white',
                      logoType: 'qwen'
                    };
                  }

                  const vramPercent = Math.min(100, Math.round((m.vram_required_mb / (systemStatus?.vram_budget_mb || 7168)) * 100));

                  return (
                    <div
                      key={i}
                      className="bg-white p-4 border-[2.5px] border-black shadow-[4px_4px_0px_#000000] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[6px_6px_0px_#000000] transition-all"
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="flex items-start space-x-3.5">
                          {/* Dedicated Brand Logo Avatar */}
                          <div className={`w-12 h-12 border-2 border-black flex items-center justify-center shrink-0 shadow-[2px_2px_0px_#000000] ${
                            providerBadge.logoType === 'musky'
                              ? 'bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 text-white'
                              : providerBadge.logoType === 'google'
                              ? 'bg-white text-[#4285F4]'
                              : providerBadge.logoType === 'qwen'
                              ? 'bg-[#615ced] text-white'
                              : 'bg-black text-white'
                          }`}>
                            {providerBadge.logoType === 'musky' && (
                              <span className="font-cursive text-2xl font-black leading-none pb-0.5">M</span>
                            )}
                            {providerBadge.logoType === 'google' && (
                              <svg className="w-7 h-7" viewBox="0 0 24 24">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                              </svg>
                            )}
                            {providerBadge.logoType === 'qwen' && (
                              <div className="flex flex-col items-center justify-center">
                                <span className="font-mono font-black text-sm tracking-tighter leading-none">通义</span>
                                <span className="text-[8px] font-mono font-bold uppercase leading-none mt-0.5">QWEN</span>
                              </div>
                            )}
                            {providerBadge.logoType !== 'musky' && providerBadge.logoType !== 'google' && providerBadge.logoType !== 'qwen' && (
                              <Bot className="w-6 h-6" />
                            )}
                          </div>

                          {/* Model Details */}
                          <div className="space-y-1 font-mono">
                            <div className="flex items-center space-x-2 flex-wrap">
                              <span className="text-sm font-black text-black uppercase tracking-tight">{m.model_name}</span>
                              <span className={`text-[9px] font-black px-2 py-0.5 border border-black uppercase ${providerBadge.bg} ${providerBadge.color}`}>
                                {providerBadge.name}
                              </span>
                              <span className={`text-[9px] font-black px-1.5 py-0.5 border border-black uppercase ${m.is_loaded ? 'bg-[#00e676] text-black' : 'bg-[#f5f4ef] text-slate-600'}`}>
                                {m.is_loaded ? '● IN RESIDENCE' : '○ EVICTED / COLD'}
                              </span>
                            </div>

                            <div className="flex items-center space-x-3 text-[11px] text-black flex-wrap">
                              <span><strong className="uppercase">ROLE:</strong> {m.worker_type}</span>
                              <span>•</span>
                              <span><strong className="uppercase">VRAM REQ:</strong> {m.vram_required_mb} MB ({vramPercent}% budget)</span>
                              <span>•</span>
                              <span><strong className="uppercase">LICENSE:</strong> {m.license}</span>
                            </div>

                            {/* Capabilities tags */}
                            {m.capabilities && m.capabilities.length > 0 && (
                              <div className="flex items-center space-x-1.5 pt-1 flex-wrap gap-y-1">
                                {m.capabilities.map((cap: string, cIdx: number) => (
                                  <span key={cIdx} className="text-[9px] font-bold bg-[#f5f4ef] text-black px-1.5 py-0.5 border border-black uppercase">
                                    {cap}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        {/* VRAM Allocation Visual Bar */}
                        <div className="w-full md:w-56 shrink-0 font-mono">
                          <div className="flex justify-between text-[10px] font-bold text-black uppercase mb-1">
                            <span>VRAM FOOTPRINT</span>
                            <span>{m.vram_required_mb} MB</span>
                          </div>
                          <div className="w-full bg-slate-200 h-3 border border-black p-0.5">
                            <div
                              className={`h-full transition-all duration-300 ${m.is_loaded ? 'bg-[#00e676]' : 'bg-black'}`}
                              style={{ width: `${vramPercent}%` }}
                            />
                          </div>
                          <div className="text-right text-[9px] text-slate-500 mt-0.5">
                            {vramPercent}% of 7.16 GB Total VRAM
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
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
