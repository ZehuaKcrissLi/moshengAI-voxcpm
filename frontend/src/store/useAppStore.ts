import { create } from 'zustand';
import { Voice, fetchVoices } from '@/lib/api';

interface AppState {
  voices: Voice[];
  selectedVoice: Voice | null;
  isLoadingVoices: boolean;
  credits: number;
  user: { name: string; email: string; plan: string } | null;
  
  // Actions
  loadVoices: () => Promise<void>;
  selectVoice: (voice: Voice) => void;
  deductCredits: (amount: number) => void;
  addCredits: (amount: number) => void;
  login: (email: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  voices: [],
  selectedVoice: null,
  isLoadingVoices: false,
  credits: 100, // Mock initial credits
  user: null, // Not logged in by default

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
  
  deductCredits: (amount) => set((state) => ({ credits: Math.max(0, state.credits - amount) })),
  
  addCredits: (amount) => set((state) => ({ credits: state.credits + amount })),

  login: (email) => set({ user: { name: email.split('@')[0], email, plan: 'Free' } })
}));
