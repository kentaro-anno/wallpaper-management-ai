import { motion } from 'framer-motion';
import { Copy, CloudSun, ChevronRight } from 'lucide-react';
import { GlassCard } from '../../components/common/GlassCard';

interface HomeProps {
    onTabChange: (tab: string) => void;
}

export const Home = ({ onTabChange }: HomeProps) => {
    return (
        <motion.div
            key="home"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -30 }}
            className="max-w-6xl mx-auto space-y-12 h-full flex flex-col justify-center pb-24"
        >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-10 max-w-5xl mx-auto w-full">
                <GlassCard
                    onClick={() => onTabChange('duplicates')}
                    className="min-h-[350px] flex flex-col justify-end group cursor-pointer hover:border-primary/50 relative overflow-hidden"
                >
                    <div className="absolute top-[-20px] right-[-20px] p-8 text-white/5 group-hover:text-primary/10 transition-all duration-700">
                        <Copy size={240} />
                    </div>
                    <div className="relative z-10">
                        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
                            <Copy size={24} />
                        </div>
                        <h3 className="text-4xl font-black mb-4 flex items-center">
                            Duplicate Finder <ChevronRight className="ml-3 group-hover:translate-x-2 transition-transform text-primary" />
                        </h3>
                        <p className="text-muted-foreground text-lg leading-relaxed max-w-sm">
                            視覚的に似ている画像を特定し、無駄なストレージ消費を抑えます。
                        </p>
                    </div>
                </GlassCard>

                <GlassCard
                    onClick={() => onTabChange('seasons')}
                    className="min-h-[350px] flex flex-col justify-end group cursor-pointer hover:border-purple-500/50 relative overflow-hidden"
                >
                    <div className="absolute top-[-20px] right-[-20px] p-8 text-white/5 group-hover:text-purple-500/10 transition-all duration-700">
                        <CloudSun size={240} />
                    </div>
                    <div className="relative z-10">
                        <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-500 mb-6 group-hover:scale-110 transition-transform">
                            <CloudSun size={24} />
                        </div>
                        <h3 className="text-4xl font-black mb-4 flex items-center">
                            AI Season Classifier <ChevronRight className="ml-3 group-hover:translate-x-2 transition-transform text-purple-500" />
                        </h3>
                        <p className="text-muted-foreground text-lg leading-relaxed max-w-sm">
                            AI モデルを活用して風景を四季に自動分類。壁紙ライブラリを整理します。
                        </p>
                    </div>
                </GlassCard>
            </div>
        </motion.div>
    );
};
