import { format, formatDistanceToNow, isToday, isTomorrow, isThisWeek } from 'date-fns';
import { ru } from 'date-fns/locale';

export function formatStreamDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  
  if (isToday(date)) {
    return `Сегодня в ${format(date, 'HH:mm')}`;
  }
  if (isTomorrow(date)) {
    return `Завтра в ${format(date, 'HH:mm')}`;
  }
  if (isThisWeek(date)) {
    return format(date, 'EEEE в HH:mm', { locale: ru });
  }
  return format(date, 'd MMMM в HH:mm', { locale: ru });
}

export function formatShortDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return format(date, 'dd.MM HH:mm');
}

export function formatTimeAgo(dateString) {
  if (!dateString) return '';
  return formatDistanceToNow(new Date(dateString), { addSuffix: true, locale: ru });
}

export const CATEGORY_CONFIG = {
  game_idea: {
    label: 'Идея для игры',
    emoji: '🎮',
    badgeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  },
  question: {
    label: 'Вопрос стримеру',
    emoji: '❓',
    badgeClass: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  },
  challenge: {
    label: 'Челлендж',
    emoji: '🔥',
    badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  },
  other: {
    label: 'Другое',
    emoji: '💬',
    badgeClass: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  },
};

export const STATUS_CONFIG = {
  pending: {
    label: 'На рассмотрении',
    badgeClass: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
    icon: '⏳',
  },
  accepted: {
    label: 'Взято на стрим',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium',
    icon: '✅',
  },
  rejected: {
    label: 'Отклонено',
    badgeClass: 'bg-rose-500/10 text-rose-400 border border-rose-500/30',
    icon: '❌',
  },
  answered: {
    label: 'Отвечено',
    badgeClass: 'bg-blue-500/10 text-blue-400 border border-blue-500/30',
    icon: '💬',
  },
};

export const PLATFORM_CONFIG = {
  Twitch: {
    name: 'Twitch',
    color: '#9146ff',
    badgeClass: 'bg-[#9146ff]/20 text-[#c084fc] border-[#9146ff]/40',
  },
  Kick: {
    name: 'Kick',
    color: '#53fc18',
    badgeClass: 'bg-[#53fc18]/20 text-[#4ade80] border-[#53fc18]/40',
  },
  'VK Video': {
    name: 'VK Видео',
    color: '#0077ff',
    badgeClass: 'bg-[#0077ff]/20 text-[#60a5fa] border-[#0077ff]/40',
  },
  YouTube: {
    name: 'YouTube',
    color: '#ff0000',
    badgeClass: 'bg-[#ff0000]/20 text-[#f87171] border-[#ff0000]/40',
  },
};
