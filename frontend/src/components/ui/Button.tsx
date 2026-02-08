import React from 'react';
import { cn } from '@/lib/utils';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-[#00ff88] hover:bg-[#00aa55] text-[#0a0a0a] font-semibold uppercase tracking-wider',
  secondary:
    'bg-[#1e1e1e] border border-[#2a2a2a] hover:border-[#00ff88] text-[#e0e0e0]',
  ghost: 'bg-transparent hover:bg-[#1e1e1e] text-[#888888] hover:text-[#e0e0e0]',
  danger: 'bg-transparent border border-[#ff4444] text-[#ff4444] hover:bg-[#ff4444] hover:text-[#0a0a0a]',
  success: 'bg-transparent border border-[#00ff88] text-[#00ff88] hover:bg-[#00ff88] hover:text-[#0a0a0a]',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-2.5 text-sm',
};

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className,
  disabled = false,
  onClick,
  type = 'button',
}: ButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center font-medium transition-colors focus:outline-none',
        variantStyles[variant],
        sizeStyles[size],
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className
      )}
    >
      {children}
    </button>
  );
}
