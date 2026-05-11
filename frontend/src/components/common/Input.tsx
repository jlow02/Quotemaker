import { Input as ShadcnInput } from "@/components/ui/input";
import React from "react";
import { cn } from "@/lib/utils"; // Assuming shadcn's utility for class merging

/**
 * @purpose Props for the Input component.
 * @owner Gemini
 */
interface InputProps extends React.ComponentPropsWithoutRef<typeof ShadcnInput> {
  /**
   * Optional label for the input field.
   */
  label?: string;
  /**
   * An error message to display below the input. When present, the input will be marked as invalid.
   */
  errorMessage?: string;
  /**
   * Helper text to display below the input, providing additional context.
   */
  helperText?: string;
}

/**
 * @purpose A wrapper around shadcn Input with optional label, error message, and helper text.
 * @param {InputProps} props - The props for the Input component.
 * @returns {JSX.Element} The rendered Input component.
 * @owner Gemini
 */
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, errorMessage, helperText, className, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id || generatedId;
    const hasError = !!errorMessage;

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            {label}
          </label>
        )}
        <ShadcnInput
          ref={ref}
          id={inputId}
          className={cn(hasError && "border-destructive focus-visible:ring-destructive", className)}
          aria-invalid={hasError}
          {...props}
        />
        {errorMessage && (
          <p className="text-sm font-medium text-destructive">{errorMessage}</p>
        )}
        {!errorMessage && helperText && (
          <p className="text-sm text-muted-foreground">{helperText}</p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };