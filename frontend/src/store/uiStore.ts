import { create } from 'zustand';

/**
 * Interface for the UI store's state.
 * @owner [Gemini]
 */
export interface UiState {
  /**
   * Indicates whether the sidebar is currently open.
   */
  sidebarOpen: boolean;
  /**
   * The ID of the currently active sheet (e.g., a specific quote or costing sheet).
   * Null if no sheet is active.
   */
  activeSheetId: string | null;
  /**
   * The ID of the currently active scenario within a sheet.
   * Null if no scenario is active or no sheet is active.
   */
  activeScenarioId: string | null;
}

/**
 * Interface for the UI store's actions.
 * @owner [Gemini]
 */
export interface UiActions {
  /**
   * Toggles the sidebar's open/closed state.
   * @owner [Gemini]
   */
  toggleSidebar: () => void;
  /**
   * Sets the sidebar's open/closed state explicitly.
   * @param open - True to open the sidebar, false to close it.
   * @owner [Gemini]
   */
  setSidebar: (open: boolean) => void;
  /**
   * Sets the ID of the currently active sheet.
   * @param id - The ID of the sheet to set as active. Use null to clear.
   * @owner [Gemini]
   */
  setActiveSheet: (id: string | null) => void;
  /**
   * Sets the ID of the currently active scenario.
   * @param id - The ID of the scenario to set as active. Use null to clear.
   * @owner [Gemini]
   */
  setActiveScenario: (id: string | null) => void;
}

/**
 * Type combining the UI state and actions.
 * @owner [Gemini]
 */
export type UiStore = UiState & UiActions;

/**
 * Zustand store for managing global UI state.
 *
 * @purpose Manages global UI elements like sidebar visibility and active navigation states (sheet, scenario).
 * @returns A Zustand store hook for accessing UI state and actions.
 * @owner [Gemini]
 */
export const useUiStore = create<UiStore>((set: (partial: ((state: UiStore) => Partial<UiStore>) | Partial<UiStore>, replace?: boolean | undefined) => void) => ({
  // State
  sidebarOpen: true, // Default to open
  activeSheetId: null,
  activeScenarioId: null,

  // Actions
  toggleSidebar: (): void =>
    set((state: UiStore) => ({ sidebarOpen: !state.sidebarOpen })),

  setSidebar: (open: boolean): void =>
    set({ sidebarOpen: open }),

  setActiveSheet: (id: string | null): void =>
    set({ activeSheetId: id, activeScenarioId: null }), // Clear active scenario when sheet changes

  setActiveScenario: (id: string | null): void =>
    set((state: UiStore) => {
      // Only set scenario if a sheet is active, otherwise clear it.
      // Or, allow setting to null even if no sheet is active.
      if (state.activeSheetId === null && id !== null) {
        console.warn("Attempted to set active scenario without an active sheet.");
        return { activeScenarioId: null };
      }
      return { activeScenarioId: id };
    }),
}));
