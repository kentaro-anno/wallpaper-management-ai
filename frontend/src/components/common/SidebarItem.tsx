import type { LucideIcon } from 'lucide-react';

interface SidebarItemProps {
    icon: LucideIcon;
    label: string;
    active: boolean;
    onClick: () => void;
}

export const SidebarItem = ({ icon: Icon, label, active, onClick }: SidebarItemProps) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300 ${active
            ? 'bg-primary/20 text-primary border border-primary/20'
            : 'text-muted-foreground hover:bg-white/5 hover:text-foreground'
            }`}
    >
        <Icon size={20} />
        <span className="font-medium">{label}</span>
    </button>
);
