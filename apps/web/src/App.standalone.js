import React, { useState, useEffect, useRef } from 'react';
import { Shield, Radio, Activity, Terminal, Zap, Power, AlertTriangle, RefreshCcw, Check, X, ShieldAlert, Cpu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { MockDaemonBridge } from 'mock-daemon';

function App() {
   const [isHalted, setIsHalted] = useState(false);
   const [events, setEvents] = useState([]);
   const [activeIntervention, setActiveIntervention] = useState(null);
   const bridgeRef = useRef(null);

   useEffect(() => {
      if (!bridgeRef.current) {
         bridgeRef.current = new MockDaemonBridge((event) => {
            setEvents(prev => [...prev, event]);
            if (event.type === 'INTERVENTION') {
               setActiveIntervention(event);
            }
         });
         bridgeRef.current.start();
      }
      return () => bridgeRef.current?.stop();
   }, []);

   const toggleKillSwitch = () => {
      setIsHalted(!isHalted);
   };

   const handleIntervention = (approved) => {
      setActiveIntervention(null);
      bridgeRef.current.respondToIntervention(activeIntervention.id, approved);
   };

   return React.createElement('div', { className: 'min-h-screen w-full flex flex-col p-8 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-blue-900/20 via-slate-900 to-slate-950 font-sans' }, [

      // System Halted Overlay
      React.createElement(AnimatePresence, { key: 'halted-presence' },
         isHalted && React.createElement(motion.div, {
            initial: { opacity: 0 },
            animate: { opacity: 1 },
            exit: { opacity: 0 },
            className: 'fixed inset-0 z-[100] flex items-center justify-center bg-red-950/40 backdrop-blur-md'
         }, [
            React.createElement(motion.div, {
               initial: { scale: 0.9, y: 20 },
               animate: { scale: 1, y: 0 },
               className: 'bg-red-600/10 border-2 border-red-500/50 p-12 rounded-3xl text-center max-w-lg shadow-[0_0_100px_rgba(239,68,68,0.2)]'
            }, [
               React.createElement(AlertTriangle, { className: 'text-red-500 w-24 h-24 mx-auto mb-6 animate-pulse' }),
               React.createElement('h1', { className: 'text-5xl font-black text-red-500 mb-4 tracking-tighter' }, 'SYSTEM HALTED'),
               React.createElement('p', { className: 'text-red-200/60 mb-8 font-mono text-sm' }, 'Manual intervention triggered. All agentic processes suspended.'),
               React.createElement('button', {
                  onClick: toggleKillSwitch,
                  className: 'flex items-center mx-auto space-x-2 bg-red-500 hover:bg-red-400 text-white px-8 py-4 rounded-xl font-bold transition-all shadow-lg hover:shadow-red-500/40'
               }, [
                  React.createElement(RefreshCcw, { className: 'w-5 h-5' }),
                  React.createElement('span', null, 'RESET CIRCUIT')
               ])
            ])
         ])
      ),

      // Header
      React.createElement('header', { key: 'header', className: 'flex justify-between items-center mb-12' }, [
         React.createElement('div', { className: 'flex items-center space-x-3' }, [
            React.createElement(Shield, { className: 'text-primary w-8 h-8' }),
            React.createElement('div', null, [
               React.createElement('h1', { className: 'text-2xl font-bold tracking-tight text-white' }, 'JCapy Control Plane'),
               React.createElement('p', { className: 'text-[10px] text-slate-500 font-mono tracking-widest' }, 'STATION // ALPHA-01')
            ])
         ]),
         React.createElement('div', { className: 'flex items-center space-x-4' }, [
            React.createElement('div', { className: 'flex items-center space-x-2 text-xs bg-blue-500/10 text-blue-400 px-4 py-1.5 rounded-full border border-blue-500/20' }, [
               React.createElement('div', { className: 'w-2 h-2 bg-blue-500 rounded-full' }),
               React.createElement('span', { className: 'font-semibold tracking-wide' }, 'DAEMON SYNCHRONIZED')
            ]),
            React.createElement('button', {
               onClick: toggleKillSwitch,
               className: 'group flex items-center space-x-2 bg-red-600/10 hover:bg-red-600/30 text-red-500 px-4 py-1.5 rounded-full border border-red-500/30 transition-all font-black text-[10px] uppercase tracking-widest ring-1 ring-red-500/20 hover:ring-red-500/50'
            }, [
               React.createElement(Power, { className: 'w-3 h-3 group-hover:animate-pulse' }),
               React.createElement('span', null, 'Kill Switch')
            ])
         ])
      ]),

      // Main Content
      React.createElement('main', { key: 'main', className: 'flex-1 grid grid-cols-12 gap-8 h-[calc(100vh-200px)]' }, [
         // Left Sidebar: Capability Manifest
         React.createElement('aside', { key: 'sidebar', className: 'col-span-3 flex flex-col space-y-6 overflow-y-auto pr-2' }, [
            React.createElement('div', { className: 'glass-card border-white/5 bg-slate-400/5' }, [
               React.createElement('h2', { className: 'text-[10px] font-black text-slate-500 mb-6 flex items-center tracking-[4px]' }, [
                  React.createElement(Zap, { size: 12, className: 'mr-2 text-blue-400' }),
                  'CAPABILITY MANIFEST'
               ]),
               React.createElement('div', { className: 'space-y-4' }, [
                  { label: 'File System (READ)', status: 'ACTIVE', color: 'text-green-400', bg: 'bg-green-400/10' },
                  { label: 'File System (WRITE)', status: activeIntervention ? 'INTERVENING' : 'LOCKED', color: activeIntervention ? 'text-amber-500 animate-pulse' : 'text-amber-400', bg: activeIntervention ? 'bg-amber-500/20' : 'bg-amber-400/10' },
                  { label: 'Terminal Access', status: 'ACTIVE', color: 'text-green-400', bg: 'bg-green-400/10' },
                  { label: 'Network Ingress', status: 'BLOCKED', color: 'text-red-400', bg: 'bg-red-400/10' }
               ].map((item, i) =>
                  React.createElement('div', { key: i, className: `flex justify-between items-center p-3 rounded-lg bg-white/5 border border-white/5 transition-all ${item.status === 'INTERVENING' ? 'border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.2)]' : ''}` }, [
                     React.createElement('span', { className: 'text-xs text-slate-300 font-medium' }, item.label),
                     React.createElement('span', { className: `text-[9px] font-black px-2 py-0.5 rounded ${item.bg} ${item.color}` }, item.status)
                  ])
               ))
            ]),

            // Active Agent Info
            React.createElement('div', { className: 'glass-card border-white/5 bg-blue-500/5' }, [
               React.createElement('h2', { className: 'text-[10px] font-black text-slate-500 mb-4 flex items-center tracking-[4px]' }, [
                  React.createElement(Cpu, { size: 12, className: 'mr-2 text-blue-400' }),
                  'ACTIVE AGENT'
               ]),
               React.createElement('div', { className: 'flex items-center space-x-3 mb-4' }, [
                  React.createElement('div', { className: 'w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center' }, [
                     React.createElement(Terminal, { className: 'text-blue-400 w-6 h-6' })
                  ]),
                  React.createElement('div', null, [
                     React.createElement('p', { className: 'text-xs font-bold' }, 'ClawEngine.v2'),
                     React.createElement('p', { className: 'text-[10px] text-slate-500 font-mono' }, 'MODEL // CLAUDE-02')
                  ])
               ]),
               React.createElement('div', { className: 'w-full h-1 bg-white/5 rounded-full overflow-hidden' }, [
                  React.createElement(motion.div, {
                     animate: { width: ['0%', '70%', '40%', '90%'] },
                     transition: { repeat: Infinity, duration: 4 },
                     className: 'h-full bg-blue-500'
                  })
               ])
            ])
         ]),

         // Center Column: Reasoning Stream
         React.createElement('section', { key: 'stream', className: 'col-span-9 flex flex-col' }, [
            React.createElement('div', { className: 'glass-card flex-1 min-h-[600px] flex flex-col overflow-hidden' }, [
               React.createElement('div', { className: 'flex justify-between items-center mb-6' }, [
                  React.createElement('h2', { className: 'text-[10px] font-black text-slate-500 flex items-center tracking-[4px]' }, [
                     React.createElement(Terminal, { size: 12, className: 'mr-2 text-blue-400' }),
                     'REASONING STREAM (ASI-10)'
                  ]),
                  React.createElement('div', { className: 'flex items-center space-x-2' }, [
                     React.createElement('span', { className: 'text-[9px] text-slate-500 font-mono' }, 'v2.0.0-ORBITAL'),
                     React.createElement(Radio, { size: 12, className: 'text-primary animate-pulse' })
                  ])
               ]),

               React.createElement('div', { className: 'flex-1 border border-white/5 rounded-2xl bg-black/40 p-6 font-mono text-sm overflow-y-auto space-y-6 custom-scrollbar' }, [
                  events.map((event, i) => {
                     if (event.type === 'INTERVENTION') {
                        return React.createElement(motion.div, {
                           key: i,
                           initial: { opacity: 0, scale: 0.98 },
                           animate: { opacity: 1, scale: 1 },
                           className: 'p-6 bg-amber-500/10 rounded-2xl border-2 border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.1)]'
                        }, [
                           React.createElement('div', { className: 'flex items-center space-x-2 text-amber-500 mb-4' }, [
                              React.createElement(ShieldAlert, { size: 20 }),
                              React.createElement('span', { className: 'font-black text-xs uppercase tracking-widest' }, 'Intervention Required: Tool Proxy Boundary')
                           ]),
                           React.createElement('p', { className: 'text-sm text-amber-200/80 mb-4' }, `The agent is requesting to execute ${event.tool} on ${event.path}`),

                           // Diff Block
                           React.createElement('div', { className: 'bg-black/40 rounded-xl p-4 border border-white/5 mb-6 overflow-x-auto' }, [
                              React.createElement('pre', { className: 'text-[11px] leading-relaxed' },
                                 event.diff.split('\n').map((line, li) =>
                                    React.createElement('div', { key: li, className: line.startsWith('+') ? 'text-green-400 bg-green-400/10' : line.startsWith('-') ? 'text-red-400 bg-red-400/10' : 'text-slate-400' }, line)
                                 )
                              )
                           ]),

                           // Action Buttons
                           activeIntervention?.id === event.id ? React.createElement('div', { className: 'flex space-x-3' }, [
                              React.createElement('button', {
                                 onClick: () => handleIntervention(true),
                                 className: 'flex-1 flex items-center justify-center space-x-2 bg-green-500/20 hover:bg-green-500 text-green-400 hover:text-white border border-green-500/30 p-3 rounded-xl font-bold transition-all'
                              }, [
                                 React.createElement(Check, { size: 16 }),
                                 React.createElement('span', null, 'APPROVE')
                              ]),
                              React.createElement('button', {
                                 onClick: () => handleIntervention(false),
                                 className: 'flex-1 flex items-center justify-center space-x-2 bg-red-500/20 hover:bg-red-500 text-red-400 hover:text-white border border-red-500/30 p-3 rounded-xl font-bold transition-all'
                              }, [
                                 React.createElement(X, { size: 16 }),
                                 React.createElement('span', null, 'REJECT')
                              ])
                           ]) : React.createElement('p', { className: 'text-xs text-slate-500 italic' }, 'Handled by Operator')
                        ]);
                     }

                     return React.createElement(motion.div, {
                        key: i,
                        initial: { opacity: 0, x: -10 },
                        animate: { opacity: 1, x: 0 },
                        className: `p-4 rounded-xl border relative overflow-hidden ${event.type === 'THOUGHT' ? 'bg-blue-500/5 border-blue-500/10' : 'bg-slate-500/5 border-white/5'}`
                     }, [
                        React.createElement('div', { className: `absolute left-0 top-0 bottom-0 w-1 ${event.type === 'THOUGHT' ? 'bg-blue-500' : 'bg-slate-700'}` }),
                        React.createElement('div', { className: 'flex justify-between mb-2' }, [
                           React.createElement('span', { className: `text-[10px] font-black uppercase tracking-widest ${event.type === 'THOUGHT' ? 'text-blue-400/60' : 'text-slate-500'}` }, event.type),
                           React.createElement('span', { className: 'text-[10px] font-mono text-slate-600' }, event.timestamp)
                        ]),
                        React.createElement('p', { className: 'text-slate-300 leading-relaxed' }, event.message)
                     ]);
                  })
               ])
            ])
         ])
      ])
   ]);
}

export default App;
