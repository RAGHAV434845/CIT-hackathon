import axios from 'axios';
import { auth } from '../firebase';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for analysis
});

// Attach Firebase token to every request
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired — redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ---- Auth ----
export const registerUser = (data) => api.post('/auth/register', data);
export const getProfile = () => api.get('/auth/profile');
export const updateProfile = (data) => api.put('/auth/profile', data);

// ---- Repos ----
export const createRepoFromGithub = (githubUrl, name) =>
  api.post('/repos', { source: 'github', github_url: githubUrl, name });

export const uploadRepoZip = (file, name) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);
  formData.append('source', 'upload');
  return api.post('/repos', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const listRepos = () => api.get('/repos');
export const getRepo = (id) => api.get(`/repos/${id}`);
export const deleteRepo = (id) => api.delete(`/repos/${id}`);
export const searchRepos = (q) => api.get(`/repos/search?q=${encodeURIComponent(q)}`);

// ---- Analysis ----
export const startAnalysis = (repoId) => api.post(`/analysis/${repoId}`);
export const getAnalysis = (repoId) => api.get(`/analysis/${repoId}`);
export const getAnalysisStatus = (repoId) => api.get(`/analysis/${repoId}/status`);

// ---- Security ----
export const getSecurityScan = (repoId) => api.get(`/security/${repoId}`);
export const resolveSecurityIssues = (repoId, action, indices) =>
  api.post(`/security/${repoId}/resolve`, { action, indices });

// ---- Docs ----
export const generateReadme = (repoId) => api.post(`/docs/${repoId}/readme`);
export const generateApiDoc = (repoId) => api.post(`/docs/${repoId}/api-doc`);
export const generateReport = (repoId) => api.post(`/docs/${repoId}/report`);
export const generateModuleBreakdown = (repoId) => api.post(`/docs/${repoId}/module-breakdown`);
export const listDocs = (repoId) => api.get(`/docs/${repoId}`);
export const editDoc = (docId, content) => api.put(`/docs/${docId}/edit`, { content });
export const exportDoc = (docId, format) => api.get(`/docs/${docId}/export/${format}`);

// ---- Diagrams ----
export const generateDiagrams = (repoId, type = 'all') =>
  api.post(`/diagrams/${repoId}`, { type });
export const listDiagrams = (repoId) => api.get(`/diagrams/${repoId}`);
export const updateDiagram = (diagramId, data) => api.put(`/diagrams/${diagramId}/edit`, data);

// ---- Chat ----
export const sendChatMessage = (repoId, message) =>
  api.post(`/chat/${repoId}`, { message });

// ---- Analytics ----
export const getDashboardStats = () => api.get('/analytics/dashboard');
export const getUserStats = (uid) => api.get(`/analytics/user/${uid}`);

// ---- Faculty ----
export const createProject = (data) => api.post('/faculty/projects', data);
export const listProjects = () => api.get('/faculty/projects');
export const scoreProject = (projectId, scores) =>
  api.put(`/faculty/projects/${projectId}/score`, scores);
export const addStudentToProject = (projectId, studentUid) =>
  api.post(`/faculty/projects/${projectId}/add-student`, { student_uid: studentUid });
export const addRepoToProject = (projectId, repoId) =>
  api.post(`/faculty/projects/${projectId}/add-repo`, { repo_id: repoId });
export const listStudents = (department) =>
  api.get(`/faculty/students${department ? `?department=${department}` : ''}`);

// ---- HOD ----
export const listFaculty = (department) =>
  api.get(`/hod/faculty${department ? `?department=${department}` : ''}`);
export const listAllStudents = (department) =>
  api.get(`/hod/students${department ? `?department=${department}` : ''}`);
export const assignMentor = (facultyUid, studentUid) =>
  api.post('/hod/assign-mentor', { faculty_uid: facultyUid, student_uid: studentUid });
export const scoreFaculty = (facultyUid, score, feedback) =>
  api.put(`/hod/faculty/${facultyUid}/score`, { score, feedback });
export const getDeptAnalytics = (department) =>
  api.get(`/hod/analytics${department ? `?department=${department}` : ''}`);
export const listAllRepos = (department) =>
  api.get(`/hod/repositories${department ? `?department=${department}` : ''}`);

export default api;
