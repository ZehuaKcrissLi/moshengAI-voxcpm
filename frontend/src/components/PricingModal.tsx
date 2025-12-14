import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CreditCard, Check, Zap } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { getCreditsBalance } from '@/lib/api';

interface PricingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    price: '$10',
    credits: 10000,
    features: ['Standard Latency', 'Public Voices'],
    popular: false
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$29',
    credits: 50000,
    features: ['Ultra-low Latency', 'All Voices', 'Priority Queue'],
    popular: true
  },
  {
    id: 'business',
    name: 'Business',
    price: '$99',
    credits: 200000,
    features: ['Custom Voice Cloning', 'API Access', 'Dedicated Support'],
    popular: false
  }
];

export function PricingModal({ isOpen, onClose }: PricingModalProps) {
  const { setCredits, refreshUser } = useAppStore();

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
            onClick={onClose}
          />
          
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="relative bg-[#09090b] border border-white/10 w-full max-w-4xl rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 md:p-8 text-center">
              <button 
                onClick={onClose}
                className="absolute top-4 right-4 p-2 hover:bg-white/10 rounded-full transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              
              <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                Upgrade your voice
              </h2>
              <p className="text-muted-foreground mt-2">Choose a plan that fits your creative needs.</p>
            </div>

            <div className="flex-1 overflow-y-auto p-6 pt-0">
              <div className="grid md:grid-cols-3 gap-6">
                {PLANS.map((plan) => (
                  <div 
                    key={plan.id}
                    className={cn(
                      "relative p-6 rounded-2xl border flex flex-col",
                      plan.popular 
                        ? "bg-blue-500/5 border-blue-500/50 shadow-lg shadow-blue-900/20" 
                        : "bg-secondary/20 border-white/10"
                    )}
                  >
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full uppercase tracking-wide shadow-lg">
                        Most Popular
                      </div>
                    )}
                    
                    <h3 className="text-xl font-bold">{plan.name}</h3>
                    <div className="mt-2 flex items-baseline gap-1">
                      <span className="text-3xl font-bold">{plan.price}</span>
                      <span className="text-muted-foreground">/mo</span>
                    </div>
                    <div className="mt-4 p-3 bg-white/5 rounded-xl flex items-center gap-3">
                       <Zap className="w-5 h-5 text-yellow-400" />
                       <span className="font-semibold">{plan.credits.toLocaleString()} Credits</span>
                    </div>

                    <ul className="mt-6 space-y-3 flex-1">
                      {plan.features.map((feat, i) => (
                        <li key={i} className="flex items-center gap-3 text-sm text-muted-foreground">
                          <Check className="w-4 h-4 text-green-500" />
                          {feat}
                        </li>
                      ))}
                    </ul>

                    <button 
                      onClick={async () => {
                        // For MVP: Just show a message that payment integration is coming
                        // In production, this would integrate with payment gateway
                        alert(`Payment integration coming soon! This would add ${plan.credits.toLocaleString()} credits to your account.`);
                        // Refresh credits to show current balance
                        try {
                          await refreshUser();
                        } catch (err) {
                          console.error('Failed to refresh user:', err);
                        }
                        onClose();
                      }}
                      className={cn(
                        "mt-8 w-full py-3 rounded-xl font-medium transition-all",
                        plan.popular 
                          ? "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20" 
                          : "bg-white text-black hover:bg-gray-200"
                      )}
                    >
                      Choose {plan.name}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

