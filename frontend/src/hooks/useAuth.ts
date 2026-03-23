import { create } from "zustand";
import {
  authApi,
  type User,
  type LoginPayload,
  type RegisterPayload,
  type OtpVerifyPayload,
} from "@/lib/api";

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
  register: (data: RegisterPayload) => Promise<void>;
  login: (data: LoginPayload) => Promise<void>;
  sendOtp: (phone: string) => Promise<void>;
  verifyOtp: (data: OtpVerifyPayload) => Promise<void>;
  logout: () => void;
  hydrate: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  token: null,
  user: null,
  loading: true,

  register: async (data) => {
    const res = await authApi.register(data);
    const { access_token, user } = res.data;
    localStorage.setItem("prism_token", access_token);
    set({ token: access_token, user });
  },

  login: async (data) => {
    const res = await authApi.login(data);
    const { access_token, user } = res.data;
    localStorage.setItem("prism_token", access_token);
    set({ token: access_token, user });
  },

  sendOtp: async (phone) => {
    await authApi.sendOtp({ phone });
  },

  verifyOtp: async (data) => {
    const res = await authApi.verifyOtp(data);
    const { access_token, user } = res.data;
    localStorage.setItem("prism_token", access_token);
    set({ token: access_token, user });
  },

  logout: () => {
    localStorage.removeItem("prism_token");
    set({ token: null, user: null });
  },

  hydrate: async () => {
    const token = localStorage.getItem("prism_token");
    if (!token) {
      set({ loading: false });
      return;
    }
    try {
      const res = await authApi.me();
      set({ token, user: res.data, loading: false });
    } catch {
      localStorage.removeItem("prism_token");
      set({ token: null, user: null, loading: false });
    }
  },
}));
