import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Voice, fetchVoices, getMe, getCreditsBalance, UserResponse } from '@/lib/api';

export interface Message {
  type: 'user' | 'ai';
  content: string;
  audio?: string;
  voiceName?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export interface User {
  id: string;
  name: string;
  email: string;
  plan: string;
  credits: number;
  avatar?: string;
}

interface AppState {
  voices: Voice[];
  selectedVoice: Voice | null;
  isLoadingVoices: boolean;
  credits: number;
  user: User | null;
  
  // Conversation management
  conversations: Conversation[];
  currentConversationId: string | null;
  
  // Actions
  loadVoices: () => Promise<void>;
  selectVoice: (voice: Voice | null) => void;
  setCredits: (credits: number) => void;
  deductCredits: (amount: number) => void;
  addCredits: (amount: number) => void;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  
  // Conversation actions
  createConversation: () => string;
  selectConversation: (id: string) => void;
  updateConversationMessages: (id: string, messages: Message[]) => void;
  deleteConversation: (id: string) => void;
  getCurrentConversation: () => Conversation | null;
  updateConversationTitle: (id: string, title: string) => void;
}

const generateId = () => `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const generateTitle = (messages: Message[]): string => {
  if (messages.length === 0) return 'New Conversation';
  const firstUserMessage = messages.find(m => m.type === 'user');
  if (!firstUserMessage) return 'New Conversation';
  
  // Use first 50 chars of first message as title
  const title = firstUserMessage.content.trim().substring(0, 50);
  return title + (firstUserMessage.content.length > 50 ? '...' : '');
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
  voices: [],
  selectedVoice: null,
  isLoadingVoices: false,
      credits: 100,
      user: null,
      conversations: [],
      currentConversationId: null,

  loadVoices: async () => {
    set({ isLoadingVoices: true });
    try {
      const voices = await fetchVoices();
      set({ voices, isLoadingVoices: false });
      if (voices.length > 0) {
        set((state) => ({ 
          selectedVoice: state.selectedVoice || voices[0] 
        }));
      }
    } catch (error) {
      console.error("Failed to load voices", error);
      set({ isLoadingVoices: false });
    }
  },

  selectVoice: (voice) => set({ selectedVoice: voice }),
  
  setCredits: (credits) => set({ credits }),
  
  deductCredits: (amount) => set((state) => ({ credits: Math.max(0, state.credits - amount) })),
  
  addCredits: (amount) => set((state) => ({ credits: state.credits + amount })),

      login: async (token: string) => {
        localStorage.setItem('access_token', token);
        try {
          const userData = await getMe();
          const balanceData = await getCreditsBalance();
          
          set({
            user: {
              id: userData.id,
              name: userData.email.split('@')[0],
              email: userData.email,
              plan: 'Free',
              credits: balanceData.balance,
              avatar: userData.avatar,
            },
            credits: balanceData.balance,
          });
        } catch (error) {
          console.error('Failed to fetch user data:', error);
          localStorage.removeItem('access_token');
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, credits: 0 });
      },

      refreshUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        try {
          const userData = await getMe();
          const balanceData = await getCreditsBalance();
          
          set({
            user: {
              id: userData.id,
              name: userData.email.split('@')[0],
              email: userData.email,
              plan: 'Free',
              credits: balanceData.balance,
              avatar: userData.avatar,
            },
            credits: balanceData.balance,
          });
        } catch (error) {
          console.error('Failed to refresh user data:', error);
          localStorage.removeItem('access_token');
          set({ user: null, credits: 0 });
        }
      },

      // Conversation management
      createConversation: () => {
        const id = generateId();
        const newConv: Conversation = {
          id,
          title: 'New Conversation',
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        
        set((state) => ({
          conversations: [newConv, ...state.conversations],
          currentConversationId: id,
        }));
        
        return id;
      },

      selectConversation: (id) => {
        set({ currentConversationId: id });
      },

      updateConversationMessages: (id, messages) => {
        set((state) => {
          const conversations = state.conversations.map((conv) => {
            if (conv.id === id) {
              return {
                ...conv,
                messages,
                title: messages.length > 0 ? generateTitle(messages) : conv.title,
                updatedAt: Date.now(),
              };
            }
            return conv;
          });
          
          // Sort by updatedAt (most recent first)
          conversations.sort((a, b) => b.updatedAt - a.updatedAt);
          
          return { conversations };
        });
      },

      updateConversationTitle: (id, title) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === id ? { ...conv, title } : conv
          ),
        }));
      },

      deleteConversation: (id) => {
        set((state) => {
          const conversations = state.conversations.filter((c) => c.id !== id);
          let newCurrentId = state.currentConversationId;
          
          // If deleting current conversation, switch to another
          if (state.currentConversationId === id) {
            newCurrentId = conversations.length > 0 ? conversations[0].id : null;
          }
          
          return {
            conversations,
            currentConversationId: newCurrentId,
          };
        });
      },

      getCurrentConversation: () => {
        const state = get();
        if (!state.currentConversationId) return null;
        return state.conversations.find((c) => c.id === state.currentConversationId) || null;
      },
    }),
    {
      name: 'mosheng-storage',
      partialize: (state) => ({
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
        selectedVoice: state.selectedVoice,
        user: state.user,
      }),
    }
  )
);
