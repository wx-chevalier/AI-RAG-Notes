import React, { useEffect, useState } from 'react';
import { AlertTriangle, Clock, MessageSquare, Download } from 'lucide-react';

interface BadCase {
    id: string;
    question: string;
    comment: string;
    user: string;
    time: string;
}

export function BadCases() {
    const [cases, setCases] = useState<BadCase[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('http://localhost:8000/admin/badcases')
            .then(res => res.json())
            .then(data => {
                setCases(data);
                setLoading(false);
            })
            .catch(e => console.error(e));
    }, []);

    function formatTime(iso: string) {
        const d = new Date(iso);
        return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
    }

    return (
        <div className="flex-1 overflow-y-auto bg-[#f5f7fa] p-8 h-full animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-white sticky top-0 z-10">
                    <div>
                        <h3 className="font-bold text-slate-700 text-lg flex items-center gap-2">
                            <AlertTriangle className="text-orange-500" size={20} />
                            待优化案例 (Bad Cases)
                        </h3>
                        <p className="text-xs text-slate-400 mt-1">用户反馈为"无帮助"的对话记录，请优先分析处理。</p>
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors">
                        <Download size={16} /> 导出 CSV
                    </button>
                </div>

                <div className="divide-y divide-slate-100">
                    {loading ? (
                        <div className="p-12 text-center text-slate-400">加载数据中...</div>
                    ) : cases.length === 0 ? (
                        <div className="p-12 text-center flex flex-col items-center gap-3">
                            <div className="w-12 h-12 bg-green-50 text-green-500 rounded-full flex items-center justify-center text-2xl">🎉</div>
                            <div className="text-slate-800 font-medium">太棒了！暂无 Bad Cases</div>
                            <div className="text-slate-400 text-sm">用户的反馈都非常积极。</div>
                        </div>
                    ) : (
                        cases.map((c) => (
                            <div key={c.id} className="p-6 hover:bg-slate-50 transition-colors group">
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex-1 pr-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="bg-blue-100 text-blue-700 text-[10px] font-bold px-1.5 py-0.5 rounded">用户提问</span>
                                            <span className="text-sm font-medium text-slate-800">{c.question}</span>
                                        </div>
                                    </div>
                                    <span className="text-xs text-slate-400 font-mono flex items-center gap-1 shrink-0">
                                        <Clock size={12} /> {formatTime(c.time)}
                                    </span>
                                </div>

                                <div className="bg-orange-50 border-l-4 border-orange-400 p-3 rounded-r-lg mb-3">
                                    <div className="text-xs font-bold text-orange-800 mb-1 flex items-center gap-1">
                                        <AlertTriangle size={12} /> 用户反馈建议
                                    </div>
                                    <p className="text-sm text-orange-900 leading-relaxed">
                                        {c.comment || "用户未留下具体评论 (仅点踩)"}
                                    </p>
                                </div>

                                <div className="flex items-center justify-between text-xs text-slate-500 mt-4">
                                    <div className="flex items-center gap-4">
                                        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-300"></span> {c.user}</span>
                                        <span>ID: {c.id.slice(0, 8)}</span>
                                    </div>
                                    <button className="text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <MessageSquare size={14} /> 查看完整上下文
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
