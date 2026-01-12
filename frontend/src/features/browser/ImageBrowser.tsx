import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE } from '../../constants';
import { ChevronLeft, ChevronRight, X, Loader2, Folder, Search, ArrowUpDown, ArrowDownUp } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

interface DirectoryItem {
    name: string;
    path: string;
}

interface ImageItem {
    filename: string;
    path: string;
    size: number;
    mtime: number;
}

interface ImageBrowserProps {
    targetFolder: string;
}

export const ImageBrowser = ({ targetFolder }: ImageBrowserProps) => {
    // State
    const [images, setImages] = useState<ImageItem[]>([]);
    const [directories, setDirectories] = useState<DirectoryItem[]>([]);
    const [currentPath, setCurrentPath] = useState('');

    // Pagination & Loading
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Filter & Sort
    const [searchQuery, setSearchQuery] = useState('');
    const [sort, setSort] = useState('name');
    const [order, setOrder] = useState('asc');

    // Lightbox State
    const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

    const limit = 50;

    // Initial load & Path change
    useEffect(() => {
        if (targetFolder) {
            // If currentPath is empty or not set yet, use targetFolder
            // But we want to respect navigation. 
            // If targetFolder changes in settings, we should reset to it.
            // For now, let's sync if currentPath is empty or if we detect a "root" change.
            // Simplest: If component mounts or targetFolder changes, start there.
            setCurrentPath(targetFolder);
        }
    }, [targetFolder]);

    // Reset list when parameters change
    useEffect(() => {
        if (currentPath) {
            setImages([]);
            setPage(1);
            setHasMore(true);
            fetchImages(1, true);
        }
    }, [currentPath, sort, order, searchQuery]);

    const fetchImages = async (pageNum: number, reset: boolean = false) => {
        if (!currentPath) return;
        setLoading(true);
        setError(null);
        try {
            const res = await axios.get(`${API_BASE}/api/browser/images`, {
                params: {
                    folder: currentPath,
                    page: pageNum,
                    limit,
                    sort,
                    order,
                    search: searchQuery || undefined
                }
            });

            setDirectories(res.data.directories || []);
            const newItems = res.data.items;
            const total = res.data.total;

            if (reset) {
                setImages(newItems);
            } else {
                setImages(prev => [...prev, ...newItems]);
            }

            setHasMore(images.length + newItems.length < total && newItems.length > 0);
        } catch (err: any) {
            console.error(err);
            setError('画像の読み込みに失敗しました。');
        } finally {
            setLoading(false);
        }
    };

    const loadMore = () => {
        if (!loading && hasMore) {
            const nextPage = page + 1;
            setPage(nextPage);
            fetchImages(nextPage);
        }
    };

    // Keyboard navigation for lightbox
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (lightboxIndex === null) return;

            if (e.key === 'Escape') setLightboxIndex(null);
            if (e.key === 'ArrowLeft') navigateLightbox(-1);
            if (e.key === 'ArrowRight') navigateLightbox(1);
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [lightboxIndex, images.length]);

    const navigateLightbox = (direction: number) => {
        if (lightboxIndex === null) return;
        const newIndex = lightboxIndex + direction;
        if (newIndex >= 0 && newIndex < images.length) {
            setLightboxIndex(newIndex);
        }
    };

    const handleNavigateFolder = (path: string) => {
        setCurrentPath(path);
        setSearchQuery(''); // Reset search on nav
    };

    const handleNavigateUp = () => {
        if (!currentPath) return;
        // Simple string manipulation for parent path
        // Adjust for Windows paths if needed, but assuming '/' or '\' separator
        // Sending backend request for parent logic might be safer but string manipulating for now
        const separator = currentPath.includes('\\') ? '\\' : '/';
        const parts = currentPath.split(separator);
        parts.pop(); // Remove current folder
        // If empty (root), keep it basic or stop? 
        // For simplicity, just join. If only drive letter left (e.g. "C:"), backend handles it.
        const parentPath = parts.join(separator) || '/';
        setCurrentPath(parentPath);
        setSearchQuery('');
    };

    const currentImage = lightboxIndex !== null ? images[lightboxIndex] : null;

    return (
        <div className="h-full flex flex-col">
            <header className="mb-6 flex flex-col gap-4">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight">Image Browser</h2>
                    <div className="flex items-center text-white/60 text-sm mt-1 overflow-hidden">
                        <button
                            onClick={handleNavigateUp}
                            disabled={currentPath === targetFolder}
                            className="mr-2 p-1 hover:bg-white/10 rounded disabled:opacity-30 transition-colors"
                            title="Go Up"
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <span className="truncate font-mono" title={currentPath}>
                            {currentPath ? currentPath : 'ターゲットフォルダが設定されていません'}
                        </span>
                    </div>
                </div>

                {/* Controls */}
                <div className="flex flex-wrap gap-4 items-center bg-white/5 p-3 rounded-xl border border-white/10">
                    {/* Search */}
                    <div className="relative flex-1 min-w-[200px]">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" size={16} />
                        <input
                            type="text"
                            placeholder="ファイル名で検索..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-black/20 border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>

                    {/* Sort */}
                    <div className="flex items-center space-x-2">
                        <select
                            value={sort}
                            onChange={(e) => setSort(e.target.value)}
                            className="bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-primary/50 cursor-pointer appearance-none"
                        >
                            <option value="name">名前順</option>
                            <option value="date">日付順</option>
                            <option value="size">サイズ順</option>
                        </select>
                        <button
                            onClick={() => setOrder(order === 'asc' ? 'desc' : 'asc')}
                            className="p-1.5 bg-black/20 border border-white/10 rounded-lg hover:bg-white/10 transition-colors"
                            title={order === 'asc' ? '昇順' : '降順'}
                        >
                            {order === 'asc' ? <ArrowDownUp size={16} /> : <ArrowUpDown size={16} />}
                        </button>
                    </div>
                </div>
            </header>

            {error && (
                <div className="bg-red-500/10 border border-red-500 text-red-500 rounded-lg p-4 mb-4">
                    {error}
                </div>
            )}

            <div className="flex-1 overflow-y-auto pr-2 pb-20">
                {!targetFolder ? (
                    <div className="flex items-center justify-center h-64 text-white/40">
                        設定画面でターゲットフォルダを指定してください。
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                            {/* Directories */}
                            {!searchQuery && directories.map((dir) => (
                                <div
                                    key={dir.path}
                                    className="aspect-square bg-white/5 rounded-xl border border-white/10 flex flex-col items-center justify-center cursor-pointer hover:bg-white/10 hover:border-primary/50 transition-all group"
                                    onClick={() => handleNavigateFolder(dir.path)}
                                >
                                    <Folder className="text-yellow-500/70 mb-2 group-hover:scale-110 transition-transform" size={48} />
                                    <span className="text-xs text-center px-2 truncate w-full text-white/70 group-hover:text-white">
                                        {dir.name}
                                    </span>
                                </div>
                            ))}

                            {/* Images */}
                            {images.map((img, idx) => (
                                <div
                                    key={`${img.filename}-${idx}`}
                                    className="aspect-square bg-white/5 rounded-xl overflow-hidden cursor-pointer hover:ring-2 hover:ring-primary transition-all group relative"
                                    onClick={() => setLightboxIndex(idx)}
                                >
                                    <img
                                        src={`${API_BASE}/api/browser/image?path=${encodeURIComponent(img.path)}`}
                                        alt={img.filename}
                                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                        loading="lazy"
                                    />
                                    <div className="absolute bottom-0 left-0 right-0 bg-black/60 p-2 text-xs truncate opacity-0 group-hover:opacity-100 transition-opacity flex flex-col">
                                        <span title={img.filename}>{img.filename}</span>
                                        {/* <span className="text-[10px] text-white/60">{new Date(img.mtime * 1000).toLocaleDateString()}</span> */}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {loading && (
                            <div className="flex justify-center py-8">
                                <Loader2 className="animate-spin text-primary" />
                            </div>
                        )}

                        {!loading && hasMore && images.length > 0 && (
                            <div className="flex justify-center py-8">
                                <button
                                    onClick={loadMore}
                                    className="px-6 py-2 bg-white/10 hover:bg-white/20 rounded-full text-sm font-medium transition-colors"
                                >
                                    もっと読み込む
                                </button>
                            </div>
                        )}

                        {!loading && !hasMore && images.length > 0 && (
                            <div className="text-center py-8 text-white/40 text-sm">
                                全ての画像を表示しました
                            </div>
                        )}

                        {!loading && images.length === 0 && directories.length === 0 && (
                            <div className="text-center py-16 text-white/40">
                                項目が見つかりません
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Lightbox Modal */}
            <AnimatePresence>
                {currentImage && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 backdrop-blur-sm p-4"
                        onClick={() => setLightboxIndex(null)}
                    >
                        {/* Close Button */}
                        <button
                            className="absolute top-4 right-4 p-2 text-white/60 hover:text-white bg-white/10 hover:bg-white/20 rounded-full transition-colors z-50"
                            onClick={() => setLightboxIndex(null)}
                        >
                            <X size={24} />
                        </button>

                        {/* Image Container */}
                        <div
                            className="relative max-w-full max-h-full flex items-center justify-center"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <img
                                src={`${API_BASE}/api/browser/image?path=${encodeURIComponent(currentImage.path)}`}
                                alt={currentImage.filename}
                                className="max-w-full max-h-[90vh] object-contain shadow-2xl rounded-sm"
                            />

                            <div className="absolute bottom-[-3rem] left-0 right-0 text-center text-white/80 text-sm font-mono">
                                {currentImage.filename} ({lightboxIndex !== null ? lightboxIndex + 1 : 0} / {images.length})
                            </div>
                        </div>

                        {/* Navigation Buttons */}
                        <button
                            className={`absolute left-4 p-4 text-white/40 hover:text-white transition-colors ${lightboxIndex === 0 ? 'opacity-0 pointer-events-none' : ''}`}
                            onClick={(e) => { e.stopPropagation(); navigateLightbox(-1); }}
                        >
                            <ChevronLeft size={48} />
                        </button>

                        <button
                            className={`absolute right-4 p-4 text-white/40 hover:text-white transition-colors ${lightboxIndex === images.length - 1 ? 'opacity-0 pointer-events-none' : ''}`}
                            onClick={(e) => { e.stopPropagation(); navigateLightbox(1); }}
                        >
                            <ChevronRight size={48} />
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
