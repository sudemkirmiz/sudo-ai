import { useRef, useEffect, useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, Copy, Check, Cog, Volume2, Square, FileText, CalendarPlus, Loader2 } from 'lucide-react';

export default function ChatArea({ messages, isStreaming, streamingText, toolNotification, onQuickAction }) {
    const endRef = useRef(null);

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, streamingText, toolNotification]);

    return (
        <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-3xl mx-auto space-y-4">
                {messages.map((msg, i) => (
                    <MessageBubble
                        key={i}
                        role={msg.role}
                        content={msg.content}
                        onQuickAction={onQuickAction}
                        showActions={!isStreaming}
                    />
                ))}

                {/* Tool notification pill badge */}
                {toolNotification && <ToolPill text={toolNotification} />}

                {/* Thinking indicator (isStreaming === true BUT no tokens arrived yet) */}
                {isStreaming && !streamingText && !toolNotification && (
                    <div className="flex gap-3">
                        <div
                            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm"
                            style={{ background: 'linear-gradient(135deg, #9333ea, #818cf8)' }}
                        >
                            <Bot size={17} className="text-white" />
                        </div>
                        <div
                            className="px-5 py-4 rounded-[20px] rounded-bl-[4px] flex items-center gap-1.5 w-fit"
                            style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}
                        >
                            <div className="w-2 h-2 rounded-full typing-dot" style={{ background: 'var(--accent)' }}></div>
                            <div className="w-2 h-2 rounded-full typing-dot" style={{ background: 'var(--accent)' }}></div>
                            <div className="w-2 h-2 rounded-full typing-dot" style={{ background: 'var(--accent)' }}></div>
                        </div>
                    </div>
                )}

                {/* Streaming text */}
                {isStreaming && streamingText && (
                    <MessageBubble role="assistant" content={streamingText} isStreaming />
                )}

                <div ref={endRef} />
            </div>
        </div>
    );
}

// ===== Tool Call Pill Badge =====
function ToolPill({ text }) {
    return (
        <div className="flex justify-start">
            <div
                className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full text-sm font-medium animate-pulse"
                style={{
                    background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.08), rgba(244, 114, 182, 0.08))',
                    color: 'var(--accent)',
                    border: '1px solid var(--border-color)',
                    backdropFilter: 'blur(8px)',
                }}
            >
                <Cog size={16} className="animate-spin" style={{ animationDuration: '2s' }} />
                <span>{text}</span>
            </div>
        </div>
    );
}

// ===== Code Block with Copy Button =====
function CodeBlock({ children, className }) {
    const [copied, setCopied] = useState(false);
    const codeText = String(children).replace(/\n$/, '');
    const language = className ? className.replace('language-', '') : '';

    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(codeText).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    }, [codeText]);

    return (
        <div className="relative group rounded-2xl overflow-hidden my-3">
            <div
                className="flex items-center justify-between px-4 py-2 text-xs font-medium"
                style={{ background: '#16132a', color: '#a78bfa' }}
            >
                <span>{language || 'code'}</span>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition-all hover:scale-105 cursor-pointer"
                    style={{
                        background: copied ? 'rgba(34, 197, 94, 0.2)' : 'rgba(167, 139, 250, 0.15)',
                        color: copied ? '#22c55e' : '#c4b5fd',
                    }}
                >
                    {copied ? <Check size={13} /> : <Copy size={13} />}
                    {copied ? 'Kopyalandı!' : 'Kopyala'}
                </button>
            </div>
            <pre
                className="px-4 py-3 overflow-x-auto text-sm leading-relaxed"
                style={{ background: '#1e1b2e', color: '#e2e8f0', margin: 0 }}
            >
                <code>{codeText}</code>
            </pre>
        </div>
    );
}

