import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Dumbbell,
  BookOpen,
  BarChart3,
  Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { label: '[ ] ГЛАВНАЯ', path: '/', icon: LayoutDashboard },
  { label: '[>] ТРЕНИРОВКА', path: '/train', icon: Dumbbell },
  { label: '[#] СЛОВА', path: '/words', icon: BookOpen },
  { label: '[*] СТАТИСТИКА', path: '/stats', icon: BarChart3 },
  { label: '[~] НАСТРОЙКИ', path: '/settings', icon: Settings },
];

export default function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Top Command Bar */}
      <nav className="sticky top-0 z-50 border-b-2 border-[#2a2a2a] bg-[#141414]">
        <div className="flex items-center">
          {/* Logo */}
          <div className="shrink-0 border-r border-[#2a2a2a] px-6 py-4">
            <span className="text-base font-bold uppercase tracking-widest text-[#00ff88]">
              WORD_FORGE
            </span>
          </div>

          {/* Navigation Tabs */}
          <div className="flex flex-1">
            {navItems.map((item) => {
              const isActive = item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'flex items-center gap-2 border-r border-[#2a2a2a] px-5 py-4 text-xs font-semibold uppercase tracking-wide transition-all',
                    isActive
                      ? 'bg-[#0a0a0a] text-[#00ff88] border-b-2 border-b-[#00ff88]'
                      : 'text-[#888888] hover:bg-[#1e1e1e] hover:text-[#e0e0e0]'
                  )}
                >
                  {item.label}
                </NavLink>
              );
            })}
          </div>

          {/* Version */}
          <div className="shrink-0 px-6 py-4">
            <span className="text-xs text-[#666666]">v2.0</span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="mx-auto max-w-6xl px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}
