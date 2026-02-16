import React, { useState, useRef, useEffect } from 'react';
import { chat } from '../../services/api';
import { Send, User, Bot, Loader, History, X, MessageSquare } from 'lucide-react';

const Chatbot = () => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your inventory assistant. How can I help you today?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [sessions, setSessions] = useState([]);
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const loadHistory = async () => {
        try {
            const response = await chat.getSessions();
            if (response.data.success) {
                setSessions(response.data.sessions);
            }
        } catch (err) {
            console.error("Failed to load history:", err);
        }
    };

    const loadSession = async (sessionId) => {
        try {
            setIsLoading(true);
            const response = await chat.getHistory(sessionId);
            if (response.data.success) {
                setMessages(response.data.messages);
                setCurrentConversationId(sessionId);
                setShowHistory(false);
            }
        } catch (err) {
            console.error("Failed to load session:", err);
        } finally {
            setIsLoading(false);
        }
    };

    const startNewChat = () => {
        setMessages([
            { role: 'assistant', content: 'Hello! I am your inventory assistant. How can I help you today?' }
        ]);
        setCurrentConversationId(null);
        setShowHistory(false);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const payload = {
                question: userMessage.content,
                conversation_id: currentConversationId
            };

            const response = await chat.query(payload);
            if (response.data.success) {
                setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
                if (response.data.conversation_id && !currentConversationId) {
                    setCurrentConversationId(response.data.conversation_id);
                }
            } else {
                setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error." }]);
            }
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { role: 'assistant', content: "Network error. Please try again." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden h-[calc(100vh-8rem)] relative">

            {/* History Sidebar (Mobile/Overlay style) */}
            {showHistory && (
                <div className="absolute inset-0 z-10 flex">
                    <div className="w-64 bg-slate-50 border-r border-slate-200 flex flex-col h-full animate-in slide-in-from-left duration-200">
                        <div className="p-4 border-b border-slate-200 flex justify-between items-center">
                            <h3 className="font-semibold text-slate-700">History</h3>
                            <button onClick={() => setShowHistory(false)} className="text-slate-400 hover:text-slate-600">
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-3">
                            <button
                                onClick={startNewChat}
                                className="w-full text-left px-3 py-2 rounded-lg bg-blue-100 text-blue-700 font-medium hover:bg-blue-200 mb-4 flex items-center gap-2"
                            >
                                <MessageSquare size={16} />
                                New Chat
                            </button>

                            <div className="space-y-1 overflow-y-auto max-h-[calc(100%-80px)]">
                                {sessions.length === 0 ? (
                                    <p className="text-xs text-slate-400 text-center py-4">No recent history</p>
                                ) : (
                                    sessions.map(session => (
                                        <button
                                            key={session.id}
                                            onClick={() => loadSession(session.id)}
                                            className={`w-full text-left px-3 py-3 rounded-lg text-sm hover:bg-white hover:shadow-sm transition-all border border-transparent hover:border-slate-100 group ${currentConversationId === session.id ? 'bg-white shadow-sm border-slate-100' : ''}`}
                                        >
                                            <p className="font-medium text-slate-700 truncate">{session.preview}</p>
                                            <p className="text-xs text-slate-400 mt-1">{session.message_count} messages</p>
                                        </button>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="flex-1 bg-black/20 backdrop-blur-sm" onClick={() => setShowHistory(false)} />
                </div>
            )}

            <div className="flex-1 flex flex-col h-full">
                <div className="p-4 bg-slate-50 border-b border-slate-100 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <Bot className="text-blue-500" size={24} />
                        <div>
                            <h2 className="text-lg font-semibold text-slate-800">AI Assistant</h2>
                            <p className="text-xs text-slate-500">Ask about stock levels, reorders, or analytics</p>
                        </div>
                    </div>
                    <button
                        onClick={() => {
                            setShowHistory(true);
                            loadHistory();
                        }}
                        className="p-2 text-slate-500 hover:bg-slate-200 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                    >
                        <History size={20} />
                        <span>History</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg, index) => (
                        <div
                            key={index}
                            className={`flex items-start gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div className={`p-2 rounded-full shrink-0 ${msg.role === 'user' ? 'bg-blue-100' : 'bg-slate-100'}`}>
                                {msg.role === 'user' ? <User size={20} className="text-blue-600" /> : <Bot size={20} className="text-slate-600" />}
                            </div>

                            <div
                                className={`max-w-[80%] p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white rounded-tr-none'
                                    : 'bg-slate-100 text-slate-800 rounded-tl-none'
                                    }`}
                            >
                                {msg.content}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-center gap-2 text-slate-400 text-sm ml-12">
                            <Loader size={16} className="animate-spin" />
                            Thinking...
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <form onSubmit={handleSubmit} className="p-4 border-t border-slate-100 bg-white">
                    <div className="flex items-center gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your question..."
                            className="flex-1 px-4 py-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Chatbot;
