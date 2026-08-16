import React from 'react';
import { useTelegram } from '../context/TelegramContext';
import { Shield, UserCheck, Eye, Terminal } from 'lucide-react';

export function MockTelegramBar() {
  const { isInsideTelegram, mockUser, switchMockRole } = useTelegram();

  if (isInsideTelegram) return null;

  return (
    <div className="bg-gradient-to-r from-indigo-950 via-slate-900 to-purple-950 border-b border-indigo-500/30 px-3 py-2 text-xs text-slate-300 flex items-center justify-between sticky top-0 z-50 backdrop-blur-md">
      <div className="flex items-center gap-1.5 font-medium text-indigo-300">
        <Terminal className="w-3.5 h-3.5 text-purple-400" />
        <span className="hidden sm:inline">Browser Dev Mode:</span>
        <span className="text-slate-400">Роль:</span>
        <span className={`font-bold px-1.5 py-0.5 rounded text-[11px] ${
          mockUser.role === 'admin' 
            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' 
            : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
        }`}>
          {mockUser.role === 'admin' ? '🛡️ Стример / Админ' : '👤 Зритель'}
        </span>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => switchMockRole('viewer')}
          className={`px-2 py-1 rounded transition-all flex items-center gap-1 ${
            mockUser.role === 'viewer'
              ? 'bg-emerald-600 text-white font-semibold shadow-sm'
              : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300'
          }`}
        >
          <Eye className="w-3 h-3" />
          <span>Зритель</span>
        </button>
        <button
          onClick={() => switchMockRole('admin')}
          className={`px-2 py-1 rounded transition-all flex items-center gap-1 ${
            mockUser.role === 'admin'
              ? 'bg-purple-600 text-white font-semibold shadow-sm'
              : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300'
          }`}
        >
          <Shield className="w-3 h-3" />
          <span>Стример</span>
        </button>
      </div>
    </div>
  );
}