// ===== TTS Hook =====
function useTTS() {
    const [speaking, setSpeaking] = useState(false);
    const utterRef = useRef(null);
    const [voices, setVoices] = useState([]);

    useEffect(() => {
        const loadVoices = () => setVoices(window.speechSynthesis.getVoices());
        loadVoices();
        window.speechSynthesis.onvoiceschanged = loadVoices;
    }, []);

    const speak = useCallback((text) => {
        window.speechSynthesis.cancel();

        // Regex ile Markdown ve URL temizliği yap, akıcı okunacak sese dönüştür
        const cleanText = text
            .replace(/```[\s\S]*?```/g, '') // Kod bloklarını sil
            .replace(/\[.*?\]\(.*?\)/g, '') // Linkleri sil
            .replace(/https?:\/\/[^\s]+/g, '') // Düz URL'leri sil
            .replace(/[*#>_~|`]/g, '') // Markdown formatting sembolleri
            .replace(/\s+/g, ' ') // Birden fazla boşluğu tek boşluk yap
            .replace(/\n+/g, '. ') // Satır sonlarını dinlenme (nokta) süresi olarak ayarla
            .trim();

        if (!cleanText) return;

        const utter = new SpeechSynthesisUtterance(cleanText);
        utter.lang = 'tr-TR';
        utter.rate = 0.9; // Biraz yavaşlat (kelime yutmayı engeller)
        utter.pitch = 1.1; // Kadınsı bir ton için biraz tiz

        // Kadın sesi önceliği (Yelda, Female vs.)
        let voice = voices.find(v => v.lang.startsWith('tr') && (v.name.includes('Yelda') || v.name.includes('Female')));
        if (!voice) {
            voice = voices.find(v => v.lang.startsWith('tr')); // Herhangi bir Türkçe ses
        }
        if (voice) utter.voice = voice;

        utter.onend = () => setSpeaking(false);
        utter.onerror = () => setSpeaking(false);
        utterRef.current = utter;
        setSpeaking(true);
        window.speechSynthesis.speak(utter);
    }, [voices]);

    const stop = useCallback(() => {
        window.speechSynthesis.cancel();
        setSpeaking(false);
    }, []);

    return { speaking, speak, stop };
}

// ===== Message Bubble =====
function MessageBubble({ role, content, isStreaming, onQuickAction, showActions }) {
    const isUser = role === 'user';
    const { speaking, speak, stop } = useTTS();
    const [actionLoading, setActionLoading] = useState(null);

    const handleQuickAction = async (type) => {
        if (!onQuickAction || actionLoading) return;
        setActionLoading(type);
        try {
            await onQuickAction(type, content);
        } finally {
            setActionLoading(null);
        }
    };

    const markdownComponents = {
        code({ inline, className, children, ...props }) {
            if (!inline && className) {
                return <CodeBlock className={className}>{children}</CodeBlock>;
            }
            return (
                <code
                    className="px-1.5 py-0.5 rounded-md text-sm"
                    style={{ background: 'rgba(147, 51, 234, 0.1)' }}
                    {...props}
                >
                    {children}
                </code>
            );
        },
        pre({ children }) {
            if (children?.type === CodeBlock) return children;
            return (
                <div className="relative group rounded-2xl overflow-hidden my-3">
                    <pre
                        className="px-4 py-3 overflow-x-auto text-sm leading-relaxed"
                        style={{ background: '#1e1b2e', color: '#e2e8f0', margin: 0, borderRadius: '14px' }}
                    >
                        {children}
                    </pre>
                </div>
            );
        },
    };

    return (
        <div className={`flex gap-3 ${isUser ? 'flex-row-reverse justify-end ml-10' : ''}`}>
            {/* Sadece asistan için avatar göster */}
            {!isUser && (
                <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm"
                    style={{
                        background: 'linear-gradient(135deg, #9333ea, #818cf8)',
                    }}
                >
                    <Bot size={17} className="text-white" />
                </div>
            )}

            {/* Content */}
            <div className={`max-w-[85%] ${isUser ? 'ml-auto' : ''}`}>
                <div
                    className={`px-5 py-3.5 text-sm leading-relaxed 
            ${isUser ? 'rounded-[20px] rounded-br-[6px]' : 'rounded-[20px] rounded-bl-[6px]'}
            ${isStreaming && !isUser ? 'typing-cursor' : ''}`}
                    style={{
                        background: isUser ? 'linear-gradient(135deg, #9333ea, #c084fc)' : 'var(--bg-card)',
                        color: isUser ? '#ffffff' : 'var(--text-primary)',
                        border: isUser ? 'none' : '1px solid var(--border-color)',
                        boxShadow: '0 2px 5px rgba(0,0,0,0.02)',
                    }}
                >
                    {isUser ? (
                        <p>{content}</p>
                    ) : (
                        <div className="message-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                                {content}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>

                {/* Action bar — only for assistant, non-streaming */}
                {!isUser && !isStreaming && showActions && (
                    <div className="flex items-center gap-1.5 mt-2 ml-1">
                        {/* TTS */}
                        <button
                            onClick={() => (speaking ? stop() : speak(content))}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium transition-all hover:scale-105 cursor-pointer"
                            style={{
                                color: speaking ? '#ef4444' : 'var(--text-secondary)',
                                background: speaking ? 'rgba(239,68,68,0.1)' : 'var(--accent-pastel)',
                            }}
                            title={speaking ? 'Durdur' : 'Seslendir'}
                        >
                            {speaking ? <Square size={13} /> : <Volume2 size={13} />}
                            {speaking ? 'Durdur' : 'Seslendir'}
                        </button>

                        {/* Docs'a Aktar */}
                        <button
                            onClick={() => handleQuickAction('docs')}
                            disabled={!!actionLoading}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium transition-all hover:scale-105 cursor-pointer disabled:opacity-50"
                            style={{ color: 'var(--text-secondary)', background: 'var(--accent-pastel)' }}
                        >
                            {actionLoading === 'docs' ? (
                                <Loader2 size={13} className="animate-spin" />
                            ) : (
                                <FileText size={13} />
                            )}
                            Docs'a Aktar
                        </button>

                        {/* Takvime İşle */}
                        <button
                            onClick={() => handleQuickAction('calendar')}
                            disabled={!!actionLoading}
                            className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium transition-all hover:scale-105 cursor-pointer disabled:opacity-50"
                            style={{ color: 'var(--text-secondary)', background: 'var(--accent-pastel)' }}
                        >
                            {actionLoading === 'calendar' ? (
                                <Loader2 size={13} className="animate-spin" />
                            ) : (
                                <CalendarPlus size={13} />
                            )}
                            Takvime İşle
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
