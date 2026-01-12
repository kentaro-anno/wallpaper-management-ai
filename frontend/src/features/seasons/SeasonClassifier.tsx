import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CloudSun, Loader2, CheckCircle2 } from 'lucide-react';
import { API_BASE } from '../../constants';

interface SeasonClassifierProps {
    scanning: boolean;
    progress: number;
    classificationResults: any[];
    threshold: number;
    metric: string;
    metricLabels: any;
    onRunScan: () => void;
    onExecute: (mode: 'move' | 'copy') => Promise<string>;
    onClearResults: () => void;
    onReclassify: (index: number, newSeason: string) => void;
    onThresholdChange: (value: number) => void;
    onMetricChange: (value: string) => void;
}

export const SeasonClassifier = ({
    scanning,
    progress,
    classificationResults,
    threshold,
    metric,
    metricLabels,
    onRunScan,
    onExecute,
    onClearResults,
    onReclassify,
    onThresholdChange,
    onMetricChange
}: SeasonClassifierProps) => {
    const [executionState, setExecutionState] = useState<{ mode: 'move' | 'copy' | null; status: 'idle' | 'executing' | 'success' }>({ mode: null, status: 'idle' });
    const [successMessage, setSuccessMessage] = useState('');

    const handleExecute = async (mode: 'move' | 'copy') => {
        setExecutionState({ mode, status: 'executing' });
        try {
            const msg = await onExecute(mode);
            setSuccessMessage(msg);
            setExecutionState({ mode, status: 'success' });

            // Wait 3 seconds then clear results to return to initial screen
            setTimeout(() => {
                setExecutionState({ mode: null, status: 'idle' });
                setSuccessMessage('');
                onClearResults();
            }, 3000);
        } catch (error) {
            setExecutionState({ mode: null, status: 'idle' });
        }
    };

    return (
        <motion.div
            key="seasons"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-4xl mx-auto py-12"
        >
            <div className="text-center space-y-8">
                <h2 className="text-4xl font-bold">AI Season Classifier</h2>
                <div className="glass-card p-16 rounded-[3rem] border border-purple-500/20 space-y-10">
                    {!scanning ? (
                        <div className="space-y-10 w-full">
                            <div className="w-24 h-24 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400 mx-auto">
                                <CloudSun size={48} />
                            </div>
                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <h3 className="text-2xl font-bold">AI 分類の準備</h3>
                                    <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                                        {Object.keys(metricLabels).map((m) => (
                                            <button
                                                key={m}
                                                onClick={() => onMetricChange(m)}
                                                className={`p-3 rounded-xl border text-xs font-bold transition-all ${metric === m
                                                    ? 'bg-purple-600 border-purple-400 text-white shadow-lg shadow-purple-600/20'
                                                    : 'bg-white/5 border-white/10 text-white/40 hover:bg-white/10'
                                                    }`}
                                            >
                                                {metricLabels[m].label}
                                            </button>
                                        ))}
                                    </div>
                                    <p className="text-[10px] text-white/40 italic">{metricLabels[metric].desc}</p>
                                </div>

                                <div className="max-w-xs mx-auto space-y-3 bg-white/5 p-4 rounded-2xl border border-white/10 text-left">
                                    <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider">
                                        <span>{metricLabels[metric].label}の閾値</span>
                                        <span className="text-purple-400">{Math.round(threshold * 100)}%</span>
                                    </div>
                                    <input
                                        type="range"
                                        min="0.0"
                                        max="1.0"
                                        step="0.01"
                                        value={threshold}
                                        onChange={(e) => onThresholdChange(parseFloat(e.target.value))}
                                        className="w-full accent-purple-500 cursor-pointer"
                                    />
                                </div>
                            </div>

                            <button
                                onClick={onRunScan}
                                className="px-12 py-5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-[2rem] font-black text-lg shadow-xl shadow-purple-500/20 hover:scale-105 transition-all"
                            >
                                解析を実行
                            </button>

                            {classificationResults.length > 0 && (
                                <div className="mt-12 text-left space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="flex items-center justify-between border-b border-white/10 pb-4 text-left">
                                        <h4 className="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-indigo-400">
                                            Analysis Summary
                                        </h4>
                                        <div className="flex space-x-2">
                                            {['Spring', 'Summer', 'Autumn', 'Winter', 'Unknown'].map((s) => {
                                                const count = s === 'Unknown'
                                                    ? classificationResults.filter((r) => r.is_unknown).length
                                                    : classificationResults.filter((r) => !r.is_unknown && r.prediction.toLowerCase().includes(s.toLowerCase())).length;
                                                return (
                                                    <div key={s} className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-bold border border-white/10">
                                                        {s}: {count}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>

                                    <div className="flex space-x-4 bg-purple-500/5 p-6 rounded-3xl border border-purple-500/20 justify-center">
                                        <div className="flex-1">
                                            <p className="text-sm font-bold mb-1">整理の実行</p>
                                            <p className="text-xs text-muted-foreground">結果フォルダへ移動/コピーします。</p>
                                        </div>

                                        {/* Copy Button */}
                                        <button
                                            onClick={() => handleExecute('copy')}
                                            disabled={executionState.status !== 'idle'}
                                            className={`px-6 py-2 rounded-xl text-sm font-bold border transition-all duration-300 min-w-[120px] flex items-center justify-center space-x-2
                                                ${executionState.mode === 'copy' && executionState.status === 'success'
                                                    ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                                                    : 'bg-white/5 hover:bg-white/10 border-white/10'}`}
                                        >
                                            {executionState.mode === 'copy' ? (
                                                executionState.status === 'executing' ? <Loader2 className="animate-spin" size={16} /> :
                                                    executionState.status === 'success' ? <><CheckCircle2 size={16} /><span>完了</span></> :
                                                        <span>コピー整理</span>
                                            ) : (
                                                <span>コピー整理</span>
                                            )}
                                        </button>

                                        {/* Move Button */}
                                        <button
                                            onClick={() => handleExecute('move')}
                                            disabled={executionState.status !== 'idle'}
                                            className={`px-6 py-2 rounded-xl text-sm font-bold shadow-lg transition-all duration-300 min-w-[120px] flex items-center justify-center space-x-2
                                                ${executionState.mode === 'move' && executionState.status === 'success'
                                                    ? 'bg-emerald-500 border border-emerald-400 text-white shadow-emerald-500/20'
                                                    : 'bg-purple-600 hover:bg-purple-500 shadow-purple-600/20'}`}
                                        >
                                            {executionState.mode === 'move' ? (
                                                executionState.status === 'executing' ? <Loader2 className="animate-spin" size={16} /> :
                                                    executionState.status === 'success' ? <><CheckCircle2 size={16} /><span>完了</span></> :
                                                        <span>移動整理</span>
                                            ) : (
                                                <span>移動整理</span>
                                            )}
                                        </button>
                                    </div>

                                    <AnimatePresence>
                                        {successMessage && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                className="text-center text-emerald-400 text-sm font-bold"
                                            >
                                                {successMessage}
                                            </motion.div>
                                        )}
                                    </AnimatePresence>

                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                        {classificationResults.map((r, i) => {
                                            const season = r.is_unknown ? 'unknown' : r.prediction.split(' ').pop().toLowerCase();
                                            return (
                                                <div key={i} className="group relative">
                                                    <div
                                                        className={`relative aspect-video rounded-xl border overflow-hidden transition-all ${r.is_unknown ? 'border-amber-500/50 bg-amber-500/5 shadow-lg shadow-amber-500/10' : 'border-purple-500/30'
                                                            }`}
                                                    >
                                                        <img
                                                            src={`${API_BASE}/api/images/preview?path=${encodeURIComponent(r.path)}`}
                                                            className={`w-full h-full object-cover ${r.is_unknown ? 'sepia-[0.3] opacity-70' : ''}`}
                                                            alt=""
                                                        />

                                                        {r.is_unknown && (
                                                            <div className="absolute top-2 right-2 bg-amber-500 text-black text-[8px] font-black px-1.5 py-0.5 rounded shadow-lg animate-bounce">
                                                                要確認
                                                            </div>
                                                        )}

                                                        <div className="absolute inset-x-0 bottom-0 p-2 bg-black/60 flex justify-between items-center">
                                                            <span className="text-[9px] font-bold uppercase">{season}</span>
                                                            <span className="text-[9px] text-white/40">
                                                                {(() => {
                                                                    const lastWord = r.prediction.split(' ').pop();
                                                                    const capitalized = lastWord.charAt(0).toUpperCase() + lastWord.slice(1);
                                                                    const prob = r.probs?.[capitalized] || r.probs?.[lastWord] || 0;
                                                                    return Math.round(prob * 100);
                                                                })()}%
                                                            </span>
                                                        </div>

                                                        {/* Hover Overlay for Reclassification */}
                                                        <div className="absolute inset-0 bg-black/90 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center p-2 space-y-2">
                                                            <p className="text-[10px] font-black text-amber-400 mb-1 tracking-tighter">
                                                                季節を選択して確定
                                                            </p>
                                                            <div className="grid grid-cols-2 gap-1.5 w-full">
                                                                {['spring', 'summer', 'autumn', 'winter'].map((s) => (
                                                                    <button
                                                                        key={s}
                                                                        onClick={() => onReclassify(i, s)}
                                                                        className="py-1.5 px-1 bg-white/5 hover:bg-purple-600 border border-white/10 rounded text-[9px] font-black transition-all transform hover:scale-105 active:scale-95"
                                                                    >
                                                                        {s.toUpperCase()}
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-10 py-12">
                            <div className="w-full bg-white/5 rounded-full h-2 max-w-md mx-auto overflow-hidden">
                                <motion.div animate={{ width: `${progress}%` }} className="h-full bg-purple-500" />
                            </div>
                            <p className="animate-pulse text-purple-400 font-bold">Classifying... {progress}%</p>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};
