import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { SuggestionCard } from '../components/SuggestionCard';
import { AdminReplyModal } from '../components/AdminReplyModal';
import { StreamEditorModal } from '../components/StreamEditorModal';
import { BroadcastModal } from '../components/BroadcastModal';
import { StreamCard } from '../components/StreamCard';
import {
  Shield,
  Users,
  Lightbulb,
  Calendar,
  Radio,
  Plus,
  Megaphone,
  CheckCircle,
  Clock,
  Sparkles,
  Layers,
  Flame,
} from 'lucide-react';

export function AdminPage() {
  const {
    currentUser,
    adminStats,
    suggestions,
    streams,
    deleteSuggestion,
    deleteStream,
    toggleStreamLive,
    fetchAdminStats,
  } = useApp();

  const [adminSubTab, setAdminSubTab] = useState('moderation'); // 'moderation' | 'streams' | 'broadcast'
  const [moderatingSuggestion, setModeratingSuggestion] = useState(null);
  const [editingStream, setEditingStream] = useState(null);
  const [isStreamModalOpen, setIsStreamModalOpen] = useState(false);
  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState(false);

  const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'moderator';

  useEffect(() => {
    fetchAdminStats();
  }, [fetchAdminStats]);

  if (!isAdmin) {
    return (
      <div className="p-8 text-center text-slate-400">
        <Shield className="w-12 h-12 text-rose-500/50 mx-auto mb-3" />
        <h3 className="text-base font-bold text-white">Доступ ограничен</h3>
        <p className="text-xs text-slate-500 mt-1">
          Эта панель доступна только стримеру и модераторам.
        </p>
      </div>
    );
  }

  // Filter pending suggestions for moderation tab
  const pendingSuggestions = suggestions.filter((s) => s.status === 'pending');

  return (
    <div className="pb-24 pt-3 px-4 space-y-4">
      {/* Top Admin Header */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-950 via-slate-900 to-indigo-950 border border-purple-500/40 shadow-glow-purple">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-purple-400" />
            <h3 className="font-display font-extrabold text-base text-white">
              Панель управления Стримера
            </h3>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-500/20 text-rose-300 border border-rose-500/40">
            {currentUser.role.toUpperCase()}
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-2">
          <div className="bg-slate-950/70 border border-purple-500/20 rounded-xl p-2 text-center">
            <div className="text-xs text-slate-400 flex items-center justify-center gap-1">
              <Users className="w-3 h-3 text-purple-400" />
              <span>Зрители</span>
            </div>
            <div className="font-display font-extrabold text-sm text-white mt-0.5">
              {adminStats?.users_count || 0}
            </div>
          </div>

          <div className="bg-slate-950/70 border border-purple-500/20 rounded-xl p-2 text-center">
            <div className="text-xs text-slate-400 flex items-center justify-center gap-1">
              <Clock className="w-3 h-3 text-amber-400" />
              <span>На модерации</span>
            </div>
            <div className="font-display font-extrabold text-sm text-amber-400 mt-0.5">
              {adminStats?.pending_suggestions || 0}
            </div>
          </div>

          <div className="bg-slate-950/70 border border-purple-500/20 rounded-xl p-2 text-center">
            <div className="text-xs text-slate-400 flex items-center justify-center gap-1">
              <Calendar className="w-3 h-3 text-cyan-400" />
              <span>Стримы</span>
            </div>
            <div className="font-display font-extrabold text-sm text-white mt-0.5">
              {adminStats?.total_streams || 0}
            </div>
          </div>

          <div className="bg-slate-950/70 border border-purple-500/20 rounded-xl p-2 text-center">
            <div className="text-xs text-slate-400 flex items-center justify-center gap-1">
              <Flame className="w-3 h-3 text-rose-400" />
              <span>Голоса</span>
            </div>
            <div className="font-display font-extrabold text-sm text-white mt-0.5">
              {adminStats?.total_votes || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Admin Sub-Tabs */}
      <div className="grid grid-cols-3 gap-1 p-1 bg-slate-900/90 border border-slate-800 rounded-2xl">
        <button
          onClick={() => setAdminSubTab('moderation')}
          className={`py-2 px-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 btn-press ${
            adminSubTab === 'moderation'
              ? 'bg-purple-600 text-white shadow-glow-purple'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Lightbulb className="w-3.5 h-3.5" />
          <span>Предложка</span>
          {pendingSuggestions.length > 0 && (
            <span className="w-4 h-4 rounded-full bg-amber-500 text-slate-950 text-[10px] flex items-center justify-center font-extrabold">
              {pendingSuggestions.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setAdminSubTab('streams')}
          className={`py-2 px-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 btn-press ${
            adminSubTab === 'streams'
              ? 'bg-purple-600 text-white shadow-glow-purple'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Расписание</span>
        </button>

        <button
          onClick={() => setAdminSubTab('broadcast')}
          className={`py-2 px-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 btn-press ${
            adminSubTab === 'broadcast'
              ? 'bg-rose-600 text-white shadow-glow-live'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Megaphone className="w-3.5 h-3.5" />
          <span>Рассылка</span>
        </button>
      </div>

      {/* SUB-TAB 1: MODERATION */}
      {adminSubTab === 'moderation' && (
        <div className="space-y-3.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300">
              Ожидают решения ({pendingSuggestions.length})
            </span>
          </div>

          {pendingSuggestions.length > 0 ? (
            pendingSuggestions.map((item) => (
              <SuggestionCard
                key={item.id}
                suggestion={item}
                onModerate={(sug) => setModeratingSuggestion(sug)}
                onDelete={(id) => deleteSuggestion(id)}
              />
            ))
          ) : (
            <div className="p-8 rounded-2xl glass-panel text-center border border-white/5">
              <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-300">Все предложения обработаны!</h4>
              <p className="text-xs text-slate-500 mt-1">
                Новые идеи от зрителей появятся здесь автоматически.
              </p>
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 2: STREAMS MANAGEMENT */}
      {adminSubTab === 'streams' && (
        <div className="space-y-3.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300">
              Управление трансляциями
            </span>
            <button
              onClick={() => {
                setEditingStream(null);
                setIsStreamModalOpen(true);
              }}
              className="flex items-center gap-1 px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-glow-purple transition-all btn-press"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Создать стрим</span>
            </button>
          </div>

          <div className="space-y-3.5">
            {streams.map((stream) => (
              <StreamCard
                key={stream.id}
                stream={stream}
                onEdit={(s) => {
                  setEditingStream(s);
                  setIsStreamModalOpen(true);
                }}
                onDelete={(id) => deleteStream(id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* SUB-TAB 3: BROADCAST */}
      {adminSubTab === 'broadcast' && (
        <div className="space-y-4">
          <div className="p-5 rounded-2xl glass-panel-elevated border-rose-500/30 text-center space-y-3">
            <Megaphone className="w-10 h-10 text-rose-400 mx-auto" />
            <h4 className="font-display font-bold text-base text-white">
              Мгновенный анонс по всей аудитории
            </h4>
            <p className="text-xs text-slate-300 max-w-xs mx-auto leading-relaxed">
              Отправь пуш-уведомление всем подписчикам Telegram бота. Идеально для внезапного запуска стрима или важной новости!
            </p>
            <button
              onClick={() => setIsBroadcastModalOpen(true)}
              className="px-6 py-3 rounded-2xl bg-gradient-to-r from-rose-600 to-pink-600 text-white font-display font-bold text-sm shadow-glow-live hover:brightness-110 transition-all btn-press inline-flex items-center gap-2"
            >
              <Megaphone className="w-4 h-4" />
              <span>Создать рассылку</span>
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      <AdminReplyModal
        suggestion={moderatingSuggestion}
        isOpen={!!moderatingSuggestion}
        onClose={() => setModeratingSuggestion(null)}
      />

      <StreamEditorModal
        stream={editingStream}
        isOpen={isStreamModalOpen}
        onClose={() => {
          setIsStreamModalOpen(false);
          setEditingStream(null);
        }}
      />

      <BroadcastModal
        isOpen={isBroadcastModalOpen}
        onClose={() => setIsBroadcastModalOpen(false)}
      />
    </div>
  );
}
