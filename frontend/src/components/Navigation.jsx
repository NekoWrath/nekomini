import React from 'react';
import { useApp } from '../context/AppContext';
import { Calendar, Lightbulb, Bell, Shield, Radio } from 'lucide-react';

export function Navigation() {
  const { activeTab, switchTab, currentUser, adminStats, currentStream } = useApp();
  const isAdmin = currentUser?.role === 'admin' || currentUser?.role === 'moderator';
  const isLive = currentStream?.is_live || false;

  const tabs = [
    {
      id: 'schedule',
      label: 'Расписание',
      icon: Calendar,
      badge: isLive ? 'LIVE' : null,
      badgeClass: 'bg-rose-500 text-white animate-pulse',
    },
    {
      id: 'suggestions',
      label: 'Предложка',
      icon: Lightbulb,
    },
    {
      id: 'settings',
      label: 'Настройки',
      icon: Bell,
    },
  ];

  if (isAdmin) {
    tabs.push({
      id: 'admin',
      label: 'Админка',
      icon: Shield,
      badge: adminStats?.pending_suggestions > 0 ? adminStats.pending_suggestions : null,
      badgeClass: 'bg-purple-600 text-white font-bold',
    });
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 glass-nav border-t border-indigo-500/20 safe-pb">
      <div className="max-w-md mx-auto px-2 pt-2 pb-1 flex items-center justify-around">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => switchTab(tab.id)}
              className={`relative flex flex-col items-center justify-center flex-1 py-1 px-2 rounded-xl transition-all duration-200 btn-press ${
                isActive
                  ? 'text-purple-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {/* Active glow pill */}
              {isActive && (
                <span className="absolute -top-1 w-8 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full shadow-glow-purple" />
              )}

              <div className="relative mt-0.5">
                <Icon className={`w-5 h-5 transition-transform ${isActive ? 'scale-110 text-purple-400' : ''}`} />
                
                {/* Badge (e.g. LIVE or pending count) */}
                {tab.badge && (
                  <span className={`absolute -top-1.5 -right-3 text-[9px] px-1 py-0.2 rounded-full font-bold leading-none ${tab.badgeClass}`}>
                    {tab.badge}
                  </span>
                )}
              </div>

              <span className={`text-[11px] mt-1 tracking-tight ${isActive ? 'text-purple-300' : 'text-slate-400'}`}>
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
