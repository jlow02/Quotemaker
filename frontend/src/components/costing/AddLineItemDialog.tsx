import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';

const SECTIONS = ['Hardware', 'Software', 'Professional Fees', 'Maintenance'] as const;
type Section = typeof SECTIONS[number];

interface AddLineItemDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: {
    section: string;
    description: string;
    qty: string;
    unit: string;
    cost_rate: string;
    cost_currency: string;
    markup_pct: string;
    contingency_pct: string;
  }) => void;
  isLoading: boolean;
}

const DEFAULT_FORM = {
  section: 'Hardware' as Section,
  description: '',
  qty: '1',
  unit: 'unit',
  cost_rate: '0',
  cost_currency: 'SGD',
  markup_pct: '0',
  contingency_pct: '0',
};

/**
 * @purpose Modal dialog for creating a new line item in a scenario.
 * @owner [Claude]
 */
export function AddLineItemDialog({ open, onClose, onSubmit, isLoading }: AddLineItemDialogProps) {
  const [form, setForm] = useState({ ...DEFAULT_FORM });

  const handleChange = (field: keyof typeof form, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.description.trim()) return;
    // Backend stores markup_pct and contingency_pct as decimals (0.10 = 10%)
    // The form collects them as percentages (10 = 10%), so divide by 100
    onSubmit({
      ...form,
      markup_pct: String(Number(form.markup_pct) / 100),
      contingency_pct: String(Number(form.contingency_pct) / 100),
    });
  };

  const handleClose = () => {
    setForm({ ...DEFAULT_FORM });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) handleClose(); }}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Line Item</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          {/* Section */}
          <div className="space-y-1">
            <Label htmlFor="section">Section</Label>
            <select
              id="section"
              value={form.section}
              onChange={(e) => handleChange('section', e.target.value)}
              className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {SECTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div className="space-y-1">
            <Label htmlFor="description">Description *</Label>
            <Input
              id="description"
              value={form.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="e.g. 4K IP Camera"
              required
            />
          </div>

          {/* Qty + Unit */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="qty">Qty</Label>
              <Input
                id="qty"
                type="number"
                min="0"
                step="any"
                value={form.qty}
                onChange={(e) => handleChange('qty', e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="unit">Unit</Label>
              <Input
                id="unit"
                value={form.unit}
                onChange={(e) => handleChange('unit', e.target.value)}
                placeholder="unit"
              />
            </div>
          </div>

          {/* Cost Rate + Currency */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="cost_rate">Unit Cost</Label>
              <Input
                id="cost_rate"
                type="number"
                min="0"
                step="any"
                value={form.cost_rate}
                onChange={(e) => handleChange('cost_rate', e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="cost_currency">Currency</Label>
              <select
                id="cost_currency"
                value={form.cost_currency}
                onChange={(e) => handleChange('cost_currency', e.target.value)}
                className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {['SGD', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'AUD', 'MYR'].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Markup + Contingency */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="markup_pct">Markup %</Label>
              <Input
                id="markup_pct"
                type="number"
                min="0"
                step="any"
                value={form.markup_pct}
                onChange={(e) => handleChange('markup_pct', e.target.value)}
                placeholder="0"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="contingency_pct">Contingency %</Label>
              <Input
                id="contingency_pct"
                type="number"
                min="0"
                step="any"
                value={form.contingency_pct}
                onChange={(e) => handleChange('contingency_pct', e.target.value)}
                placeholder="0"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={handleClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !form.description.trim()}>
              {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Add Item
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
