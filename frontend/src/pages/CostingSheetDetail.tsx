import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Download, History, ArrowLeft } from 'lucide-react';
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
  downloadExport,
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
 * @owner [Claude]
 */
const CostingSheetDetail: React.FC = () => {
  const { sheetId } = useParams<{ sheetId: string }>();
  const navigate = useNavigate();
  const { activeSheetId, activeScenarioId, setActiveSheet, setActiveScenario } = useUiStore();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [addItemOpen, setAddItemOpen] = useState(false);

  const sheetQuery = useQuery({
    queryKey: ['costingSheet', sheetId],
    queryFn: () => getCostingSheet(sheetId!),
    enabled: !!sheetId,
  });

  const scenariosQuery = useQuery({
    queryKey: ['scenarios', sheetId],
    queryFn: () => listScenarios(sheetId!),
    enabled: !!sheetId,
  });

  const fxOverridesQuery = useQuery({
    queryKey: ['fxOverrides', sheetId],
    queryFn: () => listFxOverrides(sheetId!),
    enabled: !!sheetId,
  });

  const liveFxRatesQuery = useQuery({
    queryKey: ['liveFxRates'],
    queryFn: () => getLiveFxRates(),
    staleTime: 1000 * 60 * 30,
    gcTime: 1000 * 60 * 60,
  });

  useEffect(() => {
    if (sheetId && activeSheetId !== sheetId) {
      setActiveSheet(sheetId);
    }
  }, [sheetId, activeSheetId, setActiveSheet]);

  useEffect(() => {
    if (!activeScenarioId && scenariosQuery.data && scenariosQuery.data.length > 0) {
      setActiveScenario(scenariosQuery.data[0].id);
    }
  }, [activeScenarioId, scenariosQuery.data, setActiveScenario]);

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
    const items = lineItemsQuery.data ?? [];
    return items
      .filter((item) => item.is_visible !== false && !item.parent_line_item_id)
      .reduce((sum, item) => {
        const lt = Number(item.computed?.line_total_sgd ?? 0);
        return sum + (lt > 0 ? lt : Number(item.qty) * Number(item.cost_rate));
      }, 0);
  }, [lineItemsQuery.data]);

  const grandTotalDisplay = new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    minimumFractionDigits: 2,
  }).format(grandTotal);

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
    onSuccess: async (exportData) => {
      try {
        const response = await downloadExport(exportData.id);
        const signedUrl = response?.signed_url;
        if (!signedUrl) throw new Error('No download URL returned from server');
        const a = document.createElement('a');
        a.href = signedUrl;
        a.download = 'quote_' + exportData.id + '.docx';
        a.click();
        a.remove();
        toast({ title: 'Export downloaded!', description: 'Your DOCX file is downloading.' });
      } catch (_dlErr) {
        toast({
          title: 'Export saved',
          description: 'File saved to exports history — click "View Exports" to download manually.',
        });
      }
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
      <div className="mb-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Dashboard
        </Button>
      </div>
      <SheetHeader sheet={sheetQuery.data as any} onUpdate={() => {}} />
      <Separator className="my-4" />
      <div className="mb-6">
        <ScenarioTabs
          scenarios={scenariosQuery.data || []}
          activeScenarioId={activeScenarioId || ''}
          onCreateScenario={() => createScenarioMutation.mutate('Scenario ' + ((scenariosQuery.data?.length ?? 0) + 1))}
          onSelectScenario={setActiveScenario}
        />
      </div>
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
      <div className="mt-4 flex justify-between items-center bg-gray-50 p-4 rounded-lg shadow-sm">
        <div className="text-xl font-semibold">Grand Total: {grandTotalDisplay}</div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => sheetId && navigate('/sheets/' + sheetId + '/exports')}
          >
            <History className="mr-2 h-4 w-4" />
            View Exports
          </Button>
          <Button
            onClick={() => activeScenarioId && exportMutation.mutate(activeScenarioId)}
            disabled={!activeScenarioId || exportMutation.isPending}
          >
            {exportMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Download className="mr-2 h-4 w-4" />
            )}
            {exportMutation.isPending ? 'Exporting...' : 'Export DOCX'}
          </Button>
        </div>
      </div>
      <Toaster />
    </div>
  );
};

export default CostingSheetDetail;
