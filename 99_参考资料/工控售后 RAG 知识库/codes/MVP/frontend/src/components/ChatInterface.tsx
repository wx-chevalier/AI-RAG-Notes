import React, { useState, useEffect, useRef } from 'react';
import { Bot, User, XCircle, LogOut, FileText, ThumbsUp, ThumbsDown, Paperclip, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import clsx from 'clsx';

interface Message {
    id: string;
    role: 'assistant' | 'user';
    content: string;
    timestamp: string;
    isStreaming?: boolean;
    sources?: string[];
}

const MOCK_MESSAGES: Message[] = [
    {
        id: '1',
        role: 'assistant',
        content: '您好！我是工业智能售后助手。请问有什么技术问题需要帮您解答吗？',
        timestamp: '10:00'
    }
];

interface ChatInterfaceProps {
    role: string;
    user: any;
}

export function ChatInterface({ role, user }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>(MOCK_MESSAGES);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userText = input;
        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: userText,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        const aiMsgId = (Date.now() + 1).toString();

        try {
            const historyForApi = messages.map(m => ({
                role: m.role,
                content: m.content
            }));

            // Use SSE streaming endpoint
            const res = await fetch('http://localhost:8000/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userText,
                    history: historyForApi,
                    user_id: user?.id || 'mvp-user-001',
                    top_k: 3
                })
            });

            if (!res.ok) throw new Error('API request failed');
            if (!res.body) throw new Error('No response body');

            // Create AI message placeholder
            const initialAiMsg: Message = {
                id: aiMsgId,
                role: 'assistant',
                content: '',
                isStreaming: true,
                sources: [],
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, initialAiMsg]);
            setIsTyping(false);

            // Read the SSE stream
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep incomplete chunk

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.type === 'token') {
                                // Append token to message content
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId
                                        ? { ...m, content: m.content + data.content }
                                        : m
                                ));
                            } else if (data.type === 'sources') {
                                // Update sources
                                const sourceNames = data.sources?.map((s: any) => s.title) || [];
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId
                                        ? { ...m, sources: sourceNames }
                                        : m
                                ));
                            } else if (data.type === 'done') {
                                // Mark streaming complete, use processed final answer
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId
                                        ? { ...m, isStreaming: false, content: data.final_answer }
                                        : m
                                ));
                            } else if (data.type === 'error') {
                                setMessages(prev => prev.map(m =>
                                    m.id === aiMsgId
                                        ? { ...m, isStreaming: false, content: `⚠️ 错误: ${data.message}` }
                                        : m
                                ));
                            }
                        } catch (e) {
                            console.error('Failed to parse SSE data:', e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error(error);
            setIsTyping(false);
            const errorMsg: Message = {
                id: Date.now().toString(),
                role: 'assistant',
                content: '⚠️ 系统连接失败，请检查后端服务是否启动 (http://localhost:8000)。',
                timestamp: new Date().toLocaleTimeString()
            };
            setMessages(prev => [...prev, errorMsg]);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#f5f7fa]">
            {/* Header */}
            <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 shadow-sm z-10">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                        <Bot size={20} />
                    </div>
                    <div>
                        <h2 className="font-bold text-slate-800 text-sm">技术支持专家 Agent</h2>
                        <div className="flex items-center gap-1.5">
                            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                            <span className="text-xs text-slate-500 font-medium">RAG Engine Online</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <button className="text-slate-400 hover:text-slate-600 transition-colors" title="Clear Chat">
                        <XCircle size={18} />
                    </button>
                    <div className="h-4 w-px bg-slate-200"></div>
                    <button className="text-slate-400 hover:text-red-500 transition-colors" title="End Session">
                        <LogOut size={18} />
                    </button>
                </div>
            </header>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin">
                {messages.map((msg) => (
                    <div key={msg.id} className={clsx("flex gap-4 group", msg.role === 'user' ? 'flex-row-reverse' : '')}>
                        {/* Avatar */}
                        <div className={clsx(
                            "w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 border-2",
                            msg.role === 'assistant'
                                ? 'bg-white border-blue-100 text-blue-600 shadow-sm'
                                : 'bg-slate-800 border-slate-700 text-white shadow-sm'
                        )}>
                            {msg.role === 'assistant' ? <Bot size={18} /> : <User size={18} />}
                        </div>

                        {/* Bubble */}
                        <div className={clsx("flex flex-col max-w-[85%] md:max-w-[70%]", msg.role === 'user' ? 'items-end' : 'items-start')}>
                            <div className="flex items-center gap-2 mb-1 px-1">
                                <span className="text-[10px] font-bold text-slate-400">{msg.role === 'user' ? 'You' : 'AI Agent'}</span>
                                <span className="text-[10px] text-slate-300">{msg.timestamp}</span>
                            </div>
                            <div className={clsx(
                                "px-5 py-3.5 rounded-2xl text-[14px] leading-relaxed shadow-sm whitespace-pre-wrap prose prose-sm max-w-none",
                                msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-none prose-invert'
                                    : 'bg-white text-slate-700 border border-slate-100 rounded-tl-none'
                            )}>
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                {msg.isStreaming && <span className="inline-block w-1.5 h-4 ml-1 bg-blue-400 animate-pulse align-middle"></span>}
                            </div>

                            {/* RAG Sources */}
                            {msg.role === 'assistant' && msg.sources && !msg.isStreaming && (
                                <div className="mt-3 animate-in fade-in slide-in-from-top-2 duration-500">
                                    <div className="flex flex-wrap gap-2 mb-2">
                                        {msg.sources.map((src, idx) => (
                                            <div key={idx} className="flex items-center gap-1.5 bg-white border border-slate-200 px-2.5 py-1.5 rounded-md text-xs text-slate-500 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 cursor-pointer transition-all shadow-sm group/source">
                                                <FileText size={12} className="text-slate-400 group-hover/source:text-blue-500" />
                                                <span className="truncate max-w-[150px]">{src}</span>
                                            </div>
                                        ))}
                                    </div>
                                    {/* Feedback Actions */}
                                    <div className="flex items-center gap-3 px-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                        <button className="flex items-center gap-1 text-xs text-slate-400 hover:text-green-600 transition-colors">
                                            <ThumbsUp size={14} /> 有帮助
                                        </button>
                                        <button className="flex items-center gap-1 text-xs text-slate-400 hover:text-rose-500 transition-colors">
                                            <ThumbsDown size={14} /> 没用
                                        </button>
                                        <span className="text-slate-300">|</span>
                                        <button className="text-xs text-slate-400 hover:text-blue-600 transition-colors">复制</button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="flex gap-4">
                        <div className="w-9 h-9 rounded-full bg-white border border-blue-100 flex items-center justify-center text-blue-600"><Bot size={18} /></div>
                        <div className="flex items-center gap-1 h-9 px-4 bg-white border border-slate-100 rounded-2xl rounded-tl-none shadow-sm">
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-75"></div>
                            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-150"></div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} className="h-1" />
            </div>

            {/* Input Area */}
            <div className="p-4 md:p-6 bg-white border-t border-slate-200">
                <div className="max-w-4xl mx-auto relative">
                    <div className="absolute -top-10 left-0 flex gap-2">
                        <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-md border border-slate-200 cursor-pointer hover:bg-slate-200 transition-colors">如何配置 MQTT?</span>
                        <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-md border border-slate-200 cursor-pointer hover:bg-slate-200 transition-colors">安装失败报错 1062</span>
                    </div>
                    <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus-within:ring-2 focus-within:ring-blue-100 focus-within:border-blue-400 focus-within:bg-white transition-all shadow-inner">
                        <button className="text-slate-400 hover:text-blue-600 transition-colors p-1">
                            <Paperclip size={20} />
                        </button>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="请输入您的问题... (Enter 发送)"
                            className="flex-1 bg-transparent border-none outline-none text-sm text-slate-700 placeholder:text-slate-400"
                        />
                        <button
                            onClick={handleSend}
                            disabled={!input.trim()}
                            className={clsx(
                                "p-2 rounded-lg transition-all duration-200",
                                input.trim()
                                    ? 'bg-blue-600 text-white shadow-md hover:bg-blue-700 hover:scale-105 active:scale-95'
                                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            )}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                    <div className="text-center mt-2">
                        <p className="text-[10px] text-slate-400">AI 生成内容可能存在误差，请以官方技术文档为准 · RAG Engine v1.0.2</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
