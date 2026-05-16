import "./globals.css";
import type { ReactNode } from "react";
import { AppShell } from "../components/app-shell";

export const metadata = {
  title: "SpendAgent",
  description: "Autonomous vendor spend intelligence"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppShell>
          {children}
        </AppShell>
      </body>
    </html>
  );
}

