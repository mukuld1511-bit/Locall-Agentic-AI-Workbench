/**
 * Sovereign Industrial AI Workbench (MRPL SIH26117)
 * Local Desktop AI Assistant & Workbench Client Simulator
 * 
 * Simplified, Security-First Desktop Architecture:
 * - Automatic hardware detection & resource management in the backend (zero manual GPU/VRAM configuration).
 * - Clean 3-tab navigation: CHAT, FILES, ADMIN (Admin only).
 * - CHAT: Conversation area, file attachment, message input, dispatch button,
 *         compact workflow side panel (task, step, selected worker, tool, status).
 * - FILES: Uploaded & Generated industrial files with local open/save actions.
 * - SECURITY: Status indicators in header (User & Grade, Local Only 0-Egress, Default-Deny Policy, SHA-256 Audit).
 * - ADMIN: Users, Roles & Policies, Auto-managed Model Registry, Audit Log Verification.
 */

import React, { useState } from 'react';
import {
  Shield,
  Send,
  Paperclip,
  X,
  FileText,
  CheckCircle,
  AlertTriangle,
  LogOut,
  Settings,
  FolderOpen,
  MessageSquare,
  Activity,
  User,
  Database,
  Lock,
  RefreshCw,
  Check,
  FileCheck
} from 'lucide-react';

interface UserSession {
  user_id: string;
  username: string;
  full_name: string;
  role: 'GRADE_1' | 'GRADE_2' | 'GRADE_3' | 'ADMIN';
  department: string;
}

interface WorkflowState {
  task: string;
  step: string;
  worker: string;
  tool: string;
  status: 'IDLE' | 'RUNNING' | 'SUCCESS' | 'BLOCKED' | 'FAILED';
  progress: number;
}

