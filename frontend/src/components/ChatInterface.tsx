import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Sparkles, User, Copy, Download, Mic } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { generateAudio, getTaskStatus } from '@/lib/api';
import { AudioPlayer } from './AudioPlayer';
import { VoiceSelector } from './VoiceSelector';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatInterfaceProps {
  onOpenVoiceDrawer: () => void;
}

export function ChatInterface({ onOpenVoiceDrawer }: ChatInterfaceProps) {
  const { selectedVoice, deductCredits, credits } = useAppStore();
  const [text, setText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{type: 'user'|'ai', content: string, audio?: string, voiceName?: string}>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  const handleGenerate = async () => {
    if (!text.trim() || !selectedVoice) return;
    if (credits < text.length) {
      setError('Not enough credits');
      return;
    }

    setIsGenerating(true);
    setError(null);
    
    const currentText = text;
    setMessages(prev => [...prev, { type: 'user', content: currentText }]);
    setText('');

    try {
      const { task_id } = await generateAudio(currentText, selectedVoice.id);
      
      const pollInterval = setInterval(async () => {
        try {
          const status = await getTaskStatus(task_id);
          
          if (status.status === 'completed' && status.output_url) {
            clearInterval(pollInterval);
            setIsGenerating(false);
            // Use window.location.hostname to automatically match the current host
            const fullUrl = `http://${window.location.hostname}:8000${status.output_url}`;
            setMessages(prev => [...prev, { 
              type: 'ai', 
              content: '', 
              audio: fullUrl,
              voiceName: selectedVoice.name
            }]);
            deductCredits(currentText.length);
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setIsGenerating(false);
            setError(status.error || 'Generation failed');
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 1000);

    } catch (err: any) {
      setIsGenerating(false);
      setError(err.response?.data?.detail || 'Failed to submit task');
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-8 pb-32 scrollbar-hide">
        <AnimatePresence initial={false}>
          {messages.length === 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center h-full text-center px-4"
            >
              <div className="w-20 h-20 rounded-3xl bg-secondary/30 flex items-center justify-center mb-6 border border-white/5 shadow-2xl">
                <Sparkles className="w-10 h-10 text-blue-500" />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-b from-white to-gray-400 bg-clip-text text-transparent mb-4">
                Mosheng AI
              </h1>
              <p className="text-muted-foreground max-w-md text-lg leading-relaxed">
                Generate hyper-realistic speech in seconds. Select a voice, type your text, and let the magic happen.
              </p>
            </motion.div>
          )}

          {messages.map((msg, idx) => (
            <motion.div 
              key={idx} 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "flex gap-4 sm:gap-6",
                msg.type === 'user' ? "flex-row-reverse" : "flex-row"
              )}
            >
              {/* Avatar */}
              <div className={cn(
                "w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center shrink-0 border border-white/10 shadow-lg",
                msg.type === 'user' ? "bg-secondary text-gray-300" : "bg-blue-600 text-white"
              )}>
                {msg.type === 'user' ? <User className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
              </div>

              {/* Content */}
              <div className={cn(
                "flex flex-col max-w-[85%] sm:max-w-[75%]",
                msg.type === 'user' ? "items-end" : "items-start"
              )}>
                {msg.type === 'user' ? (
                  <div className="bg-secondary text-foreground rounded-3xl rounded-tr-sm px-6 py-4 border border-white/5 shadow-sm">
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                ) : (
                  <div className="w-full">
                    {msg.audio && (
                      <>
                        <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground">
                          <Mic className="w-3 h-3" />
                          <span>Voice: {msg.voiceName || 'Unknown'}</span>
                        </div>
                        <AudioPlayer src={msg.audio} autoPlay={true} />
                      </>
                    )}
                    <div className="flex items-center gap-2 mt-2 ml-2">
                       <button className="p-1.5 hover:bg-secondary rounded-lg text-muted-foreground hover:text-foreground transition-colors">
                         <Copy className="w-4 h-4" />
                       </button>
                       <button className="p-1.5 hover:bg-secondary rounded-lg text-muted-foreground hover:text-foreground transition-colors">
                         <Download className="w-4 h-4" />
                       </button>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {isGenerating && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-6"
            >
              <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center shrink-0 border border-white/10 shadow-lg">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="flex items-center gap-2 h-10">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-6 bg-gradient-to-t from-background via-background to-transparent z-20">
        <div className="relative bg-secondary/50 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50 transition-all duration-300">
          {/* Voice Selector Ball - Inside Input */}
          <VoiceSelector onClick={onOpenVoiceDrawer} />
          
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={selectedVoice ? `Type your text here...` : "Select a voice first..."}
            className="w-full bg-transparent text-foreground p-4 sm:p-5 pl-16 pr-16 max-h-40 min-h-[60px] resize-none focus:outline-none scrollbar-hide text-base sm:text-lg placeholder:text-muted-foreground/50"
            disabled={isGenerating}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleGenerate();
              }
            }}
          />
          
          <div className="absolute bottom-3 right-3 flex items-center gap-2">
            <span className={cn(
              "text-xs font-medium px-2 py-1 rounded-md bg-black/20 transition-colors",
              text.length > credits ? "text-red-400" : "text-muted-foreground"
            )}>
               {text.length}/{credits}
            </span>
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !text.trim() || !selectedVoice}
              className={cn(
                "w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-lg",
                text.trim() && !isGenerating 
                  ? "bg-blue-600 hover:bg-blue-500 text-white scale-100 rotate-0" 
                  : "bg-white/5 text-muted-foreground cursor-not-allowed scale-90"
              )}
            >
              {isGenerating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5 ml-0.5" />}
            </button>
          </div>
        </div>
        
        {error && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute -top-12 left-1/2 -translate-x-1/2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-full px-4 py-2 text-sm flex items-center gap-2 backdrop-blur-md"
          >
            {error}
          </motion.div>
        )}
      </div>
    </div>
  );
}
