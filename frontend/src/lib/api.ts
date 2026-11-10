/**
 * Typed API Client for Site DNA FastAPI Backend.
 */

export interface AgentRegistryItem {
  id: string;
  phase: number;
  name: string;
  name_ar: string;
  description: string;
  description_ar: string;
  icon: string;
  category: string;
  implementation_status: 'implemented' | 'planned' | 'disabled';
  runtime_availability:
    | 'ready'
    | 'running'
    | 'completed'
    | 'partial'
    | 'ai_blocked'
    | 'failed'
    | 'unavailable'
    | 'not_implemented';
  can_execute: boolean;
  requires_visual: boolean;
  dependencies: string[];
  output_types: string[];
  display_order: number;
  model_name: string;
}

export interface StageExecutionRecord {
  stage_id: string;
  name: string;
  name_ar: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'partial' | 'ai_blocked' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
  duration_ms: number;
  score?: number;
  findings_count: number;
  recommendations_count: number;
  error_message?: string;
  output_path?: string;
  analysis_run_id?: string;
}

export interface RunRecord {
  run_id: string;
  url: string;
  canonical_origin?: string;
  status: 'created' | 'queued' | 'running' | 'completed' | 'partial' | 'ai_blocked' | 'failed' | 'cancelled';
  created_at: string;
  completed_at?: string;
  total_duration_ms: number;
  stages: Record<string, StageExecutionRecord>;
  visual_run_id?: string;
  scores: Record<string, number>;
  overall_score?: number;
  total_findings: number;
  total_recommendations: number;
  error_message?: string;
}

export interface RunEvent {
  event_id: string;
  run_id: string;
  stage_id?: string;
  event_type: string;
  message: string;
  message_ar: string;
  timestamp: string;
  data: Record<string, any>;
}

export interface DashboardSummary {
  total_runs: number;
  completed_runs: number;
  running_runs: number;
  failed_runs: number;
  total_findings: number;
  total_recommendations: number;
  recent_runs: any[];
  agent_readiness: Record<string, any>;
}

