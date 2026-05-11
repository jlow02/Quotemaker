import { useMemo } from 'react';

/**
 * @purpose Defines the shape of a single line item in the costing scenario.
 * @owner [Gemini]
 */
export interface LineItem {
  id: string;
  quantity: number;
  unit_cost: number;
  fx_currency: string | null;
  bundle_override_price: number | null;
}

/**
 * @purpose Defines the structure for foreign exchange rates, mapping currency codes to their rates.
 * @owner [Gemini]
 */
export interface FxRates {
  [currencyCode: string]: number;
}

/**
 * @purpose Defines the structure of the computed costing values returned by the hook.
 * @owner [Gemini]
 */
export interface CostingCalculations {
  subtotal: number;
  fxAdjustedSubtotal: number;
  withContingency: number;
  withMargin: number;
  grandTotal: number;
}

/**
 * @purpose A hook that computes derived costing values from a scenario's line items,
 * applying foreign exchange rates, contingency, and margin percentages.
 * All computations are performed in-memory and memoized for performance.
 * @param {LineItem[]} lineItems An array of line items for the costing scenario.
 * @param {FxRates} fxRates A record of foreign exchange rates, e.g., { "EUR": 1.15 }.
 * @param {number} marginPct The margin percentage to apply (e.g., 0.10 for 10%).
 * @param {number} contingencyPct The contingency percentage to apply (e.g., 0.05 for 5%).
 * @returns {CostingCalculations} An object containing the computed costing values.
 * @owner [Gemini]
 */
export function useCostingCalculations(
  lineItems: LineItem[],
  fxRates: FxRates,
  marginPct: number,
  contingencyPct: number
): CostingCalculations {
  const calculations = useMemo<CostingCalculations>(() => {
    let currentSubtotal: number = 0; // Sum of base costs before any FX adjustment
    let currentFxAdjustedSubtotal: number = 0; // Sum of costs after FX adjustment

    if (!lineItems || lineItems.length === 0) {
      return {
        subtotal: 0,
        fxAdjustedSubtotal: 0,
        withContingency: 0,
        withMargin: 0,
        grandTotal: 0,
      };
    }

    for (const item of lineItems) {
      // Determine the base cost for the line item
      const baseItemCost: number =
        item.bundle_override_price !== null && item.bundle_override_price !== undefined
          ? item.bundle_override_price
          : item.quantity * item.unit_cost;

      currentSubtotal += baseItemCost;

      // Apply FX rate if currency is specified and available
      let adjustedItemCost: number = baseItemCost;
      if (item.fx_currency && fxRates[item.fx_currency]) {
        adjustedItemCost *= fxRates[item.fx_currency];
      }
      currentFxAdjustedSubtotal += adjustedItemCost;
    }

    const withContingency: number = currentFxAdjustedSubtotal * (1 + contingencyPct);
    const withMargin: number = withContingency * (1 + marginPct);
    const grandTotal: number = withMargin;

    return {
      subtotal: currentSubtotal,
      fxAdjustedSubtotal: currentFxAdjustedSubtotal,
      withContingency: withContingency,
      withMargin: withMargin,
      grandTotal: grandTotal,
    };
  }, [lineItems, fxRates, marginPct, contingencyPct]); // Re-compute only if dependencies change

  return calculations;
}