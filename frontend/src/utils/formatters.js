/**
 * Display formatting helpers.
 *
 * These functions keep number formatting consistent across the frontend.
 * They are intentionally simple and safe for empty/null API values.
 */

/**
 * Format a decimal-like value.
 *
 * @param {string|number|null|undefined} value - API value.
 * @param {number} digits - Number of decimal places.
 * @returns {string} Formatted value or "-".
 */
export function formatDecimal(value, digits = 2) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return "-";
  }

  return numericValue.toFixed(digits);
}

/**
 * Format a percentage value.
 *
 * The backend stores most yield/rate values already as percentages, for
 * example 4.35 means 4.35%.
 *
 * @param {string|number|null|undefined} value - API value.
 * @param {number} digits - Number of decimal places.
 * @returns {string} Formatted percentage or "-".
 */
export function formatPercent(value, digits = 2) {
  const formattedValue = formatDecimal(value, digits);

  if (formattedValue === "-") {
    return "-";
  }

  return `${formattedValue}%`;
}

/**
 * Format a ratio as percentage.
 *
 * Example:
 *   0.25 becomes 25.00%
 *
 * @param {string|number|null|undefined} value - Ratio value.
 * @param {number} digits - Number of decimal places.
 * @returns {string} Formatted percentage or "-".
 */
export function formatRatioAsPercent(value, digits = 2) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return "-";
  }

  return `${(numericValue * 100).toFixed(digits)}%`;
}

/**
 * Format a money-like value.
 *
 * @param {string|number|null|undefined} value - API value.
 * @param {string} currency - Currency code.
 * @param {number} digits - Number of decimal places.
 * @returns {string} Formatted money value or "-".
 */
export function formatMoney(value, currency = "", digits = 2) {
  const formattedValue = formatDecimal(value, digits);

  if (formattedValue === "-") {
    return "-";
  }

  if (!currency) {
    return formattedValue;
  }

  return `${formattedValue} ${currency}`;
}