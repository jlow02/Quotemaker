import { useEffect, useState } from 'react';

/**
 * @purpose A generic debounce hook that delays updating a value until a specified time has passed.
 * This is useful for delaying expensive operations, like API calls or complex calculations,
 * until the user has stopped typing or interacting for a moment.
 * @param {T} value The value to debounce.
 * @param {number} delay The delay in milliseconds before the debounced value is updated.
 * @returns {T} The debounced value.
 * @owner [Gemini]
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set a timeout to update the debounced value after the specified delay
    const handler: ReturnType<typeof setTimeout> = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up the timeout if the value or delay changes, or if the component unmounts
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]); // Only re-run if value or delay changes

  return debouncedValue;
}