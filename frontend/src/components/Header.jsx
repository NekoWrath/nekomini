import React from 'react';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../context/TelegramContext';
import { Radio, ExternalLink, Sparkles, ShieldCheck } from 'lucide-react';

export function Header() {
  const { streamerInfo, currentStream, currentUser } = useApp();
  const { openLink } = useTelegram();

  const isLive = currentStream?.is_live || false;

  return (
    <header className="relative pt-4 pb-3 px-4 glass-panel border-b border-white/5 shadow-glass">
      {/* Background neon blur */}
      <div className="absolute top-0 left-1/4 w-32 h-32 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-0 right-1/4 w-32 h-32 bg-pink-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 flex items-center justify-between">
        {/* Streamer Avatar & Name */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <img
              src={streamerInfo?.avatar || 'https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150&auto=format&fit=crop&q=80'}
              alt={streamerInfo?.name || 'Streamer'}
              className="w-11 h-11 rounded-full object-cover border-2 border-purple-500/50 shadow-glow-purple"
            />
            {isLive ? (
              <span className="absolute -bottom-1 -right-1 flex h-4 w-4">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-4 w-4 bg-rose-600 border-2 border-slate-900"></span>
              </span>
            ) : (
              <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-slate-900" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="font-display font-bold text-base text-white tracking-wide">
                {streamerInfo?.name || 'StreamerLegend'}
              </h1>
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            </div>

            {/* Status indicator */}
            <div className="flex items-center gap-2 mt-0.5">
              {isLive ? (
                <div className="flex items-center gap-1 text-[11px] font-bold text-rose-400 bg-rose-500/15 px-2 py-0.5 rounded-full border border-rose-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                  <span>В ЭФИРЕ</span>
                  {currentStream?.viewers_count > 0 && (
                    <span className="text-slate-400 font-normal">
                      • {currentStream.viewers_count.toLocaleString()}
                    </span>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-1 text-[11px] text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-full border border-slate-700/50">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                  <span>Офлайн</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* User Mini Profile / Role Badge */}
        <div className="flex items-center gap-2">
          {currentUser && (
            <div className="flex items-center gap-2 bg-slate-800/70 border border-slate-700/50 px-2.5 py-1.5 rounded-xl">
              {currentUser.photo_url ? (
                <img
                  src={currentUser.photo_url}
                  alt={currentUser.first_name}
                  className="w-6 h-6 rounded-full object-cover border border-purple-500/40"
                />
              ) : (
                <div className="w-6 h-6 rounded-full bg-purple-600/30 flex items-center justify-center text-[10px] font-bold text-purple-300">
                  {currentUser.first_name?.[0] || 'U'}
                </div>
              )}
              <div className="text-left">
                <div className="text-xs font-semibold text-slate-200 line-clamp-1 max-w-[80px]">
                  {currentUser.first_name || 'Гость'}
                </div>
                {currentUser.role === 'admin' && (
                  <div className="flex items-center gap-0.5 text-[9px] font-bold text-rose-400">
                    <ShieldCheck className="w-2.5 h-2.5" />
                    <span>Admin</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
