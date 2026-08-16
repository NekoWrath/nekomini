import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const TelegramContext = createContext(null);

export function TelegramProvider({ children }) {
  const [tg, setTg] = useState(null);
  const [isInsideTelegram, setIsInsideTelegram] = useState(false);
  const [initDataRaw, setInitDataRaw] = useState('');
  
  // Dev Mock State (for testing in standard browser outside Telegram)
  const [mockUser, setMockUser] = useState({
    id: 123456789,
    first_name: 'Streamer Legend',
    last_name: '🔥',
    username: 'streamer_boss',
    photo_url: 'https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150&auto=format&fit=crop&q=80',
    role: 'admin', // 'admin', 'moderator', 'viewer'
  });

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    if (webApp && webApp.initData) {
      setTg(webApp);
      setIsInsideTelegram(true);
      setInitDataRaw(webApp.initData);

      // Configure Telegram WebApp UI
      try {
        webApp.ready();
        webApp.expand();
        if (webApp.setHeaderColor) webApp.setHeaderColor('#090d16');
        if (webApp.setBackgroundColor) webApp.setBackgroundColor('#090d16');
        if (webApp.enableClosingConfirmation) webApp.enableClosingConfirmation();
      } catch (err) {
        console.warn('Telegram WebApp setup error:', err);
      }
    } else {
      setIsInsideTelegram(false);
      // Dev mode: use simulated user
    }
  }, []);

  // Haptic feedback helpers
  const hapticImpact = useCallback((style = 'medium') => {
    try {
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred(style);
      }
    } catch (e) {
      // Ignored outside Telegram
    }
  }, []);

  const hapticNotification = useCallback((type = 'success') => {
    try {
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred(type);
      }
    } catch (e) {
      // Ignored outside Telegram
    }
  }, []);

  const hapticSelection = useCallback(() => {
    try {
      if (window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.selectionChanged();
      }
    } catch (e) {
      // Ignored outside Telegram
    }
  }, []);

  // Telegram MainButton control
  const setMainButton = useCallback(({ text, onClick, isVisible = true, color = '#8b5cf6', textColor = '#ffffff' }) => {
    const mb = window.Telegram?.WebApp?.MainButton;
    if (mb) {
      if (text) mb.setText(text);
      if (color) mb.setParams({ color, text_color: textColor });
      if (onClick) {
        mb.offClick(); // clear previous
        mb.onClick(onClick);
      }
      if (isVisible) mb.show();
      else mb.hide();
    }
  }, []);

  const hideMainButton = useCallback(() => {
    const mb = window.Telegram?.WebApp?.MainButton;
    if (mb) {
      mb.hide();
      mb.offClick();
    }
  }, []);

  const openLink = useCallback((url) => {
    if (window.Telegram?.WebApp?.openLink) {
      window.Telegram.WebApp.openLink(url);
    } else {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }, []);

  const openTelegramLink = useCallback((url) => {
    if (window.Telegram?.WebApp?.openTelegramLink) {
      window.Telegram.WebApp.openTelegramLink(url);
    } else {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }, []);

  const switchMockRole = (role) => {
    setMockUser((prev) => ({
      ...prev,
      role,
      id: role === 'admin' ? 123456789 : 987654321,
      first_name: role === 'admin' ? 'Streamer Legend' : 'Viewer Alex',
      username: role === 'admin' ? 'streamer_boss' : 'gamer_alex',
    }));
  };

  const value = {
    tg,
    isInsideTelegram,
    initDataRaw,
    mockUser,
    switchMockRole,
    hapticImpact,
    hapticNotification,
    hapticSelection,
    setMainButton,
    hideMainButton,
    openLink,
    openTelegramLink,
  };

  return (
    <TelegramContext.Provider value={value}>
      {children}
    </TelegramContext.Provider>
  );
}

export function useTelegram() {
  const context = useContext(TelegramContext);
  if (!context) {
    throw new Error('useTelegram must be used within a TelegramProvider');
  }
  return context;
}
