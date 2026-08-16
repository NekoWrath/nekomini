import React from 'react';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../context/TelegramContext';
import {
  Bell,
  Radio,
  Megaphone,
  MessageCircle,
  Shield,
  User,
  Tv,
  Send,
  ExternalLink,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';

export function SettingsPage() {
  const { currentUser, updateUserSettings, streamerInfo } = useApp();
  const { openLink, openTelegramLink } = useTelegram();

  const handleToggle = (key) => {
    if (!currentUser) return;
    updateUserSettings({
      [key]: !currentUser[key],
    });
  };

  return (
    <div className="pb-24 pt-3 px-4 space-y-4">
      {/* User Profile Card */}
      <div className="p-4 rounded-2xl glass-panel-elevated border-purple-500/30">
        <div className="flex items-center gap-3.5">
          {currentUser?.photo_url ? (
            <img
              src={currentUser.photo_url}
              alt={currentUser.first_name}
              className="w-14 h-14 rounded-full object-cover border-2 border-purple-500/50 shadow-glow-purple"
            />
          ) : (
            <div className="w-14 h-14 rounded-full bg-gradient-to-tr from-purple-700 to-pink-600 flex items-center justify-center text-lg font-bold text-white shadow-glow-purple">
              {currentUser?.first_name?.[0] || 'U'}
            </div>
          )}

          <div className="flex-1">
            <div className="flex items-center gap-1.5">
              <h3 className="font-display font-bold text-base text-white">
                {currentUser?.first_name} {currentUser?.last_name || ''}
              </h3>
              {currentUser?.role === 'admin' && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                  ADMIN
                </span>
              )}
            </div>

            {currentUser?.username && (
              <div className="text-xs text-purple-300 font-medium mt-0.5">
                @{currentUser.username}
              </div>
            )}

            <div className="text-[10px] text-slate-400 mt-1">
              Telegram ID: <span className="font-mono text-slate-300">{currentUser?.telegram_id}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Notification Preferences */}
      <div className="p-4 rounded-2xl glass-panel border-white/5 space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-white/10">
          <Bell className="w-4 h-4 text-purple-400" />
          <h4 className="font-display font-bold text-sm text-white">
            Настройки пуш-уведомлений бота
          </h4>
        </div>

        {/* Toggle 1: Live Stream Start */}
        <div className="flex items-center justify-between gap-3 py-1">
          <div className="flex items-start gap-2.5">
            <div className="p-2 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 mt-0.5">
              <Radio className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white">Старт трансляций</div>
              <div className="text-[11px] text-slate-400 leading-snug">
                Мгновенное уведомление в бота при выходе в прямой эфир
              </div>
            </div>
          </div>

          <button
            onClick={() => handleToggle('notify_stream_start')}
            className={`w-11 h-6 rounded-full transition-colors relative flex-shrink-0 ${
              currentUser?.notify_stream_start ? 'bg-purple-600 shadow-glow-purple' : 'bg-slate-800'
            }`}
          >
            <span
              className={`inline-block w-4 h-4 transform transition-transform bg-white rounded-full absolute top-1 ${
                currentUser?.notify_stream_start ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Toggle 2: Announcements & News */}
        <div className="flex items-center justify-between gap-3 py-1">
          <div className="flex items-start gap-2.5">
            <div className="p-2 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400 mt-0.5">
              <Megaphone className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white">Важные анонсы и новости</div>
              <div className="text-[11px] text-slate-400 leading-snug">
                Розыгрыши, изменения в расписании и специальные ивенты
              </div>
            </div>
          </div>

          <button
            onClick={() => handleToggle('notify_announcements')}
            className={`w-11 h-6 rounded-full transition-colors relative flex-shrink-0 ${
              currentUser?.notify_announcements ? 'bg-purple-600 shadow-glow-purple' : 'bg-slate-800'
            }`}
          >
            <span
              className={`inline-block w-4 h-4 transform transition-transform bg-white rounded-full absolute top-1 ${
                currentUser?.notify_announcements ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Toggle 3: Answers to Suggestions */}
        <div className="flex items-center justify-between gap-3 py-1">
          <div className="flex items-start gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 mt-0.5">
              <MessageCircle className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white">Ответы на мои идеи</div>
              <div className="text-[11px] text-slate-400 leading-snug">
                Личное сообщение в боте, когда стример отвечает на твою предложку
              </div>
            </div>
          </div>

          <button
            onClick={() => handleToggle('notify_answers')}
            className={`w-11 h-6 rounded-full transition-colors relative flex-shrink-0 ${
              currentUser?.notify_answers ? 'bg-purple-600 shadow-glow-purple' : 'bg-slate-800'
            }`}
          >
            <span
              className={`inline-block w-4 h-4 transform transition-transform bg-white rounded-full absolute top-1 ${
                currentUser?.notify_answers ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Streamer Links */}
      <div className="p-4 rounded-2xl glass-panel border-white/5 space-y-2.5">
        <div className="flex items-center gap-2 pb-1 border-b border-white/10">
          <Tv className="w-4 h-4 text-purple-400" />
          <h4 className="font-display font-bold text-sm text-white">
            Каналы стримера
          </h4>
        </div>

        <div className="grid grid-cols-2 gap-2">
          {streamerInfo?.twitch_url && (
            <button
              onClick={() => openLink(streamerInfo.twitch_url)}
              className="p-2.5 rounded-xl bg-[#9146ff]/15 hover:bg-[#9146ff]/25 border border-[#9146ff]/30 text-left transition-all btn-press flex items-center justify-between"
            >
              <span className="text-xs font-bold text-[#c084fc]">📺 Twitch</span>
              <ExternalLink className="w-3.5 h-3.5 text-[#c084fc]" />
            </button>
          )}

          {streamerInfo?.kick_url && (
            <button
              onClick={() => openLink(streamerInfo.kick_url)}
              className="p-2.5 rounded-xl bg-[#53fc18]/15 hover:bg-[#53fc18]/25 border border-[#53fc18]/30 text-left transition-all btn-press flex items-center justify-between"
            >
              <span className="text-xs font-bold text-[#4ade80]">⚡️ Kick</span>
              <ExternalLink className="w-3.5 h-3.5 text-[#4ade80]" />
            </button>
          )}

          {streamerInfo?.vk_url && (
            <button
              onClick={() => openLink(streamerInfo.vk_url)}
              className="p-2.5 rounded-xl bg-[#0077ff]/15 hover:bg-[#0077ff]/25 border border-[#0077ff]/30 text-left transition-all btn-press flex items-center justify-between"
            >
              <span className="text-xs font-bold text-[#60a5fa]">🎬 VK Видео</span>
              <ExternalLink className="w-3.5 h-3.5 text-[#60a5fa]" />
            </button>
          )}

          {streamerInfo?.telegram_channel && (
            <button
              onClick={() => openTelegramLink(streamerInfo.telegram_channel)}
              className="p-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/30 text-left transition-all btn-press flex items-center justify-between"
            >
              <span className="text-xs font-bold text-cyan-300">📢 Telegram</span>
              <ExternalLink className="w-3.5 h-3.5 text-cyan-300" />
            </button>
          )}
        </div>
      </div>

      {/* Info Footer */}
      <div className="text-center pt-2">
        <p className="text-[11px] text-slate-500">
          Streamer Telegram Mini App • v1.0.0
        </p>
      </div>
    </div>
  );
}
