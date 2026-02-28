import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
} from 'firebase/auth';
import { auth } from '../firebase';
import { registerUser, getProfile } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (firebaseUser) {
        try {
          const res = await getProfile();
          setProfile(res.data);
        } catch {
          setProfile(null);
        }
      } else {
        setProfile(null);
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const login = async (email, password) => {
    const cred = await signInWithEmailAndPassword(auth, email, password);
    try {
      const res = await getProfile();
      if (res.data && !res.data._stub) {
        setProfile(res.data);
      } else {
        // Profile is a stub — create real Firestore doc
        await registerUser({
          uid: cred.user.uid,
          username: email.split('@')[0],
          email,
          role: 'student',
          github_link: '',
          department: '',
        });
        const res2 = await getProfile();
        setProfile(res2.data);
      }
    } catch (err) {
      // Profile doesn't exist — create it
      await registerUser({
        uid: cred.user.uid,
        username: email.split('@')[0],
        email,
        role: 'student',
        github_link: '',
        department: '',
      });
      const res2 = await getProfile();
      setProfile(res2.data);
    }
    return cred;
  };

  const signup = async (email, password, username, role, githubLink, department) => {
    let cred;
    try {
      cred = await createUserWithEmailAndPassword(auth, email, password);
    } catch (err) {
      if (err.code === 'auth/email-already-in-use') {
        // User exists in Firebase Auth but Firestore doc may be missing — sign in instead
        cred = await signInWithEmailAndPassword(auth, email, password);
      } else {
        throw err;
      }
    }
    // Create or update Firestore profile
    await registerUser({
      uid: cred.user.uid,
      username,
      email,
      role,
      github_link: githubLink || '',
      department: department || '',
    });
    const res = await getProfile();
    setProfile(res.data);
    return cred;
  };

  const logout = async () => {
    await signOut(auth);
    setUser(null);
    setProfile(null);
  };

  const value = {
    user,
    profile,
    loading,
    login,
    signup,
    logout,
    isStudent: profile?.role === 'student',
    isFaculty: profile?.role === 'faculty',
    isHOD: profile?.role === 'hod',
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}
