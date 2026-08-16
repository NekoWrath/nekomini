import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useTelegram } from './TelegramContext';
import { api } from '../services/api';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const { initDataRaw, mockUser, hapticImpact, hapticNotification, hapticSelection } = useTelegram();

  // Active Tab: 'schedule' | 'suggestions' | 'settings' | 'admin'
  const [activeTab, setActiveTab] = useState('schedule');

  // Core Data
  const [currentUser, setCurrentUser] = useState(null);
  const [streamerInfo, setStreamerInfo] = useState(null);
  const [streams, setStreams] = useState([]);
  const [currentStream, setCurrentStream] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [adminStats, setAdminStats] = useState(null);

  // Filters
  const [suggestionTab, setSuggestionTab] = useState('new');
  const [suggestionCategory, setSuggestionCategory] = useState('all');
  const [suggestionSearch, setSuggestionSearch] = useState('');

  // Loading & Toast States
  const [loading, setLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = useCallback((text, type = 'info') => {
    setToastMessage({ text, type });
    if (type === 'success') hapticNotification('success');
    else if (type === 'error') hapticNotification('error');
    else hapticImpact('light');

    setTimeout(() => {
      setToastMessage(null);
    }, 3500);
  }, [hapticNotification, hapticImpact]);

  // Load User & Meta
  const fetchUser = useCallback(async () => {
    try {
      const data = await api.getMe(initDataRaw, mockUser);
      setCurrentUser(data);
      if (data.streamer_info) {
        setStreamerInfo(data.streamer_info);
      }
    } catch (err) {
      console.warn('Failed to load user info:', err);
    }
  }, [initDataRaw, mockUser]);

  // Load Schedule
  const fetchStreams = useCallback(async () => {
    try {
      const [streamsData, currentData] = await Promise.all([
        api.getStreams(initDataRaw, mockUser),
        api.getCurrentStream(initDataRaw, mockUser),
      ]);
      setStreams(streamsData);
      setCurrentStream(currentData);
    } catch (err) {
      console.warn('Failed to load streams:', err);
    }
  }, [initDataRaw, mockUser]);

  // Load Suggestions
  const fetchSuggestions = useCallback(async () => {
    try {
      const data = await api.getSuggestions(
        initDataRaw,
        mockUser,
        suggestionTab,
        suggestionCategory,
        suggestionSearch
      );
      setSuggestions(data);
    } catch (err) {
      console.warn('Failed to load suggestions:', err);
    }
  }, [initDataRaw, mockUser, suggestionTab, suggestionCategory, suggestionSearch]);

  // Load Admin Stats if admin
  const fetchAdminStats = useCallback(async () => {
    if (currentUser?.role === 'admin' || currentUser?.role === 'moderator') {
      try {
        const stats = await api.getAdminStats(initDataRaw, mockUser);
        setAdminStats(stats);
      } catch (err) {
        console.warn('Failed to load admin stats:', err);
      }
    }
  }, [initDataRaw, mockUser, currentUser?.role]);

  // Initial Load & Reload on mockUser change
  useEffect(() => {
    let isMounted = true;
    async function init() {
      setLoading(true);
      await fetchUser();
      await Promise.all([fetchStreams(), fetchSuggestions()]);
      if (isMounted) setLoading(false);
    }
    init();
    return () => { isMounted = false; };
  }, [fetchUser, fetchStreams, fetchSuggestions]);

  // Refetch suggestions when filters change
  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  // Refetch admin stats when navigating to admin tab
  useEffect(() => {
    if (activeTab === 'admin') {
      fetchAdminStats();
    }
  }, [activeTab, fetchAdminStats]);

  // Tab switcher with haptic feedback
  const switchTab = (tab) => {
    if (tab !== activeTab) {
      hapticSelection();
      setActiveTab(tab);
    }
  };

  // Actions: Toggle Stream Reminder
  const toggleStreamReminder = async (streamId) => {
    hapticImpact('medium');
    try {
      const res = await api.toggleReminder(streamId, initDataRaw, mockUser);
      // Optimistic update
      setStreams((prev) =>
        prev.map((s) => (s.id === streamId ? { ...s, has_reminder: res.has_reminder } : s))
      );
      if (currentStream?.id === streamId) {
        setCurrentStream((prev) => ({ ...prev, has_reminder: res.has_reminder }));
      }
      showToast(res.message, 'success');
    } catch (err) {
      showToast('Ошибка при переключении напоминания', 'error');
    }
  };

  // Actions: Upvote Suggestion
  const voteSuggestion = async (suggestionId) => {
    hapticImpact('medium');
    try {
      const res = await api.voteSuggestion(suggestionId, initDataRaw, mockUser);
      setSuggestions((prev) =>
        prev.map((s) =>
          s.id === suggestionId
            ? { ...s, has_voted: res.has_voted, upvotes_count: res.upvotes_count }
            : s
        )
      );
    } catch (err) {
      showToast('Не удалось проголосовать', 'error');
    }
  };

  // Actions: Create Suggestion
  const submitSuggestion = async (data) => {
    try {
      const newSug = await api.createSuggestion(data, initDataRaw, mockUser);
      setSuggestions((prev) => [newSug, ...prev]);
      showToast('Идея успешно отправлена!', 'success');
      return true;
    } catch (err) {
      showToast('Не удалось отправить идею', 'error');
      return false;
    }
  };

  // Actions: Moderate Suggestion (Admin)
  const moderateSuggestion = async (suggestionId, { status, admin_reply }) => {
    hapticImpact('medium');
    try {
      const updated = await api.moderateSuggestion(
        suggestionId,
        { status, admin_reply },
        initDataRaw,
        mockUser
      );
      setSuggestions((prev) =>
        prev.map((s) => (s.id === suggestionId ? updated : s))
      );
      showToast('Статус обновлен, автор уведомлен в ЛС!', 'success');
      fetchAdminStats();
      return true;
    } catch (err) {
      showToast('Ошибка при модерации', 'error');
      return false;
    }
  };

  // Actions: Delete Suggestion
  const deleteSuggestion = async (suggestionId) => {
    hapticImpact('medium');
    try {
      await api.deleteSuggestion(suggestionId, initDataRaw, mockUser);
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
      showToast('Предложение удалено', 'info');
      fetchAdminStats();
      return true;
    } catch (err) {
      showToast('Не удалось удалить предложение', 'error');
      return false;
    }
  };

  // Actions: Create/Update/Delete Stream (Admin)
  const saveStream = async (streamData, editId = null) => {
    hapticImpact('medium');
    try {
      if (editId) {
        await api.updateStream(editId, streamData, initDataRaw, mockUser);
        showToast('Стрим обновлен!', 'success');
      } else {
        await api.createStream(streamData, initDataRaw, mockUser);
        showToast('Стрим добавлен в расписание!', 'success');
      }
      await fetchStreams();
      fetchAdminStats();
      return true;
    } catch (err) {
      showToast('Ошибка при сохранении стрима', 'error');
      return false;
    }
  };

  const deleteStream = async (streamId) => {
    hapticImpact('medium');
    try {
      await api.deleteStream(streamId, initDataRaw, mockUser);
      setStreams((prev) => prev.filter((s) => s.id !== streamId));
      if (currentStream?.id === streamId) setCurrentStream(null);
      showToast('Стрим удален', 'info');
      fetchAdminStats();
      return true;
    } catch (err) {
      showToast('Ошибка при удалении стрима', 'error');
      return false;
    }
  };

  const toggleStreamLive = async (streamId, sendBroadcast = false) => {
    hapticImpact('heavy');
    try {
      const res = await api.toggleLive(streamId, sendBroadcast, initDataRaw, mockUser);
      await fetchStreams();
      fetchAdminStats();
      const statusText = res.is_live ? '🔴 Стрим запущен в эфир!' : '⚪️ Стрим завершен';
      showToast(statusText, 'success');
      return res;
    } catch (err) {
      showToast('Ошибка при переключении статуса эфира', 'error');
      return null;
    }
  };

  // Actions: Update User Settings
  const updateUserSettings = async (newSettings) => {
    try {
      const updated = await api.updateSettings(newSettings, initDataRaw, mockUser);
      setCurrentUser(updated);
      showToast('Настройки сохранены', 'success');
      return true;
    } catch (err) {
      showToast('Не удалось сохранить настройки', 'error');
      return false;
    }
  };

  // Actions: Send Broadcast (Admin)
  const sendBroadcast = async (broadcastData) => {
    hapticImpact('heavy');
    try {
      const res = await api.sendBroadcast(broadcastData, initDataRaw, mockUser);
      showToast(res.message, 'success');
      return res;
    } catch (err) {
      showToast('Ошибка при отправке рассылки', 'error');
      return null;
    }
  };

  const value = {
    activeTab,
    switchTab,
    currentUser,
    streamerInfo,
    streams,
    currentStream,
    suggestions,
    adminStats,
    suggestionTab,
    setSuggestionTab,
    suggestionCategory,
    setSuggestionCategory,
    suggestionSearch,
    setSuggestionSearch,
    loading,
    toastMessage,
    showToast,
    fetchStreams,
    fetchSuggestions,
    fetchAdminStats,
    toggleStreamReminder,
    voteSuggestion,
    submitSuggestion,
    moderateSuggestion,
    deleteSuggestion,
    saveStream,
    deleteStream,
    toggleStreamLive,
    updateUserSettings,
    sendBroadcast,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
