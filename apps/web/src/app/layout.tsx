import type { Metadata } from "next";
import React from "react";

import { Navbar } from "../components/Navbar";
import { AuthProvider } from "../context/AuthContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "Interview Ready — Real Interview Practice with Vetted Leaders",
  description: "Real interview practice. Specific feedback. A clearer next step. Practice 1-on-1 mock interviews with approved engineering leaders.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#FFF8F0] text-[#342523] antialiased flex flex-col font-sans selection:bg-[#F8DDC9] selection:text-[#342523]">
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
