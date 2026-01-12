import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

interface StatusMessageProps {
    message: { type: 'success' | 'error' | 'info', text: string } | null;
    onClose: () => void;
}

export const StatusMessage = ({ message, onClose }: StatusMessageProps) => (
    <AnimatePresence>
        {message && (
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={`fixed top-8 left-1/2 -translate-x-1/2 z-[100] px-6 py-4 rounded-2xl shadow-2xl backdrop-blur-xl border flex items-center space-x-3 
                    ${message.type === 'success' ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400' :
                        message.type === 'error' ? 'bg-red-500/20 border-red-500/30 text-red-400' :
                            'bg-primary/20 border-primary/30 text-primary'}`}
            >
                {message.type === 'success' ? <CheckCircle2 size={20} /> :
                    message.type === 'error' ? <AlertCircle size={20} /> : <Info size={20} />}
                <span className="font-bold pr-2">{message.text}</span>
                <button
                    onClick={onClose}
                    className="p-1 hover:bg-white/10 rounded-full transition-colors ml-2 border-l border-white/10 pl-3"
                >
                    <X size={16} />
                </button>
            </motion.div>
        )}
    </AnimatePresence>
);
