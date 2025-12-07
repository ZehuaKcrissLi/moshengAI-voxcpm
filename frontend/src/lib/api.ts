import axios from 'axios';

// Use window.location.hostname to automatically match the frontend host
// Falls back to localhost for development
const API_URL = typeof window !== 'undefined' 
  ? `http://${window.location.hostname}:8000`
  : 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
}

export interface TaskStatus {
  task_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  output_url?: string;
  error?: string;
}

export const fetchVoices = async (): Promise<Voice[]> => {
  const response = await api.get('/voices/');
  return response.data;
};

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

