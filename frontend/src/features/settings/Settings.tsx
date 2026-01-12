import { motion } from 'framer-motion';
import { FolderOpen, Cpu } from 'lucide-react';
import { GlassCard } from '../../components/common/GlassCard';

interface SettingsProps {
    targetFolder: string;
    outputFolder: string;
    useCustomOutput: boolean;
    workers: number;
    maxCores: number;
    deviceInfo: string;
    onTargetFolderChange: (value: string) => void;
    onOutputFolderChange: (value: string) => void;
    onUseCustomOutputChange: (value: boolean) => void;
    onWorkersChange: (value: number) => void;
    onBrowseTarget: () => void;
    onBrowseOutput: () => void;
}

export const Settings = ({
    targetFolder,
    outputFolder,
    useCustomOutput,
    workers,
    maxCores,
    deviceInfo,
    onTargetFolderChange,
    onOutputFolderChange,
    onUseCustomOutputChange,
    onWorkersChange,
    onBrowseTarget,
    onBrowseOutput
}: SettingsProps) => {
    return (
        <motion.div
            key="settings"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-4xl mx-auto space-y-12 py-8"
        >
            <h2 className="text-4xl font-bold">Settings</h2>
            <GlassCard className="space-y-6">
                <div className="space-y-3">
                    <label className="text-sm font-bold text-white/50 flex items-center">
                        <FolderOpen size={16} className="mr-2" /> 対象フォルダパス
                    </label>
                    <div className="flex space-x-3">
                        <input
                            type="text"
                            value={targetFolder}
                            onChange={(e) => onTargetFolderChange(e.target.value)}
                            className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-mono text-sm"
                        />
                        <button
                            onClick={onBrowseTarget}
                            className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all font-bold"
                        >
                            参照
                        </button>
                    </div>
                </div>

                <div className="space-y-3 pt-6 border-t border-white/5">
                    <label className="text-sm font-bold text-white/50 flex items-center justify-between">
                        <div className="flex items-center">
                            <FolderOpen size={16} className="mr-2 text-purple-400" /> 分類結果の出力先
                        </div>
                        <div className="flex bg-black/60 p-1 rounded-lg border border-white/10 scale-90">
                            <button
                                onClick={() => onUseCustomOutputChange(false)}
                                className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${!useCustomOutput ? 'bg-purple-600 text-white shadow-lg' : 'text-white/40 hover:text-white'
                                    }`}
                            >
                                対象と同じ
                            </button>
                            <button
                                onClick={() => onUseCustomOutputChange(true)}
                                className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${useCustomOutput ? 'bg-purple-600 text-white shadow-lg' : 'text-white/40 hover:text-white'
                                    }`}
                            >
                                別フォルダ
                            </button>
                        </div>
                    </label>

                    {useCustomOutput ? (
                        <div className="flex space-x-3 animate-in fade-in slide-in-from-top-2 duration-300">
                            <input
                                type="text"
                                value={outputFolder}
                                placeholder="出力先フォルダを指定してください"
                                onChange={(e) => onOutputFolderChange(e.target.value)}
                                className="flex-1 bg-black/40 border border-purple-500/30 rounded-xl px-4 py-3 font-mono text-sm focus:border-purple-500/60 outline-none"
                            />
                            <button
                                onClick={onBrowseOutput}
                                className="px-6 py-3 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-xl hover:bg-purple-500/20 transition-all font-bold"
                            >
                                参照
                            </button>
                        </div>
                    ) : (
                        <div className="p-4 bg-white/5 rounded-xl border border-white/5 italic text-white/30 text-xs">
                            整理を実行すると、対象フォルダ内に spring, summer 等のフォルダを作成します。
                        </div>
                    )}
                </div>

                <div className="space-y-4 pt-6 border-t border-white/5">
                    <div className="flex justify-between items-center text-sm font-bold text-white/50">
                        <div className="flex items-center">
                            <Cpu size={16} className="mr-2 text-primary" /> 並列作業数 (Workers)
                        </div>
                        <div className="text-primary">
                            {workers} <span className="text-[10px] text-white/30 ml-1">/ {maxCores}</span>
                        </div>
                    </div>
                    <input
                        type="range"
                        min="1"
                        max={maxCores}
                        value={workers}
                        onChange={(e) => onWorkersChange(parseInt(e.target.value))}
                        className="w-full accent-primary h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="text-[10px] text-white/30 flex justify-between">
                        <span>最小負荷 (1)</span>
                        <span className="text-primary/60">
                            推奨: {Math.max(1, Math.floor(maxCores * 0.75))}
                        </span>
                        <span>最大負荷 ({maxCores})</span>
                    </div>
                </div>
            </GlassCard>

            <GlassCard className="grid grid-cols-2 gap-8">
                <div className="space-y-2">
                    <h4 className="text-xs font-bold text-white/40 uppercase">CLIP Model</h4>
                    <p className="text-sm font-mono">clip-vit-base-patch32</p>
                    <div className="flex items-center space-x-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[10px] text-emerald-400 font-bold uppercase">Ready</span>
                    </div>
                </div>
                <div className="space-y-2 border-l border-white/5 pl-8">
                    <h4 className="text-xs font-bold text-white/40 uppercase">Device</h4>
                    <p className="text-sm font-mono">{deviceInfo}</p>
                    <div className="text-[10px] font-mono text-white/20 uppercase tracking-widest">Optimized</div>
                </div>
            </GlassCard>
        </motion.div>
    );
};
