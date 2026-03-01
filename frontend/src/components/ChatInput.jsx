import { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Paperclip, X, Loader2 } from 'lucide-react';

export default function ChatInput({ onSend, onUpload, disabled, activeChatId }) {
    const [text, setText] = useState('');
    const [isListening, setIsListening] = useState(false);
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const recognitionRef = useRef(null);
    const fileInputRef = useRef(null);

    // Web Speech API setup
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.lang = 'tr-TR';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                setText((prev) => (prev ? prev + ' ' + transcript : transcript));
                setIsListening(false);
            };

            recognition.onerror = () => setIsListening(false);
            recognition.onend = () => setIsListening(false);

            recognitionRef.current = recognition;
        }
    }, []);

    const toggleListening = () => {
        if (!recognitionRef.current) return;
        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
        } else {
            recognitionRef.current.start();
            setIsListening(true);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const trimmed = text.trim();
        if (!trimmed || disabled) return;
        onSend(trimmed);
        setText('');
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    // File handling
    const handleFileSelect = async (file) => {
        if (!file) return;
        const ext = file.name.split('.').pop()?.toLowerCase();
        if (!['pdf', 'txt'].includes(ext)) {
            alert('Sadece .pdf ve .txt dosyaları desteklenir.');
            return;
        }
        if (!activeChatId) {
            alert('Önce bir sohbet başlatın veya seçin.');
            return;
        }

        setUploading(true);
        try {
            await onUpload(activeChatId, file);
            setUploadedFile(file.name);
        } catch (err) {
            alert(`Yükleme hatası: ${err.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleFileInput = (e) => {
        const file = e.target.files?.[0];
        if (file) handleFileSelect(file);
        e.target.value = '';
    };

    // Drag and drop
    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };
    const handleDragLeave = () => setIsDragOver(false);
    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files?.[0];
        if (file) handleFileSelect(file);
    };

    return (
        <div
            className="px-8 pb-6 pt-3"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            {/* Uploaded file badge */}
            {uploadedFile && (
                <div className="max-w-3xl mx-auto mb-2 flex justify-start">
                    <span
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
                        style={{
                            background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.08), rgba(244, 114, 182, 0.08))',
                            color: 'var(--accent)',
                            border: '1px solid var(--border-color)',
                        }}
                    >
                        📎 {uploadedFile} eklendi
                        <button
                            onClick={() => setUploadedFile(null)}
                            className="hover:scale-110 transition-all cursor-pointer"
                            style={{ color: 'var(--text-secondary)' }}
                        >
                            <X size={12} />
                        </button>
                    </span>
                </div>
            )}

            {/* Drag overlay */}
            {isDragOver && (
                <div
                    className="max-w-3xl mx-auto mb-2 py-8 rounded-2xl border-2 border-dashed text-center text-sm font-medium"
                    style={{ borderColor: 'var(--accent)', color: 'var(--accent)', background: 'var(--accent-pastel)' }}
                >
                    📄 Dosyayı buraya bırakın (PDF / TXT)
                </div>
            )}

            <form
                onSubmit={handleSubmit}
                className="max-w-3xl mx-auto flex items-center gap-3 px-5 py-3 rounded-full transition-all duration-300"
                style={{
                    background: 'var(--bg-card)',
                    border: isDragOver ? '1.5px solid var(--accent)' : '1.5px solid var(--border-color)',
                    boxShadow: '0 8px 30px rgba(147, 51, 234, 0.08), 0 2px 8px rgba(0,0,0,0.04)',
                }}
            >
                {/* Paperclip upload */}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.txt"
                    onChange={handleFileInput}
                    className="hidden"
                />
                <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="p-2.5 rounded-full transition-all duration-200 hover:scale-110 cursor-pointer"
                    style={{
                        color: uploading ? 'var(--accent)' : 'var(--text-secondary)',
                        background: 'var(--accent-pastel)',
                    }}
                    title="Dosya ekle (PDF / TXT)"
                >
                    {uploading ? <Loader2 size={20} className="animate-spin" /> : <Paperclip size={20} />}
                </button>

                <input
                    type="text"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Bir şeyler sor..."
                    disabled={disabled}
                    className="flex-1 bg-transparent outline-none text-base py-1 placeholder:text-gray-400"
                    style={{ color: 'var(--text-primary)' }}
                />

                {/* Listening indicator */}
                {isListening && (
                    <div className="flex items-center gap-2 text-sm font-medium whitespace-nowrap" style={{ color: 'var(--accent)' }}>
                        <span className="relative flex h-3 w-3">
                            <span className="voice-pulse absolute inline-flex h-full w-full rounded-full opacity-75" style={{ background: 'var(--accent)' }} />
                            <span className="relative inline-flex rounded-full h-3 w-3" style={{ background: 'var(--accent)' }} />
                        </span>
                        Dinliyorum...
                    </div>
                )}

                {/* Mic Button */}
                <button
                    type="button"
                    onClick={toggleListening}
                    className="p-2.5 rounded-full transition-all duration-200 hover:scale-110 cursor-pointer"
                    style={{
                        color: isListening ? '#ffffff' : 'var(--text-secondary)',
                        background: isListening ? 'var(--accent)' : 'var(--accent-pastel)',
                    }}
                    title={isListening ? 'Dinlemeyi durdur' : 'Sesle giriş'}
                >
                    {isListening ? <MicOff size={20} /> : <Mic size={20} />}
                </button>

                {/* Send Button */}
                <button
                    type="submit"
                    disabled={disabled || !text.trim()}
                    className="p-3 rounded-full text-white transition-all duration-200 hover:scale-110 hover:shadow-lg disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
                    style={{ background: 'linear-gradient(135deg, #9333ea, #c084fc)' }}
                >
                    <Send size={20} />
                </button>
            </form>
        </div>
    );
}
