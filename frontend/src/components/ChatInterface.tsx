import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Sparkles, User, Mic, X, ChevronDown } from 'lucide-react';
import { useAppStore, Message } from '@/store/useAppStore';
import { generateAudio, getTaskStatus, getCreditsBalance } from '@/lib/api';
import { AudioPlayer } from './AudioPlayer';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatInterfaceProps {
  onOpenVoiceDrawer: () => void;
}

export function ChatInterface({ onOpenVoiceDrawer }: ChatInterfaceProps) {
  const { 
    selectedVoice, 
    getCurrentConversation, 
    updateConversationMessages,
    currentConversationId,
    createConversation,
    user,
    setCredits,
    selectVoice
  } = useAppStore();
  
  const [text, setText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Get messages from current conversation
  const currentConversation = getCurrentConversation();
  const messages = currentConversation?.messages || [];

  // Create initial conversation if none exists
  useEffect(() => {
    if (!currentConversationId) {
      createConversation();
    }
  }, [currentConversationId, createConversation]);

  const scrollToBottom = (smooth = true) => {
    if (messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      // 使用双重 requestAnimationFrame 确保DOM完全更新后再滚动
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          if (smooth) {
            container.scrollTo({
              top: container.scrollHeight,
              behavior: 'smooth'
            });
          } else {
            container.scrollTop = container.scrollHeight;
          }
        });
      });
    }
  };

  useEffect(() => {
    // 延迟滚动，确保内容已渲染
    // 使用 messages.length 而不是 messages 数组本身，避免不必要的重新渲染
    const timer = setTimeout(() => {
      scrollToBottom(true);
    }, 150);
    return () => clearTimeout(timer);
  }, [messages.length, isGenerating]);

  const handleGenerate = async () => {
    if (!text.trim() || !selectedVoice || !currentConversationId) return;

    // Check credits before generating
    const { credits } = useAppStore.getState();
    const estimatedCost = text.trim().length; // 1 credit per character
    if (credits < estimatedCost) {
      setError(`Insufficient credits. You need at least ${estimatedCost} credits, but you have ${credits}.`);
      return;
    }

    setIsGenerating(true);
    setError(null);
    
    const currentText = text;
    const newMessages: Message[] = [...messages, { type: 'user', content: currentText }];
    updateConversationMessages(currentConversationId, newMessages);
    setText('');
    // 用户消息添加后立即滚动
    setTimeout(() => scrollToBottom(true), 100);

    try {
      // Refresh credits before generating to ensure we have the latest balance
      const balance = await getCreditsBalance();
      setCredits(balance.balance);
      
      if (balance.balance < estimatedCost) {
        setIsGenerating(false);
        setError(`Insufficient credits. You need at least ${estimatedCost} credits, but you have ${balance.balance}.`);
        return;
      }
      
      const { task_id, cost } = await generateAudio(currentText, selectedVoice.id);
      
      const pollInterval = setInterval(async () => {
        try {
          const status = await getTaskStatus(task_id);
          
          if (status.status === 'completed' && status.output_url) {
            clearInterval(pollInterval);
            setIsGenerating(false);
            // Use relative path, Next.js will proxy to backend
            const fullUrl = `/api${status.output_url}`;
            const updatedMessages: Message[] = [
              ...newMessages,
              { 
              type: 'ai', 
              content: '', 
                audio: fullUrl,
                voiceName: selectedVoice.name
              }
            ];
            updateConversationMessages(currentConversationId, updatedMessages);
            
            // 确保新消息添加后滚动到底部
            setTimeout(() => scrollToBottom(true), 200);
            
            // Refresh credits balance
            try {
              const balance = await getCreditsBalance();
              setCredits(balance.balance);
            } catch (err) {
              console.error('Failed to refresh credits:', err);
            }
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
      const errorDetail = err.response?.data?.detail || 'Failed to submit task';
      setError(errorDetail);
      
      // Handle specific error codes
      if (err.response?.status === 402) {
        // Insufficient credits
        setError('Insufficient credits. Please recharge to continue.');
      } else if (err.response?.status === 401) {
        // Unauthorized - will be handled by axios interceptor
        setError('Please log in to generate audio.');
      }
    }
  };

  const handleDownload = (audioUrl: string, voiceName?: string) => {
    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = `${voiceName || 'audio'}_${Date.now()}.wav`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCopyText = (content: string) => {
    navigator.clipboard.writeText(content);
    // Could add a toast notification here
  };

  return (
    <div className="flex flex-col h-full w-full relative">
      {/* Messages Area - 修复滚动问题 */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto overscroll-contain p-4 sm:p-6 space-y-8 pb-32 scrollbar-hide"
      >
        <AnimatePresence initial={false}>
          {messages.length === 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center min-h-full text-center px-4"
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
                "flex gap-4 sm:gap-6 max-w-4xl mx-auto",
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
                        <AudioPlayer src={msg.audio} autoPlay={true} voiceName={msg.voiceName} />
                      </>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {isGenerating && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-6 max-w-4xl mx-auto"
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

      {/* Input Area - 固定在底部，嵌入背景 */}
      <div className="absolute bottom-0 left-0 right-0 p-4 sm:p-6 z-20">
        <div className="max-w-4xl mx-auto">
        <div className="relative bg-secondary/50 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50 transition-all duration-300">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={selectedVoice ? `Type your text here...` : "Select a voice first..."}
            className="w-full bg-transparent text-foreground p-4 sm:p-5 pl-4 pr-16 max-h-40 min-h-[60px] resize-none focus:outline-none scrollbar-hide text-base sm:text-lg placeholder:text-muted-foreground/50"
            disabled={isGenerating}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleGenerate();
              }
            }}
          />
          
          {/* Voice Tag - Bottom Left (Clickable) */}
          <div className="absolute bottom-3 left-3 flex items-center gap-2 z-10">
            <AnimatePresence mode="wait">
              {selectedVoice ? (
                <motion.button
                  key="selected"
                  initial={{ opacity: 0, scale: 0.8, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.8, y: 10 }}
                  transition={{ type: "spring", damping: 20, stiffness: 300 }}
                  onClick={onOpenVoiceDrawer}
                  className="group flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-400 text-sm font-medium backdrop-blur-sm hover:bg-blue-500/30 hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/20 transition-all duration-200 cursor-pointer"
                  whileHover={{ scale: 1.05, y: -1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Mic className="w-3.5 h-3.5 flex-shrink-0 group-hover:scale-110 transition-transform" />
                  <span className="max-w-[140px] truncate group-hover:max-w-none transition-all duration-300">{selectedVoice.name}</span>
                  <ChevronDown className="w-3.5 h-3.5 flex-shrink-0 opacity-60 group-hover:opacity-100 group-hover:translate-y-0.5 transition-all" />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      selectVoice(null);
                    }}
                    className="ml-0.5 p-0.5 hover:bg-blue-500/40 rounded-full transition-colors flex-shrink-0 hover:scale-110"
                    aria-label="Remove voice"
                    onMouseEnter={(e) => e.stopPropagation()}
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </motion.button>
              ) : (
                <motion.button
                  key="placeholder"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  transition={{ type: "spring", damping: 20, stiffness: 300 }}
                  onClick={onOpenVoiceDrawer}
                  className="group flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-muted-foreground text-sm font-medium hover:bg-white/20 hover:text-white hover:border-white/30 hover:shadow-lg hover:shadow-white/10 transition-all duration-200 cursor-pointer"
                  whileHover={{ scale: 1.05, y: -1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Mic className="w-3.5 h-3.5 flex-shrink-0 group-hover:scale-110 transition-transform" />
                  <span>选择音色</span>
                  <ChevronDown className="w-3.5 h-3.5 flex-shrink-0 opacity-60 group-hover:opacity-100 group-hover:translate-y-0.5 transition-all" />
                </motion.button>
              )}
            </AnimatePresence>
          </div>
          
          <div className="absolute bottom-3 right-3 flex items-center gap-2">
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
