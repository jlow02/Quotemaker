import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'; // Assuming shadcn/ui path
import { Button } from '@/components/ui/button'; // Assuming shadcn/ui path
import { PlusIcon } from 'lucide-react'; // Assuming lucide-react for icons

/**
 * @purpose Represents the shape of a scenario.
 * @owner Gemini
 */
interface Scenario {
  id: string;
  name: string;
}

/**
 * @purpose Props for the ScenarioTabs component.
 * @param scenarios An array of scenario objects to display as tabs.
 * @param activeScenarioId The ID of the currently active scenario.
 * @param onCreateScenario Callback function to create a new scenario.
 * @param onSelectScenario Callback function to select a scenario by its ID.
 * @owner Gemini
 */
interface ScenarioTabsProps {
  className?: string;
  scenarios: Scenario[];
  activeScenarioId: string;
  onCreateScenario: () => void;
  onSelectScenario: (scenarioId: string) => void;
}

/**
 * @purpose Displays a tab bar for navigating between different costing scenarios and adding new ones.
 * @param {ScenarioTabsProps} props - The props for the component.
 * @returns {JSX.Element} The rendered scenario tabs component.
 * @owner Gemini
 */
export function ScenarioTabs({
  scenarios,
  activeScenarioId,
  onCreateScenario,
  onSelectScenario,
}: ScenarioTabsProps): JSX.Element {
  return (
    <div className="flex items-center justify-between p-2 border-b bg-muted/40">
      <Tabs
        value={activeScenarioId}
        onValueChange={onSelectScenario}
        className="flex-grow max-w-full"
      >
        <TabsList className="flex overflow-x-auto whitespace-nowrap scrollbar-hide">
          {scenarios.map((scenario) => (
            <TabsTrigger key={scenario.id} value={scenario.id}>
              {scenario.name}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>
      <Button
        variant="outline"
        size="sm"
        onClick={onCreateScenario}
        className="ml-4 flex-shrink-0"
        aria-label="Create new scenario"
      >
        <PlusIcon className="mr-2 h-4 w-4" />
        New Scenario
      </Button>
    </div>
  );
}