import React, { useEffect, useRef, useState } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { Play, Pause, Search, Mic, X, Volume2, Sparkles, Filter } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Voice } from '@/lib/api';

interface VoiceDrawerProps {
  trigger?: React.ReactNode;
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function VoiceDrawer({ trigger, isOpen: controlledIsOpen, onOpenChange }: VoiceDrawerProps) {
  const { voices, selectedVoice, loadVoices, selectVoice, isLoadingVoices } = useAppStore();
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeCategory, setActiveCategory] = useState<'all' | 'male' | 'female'>('all');
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Use controlled state if provided, otherwise use internal state
  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const setIsOpen = (open: boolean) => {
    if (onOpenChange) {
      onOpenChange(open);
    } else {
      setInternalIsOpen(open);
    }
  };

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
      {/* Only show trigger if explicitly provided */}
      {trigger && (
        <div onClick={() => setIsOpen(true)}>
          {trigger}
        </div>
      )}

      {/* Drawer Overlay */}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsOpen(false)}
            />
            
            <motion.div 
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="relative w-full max-w-5xl max-h-[80vh] bg-[#09090b] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
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
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "group relative rounded-2xl border transition-all cursor-pointer overflow-hidden min-h-[140px]",
                      selectedVoice?.id === voice.id 
                        ? "bg-blue-500/10 border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.15)]" 
                        : "bg-secondary/40 border-white/5 hover:bg-secondary/60 hover:border-white/10"
                    )}
                    onClick={() => {
                      selectVoice(voice);
                      setIsOpen(false);
                    }}
                  >
                    {/* Content Section */}
                    <div className="p-4 h-full flex flex-col min-h-[140px]">
                      {/* Header - Icon, Name, Play Button */}
                      <div className="flex items-center gap-3 mb-3">
                        <div className={cn(
                          "w-10 h-10 rounded-full flex items-center justify-center text-base font-bold shadow-inner flex-shrink-0",
                          voice.category === 'female' 
                            ? "bg-gradient-to-br from-pink-500 to-rose-600 text-white" 
                            : "bg-gradient-to-br from-blue-500 to-cyan-600 text-white"
                        )}>
                          {voice.name[0]}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-foreground text-sm truncate">{voice.name}</h3>
                          <span className="text-xs text-muted-foreground capitalize">
                            {voice.category} • Pro
                          </span>
                        </div>
                        <button 
                          onClick={(e) => handlePlayPreview(e, voice)}
                          className={cn(
                            "w-9 h-9 rounded-full flex items-center justify-center transition-all flex-shrink-0",
                            playingVoiceId === voice.id 
                              ? "bg-white text-black shadow-lg" 
                              : "bg-white/10 text-white hover:bg-white hover:text-black"
                          )}
                        >
                          {playingVoiceId === voice.id ? (
                            <Pause className="w-4 h-4 fill-current" />
                          ) : (
                            <Play className="w-4 h-4 fill-current ml-0.5" />
                          )}
                        </button>
                      </div>
                      
                      {/* Transcript */}
                      {voice.transcript && (
                        <p className="text-xs text-muted-foreground line-clamp-2 font-light italic leading-relaxed mb-3">
                          "{voice.transcript}"
                        </p>
                      )}
                      
                      {/* Audio Wave Visualization - Bottom */}
                      <div className="mt-auto flex items-end justify-between gap-0.5 h-6 opacity-20">
                        {[...Array(16)].map((_, i) => (
                          <div 
                            key={i} 
                            className={cn(
                              "w-full rounded-full transition-all",
                              voice.category === 'female' ? "bg-pink-500" : "bg-blue-500",
                              playingVoiceId === voice.id && "animate-pulse"
                            )} 
                            style={{ 
                              height: `${30 + Math.sin(i * 0.5) * 50}%`,
                              animationDelay: `${i * 50}ms`
                            }} 
                          />
                        ))}
                      </div>
                    </div>
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
