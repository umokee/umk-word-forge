import React from 'react';
import { NavLink } from 'react-router-dom';
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
  { label: 'DASHBOARD', path: '/', icon: LayoutDashboard },
  { label: 'TRAINING', path: '/train', icon: Dumbbell },
  { label: 'WORDS', path: '/words', icon: BookOpen },
  { label: 'STATISTICS', path: '/stats', icon: BarChart3 },
  { label: 'SETTINGS', path: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-56 flex-col border-r border-[#2a2a2a] bg-[#0a0a0a]">
      {/* Logo */}
      <div className="flex items-center gap-2 border-b border-[#2a2a2a] px-5 py-5">
        <span className="text-lg font-bold text-[#00ff88] uppercase tracking-wider">
          WordForge
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 text-xs font-medium transition-colors tracking-wider',
                isActive
                  ? 'bg-[#00ff88]/5 text-[#00ff88] border-l-3 border-[#00ff88]'
                  : 'text-[#888888] hover:bg-[#1e1e1e] hover:text-[#e0e0e0] border-l-3 border-transparent'
              )
            }
          >
            <item.icon size={16} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-[#2a2a2a] px-5 py-4">
        <p className="text-[10px] text-[#666666] uppercase tracking-wider">
          v2.0.0
        </p>
      </div>
    </aside>
  );
}
