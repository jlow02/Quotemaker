import { useState, useRef, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { updateCostingSheet } from '../../api/services';
import type { CostingSheetAPI } from './SheetHeader';

interface TermsAndNotesPanelProps {
  sheet: CostingSheetAPI;
  sheetId: string;
}

/**
 * @purpose Editable panel for Terms Block (FR10) and Notes & Exclusions (FR9).
 * Terms fields: Payment Term, Quotation Validity, Lead Time, Local Tax, Warranty.
 * Notes & Exclusions: editable bullet list (newline-separated, stored in general_notes).
 * All changes auto-save with 800ms debounce.
 * @owner [Claude]
 */
export function TermsAndNotesPanel({ sheet, sheetId }: TermsAndNotesPanelProps) {
  const [expanded, setExpanded] = useState(true);

  // Terms block state
  const [paymentTerm, setPaymentTerm] = useState(sheet.payment_term ?? '30 days net');
  const [validityDays, setValidityDays] = useState(String(sheet.quotation_validity_days ?? 90));
  const [leadTime, setLeadTime] = useState(sheet.lead_time ?? '30 working days');
  const [localTax, setLocalTax] = useState(sheet.local_tax ?? '');
  const [warranty, setWarranty] = useState(sheet.warranty ?? '12 months standard');

  // Notes & Exclusions state — stored as newline-separated, displayed as bullet list
  const rawNotes = sheet.general_notes ?? '';
  const [bullets, setBullets] = useState<string[]>(
    rawNotes ? rawNotes.split('\n').filter(Boolean) : []
  );

  const pendingRef = useRef<Record<string, unknown>>({});
  const timerRef = useRef<ReturnType<typeof setTimeout>>();
  const qc = useQueryClient();

  const saveMutation = useMutation({
    mutationFn: (data: Parameters<typeof updateCostingSheet>[1]) =>
      updateCostingSheet(sheetId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['costingSheet', sheetId] });
    },
  });

  const scheduleSave = useCallback(
    (update: Record<string, unknown>) => {
      pendingRef.current = { ...pendingRef.current, ...update };
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        const payload = { ...pendingRef.current } as Parameters<typeof updateCostingSheet>[1];
        pendingRef.current = {};
        if (Object.keys(payload).length > 0) {
          saveMutation.mutate(payload);
        }
      }, 800);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [sheetId],
  );

  const saveBullets = (newBullets: string[]) => {
    scheduleSave({ general_notes: newBullets.filter(Boolean).join('\n') });
  };

  const handleBulletChange = (index: number, value: string) => {
    const next = [...bullets];
    next[index] = value;
    setBullets(next);
    saveBullets(next);
  };

  const addBullet = () => {
    const next = [...bullets, ''];
    setBullets(next);
    // Don't save empty line yet — user will type
  };

  const removeBullet = (index: number) => {
    const next = bullets.filter((_, i) => i !== index);
    setBullets(next);
    saveBullets(next);
  };

  const isSaving = saveMutation.isPending;

  return (
    <div className="rounded-lg border bg-card shadow-sm mt-4">
      {/* Panel header */}
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm">Terms &amp; Notes</span>
          {isSaving && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-6">
          <Separator />

          {/* Terms Block */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">
              Terms Block
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="space-y-1">
                <Label className="text-xs">Payment Term</Label>
                <Input
                  value={paymentTerm}
                  onChange={(e) => {
                    setPaymentTerm(e.target.value);
                    scheduleSave({ payment_term: e.target.value });
                  }}
                  placeholder="e.g. 30 days net"
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Quotation Validity (days)</Label>
                <Input
                  type="number"
                  min="1"
                  value={validityDays}
                  onChange={(e) => {
                    setValidityDays(e.target.value);
                    scheduleSave({ quotation_validity_days: Number(e.target.value) });
                  }}
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Lead Time</Label>
                <Input
                  value={leadTime}
                  onChange={(e) => {
                    setLeadTime(e.target.value);
                    scheduleSave({ lead_time: e.target.value });
                  }}
                  placeholder="e.g. 30 working days"
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Local Tax</Label>
                <Input
                  value={localTax}
                  onChange={(e) => {
                    setLocalTax(e.target.value);
                    scheduleSave({ local_tax: e.target.value });
                  }}
                  placeholder="e.g. 9% GST"
                  className="h-8 text-sm"
                />
              </div>
              <div className="space-y-1 sm:col-span-2">
                <Label className="text-xs">Warranty</Label>
                <Input
                  value={warranty}
                  onChange={(e) => {
                    setWarranty(e.target.value);
                    scheduleSave({ warranty: e.target.value });
                  }}
                  placeholder="e.g. 12 months standard"
                  className="h-8 text-sm"
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Notes & Exclusions */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">
              Notes &amp; Exclusions
            </h3>
            <div className="space-y-2">
              {bullets.length === 0 && (
                <p className="text-xs text-muted-foreground italic">
                  No notes yet. Click &quot;Add Note&quot; to add bullet points.
                </p>
              )}
              {bullets.map((bullet, index) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="text-muted-foreground text-sm shrink-0">&bull;</span>
                  <Input
                    value={bullet}
                    onChange={(e) => handleBulletChange(index, e.target.value)}
                    placeholder="Enter note or exclusion..."
                    className="h-8 text-sm flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0"
                    onClick={() => removeBullet(index)}
                    title="Remove"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={addBullet}
                className="mt-1"
              >
                <Plus className="h-3.5 w-3.5 mr-1" />
                Add Note
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
