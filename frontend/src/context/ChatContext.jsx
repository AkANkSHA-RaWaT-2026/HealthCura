import { useState } from 'react';
import { ChatContext } from './ChatContextObject';
import { useAuth } from '../hooks/useAuth';

export function ChatProvider({ children }) {
  const { user } = useAuth();
  const userId = user?.id ?? null;

  // Messages are stored with the id of the user they belong to. If a different
  // user logs in, the stored owner no longer matches and the old messages are hidden,
  // so no effect is needed to reset them.
  const [chat, setChat] = useState({ owner: userId, messages: [] });

  const messages = chat.owner === userId ? chat.messages : [];

  const setMessages = (update) => {
    setChat((prev) => {
      const currentMessages = prev.owner === userId ? prev.messages : [];
      const nextMessages = typeof update === 'function' ? update(currentMessages) : update;
      return { owner: userId, messages: nextMessages };
    });
  };

  return (
    <ChatContext.Provider value={{ messages, setMessages }}>
      {children}
    </ChatContext.Provider>
  );
}