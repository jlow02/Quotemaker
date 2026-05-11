import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { cn } from '@/lib/utils'; // Assuming shadcn/ui's cn utility

// Mock uiStore again, ensuring consistency with Sidebar.tsx.
// In a real app, this would be a single, shared instance.
const useUiStore = {
  isSidebarOpen: true, // Default to open for demonstration
  toggleSidebar: () => console.log('Toggling sidebar'),
};

/**
 * @purpose Defines the properties for the AppShell component.
 * @owner [Gemini]
 */
interface AppShellProps {
  // No explicit props needed for AppShell as it consumes global state.
}

/**
 * @purpose Provides the main application layout, wrapping the Sidebar, Header,
 *          and the dynamic page content via Outlet. It manages the overall
 *          structure and responsiveness based on sidebar's open/close state.
 * @param {AppShellProps} props - The properties for the component.
 * @returns {JSX.Element} The rendered application shell.
 * @owner [Gemini]
 */
export function AppShell(_props: AppShellProps): JSX.Element {
  const { isSidebarOpen } = useUiStore; // Assuming uiStore provides isSidebarOpen

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main
        className={cn(
          'flex-1 flex flex-col transition-all duration-300 ease-in-out',
          isSidebarOpen ? 'ml-0' : 'ml-0' // Sidebar is now a sibling, not adjusting margin
                                         // The sidebar handles its own width; main content fills remaining.
        )}
      >
        <Header />
        <div className="flex-1 overflow-y-auto bg-muted/40">
          <Outlet />
        </div>
      </main>
    </div>
  );
}