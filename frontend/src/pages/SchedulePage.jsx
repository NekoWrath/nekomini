import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../context/TelegramContext';
import { StreamCard } from '../components/StreamCard';
import { CountdownTimer } from '../components/CountdownTimer';
import { StreamEditorModal } from '../components/StreamEditorModal';
import { formatStreamDate, PLATFORM_CONFIG } from '../utils/helpers';
import { Calendar, Radio, Play, Plus, Tv, Sparkles, Filter, Clock } from 'lucide-react';

export function SchedulePage() {
  const { streams, currentStream, currentUser, deleteStream } = useApp();
  const { setMainButton, hideMainButton, openLink } = useTelegram();

  const [selectedDayFilter, setSelectedDayFilter] = useState('all');
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingStream, setEditingStream] = useState(null);

  const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'moderator';
  const isLive = currentStream?.is_live || false;

  // Bind Telegram MainButton when live or nearest stream is active
  useEffect(() => {
    if (isLive && currentStream?.platform_url) {
      setMainButton({
        text: `🔥 СМОТРЕТЬ НА ${currentStream.platform.toUpperCase()}`,
        color: '#dc2626',
        onClick: () => openLink(currentStream.platform_url),
        isVisible: true,
      });
    } else {
      hideMainButton();
    }
    return () => hideMainButton();
  }, [isLive, currentStream, setMainButton, hideMainButton, openLink]);

  // Filter streams by day
  const filteredStreams = streams.filter((s) => {
    if (selectedDayFilter === 'all') return true;
    if (selectedDayFilter === 'live') return s.is_live;
    const date = new Date(s.start_time);
    const dayOfWeek = date.getDay(); // 0 = Sun, 1 = Mon ...
    return String(dayOfWeek) === selectedDayFilter;
  });

  const daysNav = [
    { id: 'all', label: 'Все стримы' },
    { id: '1', label: 'Пн' },
    { id: '2', label: 'Вт' },
    { id: '3', label: 'Ср' },
    { id: '4', label: 'Чт' },
    { id: '5', label: 'Пт' },
    { id: '6', label: 'Сб' },
    { id: '0', label: 'Вс' },
  ];

  return (
    <div className="pb-24 pt-3 px-4 space-y-5">
      {/* HERO BANNER: LIVE or COUNTDOWN */}
      {currentStream && (
        <div className={`p-5 rounded-3xl relative overflow-hidden transition-all duration-300 ${
          isLive
            ? 'glass-panel-elevated border-rose-500/50 shadow-glow-live'
            : 'glass-panel border-purple-500/30'
        }`}>
          {/* Background Ambient Glow */}
          <div className={`absolute top-0 right-0 w-48 h-48 rounded-full blur-3xl pointer-events-none ${
            isLive ? 'bg-rose-600/20' : 'bg-purple-600/15'
          }`} />

          {/* Top Info */}
          <div className="flex items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              {isLive ? (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-600 text-white text-xs font-extrabold shadow-glow-live animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                  <span>ПРЯМОЙ ЭФИР</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-950/80 border border-purple-500/40 text-purple-300 text-xs font-semibold">
                  <Clock className="w-3.5 h-3.5 text-purple-400" />
                  <span>Следующий стрим</span>
                </div>
              )}
            </div>

            <span className="text-xs font-bold text-slate-300 bg-slate-800/80 px-2.5 py-1 rounded-full border border-slate-700">
              {currentStream.platform}
            </span>
          </div>

          {/* Title & Game */}
          <h2 className="font-display font-extrabold text-lg sm:text-xl text-white leading-tight">
            {currentStream.title}
          </h2>

          <div className="flex items-center gap-2 mt-2 text-xs text-purple-300 font-medium">
            <span>🎮 {currentStream.game_category}</span>
            <span>•</span>
            <span>🕒 {formatStreamDate(currentStream.start_time)}</span>
          </div>

          {/* Countdown if not live */}
          {!isLive && (
            <div className="mt-4 pt-3 border-t border-white/10">
              <div className="text-[11px] text-center text-slate-400 mb-2 font-medium">
                До начала трансляции осталось:
              </div>
              <CountdownTimer targetDate={currentStream.start_time} />
            </div>
          )}

          {/* Action Button */}
          <div className="mt-4">
            <button
              onClick={() => openLink(currentStream.platform_url)}
              className={`w-full py-3 rounded-2xl font-display font-bold text-sm flex items-center justify-center gap-2 shadow-lg transition-all btn-press ${
                isLive
                  ? 'bg-gradient-to-r from-rose-600 to-pink-600 text-white shadow-glow-live hover:brightness-110'
                  : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-glow-purple hover:brightness-110'
              }`}
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{isLive ? 'Смотреть трансляцию прямо сейчас' : 'Перейти на канал стримера'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Week Calendar Filter */}
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex items-center gap-1.5 text-sm font-bold text-white">
            <Calendar className="w-4 h-4 text-purple-400" />
            <span>Календарь недели</span>
          </div>

          {isAdmin && (
            <button
              onClick={() => {
                setEditingStream(null);
                setIsEditorOpen(true);
              }}
              className="flex items-center gap-1 text-xs font-bold text-purple-300 bg-purple-950/60 hover:bg-purple-900/60 border border-purple-500/40 px-2.5 py-1 rounded-xl transition-all btn-press"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Добавить стрим</span>
            </button>
          )}
        </div>

        {/* Day Pills Carousel */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
          {daysNav.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedDayFilter(d.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all btn-press ${
                selectedDayFilter === d.id
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-glow-purple'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 border border-slate-800'
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stream Cards List */}
      <div className="space-y-4">
        {filteredStreams.length > 0 ? (
          filteredStreams.map((stream) => (
            <StreamCard
              key={stream.id}
              stream={stream}
              onEdit={(s) => {
                setEditingStream(s);
                setIsEditorOpen(true);
              }}
              onDelete={(id) => deleteStream(id)}
            />
          ))
        ) : (
          <div className="p-8 rounded-2xl glass-panel text-center border border-white/5">
            <Calendar className="w-10 h-10 text-slate-600 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-slate-300">На этот день стримов нет</h4>
            <p className="text-xs text-slate-500 mt-1">
              Выберите другой день недели или следите за анонсами в канале!
            </p>
          </div>
        )}
      </div>

      {/* Stream Editor Modal */}
      <StreamEditorModal
        stream={editingStream}
        isOpen={isEditorOpen}
        onClose={() => {
          setIsEditorOpen(false);
          setEditingStream(null);
        }}
      />
    </div>
  );
}
