const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  getInventory: () => fetchAPI<any[]>('/inventory'),
  getRequests: () => fetchAPI<any[]>('/requests'),
  getAuditLogs: () => fetchAPI<any[]>('/audit'),
  postRequisition: (data: any) => fetchAPI<any>('/requests', {
    method: 'POST',
    body: JSON.stringify(data)
  }),
};
