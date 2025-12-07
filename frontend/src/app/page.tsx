"use client";

import { useState } from "react";
import { VoiceDrawer } from "@/components/VoiceDrawer";
import { ChatInterface } from "@/components/ChatInterface";
import { PricingModal } from "@/components/PricingModal";
import { LoginModal } from "@/components/LoginModal";
import { Sidebar as SidebarIcon, Plus, Settings, CreditCard, LogOut, User } from "lucide-react";
import { useAppStore } from '@/store/useAppStore';
import { cn } from "@/lib/utils";

export default function Home() {
  const { user, credits } = useAppStore();
  const [isPricingOpen, setIsPricingOpen] = useState(false);
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <main className="flex h-screen bg-background text-foreground overflow-hidden selection:bg-blue-500/30">
      {/* Sidebar */}
      <div className={cn(
        "bg-[#09090b] border-r border-white/10 flex flex-col transition-all duration-300 ease-in-out relative z-30",
        isSidebarOpen ? "w-72" : "w-0 md:w-20"
      )}>
        {/* App Logo */}
        <div className="p-6 flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 shrink-0 shadow-lg shadow-blue-900/20" />
          <span className={cn("font-bold text-lg tracking-tight whitespace-nowrap transition-opacity", !isSidebarOpen && "opacity-0")}>
            Mosheng
          </span>
        </div>
        
        {/* New Chat Button */}
        <div className="px-4 mb-6">
          <button 
            className={cn(
              "w-full bg-white text-black rounded-xl p-3 font-medium flex items-center justify-center gap-2 hover:bg-gray-200 transition-colors shadow-md",
              !isSidebarOpen && "px-0"
            )}
          >
            <Plus className="w-5 h-5" />
            <span className={cn("transition-opacity", !isSidebarOpen && "hidden")}>New Project</span>
          </button>
        </div>

        {/* Navigation / History */}
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
           {isSidebarOpen && <div className="text-xs font-bold text-muted-foreground px-3 py-2 uppercase tracking-wider">Recent</div>}
           {[1, 2, 3].map((i) => (
             <div key={i} className="p-3 rounded-xl text-sm text-gray-400 cursor-pointer hover:bg-white/5 hover:text-white transition-all flex items-center gap-3 group whitespace-nowrap overflow-hidden">
               <div className="w-2 h-2 rounded-full bg-blue-500/50 group-hover:bg-blue-500 transition-colors shrink-0" />
               <span className={cn("transition-opacity", !isSidebarOpen && "opacity-0")}>
                 Untitled Project {i}
               </span>
             </div>
           ))}
        </div>

        {/* User Profile Section */}
        <div className="p-4 border-t border-white/10 bg-black/20">
           {user ? (
             <div className="flex flex-col gap-3">
               <div className="flex items-center gap-3 overflow-hidden">
                 <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-yellow-400 to-orange-500 flex items-center justify-center shrink-0 font-bold text-black">
                   {user.name[0].toUpperCase()}
                 </div>
                 <div className={cn("flex flex-col transition-opacity", !isSidebarOpen && "opacity-0")}>
                   <span className="font-medium text-sm truncate max-w-[140px]">{user.name}</span>
                   <span className="text-xs text-muted-foreground bg-white/10 px-1.5 py-0.5 rounded-md w-fit">{user.plan} Plan</span>
                 </div>
               </div>
               
               <div className={cn("grid gap-2 transition-opacity", !isSidebarOpen && "hidden")}>
                 <button 
                    onClick={() => setIsPricingOpen(true)}
                    className="flex items-center gap-2 text-xs text-gray-400 hover:text-white p-2 hover:bg-white/5 rounded-lg transition-colors"
                  >
                    <CreditCard className="w-3.5 h-3.5" />
                    {credits.toLocaleString()} credits
                 </button>
                 <button className="flex items-center gap-2 text-xs text-gray-400 hover:text-white p-2 hover:bg-white/5 rounded-lg transition-colors">
                    <Settings className="w-3.5 h-3.5" />
                    Settings
                 </button>
               </div>
             </div>
           ) : (
             <button 
               onClick={() => setIsLoginOpen(true)}
               className={cn(
                 "w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-sm font-medium transition-colors flex items-center justify-center gap-2",
                 !isSidebarOpen && "px-0"
               )}
             >
               <User className="w-4 h-4" />
               <span className={cn("transition-opacity", !isSidebarOpen && "hidden")}>Sign In</span>
             </button>
           )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative bg-background">
        {/* Header */}
        <div className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between z-10 pointer-events-none">
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="pointer-events-auto p-2 hover:bg-white/5 rounded-xl text-muted-foreground hover:text-white transition-colors"
          >
            <SidebarIcon className="w-5 h-5" />
          </button>
          
          {!user && (
            <button 
              onClick={() => setIsLoginOpen(true)}
              className="pointer-events-auto px-4 py-2 bg-white text-black rounded-full text-sm font-medium shadow-lg shadow-white/10 hover:bg-gray-200 transition-colors"
          >
              Log in
            </button>
          )}
        </div>

        {/* Chat Area */}
        <div className="flex-1 relative">
          <ChatInterface />
        </div>

        {/* Voice Selection Drawer */}
        <VoiceDrawer />
      </div>

      {/* Modals */}
      <PricingModal isOpen={isPricingOpen} onClose={() => setIsPricingOpen(false)} />
      <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />
      </main>
  );
}
