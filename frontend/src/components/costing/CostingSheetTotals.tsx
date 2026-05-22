import React from 'react';
import { Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface CostingSheetTotalsProps {
  scenarioId: string;
  discountType: string | null;
  discountValue: number | null;
  showGst: boolean;
  totals: {
    subtotal_sgd: string | number | null;
    discount_amount_sgd: string | number | null;
    total_before_gst_sgd: string | number | null;
    gst_amount_sgd: string | number | null;
    grand_total_sgd: string | number | null;
  } | null | undefined;
  isSaving: boolean;
  onDiscountTypeChange: (value: string | null) => void;
  onDiscountValueChange: (value: number | null) => void;
  onGstToggle: (value: boolean) => void;
}

const formatSGD = (val: string | number | null | undefined): string => {
  if (val == null) return '—';
  const n = Number(val);
  return isNaN(n) ? '—' : new Intl.NumberFormat('en-SG', {
    style: 'currency',
    currency: 'SGD',
    minimumFractionDigits: 2,
  }).format(n);
};

/**
 * @purpose Renders discount/GST controls and the pricing summary panel for a scenario.
 * Receives server-computed totals from the backend -- does NOT perform any client-side math.
 * @inputs discountType, discountValue, showGst, totals, isSaving, and change handlers
 * @outputs JSX with discount controls, GST toggle, and read-only pricing summary
 * @owner [DeepSeek -- reviewed by Claude]
 */
const CostingSheetTotals: React.FC<CostingSheetTotalsProps> = ({
  discountType,
  discountValue,
  showGst,
  totals,
  isSaving,
  onDiscountTypeChange,
  onDiscountValueChange,
  onGstToggle,
}) => {
  const discountAmount =
    totals?.discount_amount_sgd != null ? Number(totals.discount_amount_sgd) : 0;

  return (
    <div className="space-y-4 mt-4 p-4 bg-white border border-gray-100 rounded-lg shadow-sm">
      {/* Discount controls row */}
      <div className="flex items-center gap-4">
        <Label className="w-36 text-sm font-medium shrink-0">Discount</Label>
        <div className="flex items-center gap-2">
          <select
            className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring w-44"
            value={discountType ?? '__none__'}
            onChange={(e) =>
              onDiscountTypeChange(e.target.value === '__none__' ? null : e.target.value)
            }
          >
            <option value="__none__">None</option>
            <option value="percentage">Percentage (%)</option>
            <option value="flat">Flat (SGD)</option>
          </select>
          <div className="flex items-center gap-1">
            <Input
              type="number"
              min={0}
              step={0.01}
              placeholder="0.00"
              className="w-28"
              disabled={discountType === null}
              value={discountValue ?? ''}
              onChange={(e) => {
                const raw = e.target.value;
                if (raw === '') {
                  onDiscountValueChange(null);
                } else {
                  const parsed = parseFloat(raw);
                  if (!isNaN(parsed)) onDiscountValueChange(parsed);
                }
              }}
            />
            {discountType === 'percentage' && <span className="text-sm text-gray-500">%</span>}
            {discountType === 'flat' && <span className="text-sm text-gray-500">SGD</span>}
          </div>
        </div>
      </div>

      {/* GST toggle row */}
      <div className="flex items-center gap-4">
        <Label className="w-36 text-sm font-medium shrink-0">Include GST (9%)</Label>
        <button
          type="button"
          role="switch"
          aria-checked={showGst}
          onClick={() => onGstToggle(!showGst)}
          className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${showGst ? 'bg-blue-600' : 'bg-gray-300'}`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${showGst ? 'translate-x-4' : 'translate-x-0.5'}`}
          />
        </button>
      </div>

      {/* Pricing summary panel */}
      <div className="relative bg-gray-50 rounded-lg p-4 border border-gray-200">
        {isSaving && (
          <div className="absolute top-2 right-2 flex items-center gap-1 text-xs text-gray-500">
            <Loader2 className="h-3 w-3 animate-spin" />
            Saving...
          </div>
        )}
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Subtotal</span>
            <span>{formatSGD(totals?.subtotal_sgd)}</span>
          </div>
          {discountType !== null && discountAmount > 0 && (
            <div className="flex justify-between text-red-600">
              <span>Discount</span>
              <span>- {formatSGD(totals?.discount_amount_sgd)}</span>
            </div>
          )}
          {showGst && (
            <div className="flex justify-between text-gray-600">
              <span>Total before GST</span>
              <span>{formatSGD(totals?.total_before_gst_sgd)}</span>
            </div>
          )}
          {showGst && (
            <div className="flex justify-between text-gray-600">
              <span>GST (9%)</span>
              <span>{formatSGD(totals?.gst_amount_sgd)}</span>
            </div>
          )}
          <div className="flex justify-between text-base font-bold pt-2 border-t border-gray-300">
            <span>TOTAL (SGD)</span>
            <span>{formatSGD(totals?.grand_total_sgd)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CostingSheetTotals;
