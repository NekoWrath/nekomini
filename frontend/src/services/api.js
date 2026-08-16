// API Service with Telegram InitData and Mock Header support

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export function getAuthHeaders(initDataRaw, mockUser) {
  const headers = {
    'Content-Type': 'application/json',
  };

  if (initDataRaw) {
    headers['X-Telegram-Init-Data'] = initDataRaw;
  } else if (mockUser) {
    headers['X-Mock-User-Id'] = String(mockUser.id);
    headers['X-Mock-Role'] = mockUser.role;
  }

  return headers;
}

export const api = {
  // Auth
  async getMe(initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Auth failed: ${res.status}`);
    return res.json();
  },

  // Schedule
  async getStreams(initDataRaw, mockUser, statusFilter = '') {
    const url = statusFilter
      ? `${API_BASE_URL}/schedule?status_filter=${statusFilter}`
      : `${API_BASE_URL}/schedule`;
    const res = await fetch(url, {
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to fetch schedule: ${res.status}`);
    return res.json();
  },

  async getCurrentStream(initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/schedule/current`, {
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to fetch current stream: ${res.status}`);
    return res.json();
  },

  async toggleReminder(streamId, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/schedule/${streamId}/toggle-reminder`, {
      method: 'POST',
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to toggle reminder: ${res.status}`);
    return res.json();
  },

  async createStream(streamData, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/schedule`, {
      method: 'POST',
      headers: getAuthHeaders(initDataRaw, mockUser),
      body: JSON.stringify(streamData),
    });
    if (!res.ok) throw new Error(`Failed to create stream: ${res.status}`);
    return res.json();
  },

  async updateStream(streamId, streamData, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/schedule/${streamId}`, {
      method: 'PUT',
      headers: getAuthHeaders(initDataRaw, mockUser),
      body: JSON.stringify(streamData),
    });
    if (!res.ok) throw new Error(`Failed to update stream: ${res.status}`);
    return res.json();
  },

  async deleteStream(streamId, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/schedule/${streamId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to delete stream: ${res.status}`);
    return res.json();
  },

  async toggleLive(streamId, sendBroadcast = false, initDataRaw, mockUser) {
    const res = await fetch(
      `${API_BASE_URL}/schedule/${streamId}/toggle-live?send_broadcast=${sendBroadcast}`,
      {
        method: 'POST',
        headers: getAuthHeaders(initDataRaw, mockUser),
      }
    );
    if (!res.ok) throw new Error(`Failed to toggle live: ${res.status}`);
    return res.json();
  },

  // Suggestions
  async getSuggestions(initDataRaw, mockUser, tab = 'new', category = 'all', search = '') {
    const params = new URLSearchParams();
    if (tab) params.append('tab', tab);
    if (category && category !== 'all') params.append('category', category);
    if (search) params.append('search', search);

    const res = await fetch(`${API_BASE_URL}/suggestions?${params.toString()}`, {
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to fetch suggestions: ${res.status}`);
    return res.json();
  },

  async createSuggestion(data, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/suggestions`, {
      method: 'POST',
      headers: getAuthHeaders(initDataRaw, mockUser),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Failed to create suggestion: ${res.status}`);
    return res.json();
  },

  async voteSuggestion(suggestionId, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/suggestions/${suggestionId}/vote`, {
      method: 'POST',
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to vote: ${res.status}`);
    return res.json();
  },

  async moderateSuggestion(suggestionId, { status, admin_reply }, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/suggestions/${suggestionId}/moderate`, {
      method: 'POST',
      headers: getAuthHeaders(initDataRaw, mockUser),
      body: JSON.stringify({ status, admin_reply }),
    });
    if (!res.ok) throw new Error(`Failed to moderate suggestion: ${res.status}`);
    return res.json();
  },

  async deleteSuggestion(suggestionId, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/suggestions/${suggestionId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to delete suggestion: ${res.status}`);
    return res.json();
  },

  // Settings
  async getSettings(initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/settings`, {
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to fetch settings: ${res.status}`);
    return res.json();
  },

  async updateSettings(settingsData, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/settings`, {
      method: 'PUT',
      headers: getAuthHeaders(initDataRaw, mockUser),
      body: JSON.stringify(settingsData),
    });
    if (!res.ok) throw new Error(`Failed to update settings: ${res.status}`);
    return res.json();
  },

  // Admin
  async getAdminStats(initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/admin/stats`, {
      headers: getAuthHeaders(initDataRaw, mockUser),
    });
    if (!res.ok) throw new Error(`Failed to fetch admin stats: ${res.status}`);
    return res.json();
  },

  async sendBroadcast(broadcastData, initDataRaw, mockUser) {
    const res = await fetch(`${API_BASE_URL}/admin/broadcast`, {
      method: 'POST',
      headers: getAuthHeaders(initDataRaw, mockUser),
      body: JSON.stringify(broadcastData),
    });
    if (!res.ok) throw new Error(`Failed to send broadcast: ${res.status}`);
    return res.json();
  },
};
