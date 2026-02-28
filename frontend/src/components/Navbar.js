import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, profile, logout } = useAuth();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link to={user ? '/dashboard' : '/'} className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">CL</span>
            </div>
            <span className="text-xl font-bold text-gray-900">CodeLens AI</span>
          </Link>

          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link to="/dashboard" className="text-gray-600 hover:text-primary-600 text-sm font-medium">
                  Dashboard
                </Link>
                {(profile?.role === 'faculty' || profile?.role === 'hod') && (
                  <Link to="/faculty" className="text-gray-600 hover:text-primary-600 text-sm font-medium">
                    Faculty
                  </Link>
                )}
                {profile?.role === 'hod' && (
                  <Link to="/hod" className="text-gray-600 hover:text-primary-600 text-sm font-medium">
                    HOD Panel
                  </Link>
                )}
                <span className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded-full">
                  {profile?.role}
                </span>
                <span className="text-sm text-gray-500">{profile?.username}</span>
                <button
                  onClick={logout}
                  className="text-sm text-red-600 hover:text-red-800 font-medium"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-600 hover:text-primary-600 text-sm font-medium">
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
