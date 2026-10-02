import type { Metadata } from "next";
import React from "react";

import { Navbar } from "../components/Navbar";
import { AuthProvider } from "../context/AuthContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "Interview Ready — Technical Mock Interviews",
  description: "Practice technical mock interviews with vetted engineering leaders.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased flex flex-col font-sans">
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
