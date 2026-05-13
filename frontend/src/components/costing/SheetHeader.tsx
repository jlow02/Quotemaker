import { useState, useRef, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

/**
 * @purpose Real API shape for a costing sheet (snake_case from backend).
 * @owner [Claude]
 */
export interface CostingSheetAPI {
  id: string;
  ref_number: string;
  date: string;
  quote_title: string;
  client_name: string;
  contact_name?: string | null;
  contact_email?: string | null;
  payment_term?: string | null;
  quotation_validity_days?: number | null;
  lead_time?: string | null;
  local_tax?: string | null;
  warranty?: string | null;
  general_notes?: string | null;
  created_at: string;
  updated_at: string;
}

interface SheetHeaderProps {
  sheet: CostingSheetAPI;
  onUpdate: (sheetId: string, updatedFields: Partial<CostingSheetAPI>) => void;
}

/**
 * @purpose Displays the costing sheet header — ref, title, client, date. Inline title editing.
 * @owner [Claude]
 */
export function SheetHeader({ sheet, onUpdate }: SheetHeaderProps): JSX.Element {
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState(sheet.quote_title ?? '');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditingTitle && inputRef.current) inputRef.current.focus();
  }, [isEditingTitle]);

  const handleTitleBlur = () => {
    setIsEditingTitle(false);
    if (editedTitle.trim() && editedTitle !== sheet.quote_title) {
      onUpdate(sheet.id, { quote_title: editedTitle });
    }
  };

  const formattedDate = (() => {
    const raw = sheet.date ?? sheet.created_at;
    if (!raw) return '—';
    const d = new Date(raw);
    return isNaN(d.getTime()) ? raw : d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  })();

  return (
    <div className="flex items-center justify-between p-4 border-b bg-background">
      <div className="flex flex-col gap-1">
        {isEditingTitle ? (
          <Input
            ref={inputRef}
            className="text-2xl font-bold w-96 p-1 h-auto"
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            onBlur={handleTitleBlur}
            onKeyDown={(e) => { if (e.key === 'Enter') handleTitleBlur(); if (e.key === 'Escape') { setIsEditingTitle(false); setEditedTitle(sheet.quote_title ?? ''); } }}
          />
        ) : (
          <h1
            className="text-2xl font-bold cursor-pointer hover:text-primary"
            onClick={() => setIsEditingTitle(true)}
          >
            {sheet.quote_title || 'Untitled Sheet'}
          </h1>
        )}
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          {sheet.ref_number && <span>Ref: {sheet.ref_number}</span>}
          {sheet.client_name && <span>Client: {sheet.client_name}</span>}
          <span>Created: {formattedDate}</span>
        </div>
      </div>
      <Badge variant="outline">Draft</Badge>
    </div>
  );
}
