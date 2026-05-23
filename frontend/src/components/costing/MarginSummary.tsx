// frontend/src/components/costing/MarginSummary.tsx

import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { LineItem } from '../../api/services';

/**
 * Props for the MarginSummary component.
 */
interface MarginSummaryProps {
  /** Array of line items from the costing sheet */
  lineItems: LineItem[];
}

/**
 * Internal margin summary panel for costing sheets.
 * Displays total cost, total selling, gross profit, and margin percentage,
 * along with a section breakdown. This component is for internal use only
 * and should never be rendered on exported quotes.
 *
 * @param {MarginSummaryProps} props - The component props
 * @returns {JSX.Element} The rendered margin summary panel
 */
const MarginSummary: React.FC<MarginSummaryProps> = ({ lineItems }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  /**
   * Formats a number as SGD currency string.
   * @param {number} value - The value to format
   * @returns {string} Formatted currency string
   */
  const formatSGD = (value: number): string => {
    return new Intl.NumberFormat('en-SG', {
      style: 'currency',
      currency: 'SGD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  /**
   * Formats a decimal as a percentage string.
   * @param {number} value - The decimal value (e.g., 0.1234 for 12.34%)
   * @returns {string} Formatted percentage string
   */
  const formatPercent = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };

  /**
   * Computes the cost for a single line item.
   * For bundle parents with sub-components, cost is the sum of sub-component costs.
   * Otherwise, cost is computed from the item's own cost_sgd * qty.
   *
   * @param {LineItem} item - The line item to compute cost for
   * @returns {number} The computed cost
   */
  const computeItemCost = (item: LineItem): number => {
    if (item.is_bundle_parent && item.sub_components && item.sub_components.length > 0) {
      // Sum costs of visible sub-components
      return item.sub_components
        .filter((sub) => sub.is_visible !== false)
        .reduce((sum, sub) => {
          return sum + (Number(sub.computed?.cost_sgd ?? 0) * Number(sub.qty ?? 1));
        }, 0);
    }
    // Default: use item's own cost_sgd * qty
    return Number(item.computed?.cost_sgd ?? 0) * Number(item.qty ?? 1);
  };

  /**
   * Computes the sell total for a single line item.
   * Uses the item's line_total_sgd directly.
   *
   * @param {LineItem} item - The line item to compute sell total for
   * @returns {number} The computed sell total
   */
  const computeItemSellTotal = (item: LineItem): number => {
    return Number(item.computed?.line_total_sgd ?? 0);
  };

  /**
   * Memoized computation of margin data from visible top-level line items.
   * Filters for visible items with no parent, then computes aggregates
   * and section breakdowns.
   */
  const marginData = useMemo(() => {
    // Filter visible top-level items
    const visibleTopLevelItems = lineItems.filter(
      (item) =>
        item.is_visible !== false &&
        (item.parent_line_item_id === null || item.parent_line_item_id === undefined)
    );

    // Compute per-item costs and sell totals
    const itemData = visibleTopLevelItems.map((item) => ({
      section: item.section ?? 'Uncategorized',
      cost: computeItemCost(item),
      sellTotal: computeItemSellTotal(item),
    }));

    // Aggregate totals
    const totalCost = itemData.reduce((sum, item) => sum + item.cost, 0);
    const totalSelling = itemData.reduce((sum, item) => sum + item.sellTotal, 0);
    const grossProfit = totalSelling - totalCost;
    const grossMarginPct = totalSelling > 0 ? grossProfit / totalSelling : 0;

    // Section breakdown
    const sectionMap = new Map<string, { cost: number; sellTotal: number }>();
    itemData.forEach((item) => {
      const existing = sectionMap.get(item.section) ?? { cost: 0, sellTotal: 0 };
      existing.cost += item.cost;
      existing.sellTotal += item.sellTotal;
      sectionMap.set(item.section, existing);
    });

    // Convert section map to array and compute per-section metrics
    const sectionBreakdown = Array.from(sectionMap.entries())
      .map(([section, data]) => ({
        section,
        cost: data.cost,
        sellTotal: data.sellTotal,
        gp: data.sellTotal - data.cost,
        marginPct: data.sellTotal > 0 ? (data.sellTotal - data.cost) / data.sellTotal : 0,
      }))
      .sort((a, b) => a.section.localeCompare(b.section));

    return {
      totalCost,
      totalSelling,
      grossProfit,
      grossMarginPct,
      sectionBreakdown,
    };
  }, [lineItems]);

  return (
    <div className="bg-gray-50 border-l-4 border-gray-400 rounded-md shadow-sm mb-6">
      {/* Collapsible Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-left focus:outline-none focus:ring-2 focus:ring-gray-300 rounded-t-md"
        aria-expanded={isExpanded}
        aria-controls="margin-summary-content"
      >
        <h3 className="text-sm font-semibold text-gray-700">
          Margin Summary (Internal)
        </h3>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        )}
      </button>

      {/* Collapsible Content */}
      {isExpanded && (
        <div id="margin-summary-content" className="px-4 pb-4 space-y-4">
          {/* 4-Column Summary */}
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div className="bg-white rounded p-3 border border-gray-200">
              <p className="text-xs text-gray-500 font-medium mb-1">Total Cost</p>
              <p className="text-base font-semibold text-gray-800">
                {formatSGD(marginData.totalCost)}
              </p>
            </div>
            <div className="bg-white rounded p-3 border border-gray-200">
              <p className="text-xs text-gray-500 font-medium mb-1">Total Selling</p>
              <p className="text-base font-semibold text-gray-800">
                {formatSGD(marginData.totalSelling)}
              </p>
            </div>
            <div className="bg-white rounded p-3 border border-gray-200">
              <p className="text-xs text-gray-500 font-medium mb-1">Gross Profit</p>
              <p className="text-base font-semibold text-gray-800">
                {formatSGD(marginData.grossProfit)}
              </p>
            </div>
            <div className="bg-white rounded p-3 border border-gray-200">
              <p className="text-xs text-gray-500 font-medium mb-1">Margin %</p>
              <p className="text-base font-semibold text-gray-800">
                {formatPercent(marginData.grossMarginPct)}
              </p>
            </div>
          </div>

          {/* Section Breakdown Table */}
          {marginData.sectionBreakdown.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-300">
                    <th className="text-left py-2 px-3 font-medium text-gray-600">Section</th>
                    <th className="text-right py-2 px-3 font-medium text-gray-600">Cost SGD</th>
                    <th className="text-right py-2 px-3 font-medium text-gray-600">Selling SGD</th>
                    <th className="text-right py-2 px-3 font-medium text-gray-600">GP</th>
                    <th className="text-right py-2 px-3 font-medium text-gray-600">Margin %</th>
                  </tr>
                </thead>
                <tbody>
                  {marginData.sectionBreakdown.map((section) => (
                    <tr key={section.section} className="border-b border-gray-200 hover:bg-gray-100">
                      <td className="py-2 px-3 text-gray-700">
                        {section.section === 'Maintenance'
                          ? 'Maintenance / Annual Support'
                          : section.section}
                      </td>
                      <td className="py-2 px-3 text-right text-gray-700">
                        {formatSGD(section.cost)}
                      </td>
                      <td className="py-2 px-3 text-right text-gray-700">
                        {formatSGD(section.sellTotal)}
                      </td>
                      <td className="py-2 px-3 text-right text-gray-700">
                        {formatSGD(section.gp)}
                      </td>
                      <td className="py-2 px-3 text-right text-gray-700">
                        {formatPercent(section.marginPct)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Internal Use Caption */}
          <p className="text-xs text-gray-400 italic">
            Internal only — not shown on quotes
          </p>
        </div>
      )}
    </div>
  );
};

export default MarginSummary;
