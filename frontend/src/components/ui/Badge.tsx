import React from 'react';
import { cn } from '@/lib/utils';

type BadgeVariant = 'default' | 'success' | 'error' | 'warning' | 'accent' | 'active';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-[#1e1e1e] text-[#888888] border border-[#2a2a2a]',
  success: 'bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/30',
  error: 'bg-[#ff4444]/10 text-[#ff4444] border border-[#ff4444]/30',
  warning: 'bg-[#ffaa00]/10 text-[#ffaa00] border border-[#ffaa00]/30',
  accent: 'bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/30',
  active: 'bg-[#00ff88] text-[#0a0a0a] font-semibold',
};

export function Badge({
  children,
  variant = 'default',
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'px-2 py-0.5 text-xs uppercase tracking-wider inline-flex items-center',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
