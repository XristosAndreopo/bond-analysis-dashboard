/**
 * Bond detail page.
 *
 * This page is not displayed in the sidebar. The user reaches it by clicking
 * a bond from Dashboard, Portfolio, or Watchlist.
 *
 * The page allows:
 * - viewing calculated analysis
 * - viewing cash flows
 * - editing position settings
 * - moving between Portfolio and Watchlist
 * - soft-deleting a position
 * - adding or updating manual market data
 */

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { createMarketData } from "../api/bondsApi";
import {
  deletePosition,
  fetchPositionDetail,
  movePosition,
  updatePosition,
} from "../api/portfolioApi";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import {
  formatDecimal,
  formatMoney,
  formatPercent,
  formatRatioAsPercent,
} from "../utils/formatters";

const HOLDING_TYPES = {
  PORTFOLIO: "PORTFOLIO",
  WATCHLIST: "WATCHLIST",
};

function BondDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [detailData, setDetailData] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [activePanel, setActivePanel] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [positionForm, setPositionForm] = useState({
    quantity: "0",
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

  const [moveForm, setMoveForm] = useState({
    quantity: "1",
    purchase_price: "",
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

  useEffect(() => {
    loadDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function loadDetail() {
    setErrorMessage("");

    try {
      const data = await fetchPositionDetail(id);
      setDetailData(data);
      hydrateForms(data.item);
    } catch (error) {
      setErrorMessage("Δεν ήταν δυνατή η φόρτωση της ανάλυσης ομολόγου.");
    }
  }

  function hydrateForms(item) {
    const latestMarketData = item.latest_market_data;

    setPositionForm({
      quantity: String(item.quantity ?? "0"),
      purchase_price: item.purchase_price ?? "",
      base_currency: item.base_currency ?? "EUR",
      reinvest_coupons: Boolean(item.reinvest_coupons),
      trading_fees_percent: item.trading_fees_percent ?? "0.0000",
      coupon_tax_percent: item.coupon_tax_percent ?? "0.0000",
      expected_yield_change: item.expected_yield_change ?? "0.00000",
      valuation_threshold_percent: item.valuation_threshold_percent ?? "2.0000",
      evaluation_basis: item.evaluation_basis ?? "MARKET_DATA",
      target_required_return: item.target_required_return ?? "",
      notes: item.notes ?? "",
      is_active: Boolean(item.is_active),
    });

    setMoveForm({
      quantity: item.quantity > 0 ? String(item.quantity) : "1",
      purchase_price:
        item.purchase_price || latestMarketData?.market_price || "",
    });

    setMarketDataForm({
      quote_date:
        latestMarketData?.quote_date || new Date().toISOString().slice(0, 10),
      market_price: latestMarketData?.market_price || "",
      market_required_return: latestMarketData?.market_required_return || "",
      ytm: latestMarketData?.ytm || "",
      bid_price: latestMarketData?.bid_price || "",
      ask_price: latestMarketData?.ask_price || "",
      source: latestMarketData?.source || "manual",
      is_manual: latestMarketData?.is_manual ?? true,
      notes: latestMarketData?.notes || "",
    });
  }

  function cleanOptionalValue(value) {
    if (value === "" || value === null || value === undefined) {
      return null;
    }

    return value;
  }

  function handlePositionChange(event) {
    const { name, type, checked, value } = event.target;

    setPositionForm((previousData) => ({
      ...previousData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleMoveChange(event) {
    const { name, value } = event.target;

    setMoveForm((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  }

  function handleMarketDataChange(event) {
    const { name, type, checked, value } = event.target;

    setMarketDataForm((previousData) => ({
      ...previousData,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function getTargetHoldingType(item) {
    if (item.holding_type === HOLDING_TYPES.PORTFOLIO) {
      return HOLDING_TYPES.WATCHLIST;
    }

    return HOLDING_TYPES.PORTFOLIO;
  }

  function getMoveButtonLabel(item) {
    if (item.holding_type === HOLDING_TYPES.PORTFOLIO) {
      return "Move to Watchlist";
    }

    return "Move to Portfolio";
  }

  function buildPositionPayload(item) {
    const isPortfolio = item.holding_type === HOLDING_TYPES.PORTFOLIO;

    return {
      bond: item.bond.id,
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

  function buildMarketDataPayload(item) {
    return {
      bond: item.bond.id,
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

  async function handlePositionSubmit(event) {
    event.preventDefault();

    if (!detailData?.item) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await updatePosition(id, buildPositionPayload(detailData.item));
      await loadDetail();

      setSuccessMessage("Η θέση ενημερώθηκε με επιτυχία.");
      setActivePanel(null);
    } catch (error) {
      setErrorMessage(formatApiError(error, "Η ενημέρωση της θέσης απέτυχε."));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleMarketDataSubmit(event) {
    event.preventDefault();

    if (!detailData?.item) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await createMarketData(buildMarketDataPayload(detailData.item));
      await loadDetail();

      setSuccessMessage("Τα market data ενημερώθηκαν με επιτυχία.");
      setActivePanel(null);
    } catch (error) {
      setErrorMessage(
        formatApiError(error, "Η ενημέρωση των market data απέτυχε.")
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleMoveSubmit(event) {
    event.preventDefault();

    if (!detailData?.item) {
      return;
    }

    const item = detailData.item;
    const targetHoldingType = getTargetHoldingType(item);

    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const payload =
        targetHoldingType === HOLDING_TYPES.PORTFOLIO
          ? {
              target_holding_type: targetHoldingType,
              quantity: Number(moveForm.quantity),
              purchase_price: cleanOptionalValue(moveForm.purchase_price),
            }
          : {
              target_holding_type: targetHoldingType,
            };

      const movedItem = await movePosition(id, payload);

      setSuccessMessage("Το ομόλογο μετακινήθηκε με επιτυχία.");
      setActivePanel(null);

      navigate(`/positions/${movedItem.id}`);
    } catch (error) {
      setErrorMessage(
        formatApiError(error, "Η μετακίνηση του ομολόγου απέτυχε.")
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm(
      "Θέλεις σίγουρα να διαγράψεις αυτή τη θέση;"
    );

    if (!confirmed) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const currentHoldingType = detailData.item.holding_type;

      await deletePosition(id);

      if (currentHoldingType === HOLDING_TYPES.PORTFOLIO) {
        navigate("/portfolio");
      } else {
        navigate("/watchlist");
      }
    } catch (error) {
      setErrorMessage(formatApiError(error, "Η διαγραφή της θέσης απέτυχε."));
    } finally {
      setIsSubmitting(false);
    }
  }

  function formatApiError(error, fallbackMessage) {
    const apiError = error.response?.data;

    if (typeof apiError === "string") {
      return apiError;
    }

    if (apiError) {
      return JSON.stringify(apiError);
    }

    return fallbackMessage;
  }

  if (errorMessage && !detailData) {
    return <div className="error-box">{errorMessage}</div>;
  }

  if (!detailData) {
    return <div className="loading-text">Loading bond detail...</div>;
  }

  const item = detailData.item;
  const bond = item.bond;
  const analysis = item.latest_analysis;
  const marketData = item.latest_market_data;
  const cashFlows = analysis?.cash_flows || [];
  const targetHoldingType = getTargetHoldingType(item);

  return (
    <section className="page-section">
      <div className="detail-hero">
        <span>{item.holding_type_label}</span>
        <h1>{bond.name}</h1>
        <p>
          {bond.isin} | {bond.issuer} | {bond.currency}
        </p>

        <div className="signal-box">
          <SignalBadge
            signal={analysis?.final_signal}
            label={analysis?.final_signal_label}
          />

          <RiskBadge
            riskLevel={analysis?.risk_level}
            label={analysis?.risk_level_label}
          />

          <span>Risk Score: {formatDecimal(analysis?.risk_score, 2)}</span>
        </div>

        <p>{analysis?.reasoning || "Δεν υπάρχει ακόμα διαθέσιμη ανάλυση."}</p>

        <div className="detail-actions">
          <button
            type="button"
            onClick={() =>
              setActivePanel(activePanel === "edit" ? null : "edit")
            }
          >
            Edit Position
          </button>

          <button
            type="button"
            onClick={() =>
              setActivePanel(activePanel === "marketData" ? null : "marketData")
            }
          >
            Add / Update Market Data
          </button>

          <button
            type="button"
            onClick={() =>
              setActivePanel(activePanel === "move" ? null : "move")
            }
          >
            {getMoveButtonLabel(item)}
          </button>

          <button
            type="button"
            className="danger-button"
            onClick={handleDelete}
            disabled={isSubmitting}
          >
            Delete
          </button>
        </div>
      </div>

      <Disclaimer text={detailData.disclaimer} />

      {errorMessage && <div className="error-box">{errorMessage}</div>}
      {successMessage && <div className="success-box">{successMessage}</div>}

      {activePanel === "edit" && (
        <form className="form-card" onSubmit={handlePositionSubmit}>
          <section className="form-section">
            <h2>Edit Position</h2>

            <div className="form-grid">
              {item.holding_type === HOLDING_TYPES.PORTFOLIO && (
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
              onClick={() => setActivePanel(null)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {activePanel === "marketData" && (
        <form className="form-card" onSubmit={handleMarketDataSubmit}>
          <section className="form-section">
            <h2>Add / Update Market Data</h2>

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

          <div className="form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Market Data"}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={() => setActivePanel(null)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {activePanel === "move" && (
        <form className="form-card" onSubmit={handleMoveSubmit}>
          <section className="form-section">
            <h2>{getMoveButtonLabel(item)}</h2>

            {targetHoldingType === HOLDING_TYPES.PORTFOLIO ? (
              <div className="form-grid">
                <label>
                  Quantity
                  <input
                    name="quantity"
                    type="number"
                    min="1"
                    value={moveForm.quantity}
                    onChange={handleMoveChange}
                    required
                  />
                </label>

                <label>
                  Purchase Price
                  <input
                    name="purchase_price"
                    type="number"
                    step="0.0001"
                    value={moveForm.purchase_price}
                    onChange={handleMoveChange}
                    placeholder="Optional"
                  />
                </label>
              </div>
            ) : (
              <p className="muted-text">
                Το ομόλογο θα μετακινηθεί στη Watchlist και η ποσότητα θα γίνει
                μηδέν.
              </p>
            )}
          </section>

          <div className="form-actions">
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Moving..." : getMoveButtonLabel(item)}
            </button>

            <button
              type="button"
              className="secondary-button"
              onClick={() => setActivePanel(null)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="metrics-grid">
        <MetricCard
          title="Market Price"
          value={formatMoney(marketData?.market_price, bond.currency, 4)}
          description="Τρέχουσα αγοραία τιμή σύμφωνα με τα τελευταία market data."
        />

        <MetricCard
          title="Market Required Return"
          value={formatPercent(marketData?.market_required_return, 2)}
          description="Απαιτούμενη απόδοση αγοράς που χρησιμοποιείται ως βασικό discount rate."
        />

        <MetricCard
          title="YTM"
          value={formatPercent(marketData?.ytm, 2)}
          description="Απόδοση έως τη λήξη, χρησιμοποιείται ως fallback αν δεν υπάρχει required return."
        />

        <MetricCard
          title="Macaulay Duration"
          value={formatDecimal(analysis?.macaulay_duration, 2)}
          description="Σταθμισμένος χρόνος είσπραξης των ταμειακών ροών."
        />

        <MetricCard
          title="Modified Duration"
          value={formatDecimal(analysis?.modified_duration, 2)}
          description="Ευαισθησία της τιμής σε μεταβολές επιτοκίων."
        />

        <MetricCard
          title="Price Impact"
          value={formatRatioAsPercent(analysis?.price_impact, 2)}
          description="Εκτίμηση ποσοστιαίας μεταβολής τιμής με βάση το αναμενόμενο Δy."
        />

        <MetricCard
          title="Estimated Price"
          value={formatMoney(analysis?.estimated_price, bond.currency, 4)}
          description="Εκτιμώμενη τιμή μετά την επίδραση της μεταβολής απόδοσης."
        />

        <MetricCard
          title="Intrinsic Value"
          value={formatMoney(analysis?.intrinsic_value, bond.currency, 4)}
          description="Παρούσα αξία των μελλοντικών καθαρών ταμειακών ροών."
        />

        <MetricCard
          title="IV vs Market Price"
          value={formatPercent(analysis?.iv_vs_market_price, 2)}
          description="Διαφορά εσωτερικής αξίας από την τρέχουσα αγοραία τιμή."
        />

        <MetricCard
          title="Current Yield"
          value={formatPercent(analysis?.current_yield, 2)}
          description="Ετήσιο κουπόνι σε σχέση με την αγοραία τιμή."
        />

        <MetricCard
          title="Approx AYTM"
          value={formatPercent(analysis?.approx_aytm, 2)}
          description="Προσεγγιστική ετήσια απόδοση έως τη λήξη."
        />

        <MetricCard
          title="Net YTM"
          value={formatPercent(analysis?.net_ytm, 2)}
          description="Εκτίμηση απόδοσης μετά τη φορολογία κουπονιών."
        />

        <MetricCard
          title="RCY"
          value={formatPercent(analysis?.rcy, 2)}
          description="Ένδειξη απόδοσης με βάση την επανεπένδυση κουπονιών."
        />
      </div>

      <div className="table-card">
        <h2>Cash Flows</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Period</th>
                <th>Payment Date</th>
                <th>Coupon Gross</th>
                <th>Coupon Tax</th>
                <th>Coupon Net</th>
                <th>Principal</th>
                <th>Total Cash Flow</th>
                <th>Discounted Cash Flow</th>
              </tr>
            </thead>

            <tbody>
              {cashFlows.length === 0 ? (
                <tr>
                  <td colSpan="8">Δεν υπάρχουν διαθέσιμα cash flows.</td>
                </tr>
              ) : (
                cashFlows.map((cashFlow) => (
                  <tr key={cashFlow.id}>
                    <td>{cashFlow.period_number}</td>
                    <td>{cashFlow.payment_date}</td>
                    <td>
                      {formatMoney(cashFlow.coupon_gross, bond.currency, 4)}
                    </td>
                    <td>{formatMoney(cashFlow.coupon_tax, bond.currency, 4)}</td>
                    <td>{formatMoney(cashFlow.coupon_net, bond.currency, 4)}</td>
                    <td>{formatMoney(cashFlow.principal, bond.currency, 4)}</td>
                    <td>
                      {formatMoney(cashFlow.total_cash_flow, bond.currency, 4)}
                    </td>
                    <td>
                      {formatMoney(
                        cashFlow.discounted_cash_flow,
                        bond.currency,
                        4
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function MetricCard({ title, value, description }) {
  return (
    <div className="metric-card">
      <span>{title}</span>
      <strong>{value || "-"}</strong>
      <p>{description}</p>
    </div>
  );
}

export default BondDetailPage;