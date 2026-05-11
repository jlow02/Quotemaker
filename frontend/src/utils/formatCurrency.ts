/**
 * @purpose Formats a numeric amount into a currency string based on the provided currency code.
 * @param {number} amount - The numeric value to format.
 * @param {string} currency - The ISO 4217 currency code (e.g., 'USD', 'EUR', 'GBP').
 * @returns {string} The formatted currency string.
 * @owner [Gemini]
 */
export function formatCurrency(amount: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}