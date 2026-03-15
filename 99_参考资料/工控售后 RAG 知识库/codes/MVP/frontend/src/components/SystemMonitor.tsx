import React, { useEffect, useState } from 'react';
import { Activity, Clock, Database, Zap, ArrowUpRight } from 'lucide-react';
import clsx from 'clsx';

export function SystemMonitor() {
    const [metrics, setMetrics] = useState<any>(null);
    const [chartData, setChartData] = useState<any>(null);

    useEffect(() => {
        fetch('http://localhost:8000/admin/performance')
            .then(res => res.json())
            .then(data => {
                setMetrics(data.metrics);
                setChartData(data.chart);
            })
            .catch(e => console.error(e));
    }, []);

    if (!metrics) return <div className="p-8 text-center text-slate-400">Loading System Metrics...</div>;

    return (
        <div className="flex-1 overflow-y-auto bg-[#f5f7fa] p-8 h-full animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 tracking-tight">系统监控 (System Monitor)</h2>
                    <p className="text-sm text-slate-500 mt-1">实时监控 RAG 链路各环节延迟与性能指标</p>
                </div>
                <div className="flex gap-3">
                    <span className="px-3 py-1.5 bg-green-50 border border-green-100 text-green-700 text-sm rounded-lg flex items-center gap-2 font-medium shadow-sm">
                        <Activity size={14} /> 运行正常
                    </span>
                </div>
            </div>

            {/* Top Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
                <PerfCard icon={<Zap size={20} />} color="blue" label="Query Rewrite" value={`${metrics.avg_rewrite}s`} />
                <PerfCard icon={<Database size={20} />} color="green" label="Vector Retrieve" value={`${metrics.avg_retrieve}s`} />
                <PerfCard icon={<Activity size={20} />} color="orange" label="LLM Generate" value={`${metrics.avg_generate}s`} />
                <PerfCard icon={<Clock size={20} />} color="purple" label="Total Latency (Avg)" value={`${metrics.avg_total}s`} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Visual: Simulated Bar Chart using CSS */}
                <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="font-bold text-slate-700">各环节耗时分布 (Recent Requests)</h3>
                    </div>

                    <div className="h-64 flex items-end justify-between gap-1 px-4 border-b border-slate-100 pb-2 relative">
                        {/* Background Grid */}
                        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
                            {[1, 2, 3, 4].map(i => <div key={i} className="w-full h-px bg-slate-50"></div>)}
                        </div>

                        {chartData?.labels?.map((label: string, i: number) => {
                            // Stacked Bar Logic
                            const v1 = chartData.rewrite[i] || 0;
                            const v2 = chartData.retrieve[i] || 0;
                            const v3 = chartData.generate[i] || 0;
                            const total = v1 + v2 + v3;
                            // Normalize height (assuming max reasonable latency ~ 10s for scale, or dynamic)
                            const maxScale = 15;
                            const h1 = (v1 / maxScale) * 100;
                            const h2 = (v2 / maxScale) * 100;
                            const h3 = (v3 / maxScale) * 100;

                            return (
                                <div key={i} className="w-full h-full flex flex-col justify-end group hover:bg-slate-50/50 rounded-t relative">
                                    {/* Tooltip */}
                                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-slate-800 text-white text-[10px] py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-nowrap">
                                        Total: {total.toFixed(1)}s
                                    </div>

                                    {/* Stacked Segments */}
                                    {/* Generate (Top) */}
                                    <div style={{ height: `${h3}%` }} className="bg-orange-400 w-full opacity-90 rounded-t-sm"></div>
                                    {/* Retrieve (Mid) */}
                                    <div style={{ height: `${h2}%` }} className="bg-green-500 w-full opacity-90"></div>
                                    {/* Rewrite (Bot) */}
                                    <div style={{ height: `${h1}%` }} className="bg-blue-500 w-full opacity-90 rounded-b-sm"></div>
                                </div>
                            );
                        })}
                    </div>
                    <div className="flex justify-center mt-4 gap-6 text-xs font-medium text-slate-500">
                        <div className="flex items-center gap-2"><span className="w-3 h-3 bg-blue-500 rounded-sm"></span> Rewrite</div>
                        <div className="flex items-center gap-2"><span className="w-3 h-3 bg-green-500 rounded-sm"></span> Retrieve</div>
                        <div className="flex items-center gap-2"><span className="w-3 h-3 bg-orange-400 rounded-sm"></span> Generate</div>
                    </div>
                </div>

                {/* Metrics Breakdown */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <h3 className="font-bold text-slate-700 mb-6">关键性能指标 (KPIs)</h3>
                    <div className="space-y-6">
                        <MetricBar label="P50 Latency" value={`${metrics.avg_total}s`} percentage={40} color="bg-green-500" />
                        <MetricBar label="P99 Latency (Tail)" value={`${metrics.p99_total}s`} percentage={85} color="bg-red-500" />

                        <div className="pt-4 border-t border-slate-100">
                            <div className="flex justify-between items-center mb-3">
                                <span className="text-sm text-slate-500">请求成功率</span>
                                <span className="text-sm font-bold text-green-600">{metrics.success_rate}</span>
                            </div>
                            <div className="flex justify-between items-center mb-3">
                                <span className="text-sm text-slate-500">Embedding Provider</span>
                                <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded">OpenAI/Local</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-500">Rerank Model</span>
                                <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded">BGE-Reranker</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function PerfCard({ icon, color, label, value }: any) {
    const colorClasses: Record<string, string> = {
        blue: 'bg-blue-50 text-blue-600',
        green: 'bg-green-50 text-green-600',
        orange: 'bg-orange-50 text-orange-600',
        purple: 'bg-purple-50 text-purple-600',
    };
    return (
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-start mb-3">
                <div className={clsx("w-10 h-10 rounded-lg flex items-center justify-center", colorClasses[color])}>
                    {icon}
                </div>
            </div>
            <div className="text-2xl font-bold text-slate-800 mb-1">{value}</div>
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</div>
        </div>
    );
}

function MetricBar({ label, value, percentage, color }: any) {
    return (
        <div>
            <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-600 font-medium">{label}</span>
                <span className="font-bold text-slate-800">{value}</span>
            </div>
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div style={{ width: `${percentage}%` }} className={`h-full rounded-full ${color}`}></div>
            </div>
        </div>
    )
}
