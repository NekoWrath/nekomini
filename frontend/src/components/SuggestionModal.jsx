import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { CATEGORY_CONFIG } from '../utils/helpers';
import { X, Send, Sparkles, Link2 } from 'lucide-react';

export function SuggestionModal({ isOpen, onClose }) {
  const { submitSuggestion } = useApp();

  const [category, setCategory] = useState('game_idea');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [mediaUrl, setMediaUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    setSubmitting(true);
    const success = await submitSuggestion({
      category,
      title: title.trim(),
      content: content.trim(),
      media_url: mediaUrl.trim() || null,
    });
    setSubmitting(false);

    if (success) {
      setTitle('');
      setContent('');
      setMediaUrl('');
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-lg bg-slate-900 border border-purple-500/30 rounded-t-3xl sm:rounded-3xl p-5 shadow-glass max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h3 className="font-display font-bold text-lg text-white">
              Предложить идею или вопрос
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          {/* Category Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Категория
            </label>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(CATEGORY_CONFIG).map(([key, item]) => (
                <button
                  type="button"
                  key={key}
                  onClick={() => setCategory(key)}
                  className={`p-2.5 rounded-xl border text-left text-xs font-semibold flex items-center gap-2 transition-all ${
                    category === key
                      ? 'bg-purple-600/30 border-purple-500 text-white shadow-glow-purple'
                      : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <span className="text-base">{item.emoji}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Краткий заголовок *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Например: Сыграть в Lethal Company со зрителями"
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Content */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Подробное описание *
            </label>
            <textarea
              required
              rows={4}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Опиши подробнее суть идеи, правила челленджа или свой вопрос..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors resize-none"
            />
          </div>

          {/* Optional Media Link */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1">
              <Link2 className="w-3.5 h-3.5 text-purple-400" />
              <span>Ссылка на клип / трейлер / изображение (необязательно)</span>
            </label>
            <input
              type="url"
              value={mediaUrl}
              onChange={(e) => setMediaUrl(e.target.value)}
              placeholder="https://..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Submit */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting || !title.trim() || !content.trim()}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-display font-bold text-sm shadow-glow-purple flex items-center justify-center gap-2 hover:brightness-110 disabled:opacity-50 transition-all btn-press"
            >
              <Send className="w-4 h-4" />
              <span>{submitting ? 'Отправка...' : 'Отправить в предложку'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
