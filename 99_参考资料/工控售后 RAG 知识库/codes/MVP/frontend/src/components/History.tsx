import React, { useEffect, useState } from 'react';
import { Clock, MessageSquare, ChevronRight, Calendar, User, Bot, FileText } from 'lucide-react';
import clsx from 'clsx';
import ReactMarkdown from 'react-markdown';
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(res => res.json());

interface Session {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
    sources?: any[];
}

interface HistoryProps {
    user: any;
}

export function History({ user }: HistoryProps) {
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

    // 1. Fetch Sessions with SWR (Cache key depends on user.id)
    const { data: sessions = [], isLoading: loadingSessions } = useSWR(
        user?.id ? `http://localhost:8000/history?user_id=${user.id}` : null,
        fetcher,
        {
            revalidateOnFocus: false, // Don't re-fetch just because user clicked window
            onSuccess: (data) => {
                // Auto-select first session if none selected
                if (data && data.length > 0 && !selectedSessionId) {
                    setSelectedSessionId(data[0].id);
                }
            }
        }
    );

    // 2. Fetch Messages with SWR (Cache key depends on selectedSessionId)
    const { data: messages = [], isLoading: loadingMessages } = useSWR(
        selectedSessionId ? `http://localhost:8000/history/${selectedSessionId}` : null,
        fetcher,
        {
            revalidateOnFocus: false
        }
    );

    function formatTime(iso: string) {
        return new Date(iso).toLocaleString('zh-CN', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    return (
        <div className="flex bg-[#f5f7fa] h-full animate-in fade-in slide-in-from-bottom-4 duration-500 overflow-hidden">

            {/* Left Sidebar: Session List */}
            <div className="w-80 bg-white border-r border-slate-200 flex flex-col h-full">
                <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                    <h3 className="font-bold text-slate-700 text-lg flex items-center gap-2">
                        <Clock size={20} className="text-blue-600" />
                        对话历史
                    </h3>
                    <span className="text-xs font-medium bg-slate-100 text-slate-500 px-2 py-1 rounded-full">
                        {sessions.length}
                    </span>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {loadingSessions ? (
                        [1, 2, 3].map(i => (
                            <div key={i} className="h-16 bg-slate-100 rounded-lg animate-pulse" />
                        ))
                    ) : sessions.length === 0 ? (
                        <div className="text-center p-8 text-slate-400">暂无历史记录</div>
                    ) : (
                        sessions.map((session: Session) => (
                            <div
                                key={session.id}
                                onClick={() => setSelectedSessionId(session.id)}
                                className={clsx(
                                    "p-3 rounded-xl cursor-pointer transition-all border",
                                    selectedSessionId === session.id
                                        ? "bg-blue-50 border-blue-200 shadow-sm"
                                        : "bg-white border-transparent hover:bg-slate-50 hover:border-slate-200"
                                )}
                            >
                                <div className={clsx(
                                    "font-medium mb-1 line-clamp-1",
                                    selectedSessionId === session.id ? "text-blue-700" : "text-slate-700"
                                )}>
                                    {session.title || "新对话"}
                                </div>
                                <div className="flex items-center justify-between text-xs text-slate-400">
                                    <span className="flex items-center gap-1">
                                        <Calendar size={10} />
                                        {formatTime(session.created_at)}
                                    </span>
                                    {selectedSessionId === session.id && <ChevronRight size={14} className="text-blue-400" />}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Right Main: Chat View */}
            <div className="flex-1 flex flex-col h-full bg-slate-50 relative">
                {selectedSessionId ? (
                    <>
                        {/* Header */}
                        <div className="bg-white px-6 py-4 border-b border-slate-200 shadow-sm z-10">
                            <h2 className="font-bold text-slate-800 text-lg">
                                {sessions.find((s: Session) => s.id === selectedSessionId)?.title || "对话详情"}
                            </h2>
                            <p className="text-xs text-slate-400 mt-1 flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-green-500" />
                                已归档
                            </p>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {loadingMessages ? (
                                <div className="space-y-4">
                                    <div className="w-1/3 h-10 bg-slate-200 rounded-lg animate-pulse ml-auto" />
                                    <div className="w-2/3 h-24 bg-slate-200 rounded-lg animate-pulse mr-auto" />
                                </div>
                            ) : messages.length === 0 ? (
                                <div className="text-center text-slate-400 mt-20">此会话没有消息</div>
                            ) : (
                                messages.map((msg: Message, idx: number) => (
                                    <div key={idx} className={clsx("flex gap-4 max-w-4xl mx-auto", msg.role === 'user' ? "justify-end" : "justify-start")}>
                                        {msg.role === 'assistant' && (
                                            <div className="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center shrink-0 shadow-sm">
                                                <Bot size={16} className="text-blue-500" />
                                            </div>
                                        )}

                                        <div className={clsx(
                                            "max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed",
                                            msg.role === 'user'
                                                ? "bg-blue-600 text-white rounded-tr-none"
                                                : "bg-white text-slate-700 border border-slate-100 rounded-tl-none"
                                        )}>
                                            <div className="markdown-body">
                                                {/* Use ReactMarkdown for safe rendering */}
                                                <span className="whitespace-pre-wrap">{msg.content}</span>
                                            </div>

                                            {/* Sources if any */}
                                            {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                                                <div className="mt-3 pt-3 border-t border-slate-100">
                                                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">参考来源:</div>
                                                    <div className="flex flex-wrap gap-2">
                                                        {msg.sources.map((src, i) => (
                                                            <div key={i} className="flex items-center gap-1.5 bg-slate-50 text-slate-600 px-2 py-1 rounded text-xs border border-slate-200">
                                                                <FileText size={10} />
                                                                <span className="truncate max-w-[150px]">{src.title || src.path || "文档"}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {msg.role === 'user' && (
                                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                                                <User size={16} className="text-blue-600" />
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400">
                        <MessageSquare size={64} className="mb-4 opacity-10" />
                        <p>请选择左侧的历史会话查看详情</p>
                    </div>
                )}
            </div>
        </div>
    );
}
