import { useState, useRef, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PlusCircle, Trash2, Eye, EyeOff, Loader2, ChevronDown, ChevronRight, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { updateLineItem, setBundleOverride, addBundleComponent } from '../../api/services';
import type { LineItem } from '../../api/services';

const SECTIONS = ['Hardware', 'Software', 'Professional Fees', 'Maintenance'] as const;
type Section = typeof SECTIONS[number];

const fmtSGD = (val?: string | number | null): string => {
  const n = Number(val ?? 0);
  if (isNaN(n)) return '—';
  return new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
};

const pct = (val: string | number) => {
  const n = Number(val);
  return isNaN(n) ? 0 : Math.round(n * 100);
};

// == Editable row =============================================================

interface EditableRowProps {
  item: LineItem;
  scenarioId: string;
  onDelete: (id: string) => void;
  selected: boolean;
  onSelect: (id: string, checked: boolean) => void;
}

function EditableRow({ item, scenarioId, onDelete, selected, onSelect }: EditableRowProps) {
  const [description, setDescription] = useState(item.description);
  const [qty, setQty] = useState(String(item.qty));
  const [unit, setUnit] = useState(item.unit);
  const [costRate, setCostRate] = useState(String(item.cost_rate));
  const [markupDisplay, setMarkupDisplay] = useState(String(pct(item.markup_pct)));
  const [contingencyDisplay, setContingencyDisplay] = useState(String(pct(item.contingency_pct ?? 0)));
  const [visible, setVisible] = useState(item.is_visible ?? true);

  const pendingRef = useRef<Partial<Parameters<typeof updateLineItem>[1]>>({});
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  const qc = useQueryClient();

  const saveMutation = useMutation({
    mutationFn: (data: Parameters<typeof updateLineItem>[1]) =>
      updateLineItem(item.id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['lineItems', scenarioId] });
    },
  });

  const scheduleSave = useCallback(
    (update: Partial<Parameters<typeof updateLineItem>[1]>) => {
      pendingRef.current = { ...pendingRef.current, ...update };
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        const payload = { ...pendingRef.current };
        pendingRef.current = {};
        if (Object.keys(payload).length > 0) {
          saveMutation.mutate(payload);
        }
      }, 800);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [item.id, scenarioId],
  );

  const handleVisible = () => {
    const next = !visible;
    setVisible(next);
    scheduleSave({ is_visible: next });
  };

  const sellingRateSGD = item.computed?.selling_rate_sgd
    ? Number(item.computed.selling_rate_sgd)
    : Number(costRate) * (1 + Number(markupDisplay) / 100 + Number(contingencyDisplay) / 100);

  const lineTotalSGD = item.computed?.line_total_sgd
    ? Number(item.computed.line_total_sgd)
    : sellingRateSGD * Number(qty);

  const isSaving = saveMutation.isPending;

  return (
    <tr className={`border-b last:border-b-0 transition-opacity ${!visible ? 'opacity-40' : ''}`}>
      <td className='px-2 py-1.5 w-8'>
        <input
          type='checkbox'
          className='h-4 w-4'
          checked={selected}
          onChange={(e) => onSelect(item.id, e.target.checked)}
        />
      </td>
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-1">
          {isSaving && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground shrink-0" />}
          <Input
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              scheduleSave({ description: e.target.value });
            }}
            className="h-8 text-sm min-w-[160px]"
          />
        </div>
      </td>
      <td className="px-2 py-1.5">
        <Input
          type="number"
          min="0"
          step="any"
          value={qty}
          onChange={(e) => {
            setQty(e.target.value);
            scheduleSave({ qty: e.target.value });
          }}
          className="h-8 text-sm w-16 text-right"
        />
      </td>
      <td className="px-2 py-1.5">
        <Input
          value={unit}
          onChange={(e) => {
            setUnit(e.target.value);
            scheduleSave({ unit: e.target.value });
          }}
          className="h-8 text-sm w-20"
        />
      </td>
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground w-8 shrink-0">{item.cost_currency}</span>
          <Input
            type="number"
            min="0"
            step="any"
            value={costRate}
            onChange={(e) => {
              setCostRate(e.target.value);
              scheduleSave({ cost_rate: e.target.value });
            }}
            className="h-8 text-sm w-24 text-right"
          />
        </div>
      </td>
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-0.5">
          <Input
            type="number"
            min="0"
            step="1"
            value={markupDisplay}
            onChange={(e) => {
              setMarkupDisplay(e.target.value);
              scheduleSave({ markup_pct: String(Number(e.target.value) / 100) });
            }}
            className="h-8 text-sm w-14 text-right"
          />
          <span className="text-xs text-muted-foreground">%</span>
        </div>
      </td>
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-0.5">
          <Input
            type="number"
            min="0"
            step="1"
            value={contingencyDisplay}
            onChange={(e) => {
              setContingencyDisplay(e.target.value);
              scheduleSave({ contingency_pct: String(Number(e.target.value) / 100) });
            }}
            className="h-8 text-sm w-14 text-right"
          />
          <span className="text-xs text-muted-foreground">%</span>
        </div>
      </td>
      <td className="px-2 py-1.5 text-right text-sm tabular-nums text-muted-foreground">
        {fmtSGD(sellingRateSGD)}
      </td>
      <td className="px-2 py-1.5 text-right text-sm font-semibold tabular-nums">
        {fmtSGD(lineTotalSGD)}
      </td>
      <td className="px-2 py-1.5 text-center">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={handleVisible}
          title={visible ? 'Hide from quote' : 'Show on quote'}
        >
          {visible ? (
            <Eye className="h-4 w-4 text-green-600" />
          ) : (
            <EyeOff className="h-4 w-4 text-muted-foreground" />
          )}
        </Button>
      </td>
      <td className="px-2 py-1.5 text-center">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => onDelete(item.id)}
          title="Delete item"
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </td>
    </tr>
  );
}

