import React, { useState, useEffect } from 'react';
import { Download, Trash2, Check, Loader2, HardDrive, Cpu } from 'lucide-react';
import { modelApi, jobApi, Model, JobStatus } from '../api/client';

const ModelManager: React.FC = () => {
    const [models, setModels] = useState<Model[]>([]);
    const [loading, setLoading] = useState(true);
    const [downloadingJobs, setDownloadingJobs] = useState<Map<string, string>>(new Map());
    const [jobStatuses, setJobStatuses] = useState<Map<string, JobStatus>>(new Map());

    useEffect(() => {
        loadModels();
        const interval = setInterval(loadModels, 5000); // Refresh every 5s
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        // Poll job statuses
        if (downloadingJobs.size > 0) {
            const interval = setInterval(pollJobStatuses, 1000);
            return () => clearInterval(interval);
        }
    }, [downloadingJobs]);

    const loadModels = async () => {
        try {
            const data = await modelApi.list();
            setModels(data);
            setLoading(false);
        } catch (error) {
            console.error('Failed to load models:', error);
            setLoading(false);
        }
    };

    const pollJobStatuses = async () => {
        const newStatuses = new Map(jobStatuses);
        const jobsToRemove: string[] = [];

        for (const [modelId, jobId] of downloadingJobs.entries()) {
            try {
                const status = await jobApi.getStatus(jobId);
                newStatuses.set(jobId, status);

                if (status.status === 'completed' || status.status === 'failed') {
                    jobsToRemove.push(modelId);
                    await loadModels(); // Refresh model list
                }
            } catch (error) {
                console.error(`Failed to get job status for ${jobId}:`, error);
            }
        }

        // Remove completed/failed jobs
        jobsToRemove.forEach(modelId => {
            const newJobs = new Map(downloadingJobs);
            newJobs.delete(modelId);
            setDownloadingJobs(newJobs);
        });

        setJobStatuses(newStatuses);
    };

    const handleDownload = async (modelId: string) => {
        try {
            const { job_id } = await modelApi.download(modelId);
            const newJobs = new Map(downloadingJobs);
            newJobs.set(modelId, job_id);
            setDownloadingJobs(newJobs);
        } catch (error) {
            console.error('Failed to start download:', error);
            alert('Failed to start download. Please try again.');
        }
    };

    const handleDelete = async (modelId: string) => {
        if (!confirm('Are you sure you want to delete this model?')) {
            return;
        }

        try {
            await modelApi.delete(modelId);
            await loadModels();
        } catch (error) {
            console.error('Failed to delete model:', error);
            alert('Failed to delete model. Please try again.');
        }
    };

    const formatSize = (mb: number): string => {
        if (mb < 1024) return `${mb}MB`;
        return `${(mb / 1024).toFixed(1)}GB`;
    };

    const getModelIcon = (type: string) => {
        switch (type) {
            case 'llm':
                return <Cpu className="w-5 h-5" />;
            default:
                return <HardDrive className="w-5 h-5" />;
        }
    };

    const getJobStatus = (modelId: string): JobStatus | null => {
        const jobId = downloadingJobs.get(modelId);
        if (!jobId) return null;
        return jobStatuses.get(jobId) || null;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
                        Model Manager
                    </h1>
                    <p className="text-dark-400 mt-1">Download and manage AI models</p>
                </div>
            </div>

            <div className="grid gap-4">
                {models.map((model) => {
                    const jobStatus = getJobStatus(model.id);
                    const isDownloading = jobStatus?.status === 'running';
                    const downloadFailed = jobStatus?.status === 'failed';

                    return (
                        <div
                            key={model.id}
                            className="card hover:bg-white/10 transition-all duration-200"
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex items-start space-x-4 flex-1">
                                    <div className="p-3 glass rounded-lg">
                                        {getModelIcon(model.type)}
                                    </div>

                                    <div className="flex-1">
                                        <div className="flex items-center space-x-3">
                                            <h3 className="text-lg font-semibold">{model.name}</h3>
                                            {model.installed && (
                                                <span className="flex items-center space-x-1 text-green-400 text-sm">
                                                    <Check className="w-4 h-4" />
                                                    <span>Installed</span>
                                                </span>
                                            )}
                                        </div>

                                        <p className="text-dark-400 text-sm mt-1">{model.description}</p>

                                        <div className="flex items-center space-x-4 mt-3 text-sm text-dark-400">
                                            <span className="flex items-center space-x-1">
                                                <HardDrive className="w-4 h-4" />
                                                <span>{formatSize(model.size_mb)}</span>
                                            </span>
                                            <span className="flex items-center space-x-1">
                                                <Cpu className="w-4 h-4" />
                                                <span>{formatSize(model.ram_required_mb)} RAM</span>
                                            </span>
                                            <span className="px-2 py-0.5 glass rounded text-xs uppercase">
                                                {model.type}
                                            </span>
                                        </div>

                                        {isDownloading && (
                                            <div className="mt-3">
                                                <div className="flex items-center justify-between text-sm mb-1">
                                                    <span className="text-primary-400">Downloading...</span>
                                                </div>
                                                <div className="w-full h-2 glass rounded-full overflow-hidden">
                                                    <div className="h-full bg-gradient-to-r from-primary-500 to-primary-600 animate-shimmer"
                                                        style={{ width: '100%', backgroundSize: '200% 100%' }} />
                                                </div>
                                            </div>
                                        )}

                                        {downloadFailed && (
                                            <div className="mt-3 text-red-400 text-sm">
                                                Download failed: {jobStatus?.error}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <div className="flex items-center space-x-2">
                                    {!model.installed && !isDownloading && (
                                        <button
                                            onClick={() => handleDownload(model.id)}
                                            className="btn-primary flex items-center space-x-2"
                                        >
                                            <Download className="w-4 h-4" />
                                            <span>Download</span>
                                        </button>
                                    )}

                                    {model.installed && (
                                        <button
                                            onClick={() => handleDelete(model.id)}
                                            className="btn-secondary flex items-center space-x-2 text-red-400 hover:text-red-300"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                            <span>Delete</span>
                                        </button>
                                    )}

                                    {isDownloading && (
                                        <button
                                            disabled
                                            className="btn-secondary flex items-center space-x-2 opacity-50 cursor-not-allowed"
                                        >
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span>Downloading</span>
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {models.length === 0 && (
                <div className="text-center py-12 text-dark-400">
                    <HardDrive className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No models available</p>
                </div>
            )}
        </div>
    );
};

export default ModelManager;
