import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Settings, Files } from 'lucide-react';
import { cn } from '@/lib/utils'; // Assuming shadcn/ui's cn utility
import { Separator } from '@/components/ui/separator'; // Assuming shadcn/ui Separator

// Mock uiStore for demonstration. In a real app, this would be a Zustand/Jotai store.
const useUiStore = {
  isSidebarOpen: true, // Default to open for demonstration
  toggleSidebar: () => console.log('Toggling sidebar'),
};

/**
 * @purpose Defines the properties for the Sidebar component.
 * @owner [Gemini]
 */
interface SidebarProps {
  // No explicit props needed for Sidebar as it consumes global state.
}

/**
 * @purpose Renders the left-hand sidebar navigation for the application.
 *          It displays primary navigation links and manages its open/close state
 *          via the global uiStore.
 * @param {SidebarProps} props - The properties for the component.
 * @returns {JSX.Element} The rendered sidebar component.
 * @owner [Gemini]
 */
export function Sidebar(_props: SidebarProps): JSX.Element {
  const { isSidebarOpen } = useUiStore; // Assuming uiStore provides isSidebarOpen

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Settings', path: '/settings', icon: Settings },
    { name: 'Exports', path: '/exports', icon: Files },
  ];

  return (
    <aside
      className={cn(
        'flex flex-col h-screen border-r bg-background transition-all duration-300 ease-in-out',
        isSidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      <div className="flex items-center h-16 px-4">
        {isSidebarOpen ? (
          <h1 className="text-xl font-semibold text-primary">NEXTAN</h1>
        ) : (
          <span className="text-xl font-semibold text-primary">N</span>
        )}
      </div>
      <Separator />
      <nav className="flex-1 mt-4 space-y-2 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex items-center py-2 px-3 rounded-md text-sm font-medium transition-colors duration-200',
                  'hover:bg-accent hover:text-accent-foreground',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground',
                  isSidebarOpen ? 'justify-start' : 'justify-center'
                )
              }
            >
              <Icon className={cn('h-5 w-5', isSidebarOpen ? 'mr-3' : '')} />
              {isSidebarOpen && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}