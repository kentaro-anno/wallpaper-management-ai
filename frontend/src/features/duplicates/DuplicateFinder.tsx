import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Trash2, AlertCircle } from 'lucide-react';
import { API_BASE } from '../../constants';
import { GlassCard } from '../../components/common/GlassCard';

interface DuplicateFinderProps {
    scanning: boolean;
    progress: number;
    duplicateGroups: any[];
    targetFolder: string;
    workers: number;
    onRunScan: () => void;
    onDelete: (path: string) => void;
}

export const DuplicateFinder = ({
    scanning,
    progress,
    duplicateGroups,
    targetFolder,
    onRunScan,
    onDelete
}: DuplicateFinderProps) => {
    return (
        <motion.div
            key="duplicates"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="max-w-6xl mx-auto py-8 space-y-8"
        >
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-4xl font-bold">Duplicate Finder</h2>
                    <p className="text-white/40 text-sm font-mono mt-2">Target: {targetFolder}</p>
                </div>
                {!scanning && duplicateGroups.length > 0 && (
                    <div className="text-right">
                        <span className="text-2xl font-bold text-primary">{duplicateGroups.length}</span>
                        <span className="text-white/40 text-sm ml-2">GROUPS FOUND</span>
                    </div>
                )}
            </div>

            <AnimatePresence mode="wait">
                {scanning ? (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="glass-card p-12 text-center space-y-8 rounded-[3rem] border border-white/5"
                    >
                        <div className="w-full bg-white/5 rounded-full h-2 max-w-md mx-auto overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${progress}%` }}
                                className="h-full bg-primary"
                            />
                        </div>
                        <p className="animate-pulse text-primary font-bold">Scanning... {progress}%</p>
                    </motion.div>
                ) : duplicateGroups.length === 0 ? (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        key="empty"
                        className="glass-card p-16 text-center space-y-8 rounded-[3rem] border border-white/5"
                    >
                        <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center text-primary mx-auto">
                            <Copy size={48} />
                        </div>
                        <div className="space-y-4">
                            <h3 className="text-2xl font-bold">Ready to Scan</h3>
                            <p className="text-muted-foreground">
                                対象フォルダ内の重複画像を検索し、グループごとに表示します。<br />
                                3枚以上の重複もまとめて整理できます。
                            </p>
                        </div>
                        <button
                            onClick={onRunScan}
                            className="px-12 py-5 bg-gradient-to-r from-primary to-purple-600 rounded-[2rem] font-black text-lg shadow-xl shadow-primary/20 hover:scale-105 transition-all"
                        >
                            スキャン開始
                        </button>
                    </motion.div>
                ) : (
                    <motion.div
                        key="results"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="space-y-8"
                    >
                        {duplicateGroups.map((group, groupIndex) => (
                            <GlassCard key={group.hash} className="space-y-4 border-l-4 border-l-primary/50">
                                <div className="flex items-center space-x-3 text-sm font-bold text-white/40 pb-2 border-b border-white/5">
                                    <AlertCircle size={16} />
                                    <span>Group #{groupIndex + 1}</span>
                                    <span className="font-mono text-xs opacity-50">Hash: {group.hash.substring(0, 12)}...</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                    {group.images.map((img: any) => (
                                        <div key={img.path} className="relative group rounded-xl overflow-hidden border border-white/10 bg-black/40">
                                            <div className="aspect-square bg-[url('/checker.png')] bg-repeat">
                                                <img
                                                    src={`${API_BASE}/api/images/preview?path=${encodeURIComponent(img.path)}`}
                                                    alt={img.name}
                                                    className="w-full h-full object-contain"
                                                />
                                            </div>
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-4">
                                                <p className="text-[10px] text-white/70 truncate mb-3" title={img.name}>
                                                    {img.name}
                                                </p>
                                                <button
                                                    onClick={() => onDelete(img.path)}
                                                    className="w-full py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-xs font-bold flex items-center justify-center space-x-2 transition-colors"
                                                >
                                                    <Trash2 size={14} />
                                                    <span>削除</span>
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </GlassCard>
                        ))}

                        <div className="flex justify-center pt-8 pb-12">
                            <button
                                onClick={onRunScan}
                                className="px-8 py-3 bg-white/5 hover:bg-white/10 rounded-full text-sm font-bold transition-all"
                            >
                                再スキャン
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};
