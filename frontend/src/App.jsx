import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import SettingsModal from './components/SettingsModal';
import WelcomeScreen from './components/WelcomeScreen';
import ChatArea from './components/ChatArea';
import ChatInput from './components/ChatInput';
import { createChat, listChats, getChatHistory, sendMessageSSE, deleteChat, uploadFile } from './services/api';

const DEFAULT_SETTINGS = {
  provider: 'gemini',
  model: 'gemini-2.5-flash',
  apiKey: '',
  ollamaHost: 'http://localhost:11434',
};

export default function App() {
  // Username from localStorage
  const [username, setUsername] = useState(() => localStorage.getItem('sudo_username') || '');
  const [darkMode, setDarkMode] = useState(false);
  const [chats, setChats] = useState([]);
  const [activeChatId, setActiveChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [toolNotification, setToolNotification] = useState(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('sudo-ai-settings');
    return saved ? JSON.parse(saved) : DEFAULT_SETTINGS;
  });

  // Dark mode class
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  // Load chats on mount (only if username is set)
  useEffect(() => {
    if (username) loadChats();
  }, [username]);

  const handleSetUsername = (name) => {
    localStorage.setItem('sudo_username', name);
    setUsername(name);
  };

  const loadChats = async () => {
    try {
      const data = await listChats();
      setChats(data);
    } catch (err) {
      console.error('Sohbetler yüklenemedi:', err);
    }
  };

  const handleNewChat = async () => {
    try {
      const chat = await createChat('Yeni Sohbet');
      setChats((prev) => [chat, ...prev]);
      setActiveChatId(chat.id);
      setMessages([]);
    } catch (err) {
      console.error('Sohbet oluşturulamadı:', err);
    }
  };

  const handleSelectChat = async (chatId) => {
    setActiveChatId(chatId);
    try {
      const data = await getChatHistory(chatId);
      setMessages(data.messages.filter((m) => m.role !== 'system'));
    } catch (err) {
      console.error('Mesajlar alınamadı:', err);
    }
  };

  const handleDeleteChat = async (chatId) => {
    try {
      await deleteChat(chatId);
      setChats((prev) => prev.filter((c) => c.id !== chatId));
      if (activeChatId === chatId) {
        setActiveChatId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Sohbet silinemedi:', err);
    }
  };

  const handleSendMessage = useCallback(
    async (content) => {
      let chatId = activeChatId;
      if (!chatId) {
        try {
          const chat = await createChat('Yeni Sohbet');
          setChats((prev) => [chat, ...prev]);
          chatId = chat.id;
          setActiveChatId(chatId);
        } catch (err) {
          console.error('Sohbet oluşturulamadı:', err);
          return;
        }
      }

      const userMsg = { role: 'user', content };
      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
      setStreamingText('');
      setToolNotification(null);

      try {
        await sendMessageSSE(chatId, content, settings, (eventType, data) => {
          switch (eventType) {
            case 'tool_call':
              setToolNotification(`Sudo AI ${data.tool} aracına erişiyor...`);
              break;
            case 'tool_result':
              setTimeout(() => setToolNotification(null), 1500);
              break;
            case 'token':
              setStreamingText((prev) => prev + data.content);
              break;
            case 'done': {
              const fullContent = data.full_content || '';
              setMessages((prev) => [...prev, { role: 'assistant', content: fullContent }]);
              setStreamingText('');
              setIsStreaming(false);
              setToolNotification(null);
              loadChats();
              break;
            }
            case 'error':
              setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: `⚠️ ${data.message}` },
              ]);
              setStreamingText('');
              setIsStreaming(false);
              setToolNotification(null);
              break;
          }
        });
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `⚠️ Bir hata oluştu: ${err.message}` },
        ]);
        setStreamingText('');
        setIsStreaming(false);
        setToolNotification(null);
      }
    },
    [activeChatId, settings]
  );

  const handleSaveSettings = (newSettings) => {
    setSettings(newSettings);
    localStorage.setItem('sudo-ai-settings', JSON.stringify(newSettings));
  };

  // Quick action handler for organizer buttons
  const handleQuickAction = useCallback(
    async (type, messageContent) => {
      const prompts = {
        docs: `Lütfen bir önceki mesajındaki tüm planı/metni Google Docs aracıyla yeni bir dokümana kaydet. İçerik:\n\n${messageContent}`,
        calendar: `Lütfen bir önceki mesajındaki etkinlikleri/randevuları Google Takvim'e ekle. İçerik:\n\n${messageContent}`,
      };
      const prompt = prompts[type];
      if (prompt) await handleSendMessage(prompt);
    },
    [handleSendMessage]
  );

  // File upload handler
  const handleUpload = useCallback(async (chatId, file) => {
    return uploadFile(chatId, file);
  }, []);

  const hasMessages = messages.length > 0 || isStreaming;

  // ===== ONBOARDING SCREEN — No username yet =====
  if (!username) {
    return <OnboardingScreen onSetUsername={handleSetUsername} />;
  }

  // ===== MAIN APP =====
  return (
    <div
      className="flex w-full h-[95vh] max-w-[1400px] rounded-3xl overflow-hidden"
      style={{
        background: 'var(--bg-main)',
        boxShadow: '0 25px 60px rgba(0,0,0,0.12), 0 0 0 1px rgba(147,51,234,0.06)',
      }}
    >
      {/* Sidebar */}
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onOpenSettings={() => setSettingsOpen(true)}
        darkMode={darkMode}
        onToggleDark={() => setDarkMode((d) => !d)}
      />

      {/* Main Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden" style={{ background: 'var(--bg-main)' }}>
        {hasMessages ? (
          <>
            {/* Chat Header */}
            <div
              className="px-8 py-4 border-b flex items-center"
              style={{ borderColor: 'var(--border-color)' }}
            >
              <h2 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                {chats.find((c) => c.id === activeChatId)?.title || 'Sohbet'}
              </h2>
            </div>

            <ChatArea
              messages={messages}
              isStreaming={isStreaming}
              streamingText={streamingText}
              toolNotification={toolNotification}
              onQuickAction={handleQuickAction}
            />
          </>
        ) : (
          <WelcomeScreen username={username} />
        )}

        <ChatInput onSend={handleSendMessage} onUpload={handleUpload} disabled={isStreaming} activeChatId={activeChatId} />

        {/* App Footer Inside Main Area */}
        <div className="pb-4 text-center text-[11px] font-medium" style={{ color: 'var(--text-secondary)' }}>
          Sudo AI, Google Workspace araçlarınıza güvenli erişim sağlar.
        </div>
      </main>

      {/* Settings Modal */}
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        onSave={handleSaveSettings}
        username={username}
        onChangeUsername={handleSetUsername}
      />
    </div>
  );
}

