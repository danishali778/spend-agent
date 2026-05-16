"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { label: "Work Queue", href: "/" },
    { label: "Cases", disabled: true },
    { label: "Documents", disabled: true },
    { label: "Analytics", disabled: true },
    { label: "Settings", disabled: true },
  ];

  return (
    <div className="app-shell">
      <nav className="app-sidebar">
        <div className="app-brand">
          <div className="app-logo">SpendAgent</div>
          <div className="app-subtitle">Procurement Workbench</div>
        </div>
        <div className="nav-links">
          {navItems.map((item) => {
            if (item.disabled) {
              return (
                <button
                  key={item.label}
                  disabled
                  aria-disabled="true"
                  className="nav-item nav-item-disabled"
                >
                  {item.label}
                </button>
              );
            }

            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href as string));
              
            return (
              <Link
                key={item.label}
                href={item.href!}
                className={`nav-item ${isActive ? "active" : ""}`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
      <main className="app-main">{children}</main>
    </div>
  );
}
