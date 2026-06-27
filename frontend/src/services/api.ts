import axios from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken && !originalRequest._retry) {
        if (isRefreshing) {
          return new Promise<string>((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          }).then(token => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return api(originalRequest);
          });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const resp = await axios.post(`${API_BASE_URL}/auth/refresh`, null, {
            params: { refresh_token: refreshToken },
          });
          const { access_token, refresh_token: newRefresh } = resp.data;
          localStorage.setItem('token', access_token);
          localStorage.setItem('refresh_token', newRefresh);
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          processQueue(null, access_token);
          originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('role');
          localStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      // No refresh token — clear and redirect
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('role');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export const authApi = {
  signup: (data: any) => api.post('/auth/signup', data),
  login: (data: any) => api.post('/auth/login', data),
};

export const userApi = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data: { name?: string; email?: string }) => api.put('/users/profile', data),
  changePassword: (data: { current_password: string; new_password: string }) => api.put('/users/password', data),
  deleteAccount: () => api.delete('/users/account'),
};

export const resumeApi = {
  upload: (formData: FormData, onProgress?: (pct: number) => void) => {
    return new Promise<any>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE_URL}/resumes/upload`);
      const token = localStorage.getItem('token');
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || 'Upload failed'));
          } catch {
            reject(new Error('Upload failed'));
          }
        }
      };
      xhr.onerror = () => reject(new Error('Network error'));
      xhr.send(formData);
    });
  },
  getMyResumes: (params?: { page?: number; per_page?: number; search?: string; active_only?: boolean }) =>
    api.get('/resumes/', { params }),
  getResume: (resumeId: number) => api.get(`/resumes/${resumeId}`),
  getVersions: (resumeId: number) => api.get(`/resumes/${resumeId}/versions`),
  createVersion: (resumeId: number) => api.post(`/resumes/${resumeId}/versions`),
  setActive: (resumeId: number) => api.put(`/resumes/${resumeId}/active`),
  getActive: () => api.get('/resumes/active'),
  delete: (resumeId: number) => api.delete(`/resumes/${resumeId}`),
  bulkDelete: (resumeIds: number[]) => api.post('/resumes/bulk-delete', { resume_ids: resumeIds }),
  compare: (resumeIdA: number, resumeIdB: number) =>
    api.post('/resumes/compare', { resume_id_a: resumeIdA, resume_id_b: resumeIdB }),
};

export const interviewApi = {
  create: (data: { role: string; difficulty?: string; interview_type?: string }) => api.post('/interviews/', data),
  retry: (data: { role: string; difficulty?: string; interview_type?: string }) => api.post('/interviews/retry', data),
  getMyInterviews: () => api.get('/interviews/'),
  getSession: (sessionId: number) => api.get(`/interviews/${sessionId}`),
  getFeedback: (sessionId: number) => api.get(`/interviews/${sessionId}/feedback`),
  downloadReport: (sessionId: number) => api.get(`/interviews/${sessionId}/report`, { responseType: 'blob' }),
  getQuestions: (sessionId: number) => api.get(`/interviews/${sessionId}/questions`),
  submitAnswer: (sessionId: number, questionId: number, answer: string) =>
    api.post(`/interviews/${sessionId}/questions/${questionId}/answer`, { answer }),
};

export const analyticsApi = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getInterview: () => api.get('/analytics/interview'),
  getCoding: () => api.get('/analytics/coding'),
  getSkills: () => api.get('/analytics/skills'),
  getLearning: () => api.get('/analytics/learning'),
  getCareer: () => api.get('/analytics/career'),
  getTopics: () => api.get('/analytics/topics'),
  getHistory: () => api.get('/analytics/history'),
  getPredictions: () => api.get('/analytics/predictions'),
};

export const codingApi = {
  // Challenges
  getChallenges: () => api.get('/coding/challenges'),
  getChallenge: (challengeId: number) => api.get(`/coding/challenges/${challengeId}`),

  // Session management
  startSession: (data: { interview_session_id?: number; language?: string }) =>
    api.post('/coding/session/start', data),
  getSession: (codingSessionId: number) => api.get(`/coding/session/${codingSessionId}`),
  retry: (data: { interview_session_id?: number; language?: string }) =>
    api.post('/coding/retry', data),

  // Execution
  runCode: (data: { challenge_id: number; code: string; language: string; coding_session_id?: number }) =>
    api.post('/coding/run', data),
  submitCode: (data: { challenge_id: number; code: string; language: string; coding_session_id?: number; session_id?: number }) =>
    api.post('/coding/submit', data),

  // History & Results
  getSubmissions: (params?: { coding_session_id?: number; challenge_id?: number }) =>
    api.get('/coding/submissions', { params }),
  getLatestSubmission: (coding_session_id: number) =>
    api.get('/coding/latest-submission', { params: { coding_session_id } }),
};

export const careerApi = {
  // Job Descriptions
  uploadJobDescription: (formData: FormData, onProgress?: (pct: number) => void) => {
    return new Promise<any>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE_URL}/career/job-description/upload`);
      const token = localStorage.getItem('token');
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || 'Upload failed'));
          } catch {
            reject(new Error('Upload failed'));
          }
        }
      };
      xhr.onerror = () => reject(new Error('Network error'));
      xhr.send(formData);
    });
  },
  analyzeJobDescription: (jdId: number) => api.post(`/career/job-description/analyze/${jdId}`),
  getJobDescriptions: (params?: { page?: number; per_page?: number; search?: string }) =>
    api.get('/career/job-descriptions', { params }),
  getJobDescription: (jdId: number) => api.get(`/career/job-description/${jdId}`),
  updateJobDescription: (jdId: number, formData: FormData) =>
    api.put(`/career/job-description/${jdId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // Career Analysis
  analyzeCareer: (resumeId: number, jobDescriptionId?: number) =>
    api.post('/career/analyze', null, { params: { resume_id: resumeId, job_description_id: jobDescriptionId } }),
  getResumeAnalysis: (analysisId: number) => api.get(`/career/resume-analysis/${analysisId}`),
  getResumeAnalyses: () => api.get('/career/resume-analyses'),

  // Skill Gap
  getSkillGap: (gapId: number) => api.get(`/career/skill-gap/${gapId}`),
  getSkillGapAnalyses: (page = 1, perPage = 20, search?: string) =>
    api.get('/career/skill-gap-analyses', { params: { page, per_page: perPage, search } }),
  analyzeSkillGap: (resumeAnalysisId?: number, jobDescriptionId?: number) =>
    api.post('/career/skill-gap/analyze', null, { params: { resume_analysis_id: resumeAnalysisId, job_description_id: jobDescriptionId } }),
  getSkillGapTrend: (limit = 10) =>
    api.get('/career/skill-gap-trend', { params: { limit } }),

  // Learning Roadmap
  generateRoadmap: (skillGapId: number) => api.post(`/career/roadmap/generate`, null, { params: { skill_gap_id: skillGapId } }),
  generateEnhancedRoadmap: (skillGapId: number, resumeAnalysisId?: number, jobDescriptionId?: number) =>
    api.post('/career/roadmap/generate-enhanced', null, { params: { skill_gap_id: skillGapId, resume_analysis_id: resumeAnalysisId, job_description_id: jobDescriptionId } }),
  getRoadmap: (roadmapId: number) => api.get(`/career/roadmap/${roadmapId}`),
  getRoadmaps: () => api.get('/career/roadmaps'),
  getRoadmapAnalytics: (roadmapId: number) => api.get(`/career/roadmap/${roadmapId}/analytics`),
  updateRoadmapProgress: (roadmapId: number, completedTopics: string[]) =>
    api.patch(`/career/roadmap/${roadmapId}/progress`, null, { params: { completed_topics: completedTopics } }),

  // Learning Progress
  getLearningProgress: (roadmapId?: number, page = 1, perPage = 50) =>
    api.get('/career/learning-progress', { params: { roadmap_id: roadmapId, page, per_page: perPage } }),
  startLearningTopic: (roadmapId: number, topicName: string, skillName?: string, estimatedHours?: number) =>
    api.post('/career/learning-progress/start', null, {
      params: { roadmap_id: roadmapId, topic_name: topicName, skill_name: skillName, estimated_hours: estimatedHours },
    }),
  completeLearningTopic: (roadmapId: number, topicName: string, actualHours?: number) =>
    api.post('/career/learning-progress/complete', null, {
      params: { roadmap_id: roadmapId, topic_name: topicName, actual_hours: actualHours },
    }),
  masterLearningTopic: (roadmapId: number, topicName: string) =>
    api.post('/career/learning-progress/master', null, { params: { roadmap_id: roadmapId, topic_name: topicName } }),
  updateLearningProgress: (roadmapId: number, topicName: string, percentage: number, actualHours?: number) =>
    api.put('/career/learning-progress/update', null, {
      params: { roadmap_id: roadmapId, topic_name: topicName, percentage, actual_hours: actualHours },
    }),

  // Resume Optimization
  optimizeResume: (resumeAnalysisId: number, jobDescriptionId?: number) =>
    api.post('/career/resume/optimize', null, { params: { resume_analysis_id: resumeAnalysisId, job_description_id: jobDescriptionId } }),
  getOptimizedResume: (optId: number) => api.get(`/career/optimized-resume/${optId}`),

  // Career Readiness
  getReadiness: () => api.get('/career/readiness'),
  getReadinessHistory: (limit = 30) => api.get('/career/readiness/history', { params: { limit } }),
  getReadinessBreakdown: () => api.get('/career/readiness/breakdown'),
  getRoleReadiness: () => api.get('/career/readiness/roles'),
  getCompanyReadiness: () => api.get('/career/readiness/companies'),
  recalculateReadiness: () => api.post('/career/readiness/recalculate'),

  // Dashboard
  getDashboard: () => api.get('/career/dashboard'),

  // ATS Analysis
  analyzeATS: (resumeId: number, jobDescriptionId?: number) =>
    api.post('/ats/analyze', { resume_id: resumeId, job_description_id: jobDescriptionId }),
  getATSReport: (reportId: number) => api.get(`/ats/report/${reportId}`),
  getATSHistory: () => api.get('/ats/history'),
  downloadATSReport: (reportId: number) =>
    api.get(`/ats/report/${reportId}/download`, { responseType: 'blob' }),

  // ATS Optimization
  optimizeATS: (resumeId: number, jobDescriptionId?: number) =>
    api.post('/ats/optimize', { resume_id: resumeId, job_description_id: jobDescriptionId }),
  getATSOptimizedResume: (optimizeId: number) => api.get(`/ats/optimize/${optimizeId}`),
  getOptimizeHistory: () => api.get('/ats/optimize-history'),
  downloadOptimizedResume: (optimizeId: number) =>
    api.get(`/ats/optimize/${optimizeId}/download`, { responseType: 'blob' }),

  // ATS Format-Preserving Optimization (DOCX/PDF)
  optimizeATSDocx: (resumeId: number, jobDescriptionId?: number) =>
    api.post('/ats/optimize-docx', { resume_id: resumeId, job_description_id: jobDescriptionId }),
  optimizeATSPdf: (resumeId: number, jobDescriptionId?: number) =>
    api.post('/ats/optimize-pdf', { resume_id: resumeId, job_description_id: jobDescriptionId }, { responseType: 'blob' }),
  downloadOptimizedDocx: (optimizeId: number) =>
    api.get(`/ats/optimize/${optimizeId}/download-docx`, { responseType: 'blob' }),
  downloadOptimizedPdf: (optimizeId: number) =>
    api.get(`/ats/optimize/${optimizeId}/download-pdf`, { responseType: 'blob' }),

  // Suggestions
  getSuggestions: () => api.get('/career/suggestions'),

  // Report
  downloadReport: () => api.get('/career/report/pdf', { responseType: 'blob' }),

  // Delete operations
  deleteJobDescription: (jdId: number) => api.delete(`/career/job-description/${jdId}`),
  deleteResumeAnalysis: (analysisId: number) => api.delete(`/career/resume-analysis/${analysisId}`),
  deleteRoadmap: (roadmapId: number) => api.delete(`/career/roadmap/${roadmapId}`),
  deleteOptimizedResume: (optId: number) => api.delete(`/career/optimized-resume/${optId}`),
  getCurrentRoadmap: () => api.get('/career/roadmap/current'),
  getRoadmapHistory: () => api.get('/career/roadmap/history'),
};

export const adminApi = {
  // Legacy
  getStats: () => api.get('/admin/stats'),

  // Dashboard
  getDashboard: () => api.get('/admin/dashboard'),

  // Users
  getUsers: (params?: {
    page?: number;
    per_page?: number;
    search?: string;
    status?: string;
    role?: string;
  }) => api.get('/admin/users', { params }),
  getUserDetail: (userId: number) => api.get(`/admin/users/${userId}`),
  toggleUserActive: (userId: number) => api.patch(`/admin/users/${userId}/toggle-active`),
  deleteUser: (userId: number) => api.delete(`/admin/users/${userId}`),
  resetUserPassword: (userId: number) => api.post(`/admin/users/${userId}/reset-password`),

  // Recruiters
  getRecruiters: (params?: { search?: string }) => api.get('/admin/recruiters', { params }),
  approveRecruiter: (recruiterId: number) => api.patch(`/admin/recruiters/${recruiterId}/approve`),
  rejectRecruiter: (recruiterId: number) => api.patch(`/admin/recruiters/${recruiterId}/reject`),

  // Interviews
  getInterviews: (params?: {
    page?: number;
    per_page?: number;
    search?: string;
    status?: string;
    interview_type?: string;
    role?: string;
    score_min?: number;
    score_max?: number;
    date_from?: string;
    date_to?: string;
  }) => api.get('/admin/interviews', { params }),
  getInterviewDetail: (sessionId: number) => api.get(`/admin/interviews/${sessionId}`),

  // Voice Sessions
  getVoiceSessions: (params?: { status?: string; limit?: number }) =>
    api.get('/admin/voice-sessions', { params }),

  // AI Usage
  getAIUsageDetail: (params?: { days?: number }) =>
    api.get('/admin/ai-usage/detail', { params }),
  getAPIUsage: () => api.get('/admin/api-usage'),

  // Reports
  getReports: (params?: { search?: string; page?: number; per_page?: number }) =>
    api.get('/admin/reports', { params }),
  deleteReport: (sessionId: number) => api.delete(`/admin/reports/${sessionId}`),

  // Analytics
  getPlatformAnalytics: () => api.get('/admin/analytics'),

  // System Health
  getSystemHealth: () => api.get('/admin/system-health'),

  // Audit Logs
  getAuditLogs: (params?: { page?: number; per_page?: number; action?: string }) =>
    api.get('/admin/audit-logs', { params }),

  // Notifications
  getNotifications: (unreadOnly?: boolean) =>
    api.get('/admin/notifications', { params: { unread_only: unreadOnly } }),
  markNotificationRead: (notifId: number) =>
    api.patch(`/admin/notifications/${notifId}/read`),
  markAllNotificationsRead: () => api.patch('/admin/notifications/read-all'),

  // Settings
  getSettings: () => api.get('/admin/settings'),
  updateSettings: (data: any) => api.put('/admin/settings', data),

  // Abuse/Cheating Logs
  getAbuseLogs: (limit?: number) => api.get('/admin/abuse-logs', { params: { limit } }),

  // Coding Module
  getCodingSubmissions: (params?: { page?: number; per_page?: number; language?: string; status?: string; search?: string }) =>
    api.get('/admin/coding/submissions', { params }),
  getCodingSubmissionDetail: (id: number) => api.get(`/admin/coding/submissions/${id}`),
  getCodingAnalytics: () => api.get('/admin/coding/analytics'),
};

export const mlApi = {
  classify: (resumeId: number) => api.post('/ml/classify', { resume_id: resumeId }),
  extractSkills: (resumeId: number) => api.post('/ml/extract-skills', { resume_id: resumeId }),
  predictATS: (resumeId: number, jobDescriptionId?: number) =>
    api.post('/ml/predict-ats', { resume_id: resumeId, job_description_id: jobDescriptionId }),
  skillGap: (resumeId: number, jobDescriptionId: number) =>
    api.post('/ml/skill-gap', { resume_id: resumeId, job_description_id: jobDescriptionId }),
  recommendJobs: (resumeId: number) => api.post('/ml/recommend-jobs', { resume_id: resumeId }),
  rankResumes: (resumeIds: number[], jobDescriptionId: number) =>
    api.post('/ml/rank-resumes', { resume_ids: resumeIds, job_description_id: jobDescriptionId }),
  search: (query: string, topK?: number) => api.post('/ml/search', { query, top_k: topK }),
  careerPath: (resumeId: number, currentRole?: string) =>
    api.post('/ml/career-path', { resume_id: resumeId, current_role: currentRole }),
  quality: (resumeId: number) => api.post('/ml/quality', { resume_id: resumeId }),
  recommendSkills: (resumeId: number, targetRole?: string) =>
    api.post('/ml/recommend-skills', { resume_id: resumeId, target_role: targetRole }),
  analyzeFull: (resumeId: number, jobDescriptionId?: number) =>
    api.post('/ml/analyze-full', { resume_id: resumeId, job_description_id: jobDescriptionId }),
  getHistory: () => api.get('/ml/history'),
  getAnalytics: () => api.get('/ml/analytics'),
};

export const reportsApi = {
  list: (params?: { page?: number; per_page?: number; report_type?: string; include_all?: boolean }) =>
    api.get('/reports', { params }),
  get: (reportId: number) => api.get(`/reports/${reportId}`),
  generate: (reportType: string = 'portfolio', title?: string) =>
    api.post('/reports/generate', null, { params: { report_type: reportType, title } }),
  download: (reportId: number, format: 'pdf' | 'docx' = 'pdf') => {
    if (format === 'docx') {
      return api.post(`/reports/${reportId}/download-docx`, null, { responseType: 'blob' });
    }
    return api.get(`/reports/${reportId}/download`, { responseType: 'blob' });
  },
  delete: (reportId: number) => api.delete(`/reports/${reportId}`),
  regenerate: (reportId: number) => api.post(`/reports/${reportId}/regenerate`),
  markOutdated: (reason: string) =>
    api.post('/reports/mark-outdated', null, { params: { reason } }),
  getHistory: () => api.get('/reports', { params: { include_all: true } }),
};

export default api;
