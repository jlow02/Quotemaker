import { Badge as ShadcnBadge } from "@/components/ui/badge";
import React from "react";
import { cn } from "@/lib/utils"; // Assuming shadcn's utility for class merging

/**
 * @purpose Defines the custom variants for the Badge component.
 * @owner Gemini
 */
type CustomBadgeVariant = 'default' | 'success' | 'warning' | 'error';

/**
 * @purpose Props for the Badge component.
 * @owner Gemini
 */
interface BadgeProps extends Omit<React.ComponentPropsWithoutRef<typeof ShadcnBadge>, 'variant'> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'error';
  children?: React.ReactNode;
}

/**
 * @purpose A wrapper around shadcn Badge with extended variants for semantic states.
 * @param {BadgeProps} props - The props for the Badge component.
 * @returns {JSX.Element} The rendered Badge component.
 * @owner Gemini
 */
const Badge: React.FC<BadgeProps> = ({ variant = 'default', className, ...props }) => {
  const variantClasses: Record<CustomBadgeVariant, string> = {
    default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
    success: "border-transparent bg-green-500 text-green-50 hover:bg-green-500/80",
    warning: "border-transparent bg-yellow-500 text-yellow-50 hover:bg-yellow-500/80",
    error: "border-transparent bg-red-500 text-red-50 hover:bg-red-500/80",
  };

  const currentVariantClass = variantClasses[variant as CustomBadgeVariant] ?? '';

  return (
    <ShadcnBadge className={cn(currentVariantClass, className)} {...props} />
  );
};

export { Badge };