import React from 'react';
import { useApp } from '../context/AppContext';
import { useTelegram } from '../context/TelegramContext';
import { CATEGORY_CONFIG, STATUS_CONFIG, formatTimeAgo } from '../utils/helpers';
import { ThumbsUp, Flame, MessageCircle, ExternalLink, Shield, Check, X, Sparkles, Trash2 } from 'lucide-react';

export function SuggestionCard({ suggestion, onModerate, onDelete }) {
  const { voteSuggestion, currentUser, streamerInfo } = useApp();
  const { openLink } = useTelegram();

  const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'moderator';
  const isAuthor = suggestion.is_author || suggestion.telegram_id === currentUser?.telegram_id;

  const category = CATEGORY_CONFIG[suggestion.category] || CATEGORY_CONFIG.other;
  const status = STATUS_CONFIG[suggestion.status] || STATUS_CONFIG.pending;

  const handleVote = (e) => {
    e.stopPropagation();
    voteSuggestion(suggestion.id);
  };

  return (
    <div className={`p-4 rounded-2xl glass-panel border transition-all duration-200 ${
      suggestion.status === 'accepted'
        ? 'border-emerald-500/30 bg-emerald-950/10'
        : 'hover:border-purple-500/30'
    }`}>
      {/* Header: Author & Category & Status */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          {suggestion.author_avatar ? (
            <img
              src={suggestion.author_avatar}
              alt={suggestion.author_name}
              className="w-8 h-8 rounded-full object-cover border border-purple-500/30"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-700 to-indigo-600 flex items-center justify-center text-xs font-bold text-white">
              {suggestion.author_name?.[0] || 'U'}
            </div>
          )}

          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-xs text-slate-200">
                {suggestion.author_name}
              </span>
              {suggestion.author_username && (
                <span className="text-[11px] text-slate-500">
                  @{suggestion.author_username}
                </span>
              )}
            </div>
            <div className="text-[10px] text-slate-400">
              {formatTimeAgo(suggestion.created_at)}
            </div>
          </div>
        </div>

        {/* Category Pill */}
        <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full border ${category.badgeClass} flex items-center gap-1`}>
          <span>{category.emoji}</span>
          <span>{category.label}</span>
        </span>
      </div>

      {/* Title & Body */}
      <div className="mt-3">
        <h4 className="font-display font-bold text-sm text-white leading-snug">
          {suggestion.title}
        </h4>
        <p className="text-xs text-slate-300 mt-1 leading-relaxed whitespace-pre-line">
          {suggestion.content}
        </p>

        {/* Optional Media Link */}
        {suggestion.media_url && (
          <div className="mt-2">
            <button
              onClick={() => openLink(suggestion.media_url)}
              className="inline-flex items-center gap-1 text-[11px] text-purple-400 hover:text-purple-300 font-medium bg-purple-950/40 border border-purple-500/30 px-2.5 py-1 rounded-lg transition-colors"
            >
              <ExternalLink className="w-3 h-3" />
              <span>Прикрепленная ссылка / медиа</span>
            </button>
          </div>
        )}
      </div>

      {/* Streamer Reply Box if answered */}
      {suggestion.admin_reply && (
        <div className="mt-3.5 p-3 rounded-xl bg-purple-950/40 border border-purple-500/30 relative">
          <div className="flex items-center gap-2 mb-1.5">
            <img
              src={streamerInfo?.avatar || 'https://images.unsplash.com/photo-1566492031773-4f4e44671857?w=150&auto=format&fit=crop&q=80'}
              alt={streamerInfo?.name || 'Streamer'}
              className="w-5 h-5 rounded-full object-cover border border-purple-400"
            />
            <span className="text-xs font-bold text-purple-300 flex items-center gap-1">
              {streamerInfo?.name || 'Стример'}
              <Sparkles className="w-3 h-3 text-purple-400" />
            </span>
            <span className="text-[10px] text-purple-400/70 ml-auto">
              Ответ стримера
            </span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed italic">
            «{suggestion.admin_reply}»
          </p>
        </div>
      )}

      {/* Footer: Upvote Button & Status Badge & Actions */}
      <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between gap-2">
        {/* Status Badge */}
        <div className="flex items-center gap-2">
          <span className={`text-[11px] px-2.5 py-0.5 rounded-full ${status.badgeClass} flex items-center gap-1`}>
            <span>{status.icon}</span>
            <span>{status.label}</span>
          </span>
        </div>

        {/* Right actions: Upvote + Admin Moderate + Delete */}
        <div className="flex items-center gap-1.5">
          {/* Delete button (Admin or Author) */}
          {(isAdmin || isAuthor) && onDelete && (
            <button
              onClick={() => onDelete(suggestion.id)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors"
              title="Удалить"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}

          {/* Admin Moderate Button */}
          {isAdmin && onModerate && (
            <button
              onClick={() => onModerate(suggestion)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-purple-900/40 text-purple-300 border border-purple-500/30 transition-all btn-press"
            >
              <Shield className="w-3 h-3" />
              <span>Модерация</span>
            </button>
          )}

          {/* Upvote Button */}
          <button
            onClick={handleVote}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold transition-all btn-press ${
              suggestion.has_voted
                ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-glow-purple'
                : 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border border-slate-700/60'
            }`}
          >
            <Flame className={`w-3.5 h-3.5 ${suggestion.has_voted ? 'text-amber-300 fill-amber-300' : 'text-slate-400'}`} />
            <span>{suggestion.upvotes_count}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
