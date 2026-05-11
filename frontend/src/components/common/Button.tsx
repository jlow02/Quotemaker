import { Button as ShadcnButton } from "@/components/ui/button";
import { Spinner } from "./Spinner";
import React from "react";

/**
 * @purpose Props for the Button component.
 * @owner Gemini
 */
interface ButtonProps extends React.ComponentPropsWithoutRef<typeof ShadcnButton> {
  /**
   * Whether the button is in a loading state. When true, a Spinner is shown and the button is disabled.
   */
  isLoading?: boolean;
}

/**
 * @purpose A wrapper around shadcn Button with loading state handling.
 * Displays a Spinner when `isLoading` is true, automatically disabling the button.
 * @param {ButtonProps} props - The props for the Button component.
 * @returns {JSX.Element} The rendered Button component.
 * @owner Gemini
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, isLoading = false, disabled, className, ...props }, ref) => {
    return (
      <ShadcnButton
        ref={ref}
        disabled={isLoading || disabled}
        className={className}
        {...props}
      >
        {isLoading ? <Spinner size="sm" /> : children}
      </ShadcnButton>
    );
  }
);
Button.displayName = "Button";

export { Button };