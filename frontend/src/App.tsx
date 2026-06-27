import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './components/ui/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import LandingPage from './pages/LandingPage';
import NotFoundPage from './pages/NotFoundPage';

import DashboardPage from './pages/DashboardPage';
import InterviewPage from './pages/InterviewPage';
import InterviewSetupPage from './pages/InterviewSetupPage';
import CodingPage from './pages/CodingPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ReportPage from './pages/ReportPage';
import ResumePage from './pages/ResumePage';
import SettingsPage from './pages/SettingsPage';
import RecruiterPage from './pages/RecruiterPage';

import CareerDashboardPage from './pages/career/CareerDashboardPage';
import JobDescriptionPage from './pages/career/JobDescriptionPage';
import SkillGapPage from './pages/career/SkillGapPage';
import ResumeOptimizerPage from './pages/career/ResumeOptimizerPage';
import ATSReportPage from './pages/career/ATSReportPage';
import LearningRoadmapPage from './pages/career/LearningRoadmapPage';
import CareerReadinessPage from './pages/career/CareerReadinessPage';
import ReportsPage from './pages/ReportsPage';

import MLInsightsPage from './pages/ml/MLInsightsPage';

import AdminPage from './pages/AdminPage';
import AdminLayout from './pages/admin/AdminLayout';
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminRecruitersPage from './pages/admin/AdminRecruitersPage';
import AdminInterviewsPage from './pages/admin/AdminInterviewsPage';
import AdminVoicePage from './pages/admin/AdminVoicePage';
import AdminAIUsagePage from './pages/admin/AdminAIUsagePage';
import AdminReportsPage from './pages/admin/AdminReportsPage';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import AdminSystemHealthPage from './pages/admin/AdminSystemHealthPage';
import AdminAuditLogsPage from './pages/admin/AdminAuditLogsPage';
import AdminSettingsPage from './pages/admin/AdminSettingsPage';
import AdminNotificationsPage from './pages/admin/AdminNotificationsPage';
import AdminCodingPage from './pages/admin/AdminCodingPage';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/signup" element={<SignupPage />} />

              {/* Candidate routes (with shared AppLayout) */}
              <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/resume" element={<ResumePage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/report" element={<ReportPage />} />
                <Route path="/report/:sessionId" element={<ReportPage />} />
                <Route path="/interview-setup" element={<InterviewSetupPage />} />
                <Route path="/settings" element={<SettingsPage />} />

                {/* Career routes */}
                <Route path="/career/dashboard" element={<CareerDashboardPage />} />
                <Route path="/career/jd-upload" element={<JobDescriptionPage />} />
                <Route path="/career/skill-gap" element={<SkillGapPage />} />
                <Route path="/career/resume-optimizer" element={<ResumeOptimizerPage />} />
                <Route path="/career/ats-report" element={<ATSReportPage />} />
                <Route path="/career/learning-roadmap" element={<LearningRoadmapPage />} />
                <Route path="/career/readiness" element={<CareerReadinessPage />} />

                {/* Reports */}
                <Route path="/reports" element={<ReportsPage />} />

                {/* ML Insights */}
                <Route path="/ml-insights" element={<MLInsightsPage />} />

                {/* Recruiter */}
                <Route path="/recruiter" element={<RecruiterPage />} />
              </Route>

              {/* Full-screen routes (no layout) */}
              <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                <Route path="/interview/:sessionId" element={<InterviewPage />} />
                <Route path="/coding" element={<CodingPage />} />
                <Route path="/coding/:sessionId" element={<CodingPage />} />
              </Route>

              {/* Admin routes (own layout) */}
              <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><AdminPage /></ProtectedRoute>} />
              <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><AdminLayout /></ProtectedRoute>}>
                <Route path="dashboard" element={<AdminDashboardPage />} />
                <Route path="users" element={<AdminUsersPage />} />
                <Route path="recruiters" element={<AdminRecruitersPage />} />
                <Route path="interviews" element={<AdminInterviewsPage />} />
                <Route path="voice" element={<AdminVoicePage />} />
                <Route path="ai-usage" element={<AdminAIUsagePage />} />
                <Route path="reports" element={<AdminReportsPage />} />
                <Route path="analytics" element={<AdminAnalyticsPage />} />
                <Route path="system-health" element={<AdminSystemHealthPage />} />
                <Route path="audit-logs" element={<AdminAuditLogsPage />} />
                <Route path="settings" element={<AdminSettingsPage />} />
                <Route path="notifications" element={<AdminNotificationsPage />} />
                <Route path="coding" element={<AdminCodingPage />} />
              </Route>

              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Router>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
