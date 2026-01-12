import type { ReactNode } from 'react';

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    onClick?: () => void;
}

export const GlassCard = ({ children, className = "", onClick }: GlassCardProps) => (
    <div
        onClick={onClick}
        className={`glass-card p-6 rounded-2xl border border-white/5 bg-white/5 backdrop-blur-md transition-all duration-300 ${className}`}
    >
        {children}
    </div>
);
