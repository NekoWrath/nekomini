import React from 'react';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../context/TelegramContext';
import { formatStreamDate, PLATFORM_CONFIG } from '../utils/helpers';
import { Bell, BellRing, Play, Tv, Gamepad2, Calendar, Radio, MoreVertical, Trash2, Edit } from 'lucide-react';

export function StreamCard({ stream, onEdit, onDelete }) {
  const { toggleStreamReminder, currentUser, toggleStreamLive } = useApp();
  const { openLink } = useTelegram();

  const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'moderator';
  const platformInfo = PLATFORM_CONFIG[stream.platform] || PLATFORM_CONFIG.Twitch;
  const isLive = stream.is_live;

  const handleOpenStream = () => {
    openLink(stream.platform_url);
  };

  const handleToggleReminder = (e) => {
    e.stopPropagation();
    toggleStreamReminder(stream.id);
  };

  return (
    <div className={`relative rounded-2xl overflow-hidden transition-all duration-300 ${
      isLive
        ? 'glass-panel-elevated border-rose-500/40 shadow-glow-live'
        : 'glass-panel hover:border-purple-500/30'
    }`}>
      {/* Cover Image / Gradient */}
      <div className="relative h-36 sm:h-44 w-full bg-slate-900 overflow-hidden">
        {stream.preview_image_url ? (
          <img
            src={stream.preview_image_url}
            alt={stream.title}
            className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-indigo-950 via-slate-900 to-purple-950 flex items-center justify-center">
            <Gamepad2 className="w-12 h-12 text-purple-500/40" />
          </div>
        )}

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-transparent" />

        {/* Badges on Top */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
          {/* Platform Badge */}
          <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border backdrop-blur-md flex items-center gap-1 ${platformInfo.badgeClass}`}>
            <Tv className="w-3 h-3" />
            <span>{stream.platform}</span>
          </span>

          {/* Live Status or Reminder Button */}
          {isLive ? (
            <span className="flex items-center gap-1.5 text-[11px] font-bold px-3 py-1 rounded-full bg-rose-600 text-white shadow-glow-live animate-pulse">
              <Radio className="w-3.5 h-3.5" />
              <span>В ЭФИРЕ</span>
            </span>
          ) : (
            <button
              onClick={handleToggleReminder}
              className={`flex items-center gap-1 text-xs font-semibold px-3 py-1 rounded-full backdrop-blur-md border transition-all btn-press ${
                stream.has_reminder
                  ? 'bg-purple-600/90 text-white border-purple-400 shadow-glow-purple'
                  : 'bg-slate-900/80 text-slate-300 border-slate-700/60 hover:border-purple-500/50'
              }`}
            >
              {stream.has_reminder ? (
                <>
                  <BellRing className="w-3.5 h-3.5 text-purple-200 animate-bounce" />
                  <span>Напомнить (Вкл)</span>
                </>
              ) : (
                <>
                  <Bell className="w-3.5 h-3.5 text-slate-400" />
                  <span>Напомнить</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Game category badge on cover bottom-left */}
        <div className="absolute bottom-2 left-3 z-10">
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-purple-300 bg-purple-950/70 border border-purple-500/30 px-2 py-0.5 rounded-md backdrop-blur-sm">
            <Gamepad2 className="w-3 h-3 text-purple-400" />
            <span>{stream.game_category}</span>
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="font-display font-bold text-base text-white line-clamp-2 leading-snug">
          {stream.title}
        </h3>

        {stream.description && (
          <p className="text-xs text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
            {stream.description}
          </p>
        )}

        {/* Stream tags */}
        {stream.tags && (
          <div className="flex flex-wrap gap-1 mt-2.5">
            {stream.tags.split(',').map((tag) => (
              <span
                key={tag.trim()}
                className="text-[10px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded-full border border-slate-700/40"
              >
                #{tag.trim()}
              </span>
            ))}
          </div>
        )}

        {/* Date / Action Footer */}
        <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-300 font-medium">
            <Calendar className="w-3.5 h-3.5 text-purple-400" />
            <span>{formatStreamDate(stream.start_time)}</span>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Admin Controls */}
            {isAdmin && (
              <>
                <button
                  onClick={() => toggleStreamLive(stream.id, !isLive)}
                  title={isLive ? 'Завершить эфир' : 'Запустить в эфир'}
                  className={`p-1.5 rounded-lg text-xs font-semibold border transition-all ${
                    isLive
                      ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 hover:bg-rose-500/30'
                      : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30'
                  }`}
                >
                  <Radio className="w-3.5 h-3.5" />
                </button>
                {onEdit && (
                  <button
                    onClick={() => onEdit(stream)}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
                  >
                    <Edit className="w-3.5 h-3.5" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => onDelete(stream.id)}
                    className="p-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-400 border border-rose-800/40"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </>
            )}

            {/* Watch Stream Button */}
            <button
              onClick={handleOpenStream}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold transition-all btn-press ${
                isLive
                  ? 'bg-gradient-to-r from-rose-600 to-pink-600 text-white shadow-glow-live'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-glow-purple hover:brightness-110'
              }`}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{isLive ? 'Смотреть' : 'Ссылка'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
