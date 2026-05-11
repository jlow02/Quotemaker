import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * @purpose Merges Tailwind CSS classes with conflict resolution.
 * @param inputs Class values to merge.
 * @returns Merged class string.
 * @owner [Gemini]
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}