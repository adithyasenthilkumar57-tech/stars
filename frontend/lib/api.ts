/**
 * ClearWay AI — API client
 * All calls go through /api/ which Next.js proxies to the FastAPI backend.
 */

const BASE = '/api';

async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  // Traffic
  getLiveTraffic: () => apiFetch('/traffic/live'),
  getTrafficHistory: (hours = 24, id?: string) =>
    apiFetch(`/traffic/history?hours=${hours}${id ? `&intersection_id=${id}` : ''}`),

  // Intersections
  getIntersections: () => apiFetch('/intersections'),
  getIntersection: (id: string) => apiFetch(`/intersections/${id}`),

  // Cameras
  getCameras: () => apiFetch('/cameras'),
  analyzeCamera: (cameraId: string) => apiFetch(`/cameras/${cameraId}/analyze`),

  // Microphones
  getMicrophones: () => apiFetch('/microphones'),

  // Optimization
  runOptimization: (method: string, intersectionIds?: string[]) =>
    apiFetch('/optimization/run', {
      method: 'POST',
      body: JSON.stringify({ method, intersection_ids: intersectionIds }),
    }),
  getOptimizationMethods: () => apiFetch('/optimization/methods'),

  // Emergency
  activateEmergency: (origin: string, destination?: string, via?: string) =>
    apiFetch('/emergency/activate', {
      method: 'POST',
      body: JSON.stringify({ origin_intersection_id: origin, destination_name: destination || 'City Hospital', detected_via: via || 'MANUAL' }),
    }),
  advanceCorridor: () => apiFetch('/emergency/advance', { method: 'POST', body: '{}' }),
  completeCorridor: () => apiFetch('/emergency/complete', { method: 'POST', body: '{}' }),
  resetCorridor: () => apiFetch('/emergency/reset', { method: 'POST', body: '{}' }),
  getEmergencyStatus: () => apiFetch('/emergency/status'),

  // Siren
  triggerSirenDetection: (junctionId: string) =>
    apiFetch(`/siren/detect/${junctionId}?force=true`, { method: 'POST', body: '{}' }),
  getSirenStatuses: () => apiFetch('/siren/status'),
  getSirenStatus: (id: string) => apiFetch(`/siren/status/${id}`),
  getSirenEvents: () => apiFetch('/siren/events'),
  getDispatches: () => apiFetch('/siren/dispatches'),
  acknowledgeSiren: (sirenEventId: string, status: string, officerId?: string) =>
    apiFetch('/siren/acknowledge', {
      method: 'POST',
      body: JSON.stringify({ siren_event_id: sirenEventId, officer_status: status, officer_id: officerId }),
    }),

  // Pollution
  getPollutionEstimates: (id?: string) =>
    apiFetch(`/pollution/estimates${id ? `?intersection_id=${id}` : ''}`),
  getPollutionTrend: (id: string, hours = 24) =>
    apiFetch(`/pollution/trend/${id}?hours=${hours}`),

  // Predictions
  getPredictions: () => apiFetch('/predictions'),

  // Simulation
  runSimulation: (scenario: Record<string, unknown>) =>
    apiFetch('/simulation/run', { method: 'POST', body: JSON.stringify({ scenario }) }),

  // Events
  triggerEvent: (type: string, intersectionId?: string) =>
    apiFetch('/events', { method: 'POST', body: JSON.stringify({ type, intersection_id: intersectionId }) }),

  // AI Chat
  chat: (message: string, context?: Record<string, unknown>) =>
    apiFetch('/ai/chat', { method: 'POST', body: JSON.stringify({ message, context }) }),

  // Reports
  generateReport: (format: string) =>
    fetch(`${BASE}/reports/generate`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ format }) }),

  // Auth
  login: (email: string, password: string) =>
    apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  getDemoUsers: () => apiFetch('/auth/demo-users'),
  getFirebaseConfig: () => apiFetch('/auth/config'),

  // Health
  health: () => apiFetch('/health'),
};

export default api;
