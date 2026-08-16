import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { STATUS_CONFIG } from '../utils/helpers';
import { X, Send, ShieldCheck, Check, MessageSquare, AlertCircle } from 'lucide-react';

export function AdminReplyModal({ suggestion, isOpen, onClose }) {
  const { moderateSuggestion } = useApp();

  const [status, setStatus] = useState(suggestion?.status || 'accepted');
  const [adminReply, setAdminReply] = useState(suggestion?.admin_reply || '');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen || !suggestion) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    const success = await moderateSuggestion(suggestion.id, {
      status,
      admin_reply: adminReply.trim() || null,
    });
    setSubmitting(false);

    if (success) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-lg bg-slate-900 border border-purple-500/30 rounded-t-3xl sm:rounded-3xl p-5 shadow-glass max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-rose-400" />
            <h3 className="font-display font-bold text-lg text-white">
              Модерация предложения
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Suggestion Context Summary */}
        <div className="mt-4 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <div className="text-xs text-purple-400 font-semibold mb-1">
            Автор: {suggestion.author_name} {suggestion.author_username ? `(@${suggestion.author_username})` : ''}
          </div>
          <div className="text-sm font-bold text-white mb-1">
            {suggestion.title}
          </div>
          <div className="text-xs text-slate-400 line-clamp-3">
            {suggestion.content}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Status Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Решение / Статус
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setStatus('accepted')}
                className={`py-2 px-2 rounded-xl border text-xs font-bold transition-all flex flex-col items-center gap-1 ${
                  status === 'accepted'
                    ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300 shadow-sm'
                    : 'bg-slate-800/60 border-slate-700 text-slate-400'
                }`}
              >
                <span>✅</span>
                <span>Взять на стрим</span>
              </button>

              <button
                type="button"
                onClick={() => setStatus('answered')}
                className={`py-2 px-2 rounded-xl border text-xs font-bold transition-all flex flex-col items-center gap-1 ${
                  status === 'answered'
                    ? 'bg-blue-600/30 border-blue-500 text-blue-300 shadow-sm'
                    : 'bg-slate-800/60 border-slate-700 text-slate-400'
                }`}
              >
                <span>💬</span>
                <span>Ответить</span>
              </button>

              <button
                type="button"
                onClick={() => setStatus('rejected')}
                className={`py-2 px-2 rounded-xl border text-xs font-bold transition-all flex flex-col items-center gap-1 ${
                  status === 'rejected'
                    ? 'bg-rose-600/30 border-rose-500 text-rose-300 shadow-sm'
                    : 'bg-slate-800/60 border-slate-700 text-slate-400'
                }`}
              >
                <span>❌</span>
                <span>Отклонить</span>
              </button>
            </div>
          </div>

          {/* Admin Reply Text */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
              <span>Ответ стримера (уйдет автору в ЛС через бота):</span>
              <span className="text-[11px] text-purple-400 font-normal">Telegram Bot DM</span>
            </label>
            <textarea
              rows={3}
              value={adminReply}
              onChange={(e) => setAdminReply(e.target.value)}
              placeholder="Например: Супер идея! Обязательно сделаем на стриме в пятницу..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors resize-none"
            />
          </div>

          <div className="p-2.5 rounded-xl bg-purple-950/30 border border-purple-500/20 text-[11px] text-purple-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-purple-400 flex-shrink-0" />
            <span>Бот автоматически отправит уведомление пользователю в личные сообщения.</span>
          </div>

          {/* Submit */}
          <div className="pt-2 flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-sm shadow-glow-purple flex items-center justify-center gap-1.5 hover:brightness-110 disabled:opacity-50 transition-all btn-press"
            >
              <Send className="w-4 h-4" />
              <span>{submitting ? 'Сохранение...' : 'Сохранить и уведомить'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
