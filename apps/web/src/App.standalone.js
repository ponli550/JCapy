import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Shield, Radio, Activity, Terminal, Zap, Power, AlertTriangle, RefreshCcw, Check, X, ShieldAlert, Cpu, Link, Unlink, Database, Send, Play, User, Settings, Cpu as CpuIcon, HardDrive, Clock, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { WebSocketBridge } from 'bridge-service';

function App() {
   const [isHalted, setIsHalted] = useState(false);
   const [events, setEvents] = useState([]);
   const [activeIntervention, setActiveIntervention] = useState(null);
   const [linkStatus, setLinkStatus] = useState('OFFLINE');
   const [commandInput, setCommandInput] = useState('');
   const [terminalLines, setTerminalLines] = useState([]);
   const [persona, setPersona] = useState('developer');
   const [mode, setMode] = useState('NORMAL');
   const [commandHistory, setCommandHistory] = useState([]);
   const [historyIndex, setHistoryIndex] = useState(-1);
   const [systemStats, setSystemStats] = useState({ cpu: 0, memory: 0, tasks: 0, uptime: '0s' });
   const bridgeRef = useRef(null);
   const terminalRef = useRef(null);
   const inputRef = useRef(null);

   // Auto-scroll terminal
   useEffect(() => {
      if (terminalRef.current) {
         terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
      }
   }, [terminalLines]);

   useEffect(() => {
      if (!bridgeRef.current) {
         bridgeRef.current = new WebSocketBridge((event) => {
            if (event.type === 'STATUS' && event.message === 'CONNECTION_ACTIVE') {
               setLinkStatus('SYNCHRONIZED');
               return;
            }

            setEvents(prev => {
               const next = [...prev, event];
               return next.length > 100 ? next.slice(-100) : next;
            });

            if (event.type === 'INTERVENTION') {
               setActiveIntervention(event);
            }
         });
         bridgeRef.current.start();
      }
      return () => bridgeRef.current?.stop();
   }, []);

   // Handle events from TUI
   useEffect(() => {
      if (!bridgeRef.current) return;
      
      const originalHandler = bridgeRef.current.onEvent;
      bridgeRef.current.onEvent = (event) => {
         if (originalHandler) originalHandler(event);
         
         // Terminal output
         if (event.type === 'TERMINAL_OUTPUT' || event.topic === 'TERMINAL_OUTPUT') {
            const line = event.line || event.data?.line || '';
            if (line) {
               setTerminalLines(prev => {
                  const next = [...prev, line];
                  return next.length > 500 ? next.slice(-500) : next;
               });
            }
         }
         
         // Mode changes
         if (event.type === 'MODE_CHANGED' || event.topic === 'MODE_CHANGED') {
            setMode(event.mode || event.data?.mode || 'NORMAL');
            if (event.persona || event.data?.persona) {
               setPersona(event.persona || event.data?.persona);
            }
         }
         
         // Commands
         if (event.type === 'COMMAND_EXECUTED' || event.topic === 'COMMAND_EXECUTED') {
            const cmd = event.command || event.data?.command || '';
            if (cmd) {
               setTerminalLines(prev => [...prev, `❯ ${cmd}`]);
            }
         }
         
         // Heartbeat with stats
         if (event.type === 'HEARTBEAT' || event.topic === 'HEARTBEAT') {
            setLinkStatus('SYNCHRONIZED');
            const status = event.status || event.data?.status || {};
            if (status.tasks_completed !== undefined) {
               setSystemStats(prev => ({
                  ...prev,
                  tasks: status.tasks_completed,
                  uptime: status.uptime_human || prev.uptime
               }));
            }
         }
      };
   }, []);

   const executeCommand = useCallback(() => {
      if (!commandInput.trim()) return;
      
      setTerminalLines(prev => [...prev, `❯ ${commandInput}`]);
      setCommandHistory(prev => [...prev, commandInput]);
      setHistoryIndex(-1);
      
      if (bridgeRef.current) {
         bridgeRef.current.send({
            type: 'EXECUTE_COMMAND',
            command: commandInput
         });
      }
      
      setCommandInput('');
   }, [commandInput]);

   const handleKeyDown = (e) => {
      if (e.key === 'Enter') {
         executeCommand();
      } else if (e.key === 'ArrowUp') {
         e.preventDefault();
         if (commandHistory.length > 0) {
            const newIndex = historyIndex < commandHistory.length - 1 ? historyIndex + 1 : historyIndex;
            setHistoryIndex(newIndex);
            setCommandInput(commandHistory[commandHistory.length - 1 - newIndex] || '');
         }
      } else if (e.key === 'ArrowDown') {
         e.preventDefault();
         if (historyIndex > 0) {
            const newIndex = historyIndex - 1;
            setHistoryIndex(newIndex);
            setCommandInput(commandHistory[commandHistory.length - 1 - newIndex] || '');
         } else {
            setHistoryIndex(-1);
            setCommandInput('');
         }
      }
   };

   const toggleKillSwitch = () => setIsHalted(!isHalted);

   const handleIntervention = (approved) => {
      if (!activeIntervention) return;
      bridgeRef.current?.send({
         type: 'APPROVE_ACTION',
         id: activeIntervention.id,
         approved: approved
      });
      setActiveIntervention(null);
   };

   const switchPersona = (newPersona) => {
      setPersona(newPersona);
      bridgeRef.current?.send({
         type: 'SWITCH_PERSONA',
         persona: newPersona
      });
   };

   const personas = ['developer', 'devops', 'designer', 'architect'];

   // Simulate system stats for demo
   useEffect(() => {
      const interval = setInterval(() => {
         setSystemStats(prev => ({
            ...prev,
            cpu: Math.floor(Math.random() * 40) + 10,
            memory: Math.floor(Math.random() * 30) + 40,
         }));
      }, 3000);
      return () => clearInterval(interval);
   }, []);

   return React.createElement('div', { className: 'min-h-screen w-full flex flex-col bg-slate-950 font-mono' }, [
      
      // Header
      React.createElement('header', { key: 'header', className: 'flex-shrink-0 border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm' }, [
         React.createElement('div', { className: 'flex items-center justify-between px-6 py-3' }, [
            React.createElement('div', { className: 'flex items-center space-x-4' }, [
               React.createElement(Shield, { className: 'text-cyan-400 w-6 h-6' }),
               React.createElement('div', null, [
                  React.createElement('h1', { className: 'text-lg font-bold text-white' }, 'JCapy Control Plane'),
                  React.createElement('p', { className: 'text-xs text-slate-500' }, 'v4.1.8 • STATION-01')
               ])
            ]),
            React.createElement('div', { className: 'flex items-center space-x-3' }, [
               // Connection Status
               React.createElement('div', { className: `flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs ${linkStatus === 'SYNCHRONIZED' ? 'bg-cyan-500/10 text-cyan-400' : 'bg-red-500/10 text-red-400'}` }, [
                  React.createElement(linkStatus === 'SYNCHRONIZED' ? Link : Unlink, { size: 14 }),
                  React.createElement('span', null, linkStatus)
               ]),
               // Kill Switch
               React.createElement('button', {
                  onClick: toggleKillSwitch,
                  className: 'flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors text-xs'
               }, [
                  React.createElement(Power, { size: 14 }),
                  React.createElement('span', null, 'HALT')
               ])
            ])
         ])
      ]),

      // Main Content
      React.createElement('main', { key: 'main', className: 'flex-1 flex overflow-hidden' }, [
         
         // Left Sidebar - Stats & Controls
         React.createElement('aside', { key: 'sidebar', className: 'w-64 flex-shrink-0 border-r border-slate-800 bg-slate-900/30 p-4 flex flex-col space-y-4 overflow-y-auto' }, [
            
            // System Stats
            React.createElement('div', { className: 'bg-slate-800/50 rounded-lg p-3' }, [
               React.createElement('h3', { className: 'text-xs font-bold text-slate-400 mb-3 flex items-center' }, [
                  React.createElement(CpuIcon, { size: 12, className: 'mr-2' }),
                  'SYSTEM STATUS'
               ]),
               React.createElement('div', { className: 'space-y-2' }, [
                  React.createElement('div', { className: 'flex justify-between text-xs' }, [
                     React.createElement('span', { className: 'text-slate-500' }, 'CPU'),
                     React.createElement('span', { className: 'text-cyan-400' }, `${systemStats.cpu}%`)
                  ]),
                  React.createElement('div', { className: 'h-1 bg-slate-700 rounded-full overflow-hidden' }, [
                     React.createElement('div', { className: 'h-full bg-cyan-500 transition-all', style: { width: `${systemStats.cpu}%` } })
                  ]),
                  React.createElement('div', { className: 'flex justify-between text-xs mt-2' }, [
                     React.createElement('span', { className: 'text-slate-500' }, 'Memory'),
                     React.createElement('span', { className: 'text-green-400' }, `${systemStats.memory}%`)
                  ]),
                  React.createElement('div', { className: 'h-1 bg-slate-700 rounded-full overflow-hidden' }, [
                     React.createElement('div', { className: 'h-full bg-green-500 transition-all', style: { width: `${systemStats.memory}%` } })
                  ]),
                  React.createElement('div', { className: 'flex justify-between text-xs mt-2' }, [
                     React.createElement('span', { className: 'text-slate-500' }, 'Tasks'),
                     React.createElement('span', { className: 'text-yellow-400' }, systemStats.tasks)
                  ]),
                  React.createElement('div', { className: 'flex justify-between text-xs' }, [
                     React.createElement('span', { className: 'text-slate-500' }, 'Uptime'),
                     React.createElement('span', { className: 'text-slate-300' }, systemStats.uptime)
                  ])
               ])
            ]),

            // Persona Switcher
            React.createElement('div', { className: 'bg-slate-800/50 rounded-lg p-3' }, [
               React.createElement('h3', { className: 'text-xs font-bold text-slate-400 mb-3 flex items-center' }, [
                  React.createElement(User, { size: 12, className: 'mr-2' }),
                  'PERSONA'
               ]),
               React.createElement('div', { className: 'space-y-1' }, 
                  personas.map(p => 
                     React.createElement('button', {
                        key: p,
                        onClick: () => switchPersona(p),
                        className: `w-full text-left text-xs px-2 py-1.5 rounded ${persona === p ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400 hover:bg-slate-700/50'}`
                     }, [
                        React.createElement(ChevronRight, { size: 12, className: 'inline mr-1' }),
                        p.charAt(0).toUpperCase() + p.slice(1)
                     ])
                  )
               )
            ]),

            // Mode Indicator
            React.createElement('div', { className: 'bg-slate-800/50 rounded-lg p-3' }, [
               React.createElement('h3', { className: 'text-xs font-bold text-slate-400 mb-2' }, 'MODE'),
               React.createElement('div', { className: `text-sm font-bold ${mode === 'INSERT' ? 'text-magenta-400' : mode === 'VISUAL' ? 'text-yellow-400' : 'text-cyan-400'}` }, 
                  `⬤ ${mode}`
               )
            ]),

            // Quick Actions
            React.createElement('div', { className: 'bg-slate-800/50 rounded-lg p-3' }, [
               React.createElement('h3', { className: 'text-xs font-bold text-slate-400 mb-3' }, 'QUICK ACTIONS'),
               React.createElement('div', { className: 'space-y-1' }, [
                  React.createElement('button', {
                     onClick: () => { setCommandInput('jcapy doctor'); executeCommand(); },
                     className: 'w-full text-left text-xs px-2 py-1.5 rounded text-slate-400 hover:bg-slate-700/50'
                  }, '🏥 Run Doctor'),
                  React.createElement('button', {
                     onClick: () => { setCommandInput('jcapy sync'); executeCommand(); },
                     className: 'w-full text-left text-xs px-2 py-1.5 rounded text-slate-400 hover:bg-slate-700/50'
                  }, '🔄 Sync'),
                  React.createElement('button', {
                     onClick: () => { setCommandInput('jcapy status'); executeCommand(); },
                     className: 'w-full text-left text-xs px-2 py-1.5 rounded text-slate-400 hover:bg-slate-700/50'
                  }, '📊 Status')
               ])
            ])
         ]),

         // Center - Terminal
         React.createElement('div', { key: 'terminal', className: 'flex-1 flex flex-col min-w-0' }, [
            // Terminal Header
            React.createElement('div', { className: 'flex-shrink-0 border-b border-slate-800 bg-slate-900/30 px-4 py-2 flex items-center justify-between' }, [
               React.createElement('div', { className: 'flex items-center space-x-2' }, [
                  React.createElement(Terminal, { size: 16, className: 'text-cyan-400' }),
                  React.createElement('span', { className: 'text-sm font-bold text-white' }, 'TERMINAL'),
                  React.createElement('span', { className: 'text-xs text-slate-500' }, `(${terminalLines.length} lines)`)
               ]),
               React.createElement('button', {
                  onClick: () => setTerminalLines([]),
                  className: 'text-xs text-slate-500 hover:text-slate-300'
               }, 'Clear')
            ]),
            
            // Terminal Output
            React.createElement('div', { 
               ref: terminalRef,
               className: 'flex-1 overflow-y-auto bg-black/40 p-4 font-mono text-sm'
            }, [
               terminalLines.length === 0 && React.createElement('div', { className: 'flex flex-col items-center justify-center h-full text-slate-600' }, [
                  React.createElement(Terminal, { size: 48, className: 'mb-4 opacity-20' }),
                  React.createElement('p', null, 'Terminal output will appear here...'),
                  React.createElement('p', { className: 'text-xs mt-2' }, 'Start JCapy TUI to see live output')
               ]),
               terminalLines.map((line, i) => 
                  React.createElement('div', { 
                     key: i, 
                     className: `whitespace-pre-wrap ${line.startsWith('❯') ? 'text-cyan-400' : line.startsWith('✓') || line.startsWith('✔') ? 'text-green-400' : line.startsWith('✗') || line.startsWith('✘') || line.startsWith('Error') ? 'text-red-400' : 'text-slate-300'}`
                  }, line)
               )
            ]),
            
            // Command Input
            React.createElement('div', { className: 'flex-shrink-0 border-t border-slate-800 bg-slate-900/50 p-3' }, [
               React.createElement('div', { className: 'flex items-center space-x-2' }, [
                  React.createElement('span', { className: 'text-cyan-400' }, '❯'),
                  React.createElement('input', {
                     ref: inputRef,
                     type: 'text',
                     value: commandInput,
                     onChange: (e) => setCommandInput(e.target.value),
                     onKeyDown: handleKeyDown,
                     placeholder: 'Enter command...',
                     className: 'flex-1 bg-transparent border-none outline-none text-white placeholder-slate-600 text-sm'
                  }),
                  React.createElement('button', {
                     onClick: executeCommand,
                     className: 'px-3 py-1 bg-cyan-500/20 text-cyan-400 rounded hover:bg-cyan-500/30 transition-colors text-xs'
                  }, [
                     React.createElement(Send, { size: 14 })
                  ])
               ])
            ])
         ]),

         // Right Sidebar - Events
         React.createElement('aside', { key: 'events', className: 'w-80 flex-shrink-0 border-l border-slate-800 bg-slate-900/30 flex flex-col' }, [
            React.createElement('div', { className: 'flex-shrink-0 border-b border-slate-800 px-4 py-2' }, [
               React.createElement('h3', { className: 'text-sm font-bold text-white flex items-center' }, [
                  React.createElement(Activity, { size: 16, className: 'mr-2 text-cyan-400' }),
                  'EVENT STREAM'
               ])
            ]),
            React.createElement('div', { className: 'flex-1 overflow-y-auto p-3 space-y-2' }, [
               events.length === 0 && React.createElement('div', { className: 'text-center text-slate-600 py-8' }, [
                  React.createElement('p', { className: 'text-xs' }, 'No events yet'),
                  React.createElement('p', { className: 'text-xs mt-1' }, 'Events from TUI will appear here')
               ]),
               events.slice(-20).map((event, i) => 
                  React.createElement('div', { 
                     key: i,
                     className: `p-2 rounded text-xs ${event.type === 'THOUGHT' ? 'bg-blue-500/10 border-l-2 border-blue-500' : 'bg-slate-800/50'}`
                  }, [
                     React.createElement('div', { className: 'flex justify-between mb-1' }, [
                        React.createElement('span', { className: 'font-bold text-slate-400' }, event.type || 'EVENT'),
                        React.createElement('span', { className: 'text-slate-600' }, event.timestamp || '')
                     ]),
                     React.createElement('p', { className: 'text-slate-300' }, event.message || JSON.stringify(event.data || {}).slice(0, 50))
                  ])
               )
            ])
         ])
      ]),

      // Halted Overlay
      React.createElement(AnimatePresence, { key: 'halted' },
         isHalted && React.createElement(motion.div, {
            initial: { opacity: 0 },
            animate: { opacity: 1 },
            className: 'fixed inset-0 z-50 flex items-center justify-center bg-red-950/80 backdrop-blur-sm'
         }, [
            React.createElement(motion.div, {
               initial: { scale: 0.9 },
               animate: { scale: 1 },
               className: 'bg-slate-900 border-2 border-red-500 p-8 rounded-2xl text-center max-w-md'
            }, [
               React.createElement(AlertTriangle, { className: 'text-red-500 w-16 h-16 mx-auto mb-4' }),
               React.createElement('h2', { className: 'text-3xl font-black text-red-500 mb-2' }, 'SYSTEM HALTED'),
               React.createElement('p', { className: 'text-slate-400 mb-6' }, 'All agentic processes suspended'),
               React.createElement('button', {
                  onClick: toggleKillSwitch,
                  className: 'px-6 py-3 bg-red-500 text-white rounded-lg font-bold hover:bg-red-400 transition-colors'
               }, [
                  React.createElement(RefreshCcw, { size: 16, className: 'inline mr-2' }),
                  'RESET'
               ])
            ])
         ])
      )
   ]);
}

export default App;