// == Main table ================================================================

interface LineItemTableProps {
  scenarioId: string;
  lineItems: LineItem[];
  onAddLineItem: (scenarioId: string) => void;
  onDeleteLineItem: (itemId: string) => void;
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  onAddBundleComponent: (parentId: string) => void;
  onSetBundleOverride: (itemId: string, price: string | null) => void;
}

/**
 * @purpose Displays line items grouped by section (Hardware/Software/Professional Fees/Maintenance)
 * with section subtotals, inline editing with auto-save (800ms debounce), and visibility toggles.
 * Uses computed.line_total_sgd from backend (selling_rate = cost_sgd * (1 + markup + contingency)).
 * @owner [Claude]
 */
export function LineItemTable({
  scenarioId,
  lineItems,
  onAddLineItem,
  onDeleteLineItem,
  selectedIds,
  onSelectionChange,
  onAddBundleComponent,
  onSetBundleOverride,
}: LineItemTableProps): JSX.Element {
  const topLevelItems = lineItems.filter((i) => !i.parent_line_item_id);
  const [expandedBundles, setExpandedBundles] = useState<Set<string>>(new Set(topLevelItems.filter(i => i.is_bundle_parent).map(i => i.id)));

  const bySection: Record<Section, LineItem[]> = {
    Hardware: [],
    Software: [],
    'Professional Fees': [],
    Maintenance: [],
  };

  for (const item of lineItems) {
    if (item.parent_line_item_id) continue;
    const sec = item.section as Section;
    if (bySection[sec]) {
      bySection[sec].push(item);
    } else {
      bySection.Hardware.push(item);
    }
  }

  for (const sec of SECTIONS) {
    bySection[sec].sort((a, b) => a.display_order - b.display_order);
  }

  const sectionSubtotal = (items: LineItem[]): number =>
    items
      .filter((i) => i.is_visible !== false)
      .reduce((sum, i) => {
        const lt = Number(i.computed?.line_total_sgd ?? 0);
        return sum + (lt > 0 ? lt : Number(i.qty) * Number(i.cost_rate));
      }, 0);

  const allSelected = topLevelItems.length > 0 && topLevelItems.every(i => selectedIds.has(i.id));

  const handleSelectAll = () => {
    if (allSelected) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(topLevelItems.map(i => i.id)));
    }
  };

  const handleSelect = (id: string, checked: boolean) => {
    const next = new Set(selectedIds);
    if (checked) {
      next.add(id);
    } else {
      next.delete(id);
    }
    onSelectionChange(next);
  };

  const toggleBundle = (id: string) => {
    const next = new Set(expandedBundles);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setExpandedBundles(next);
  };

  const BundleParentRow = ({ item }: { item: LineItem }) => {
    const [description, setDescription] = useState(item.description);
    const [qty, setQty] = useState(String(item.qty));
    const [unit, setUnit] = useState(item.unit);
    const [visible, setVisible] = useState(item.is_visible ?? true);
    const [overridePrice, setOverridePrice] = useState(item.bundle_override_price ?? '');

    const pendingRef = useRef<Partial<Parameters<typeof updateLineItem>[1]>>({});
    const timerRef = useRef<ReturnType<typeof setTimeout>>();

    const qc = useQueryClient();

    const saveMutation = useMutation({
      mutationFn: (data: Parameters<typeof updateLineItem>[1]) =>
        updateLineItem(item.id, data),
      onSuccess: () => {
        qc.invalidateQueries({ queryKey: ['lineItems', scenarioId] });
      },
    });

    const scheduleSave = useCallback(
      (update: Partial<Parameters<typeof updateLineItem>[1]>) => {
        pendingRef.current = { ...pendingRef.current, ...update };
        clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => {
          const payload = { ...pendingRef.current };
          pendingRef.current = {};
          if (Object.keys(payload).length > 0) {
            saveMutation.mutate(payload);
          }
        }, 800);
      },
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [item.id, scenarioId],
    );

    const handleVisible = () => {
      const next = !visible;
      setVisible(next);
      scheduleSave({ is_visible: next });
    };

    const subComponents = lineItems.filter((li) => li.parent_line_item_id === item.id);
    const subTotal = subComponents.reduce((sum, sub) => {
      const lt = Number(sub.computed?.line_total_sgd ?? 0);
      return sum + (lt > 0 ? lt : Number(sub.qty) * Number(sub.cost_rate));
    }, 0);

    const lineTotal = item.is_bundle_override_active && item.bundle_override_price
      ? Number(item.bundle_override_price)
      : subTotal;

    const isExpanded = expandedBundles.has(item.id);
    const isSaving = saveMutation.isPending;

    return (
      <>
        <tr className={`border-b last:border-b-0 transition-opacity ${!visible ? 'opacity-40' : ''}`}>
          <td className='px-2 py-1.5 w-8'>
            <input
              type='checkbox'
              className='h-4 w-4'
              checked={selectedIds.has(item.id)}
              onChange={(e) => handleSelect(item.id, e.target.checked)}
            />
          </td>
          <td className="px-2 py-1.5">
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 shrink-0"
                onClick={() => toggleBundle(item.id)}
                title={isExpanded ? 'Collapse bundle' : 'Expand bundle'}
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
              {isSaving && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground shrink-0" />}
              <Input
                value={description}
                onChange={(e) => {
                  setDescription(e.target.value);
                  scheduleSave({ description: e.target.value });
                }}
                className="h-8 text-sm min-w-[140px]"
              />
              <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 ml-1">
                BUNDLE
              </span>
            </div>
          </td>
          <td className="px-2 py-1.5">
            <Input
              type="number"
              min="0"
              step="any"
              value={qty}
              onChange={(e) => {
                setQty(e.target.value);
                scheduleSave({ qty: e.target.value });
              }}
              className="h-8 text-sm w-16 text-right"
            />
          </td>
          <td className="px-2 py-1.5">
            <Input
              value={unit}
              onChange={(e) => {
                setUnit(e.target.value);
                scheduleSave({ unit: e.target.value });
              }}
              className="h-8 text-sm w-20"
            />
          </td>
          <td colSpan={3} className="px-2 py-1.5 text-sm text-muted-foreground italic">
            Price from components
          </td>
          <td className="px-2 py-1.5 text-right text-sm font-semibold tabular-nums">
            {item.is_bundle_override_active && item.bundle_override_price ? (
              <span className="italic">{fmtSGD(lineTotal)}</span>
            ) : (
              fmtSGD(lineTotal)
            )}
          </td>
          <td className="px-2 py-1.5 text-center">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleVisible}
              title={visible ? 'Hide from quote' : 'Show on quote'}
            >
              {visible ? (
                <Eye className="h-4 w-4 text-green-600" />
              ) : (
                <EyeOff className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          </td>
          <td className="px-2 py-1.5 text-center">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onDeleteLineItem(item.id)}
              title="Delete item"
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          </td>
        </tr>
        {isExpanded && (
          <>
            {/* Override price row */}
            <tr className="bg-blue-50/30 border-b">
              <td colSpan={2} />
              <td colSpan={7} className="px-3 py-1.5">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-muted-foreground shrink-0">Override price (optional):</span>
                  <Input
                    type="number"
                    min="0"
                    step="any"
                    className="h-7 text-xs w-36"
                    placeholder="Leave blank for component sum"
                    value={overridePrice}
                    onChange={(e) => setOverridePrice(e.target.value)}
                    onBlur={() => onSetBundleOverride(item.id, overridePrice.trim() || null)}
                  />
                  {item.is_bundle_override_active && (
                    <span className="text-xs text-blue-600">Override active</span>
                  )}
                  {item.is_bundle_override_active && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 text-xs px-2"
                      onClick={() => { setOverridePrice(''); onSetBundleOverride(item.id, null); }}
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </td>
              <td colSpan={2} />
            </tr>
            {/* Sub-component rows */}
            {item.sub_components?.map((sub) => (
              <tr key={sub.id} className="border-b bg-muted/5">
                <td />
                <td className="px-2 py-1.5 pl-8">
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <span className="shrink-0">↳</span>
                    <span>{sub.description}</span>
                  </div>
                </td>
                <td className="px-2 py-1.5 text-sm text-muted-foreground text-center">{sub.qty}</td>
                <td className="px-2 py-1.5 text-sm text-muted-foreground">{sub.unit}</td>
                <td className="px-2 py-1.5 text-sm text-muted-foreground">
                  <span className="text-xs mr-1">{sub.cost_currency}</span>{sub.cost_rate}
                </td>
                <td colSpan={2} />
                <td className="px-2 py-1.5 text-right text-sm tabular-nums text-muted-foreground">
                  {fmtSGD(sub.computed?.line_total_sgd)}
                </td>
                <td />
                <td className="px-2 py-1.5 text-center">
                  <Button variant="ghost" size="icon" className="h-6 w-6"
                    onClick={() => onDeleteLineItem(sub.id)} title="Remove component">
                    <Trash2 className="h-3 w-3 text-destructive" />
                  </Button>
                </td>
              </tr>
            ))}
            {/* Add component button row */}
            <tr className="border-b">
              <td colSpan={11} className="px-4 py-1.5">
                <Button variant="ghost" size="sm" className="h-7 text-xs gap-1"
                  onClick={() => onAddBundleComponent(item.id)}>
                  <Plus className="h-3.5 w-3.5" />
                  Add component to bundle
                </Button>
              </td>
            </tr>
          </>
        )}
      </>
    );
  };

  // == Render =================================================================

  return (
    <div className="rounded-lg border bg-card shadow-sm overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50 text-muted-foreground text-xs">
            <th className="px-2 py-2 w-8">
              <input type="checkbox" className="h-4 w-4"
                checked={allSelected} onChange={handleSelectAll} />
            </th>
            <th className="px-2 py-2 text-left font-medium">Description</th>
            <th className="px-2 py-2 text-right font-medium w-16">Qty</th>
            <th className="px-2 py-2 text-left font-medium w-20">Unit</th>
            <th className="px-2 py-2 text-right font-medium">Unit Cost</th>
            <th className="px-2 py-2 text-right font-medium w-20">Markup</th>
            <th className="px-2 py-2 text-right font-medium w-24">Contingency</th>
            <th className="px-2 py-2 text-right font-medium w-28">Sell Rate (SGD)</th>
            <th className="px-2 py-2 text-right font-medium w-28">Line Total (SGD)</th>
            <th className="px-2 py-2 text-center font-medium w-10" title="Visible on quote">
              {'\u{1F441}'}
            </th>
            <th className="px-2 py-2 w-10" />
          </tr>
        </thead>
        {topLevelItems.length === 0 ? (
          <tbody>
            <tr>
              <td colSpan={11} className="h-24 text-center text-muted-foreground">
                No line items yet. Click &quot;Add Line Item&quot; to start.
              </td>
            </tr>
          </tbody>
        ) : (
          SECTIONS.map((section) => {
            const items = bySection[section];
            if (items.length === 0) return null;
            const subtotal = sectionSubtotal(items);
            return (
              <tbody key={section}>
                <tr className="bg-muted/30">
                  <td colSpan={11}
                    className="px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {section}
                  </td>
                </tr>
                {items.map((item) =>
                  item.is_bundle_parent ? (
                    <BundleParentRow key={item.id} item={item} />
                  ) : (
                    <EditableRow
                      key={item.id}
                      item={item}
                      scenarioId={scenarioId}
                      onDelete={onDeleteLineItem}
                      selected={selectedIds.has(item.id)}
                      onSelect={handleSelect}
                    />
                  )
                )}
                <tr className="bg-muted/10 border-t">
                  <td colSpan={8}
                    className="px-3 py-1 text-xs text-right text-muted-foreground italic">
                    {section} subtotal
                  </td>
                  <td className="px-2 py-1 text-right text-sm font-semibold tabular-nums">
                    {fmtSGD(subtotal)}
                  </td>
                  <td colSpan={2} />
                </tr>
              </tbody>
            );
          })
        )}
      </table>
      <div className="border-t px-4 py-3 flex justify-center">
        <Button variant="outline" size="sm" onClick={() => onAddLineItem(scenarioId)}>
          <PlusCircle className="mr-2 h-4 w-4" />
          Add Line Item
        </Button>
      </div>
    </div>
  );
}
