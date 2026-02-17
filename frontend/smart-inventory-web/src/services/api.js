import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
});

export const analytics = {
    getStats: () => api.get('/analytics/dashboard/stats'),
};

export const inventory = {
    getLocations: () => api.get('/inventory/locations'),
    getItems: () => api.get('/inventory/items'),
    getLocationItems: (locationId) => api.get(`/inventory/location/${locationId}/items`),
    addTransaction: (data) => api.post('/inventory/transaction', data),
    addBulkTransaction: (data) => api.post('/inventory/bulk-transaction', data),
};

export const chat = {
    query: (data) => api.post('/chat/query', data),
    getSessions: () => api.get('/chat/sessions'),
    getHistory: (id) => api.get(`/chat/history/${id}`),
    transcribe: (audioBlob) => {
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.wav');
        return api.post('/chat/transcribe', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },
};

export default api;
