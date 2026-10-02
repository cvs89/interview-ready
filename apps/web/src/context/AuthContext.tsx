"use client";

import type { User as ApiUser } from "@interview-ready/api-types";
import {
  createUserWithEmailAndPassword,
  onIdTokenChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  type User as FirebaseUser,
} from "firebase/auth";
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import { ApiClient } from "../lib/api-client";
import { auth, googleProvider } from "../lib/firebase";

export interface AuthContextValue {
  user: FirebaseUser | null;
  apiUser: ApiUser | null;
  loading: boolean;
  getIdToken: () => Promise<string | null>;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, pass: string) => Promise<void>;
  signUpWithEmail: (email: string, pass: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshApiUser: () => Promise<void>;
  api: ApiClient;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [apiUser, setApiUser] = useState<ApiUser | null>(null);
  const [loading, setLoading] = useState(true);

  const getIdToken = async (): Promise<string | null> => {
    if (!auth.currentUser) return null;
    return auth.currentUser.getIdToken();
  };

  const api = useMemo(() => new ApiClient(undefined, getIdToken), []);

  const fetchApiUser = React.useCallback(async () => {
    if (!auth.currentUser) {
      setApiUser(null);
      return;
    }
    try {
      const userData = await api.get<ApiUser>("/auth/me");
      setApiUser(userData);
    } catch {
      setApiUser(null);
    }
  }, [api]);

  useEffect(() => {
    const unsubscribe = onIdTokenChanged(auth, async (currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        await fetchApiUser();
      } else {
        setApiUser(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, [fetchApiUser]);

  const signInWithGoogle = async () => {
    setLoading(true);
    try {
      await signInWithPopup(auth, googleProvider);
    } finally {
      setLoading(false);
    }
  };

  const signInWithEmail = async (email: string, pass: string) => {
    setLoading(true);
    try {
      await signInWithEmailAndPassword(auth, email, pass);
    } finally {
      setLoading(false);
    }
  };

  const signUpWithEmail = async (email: string, pass: string, fullName: string) => {
    setLoading(true);
    try {
      const cred = await createUserWithEmailAndPassword(auth, email, pass);
      if (cred.user && fullName) {
        await updateProfile(cred.user, { displayName: fullName });
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await signOut(auth);
      setUser(null);
      setApiUser(null);
    } finally {
      setLoading(false);
    }
  };

  const value: AuthContextValue = {
    user,
    apiUser,
    loading,
    getIdToken,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    logout,
    refreshApiUser: fetchApiUser,
    api,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
