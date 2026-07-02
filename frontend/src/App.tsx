import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { PreferencesProvider } from './contexts/PreferencesContext';
import { ToastProvider } from './components/ui/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

const LoginPage = lazy(() => import('./pages/LoginPage'));
const SignupPage = lazy(() => import('./pages/SignupPage'));
const LandingPage = lazy(() => import('./pages/LandingPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const InterviewPage = lazy(() => import('./pages/InterviewPage'));
const InterviewSetupPage = lazy(() => import('./pages/InterviewSetupPage'));
const CodingPage = lazy(() => import('./pages/CodingPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const ReportPage = lazy(() => import('./pages/ReportPage'));
const ResumePage = lazy(() => import('./pages/ResumePage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

const RecruiterLayout = lazy(() => import('./pages/recruiter/RecruiterLayout'));
const RecruiterDashboardPage = lazy(() => import('./pages/recruiter/RecruiterDashboardPage'));
const RecruiterJobsPage = lazy(() => import('./pages/recruiter/RecruiterJobsPage'));
const RecruiterJobCreatePage = lazy(() => import('./pages/recruiter/RecruiterJobCreatePage'));
const RecruiterJobDetailPage = lazy(() => import('./pages/recruiter/RecruiterJobDetailPage'));
const RecruiterApplicationsPage = lazy(() => import('./pages/recruiter/RecruiterApplicationsPage'));
const RecruiterCandidateProfilePage = lazy(() => import('./pages/recruiter/RecruiterCandidateProfilePage'));
const RecruiterInterviewsPage = lazy(() => import('./pages/recruiter/RecruiterInterviewsPage'));
const RecruiterCodingPage = lazy(() => import('./pages/recruiter/RecruiterCodingPage'));
const RecruiterComparePage = lazy(() => import('./pages/recruiter/RecruiterComparePage'));
const RecruiterAnalyticsPage = lazy(() => import('./pages/recruiter/RecruiterAnalyticsPage'));
const RecruiterReportsPage = lazy(() => import('./pages/recruiter/RecruiterReportsPage'));
const RecruiterNotificationsPage = lazy(() => import('./pages/recruiter/RecruiterNotificationsPage'));
const RecruiterSettingsPage = lazy(() => import('./pages/recruiter/RecruiterSettingsPage'));

const CareerDashboardPage = lazy(() => import('./pages/career/CareerDashboardPage'));
const JobDescriptionPage = lazy(() => import('./pages/career/JobDescriptionPage'));
const SkillGapPage = lazy(() => import('./pages/career/SkillGapPage'));
const ResumeOptimizerPage = lazy(() => import('./pages/career/ResumeOptimizerPage'));
const ATSReportPage = lazy(() => import('./pages/career/ATSReportPage'));
const LearningRoadmapPage = lazy(() => import('./pages/career/LearningRoadmapPage'));
const CareerReadinessPage = lazy(() => import('./pages/career/CareerReadinessPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));

const MLInsightsPage = lazy(() => import('./pages/ml/MLInsightsPage'));

const CandidateJobsPage = lazy(() => import('./pages/candidate/CandidateJobsPage'));
const CandidateJobDetailPage = lazy(() => import('./pages/candidate/CandidateJobDetailPage'));
const MyApplicationsPage = lazy(() => import('./pages/candidate/MyApplicationsPage'));

const AdminPage = lazy(() => import('./pages/AdminPage'));
const AdminLayout = lazy(() => import('./pages/admin/AdminLayout'));
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage'));
const AdminUsersPage = lazy(() => import('./pages/admin/AdminUsersPage'));
const AdminRecruitersPage = lazy(() => import('./pages/admin/AdminRecruitersPage'));
const AdminInterviewsPage = lazy(() => import('./pages/admin/AdminInterviewsPage'));
const AdminVoicePage = lazy(() => import('./pages/admin/AdminVoicePage'));
const AdminAIUsagePage = lazy(() => import('./pages/admin/AdminAIUsagePage'));
const AdminReportsPage = lazy(() => import('./pages/admin/AdminReportsPage'));
const AdminAnalyticsPage = lazy(() => import('./pages/admin/AdminAnalyticsPage'));
const AdminSystemHealthPage = lazy(() => import('./pages/admin/AdminSystemHealthPage'));
const AdminAuditLogsPage = lazy(() => import('./pages/admin/AdminAuditLogsPage'));
const AdminSettingsPage = lazy(() => import('./pages/admin/AdminSettingsPage'));
const AdminNotificationsPage = lazy(() => import('./pages/admin/AdminNotificationsPage'));
const AdminCodingPage = lazy(() => import('./pages/admin/AdminCodingPage'));

function PageLoader() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: '100vh', color: 'var(--muted, #888)', fontSize: '0.875rem'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: 24, height: 24, border: '2.5px solid var(--border, #e5e7eb)',
          borderTopColor: 'var(--accent-strong, #2563eb)', borderRadius: '50%',
          animation: 'spin 0.6s linear infinite', margin: '0 auto 0.75rem'
        }} />
        Loading...
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <PreferencesProvider>
          <ToastProvider>
            <Router>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  {/* Public routes */}
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/signup" element={<SignupPage />} />

                  {/* Candidate-only routes (with shared AppLayout) */}
                  <Route element={<ProtectedRoute allowedRoles={['candidate', 'admin']}><AppLayout /></ProtectedRoute>}>
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/resume" element={<ResumePage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/report" element={<ReportPage />} />
                    <Route path="/report/:sessionId" element={<ReportPage />} />
                    <Route path="/interview-setup" element={<InterviewSetupPage />} />

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

                    {/* Job Board & Applications */}
                    <Route path="/jobs" element={<CandidateJobsPage />} />
                    <Route path="/jobs/:jobId" element={<CandidateJobDetailPage />} />
                    <Route path="/my-applications" element={<MyApplicationsPage />} />
                  </Route>

                  {/* Shared routes (all roles) */}
                  <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
                    <Route path="/settings" element={<SettingsPage />} />
                  </Route>

                  {/* Recruiter Portal (own layout) */}
                  <Route path="/recruiter" element={<ProtectedRoute allowedRoles={['recruiter', 'admin']}><RecruiterLayout /></ProtectedRoute>}>
                    <Route path="dashboard" element={<RecruiterDashboardPage />} />
                    <Route path="jobs" element={<RecruiterJobsPage />} />
                    <Route path="jobs/create" element={<RecruiterJobCreatePage />} />
                    <Route path="jobs/:jobId" element={<RecruiterJobDetailPage />} />
                    <Route path="jobs/:jobId/edit" element={<RecruiterJobCreatePage />} />
                    <Route path="applications" element={<RecruiterApplicationsPage />} />
                    <Route path="candidates/:userId" element={<RecruiterCandidateProfilePage />} />
                    <Route path="interviews" element={<RecruiterInterviewsPage />} />
                    <Route path="coding" element={<RecruiterCodingPage />} />
                    <Route path="compare" element={<RecruiterComparePage />} />
                    <Route path="analytics" element={<RecruiterAnalyticsPage />} />
                    <Route path="reports" element={<RecruiterReportsPage />} />
                    <Route path="notifications" element={<RecruiterNotificationsPage />} />
                    <Route path="settings" element={<RecruiterSettingsPage />} />
                  </Route>
                  <Route path="/recruiter" element={<ProtectedRoute allowedRoles={['recruiter', 'admin']}><RecruiterLayout /></ProtectedRoute>}>
                    <Route index element={<RecruiterDashboardPage />} />
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
              </Suspense>
            </Router>
          </ToastProvider>
        </PreferencesProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
