/**
 * Add position page.
 *
 * This page allows the user to:
 * - select an existing bond or create a new bond
 * - enter manual market data
 * - add the bond to Portfolio or Watchlist
 *
 * The backend automatically recalculates analysis after the UserBond and
 * market data records are saved.
 */

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { createBond, createMarketData, fetchBonds } from "../api/bondsApi";
import {
  createPortfolioItem,
  createWatchlistItem,
} from "../api/portfolioApi";

const HOLDING_TYPES = {
  PORTFOLIO: "PORTFOLIO",
  WATCHLIST: "WATCHLIST",
};

const BOND_TYPE_OPTIONS = [
  { value: "GOVERNMENT", label: "Government Bond" },
  { value: "CORPORATE", label: "Corporate Bond" },
  { value: "TREASURY", label: "Treasury" },
  { value: "MUNICIPAL", label: "Municipal Bond" },
  { value: "OTHER", label: "Other" },
];

const SENIORITY_OPTIONS = [
  { value: "SENIOR_SECURED", label: "Senior Secured" },
  { value: "SENIOR_UNSECURED", label: "Senior Unsecured" },
  { value: "SUBORDINATED", label: "Subordinated" },
  { value: "JUNIOR", label: "Junior" },
  { value: "OTHER", label: "Other" },
];

const LIQUIDITY_OPTIONS = [
  { value: "HIGH", label: "High" },
  { value: "MEDIUM", label: "Medium" },
  { value: "LOW", label: "Low" },
];

function AddPositionPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const requestedType = searchParams.get("type");
  const initialHoldingType =
    requestedType === HOLDING_TYPES.PORTFOLIO
      ? HOLDING_TYPES.PORTFOLIO
      : HOLDING_TYPES.WATCHLIST;

  const [bondMode, setBondMode] = useState("existing");
  const [holdingType, setHoldingType] = useState(initialHoldingType);
  const [availableBonds, setAvailableBonds] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [existingBondForm, setExistingBondForm] = useState({
    search: "",
    bond: "",
  });

  const [bondForm, setBondForm] = useState({
    name: "",
    isin: "",
    issuer: "",
    bond_type: "GOVERNMENT",
    currency: "EUR",
    seniority: "SENIOR_UNSECURED",
    is_callable: false,
    market_liquidity: "MEDIUM",
    credit_rating: "",
    face_value: "100.0000",
    annual_coupon_rate: "0.0000",
    coupon_frequency: "1",
    maturity_date: "",
  });

  const [marketDataForm, setMarketDataForm] = useState({
    quote_date: new Date().toISOString().slice(0, 10),
    market_price: "",
    market_required_return: "",
    ytm: "",
    bid_price: "",
    ask_price: "",
    source: "manual",
    is_manual: true,
    notes: "",
  });

  const [positionForm, setPositionForm] = useState({
    quantity: holdingType === HOLDING_TYPES.PORTFOLIO ? "1" : "0",
    purchase_price: "",
    base_currency: "EUR",
    reinvest_coupons: false,
    trading_fees_percent: "0.0000",
    coupon_tax_percent: "0.0000",
    expected_yield_change: "0.00000",
    valuation_threshold_percent: "2.0000",
    evaluation_basis: "MARKET_DATA",
    target_required_return: "",
    notes: "",
    is_active: true,
  });

  useEffect(() => {
    async function loadBonds() {
      try {
        const bonds = await fetchBonds(existingBondForm.search);
        setAvailableBonds(bonds);
      } catch (error) {
        setErrorMessage("Δεν ήταν δυνατή η φόρτωση των ομολόγων.");
      }
    }

    loadBonds();
  }, [existingBondForm.search]);

  function handleBondModeChange(event) {
    setBondMode(event.target.value);
    setErrorMessage("");
    setSuccessMessage("");
  }

  function handleHoldingTypeChange(event) {
    const newHoldingType = event.target.value;
    setHoldingType(newHoldingType);

    setPositionForm((previousData) => ({
      ...previousData,
      quantity:
        newHoldingType === HOLDING_TYPES.PORTFOLIO
          ? previousData.quantity || "1"
          : "0",
      purchase_price:
        newHoldingType === HOLDING_TYPES.PORTFOLIO
          ? previousData.purchase_price
          : "",
    }));
  }

  function handleExistingBondChange(event) {
    const { name, value } = event.target;

    setExistingBondForm((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  }

  function handleBondFormChange(event) {
    const { name, type, checked, value } = event.target;

    setBondForm((previousData) => ({
      ...previousData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleMarketDataChange(event) {
    const { name, type, checked, value } = event.target;

    setMarketDataForm((previousData) => ({
      ...previousData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handlePositionChange(event) {
    const { name, type, checked, value } = event.target;

    setPositionForm((previousData) => ({
      ...previousData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function cleanOptionalValue(value) {
    if (value === "" || value === null || value === undefined) {
      return null;
    }

    return value;
  }

  function buildBondPayload() {
    return {
      ...bondForm,
      face_value: bondForm.face_value,
      annual_coupon_rate: bondForm.annual_coupon_rate,
      coupon_frequency: Number(bondForm.coupon_frequency),
    };
  }

  function buildMarketDataPayload(bondId) {
    return {
      bond: bondId,
      quote_date: marketDataForm.quote_date,
      market_price: marketDataForm.market_price,
      market_required_return: cleanOptionalValue(
        marketDataForm.market_required_return
      ),
      ytm: cleanOptionalValue(marketDataForm.ytm),
      bid_price: cleanOptionalValue(marketDataForm.bid_price),
      ask_price: cleanOptionalValue(marketDataForm.ask_price),
      source: marketDataForm.source || "manual",
      is_manual: marketDataForm.is_manual,
      notes: marketDataForm.notes,
    };
  }

  function buildPositionPayload(bondId) {
    const isPortfolio = holdingType === HOLDING_TYPES.PORTFOLIO;

    return {
      bond: bondId,
      quantity: isPortfolio ? Number(positionForm.quantity) : 0,
      purchase_price: isPortfolio
        ? cleanOptionalValue(positionForm.purchase_price)
        : null,
      base_currency: positionForm.base_currency,
      reinvest_coupons: positionForm.reinvest_coupons,
      trading_fees_percent: positionForm.trading_fees_percent,
      coupon_tax_percent: positionForm.coupon_tax_percent,
      expected_yield_change: positionForm.expected_yield_change,
      valuation_threshold_percent: positionForm.valuation_threshold_percent,
      evaluation_basis: positionForm.evaluation_basis,
      target_required_return: cleanOptionalValue(
        positionForm.target_required_return
      ),
      notes: positionForm.notes,
      is_active: true,
    };
  }

  async function resolveBondId() {
    if (bondMode === "existing") {
      if (!existingBondForm.bond) {
        throw new Error("Πρέπει να επιλέξεις υπάρχον ομόλογο.");
      }

      return existingBondForm.bond;
    }

    const createdBond = await createBond(buildBondPayload());

    return createdBond.id;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setErrorMessage("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      const bondId = await resolveBondId();

      await createMarketData(buildMarketDataPayload(bondId));

      const payload = buildPositionPayload(bondId);
      const createdPosition =
        holdingType === HOLDING_TYPES.PORTFOLIO
          ? await createPortfolioItem(payload)
          : await createWatchlistItem(payload);

      setSuccessMessage("Το ομόλογο προστέθηκε με επιτυχία.");
      navigate(`/positions/${createdPosition.id}`);
    } catch (error) {
      const apiError = error.response?.data;

      if (typeof apiError === "string") {
        setErrorMessage(apiError);
      } else if (apiError) {
        setErrorMessage(JSON.stringify(apiError));
      } else {
        setErrorMessage(error.message || "Η αποθήκευση απέτυχε.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="page-section">
      <div className="page-header">
        <h1>Add Bond Position</h1>
        <p>
          Πρόσθεσε ομόλογο σε Portfolio ή Watchlist με manual market data.
        </p>
      </div>

      {errorMessage && <div className="error-box">{errorMessage}</div>}
      {successMessage && <div className="success-box">{successMessage}</div>}

      <form className="form-card" onSubmit={handleSubmit}>
        <section className="form-section">
          <h2>1. Section</h2>

          <div className="form-grid">
            <label>
              Add to
              <select value={holdingType} onChange={handleHoldingTypeChange}>
                <option value={HOLDING_TYPES.PORTFOLIO}>Portfolio</option>
                <option value={HOLDING_TYPES.WATCHLIST}>Watchlist</option>
              </select>
            </label>

            <label>
              Bond source
              <select value={bondMode} onChange={handleBondModeChange}>
                <option value="existing">Existing Bond</option>
                <option value="new">New Bond</option>
              </select>
            </label>
          </div>
        </section>

        {bondMode === "existing" ? (
          <section className="form-section">
            <h2>2. Select Existing Bond</h2>

            <div className="form-grid">
              <label>
                Search
                <input
                  name="search"
                  type="text"
                  value={existingBondForm.search}
                  onChange={handleExistingBondChange}
                  placeholder="Search by ISIN, name, or issuer"
                />
              </label>

              <label>
                Bond
                <select
                  name="bond"
                  value={existingBondForm.bond}
                  onChange={handleExistingBondChange}
                  required
                >
                  <option value="">Select bond</option>
                  {availableBonds.map((bond) => (
                    <option key={bond.id} value={bond.id}>
                      {bond.isin} — {bond.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </section>
        ) : (
          <section className="form-section">
            <h2>2. New Bond Details</h2>

            <div className="form-grid">
              <label>
                Bond Name
                <input
                  name="name"
                  type="text"
                  value={bondForm.name}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label>
                ISIN
                <input
                  name="isin"
                  type="text"
                  value={bondForm.isin}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label>
                Issuer
                <input
                  name="issuer"
                  type="text"
                  value={bondForm.issuer}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label>
                Bond Type
                <select
                  name="bond_type"
                  value={bondForm.bond_type}
                  onChange={handleBondFormChange}
                >
                  {BOND_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Currency
                <input
                  name="currency"
                  type="text"
                  maxLength="3"
                  value={bondForm.currency}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label>
                Seniority
                <select
                  name="seniority"
                  value={bondForm.seniority}
                  onChange={handleBondFormChange}
                >
                  {SENIORITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Market Liquidity
                <select
                  name="market_liquidity"
                  value={bondForm.market_liquidity}
                  onChange={handleBondFormChange}
                >
                  {LIQUIDITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Credit Rating
                <input
                  name="credit_rating"
                  type="text"
                  value={bondForm.credit_rating}
                  onChange={handleBondFormChange}
                  placeholder="AA+, BBB, BB+"
                />
              </label>

              <label>
                Face Value
                <input
                  name="face_value"
                  type="number"
                  step="0.0001"
                  min="0"
                  value={bondForm.face_value}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label>
                Annual Coupon %
                <input
                  name="annual_coupon_rate"
                  type="number"
                  step="0.0001"
                  min="0"
                  value={bondForm.annual_coupon_rate}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label>
                Coupon Frequency
                <input
                  name="coupon_frequency"
                  type="number"
                  min="1"
                  max="12"
                  value={bondForm.coupon_frequency}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label>
                Maturity Date
                <input
                  name="maturity_date"
                  type="date"
                  value={bondForm.maturity_date}
                  onChange={handleBondFormChange}
                  required
                />
              </label>

              <label className="checkbox-label">
                <input
                  name="is_callable"
                  type="checkbox"
                  checked={bondForm.is_callable}
                  onChange={handleBondFormChange}
                />
                Callable bond
              </label>
            </div>
          </section>
        )}

        <section className="form-section">
          <h2>3. Market Data</h2>

          <div className="form-grid">
            <label>
              Quote Date
              <input
                name="quote_date"
                type="date"
                value={marketDataForm.quote_date}
                onChange={handleMarketDataChange}
                required
              />
            </label>

            <label>
              Market Price
              <input
                name="market_price"
                type="number"
                step="0.0001"
                min="0"
                value={marketDataForm.market_price}
                onChange={handleMarketDataChange}
                required
              />
            </label>

            <label>
              Market Required Return %
              <input
                name="market_required_return"
                type="number"
                step="0.00001"
                value={marketDataForm.market_required_return}
                onChange={handleMarketDataChange}
                placeholder="Optional"
              />
            </label>

            <label>
              YTM %
              <input
                name="ytm"
                type="number"
                step="0.00001"
                value={marketDataForm.ytm}
                onChange={handleMarketDataChange}
                placeholder="Optional fallback"
              />
            </label>

            <label>
              Bid Price
              <input
                name="bid_price"
                type="number"
                step="0.0001"
                value={marketDataForm.bid_price}
                onChange={handleMarketDataChange}
                placeholder="Optional"
              />
            </label>

            <label>
              Ask Price
              <input
                name="ask_price"
                type="number"
                step="0.0001"
                value={marketDataForm.ask_price}
                onChange={handleMarketDataChange}
                placeholder="Optional"
              />
            </label>

            <label>
              Source
              <input
                name="source"
                type="text"
                value={marketDataForm.source}
                onChange={handleMarketDataChange}
              />
            </label>

            <label>
              Market Data Notes
              <textarea
                name="notes"
                value={marketDataForm.notes}
                onChange={handleMarketDataChange}
                rows="3"
              />
            </label>
          </div>
        </section>

        <section className="form-section">
          <h2>4. Position / Analysis Settings</h2>

          <div className="form-grid">
            {holdingType === HOLDING_TYPES.PORTFOLIO && (
              <>
                <label>
                  Quantity
                  <input
                    name="quantity"
                    type="number"
                    min="1"
                    value={positionForm.quantity}
                    onChange={handlePositionChange}
                    required
                  />
                </label>

                <label>
                  Purchase Price
                  <input
                    name="purchase_price"
                    type="number"
                    step="0.0001"
                    value={positionForm.purchase_price}
                    onChange={handlePositionChange}
                    placeholder="Optional"
                  />
                </label>
              </>
            )}

            <label>
              Base Currency
              <input
                name="base_currency"
                type="text"
                maxLength="3"
                value={positionForm.base_currency}
                onChange={handlePositionChange}
                required
              />
            </label>

            <label>
              Trading Fees %
              <input
                name="trading_fees_percent"
                type="number"
                step="0.0001"
                min="0"
                value={positionForm.trading_fees_percent}
                onChange={handlePositionChange}
              />
            </label>

            <label>
              Coupon Tax %
              <input
                name="coupon_tax_percent"
                type="number"
                step="0.0001"
                min="0"
                value={positionForm.coupon_tax_percent}
                onChange={handlePositionChange}
              />
            </label>

            <label>
              Expected Yield Change Δy %
              <input
                name="expected_yield_change"
                type="number"
                step="0.00001"
                value={positionForm.expected_yield_change}
                onChange={handlePositionChange}
              />
            </label>

            <label>
              Valuation Threshold %
              <input
                name="valuation_threshold_percent"
                type="number"
                step="0.0001"
                min="0"
                value={positionForm.valuation_threshold_percent}
                onChange={handlePositionChange}
              />
            </label>

            <label>
              Personal Target Return %
              <input
                name="target_required_return"
                type="number"
                step="0.00001"
                value={positionForm.target_required_return}
                onChange={handlePositionChange}
                placeholder="Optional"
              />
            </label>

            <label className="checkbox-label">
              <input
                name="reinvest_coupons"
                type="checkbox"
                checked={positionForm.reinvest_coupons}
                onChange={handlePositionChange}
              />
              Reinvest coupons
            </label>

            <label>
              Position Notes
              <textarea
                name="notes"
                value={positionForm.notes}
                onChange={handlePositionChange}
                rows="3"
              />
            </label>
          </div>
        </section>

        <div className="form-actions">
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Save Position"}
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate(-1)}
          >
            Cancel
          </button>
        </div>
      </form>
    </section>
  );
}

export default AddPositionPage;