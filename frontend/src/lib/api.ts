import axios from "axios";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("prism_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("prism_token");
      window.location.href = "/";
    }
    return Promise.reject(err);
  }
);

/* ── Auth ── */
export interface OtpSendPayload {
  phone: string;
}
export interface OtpVerifyPayload {
  phone: string;
  otp: string;
  name?: string;
}
export interface RegisterPayload {
  email: string;
  password: string;
  name: string;
}
export interface LoginPayload {
  email: string;
  password: string;
}
export interface User {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  role: string;
  level: number;
  xp_points: number;
  current_archetype_label: string | null;
  onboarded: boolean;
  school_id: string | null;
}
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

export const authApi = {
  register: (data: RegisterPayload) =>
    api.post<AuthResponse>("/auth/register", data),
  login: (data: LoginPayload) =>
    api.post<AuthResponse>("/auth/login", data),
  sendOtp: (data: OtpSendPayload) =>
    api.post("/auth/otp/send", data),
  verifyOtp: (data: OtpVerifyPayload) =>
    api.post<AuthResponse>("/auth/otp/verify", data),
  refresh: (refresh_token: string) =>
    api.post("/auth/refresh", { refresh_token }),
  me: () => api.get<User>("/auth/me"),
};

/* ── Spectrum ── */
export interface SpectrumData {
  analytical_creative: number;
  builder_explorer: number;
  leader_specialist: number;
  entrepreneur_steward: number;
  people_systems: number;
  primary_archetype: Archetype | null;
  secondary_archetype: Archetype | null;
  confidence_score: number;
  color_ratios: Record<string, number>;
  total_signals: number;
}
export interface Archetype {
  id: string;
  name: string;
  label: string;
  description: string;
  emoji_icon: string;
}

export const spectrumApi = {
  get: () => api.get<SpectrumData>("/spectrum/me"),
  history: (limit = 20) =>
    api.get("/spectrum/history", { params: { limit } }),
};

/* ── Worlds & Missions ── */
export interface World {
  id: string;
  name: string;
  slug: string;
  description: string;
  color_hex: string;
  icon_url: string | null;
  sort_order: number;
  mission_count: number;
  user_progress: number | null;
}
export interface Mission {
  id: string;
  world_id: string;
  title: string;
  type: string;
  difficulty: string;
  duration_seconds: number;
  content_payload: Record<string, unknown>;
  completed?: boolean;
  xp_earned?: number | null;
}
export interface MissionResult {
  scores: Record<string, number>;
  xp_earned: number;
  creativity_score: number;
  speed_score: number;
  accuracy_score: number;
  spectrum_update: Record<string, number> | null;
}

export const worldsApi = {
  list: () => api.get<World[]>("/game/worlds"),
  missions: (worldId: string) =>
    api.get<Mission[]>(`/game/worlds/${worldId}/missions`),
  startMission: (missionId: string) =>
    api.post(`/game/missions/${missionId}/start`),
  submitMission: (missionId: string, data: { responses: Record<string, unknown>; time_spent: number }) =>
    api.post<MissionResult>(`/game/missions/${missionId}/submit`, data),
  submitTot: (responses: { qid: string; choice: string }[]) =>
    api.post("/game/tot/submit-batch", { responses }),
  dailyQuest: () => api.get("/game/daily-quest"),
};

/* ── Careers ── */
export interface Career {
  id: string;
  title: string;
  slug: string;
  category: string;
  stream_fit: string;
  description: string;
  salary_range: Record<string, string>;
}

export const careersApi = {
  list: (params?: { stream?: string; q?: string; page?: number; limit?: number }) =>
    api.get("/careers", { params }),
  recommended: () => api.get("/careers/recommended"),
  get: (id: string) => api.get<Career>(`/careers/${id}`),
  bookmark: (id: string, notes?: string) =>
    api.post(`/careers/${id}/bookmark`, { notes }),
};

/* ── Prism Card ── */
export interface PrismCardData {
  id: string;
  card_data: Record<string, unknown>;
  image_url: string | null;
  share_token: string;
  is_public: boolean;
  generated_at: string;
}

export const cardApi = {
  generate: () => api.post<PrismCardData>("/cards/generate"),
  mine: () => api.get<PrismCardData[]>("/cards/me"),
  byToken: (token: string) =>
    api.get<PrismCardData>(`/cards/${token}`),
};

/* ── Chat (Ray AI) ── */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export const chatApi = {
  send: (message: string, session_id?: string) =>
    api.post<{ message: string; session_id: string }>("/ai/chat", {
      message,
      session_id,
    }),
  conversations: () => api.get("/ai/conversations"),
  conversation: (sessionId: string) =>
    api.get(`/ai/conversations/${sessionId}`),
};

/* ── Dashboard (school) ── */
export interface DashboardStats {
  total_students: number;
  active_students: number;
  avg_engagement: number;
  archetype_distribution: Record<string, number>;
  stream_readiness: Record<string, number>;
}

export const dashboardApi = {
  stats: () => api.get<DashboardStats>("/school/dashboard"),
  classes: () => api.get("/school/classes"),
  students: (params?: { class_id?: string; page?: number }) =>
    api.get("/school/students", { params }),
};

export default api;
