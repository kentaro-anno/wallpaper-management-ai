import { motion } from 'framer-motion';
import { Copy, X, CheckCircle2 } from 'lucide-react';
import { API_BASE } from '../../constants';

interface DuplicateFinderProps {
    scanning: boolean;
    progress: number;
    duplicatePairs: any[];
    currentPairIndex: number;
    targetFolder: string;
    workers: number;
    onRunScan: () => void;
    onDelete: (side: 'left' | 'right') => void;
    onNextPair: () => void;
    onResetIndex: () => void;
}

export const DuplicateFinder = ({
    scanning,
    progress,
    duplicatePairs,
    currentPairIndex,
    targetFolder,
    onRunScan,
    onDelete,
    onNextPair,
    onResetIndex
}: DuplicateFinderProps) => {
    // スキャン完了後（duplicatePairsがある）かつ、まだ確認を開始していない（indexが-1）状態
    const isScanFinished = !scanning && duplicatePairs.length > 0 && currentPairIndex === -1;

    return (
        <motion.div
            key="duplicates"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="max-w-4xl mx-auto py-12"
        >
            <div className="text-center space-y-8">
                <h2 className="text-4xl font-bold">Duplicate Finder</h2>
                <div className="glass-card p-16 rounded-[3rem] space-y-10 border border-white/5">
                    {!scanning ? (
                        currentPairIndex === -1 ? (
                            <div className="space-y-10">
                                {isScanFinished ? (
                                    <div className="w-24 h-24 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 mx-auto">
                                        <CheckCircle2 size={48} />
                                    </div>
                                ) : (
                                    <div className="w-24 h-24 rounded-full bg-primary/10 flex items-center justify-center text-primary mx-auto">
                                        <Copy size={48} />
                                    </div>
                                )}

                                <div className="space-y-4">
                                    <h3 className="text-2xl font-bold">
                                        {isScanFinished ? 'スキャン完了' : 'スキャン準備完了'}
                                    </h3>
                                    <p className="text-muted-foreground">
                                        {isScanFinished
                                            ? `${duplicatePairs.length} 個の重複ペアが見つかりました。`
                                            : `対象: ${targetFolder}`}
                                    </p>
                                </div>

                                <div className="flex flex-col items-center space-y-4">
                                    {isScanFinished ? (
                                        <>
                                            <button
                                                onClick={() => onNextPair()} // Start verification by going to index 0
                                                className="px-12 py-5 bg-gradient-to-r from-emerald-600 to-teal-500 rounded-[2rem] font-black text-lg shadow-xl shadow-emerald-500/20 hover:scale-105 transition-all w-full max-w-xs"
                                            >
                                                重複を確認する
                                            </button>
                                            <button
                                                onClick={onRunScan}
                                                className="text-sm text-white/40 hover:text-white transition-colors"
                                            >
                                                再スキャンする
                                            </button>
                                        </>
                                    ) : (
                                        <button
                                            onClick={onRunScan}
                                            className="px-12 py-5 bg-gradient-to-r from-primary to-purple-600 rounded-[2rem] font-black text-lg shadow-xl shadow-primary/20 hover:scale-105 transition-all w-full max-w-xs"
                                        >
                                            スキャン開始
                                        </button>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-8 w-full text-left">
                                <div className="flex justify-between items-center bg-white/5 p-4 rounded-2xl">
                                    <span className="font-bold text-primary">
                                        Pair {currentPairIndex + 1} / {duplicatePairs.length}
                                    </span>
                                    <button
                                        onClick={onResetIndex}
                                        className="text-muted-foreground hover:text-white"
                                    >
                                        <X size={20} />
                                    </button>
                                </div>
                                <div className="grid grid-cols-2 gap-6 h-[400px]">
                                    {[
                                        { side: 'left' as const, path: duplicatePairs[currentPairIndex].left, name: duplicatePairs[currentPairIndex].left_name },
                                        { side: 'right' as const, path: duplicatePairs[currentPairIndex].right, name: duplicatePairs[currentPairIndex].right_name }
                                    ].map((item) => (
                                        <div key={item.side} className="relative group rounded-2xl overflow-hidden border border-white/10 bg-black/40 flex flex-col">
                                            <div className="flex-1 overflow-hidden">
                                                <img
                                                    src={`${API_BASE}/api/images/preview?path=${encodeURIComponent(item.path)}`}
                                                    alt=""
                                                    className="w-full h-full object-contain"
                                                />
                                            </div>
                                            <div className="p-4 bg-black/60">
                                                <p className="text-[10px] truncate mb-2 text-white/40" title={item.name}>
                                                    {item.name}
                                                </p>
                                                <button
                                                    onClick={() => onDelete(item.side)}
                                                    className="w-full py-2 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white rounded-lg transition-all text-xs font-bold"
                                                >
                                                    削除する
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="flex justify-center pt-4">
                                    <button
                                        onClick={onNextPair}
                                        className="px-8 py-3 bg-white/5 hover:bg-white/10 rounded-xl font-bold transition-all"
                                    >
                                        スキップして次へ
                                    </button>
                                </div>
                            </div>
                        )
                    ) : (
                        <div className="space-y-10 py-12">
                            <div className="w-full bg-white/5 rounded-full h-2 max-w-md mx-auto overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${progress}%` }}
                                    className="h-full bg-primary"
                                />
                            </div>
                            <p className="animate-pulse text-primary font-bold">Scanning... {progress}%</p>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};
