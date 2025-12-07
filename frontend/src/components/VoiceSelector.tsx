import React, { useState } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { Mic } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceSelectorProps {
  onClick: () => void;
}

export function VoiceSelector({ onClick }: VoiceSelectorProps) {
  const { selectedVoice } = useAppStore();
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="absolute bottom-3 left-3 group"
      whileTap={{ scale: 0.95 }}
    >
      <motion.div
        animate={{
          width: isHovered ? 'auto' : '40px',
        }}
        transition={{ type: 'spring', damping: 20, stiffness: 300 }}
        className={cn(
          "h-10 rounded-full flex items-center gap-2 overflow-hidden transition-all",
          selectedVoice 
            ? "bg-gradient-to-r from-blue-500 to-purple-500" 
            : "bg-white/10 hover:bg-white/20"
        )}
      >
        {/* Icon Circle */}
        <div className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0",
          selectedVoice 
            ? selectedVoice.category === 'female'
              ? "bg-pink-500/30"
              : "bg-blue-500/30"
            : "bg-white/10"
        )}>
          <Mic className={cn(
            "w-5 h-5 transition-all",
            selectedVoice ? "text-white" : "text-muted-foreground",
            isHovered && "scale-110"
          )} />
        </div>

        {/* Expanded Text */}
        <AnimatePresence>
          {isHovered && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="pr-4 whitespace-nowrap"
            >
              <div className="flex flex-col items-start">
                <span className="text-[10px] text-white/70 font-medium leading-tight">
                  {selectedVoice ? 'Current Voice' : 'Select Voice'}
                </span>
                <span className="text-xs text-white font-semibold leading-tight">
                  {selectedVoice?.name || 'Click to choose'}
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.button>
  );
}

