import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Moon, Sun, FileText, BarChart3 } from "lucide-react";
import { useTheme } from "next-themes";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const location = useLocation();

  // Determine active nav based on current path
  const activeNav = location.pathname === "/dashboard" ? "dashboard" : "cv";

  // Only render theme toggle after hydration
  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-sidebar flex flex-col">
        {/* Logo/Brand */}
        <div className="flex items-center gap-3 p-6 border-b border-sidebar-border">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-primary-foreground" />
          </div>
          <h1 className="text-lg font-bold text-sidebar-foreground">CareerAI</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <Link
            to="/"
            className={`w-full flex items-center gap-3 px-5 py-3 rounded-lg transition-all text-left whitespace-nowrap ${activeNav === "cv"
              ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm font-semibold"
              : "text-sidebar-foreground hover:bg-sidebar-accent hover:pl-6"
              }`}
          >
            <FileText className="w-5 h-5 shrink-0" />
            <span>CV & Resume Matching</span>
          </Link>

          <Link
            to="/dashboard"
            className={`w-full flex items-center gap-3 px-5 py-3 rounded-lg transition-all text-left whitespace-nowrap ${activeNav === "dashboard"
              ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm font-semibold"
              : "text-sidebar-foreground hover:bg-sidebar-accent hover:pl-6"
              }`}
          >
            <BarChart3 className="w-5 h-5 shrink-0" />
            <span>IT Jobs Trending</span>
          </Link>
        </nav>

        {/* Theme Toggle */}
        <div className="p-4 border-t border-sidebar-border">
          {mounted && (
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
            >
              {theme === "dark" ? (
                <>
                  <Sun className="w-5 h-5" />
                  <span className="font-medium">Light Mode</span>
                </>
              ) : (
                <>
                  <Moon className="w-5 h-5" />
                  <span className="font-medium">Dark Mode</span>
                </>
              )}
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-background">
        {children}
      </main>
    </div>
  );
}
