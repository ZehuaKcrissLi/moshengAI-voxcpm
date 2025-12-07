import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mail, Lock, Github } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const { login } = useAppStore();
  const [email, setEmail] = useState('');
  const [isLogin, setIsLogin] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login(email);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
            onClick={onClose}
          />
          
          <motion.div 
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            className="relative bg-[#09090b] border border-white/10 w-full max-w-md rounded-2xl shadow-2xl p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={onClose}
              className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-8">
               <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl mx-auto mb-4 shadow-lg shadow-blue-900/20" />
               <h2 className="text-2xl font-bold">{isLogin ? 'Welcome back' : 'Create an account'}</h2>
               <p className="text-muted-foreground text-sm mt-2">Enter your details to access Mosheng AI</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input 
                    type="email" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full bg-secondary/30 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    placeholder="name@example.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input 
                    type="password" 
                    className="w-full bg-secondary/30 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button className="w-full bg-white text-black font-medium py-3 rounded-xl hover:bg-gray-200 transition-colors mt-2">
                {isLogin ? 'Sign In' : 'Sign Up'}
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-xs text-muted-foreground mb-4">Or continue with</p>
              <div className="grid grid-cols-2 gap-3">
                <button className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-secondary/30 hover:bg-secondary/50 border border-white/5 transition-colors">
                  <Github className="w-4 h-4" />
                  <span className="text-sm">GitHub</span>
                </button>
                <button className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-secondary/30 hover:bg-secondary/50 border border-white/5 transition-colors">
                  <span className="text-sm font-bold">G</span>
                  <span className="text-sm">Google</span>
                </button>
              </div>
            </div>

            <div className="mt-6 text-center text-sm">
              <span className="text-muted-foreground">
                {isLogin ? "Don't have an account? " : "Already have an account? "}
              </span>
              <button 
                onClick={() => setIsLogin(!isLogin)}
                className="text-blue-400 hover:text-blue-300 font-medium"
              >
                {isLogin ? 'Sign Up' : 'Sign In'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

