import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-[#141414] border border-[#2a2a2a] p-4',
        onClick && 'cursor-pointer hover:border-[#00ff88] transition-colors',
        className
      )}
    >
      {children}
    </div>
  );
}
