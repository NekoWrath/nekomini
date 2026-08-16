import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { SuggestionCard } from '../components/SuggestionCard';
import { SuggestionModal } from '../components/SuggestionModal';
import { AdminReplyModal } from '../components/AdminReplyModal';
import { CATEGORY_CONFIG } from '../utils/helpers';
import { Lightbulb, Plus, Search, Flame, Sparkles, MessageSquare, User, Filter } from 'lucide-react';

export function SuggestionsPage() {
  const {
    suggestions,
    suggestionTab,
    setSuggestionTab,
    suggestionCategory,
    setSuggestionCategory,
    suggestionSearch,
    setSuggestionSearch,
    deleteSuggestion,
    currentUser,
  } = useApp();

  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [moderatingSuggestion, setModeratingSuggestion] = useState(null);

  const tabs = [
    { id: 'new', label: 'Новые', icon: Sparkles },
    { id: 'popular', label: 'Популярные', icon: Flame },
    { id: 'answered', label: 'Отвеченные', icon: MessageSquare },
    { id: 'my', label: 'Мои', icon: User },
  ];

  return (
    <div className="pb-24 pt-3 px-4 space-y-4">
      {/* Top CTA Card */}
      <div className="p-4 rounded-2xl glass-panel-elevated border-purple-500/30 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-36 h-36 bg-gradient-to-bl from-purple-600/20 to-pink-600/20 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex items-center justify-between gap-3">
          <div>
            <h3 className="font-display font-extrabold text-base text-white flex items-center gap-1.5">
              <span>💡 Предложка и Вопросы</span>
            </h3>
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              Предлагай игры, челленджи и задавай вопросы. Топ попадает на стрим!
            </p>
          </div>

          <button
            onClick={() => setIsSubmitModalOpen(true)}
            className="flex-shrink-0 px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-display font-bold text-xs shadow-glow-purple flex items-center gap-1.5 hover:brightness-110 transition-all btn-press"
          >
            <Plus className="w-4 h-4" />
            <span>Написать</span>
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={suggestionSearch}
          onChange={(e) => setSuggestionSearch(e.target.value)}
          placeholder="Поиск по предложке..."
          className="w-full bg-slate-900/80 border border-slate-700/80 focus:border-purple-500 rounded-xl pl-9 pr-3.5 py-2 text-xs text-white placeholder-slate-400 focus:outline-none transition-colors"
        />
        {suggestionSearch && (
          <button
            onClick={() => setSuggestionSearch('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
          >
            ✕
          </button>
        )}
      </div>

      {/* Filter Tabs (New, Popular, Answered, My) */}
      <div className="grid grid-cols-4 gap-1 p-1 bg-slate-900/80 border border-slate-800 rounded-2xl">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = suggestionTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setSuggestionTab(tab.id)}
              className={`py-1.5 px-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-all btn-press ${
                isActive
                  ? 'bg-purple-600 text-white shadow-glow-purple font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Category Chips Horizontal Scroll */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        <button
          onClick={() => setSuggestionCategory('all')}
          className={`px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all btn-press ${
            suggestionCategory === 'all'
              ? 'bg-indigo-600/40 border border-indigo-400 text-indigo-200 shadow-sm'
              : 'bg-slate-900/80 border border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          Все категории
        </button>

        {Object.entries(CATEGORY_CONFIG).map(([key, item]) => (
          <button
            key={key}
            onClick={() => setSuggestionCategory(key)}
            className={`px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap border transition-all btn-press flex items-center gap-1 ${
              suggestionCategory === key
                ? `${item.badgeClass} ring-1 ring-purple-400`
                : 'bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>{item.emoji}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </div>

      {/* Suggestions Feed */}
      <div className="space-y-3.5">
        {suggestions.length > 0 ? (
          suggestions.map((item) => (
            <SuggestionCard
              key={item.id}
              suggestion={item}
              onModerate={(sug) => setModeratingSuggestion(sug)}
              onDelete={(id) => deleteSuggestion(id)}
            />
          ))
        ) : (
          <div className="p-8 rounded-2xl glass-panel text-center border border-white/5">
            <Lightbulb className="w-10 h-10 text-purple-400/40 mx-auto mb-2" />
            <h4 className="text-sm font-bold text-slate-300">Пока нет предложений</h4>
            <p className="text-xs text-slate-400 mt-1 mb-3">
              Будь первым, кто предложит крутую тему или задаст вопрос!
            </p>
            <button
              onClick={() => setIsSubmitModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-glow-purple inline-flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Предложить идею</span>
            </button>
          </div>
        )}
      </div>

      {/* Submit Modal */}
      <SuggestionModal
        isOpen={isSubmitModalOpen}
        onClose={() => setIsSubmitModalOpen(false)}
      />

      {/* Admin Moderate Modal */}
      <AdminReplyModal
        suggestion={moderatingSuggestion}
        isOpen={!!moderatingSuggestion}
        onClose={() => setModeratingSuggestion(null)}
      />
    </div>
  );
}
