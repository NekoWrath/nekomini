import React from 'react';
import { useApp } from './context/AppContext';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { MockTelegramBar } from './components/MockTelegramBar';
import { SchedulePage } from './pages/SchedulePage';
import { SuggestionsPage } from './pages/SuggestionsPage';
import { SettingsPage } from './pages/SettingsPage';
import { AdminPage } from './pages/AdminPage';
import { Sparkles, CheckCircle2, AlertCircle, Info } from 'lucide-react';

export function AppContent() {
  const { activeTab, loading, toastMessage } = useApp();

  return (
    <div className="min-h-screen bg-background-darkest text-slate-100 flex flex-col max-w-md mx-auto relative shadow-2xl overflow-x-hidden">
      {/* Dev Mode Role Switcher Bar (visible when opened outside Telegram) */}
      <MockTelegramBar />

      {/* Main Header */}
      <Header />

      {/* Main Page Content */}
      <main className="flex-1">
        {loading ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
            <div className="relative w-12 h-12">
              <div className="w-12 h-12 rounded-full border-2 border-purple-500/20 border-t-purple-500 animate-spin" />
              <Sparkles className="w-5 h-5 text-purple-400 absolute inset-0 m-auto animate-pulse" />
            </div>
            <span className="text-xs text-slate-400 font-medium">
              Загрузка стример-хаба...
            </span>
          </div>
        ) : (
          <>
            {activeTab === 'schedule' && <SchedulePage />}
            {activeTab === 'suggestions' && <SuggestionsPage />}
            {activeTab === 'settings' && <SettingsPage />}
            {activeTab === 'admin' && <AdminPage />}
          </>
        )}
      </main>

      {/* Bottom Navigation */}
      <Navigation />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-14 left-4 right-4 z-50 max-w-sm mx-auto flex items-center gap-2.5 p-3 rounded-2xl bg-slate-900/95 border border-purple-500/50 shadow-glass text-xs font-semibold text-white animate-float backdrop-blur-xl">
          {toastMessage.type === 'success' && (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          )}
          {toastMessage.type === 'error' && (
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          )}
          {toastMessage.type === 'info' && (
            <Info className="w-4 h-4 text-cyan-400 flex-shrink-0" />
          )}
          <span className="flex-1">{toastMessage.text}</span>
        </div>
      )}
    </div>
  );
}

export default function App() {
  return <AppContent />;
}
