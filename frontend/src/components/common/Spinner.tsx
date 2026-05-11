import React from "react";
import { cn } from "@/lib/utils"; // Assuming shadcn's utility for class merging

/**
 * @purpose Props for the Spinner component.
 * @owner Gemini
 */
interface SpinnerProps {
  /**
   * The size of the spinner.
   * 'sm' for small, 'md' for medium, 'lg' for large.
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Optional additional class names to apply to the spinner SVG.
   */
  className?: string;
}

/**
 * @purpose A simple SVG spinner component with different size options.
 * Utilizes Tailwind CSS for animation.
 * @param {SpinnerProps} props - The props for the Spinner component.
 * @returns {JSX.Element} The rendered SVG spinner.
 * @owner Gemini
 */
const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
  const sizeMap = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  };

  return (
    <svg
      className={cn("animate-spin text-current", sizeMap[size], className)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-label="Loading spinner"
      role="status"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      ></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
  );
};

export { Spinner };