export default function App() {
  // Session Authentication (Screen 1 & 9)
  const [session, setSession] = useState<UserSession | null>({
    user_id: 'usr_d055ea68',
    username: 'engineer_202',
    full_name: 'Priya Sharma',
    role: 'GRADE_2',
    department: 'Mechanical Reliability & Inspection',
  });

  // Top-Level Navigation: 'chat' | 'files' | 'admin'
  const [activeTab, setActiveTab] = useState<'chat' | 'files' | 'admin'>('chat');

  // Admin Sub-views: 'users' | 'policies' | 'models' | 'audit'
  const [adminSubTab, setAdminSubTab] = useState<'users' | 'policies' | 'models' | 'audit'>('users');

  // Login form state
  const [loginId, setLoginId] = useState('');
  const [loginPass, setLoginPass] = useState('');
  const [loginError, setLoginError] = useState('');

  // Chat conversation & prompt input
  const [prompt, setPrompt] = useState('');
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Chat message history
  const [messages, setMessages] = useState<
    Array<{ sender: 'user' | 'assistant' | 'system'; text: string; time: string; isSecurity?: boolean }>
  >([
    {
      sender: 'system',
      text: 'Sovereign Industrial AI Workbench initialized in Air-Gapped Mode.\nLocal hardware detected automatically. Policy Engine enforced (Default-Deny). Zero cloud egress.',
      time: '08:30',
    },
  ]);

  // Current Workflow State in compact side panel
  const [workflow, setWorkflow] = useState<WorkflowState>({
    task: 'Awaiting operator task...',
    step: 'Idle',
    worker: 'organizer (resident)',
    tool: 'None',
    status: 'IDLE',
    progress: 0,
  });

  // Audit integrity state
  const [auditVerified, setAuditVerified] = useState<boolean | null>(null);

  // Quick preset login
  const selectPreset = (u: string) => {
    setLoginId(u);
    setLoginPass('••••••••••••');
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginId.trim()) {
      setLoginError('Please enter Employee ID.');
      return;
    }

    if (loginId === 'admin') {
      setSession({
        user_id: 'usr_d934c23e',
        username: 'admin',
        full_name: 'Chief Security Administrator',
        role: 'ADMIN',
        department: 'Industrial Cyber-Security',
      });
    } else if (loginId === 'operator_101') {
      setSession({
        user_id: 'usr_d713343e',
        username: 'operator_101',
        full_name: 'Ramesh Kumar',
        role: 'GRADE_1',
        department: 'CDU/VDU Operations',
      });
    } else if (loginId === 'superintendent_303') {
      setSession({
        user_id: 'usr_1d7a7914',
        username: 'superintendent_303',
        full_name: 'Dr. Arvind Rao',
        role: 'GRADE_3',
        department: 'Technical Services',
      });
    } else {
      setSession({
        user_id: 'usr_d055ea68',
        username: 'engineer_202',
        full_name: 'Priya Sharma',
        role: 'GRADE_2',
        department: 'Mechanical Reliability & Inspection',
      });
    }
    setLoginError('');
  };

  const handleLogout = () => {
    setSession(null);
    setActiveTab('chat');
    setAttachedFile(null);
  };

  const runTask = (taskText?: string) => {
    const textToRun = taskText || prompt;
    if (!textToRun.trim() || isExecuting) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const fullText = attachedFile ? `[Attached: ${attachedFile}] ${textToRun}` : textToRun;

    setMessages((prev) => [...prev, { sender: 'user', text: fullText, time: timeStr }]);
    setPrompt('');
    setIsExecuting(true);

    // Update compact workflow side panel
    setWorkflow({
      task: textToRun,
      step: 'Step 1/5: Security & Classification',
      worker: 'organizer',
      tool: 'policy_evaluator',
      status: 'RUNNING',
      progress: 20,
    });

    // Check for simulated destructive security breach
    if (textToRun.toLowerCase().includes('delete') && textToRun.toLowerCase().includes('database')) {
      setTimeout(() => {
        setIsExecuting(false);
        setWorkflow({
          task: textToRun,
          step: 'Blocked at Policy Engine',
          worker: 'organizer',
          tool: 'policy_engine',
          status: 'BLOCKED',
          progress: 100,
        });
        setMessages((prev) => [
          ...prev,
          {
            sender: 'system',
            text: 'SECURITY VIOLATION BLOCKED\nAction: database_delete\nStatus: DENIED by Centralized Policy Engine.\nReason: Destructive schema or database operations are strictly prohibited under refinery cyber-security rules. Event logged to tamper-evident audit ledger.',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isSecurity: true,
          },
        ]);
      }, 700);
      return;
    }

    // Normal multi-step pipeline progression
    setTimeout(() => {
      setWorkflow({
        task: textToRun,
        step: 'Step 2/5: Extract Ultrasonic Thickness via Vision Model',
        worker: 'vision (auto-selected)',
        tool: 'ocr',
        status: 'RUNNING',
        progress: 40,
      });
    }, 600);

    setTimeout(() => {
      setWorkflow({
        task: textToRun,
        step: 'Step 3/5: API 510 Corrosion Rate Math in Isolated Sandbox',
        worker: 'coding (auto-selected)',
        tool: 'sandbox_exec',
        status: 'RUNNING',
        progress: 65,
      });
    }, 1300);

    setTimeout(() => {
      setWorkflow({
        task: textToRun,
        step: 'Step 4/5: Verification Engine & Official Deliverable Generation',
        worker: 'document (auto-selected)',
        tool: 'doc_generate',
        status: 'RUNNING',
        progress: 85,
      });
    }, 2000);

    setTimeout(() => {
      setIsExecuting(false);
      setWorkflow({
        task: textToRun,
        step: 'Completed: Deliverable Verified & Saved Locally',
        worker: 'organizer',
        tool: 'None (Idle)',
        status: 'SUCCESS',
        progress: 100,
      });
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `Technical Analysis & Inspection Audit Completed.\n\n- Equipment Tag: Crude Preheat Exchanger E-1102\n- Standard Applied: API 510 / MRPL SOP-HEX-042\n- Ultrasonic Thickness: 8.4 mm (T_min threshold: 6.5 mm)\n- Calculated Corrosion Rate: 0.600 mm/year\n- Remaining Safe Operational Life: 3.17 years\n- Action Item: Mandatory UT inspection re-evaluation within 24 months.\n- Verified Deliverable: Generated and saved /data/artifacts/MRPL_Approval_Note_E1102.docx locally with physical invariants satisfied.`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }, 2600);
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0d1117] text-[#e6edf3] font-sans overflow-hidden select-none">
      {/* Native Desktop Window Header Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#161b22] border-b border-[#30363d] text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-sky-500"></div>
          <span className="font-semibold text-[#c9d1d9] tracking-wide">
            MRPL AI Workbench
          </span>
          <span className="text-[10px] text-gray-400 font-mono">
            [Offline Local Desktop Client]
          </span>
        </div>

        {/* Security Status Indicators in Header */}
        <div className="flex items-center space-x-3 text-[11px] font-mono">
          <span className="flex items-center text-emerald-400 bg-emerald-950/70 px-2 py-0.5 rounded border border-emerald-800">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block mr-1.5 animate-pulse"></span>
            LOCAL ONLY (0 EGRESS)
          </span>
          <span className="text-gray-400 hidden sm:inline">POLICY: DEFAULT-DENY</span>
          <span className="text-sky-400 hidden sm:inline">AUDIT: SHA-256</span>

          {session && (
            <div className="flex items-center space-x-2 pl-2 border-l border-[#30363d]">
              <span className="text-gray-300 font-sans font-semibold">
                {session.full_name}
              </span>
              <span className="px-1.5 py-0.2 rounded text-[10px] bg-[#21262d] text-sky-400 border border-[#30363d]">
                {session.role}
              </span>
              <button
                id="btn_logout"
                onClick={handleLogout}
                className="flex items-center space-x-1 px-2 py-0.5 bg-red-950/60 hover:bg-red-900/80 text-red-300 rounded border border-red-800 text-xs transition"
                title="Logout"
              >
                <LogOut size={11} />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main View Area */}
      {!session ? (
        /* 1. LOGIN SCREEN */
        <div className="flex-1 flex items-center justify-center p-6 bg-[#0d1117]">
          <div className="w-full max-w-sm bg-[#161b22] border border-[#30363d] rounded-lg p-6 shadow-xl">
            <div className="text-center mb-5">
              <div className="inline-flex p-2.5 rounded-lg bg-sky-950/60 border border-sky-800 mb-2.5 text-sky-400">
                <Shield size={26} />
              </div>
              <h1 className="text-sm font-bold text-white tracking-wide">
                MANGALORE REFINERY & PETROCHEMICALS
              </h1>
              <p className="text-xs text-gray-400 mt-0.5">
                Sovereign Industrial AI Workbench (SIH26117)
              </p>
              <div className="mt-2 text-[10px] text-emerald-400 bg-emerald-950/50 py-0.5 px-2 rounded border border-emerald-800 font-mono inline-block">
                Air-Gapped Workstation | Auto Hardware Setup
              </div>
            </div>

            <form onSubmit={handleLogin} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">
                  Employee ID / Username
                </label>
                <input
                  id="input_login_user"
                  type="text"
                  value={loginId}
                  onChange={(e) => setLoginId(e.target.value)}
                  placeholder="e.g. engineer_202 or admin"
                  className="w-full px-3 py-1.5 bg-[#0d1117] border border-[#30363d] rounded text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-1">
                  Password
                </label>
                <input
                  id="input_login_pass"
                  type="password"
                  value={loginPass}
                  onChange={(e) => setLoginPass(e.target.value)}
                  placeholder="Industrial passphrase"
                  className="w-full px-3 py-1.5 bg-[#0d1117] border border-[#30363d] rounded text-xs text-white focus:outline-none focus:border-sky-500 font-mono"
                />
              </div>

              {loginError && (
                <div className="text-xs text-red-400 bg-red-950/40 p-2 rounded border border-red-800">
                  {loginError}
                </div>
              )}

              <button
                id="btn_submit_login"
                type="submit"
                className="w-full py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded transition shadow-sm mt-1"
              >
                Authenticate Session
              </button>
            </form>

            <div className="mt-5 pt-3 border-t border-[#30363d]">
              <div className="text-[10px] text-gray-400 mb-1.5">Quick Role Select:</div>
              <div className="grid grid-cols-2 gap-1.5 text-xs">
                <button
                  id="btn_preset_op"
                  onClick={() => selectPreset('operator_101')}
                  className="px-2 py-1 bg-[#21262d] hover:bg-[#30363d] rounded text-left border border-[#30363d]"
                >
                  <div className="font-semibold text-gray-200 text-[11px]">Operator 101</div>
                  <div className="text-[9px] text-gray-400">Grade 1 (Field Ops)</div>
                </button>
                <button
                  id="btn_preset_eng"
                  onClick={() => selectPreset('engineer_202')}
                  className="px-2 py-1 bg-[#21262d] hover:bg-[#30363d] rounded text-left border border-[#30363d]"
                >
                  <div className="font-semibold text-sky-400 text-[11px]">Engineer 202</div>
                  <div className="text-[9px] text-gray-400">Grade 2 (Reliability)</div>
                </button>
                <button
                  id="btn_preset_supt"
                  onClick={() => selectPreset('superintendent_303')}
                  className="px-2 py-1 bg-[#21262d] hover:bg-[#30363d] rounded text-left border border-[#30363d]"
                >
                  <div className="font-semibold text-amber-400 text-[11px]">Superintendent</div>
                  <div className="text-[9px] text-gray-400">Grade 3 (Plant Supt)</div>
                </button>
                <button
                  id="btn_preset_admin"
                  onClick={() => selectPreset('admin')}
                  className="px-2 py-1 bg-[#21262d] hover:bg-[#30363d] rounded text-left border border-[#30363d]"
                >
                  <div className="font-semibold text-purple-400 text-[11px]">Security Admin</div>
                  <div className="text-[9px] text-gray-400">Authorized Lead</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* 2. MAIN WORKBENCH (CHAT, FILES, ADMIN) */
        <div className="flex-1 flex flex-col overflow-hidden bg-[#0d1117]">
          {/* Top Navigation Bar: CHAT, FILES, ADMIN (Admin only) */}
          <div className="flex items-center px-4 bg-[#161b22] border-b border-[#30363d] space-x-1 text-xs">
            <button
              id="tab_chat"
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-1.5 px-4 py-2 font-semibold border-b-2 transition ${
                activeTab === 'chat'
                  ? 'border-sky-500 text-sky-400 bg-[#0d1117]'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <MessageSquare size={13} />
              <span>CHAT</span>
            </button>

            <button
              id="tab_files"
              onClick={() => setActiveTab('files')}
              className={`flex items-center space-x-1.5 px-4 py-2 font-semibold border-b-2 transition ${
                activeTab === 'files'
                  ? 'border-sky-500 text-sky-400 bg-[#0d1117]'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <FolderOpen size={13} />
              <span>FILES</span>
            </button>

            {session.role === 'ADMIN' && (
              <button
                id="tab_admin"
                onClick={() => setActiveTab('admin')}
                className={`flex items-center space-x-1.5 px-4 py-2 font-semibold border-b-2 transition ${
                  activeTab === 'admin'
                    ? 'border-purple-500 text-purple-400 bg-[#0d1117]'
                    : 'border-transparent text-gray-400 hover:text-gray-200'
                }`}
              >
                <Settings size={13} />
                <span>ADMIN</span>
              </button>
            )}
          </div>

          {/* Tab Body */}
          <div className="flex-1 overflow-hidden p-3">
            {/* ------------------------------------------------------------- */}
            {/* CHAT TAB WITH COMPACT WORKFLOW SIDE PANEL                     */}
            {/* ------------------------------------------------------------- */}
            {activeTab === 'chat' && (
              <div className="h-full flex space-x-3">
                {/* Left Area: Conversation, input, attached file, demos */}
                <div className="flex-1 flex flex-col bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
                  {/* Messages Area */}
                  <div className="flex-1 overflow-y-auto p-3.5 space-y-3 text-xs font-sans">
                    {messages.map((m, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border leading-relaxed ${
                          m.isSecurity
                            ? 'bg-red-950/40 border-red-800 text-red-200'
                            : m.sender === 'user'
                            ? 'bg-[#21262d] border-[#30363d] text-sky-200 ml-8'
                            : m.sender === 'assistant'
                            ? 'bg-[#0f172a] border-sky-900 text-slate-100 mr-8'
                            : 'bg-[#111827] border-gray-800 text-gray-300 text-[11px]'
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] text-gray-400 mb-1 pb-1 border-b border-gray-700/40">
                          <span className="font-semibold uppercase tracking-wider">
                            {m.sender === 'user' ? session.username : m.sender === 'assistant' ? 'Assistant' : 'System'}
                          </span>
                          <span className="font-mono">{m.time}</span>
                        </div>
                        <div className="whitespace-pre-wrap">{m.text}</div>
                      </div>
                    ))}

                    {isExecuting && (
                      <div className="p-2.5 bg-sky-950/30 border border-sky-800 rounded text-xs text-sky-300 flex items-center space-x-2 animate-pulse">
                        <RefreshCw className="animate-spin" size={13} />
                        <span>Workflow executing: {workflow.step}...</span>
                      </div>
                    )}
                  </div>

                  {/* Attached File Chip (if file is selected) */}
                  {attachedFile && (
                    <div className="px-3 py-1 bg-[#1a2332] border-t border-[#30363d] flex items-center justify-between text-xs text-sky-300">
                      <div className="flex items-center space-x-1.5">
                        <Paperclip size={12} />
                        <span className="font-semibold">{attachedFile}</span>
                        <span className="text-[10px] text-gray-400">(ready to dispatch with task)</span>
                      </div>
                      <button
                        id="btn_remove_attachment"
                        onClick={() => setAttachedFile(null)}
                        className="text-gray-400 hover:text-red-400 transition"
                        title="Remove attachment"
                      >
                        <X size={13} />
                      </button>
                    </div>
                  )}

                  {/* Demo Task Presets Bar */}
                  <div className="px-3 py-1.5 bg-[#21262d] border-t border-[#30363d] flex items-center space-x-2 overflow-x-auto text-[11px]">
                    <span className="text-gray-400 whitespace-nowrap">Demos:</span>
                    <button
                      id="btn_demo_audit"
                      onClick={() => {
                        setAttachedFile('scanned_inspection_E1102.pdf');
                        runTask('Audit ultrasonic thickness inspection report for E-1102 and generate official approval note.');
                      }}
                      className="px-2 py-0.5 bg-[#161b22] hover:bg-sky-950 hover:text-sky-300 text-gray-300 rounded border border-[#30363d] whitespace-nowrap text-[10px]"
                    >
                      Inspection Audit (API 510)
                    </button>
                    <button
                      id="btn_demo_efficiency"
                      onClick={() => {
                        setAttachedFile('unit3_heat_duty_log.csv');
                        runTask('Analyze sensor log spreadsheet and compute heat duty and thermal efficiency for Unit 3.');
                      }}
                      className="px-2 py-0.5 bg-[#161b22] hover:bg-sky-950 hover:text-sky-300 text-gray-300 rounded border border-[#30363d] whitespace-nowrap text-[10px]"
                    >
                      Thermal Efficiency
                    </button>
                    <button
                      id="btn_demo_block"
                      onClick={() => runTask('Delete production database and wipe audit records.')}
                      className="px-2 py-0.5 bg-red-950/50 hover:bg-red-900/60 text-red-300 rounded border border-red-800 whitespace-nowrap text-[10px]"
                    >
                      Security Block Test
                    </button>
                  </div>

                  {/* Message Input & Send */}
                  <div className="p-2.5 bg-[#161b22] border-t border-[#30363d] flex items-center space-x-2">
                    <button
                      id="btn_attach_file"
                      onClick={() => {
                        setAttachedFile('scanned_inspection_E1102.pdf');
                      }}
                      title="Attach local file"
                      className="p-2 bg-[#21262d] hover:bg-[#30363d] text-gray-300 rounded border border-[#30363d] transition"
                    >
                      <Paperclip size={14} />
                    </button>

                    <input
                      id="input_chat_prompt"
                      type="text"
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && runTask()}
                      placeholder="Type a technical instruction or question (e.g., 'Audit inspection report for E-1102')..."
                      className="flex-1 px-3 py-1.5 bg-[#0d1117] border border-[#30363d] rounded text-xs text-white focus:outline-none focus:border-sky-500 font-sans"
                    />

                    <button
                      id="btn_send_task"
                      onClick={() => runTask()}
                      disabled={isExecuting || !prompt.trim()}
                      className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 disabled:bg-gray-800 disabled:text-gray-500 text-white font-semibold rounded text-xs transition flex items-center space-x-1"
                    >
                      <Send size={12} />
                      <span>Send</span>
                    </button>
                  </div>
                </div>

                {/* Right Area: Compact Workflow & Activity Side Panel */}
                <div className="w-80 flex flex-col bg-[#161b22] border border-[#30363d] rounded-lg p-3.5 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-[#30363d]">
                    <span className="text-xs font-bold text-gray-200 flex items-center space-x-1.5">
                      <Activity size={13} className="text-sky-400" />
                      <span>WORKFLOW & ACTIVITY</span>
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                        workflow.status === 'SUCCESS'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          : workflow.status === 'RUNNING'
                          ? 'bg-sky-950 text-sky-400 border border-sky-800'
                          : workflow.status === 'BLOCKED'
                          ? 'bg-red-950 text-red-400 border border-red-800'
                          : 'bg-gray-800 text-gray-400 border border-gray-700'
                      }`}
                    >
                      {workflow.status}
                    </span>
                  </div>

                  {/* Architecture Pipeline Visualizer */}
                  <div className="p-2 bg-[#0d1117] border border-[#30363d] rounded text-[10px] space-y-1">
                    <div className="text-gray-400 font-semibold uppercase tracking-wider text-[9px]">
                      Architecture Flow
                    </div>
                    <div className="font-mono text-gray-300 leading-tight">
                      Auth &rarr; RBAC &rarr; Policy &rarr; Security &rarr; Organizer &rarr; Model &rarr; Tool &rarr; Verify &rarr; Audit
                    </div>
                  </div>

                  {/* Current Task */}
                  <div className="space-y-1 text-xs">
                    <span className="text-[11px] text-gray-400 font-semibold">Current Task:</span>
                    <div className="p-2 bg-[#0d1117] border border-[#30363d] rounded text-[11px] text-gray-200 line-clamp-3">
                      {workflow.task}
                    </div>
                  </div>

                  {/* Current Step */}
                  <div className="space-y-1 text-xs">
                    <span className="text-[11px] text-gray-400 font-semibold">Current Step:</span>
                    <div className="p-2 bg-[#0d1117] border border-[#30363d] rounded text-[11px] text-sky-400 font-medium">
                      {workflow.step}
                    </div>
                  </div>

                  {/* Selected Worker & Executing Tool */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-[#0d1117] border border-[#30363d] rounded">
                      <div className="text-[10px] text-gray-400">Selected Worker:</div>
                      <div className="font-semibold text-purple-400 text-[11px] truncate">
                        {workflow.worker}
                      </div>
                    </div>
                    <div className="p-2 bg-[#0d1117] border border-[#30363d] rounded">
                      <div className="text-[10px] text-gray-400">Tool Executing:</div>
                      <div className="font-semibold text-amber-400 text-[11px] truncate">
                        {workflow.tool}
                      </div>
                    </div>
                  </div>

                  {/* Workflow Progress */}
                  <div className="space-y-1 pt-1">
                    <div className="flex justify-between text-[10px] text-gray-400">
                      <span>Execution Progress</span>
                      <span>{workflow.progress}%</span>
                    </div>
                    <div className="w-full bg-[#0d1117] h-1.5 rounded-full overflow-hidden border border-[#30363d]">
                      <div
                        className="bg-sky-500 h-full transition-all duration-300"
                        style={{ width: `${workflow.progress}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Security Clearance Note */}
                  <div className="mt-auto p-2 bg-[#0d1117] border border-[#30363d] rounded text-[10px] text-gray-400 flex items-center space-x-1.5">
                    <Shield size={12} className="text-emerald-400 shrink-0" />
                    <span>Active Clearance: <b className="text-gray-200">{session.role}</b> ({session.department})</span>
                  </div>
                </div>
              </div>
            )}

            {/* ------------------------------------------------------------- */}
            {/* FILES TAB (Uploaded Files & Generated Technical Deliverables) */}
            {/* ------------------------------------------------------------- */}
            {activeTab === 'files' && (
              <div className="h-full flex flex-col space-y-3">
                {/* Uploaded & Ingested Files */}
                <div className="flex-1 flex flex-col bg-[#161b22] border border-[#30363d] rounded-lg p-3.5 overflow-hidden">
                  <div className="flex items-center justify-between mb-2.5">
                    <div>
                      <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                        Uploaded & Ingested Files
                      </h2>
                      <p className="text-[11px] text-gray-400">
                        Local engineering documents indexed with SHA-256 integrity checks.
                      </p>
                    </div>
                    <button
                      id="btn_open_file_dialog"
                      onClick={() => alert('Local file open dialog: scanned_inspection_E1102.pdf indexed into local storage.')}
                      className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded"
                    >
                      Open Local File...
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto border border-[#30363d] rounded">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#21262d] text-gray-300 font-mono text-[11px] border-b border-[#30363d]">
                        <tr>
                          <th className="p-2">Filename</th>
                          <th className="p-2">Type</th>
                          <th className="p-2">Size</th>
                          <th className="p-2">Sensitivity</th>
                          <th className="p-2">Integrity</th>
                          <th className="p-2">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#30363d] font-mono text-[11px]">
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-sky-400 font-semibold">scanned_inspection_E1102.pdf</td>
                          <td className="p-2 text-gray-400">PDF Scan</td>
                          <td className="p-2">342 KB</td>
                          <td className="p-2">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-sky-950 text-sky-400 border border-sky-800">
                              ROLE_RESTRICTED
                            </span>
                          </td>
                          <td className="p-2 text-emerald-400">SHA-256 Valid</td>
                          <td className="p-2">
                            <button
                              onClick={() => {
                                setAttachedFile('scanned_inspection_E1102.pdf');
                                setActiveTab('chat');
                              }}
                              className="text-sky-400 hover:underline"
                            >
                              Attach to Chat
                            </button>
                          </td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-sky-400 font-semibold">unit3_heat_duty_log.csv</td>
                          <td className="p-2 text-gray-400">Sensor CSV</td>
                          <td className="p-2">188 KB</td>
                          <td className="p-2">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-gray-800 text-gray-300 border border-gray-700">
                              PUBLIC_INTERNAL
                            </span>
                          </td>
                          <td className="p-2 text-emerald-400">SHA-256 Valid</td>
                          <td className="p-2">
                            <button
                              onClick={() => {
                                setAttachedFile('unit3_heat_duty_log.csv');
                                setActiveTab('chat');
                              }}
                              className="text-sky-400 hover:underline"
                            >
                              Attach to Chat
                            </button>
                          </td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-sky-400 font-semibold">pid_cdu_e1102.png</td>
                          <td className="p-2 text-gray-400">P&ID Diagram</td>
                          <td className="p-2">1.2 MB</td>
                          <td className="p-2">
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-950 text-amber-400 border border-amber-800">
                              CONFIDENTIAL
                            </span>
                          </td>
                          <td className="p-2 text-emerald-400">SHA-256 Valid</td>
                          <td className="p-2">
                            {session.role === 'GRADE_1' ? (
                              <span className="text-red-400">Restricted (Grade 1)</span>
                            ) : (
                              <button
                                onClick={() => {
                                  setAttachedFile('pid_cdu_e1102.png');
                                  setActiveTab('chat');
                                }}
                                className="text-sky-400 hover:underline"
                              >
                                Attach to Chat
                              </button>
                            )}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Generated Deliverables */}
                <div className="flex-1 flex flex-col bg-[#161b22] border border-[#30363d] rounded-lg p-3.5 overflow-hidden">
                  <div className="mb-2.5">
                    <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                      Generated Technical Deliverables
                    </h2>
                    <p className="text-[11px] text-gray-400">
                      Verified output files generated by specialist models and verified by the Standalone Verification Engine.
                    </p>
                  </div>

                  <div className="flex-1 overflow-y-auto border border-[#30363d] rounded">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#21262d] text-gray-300 font-mono text-[11px] border-b border-[#30363d]">
                        <tr>
                          <th className="p-2">Deliverable Title</th>
                          <th className="p-2">Format</th>
                          <th className="p-2">Size</th>
                          <th className="p-2">Verification State</th>
                          <th className="p-2">Local Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#30363d] font-mono text-[11px]">
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-white font-semibold">MRPL Approval Note E1102</td>
                          <td className="p-2 text-sky-400">DOCX</td>
                          <td className="p-2">14.8 KB</td>
                          <td className="p-2 text-emerald-400 font-bold">PASS (API 510 Invariants Verified)</td>
                          <td className="p-2">
                            <span className="text-gray-300">Saved Locally (/artifacts)</span>
                          </td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-white font-semibold">Unit 3 Heat Duty Balance</td>
                          <td className="p-2 text-emerald-400">XLSX</td>
                          <td className="p-2">22.4 KB</td>
                          <td className="p-2 text-emerald-400 font-bold">PASS (Thermodynamic Check OK)</td>
                          <td className="p-2">
                            <span className="text-gray-300">Saved Locally (/artifacts)</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* ------------------------------------------------------------- */}
            {/* ADMIN TAB (Only Visible to ADMIN)                             */}
            {/* ------------------------------------------------------------- */}
            {activeTab === 'admin' && session.role === 'ADMIN' && (
              <div className="h-full flex flex-col bg-[#161b22] border border-[#30363d] rounded-lg p-3.5 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-[#30363d]">
                  <div>
                    <h2 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
                      Industrial Administration Console
                    </h2>
                    <p className="text-[11px] text-gray-400">
                      Restricted to authorized administrators. Manage operators, security policies, auto-managed models, and audit logs.
                    </p>
                  </div>
                  {/* Admin Sub-navigation: Users, Roles & Policies, Models, Audit */}
                  <div className="flex space-x-1 bg-[#0d1117] p-1 rounded border border-[#30363d] text-xs">
                    <button
                      id="admin_subtab_users"
                      onClick={() => setAdminSubTab('users')}
                      className={`px-3 py-1 rounded transition ${
                        adminSubTab === 'users' ? 'bg-[#21262d] text-white font-semibold' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Users
                    </button>
                    <button
                      id="admin_subtab_policies"
                      onClick={() => setAdminSubTab('policies')}
                      className={`px-3 py-1 rounded transition ${
                        adminSubTab === 'policies' ? 'bg-[#21262d] text-white font-semibold' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Roles & Policies
                    </button>
                    <button
                      id="admin_subtab_models"
                      onClick={() => setAdminSubTab('models')}
                      className={`px-3 py-1 rounded transition ${
                        adminSubTab === 'models' ? 'bg-[#21262d] text-white font-semibold' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Models
                    </button>
                    <button
                      id="admin_subtab_audit"
                      onClick={() => setAdminSubTab('audit')}
                      className={`px-3 py-1 rounded transition ${
                        adminSubTab === 'audit' ? 'bg-[#21262d] text-white font-semibold' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Audit
                    </button>
                  </div>
                </div>

                {/* Subtab 1: Users */}
                {adminSubTab === 'users' && (
                  <div className="flex-1 overflow-y-auto border border-[#30363d] rounded">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#21262d] text-gray-300 font-mono text-[11px] border-b border-[#30363d]">
                        <tr>
                          <th className="p-2">Username</th>
                          <th className="p-2">Full Name</th>
                          <th className="p-2">Department</th>
                          <th className="p-2">Clearance Role</th>
                          <th className="p-2">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#30363d] font-mono text-[11px]">
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 font-semibold text-white">operator_101</td>
                          <td className="p-2">Ramesh Kumar</td>
                          <td className="p-2 text-gray-400">CDU/VDU Operations</td>
                          <td className="p-2 text-gray-300">GRADE_1</td>
                          <td className="p-2 text-emerald-400 font-bold">ACTIVE</td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 font-semibold text-white">engineer_202</td>
                          <td className="p-2">Priya Sharma</td>
                          <td className="p-2 text-gray-400">Mechanical Reliability</td>
                          <td className="p-2 text-sky-400 font-bold">GRADE_2</td>
                          <td className="p-2 text-emerald-400 font-bold">ACTIVE</td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 font-semibold text-white">superintendent_303</td>
                          <td className="p-2">Dr. Arvind Rao</td>
                          <td className="p-2 text-gray-400">Technical Services</td>
                          <td className="p-2 text-amber-400 font-bold">GRADE_3</td>
                          <td className="p-2 text-emerald-400 font-bold">ACTIVE</td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 font-semibold text-white">admin</td>
                          <td className="p-2">Chief Security Lead</td>
                          <td className="p-2 text-gray-400">Industrial Cyber-Security</td>
                          <td className="p-2 text-purple-400 font-bold">ADMIN</td>
                          <td className="p-2 text-emerald-400 font-bold">ACTIVE</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Subtab 2: Roles & Policies */}
                {adminSubTab === 'policies' && (
                  <div className="flex-1 overflow-y-auto border border-[#30363d] rounded">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-[#21262d] text-gray-300 font-mono text-[11px] border-b border-[#30363d]">
                        <tr>
                          <th className="p-2">Policy ID</th>
                          <th className="p-2">Description</th>
                          <th className="p-2">Effect</th>
                          <th className="p-2">Min Clearance</th>
                          <th className="p-2">Engine State</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#30363d] font-mono text-[11px]">
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-sky-400 font-semibold">POL_DB_DELETE_DENY</td>
                          <td className="p-2">Strictly forbid destructive database drops</td>
                          <td className="p-2 text-red-400 font-bold">DENY</td>
                          <td className="p-2">ALL_ROLES</td>
                          <td className="p-2 text-emerald-400 font-bold">ENFORCED</td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-sky-400 font-semibold">POL_SANDBOX_EXEC</td>
                          <td className="p-2">Execute mathematical calculations in isolated sandbox</td>
                          <td className="p-2 text-emerald-400 font-bold">ALLOW</td>
                          <td className="p-2">GRADE_2</td>
                          <td className="p-2 text-emerald-400 font-bold">ENFORCED</td>
                        </tr>
                        <tr className="hover:bg-[#1f2937]">
                          <td className="p-2 text-sky-400 font-semibold">POL_EGRESS_BLOCK</td>
                          <td className="p-2">Block any external network socket request</td>
                          <td className="p-2 text-red-400 font-bold">DENY</td>
                          <td className="p-2">ALL_ROLES</td>
                          <td className="p-2 text-emerald-400 font-bold">ENFORCED</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Subtab 3: Models (Auto-Managed Model Registry - No hardware inputs!) */}
                {adminSubTab === 'models' && (
                  <div className="flex-1 flex flex-col space-y-2">
                    <div className="p-2.5 bg-[#0d1117] border border-[#30363d] rounded text-xs text-gray-300">
                      <div className="font-semibold text-sky-400 mb-0.5">Automated Model & Resource Management</div>
                      <div className="text-[11px] text-gray-400">
                        Local hardware detection, worker loading/unloading, model swapping, and memory safety are handled automatically by the backend. No manual hardware parameters are required.
                      </div>
                    </div>

                    <div className="flex-1 overflow-y-auto border border-[#30363d] rounded">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-[#21262d] text-gray-300 font-mono text-[11px] border-b border-[#30363d]">
                          <tr>
                            <th className="p-2">Worker Role</th>
                            <th className="p-2">Model ID</th>
                            <th className="p-2">Quantization</th>
                            <th className="p-2">Runtime State</th>
                            <th className="p-2">Management Policy</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#30363d] font-mono text-[11px]">
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 font-semibold text-white">Organizer</td>
                            <td className="p-2 text-gray-300">Industrial Controller 500M</td>
                            <td className="p-2 text-gray-400">Q8_0</td>
                            <td className="p-2 text-emerald-400 font-bold">RESIDENT (ALWAYS)</td>
                            <td className="p-2 text-gray-400">Auto-pinned</td>
                          </tr>
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 font-semibold text-white">Vision Worker</td>
                            <td className="p-2 text-gray-300">Qwen2.5-VL-3B-Instruct</td>
                            <td className="p-2 text-gray-400">Q4_K_M</td>
                            <td className="p-2 text-sky-400">STANDBY (ON DISK)</td>
                            <td className="p-2 text-gray-400">Auto-swapped on OCR</td>
                          </tr>
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 font-semibold text-white">Coding Worker</td>
                            <td className="p-2 text-gray-300">StarCoder2-3B</td>
                            <td className="p-2 text-gray-400">Q4_K_M</td>
                            <td className="p-2 text-sky-400">STANDBY (ON DISK)</td>
                            <td className="p-2 text-gray-400">Auto-swapped on Math</td>
                          </tr>
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 font-semibold text-white">Document Worker</td>
                            <td className="p-2 text-gray-300">Qwen2.5-3B-Instruct</td>
                            <td className="p-2 text-gray-400">Q4_K_M</td>
                            <td className="p-2 text-sky-400">STANDBY (ON DISK)</td>
                            <td className="p-2 text-gray-400">Auto-swapped on RAG</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Subtab 4: Audit Logs */}
                {adminSubTab === 'audit' && (
                  <div className="flex-1 flex flex-col space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-400 font-mono">
                        Forward Cryptographic Hash Chain: SHA-256
                      </span>
                      <button
                        id="btn_verify_audit_chain"
                        onClick={() => setAuditVerified(true)}
                        className="px-2.5 py-1 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold rounded"
                      >
                        Verify Hash-Chain Integrity
                      </button>
                    </div>

                    {auditVerified && (
                      <div className="p-2 bg-emerald-950/60 border border-emerald-800 rounded text-xs text-emerald-300 font-mono">
                        Audit ledger verified. 142 records checked with SHA-256 forward chaining. Zero tampering detected.
                      </div>
                    )}

                    <div className="flex-1 overflow-y-auto border border-[#30363d] rounded">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-[#21262d] text-gray-300 font-mono text-[11px] border-b border-[#30363d]">
                          <tr>
                            <th className="p-2">Timestamp</th>
                            <th className="p-2">Event</th>
                            <th className="p-2">User</th>
                            <th className="p-2">Role</th>
                            <th className="p-2">Resource</th>
                            <th className="p-2">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#30363d] font-mono text-[11px]">
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 text-gray-400">08:30:12 UTC</td>
                            <td className="p-2 text-sky-400">AUTH_LOGIN</td>
                            <td className="p-2">engineer_202</td>
                            <td className="p-2">GRADE_2</td>
                            <td className="p-2">session:local</td>
                            <td className="p-2 text-emerald-400">SUCCESS</td>
                          </tr>
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 text-gray-400">08:30:45 UTC</td>
                            <td className="p-2 text-sky-400">MODEL_SELECTED</td>
                            <td className="p-2">engineer_202</td>
                            <td className="p-2">GRADE_2</td>
                            <td className="p-2">model:Qwen2.5-VL</td>
                            <td className="p-2 text-emerald-400">SUCCESS</td>
                          </tr>
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 text-gray-400">08:31:02 UTC</td>
                            <td className="p-2 text-sky-400">TOOL_EXECUTION</td>
                            <td className="p-2">engineer_202</td>
                            <td className="p-2">GRADE_2</td>
                            <td className="p-2">tool:sandbox_exec</td>
                            <td className="p-2 text-emerald-400">SUCCESS</td>
                          </tr>
                          <tr className="hover:bg-[#1f2937]">
                            <td className="p-2 text-gray-400">08:31:20 UTC</td>
                            <td className="p-2 text-sky-400">VERIFICATION_PASS</td>
                            <td className="p-2">engineer_202</td>
                            <td className="p-2">GRADE_2</td>
                            <td className="p-2">doc:MRPL_Approval_Note</td>
                            <td className="p-2 text-emerald-400">SUCCESS</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
