import { useState } from 'react'
import { Shield, Radio, Activity } from 'lucide-react'
import { motion } from 'framer-motion'

function App() {
   return (
      <div className="min-h-screen w-full flex items-center justify-center p-4">
         <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card max-w-md w-full text-center"
         >
            <div className="flex justify-center mb-6 space-x-4">
               <Shield className="text-blue-500 w-12 h-12" />
               <Radio className="text-green-500 w-12 h-12 animate-pulse" />
            </div>
            <h1 className="text-3xl font-bold mb-2">JCapy Web Control Plane</h1>
            <p className="text-slate-400 mb-6">Orbital Hub & Security Command Center</p>

            <div className="flex items-center justify-center space-x-2 text-sm text-green-400 bg-green-500/10 py-2 rounded-full border border-green-500/20">
               <Activity size={16} />
               <span>Daemon Ready: localhost:jcapyd</span>
            </div>
         </motion.div>
      </div>
   )
}

export default App
