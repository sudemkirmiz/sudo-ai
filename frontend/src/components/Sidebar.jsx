import { useState } from 'react';
import {
    MessageSquarePlus,
    MessagesSquare,
    Settings,
    Search,
    Moon,
    Sun,
    Trash2,
} from 'lucide-react';

export default function Sidebar({
    chats,
    activeChatId,
    onSelectChat,
    onNewChat,
    onDeleteChat,
    onOpenSettings,
    darkMode,
    onToggleDark,
}) {
    const [searchQuery, setSearchQuery] = useState('');
    const [confirmDeleteId, setConfirmDeleteId] = useState(null);

    const filteredChats = chats.filter((c) =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleDeleteClick = (e, chatId) => {
        e.stopPropagation();
        setConfirmDeleteId(chatId);
    };

    const handleConfirmDelete = (e) => {
        e.stopPropagation();
        if (confirmDeleteId) {
            onDeleteChat(confirmDeleteId);
            setConfirmDeleteId(null);
        }
    };

    const handleCancelDelete = (e) => {
        e.stopPropagation();
        setConfirmDeleteId(null);
    };

    return (
        <aside
            className="flex flex-col h-full w-[320px] min-w-[320px] border-r transition-colors duration-300"
            style={{
                background: 'var(--bg-sidebar)',
                borderColor: 'var(--border-color)',
            }}
        >
            {/* Logo + Dark Toggle */}
            <div className="p-6 pb-4">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div
                            className="w-11 h-11 rounded-2xl flex items-center justify-center text-white font-bold text-lg shadow-md"
                            style={{ background: 'linear-gradient(135deg, #9333ea, #c084fc)' }}
                        >
                            S
                        </div>
                        <span className="text-xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                            Sudo AI
                        </span>
                    </div>
                    <button
                        onClick={onToggleDark}
                        className="p-2.5 rounded-xl transition-all duration-200 hover:scale-110 cursor-pointer"
                        style={{ color: 'var(--text-secondary)', background: 'var(--accent-pastel)' }}
                        title={darkMode ? 'Aydınlık Mod' : 'Karanlık Mod'}
                    >
                        {darkMode ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                </div>

                {/* New Chat Button */}
                <button
                    onClick={onNewChat}
                    className="w-full flex items-center justify-center gap-3 px-5 py-3 rounded-2xl text-white font-semibold text-sm transition-all duration-200 hover:scale-[1.02] hover:shadow-lg cursor-pointer"
                    style={{ background: 'linear-gradient(135deg, #9333ea, #c084fc)' }}
                >
                    <MessageSquarePlus size={20} />
                    Yeni Sohbet
                </button>
            </div>

            {/* Search */}
            <div className="px-6 pb-4">
                <div
                    className="flex items-center gap-3 px-4 py-3 rounded-2xl transition-colors"
                    style={{ background: 'var(--bg-main)', border: '1px solid var(--border-color)' }}
                >
                    <Search size={18} style={{ color: 'var(--text-secondary)' }} />
                    <input
                        type="text"
                        placeholder="Sohbet ara..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="flex-1 bg-transparent outline-none text-sm"
                        style={{ color: 'var(--text-primary)' }}
                    />
                </div>
            </div>

            {/* Chat List */}
            <div className="flex-1 overflow-y-auto px-4">
                <p
                    className="text-xs uppercase font-semibold tracking-wider px-3 mb-3"
                    style={{ color: 'var(--text-secondary)' }}
                >
                    Son Sohbetler
                </p>
                {filteredChats.length === 0 ? (
                    <p className="text-xs px-3 py-6 text-center" style={{ color: 'var(--text-secondary)' }}>
                        {searchQuery ? 'Sonuç bulunamadı' : 'Henüz sohbet yok'}
                    </p>
                ) : (
                    filteredChats.map((chat) => (
                        <div key={chat.id} className="relative mb-1.5">
                            {/* Confirm Delete Overlay */}
                            {confirmDeleteId === chat.id && (
                                <div
                                    className="absolute inset-0 z-10 flex items-center justify-center gap-2 rounded-2xl backdrop-blur-sm"
                                    style={{ background: 'rgba(147, 51, 234, 0.12)' }}
                                >
                                    <span className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                                        Silinsin mi?
                                    </span>
                                    <button
                                        onClick={handleConfirmDelete}
                                        className="px-3 py-1 rounded-lg text-xs font-semibold text-white cursor-pointer transition-all hover:scale-105"
                                        style={{ background: '#ef4444' }}
                                    >
                                        Evet
                                    </button>
                                    <button
                                        onClick={handleCancelDelete}
                                        className="px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-all hover:scale-105"
                                        style={{ color: 'var(--text-secondary)', background: 'var(--bg-main)' }}
                                    >
                                        İptal
                                    </button>
                                </div>
                            )}

                            <button
                                onClick={() => onSelectChat(chat.id)}
                                className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-2xl text-left text-sm transition-all duration-150 cursor-pointer group ${activeChatId === chat.id ? 'font-semibold' : ''
                                    }`}
                                style={{
                                    background: activeChatId === chat.id ? 'var(--accent-pastel)' : 'transparent',
                                    color: activeChatId === chat.id ? 'var(--accent)' : 'var(--text-primary)',
                                }}
                            >
                                <MessagesSquare
                                    size={20}
                                    className="flex-shrink-0"
                                    style={{
                                        color: activeChatId === chat.id ? 'var(--accent)' : 'var(--text-secondary)',
                                    }}
                                />
                                <span className="truncate flex-1">{chat.title}</span>
                                {/* Trash icon — appears on hover */}
                                <span
                                    onClick={(e) => handleDeleteClick(e, chat.id)}
                                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg transition-all duration-200 hover:scale-110 hover:bg-red-100 flex-shrink-0"
                                    style={{ color: '#ef4444' }}
                                    title="Sohbeti Sil"
                                >
                                    <Trash2 size={15} />
                                </span>
                            </button>
                        </div>
                    ))
                )}
            </div>

            {/* Bottom — Settings */}
            <div className="p-5 border-t" style={{ borderColor: 'var(--border-color)' }}>
                <button
                    onClick={onOpenSettings}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all duration-200 hover:scale-[1.02] cursor-pointer"
                    style={{ color: 'var(--text-secondary)', background: 'var(--bg-main)' }}
                >
                    <Settings size={20} />
                    Ayarlar
                </button>
            </div>
        </aside>
    );
}
