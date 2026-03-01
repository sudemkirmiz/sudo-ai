import { useState, useEffect } from 'react';
import { X, Cpu, Cloud, Server, User } from 'lucide-react';

export default function SettingsModal({ open, onClose, settings, onSave, username, onChangeUsername }) {
    const [local, setLocal] = useState({ ...settings });
    const [localName, setLocalName] = useState(username || '');

    useEffect(() => {
        if (open) {
            setLocal({ ...settings });
            setLocalName(username || '');
        }
    }, [open, settings, username]);

    if (!open) return null;

    const handleSave = () => {
        onSave(local);
        if (localName.trim() && localName.trim() !== username) {
            onChangeUsername(localName.trim());
        }
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
            {/* Overlay */}
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

            {/* Modal */}
            <div
                className="relative w-full max-w-md mx-4 rounded-3xl shadow-2xl overflow-hidden"
                style={{ background: 'var(--bg-sidebar)', border: '1px solid var(--border-color)' }}
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b" style={{ borderColor: 'var(--border-color)' }}>
                    <h2 className="text-lg font-bold flex items-center gap-2.5" style={{ color: 'var(--text-primary)' }}>
                        <Cpu size={22} style={{ color: 'var(--accent)' }} />
                        Ayarlar
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-xl transition-all hover:scale-110 cursor-pointer"
                        style={{ color: 'var(--text-secondary)', background: 'var(--accent-pastel)' }}
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6 max-h-[60vh] overflow-y-auto">
                    {/* Username */}
                    <div>
                        <label className="text-sm font-semibold mb-2.5 flex items-center gap-2 block" style={{ color: 'var(--text-primary)' }}>
                            <User size={16} style={{ color: 'var(--accent)' }} />
                            Kullanıcı Adı
                        </label>
                        <input
                            type="text"
                            value={localName}
                            onChange={(e) => setLocalName(e.target.value)}
                            placeholder="İsmini gir..."
                            className="w-full px-4 py-3 rounded-2xl outline-none text-sm transition-all focus:ring-2 focus:ring-purple-400"
                            style={{
                                background: 'var(--bg-main)',
                                color: 'var(--text-primary)',
                                border: '1px solid var(--border-color)',
                            }}
                        />
                    </div>

                    {/* Provider */}
                    <div>
                        <label className="text-sm font-semibold mb-2.5 block" style={{ color: 'var(--text-primary)' }}>
                            Zeka Sağlayıcısı
                        </label>
                        <div className="grid grid-cols-2 gap-3">
                            {[
                                { value: 'gemini', label: 'Google Gemini', icon: Cloud, desc: 'Bulut' },
                                { value: 'ollama', label: 'Ollama', icon: Server, desc: 'Yerel' },
                            ].map((opt) => (
                                <button
                                    key={opt.value}
                                    onClick={() => setLocal({ ...local, provider: opt.value })}
                                    className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 transition-all duration-200 cursor-pointer ${local.provider === opt.value ? 'scale-[1.02]' : ''
                                        }`}
                                    style={{
                                        borderColor: local.provider === opt.value ? 'var(--accent)' : 'var(--border-color)',
                                        background: local.provider === opt.value ? 'var(--accent-pastel)' : 'var(--bg-main)',
                                    }}
                                >
                                    <opt.icon size={24} style={{ color: local.provider === opt.value ? 'var(--accent)' : 'var(--text-secondary)' }} />
                                    <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{opt.label}</span>
                                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{opt.desc}</span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Model */}
                    <div>
                        <label className="text-sm font-semibold mb-2.5 block" style={{ color: 'var(--text-primary)' }}>
                            Model
                        </label>
                        <select
                            value={local.model}
                            onChange={(e) => setLocal({ ...local, model: e.target.value })}
                            className="w-full px-4 py-3 rounded-2xl outline-none text-sm transition-colors cursor-pointer"
                            style={{
                                background: 'var(--bg-main)',
                                color: 'var(--text-primary)',
                                border: '1px solid var(--border-color)',
                            }}
                        >
                            {local.provider === 'gemini' ? (
                                <>
                                    <option value="gemini-2.5-flash">Gemini 2.5 Flash (Hızlı)</option>
                                    <option value="gemini-2.0-pro">Gemini 2.0 Pro (Gelişmiş)</option>
                                    <option value="gemini-1.5-flash">Gemini 1.5 Flash (Stabil)</option>
                                </>
                            ) : (
                                <>
                                    <option value="llama3.1">LLaMA 3.1</option>
                                    <option value="llama3.2">LLaMA 3.2</option>
                                    <option value="llama3">LLaMA 3</option>
                                    <option value="gpt-oss:120b-cloud">GPT-OSS 120B Cloud</option>
                                </>
                            )}
                        </select>
                    </div>

                    {/* Conditional Fields */}
                    {local.provider === 'gemini' && (
                        <div>
                            <label className="text-sm font-semibold mb-2.5 block" style={{ color: 'var(--text-primary)' }}>
                                Gemini API Key
                            </label>
                            <input
                                type="password"
                                value={local.apiKey}
                                onChange={(e) => setLocal({ ...local, apiKey: e.target.value })}
                                placeholder=".env'den otomatik okunur"
                                className="w-full px-4 py-3 rounded-2xl outline-none text-sm focus:ring-2 focus:ring-purple-400"
                                style={{
                                    background: 'var(--bg-main)',
                                    color: 'var(--text-primary)',
                                    border: '1px solid var(--border-color)',
                                }}
                            />
                        </div>
                    )}

                    {local.provider === 'ollama' && (
                        <div>
                            <label className="text-sm font-semibold mb-2.5 block" style={{ color: 'var(--text-primary)' }}>
                                Ollama Sunucu URL
                            </label>
                            <input
                                type="text"
                                value={local.ollamaHost}
                                onChange={(e) => setLocal({ ...local, ollamaHost: e.target.value })}
                                placeholder="http://localhost:11434"
                                className="w-full px-4 py-3 rounded-2xl outline-none text-sm focus:ring-2 focus:ring-purple-400"
                                style={{
                                    background: 'var(--bg-main)',
                                    color: 'var(--text-primary)',
                                    border: '1px solid var(--border-color)',
                                }}
                            />
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 p-6 pt-3 border-t" style={{ borderColor: 'var(--border-color)' }}>
                    <button
                        onClick={onClose}
                        className="px-6 py-3 rounded-2xl text-sm font-semibold transition-all cursor-pointer hover:scale-[1.02]"
                        style={{ color: 'var(--text-secondary)', background: 'var(--bg-main)' }}
                    >
                        İptal
                    </button>
                    <button
                        onClick={handleSave}
                        className="px-6 py-3 rounded-2xl text-sm font-semibold text-white transition-all hover:scale-[1.02] hover:shadow-lg cursor-pointer"
                        style={{ background: 'linear-gradient(135deg, #9333ea, #c084fc)' }}
                    >
                        Kaydet
                    </button>
                </div>
            </div>
        </div>
    );
}