// ===== ONBOARDING COMPONENT =====
function OnboardingScreen({ onSetUsername }) {
  const [name, setName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (trimmed) onSetUsername(trimmed);
  };

  return (
    <div className="flex items-center justify-center w-full h-[95vh]">
      <div
        className="w-full max-w-md rounded-3xl p-10 text-center animate-fade-in-up"
        style={{
          background: 'var(--bg-main)',
          boxShadow: '0 25px 60px rgba(0,0,0,0.12), 0 0 0 1px rgba(147,51,234,0.06)',
        }}
      >
        {/* Logo */}
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-6"
          style={{ background: 'linear-gradient(135deg, #9333ea, #c084fc)' }}
        >
          S
        </div>

        <h1
          className="text-3xl font-extrabold mb-2 bg-clip-text text-transparent"
          style={{ backgroundImage: 'linear-gradient(135deg, #9333ea, #f472b6, #c084fc)' }}
        >
          Sudo AI
        </h1>
        <p className="text-base mb-8" style={{ color: 'var(--text-secondary)' }}>
          Hoş geldin! Sana nasıl hitap edebilirim?
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="İsmini gir..."
            autoFocus
            className="w-full px-5 py-3.5 rounded-2xl outline-none text-center text-base font-medium transition-all focus:ring-2 focus:ring-purple-400"
            style={{
              background: 'var(--accent-pastel)',
              color: 'var(--text-primary)',
              border: '1.5px solid var(--border-color)',
            }}
          />
          <button
            type="submit"
            disabled={!name.trim()}
            className="w-full py-3.5 rounded-2xl text-white font-semibold text-base transition-all hover:scale-[1.02] hover:shadow-lg disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            style={{ background: 'linear-gradient(135deg, #9333ea, #c084fc)' }}
          >
            Başlayalım →
          </button>
        </form>
      </div>
    </div>
  );
}
