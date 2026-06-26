const API_BASE = '';

export interface DashboardData {
  user_id: number;
  medications_count: number;
  medications: { id: number; name: string; dosage: string }[];
  today_reminders: { id: number; medication: string; dosage: string; time: string; status: string }[];
  adherence: { adherence_rate: number; taken: number; missed: number; skipped: number; total_doses: number };
  heatmap: { date: string; taken: number; missed: number; skipped: number }[];
  caregivers: { id: number; name: string; email: string | null; notify_on_miss_count: number }[];
}

export interface CollaborationStep {
  from: string;
  to: string;
  action: string;
  reason: string;
  result: string;
}

export interface ChatResponse {
  response: string;
  agent: string;
  traces: {
    agent: string;
    tool?: string;
    args?: Record<string, unknown>;
    collaboration?: CollaborationStep[];
  }[];
}

export interface OCRMedication {
  name: string;
  dosage: string;
  instructions: string;
  time_of_day: string;
}

export interface OCRResponse {
  medications: OCRMedication[];
  patient_name?: string | null;
  doctor_name?: string | null;
  confidence: string;
  registered_ids: number[];
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || 'Request failed');
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

export const api = {
  dashboard: (userId: number) => request<DashboardData>(`/api/v1/dashboard/${userId}`),
  chat: (message: string, userId: string | number = '1') =>
    request<ChatResponse>('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, user_id: String(userId) }),
    }),
  logAdherence: (userId: number, medicationId: number, status: string) =>
    request('/api/v1/users/' + userId + '/adherence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ medication_id: medicationId, status }),
    }),
  exportCsv: (userId: number) => window.open(`/api/v1/users/${userId}/reports/csv`),
  exportPdf: (userId: number) => window.open(`/api/v1/users/${userId}/reports/pdf`),
  ocrUpload: async (file: File, userId: number, autoRegister: boolean) => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(
      `/api/v1/ocr/prescription?user_id=${userId}&auto_register=${autoRegister}`,
      { method: 'POST', body: form },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'OCR failed' }));
      const detail = Array.isArray(err.detail)
        ? err.detail.map((item: { msg?: string }) => item.msg).join(', ')
        : err.detail || err.message || 'OCR failed';
      throw new Error(detail);
    }
    return res.json() as Promise<OCRResponse>;
  },
};

export function speak(text: string) {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    speechSynthesis.speak(utterance);
  }
}
