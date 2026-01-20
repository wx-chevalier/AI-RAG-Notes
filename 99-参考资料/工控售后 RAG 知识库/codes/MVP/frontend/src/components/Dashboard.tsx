import React from 'react';
import { Users, MessageSquare, AlertTriangle, CheckCircle2, MoreHorizontal, ThumbsUp, ChevronRight, Activity } from 'lucide-react';
import clsx from 'clsx';

export function Dashboard() {
    const [stats, setStats] = React.useState<any[]>([]);
    const [trendData, setTrendData] = React.useState<any[]>([]);
    const [feedbackDist, setFeedbackDist] = React.useState<any>({ positive: 0, negative: 0, rate: 0 });
    const [activities, setActivities] = React.useState<any[]>([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        async function fetchStats() {
            try {
                const res = await fetch('http://localhost:8000/dashboard/stats');
                if (res.ok) {
                    const data = await res.json();

                    // 1. Process Stats Cards
                    if (data.stats) {
                        const mappedStats = data.stats.map((s: any) => {
                            let Icon = Users;
                            if (s.iconKey === 'message') Icon = MessageSquare;
                            else if (s.iconKey === 'alert') Icon = AlertTriangle;
                            else if (s.iconKey === 'check') Icon = CheckCircle2;

                            return { ...s, icon: <Icon size={24} /> };
                        });
                        setStats(mappedStats);
                    }

                    // 2. Process Trend
                    if (data.trend) {
                        setTrendData(data.trend);
                    }

                    // 3. Process Feedback Distribution
                    if (data.feedback_dist) {
                        setFeedbackDist(data.feedback_dist);
                    }

                    // 4. Process Activity
                    if (data.activities) {
                        setActivities(data.activities);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch stats", e);
            } finally {
                setLoading(false);
            }
        }
        fetchStats();
    }, []);

    // Helper for Chart Height Normalization
    const maxTrend = Math.max(...trendData.map(d => d.count), 1); // Avoid div by 0

    return (
        <div className="flex-1 overflow-y-auto bg-[#f5f7fa] p-8 h-full">
            {/* Header */}
            <div className="flex justify-between items-center mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 tracking-tight">数据概览 (Real-time)</h2>
                    <p className="text-sm text-slate-500 mt-1">查看系统实时运行状态与 Supabase 知识库数据</p>
                </div>
                <div className="flex gap-3">
                    <span className="px-3 py-1.5 bg-green-50 border border-green-100 text-green-700 text-sm rounded-lg flex items-center gap-2 font-medium shadow-sm">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> 系统在线
                    </span>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                {stats.length > 0 ? stats.map((stat, idx) => (
                    <StatCard key={idx} {...stat} delay={idx * 100} />
                )) : (
                    // Skeleton Loading
                    [1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-slate-200 rounded-2xl animate-pulse"></div>)
                )}
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Main Chart (Trend) */}
                <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold text-slate-700">提问趋势 (Last 7 Days)</h3>
                        <button className="text-slate-400 hover:text-blue-600"><MoreHorizontal size={20} /></button>
                    </div>
                    {/* Dynamic Chart Area */}
                    <div className="h-64 flex items-end justify-between gap-2 px-2 pb-2 border-b border-slate-100 relative">
                        {/* Grid Lines */}
                        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
                            {[1, 2, 3, 4, 5].map(i => <div key={i} className="w-full h-px bg-slate-50"></div>)}
                        </div>
                        {/* Bars */}
                        {trendData.length > 0 ? trendData.map((d, i) => {
                            const heightPct = (d.count / maxTrend) * 100; // 0 to 100
                            // Ensure minimal visibility for 0
                            const displayHeight = heightPct === 0 ? 2 : heightPct;

                            return (
                                <div key={i} className="group relative flex-1 bg-blue-50 rounded-t-lg hover:bg-blue-100 transition-all cursor-pointer flex flex-col justify-end overflow-hidden">
                                    <div
                                        style={{ height: `${displayHeight}%` }}
                                        className={clsx(
                                            "w-full rounded-t-lg transition-all relative overflow-hidden",
                                            d.count > 0 ? "bg-blue-500 opacity-80 group-hover:opacity-100" : "bg-slate-200"
                                        )}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-t from-blue-600 to-transparent opacity-50"></div>
                                    </div>
                                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                                        {d.count} Queries
                                    </div>
                                </div>
                            );
                        }) : (
                            <div className="w-full h-full flex items-center justify-center text-slate-300">暂无数据</div>
                        )}
                    </div>
                    <div className="flex justify-between mt-4 text-xs text-slate-400 font-medium px-2">
                        {trendData.map((d, i) => <span key={i}>{d.day}</span>)}
                    </div>
                </div>

                {/* Secondary Chart (Feedback) */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold text-slate-700">反馈分布</h3>
                    </div>
                    <div className="flex flex-col items-center justify-center py-4">
                        <div className="relative w-40 h-40">
                            <svg viewBox="0 0 36 36" className="w-full h-full transform -rotate-90">
                                <path className="text-slate-100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3.8" />
                                {/* Dynamic Stroke Dash Array for Positive Rate */}
                                <path
                                    className="text-green-500 transition-all duration-1000 ease-out"
                                    strokeDasharray={`${feedbackDist.rate}, 100`}
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="3.8"
                                    strokeLinecap="round"
                                />
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold text-slate-800">{feedbackDist.rate}%</span>
                                <span className="text-xs text-slate-400">好评率</span>
                            </div>
                        </div>
                    </div>
                    <div className="space-y-3 mt-4">
                        <div className="flex justify-between items-center text-sm">
                            <div className="flex items-center gap-2 text-slate-600"><div className="w-3 h-3 bg-green-500 rounded-full"></div>有帮助 (Positive)</div>
                            <span className="font-bold">{feedbackDist.positive}</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <div className="flex items-center gap-2 text-slate-600"><div className="w-3 h-3 bg-rose-500 rounded-full"></div>无帮助 (Negative)</div>
                            <span className="font-bold">{feedbackDist.negative}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Activity List */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200 overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                    <h3 className="font-bold text-slate-700">最近动态 (Recent Questions)</h3>
                    {/* <button className="text-sm text-blue-600 font-medium hover:underline">查看全部</button> */}
                </div>
                <div className="divide-y divide-slate-50">
                    {activities.length > 0 ? activities.map((act, i) => (
                        <div key={i} className="p-4 flex items-center gap-4 hover:bg-slate-50 transition-colors cursor-pointer">
                            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500">
                                <MessageSquare size={18} />
                            </div>
                            <div className="flex-1">
                                <div className="text-sm font-medium text-slate-800 line-clamp-1">
                                    用户 {act.user?.substring(0, 6)}... 提问: "{act.content}"
                                </div>
                                <div className="text-xs text-slate-400 mt-0.5">{act.time} · 来自 Next.js 前端</div>
                            </div>
                            <ChevronRight size={16} className="text-slate-300" />
                        </div>
                    )) : (
                        <div className="p-8 text-center text-slate-400">暂无最近动态</div>
                    )}
                </div>
            </div>

        </div>
    );
}

interface StatCardProps {
    icon: React.ReactNode;
    color: string;
    value: string;
    label: string;
    change?: string;
    changeType?: string;
    delay: number;
}

function StatCard({ icon, color, value, label, change, changeType, delay }: StatCardProps) {
    const colorClasses: Record<string, string> = {
        blue: 'bg-blue-50 text-blue-600',
        green: 'bg-green-50 text-green-600',
        orange: 'bg-orange-50 text-orange-600',
        purple: 'bg-purple-50 text-purple-600',
    };

    return (
        <div
            className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4"
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className="flex justify-between items-start mb-4">
                <div className={clsx("w-12 h-12 rounded-xl flex items-center justify-center", colorClasses[color] || colorClasses['blue'])}>
                    {icon}
                </div>
                {change && (
                    <span className={clsx(
                        "text-xs font-bold px-2 py-1 rounded-full",
                        changeType === 'up' ? 'bg-green-50 text-green-600' :
                            changeType === 'down' ? 'bg-rose-50 text-rose-600' : 'bg-slate-100 text-slate-500'
                    )}>
                        {change}
                    </span>
                )}
            </div>
            <div>
                <div className="text-3xl font-bold text-slate-800 tracking-tight mb-1">{value}</div>
                <div className="text-sm font-medium text-slate-400">{label}</div>
            </div>
        </div>
    );
}
