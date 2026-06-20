/**
 * FX Rates page.
 *
 * This page centralizes FX rate management for the application.
 *
 * Responsibilities:
 * - Display stored FX rates from the backend.
 * - Allow the user to select a quote/base currency.
 * - Trigger live FX rate updates.
 *
 * Portfolio and Watchlist consume FX data. They should not own the update
 * action. This keeps FX rates as shared market data.
 */

import { useEffect, useState } from "react";

import { fetchFXRates, updateFXRates } from "../api/bondsApi";
import { formatDecimal } from "../utils/formatters";

const QUOTE_CURRENCY_OPTIONS = ["EUR", "USD", "GBP"];
const DEFAULT_BASE_CURRENCIES = ["USD", "GBP", "CHF", "JPY", "CAD", "AUD"];

function FXRatesPage() {
  const [quoteCurrency, setQuoteCurrency] = useState("EUR");
  const [selectedBaseCurrencies, setSelectedBaseCurrencies] = useState(
    DEFAULT_BASE_CURRENCIES
  );
  const [fxRates, setFxRates] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    loadFXRates();
  }, [quoteCurrency]);

  async function loadFXRates() {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const data = await fetchFXRates({
        quote_currency: quoteCurrency,
      });

      const normalizedData = Array.isArray(data) ? data : data.results || [];
      setFxRates(normalizedData);
    } catch (error) {
      setErrorMessage("Δεν ήταν δυνατή η φόρτωση των ισοτιμιών.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleQuoteCurrencyChange(event) {
    const nextQuoteCurrency = event.target.value;

    setQuoteCurrency(nextQuoteCurrency);
    setMessage("");

    setSelectedBaseCurrencies(
      DEFAULT_BASE_CURRENCIES.filter(
        (currency) => currency !== nextQuoteCurrency
      )
    );
  }

  function handleBaseCurrencyToggle(currency) {
    setSelectedBaseCurrencies((previousCurrencies) => {
      if (previousCurrencies.includes(currency)) {
        return previousCurrencies.filter((item) => item !== currency);
      }

      return [...previousCurrencies, currency];
    });
  }

  async function handleUpdateFXRates() {
    setIsUpdating(true);
    setMessage("");
    setErrorMessage("");

    try {
      const baseCurrencies = selectedBaseCurrencies.filter(
        (currency) => currency !== quoteCurrency
      );

      const result = await updateFXRates({
        quote_currency: quoteCurrency,
        base_currencies: baseCurrencies,
      });

      const updatedCount = result.updated?.length || 0;
      const errorCount = result.errors?.length || 0;

      setMessage(
        `FX update completed. Updated: ${updatedCount}, Errors: ${errorCount}.`
      );

      if (errorCount > 0) {
        setErrorMessage(result.errors.join(" | "));
      }

      await loadFXRates();
    } catch (error) {
      setErrorMessage(
        "FX update failed. Έλεγξε το backend terminal ή το FX provider."
      );
    } finally {
      setIsUpdating(false);
    }
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <h1>FX Rates</h1>
        <p>
          Κεντρική διαχείριση ισοτιμιών. Το Portfolio και το Watchlist
          χρησιμοποιούν τις τελευταίες διαθέσιμες ισοτιμίες από εδώ.
        </p>
      </div>

      <div className="toolbar-card">
        <div className="fx-controls-grid">
          <label className="compact-select-label">
            Quote Currency
            <select value={quoteCurrency} onChange={handleQuoteCurrencyChange}>
              {QUOTE_CURRENCY_OPTIONS.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>
          </label>

          <div className="fx-checkbox-group">
            <span>Base Currencies</span>

            <div className="checkbox-grid">
              {DEFAULT_BASE_CURRENCIES.map((currency) => (
                <label key={currency} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedBaseCurrencies.includes(currency)}
                    disabled={currency === quoteCurrency}
                    onChange={() => handleBaseCurrencyToggle(currency)}
                  />
                  {currency}
                </label>
              ))}
            </div>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={handleUpdateFXRates}
            disabled={isUpdating || selectedBaseCurrencies.length === 0}
          >
            {isUpdating ? "Updating FX..." : "Update FX Rates"}
          </button>
        </div>

        <p className="muted-text">
          Παράδειγμα: USD/EUR = πόσα EUR αντιστοιχούν σε 1 USD.
        </p>
      </div>

      {message && <div className="info-box">{message}</div>}

      {errorMessage && <div className="warning-box">{errorMessage}</div>}

      <div className="table-card">
        <h2>Stored FX Rates</h2>

        {isLoading ? (
          <p className="loading-text">Loading FX rates...</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Pair</th>
                  <th>Rate Date</th>
                  <th>Rate</th>
                  <th>Source</th>
                  <th>Notes</th>
                  <th>Created At</th>
                </tr>
              </thead>

              <tbody>
                {fxRates.length === 0 ? (
                  <tr>
                    <td colSpan="6">
                      Δεν υπάρχουν ακόμα αποθηκευμένες ισοτιμίες.
                    </td>
                  </tr>
                ) : (
                  fxRates.map((rate) => (
                    <tr key={rate.id}>
                      <td>
                        <strong>
                          {rate.base_currency}/{rate.quote_currency}
                        </strong>
                      </td>
                      <td>{rate.rate_date}</td>
                      <td>{formatDecimal(rate.rate, 8)}</td>
                      <td>
                        <span className="status-pill">{rate.source}</span>
                      </td>
                      <td>{rate.notes || "-"}</td>
                      <td>{formatDateTime(rate.created_at)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export default FXRatesPage;