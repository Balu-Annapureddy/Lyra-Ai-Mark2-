import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface Model {
    id: string;
    name: string;
    description: string;
    size_mb: number;
    ram_required_mb: number;
    type: 'llm' | 'stt' | 'tts' | 'vision';
    url: string;
    sha256: string;
    installed: boolean;
    install_path?: string;
}

export interface JobStatus {
    job_id: string;
    name: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error?: string;
}

export interface HealthStatus {
    status: 'healthy' | 'degraded' | 'critical';
    [key: string]: any;
}

// API functions
export const modelApi = {
    list: async (): Promise<Model[]> => {
        const response = await api.get('/models');
        return response.data.models;
    },

    download: async (modelId: string): Promise<{ job_id: string }> => {
        const response = await api.post('/models/download', { model_id: modelId });
        return response.data;
    },

    delete: async (modelId: string): Promise<void> => {
        await api.delete(`/models/${modelId}`);
    },
};

export const jobApi = {
    getStatus: async (jobId: string): Promise<JobStatus> => {
        const response = await api.get(`/jobs/${jobId}`);
        return response.data;
    },
};

export const healthApi = {
    getOverall: async (): Promise<HealthStatus> => {
        const response = await api.get('/health/');
        return response.data;
    },

    getCore: async (): Promise<HealthStatus> => {
        const response = await api.get('/health/core');
        return response.data;
    },

    getGPU: async (): Promise<HealthStatus> => {
        const response = await api.get('/health/gpu');
        return response.data;
    },

    getMemory: async (): Promise<HealthStatus> => {
        const response = await api.get('/health/memory');
        return response.data;
    },
};

export default api;
