import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { X, Send, Megaphone, Image, Link, AlertTriangle } from 'lucide-react';

export function BroadcastModal({ isOpen, onClose }) {
  const { sendBroadcast } = useApp();

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [buttonText, setButtonText] = useState('🔥 Смотреть трансляцию');
  const [buttonUrl, setButtonUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) return;

    setSubmitting(true);
    const res = await sendBroadcast({
      title: title.trim(),
      content: content.trim(),
      image_url: imageUrl.trim() || null,
      button_text: buttonText.trim() || null,
      button_url: buttonUrl.trim() || null,
    });
    setSubmitting(false);

    if (res) {
      setTitle('');
      setContent('');
      setImageUrl('');
      setButtonUrl('');
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="w-full max-w-lg bg-slate-900 border border-purple-500/30 rounded-t-3xl sm:rounded-3xl p-5 shadow-glass max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <Megaphone className="w-5 h-5 text-rose-400" />
            <h3 className="font-display font-bold text-lg text-white">
              Мгновенный анонс / Рассылка
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mt-3 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <span>Сообщение будет мгновенно отправлено всем подписчикам бота, у которых включены анонсы.</span>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Заголовок анонса *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="🚨 СРОЧНЫЙ СТРИМ: Начало через 10 минут!"
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
          </div>

          {/* Content */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Текст сообщения *
            </label>
            <textarea
              required
              rows={4}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Подробности анонса, что сегодня будет..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none resize-none"
            />
          </div>

          {/* Optional Image URL */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
              <Image className="w-3.5 h-3.5 text-purple-400" />
              <span>URL фото / постера (необязательно)</span>
            </label>
            <input
              type="url"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
          </div>

          {/* Button Text & URL */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Текст кнопки
              </label>
              <input
                type="text"
                value={buttonText}
                onChange={(e) => setButtonText(e.target.value)}
                placeholder="Смотреть трансляцию"
                className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3 py-2 text-sm text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
                <Link className="w-3.5 h-3.5 text-purple-400" />
                <span>Ссылка кнопки</span>
              </label>
              <input
                type="url"
                value={buttonUrl}
                onChange={(e) => setButtonUrl(e.target.value)}
                placeholder="https://twitch.tv/..."
                className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3 py-2 text-sm text-white focus:outline-none"
              />
            </div>
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
              disabled={submitting || !title.trim() || !content.trim()}
              className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 text-white font-bold text-sm shadow-glow-live flex items-center justify-center gap-1.5 hover:brightness-110 disabled:opacity-50 transition-all btn-press"
            >
              <Send className="w-4 h-4" />
              <span>{submitting ? 'Рассылка...' : 'Запустить рассылку'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
