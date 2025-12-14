import axios from 'axios';

// Use Next.js rewrite proxy: /api/* -> http://localhost:33000/*
// This allows the backend to stay on localhost without exposing port 33000 to the public
const API_URL = typeof window !== 'undefined' 
  ? '/api'  // Browser: use relative path, Next.js will proxy to localhost:33000
  : 'http://localhost:33000';  // SSR: direct access to backend

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
    return Promise.reject(error);
  }
);

export interface Voice {
  id: string;
  name: string;
  category: string;
  preview_url: string;
  transcript: string;
}

export interface GenerateResponse {
  task_id: string;
  status: string;
  cost: number;
}

export interface TaskStatus {
  task_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  output_url?: string;
  error?: string;
}

export interface UserResponse {
  id: string;
  email: string;
  provider: string;
  avatar?: string;
  credits_balance: number;
  is_admin: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface BalanceResponse {
  balance: number;
  user_id: string;
}

// Auth APIs
export const register = async (email: string, password: string): Promise<UserResponse> => {
  const response = await api.post('/auth/register', { email, password });
  return response.data;
};

export const login = async (email: string, password: string): Promise<LoginResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', email); // OAuth2 spec uses 'username' field
  formData.append('password', password);
  
  const response = await api.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const getMe = async (): Promise<UserResponse> => {
  const response = await api.get('/auth/me');
  return response.data;
};

export const getCreditsBalance = async (): Promise<BalanceResponse> => {
  const response = await api.get('/credits/balance');
  return response.data;
};

// Voice APIs
export const fetchVoices = async (): Promise<Voice[]> => {
  const response = await api.get('/voices/');
  return response.data;
};

// TTS APIs
export const generateAudio = async (text: string, voiceId: string): Promise<GenerateResponse> => {
  const response = await api.post('/tts/generate', {
    text,
    voice_id: voiceId,
  });
  return response.data;
};

export const getTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  const response = await api.get(`/tts/status/${taskId}`);
  return response.data;
};

