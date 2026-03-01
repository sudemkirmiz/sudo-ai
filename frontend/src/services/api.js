/**
 * Sudo AI — API Service
 * FastAPI backend ile iletişim katmanı.
 */

const API_BASE = '/api';

// ===== Chat CRUD =====

export async function createChat(title = 'Yeni Sohbet') {
    const res = await fetch(`${API_BASE}/chats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Sohbet oluşturulamadı');
    return res.json();
}

export async function listChats() {
    const res = await fetch(`${API_BASE}/chats`);
    if (!res.ok) throw new Error('Sohbetler alınamadı');
    return res.json();
}

export async function getChatHistory(chatId) {
    const res = await fetch(`${API_BASE}/chats/${chatId}`);
    if (!res.ok) throw new Error('Mesajlar alınamadı');
    return res.json();
}

export async function deleteChat(chatId) {
    const res = await fetch(`${API_BASE}/chats/${chatId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Sohbet silinemedi');
    return res.json();
}

export async function uploadFile(chatId, file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chat_id', chatId);
    const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Dosya yüklenemedi');
    }
    return res.json();
}

// ===== SSE Message Stream =====

export function sendMessageSSE(chatId, content, settings, onEvent) {
    const body = {
        content,
        provider: settings.provider || 'gemini',
        model: settings.model || null,
        api_key: settings.apiKey || null,
        ollama_host: settings.ollamaHost || 'http://localhost:11434',
    };

    return new Promise((resolve, reject) => {
        fetch(`${API_BASE}/chats/${chatId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        })
            .then((res) => {
                if (!res.ok) {
                    return res.json().then((err) => {
                        reject(new Error(err.detail || 'Mesaj gönderilemedi'));
                    });
                }

                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                function read() {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            resolve();
                            return;
                        }

                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\n');
                        buffer = lines.pop() || '';

                        let eventType = '';
                        for (const line of lines) {
                            if (line.startsWith('event: ')) {
                                eventType = line.slice(7).trim();
                            } else if (line.startsWith('data: ')) {
                                const dataStr = line.slice(6);
                                try {
                                    const data = JSON.parse(dataStr);
                                    onEvent(eventType, data);
                                } catch {
                                    // skip invalid JSON
                                }
                            }
                        }

                        read();
                    }).catch(reject);
                }

                read();
            })
            .catch(reject);
    });
}
