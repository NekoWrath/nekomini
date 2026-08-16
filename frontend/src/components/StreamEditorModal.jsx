import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { PLATFORM_CONFIG } from '../utils/helpers';
import { X, Calendar, Gamepad2, Tv, Image, Tag, Save, Sparkles } from 'lucide-react';

export function StreamEditorModal({ stream, isOpen, onClose }) {
  const { saveStream, streamerInfo } = useApp();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [gameCategory, setGameCategory] = useState('Just Chatting');
  const [platform, setPlatform] = useState('Twitch');
  const [platformUrl, setPlatformUrl] = useState('');
  const [startTime, setStartTime] = useState('');
  const [previewImageUrl, setPreviewImageUrl] = useState('');
  const [tags, setTags] = useState('gaming,chill');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (stream) {
      setTitle(stream.title || '');
      setDescription(stream.description || '');
      setGameCategory(stream.game_category || 'Just Chatting');
      setPlatform(stream.platform || 'Twitch');
      setPlatformUrl(stream.platform_url || '');
      
      // Format datetime-local string
      if (stream.start_time) {
        const dt = new Date(stream.start_time);
        const pad = (n) => String(n).padStart(2, '0');
        const formatted = `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
        setStartTime(formatted);
      }
      setPreviewImageUrl(stream.preview_image_url || '');
      setTags(stream.tags || 'gaming,chill');
    } else {
      // Defaults for new stream
      setTitle('');
      setDescription('');
      setGameCategory('Counter-Strike 2');
      setPlatform('Twitch');
      setPlatformUrl(streamerInfo?.twitch_url || 'https://twitch.tv/streamer');
      
      // Default time: today + 3 hours
      const now = new Date();
      now.setHours(now.getHours() + 3);
      now.setMinutes(0);
      const pad = (n) => String(n).padStart(2, '0');
      const formatted = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
      setStartTime(formatted);

      setPreviewImageUrl('https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80');
      setTags('турнир,игры,розыгрыш');
    }
  }, [stream, isOpen, streamerInfo]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !platformUrl.trim() || !startTime) return;

    setSubmitting(true);
    const data = {
      title: title.trim(),
      description: description.trim(),
      game_category: gameCategory.trim() || 'Just Chatting',
      platform,
      platform_url: platformUrl.trim(),
      start_time: new Date(startTime).toISOString(),
      preview_image_url: previewImageUrl.trim() || null,
      tags: tags.trim() || 'gaming',
    };

    const success = await saveStream(data, stream ? stream.id : null);
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
            <Calendar className="w-5 h-5 text-purple-400" />
            <h3 className="font-display font-bold text-lg text-white">
              {stream ? 'Редактировать стрим' : 'Добавить новый стрим'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3.5">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Название стрима *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Например: Прохождение ELDEN RING без смертей"
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Описание / Анонс
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Кратко о том, что будет на стриме..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none transition-colors resize-none"
            />
          </div>

          {/* Game Category & Platform */}
          <div className="grid grid-cols-2 gap-2.5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
                <Gamepad2 className="w-3.5 h-3.5 text-purple-400" />
                <span>Категория / Игра</span>
              </label>
              <input
                type="text"
                value={gameCategory}
                onChange={(e) => setGameCategory(e.target.value)}
                placeholder="Dota 2, CS2, Чат..."
                className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
                <Tv className="w-3.5 h-3.5 text-purple-400" />
                <span>Платформа</span>
              </label>
              <select
                value={platform}
                onChange={(e) => {
                  setPlatform(e.target.value);
                  if (e.target.value === 'Kick') setPlatformUrl(streamerInfo?.kick_url || 'https://kick.com');
                  else if (e.target.value === 'VK Video') setPlatformUrl(streamerInfo?.vk_url || 'https://live.vkvideo.ru');
                  else if (e.target.value === 'Twitch') setPlatformUrl(streamerInfo?.twitch_url || 'https://twitch.tv');
                }}
                className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3 py-2 text-sm text-white focus:outline-none"
              >
                <option value="Twitch">Twitch</option>
                <option value="Kick">Kick</option>
                <option value="VK Video">VK Video</option>
                <option value="YouTube">YouTube</option>
              </select>
            </div>
          </div>

          {/* Platform URL */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Прямая ссылка на трансляцию *
            </label>
            <input
              type="url"
              required
              value={platformUrl}
              onChange={(e) => setPlatformUrl(e.target.value)}
              placeholder="https://twitch.tv/..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
          </div>

          {/* Start Time */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-purple-400" />
              <span>Дата и время начала *</span>
            </label>
            <input
              type="datetime-local"
              required
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none"
            />
          </div>

          {/* Cover Image URL */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
              <Image className="w-3.5 h-3.5 text-purple-400" />
              <span>URL баннера / обложки</span>
            </label>
            <input
              type="url"
              value={previewImageUrl}
              onChange={(e) => setPreviewImageUrl(e.target.value)}
              placeholder="https://images.unsplash.com/..."
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1">
              <Tag className="w-3.5 h-3.5 text-purple-400" />
              <span>Теги (через запятую)</span>
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="турнир, рофлы, розыгрыш"
              className="w-full bg-slate-950/80 border border-slate-700 focus:border-purple-500 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none"
            />
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
              <Save className="w-4 h-4" />
              <span>{submitting ? 'Сохранение...' : 'Сохранить'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
