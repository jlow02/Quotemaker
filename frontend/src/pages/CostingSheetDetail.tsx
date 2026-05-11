import React, { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Download } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Separator } from '../components/ui/separator';
import { Toaster } from '@/components/ui/toaster';
import { useToast } from '../components/ui/use-toast';
import { useUiStore } from '../store/uiStore';
import {
  getCostingSheet,
  listScenarios,
  listFxOverrides,
  listLineItems,
  createLineItem,
  deleteLineItem,
  createExport,
  getLiveFxRates,
  createScenario,
} from '../api/services';
import { SheetHeader } from '../components/costing/SheetHeader';
import { ScenarioTabs } from '../components/costing/ScenarioTabs';
import { LineItemTable } from '../components/costing/LineItemTable';
import { AddLineItemDialog } from '../components/costing/AddLineItemDialog';

/**
 * @purpose Renders the detailed view of a costing sheet, including scenarios, line items, and financial calculations.
 * Orchestrates data fetching and delegates rendering to sub-components.
 * @param None
 * @returns {JSX.Element} The CostingSheetDetail page component.
 * @owner Gemini
 */
const CostingSheetDetail: React.FC = () => {
  const { sheetId } = useParams<{ sheetId: string }>();
  const { activeSheetId, activeScenarioId, setActiveSheet, setActiveScenario } = useUiStore();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [addItemOpen, setAddItemOpen] = useState(false);

  // Fetch costing sheet details
  const sheetQuery = useQuery({
    queryKey: ['costingSheet', sheetId],
    queryFn: () => getCostingSheet(sheetId!),
    enabled: !!sheetId,
  });

  // Fetch scenarios for the sheet
  const scenariosQuery = useQuery({
    queryKey: ['scenarios', sheetId],
    queryFn: () => listScenarios(sheetId!),
    enabled: !!sheetId,
  });

  // Fetch FX overrides for the sheet
  const fxOverridesQuery = useQuery({
    queryKey: ['fxOverrides', sheetId],
    queryFn: () => listFxOverrides(sheetId!),
    enabled: !!sheetId,
  });

  // Fetch live FX rates once on mount and keep
  const liveFxRatesQuery = useQuery({
    queryKey: ['liveFxRates'],
    queryFn: () => getLiveFxRates(),
    staleTime: 1000 * 60 * 30, // Rates are good for 30 minutes
    gcTime: 1000 * 60 * 60, // Cache for 1 hour
  });

  // Set active sheet so uiStore allows scenario selection
  useEffect(() => {
    if (sheetId && activeSheetId !== sheetId) {
      setActiveSheet(sheetId);
    }
  }, [sheetId, activeSheetId, setActiveSheet]);

  // Set active scenario to the first one if not already set
  useEffect(() => {
    if (!activeScenarioId && scenariosQuery.data && scenariosQuery.data.length > 0) {
      setActiveScenario(scenariosQuery.data[0].id);
    }
  }, [activeScenarioId, scenariosQuery.data, setActiveScenario]);

  // Fetch line items for the active scenario
  const lineItemsQuery = useQuery({
    queryKey: ['lineItems', activeScenarioId],
    queryFn: () => listLineItems(activeScenarioId!),
    enabled: !!activeScenarioId,
  });

  const activeScenario = useMemo(
    () => scenariosQuery.data?.find((s) => s.id === activeScenarioId),
    [scenariosQuery.data, activeScenarioId],
  );

  const grandTotal = useMemo(() => {
    const items = (lineItemsQuery.data ?? []) as Array<{
      is_visible?: boolean;
      computed?: { line_total_sgd?: string | number };
      qty: string | number;
      cost_rate: string | number;
    }>;
    return items
      .filter((item) => item.is_visible !== false)
      .reduce((sum, item) => {
        // Prefer backend computed value (includes markup + FX); fall back to qty×cost_rate
        const computed = Number(item.computed?.line_total_sgd ?? 0);
        return sum + (computed > 0 ? computed : Number(item.qty) * Number(item.cost_rate));
      }, 0)
      .toFixed(2);
  }, [lineItemsQuery.data]);

  // Scenario mutation
  const createScenarioMutation = useMutation({
    mutationFn: (name: string) => createScenario(sheetId!, { name, display_order: (scenariosQuery.data?.length ?? 0) + 1 }),
    onSuccess: (newScenario) => {
      queryClient.invalidateQueries({ queryKey: ['scenarios', sheetId] });
      setActiveScenario(newScenario.id);
    },
    onError: (error) => {
      toast({ title: 'Failed to create scenario', description: error.message, variant: 'destructive' });
    },
  });

  // Line item mutations
  const createLineItemMutation = useMutation({
    mutationFn: (data: Parameters<typeof createLineItem>[1]) =>
      createLineItem(activeScenarioId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lineItems', activeScenarioId] });
      setAddItemOpen(false);
      toast({ title: 'Line item added' });
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to add line item', description: error.message, variant: 'destructive' });
    },
  });

  const deleteLineItemMutation = useMutation({
    mutationFn: (itemId: string) => deleteLineItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lineItems', activeScenarioId] });
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to delete item', description: error.message, variant: 'destructive' });
    },
  });

  const exportMutation = useMutation({
    mutationFn: (scenarioId: string) => createExport(scenarioId, { file_type: 'docx' }),
    onSuccess: () => {
      toast({ title: 'Export successful!', description: 'DOCX saved to exports history.' });
    },
    onError: (error) => {
      toast({ title: 'Export failed', description: error.message, variant: 'destructive' });
    },
  });

  const isLoading =
    sheetQuery.isLoading ||
    scenariosQuery.isLoading ||
    fxOverridesQuery.isLoading ||
    liveFxRatesQuery.isLoading;

  const isError =
    sheetQuery.isError ||
    scenariosQuery.isError ||
    fxOverridesQuery.isError ||
    liveFxRatesQuery.isError ||
    lineItemsQuery.isError;

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen text-lg text-gray-600">
        <Loader2 className="mr-2 h-6 w-6 animate-spin" /> Loading costing sheet...
      </div>
    );
  }

  if (isError) {
    const errorMessage =
      sheetQuery.error?.message ||
      scenariosQuery.error?.message ||
      fxOverridesQuery.error?.message ||
      liveFxRatesQuery.error?.message ||
      lineItemsQuery.error?.message ||
      'An unexpected error occurred.';
    return (
      <div className="flex justify-center items-center min-h-screen text-red-600 text-lg">
        Error: {errorMessage}
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <SheetHeader sheet={sheetQuery.data as any} onUpdate={() => {}} />
      <Separator className="my-4" />
      <div className='mb-6'><ScenarioTabs
        scenarios={scenariosQuery.data || []}
        activeScenarioId={activeScenarioId || ''}
        onCreateScenario={() => createScenarioMutation.mutate('Scenario ' + ((scenariosQuery.data?.length ?? 0) + 1))}
        onSelectScenario={setActiveScenario}
      /></div>
      {activeScenario && (
        <LineItemTable
          scenarioId={activeScenarioId || ''}
          lineItems={(lineItemsQuery.data || []) as import('../api/services').LineItem[]}
          onAddLineItem={() => setAddItemOpen(true)}
          onDeleteLineItem={(id) => deleteLineItemMutation.mutate(id)}
        />
      )}
      <AddLineItemDialog
        open={addItemOpen}
        onClose={() => setAddItemOpen(false)}
        onSubmit={(data) => createLineItemMutation.mutate(data)}
        isLoading={createLineItemMutation.isPending}
      />
      <div className="flex justify-between items-center bg-gray-50 p-4 rounded-lg shadow-sm">
        <div className="text-xl font-semibold">Grand Total: {grandTotal}</div>
        <Button
          onClick={() => activeScenarioId && exportMutation.mutate(activeScenarioId)}
          disabled={!activeScenarioId || exportMutation.isPending}
        >
          {exportMutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          {exportMutation.isPending ? 'Exporting…' : 'Export DOCX'}
        </Button>
      </div>
      <Toaster />
    </div>
  );
};

export default CostingSheetDetail;