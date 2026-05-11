import { useState, useEffect, useCallback, useMemo, ChangeEvent } from 'react';
import { useMutation, QueryClient } from '@tanstack/react-query';
import { Trash2 } from 'lucide-react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { TableRow, TableCell } from '../ui/table';
import { useDebounce } from '../../hooks/useDebounce';
import type { LineItem } from '../../api/services';
import { updateLineItem, deleteLineItem, setBundleOverride } from '../../api/services';

/**
 * @purpose Defines the properties for the LineItemRow component.
 * @owner [Gemini]
 */
interface LineItemRowProps {
  lineItem: LineItem;
  scenarioId: string;
  queryClient: QueryClient;
}

/**
 * @purpose Displays a single line item row within a costing sheet table, allowing inline editing, debounced autosave, bundle override, and deletion.
 * @param {LineItemRowProps} props - The properties for the component.
 * @returns {JSX.Element} A table row component for a line item.
 * @owner [Gemini]
 */
export function LineItemRow({ lineItem, scenarioId, queryClient }: LineItemRowProps): JSX.Element {
  const [quantity, setQuantity] = useState(Number(lineItem.qty));
  const [unitCost, setUnitCost] = useState(Number(lineItem.cost_rate));
  const [bundleOverridePrice, setBundleOverridePrice] = useState<number | null>(lineItem.bundle_override_price ? Number(lineItem.bundle_override_price) : null);

  const debouncedQuantity = useDebounce(quantity, 800);
  const debouncedUnitCost = useDebounce(unitCost, 800);
  const debouncedBundleOverridePrice = useDebounce(bundleOverridePrice, 800);

  const updateItemMutation = useMutation({
    mutationFn: (args: { lineItemId: string; data: Parameters<typeof updateLineItem>[1] }) => updateLineItem(args.lineItemId, args.data),
    onSuccess: (updatedItem) => {
      queryClient.setQueryData<LineItem[]>(['scenario', scenarioId, 'lineItems'], (oldData) =>
        oldData?.map((item) => (item.id === updatedItem.id ? updatedItem : item)) || []
      );
    },
  });

  const setBundleOverrideMutation = useMutation({
    mutationFn: (args: { lineItemId: string; data: Parameters<typeof setBundleOverride>[1] }) => setBundleOverride(args.lineItemId, args.data),
    onSuccess: (updatedItem) => {
      queryClient.setQueryData<LineItem[]>(['scenario', scenarioId, 'lineItems'], (oldData) =>
        oldData?.map((item) => (item.id === updatedItem.id ? updatedItem : item)) || []
      );
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (lineItemId: string) => deleteLineItem(lineItemId),
    onSuccess: (_, variables) => {
      queryClient.setQueryData<LineItem[]>(['scenario', scenarioId, 'lineItems'], (oldData) =>
        oldData?.filter((item) => item.id !== variables) || []
      );
    },
  });

  useEffect(() => {
    if (debouncedQuantity !== Number(lineItem.qty)) {
      updateItemMutation.mutate({ lineItemId: lineItem.id, data: { qty: String(debouncedQuantity), cost_rate: String(debouncedUnitCost) } });
    }
  }, [debouncedQuantity, lineItem.qty, lineItem.id, scenarioId, updateItemMutation]);

  useEffect(() => {
    if (debouncedUnitCost !== Number(lineItem.cost_rate)) {
      updateItemMutation.mutate({ lineItemId: lineItem.id, data: { qty: String(debouncedQuantity), cost_rate: String(debouncedUnitCost) } });
    }
  }, [debouncedUnitCost, lineItem.cost_rate, lineItem.id, scenarioId, updateItemMutation]);

  useEffect(() => {
    if (debouncedBundleOverridePrice !== (lineItem.bundle_override_price ? Number(lineItem.bundle_override_price) : null)) {
      setBundleOverrideMutation.mutate({ lineItemId: lineItem.id, data: { bundle_override_price: debouncedBundleOverridePrice !== null ? String(debouncedBundleOverridePrice) : null } });
    }
  }, [debouncedBundleOverridePrice, lineItem.bundle_override_price, lineItem.id, scenarioId, setBundleOverrideMutation]);

  const handleQuantityChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    setQuantity(isNaN(value) ? 0 : value);
  }, []);

  const handleUnitCostChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    setUnitCost(isNaN(value) ? 0 : value);
  }, []);

  const handleBundleOverridePriceChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    setBundleOverridePrice(isNaN(value) ? null : value);
  }, []);

  const handleDelete = useCallback(() => {
    deleteItemMutation.mutate(lineItem.id);
  }, [deleteItemMutation, lineItem.id, scenarioId]);

  const subtotal = useMemo(() => {
    if (lineItem.is_bundle && bundleOverridePrice !== null) {
      return bundleOverridePrice;
    }
    return quantity * unitCost;
  }, [quantity, unitCost, lineItem.is_bundle, bundleOverridePrice]);

  return (
    <TableRow>
      <TableCell className="font-medium">{lineItem.description}</TableCell>
      <TableCell className="w-[100px]">
        <Input type="number" value={quantity} onChange={handleQuantityChange} className="text-right" />
      </TableCell>
      <TableCell className="w-[120px]">
        <Input type="number" value={unitCost} onChange={handleUnitCostChange} step="0.01" className="text-right" />
      </TableCell>
      <TableCell className="w-[150px]">
        {lineItem.is_bundle ? (
          <Input
            type="number"
            value={bundleOverridePrice ?? ''}
            onChange={handleBundleOverridePriceChange}
            step="0.01"
            placeholder="Override price"
            className="text-right"
          />
        ) : (
          <span className="text-muted-foreground">-</span>
        )}
      </TableCell>
      <TableCell className="text-right font-semibold">
        {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(subtotal)}
      </TableCell>
      <TableCell className="w-[50px] text-right">
        <Button variant="ghost" size="icon" onClick={handleDelete} disabled={deleteItemMutation.isPending}>
          <Trash2 className="h-4 w-4 text-red-500" />
        </Button>
      </TableCell>
    </TableRow>
  );
}