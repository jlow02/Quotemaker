/**
 * @purpose Calculates the total cost of a bundle of components.
 * @param {Array<{quantity: number, unit_cost: number}>} components - An array of component objects, each with a quantity and unit_cost.
 * @returns {number} The total calculated cost for all components in the bundle.
 * @owner [Gemini]
 */
export function calcBundleTotal(components: Array<{ quantity: number; unit_cost: number }>): number {
  return components.reduce((total, component) => {
    return total + (component.quantity * component.unit_cost);
  }, 0);
}