export interface RunSubmissionRequest {
  url: string;
  stages: string[];
  max_pages?: number;
  full_site_scan?: boolean;
  offline_mode?: boolean;
  deterministic_only?: boolean;
  competitor_urls?: string[];
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

const API_BASE = '/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errMsg = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      errMsg = errJson.detail || errJson.message || errMsg;
    } catch {}
    throw new ApiError(errMsg, response.status);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  getAgents: () => request<AgentRegistryItem[]>('/agents'),
  getAgent: (id: string) => request<AgentRegistryItem>(`/agents/${encodeURIComponent(id)}`),
  getDashboardSummary: () => request<DashboardSummary>('/dashboard/summary'),
  getRuns: (params?: { query?: string; status?: string; page?: number; page_size?: number }) => {
    const q = new URLSearchParams();
    if (params?.query) q.set('query', params.query);
    if (params?.status) q.set('status', params.status);
    if (params?.page) q.set('page', String(params.page));
    if (params?.page_size) q.set('page_size', String(params.page_size));
    const qs = q.toString() ? `?${q.toString()}` : '';
    return request<{ items: RunRecord[]; total: number; page: number; page_size: number; pages_count: number }>(`/runs${qs}`);
  },
  submitRun: (data: RunSubmissionRequest) =>
    request<RunRecord>('/runs', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getRun: (runId: string) => request<RunRecord>(`/runs/${encodeURIComponent(runId)}`),
  getAIAutomation: (runId: string) => request<any>(`/runs/${encodeURIComponent(runId)}/ai-automation`),
  getScreenshots: (runId: string) => request<any[]>(`/runs/${encodeURIComponent(runId)}/screenshots`),
  getFindings: (runId: string, agent?: string) => {
    const qs = agent ? `?agent=${encodeURIComponent(agent)}` : '';
    return request<any[]>(`/runs/${encodeURIComponent(runId)}/findings${qs}`);
  },
  getRecommendations: (runId: string, priority?: string) => {
    const qs = priority ? `?priority=${encodeURIComponent(priority)}` : '';
    return request<any[]>(`/runs/${encodeURIComponent(runId)}/recommendations${qs}`);
  },
  getReport: (runId: string, stageId: string, format: 'markdown' | 'json' = 'markdown') =>
    request<{ run_id: string; stage_id: string; format: string; filename: string; content: string }>(
      `/runs/${encodeURIComponent(runId)}/reports/${encodeURIComponent(stageId)}?format=${format}`
    ),
  getCompetitorAnalysis: (id: string) => request<any>(`/analysis/competitors/${encodeURIComponent(id)}`),
  getCompetitorMatrix: (id: string) => request<any>(`/analysis/competitors/${encodeURIComponent(id)}/matrix`),
  runCompetitorAnalysis: (body: any) =>
    request<any>('/analysis/competitors', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getSecurityReport: (crawlRunId: string) =>
    request<any>(`/analysis/security-privacy/${encodeURIComponent(crawlRunId)}`),
  getSecurityHeaders: (crawlRunId: string) =>
    request<any>(`/analysis/security-privacy/${encodeURIComponent(crawlRunId)}/headers`),
  runSecurityAnalysis: (body: any) =>
    request<any>('/analysis/security-privacy', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getAccessibilityReport: (crawlRunId: string) =>
    request<any>(`/analysis/accessibility/${encodeURIComponent(crawlRunId)}`),
  getWcagCriteria: (crawlRunId: string) =>
    request<any[]>(`/analysis/accessibility/${encodeURIComponent(crawlRunId)}/wcag`),
  updateManualReviewTask: (crawlRunId: string, reviewId: string, reviewStatus: string, notes?: string) =>
    request<any>(`/analysis/accessibility/${encodeURIComponent(crawlRunId)}/tasks/${encodeURIComponent(reviewId)}`, {
      method: 'POST',
      body: JSON.stringify({ status: reviewStatus, notes }),
    }),
  runAccessibilityAnalysis: (body: any) =>
    request<any>('/analysis/accessibility', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getStrategicReport: (crawlRunId: string) =>
    request<any>(`/analysis/strategy/${encodeURIComponent(crawlRunId)}`),
  getStrategicActions: (crawlRunId: string, priority?: string, wave?: number) => {
    const q = new URLSearchParams();
    if (priority) q.set('priority', priority);
    if (wave !== undefined) q.set('wave', String(wave));
    const qs = q.toString() ? `?${q.toString()}` : '';
    return request<any[]>(`/analysis/strategy/${encodeURIComponent(crawlRunId)}/actions${qs}`);
  },
  getStrategicConflicts: (crawlRunId: string) =>
    request<any[]>(`/analysis/strategy/${encodeURIComponent(crawlRunId)}/conflicts`),
  getStrategicRoadmap: (crawlRunId: string) =>
    request<any[]>(`/analysis/strategy/${encodeURIComponent(crawlRunId)}/roadmap`),
  updateActionStatus: (crawlRunId: string, actionId: string, status: string, notes?: string) =>
    request<any>(`/analysis/strategy/${encodeURIComponent(crawlRunId)}/actions/${encodeURIComponent(actionId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    }),
  runStrategicAnalysis: (body: any) =>
    request<any>('/analysis/strategy', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getFinalReports: (crawlRunId: string) =>
    request<any[]>(`/reports/final/${encodeURIComponent(crawlRunId)}`),
  getFinalReportMetadata: (crawlRunId: string, reportId: string) =>
    request<any>(`/reports/final/${encodeURIComponent(crawlRunId)}/${encodeURIComponent(reportId)}`),
  getFinalReportArtifacts: (crawlRunId: string, reportId: string) =>
    request<any>(`/reports/final/${encodeURIComponent(crawlRunId)}/${encodeURIComponent(reportId)}/artifacts`),
  generateFinalReport: (body: {
    crawl_run_id: string;
    mode?: 'comprehensive' | 'executive' | 'agent';
    language?: 'ar' | 'en';
    paper_size?: 'A4' | 'Letter';
  }) =>
    request<any>('/reports/final', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getDownloadReportUrl: (crawlRunId: string, reportId: string, format: string = 'pdf') =>
    `/api/v1/reports/final/${encodeURIComponent(crawlRunId)}/${encodeURIComponent(reportId)}/download?format=${format}`,
  getPreviewReportUrl: (crawlRunId: string, reportId: string) =>
    `/api/v1/reports/final/${encodeURIComponent(crawlRunId)}/${encodeURIComponent(reportId)}/preview`,
  getHealth: () => request<{ status: string }>('/health'),
};
