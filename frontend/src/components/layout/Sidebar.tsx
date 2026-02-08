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
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Training', path: '/train', icon: Dumbbell },
  { label: 'Words', path: '/words', icon: BookOpen },
  { label: 'Statistics', path: '/stats', icon: BarChart3 },
  { label: 'Settings', path: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-56 flex-col border-r border-[#2A2A30] bg-[#0A0A0B]">
      {/* Logo */}
      <div className="flex items-center gap-2 border-b border-[#2A2A30] px-5 py-5">
        <span className="font-mono text-lg font-bold text-[#E8E8EC]">
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
                'flex items-center gap-3 rounded-sm px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-indigo-600/10 text-indigo-400 border-l-2 border-indigo-500'
                  : 'text-[#8B8B96] hover:bg-[#1C1C20] hover:text-[#E8E8EC] border-l-2 border-transparent'
              )
            }
          >
            <item.icon size={18} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
