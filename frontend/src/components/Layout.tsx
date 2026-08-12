import { Outlet, Link, NavLink } from "react-router-dom";
import clsx from "clsx";
import ThemeToggle from "./ThemeToggle";

const navItems = [
  { to: "/", label: "Analyze", end: true },
  { to: "/dashboard", label: "History", end: false },
];

function navClass({ isActive }: { isActive: boolean }) {
  return clsx(
    "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
    isActive
      ? "bg-brand-100 text-brand-700"
      : "text-surface-700 hover:bg-surface-100 hover:text-surface-900",
  );
}

export default function Layout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-10 border-b border-surface-200/70 bg-surface-0/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-2 px-4 sm:px-6">
          <Link to="/" className="flex shrink-0 items-center gap-2">
            <span
              aria-hidden
              className="grid h-7 w-7 place-items-center rounded-md bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm shadow-brand-700/30"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <path d="M14 2v6h6" />
                <path d="M9 13h6M9 17h4" />
              </svg>
            </span>
            <span className="font-semibold tracking-tight text-surface-900">
              Resume<span className="text-brand-600">AI</span>
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={navClass}
              >
                {item.label}
              </NavLink>
            ))}
            <span className="mx-1 hidden h-5 w-px bg-surface-200 sm:block" />
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 sm:py-12">
        <Outlet />
      </main>

      <footer className="border-t border-surface-200/70 py-6 text-center text-xs text-surface-700">
        Built with React, Flask, and a small amount of NLP.
      </footer>
    </div>
  );
}
