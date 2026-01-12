import { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import axios from 'axios';
import {
    Home as HomeIcon,
    Copy as CopyIcon,
    CloudSun as CloudSunIcon,
    Settings as SettingsIcon,
    Image as ImageIcon,
} from 'lucide-react';

// Common Components
import { SidebarItem } from './components/common/SidebarItem';
import { StatusMessage } from './components/common/StatusMessage';

// Features
import { Home } from './features/home/Home';
import { DuplicateFinder } from './features/duplicates/DuplicateFinder';
import { SeasonClassifier } from './features/seasons/SeasonClassifier';
import { Settings } from './features/settings/Settings';

import { API_BASE } from './constants';

export default function App() {
    const [activeTab, setActiveTab] = useState('home');
    const [scanning, setScanning] = useState(false);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);

    // Settings State
    const [targetFolder, setTargetFolder] = useState(() => localStorage.getItem('targetFolder') || '');
    const [outputFolder, setOutputFolder] = useState(() => localStorage.getItem('outputFolder') || '');
    const [useCustomOutput, setUseCustomOutput] = useState(() => localStorage.getItem('useCustomOutput') === 'true');
    const [workers, setWorkers] = useState(() => parseInt(localStorage.getItem('workers') || '4'));
    const [maxCores, setMaxCores] = useState(4);
    const [deviceInfo, setDeviceInfo] = useState('CPU');

    // Duplicate State
    const [duplicatePairs, setDuplicatePairs] = useState<any[]>([]);
    const [currentPairIndex, setCurrentPairIndex] = useState(-1);

    // Season State
    const [classificationResults, setClassificationResults] = useState<any[]>([]);
    const [threshold, setThreshold] = useState(0.5);
    const [metric, setMetric] = useState('probability');

    // Persistence
    useEffect(() => {
        localStorage.setItem('targetFolder', targetFolder);
        localStorage.setItem('outputFolder', outputFolder);
        localStorage.setItem('useCustomOutput', String(useCustomOutput));
        localStorage.setItem('workers', String(workers));
    }, [targetFolder, outputFolder, useCustomOutput, workers]);

    useEffect(() => {
        fetchSystemInfo();
    }, []);

    const fetchSystemInfo = async () => {
        try {
            const res = await axios.get(`${API_BASE}/api/system/info`);
            setMaxCores(res.data.cpu_count);
            setDeviceInfo(res.data.device.toUpperCase());
            if (!localStorage.getItem('workers')) {
                setWorkers(Math.max(1, Math.floor(res.data.cpu_count * 0.75)));
            }
        } catch (error) {
            console.error('Failed to fetch system info:', error);
        }
    };

    const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
        setStatusMessage({ type, text });
    };

    // --- Actions ---

    const runDuplicateScan = async () => {
        setStatusMessage(null);
        setScanning(true);
        setProgress(0);
        try {
            const progressTimer = setInterval(() => {
                setProgress(prev => Math.min(prev + 5, 95));
            }, 500);

            const res = await axios.post(`${API_BASE}/api/duplicates/scan`, {
                folder: targetFolder,
                workers: workers
            });

            clearInterval(progressTimer);
            setProgress(100);
            await new Promise(r => setTimeout(r, 200));

            if (res.data.duplicates && res.data.duplicates.length > 0) {
                setDuplicatePairs(res.data.duplicates);
                setCurrentPairIndex(0);
                showMessage('success', `${res.data.duplicates.length} 個の重複ペアが見つかりました。`);
            } else {
                showMessage('info', `重複は見つかりませんでした。`);
            }
        } catch (error) {
            showMessage('error', 'スキャン中にエラーが発生しました。');
        } finally {
            setScanning(false);
        }
    };

    const runSeasonClassification = async () => {
        setStatusMessage(null);
        setScanning(true);
        setProgress(0);
        setClassificationResults([]);
        try {
            const progressTimer = setInterval(() => {
                setProgress(prev => Math.min(prev + 1, 99));
            }, 1000);

            const res = await axios.post(`${API_BASE}/api/classify/scan`, {
                folder: targetFolder,
                threshold: threshold,
                metric: metric,
                workers: workers
            }, { timeout: 600000 });

            clearInterval(progressTimer);
            setProgress(100);
            await new Promise(r => setTimeout(r, 200));

            if (res.data.results && res.data.results.length > 0) {
                setClassificationResults(res.data.results);
                showMessage('success', `AI 季節分類が完了しました。${res.data.total_processed} 枚の画像を解析しました。`);
            } else {
                showMessage('info', `解析対象の画像が見つからないか、処理がスキップされました。`);
            }
        } catch (error: any) {
            const detail = error.response?.data?.detail || error.message;
            showMessage('error', `分類中にエラーが発生しました: ${detail}`);
        } finally {
            setScanning(false);
        }
    };

    const handleExecuteClassification = async (mode: 'move' | 'copy') => {
        if (!classificationResults.length) return;
        const confirmMsg = `${classificationResults.length} 枚のファイルを整理して${mode === 'move' ? '移動' : 'コピー'}しますか？`;
        if (!window.confirm(confirmMsg)) return;

        setStatusMessage(null);
        setScanning(true);
        try {
            const res = await axios.post(`${API_BASE}/api/classify/execute`, {
                results: classificationResults,
                mode: mode,
                folder: targetFolder,
                output_folder: useCustomOutput ? outputFolder : targetFolder
            });
            showMessage('success', res.data.message);
            setClassificationResults([]);
        } catch (error) {
            showMessage('error', '実行中にエラーが発生しました。');
        } finally {
            setScanning(false);
        }
    };

    const handleBrowseTarget = async () => {
        try {
            const res = await axios.get(`${API_BASE}/api/settings/browse?initial_dir=${encodeURIComponent(targetFolder)}`);
            if (res.data.path) setTargetFolder(res.data.path);
        } catch (error) {
            showMessage('error', 'フォルダ選択ダイアログを開けませんでした。');
        }
    };

    const handleBrowseOutput = async () => {
        try {
            const res = await axios.get(`${API_BASE}/api/settings/browse?initial_dir=${encodeURIComponent(outputFolder || targetFolder)}`);
            if (res.data.path) {
                setOutputFolder(res.data.path);
                setUseCustomOutput(true);
            }
        } catch (error) {
            showMessage('error', 'フォルダ選択ダイアログを開けませんでした。');
        }
    };

    const handleDeleteDuplicate = async (side: 'left' | 'right') => {
        const pair = duplicatePairs[currentPairIndex];
        const pathToDelete = side === 'left' ? pair.left : pair.right;
        try {
            await axios.post(`${API_BASE}/api/duplicates/delete`, { path: pathToDelete });
            handleNextPair();
        } catch (error) {
            showMessage('error', '削除に失敗しました。');
        }
    };

    const handleNextPair = () => {
        if (currentPairIndex < duplicatePairs.length - 1) {
            setCurrentPairIndex(prev => prev + 1);
        } else {
            setCurrentPairIndex(-1);
            setDuplicatePairs([]);
            showMessage('success', '全ての重複処理が完了しました。');
        }
    };

    const handleManualReclassify = (index: number, newSeason: string) => {
        const newResults = [...classificationResults];
        const item = { ...newResults[index] };
        item.prediction = `a photo of ${newSeason}`;
        item.is_unknown = false;
        newResults[index] = item;
        setClassificationResults(newResults);
    };

    const metricLabels: any = {
        probability: { label: '確信度', desc: '最も可能性が高い季節の確率が低い場合に Unknown とします。' },
        margin: { label: '競合度', desc: '1位と2位の確率差が小さい（迷っている）場合に Unknown とします。' },
        entropy: { label: '迷い度', desc: '全体的に確率が分散している場合に Unknown とします。' }
    };

    return (
        <div className="flex h-screen bg-black text-white selection:bg-primary/30 font-inter">
            {/* Background Orbs */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/10 blur-[150px] rounded-full animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-600/10 blur-[150px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
            </div>

            {/* Sidebar */}
            <aside className="w-72 border-r border-white/10 bg-black/40 backdrop-blur-3xl z-10 flex flex-col p-8 space-y-10">
                <div className="flex items-center space-x-4 px-2">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
                        <ImageIcon className="text-white" size={26} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold tracking-tight leading-none">Wallpaper</h1>
                        <span className="text-primary text-xs font-semibold tracking-widest uppercase">Management</span>
                    </div>
                </div>

                <nav className="flex-1 space-y-3">
                    <SidebarItem icon={HomeIcon} label="ホーム" active={activeTab === 'home'} onClick={() => setActiveTab('home')} />
                    <SidebarItem icon={CopyIcon} label="重複削除" active={activeTab === 'duplicates'} onClick={() => setActiveTab('duplicates')} />
                    <SidebarItem icon={CloudSunIcon} label="季節分類" active={activeTab === 'seasons'} onClick={() => setActiveTab('seasons')} />
                </nav>

                <div className="pt-8 border-t border-white/10">
                    <SidebarItem icon={SettingsIcon} label="設定" active={activeTab === 'settings'} onClick={() => setActiveTab('settings')} />
                </div>
            </aside>

            {/* Status Messages */}
            <StatusMessage message={statusMessage} onClose={() => setStatusMessage(null)} />

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto z-10 p-12">
                <AnimatePresence mode="wait">
                    {activeTab === 'home' && (
                        <Home onTabChange={setActiveTab} />
                    )}

                    {activeTab === 'duplicates' && (
                        <DuplicateFinder
                            scanning={scanning}
                            progress={progress}
                            duplicatePairs={duplicatePairs}
                            currentPairIndex={currentPairIndex}
                            targetFolder={targetFolder}
                            workers={workers}
                            onRunScan={runDuplicateScan}
                            onDelete={handleDeleteDuplicate}
                            onNextPair={handleNextPair}
                            onResetIndex={() => setCurrentPairIndex(-1)}
                        />
                    )}

                    {activeTab === 'seasons' && (
                        <SeasonClassifier
                            scanning={scanning}
                            progress={progress}
                            classificationResults={classificationResults}
                            threshold={threshold}
                            metric={metric}
                            metricLabels={metricLabels}
                            onRunScan={runSeasonClassification}
                            onExecute={handleExecuteClassification}
                            onReclassify={handleManualReclassify}
                            onThresholdChange={setThreshold}
                            onMetricChange={setMetric}
                        />
                    )}

                    {activeTab === 'settings' && (
                        <Settings
                            targetFolder={targetFolder}
                            outputFolder={outputFolder}
                            useCustomOutput={useCustomOutput}
                            workers={workers}
                            maxCores={maxCores}
                            deviceInfo={deviceInfo}
                            onTargetFolderChange={setTargetFolder}
                            onOutputFolderChange={setOutputFolder}
                            onUseCustomOutputChange={setUseCustomOutput}
                            onWorkersChange={setWorkers}
                            onBrowseTarget={handleBrowseTarget}
                            onBrowseOutput={handleBrowseOutput}
                        />
                    )}
                </AnimatePresence>
            </main>
        </div>
    );
}
