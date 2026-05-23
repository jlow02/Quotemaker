// FILE: frontend/src/pages/CostingSheetDetail.tsx
import React, { useEffect, useMemo, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Download, History, ArrowLeft, LayoutTemplate } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Separator } from '../components/ui/separator';
import { Toaster } from '@/components/ui/toaster';
import { useToast } from '../components/ui/use-toast';
import { useUiStore } from '../store/uiStore';
import {
  getCostingSheet, listScenarios, listFxOverrides, listLineItems,
  createLineItem, deleteLineItem, createExport, downloadExport,
  getLiveFxRates, createScenario, updateScenario, listTemplates, applyTemplate,
  LineItem,
} from '../api/services';
import { SheetHeader } from '../components/costing/SheetHeader';
import { ScenarioTabs } from '../components/costing/ScenarioTabs';
import { LineItemTable } from '../components/costing/LineItemTable';
import { AddLineItemDialog } from '../components/costing/AddLineItemDialog';
import { TermsAndNotesPanel } from '../components/costing/TermsAndNotesPanel';
import CostingSheetTotals from '../components/costing/CostingSheetTotals';
import QuotePreview from '../components/costing/QuotePreview';
import MarginSummary from '../components/costing/MarginSummary';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

const CostingSheetDetail: React.FC = () => {
  const { sheetId } = useParams<{ sheetId: string }>();
  const navigate = useNavigate();
  const { activeSheetId, activeScenarioId, setActiveSheet, setActiveScenario } = useUiStore();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [addItemOpen, setAddItemOpen] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);

  const sheetQuery = useQuery({ queryKey: ['costingSheet', sheetId], queryFn: () => getCostingSheet(sheetId!), enabled: !!sheetId });
  const scenariosQuery = useQuery({ queryKey: ['scenarios', sheetId], queryFn: () => listScenarios(sheetId!), enabled: !!sheetId });
  const fxOverridesQuery = useQuery({ queryKey: ['fxOverrides', sheetId], queryFn: () => listFxOverrides(sheetId!), enabled: !!sheetId });
  const liveFxRatesQuery = useQuery({ queryKey: ['liveFxRates'], queryFn: () => getLiveFxRates(), staleTime: 1000 * 60 * 30 });
  const templatesQuery = useQuery({ queryKey: ['templates'], queryFn: () => listTemplates(), enabled: templateDialogOpen });

  useEffect(() => { if (sheetId && activeSheetId !== sheetId) setActiveSheet(sheetId); }, [sheetId, activeSheetId, setActiveSheet]);
  useEffect(() => { if (!activeScenarioId && (scenariosQuery.data?.length ?? 0) > 0) setActiveScenario(scenariosQuery.data![0].id); }, [activeScenarioId, scenariosQuery.data, setActiveScenario]);

  const lineItemsQuery = useQuery({ queryKey: ['lineItems', activeScenarioId], queryFn: () => listLineItems(activeScenarioId!), enabled: !!activeScenarioId });
  const activeScenario = useMemo(() => scenariosQuery.data?.find((s) => s.id === activeScenarioId), [scenariosQuery.data, activeScenarioId]);

  const [discountType, setDiscountType] = useState<string | null>(activeScenario?.discount_type ?? null);
  const [discountValue, setDiscountValue] = useState<number | null>(
    activeScenario?.discount_value != null ? Number(activeScenario.discount_value) : null
  );
  const [showGst, setShowGst] = useState<boolean>(activeScenario?.show_gst ?? false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (activeScenario) {
      setDiscountType(activeScenario.discount_type ?? null);
      setDiscountValue(activeScenario.discount_value != null ? Number(activeScenario.discount_value) : null);
      setShowGst(activeScenario.show_gst ?? false);
    }
  }, [activeScenario?.id]);

  const updateScenarioMutation = useMutation({
    mutationFn: (data: { discount_type?: string | null; discount_value?: number | null; show_gst?: boolean }) =>
      updateScenario(activeScenarioId!, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['scenarios', sheetId] }); },
    onError: (error: Error) => { toast({ title: 'Update failed', description: error.message, variant: 'destructive' }); },
  });

  const handleDiscountTypeChange = (value: string | null) => {
    setDiscountType(value);
    const newValue = value === null ? null : discountValue;
    if (value === null) setDiscountValue(null);
    updateScenarioMutation.mutate({ discount_type: value, discount_value: newValue });
  };
  const handleDiscountValueChange = (value: number | null) => {
    setDiscountValue(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => { updateScenarioMutation.mutate({ discount_value: value }); }, 750);
  };
  const handleGstToggle = (value: boolean) => {
    setShowGst(value);
    updateScenarioMutation.mutate({ show_gst: value });
  };

  const createScenarioMutation = useMutation({ mutationFn: (name: string) => createScenario(sheetId!, { name, display_order: (scenariosQuery.data?.length ?? 0) + 1 }), onSuccess: (newScenario) => { queryClient.invalidateQueries({ queryKey: ['scenarios', sheetId] }); setActiveScenario(newScenario.id); }, onError: (error) => { toast({ title: 'Failed to create scenario', description: error.message, variant: 'destructive' }); } });
  const createLineItemMutation = useMutation({ mutationFn: (data: Parameters<typeof createLineItem>[1]) => createLineItem(activeScenarioId!, data), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['lineItems', activeScenarioId] }); setAddItemOpen(false); toast({ title: 'Line item added' }); }, onError: (error: Error) => { toast({ title: 'Failed to add line item', description: error.message, variant: 'destructive' }); } });
  const deleteLineItemMutation = useMutation({ mutationFn: (itemId: string) => deleteLineItem(itemId), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['lineItems', activeScenarioId] }); }, onError: (error: Error) => { toast({ title: 'Failed to delete item', description: error.message, variant: 'destructive' }); } });
  const exportMutation = useMutation({ mutationFn: (scenarioId: string) => createExport(scenarioId, { file_type: 'docx' }), onSuccess: async (exportData) => { try { const response = await downloadExport(exportData.id); const signedUrl = response?.signed_url; if (!signedUrl) throw new Error('No download URL returned from server'); const a = document.createElement('a'); a.href = signedUrl; a.download = 'quote_' + exportData.id + '.docx'; a.click(); a.remove(); toast({ title: 'Export downloaded!' }); } catch (_dlErr) { toast({ title: 'Export saved', description: 'File saved to exports history.' }); } }, onError: (error) => { toast({ title: 'Export failed', description: error.message, variant: 'destructive' }); } });
  const applyTemplateMutation = useMutation({
    mutationFn: () => applyTemplate(selectedTemplateId!, sheetId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scenarios', sheetId] });
      setTemplateDialogOpen(false);
      setSelectedTemplateId(null);
      toast({ title: 'Template applied successfully' });
    },
    onError: (error: Error) => {
      toast({ title: 'Failed to apply template', description: error.message, variant: 'destructive' });
    },
  });

  const isLoading = sheetQuery.isLoading || scenariosQuery.isLoading || fxOverridesQuery.isLoading || liveFxRatesQuery.isLoading;
  const isError = sheetQuery.isError || scenariosQuery.isError || fxOverridesQuery.isError || liveFxRatesQuery.isError || lineItemsQuery.isError;

  if (isLoading) return (<div className="flex justify-center items-center min-h-screen text-lg text-gray-600"><Loader2 className="mr-2 h-6 w-6 animate-spin" /> Loading costing sheet...</div>);
  if (isError) return (<div className="flex justify-center items-center min-h-screen text-red-600 text-lg">Error: {sheetQuery.error?.message || scenariosQuery.error?.message || 'An unexpected error occurred.'}</div>);

  const sheet = sheetQuery.data;

  return (
    <div className="container mx-auto p-6">
      <div className="mb-4"><Button variant="ghost" size="sm" onClick={() => navigate('/')}><ArrowLeft className="h-4 w-4 mr-1" /> Back to Dashboard</Button></div>
      <SheetHeader sheet={sheet as any} onUpdate={() => {}} />
      <Separator className="my-4" />
      <div className="mb-6 flex items-center gap-2">
        <ScenarioTabs scenarios={scenariosQuery.data || []} activeScenarioId={activeScenarioId || ''} onCreateScenario={() => createScenarioMutation.mutate('Scenario ' + ((scenariosQuery.data?.length ?? 0) + 1))} onSelectScenario={setActiveScenario} />
        <Dialog open={templateDialogOpen} onOpenChange={setTemplateDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" size="icon" title="Create scenario from template">
              <LayoutTemplate className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Select a Template</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              {templatesQuery.isLoading && (
                <div className="flex justify-center py-4">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              )}
              {templatesQuery.isError && (
                <p className="text-red-500 text-sm">Failed to load templates.</p>
              )}
              {templatesQuery.data && templatesQuery.data.length === 0 && (
                <p className="text-gray-500 text-sm">No templates available. Create one in Settings.</p>
              )}
              {templatesQuery.data && templatesQuery.data.map((template: any) => (
                <div
                  key={template.id}
                  className={`p-3 border rounded-md cursor-pointer transition-colors ${
                    selectedTemplateId === template.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedTemplateId(template.id)}
                >
                  <p className="font-medium">{template.name}</p>
                  {template.notes_exclusions && template.notes_exclusions.length > 0 && (
                    <p className="text-sm text-gray-500 mt-1">
                      {template.notes_exclusions.join(', ').substring(0, 80)}
                      {template.notes_exclusions.join(', ').length > 80 ? '...' : ''}
                    </p>
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => { setTemplateDialogOpen(false); setSelectedTemplateId(null); }}>
                Cancel
              </Button>
              <Button
                onClick={() => applyTemplateMutation.mutate()}
                disabled={!selectedTemplateId || applyTemplateMutation.isPending}
              >
                {applyTemplateMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Applying...
                  </>
                ) : (
                  'Apply Template'
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
      {activeScenario && (<LineItemTable scenarioId={activeScenarioId || ''} lineItems={(lineItemsQuery.data || []) as LineItem[]} onAddLineItem={() => setAddItemOpen(true)} onDeleteLineItem={(id) => deleteLineItemMutation.mutate(id)} />)}
      <MarginSummary lineItems={(lineItemsQuery.data || []) as LineItem[]} />
      <CostingSheetTotals
        scenarioId={activeScenarioId || ''}
        discountType={discountType}
        discountValue={discountValue}
        showGst={showGst}
        totals={activeScenario?.totals}
        isSaving={updateScenarioMutation.isPending}
        onDiscountTypeChange={handleDiscountTypeChange}
        onDiscountValueChange={handleDiscountValueChange}
        onGstToggle={handleGstToggle}
        lineItems={(lineItemsQuery.data || []) as LineItem[]}
      />
      <QuotePreview scenarioId={activeScenarioId || ''} scenarioName={activeScenario?.name} />
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="outline" onClick={() => sheetId && navigate('/sheets/' + sheetId + '/exports')}>
          <History className="mr-2 h-4 w-4" />View Exports
        </Button>
        <Button onClick={() => activeScenarioId && exportMutation.mutate(activeScenarioId)} disabled={!activeScenarioId || exportMutation.isPending}>
          {exportMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
          {exportMutation.isPending ? 'Exporting...' : `Export DOCX${activeScenario?.name ? ` — ${activeScenario.name}` : ''}`}
        </Button>
      </div>
      {sheet && sheetId && (<TermsAndNotesPanel sheet={sheet as any} sheetId={sheetId} />)}
      <AddLineItemDialog open={addItemOpen} onClose={() => setAddItemOpen(false)} onSubmit={(data) => createLineItemMutation.mutate(data)} isLoading={createLineItemMutation.isPending} />
      <Toaster />
    </div>
  );
};

export default CostingSheetDetail;
