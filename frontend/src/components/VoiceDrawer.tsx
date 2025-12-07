import React, { useEffect, useRef, useState } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { Play, Pause, Search, Mic, X, Volume2, Sparkles, Filter } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Voice } from '@/lib/api';

export function VoiceDrawer() {
  const { voices, selectedVoice, loadVoices, selectVoice, isLoadingVoices } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCategory, setActiveCategory] = useState<'all' | 'male' | 'female'>('all');
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    loadVoices();
  }, [loadVoices]);

  const filteredVoices = voices.filter(v => {
    const matchesSearch = v.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          v.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = activeCategory === 'all' || v.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const handlePlayPreview = (e: React.MouseEvent, voice: Voice) => {
    e.stopPropagation();
    
    if (playingVoiceId === voice.id) {
      audioRef.current?.pause();
      setPlayingVoiceId(null);
    } else {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      // Use window.location.hostname to automatically match the current host
      const url = `http://${window.location.hostname}:8000${voice.preview_url}`;
      const audio = new Audio(url);
      audio.onended = () => setPlayingVoiceId(null);
      audio.play();
      audioRef.current = audio;
      setPlayingVoiceId(voice.id);
    }
  };

  return (
    <>
      {/* Floating Trigger Bar */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-3 px-5 py-3 bg-secondary/80 backdrop-blur-md border border-white/10 rounded-full shadow-2xl hover:bg-secondary transition-colors text-sm font-medium"
        >
          <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
             <Mic className="w-4 h-4" />
          </div>
          <div className="flex flex-col items-start text-left min-w-[120px]">
            <span className="text-xs text-muted-foreground">Current Voice</span>
            <span className="text-foreground">{selectedVoice?.name || 'Select Voice'}</span>
          </div>
          <div className="w-px h-8 bg-white/10 mx-2" />
          <span className="text-xs text-blue-400 font-semibold">CHANGE</span>
        </motion.button>
      </div>

      {/* Drawer Overlay */}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsOpen(false)}
            />
            
            <motion.div 
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="relative w-full max-w-4xl h-[85vh] bg-[#09090b] border border-white/10 rounded-t-3xl sm:rounded-3xl shadow-2xl flex flex-col overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="p-6 border-b border-white/10 flex items-center justify-between bg-[#09090b]">
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <Sparkles className="w-6 h-6 text-blue-500" />
                    Voice Lab
                  </h2>
                  <p className="text-muted-foreground text-sm mt-1">Select a high-fidelity neural voice for your project.</p>
                </div>
                <button 
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-white/10 rounded-full transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {/* Controls */}
              <div className="p-4 border-b border-white/10 bg-secondary/30 space-y-4">
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input 
                      type="text"
                      placeholder="Search by name or style..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full bg-background border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    />
                  </div>
                  <div className="flex p-1 bg-background rounded-xl border border-white/10">
                    {(['all', 'male', 'female'] as const).map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setActiveCategory(cat)}
                        className={cn(
                          "px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-all",
                          activeCategory === cat 
                            ? "bg-secondary text-white shadow-sm" 
                            : "text-muted-foreground hover:text-white"
                        )}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Grid */}
              <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {isLoadingVoices ? (
                  <div className="col-span-full flex flex-col items-center justify-center py-20 text-muted-foreground">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
                    Loading neural voices...
                  </div>
                ) : filteredVoices.map((voice) => (
                  <motion.div 
                    key={voice.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "group relative p-4 rounded-2xl border transition-all cursor-pointer overflow-hidden",
                      selectedVoice?.id === voice.id 
                        ? "bg-blue-500/10 border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.15)]" 
                        : "bg-secondary/40 border-white/5 hover:bg-secondary/60 hover:border-white/10"
                    )}
                    onClick={() => {
                      selectVoice(voice);
                      setIsOpen(false);
                    }}
                  >
                    {/* Background Wave Animation (Mock) */}
                    <div className="absolute bottom-0 left-0 right-0 h-12 opacity-10 pointer-events-none flex items-end justify-between px-4 pb-2 gap-1">
                      {[...Array(10)].map((_, i) => (
                        <div key={i} className="w-1 bg-current h-4 rounded-full" style={{ height: `${Math.random() * 100}%` }} />
                      ))}
                    </div>

                    <div className="flex items-start justify-between relative z-10">
                      <div className="flex items-center gap-3">
                         <div className={cn(
                           "w-10 h-10 rounded-full flex items-center justify-center text-base font-bold shadow-inner",
                           voice.category === 'female' 
                             ? "bg-gradient-to-br from-pink-500 to-rose-600 text-white" 
                             : "bg-gradient-to-br from-blue-500 to-cyan-600 text-white"
                         )}>
                           {voice.name[0]}
                         </div>
                         <div>
                           <h3 className="font-semibold text-foreground">{voice.name}</h3>
                           <span className="text-xs text-muted-foreground capitalize inline-flex items-center gap-1">
                             {voice.category} • Pro
                           </span>
                         </div>
                      </div>
                      
                      <button 
                        onClick={(e) => handlePlayPreview(e, voice)}
                        className={cn(
                          "w-9 h-9 rounded-full flex items-center justify-center transition-all",
                          playingVoiceId === voice.id 
                            ? "bg-white text-black" 
                            : "bg-white/10 text-white hover:bg-white hover:text-black"
                        )}
                      >
                        {playingVoiceId === voice.id ? (
                          <Pause className="w-4 h-4 fill-current" />
                        ) : (
                          <Play className="w-4 h-4 fill-current" />
                        )}
                      </button>
                    </div>
                    
                    {voice.transcript && (
                      <p className="mt-4 text-xs text-muted-foreground line-clamp-2 relative z-10 font-light italic">
                        "{voice.transcript}"
                      </p>
                    )}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
