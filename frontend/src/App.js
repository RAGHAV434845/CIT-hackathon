import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import Dashboard from './pages/Dashboard';
import RepoDetail from './pages/RepoDetail';
import AnalysisView from './pages/AnalysisView';
import SecurityView from './pages/SecurityView';
import DocsView from './pages/DocsView';
import DiagramView from './pages/DiagramView';
import ChatView from './pages/ChatView';
import FacultyPanel from './pages/FacultyPanel';
import HODPanel from './pages/HODPanel';

function PrivateRoute({ children, roles }) {
  const { user, profile } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(profile?.role)) return <Navigate to="/dashboard" />;
  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/repo/:repoId" element={<PrivateRoute><RepoDetail /></PrivateRoute>} />
          <Route path="/repo/:repoId/analysis" element={<PrivateRoute><AnalysisView /></PrivateRoute>} />
          <Route path="/repo/:repoId/security" element={<PrivateRoute><SecurityView /></PrivateRoute>} />
          <Route path="/repo/:repoId/docs" element={<PrivateRoute><DocsView /></PrivateRoute>} />
          <Route path="/repo/:repoId/diagrams" element={<PrivateRoute><DiagramView /></PrivateRoute>} />
          <Route path="/repo/:repoId/chat" element={<PrivateRoute><ChatView /></PrivateRoute>} />
          <Route path="/faculty" element={<PrivateRoute roles={['faculty', 'hod']}><FacultyPanel /></PrivateRoute>} />
          <Route path="/hod" element={<PrivateRoute roles={['hod']}><HODPanel /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
