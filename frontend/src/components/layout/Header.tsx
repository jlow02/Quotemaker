import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';

// Mock useAuth for demonstration. In a real app, this would be a custom hook using Context or Zustand.
interface AuthState {
  user: { email: string } | null;
  logout: () => void;
}
const useAuth = (): AuthState => ({
  user: { email: 'user@nextan.com' },
  logout: () => alert('Logging out...'),
});

/**
 * @purpose Defines the properties for the Header component.
 * @owner [Gemini]
 */
interface HeaderProps {
  // No explicit props needed for Header as it consumes global state.
}

/**
 * @purpose Renders the top header bar of the application.
 *          It displays the application name, current user's email,
 *          and a logout button.
 * @param {HeaderProps} props - The properties for the component.
 * @returns {JSX.Element} The rendered header component.
 * @owner [Gemini]
 */
export function Header(_props: HeaderProps): JSX.Element {
  const { user, logout } = useAuth(); // Assuming useAuth provides user info and logout function

  const handleLogout = (): void => {
    logout();
  };

  return (
    <header className="flex items-center justify-between h-16 px-6 border-b bg-background">
      <div className="flex items-center">
        <h1 className="text-xl font-semibold text-foreground">NEXTAN Costing</h1>
      </div>
      <div className="flex items-center space-x-4">
        {user && <span className="text-sm text-muted-foreground">{user.email}</span>}
        <Button onClick={handleLogout} variant="ghost" size="sm">
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </Button>
      </div>
    </header>
  );
}