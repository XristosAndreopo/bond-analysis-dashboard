/**
 * Bond detail page.
 *
 * Displays one user-owned bond position from Portfolio or Watchlist.
 *
 * This page shows:
 * - bond master data
 * - latest market data
 * - latest bond analysis
 * - risk and signal
 * - discounted cash flows
 * - market data update form
 *
 * Important:
 *   If a position was moved from Watchlist to Portfolio, the old position ID
 *   may become inactive. In that case, the backend may return 404.
 */

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createMarketData } from "../api/bondsApi";
import {
  deletePosition,
  fetchPositionDetail,
  movePosition,
} from "../api/portfolioApi";
import Disclaimer from "../components/Disclaimer";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import {
  formatDecimal,
  formatMoney,
  formatPercent,
} from "../utils/formatters";

function BondDetailPage() {
  const { positionId } = useParams();
  const navigate = useNavigate();

  const [detailData, setDetailData] = useState(null);
  const [marketDataForm, setMarketDataForm] = useState(getEmptyMarketDataForm());
  const [isMarketFormVisible, setIsMarketFormVisible] = useState(false);
  const [isSubmittingMarketData, setIsSubmittingMarketData] = useState(false);
  const [isMovingPosition, setIsMovingPosition] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    loadPositionDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [positionId]);

  async function loadPositionDetail() {
    try {
      setErrorMessage("");
      setSuccessMessage("");

      const data = await fetchPositionDetail(positionId);

      setDetailData(data);
      setMarketDataForm(buildMarketDataForm(data.item));
    } catch (error) {
      setErrorMessage(
        "Δεν ήταν δυνατή η φόρτωση της ανάλυσης ομολόγου. " +
          "Το position μπορεί να έχει μετακινηθεί ή να έχει απενεργοποιηθεί. " +
          "Άνοιξε το ομόλογο ξανά από το Portfolio ή το Watchlist."
      );
    }
  }

  function handleMarketDataChange(event) {
    const { name, value } = event.target;

    setMarketDataForm((previousForm) => ({
      ...previousForm,
      [name]: value,
    }));
  }

  async function handleMarketDataSubmit(event) {
    event.preventDefault();

    if (!detailData?.item?.bond?.id) {
      setErrorMessage("Δεν βρέθηκε bond id για αποθήκευση market data.");
      return;
    }

    setIsSubmittingMarketData(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await createMarketData({
        bond: detailData.item.bond.id,
        quote_date: marketDataForm.quote_date,
        market_price: marketDataForm.market_price,
        market_required_return:
          marketDataForm.market_required_return || null,
        ytm: marketDataForm.ytm || null,
        bid_price: marketDataForm.bid_price || null,
        ask_price: marketDataForm.ask_price || null,
        source: marketDataForm.source || "manual",
        is_manual: true,
        notes: marketDataForm.notes || "",
      });

      setSuccessMessage(
        "Τα market data αποθηκεύτηκαν και η ανάλυση ενημερώθηκε."
      );
      setIsMarketFormVisible(false);

      await loadPositionDetail();
    } catch (error) {
      setErrorMessage(
        "Δεν ήταν δυνατή η αποθήκευση των market data. Έλεγξε τα πεδία."
      );
    } finally {
      setIsSubmittingMarketData(false);
    }
  }

  async function handleMovePosition() {
    if (!detailData?.item || isMovingPosition) {
      return;
    }

    const item = detailData.item;

    const targetHoldingType =
      item.holding_type === "PORTFOLIO" ? "WATCHLIST" : "PORTFOLIO";

    const targetPath =
      targetHoldingType === "PORTFOLIO" ? "/portfolio" : "/watchlist";

    const payload = {
      target_holding_type: targetHoldingType,
    };

    /*
     * When moving from Watchlist to Portfolio, the backend needs quantity.
     * Default logic:
     * - quantity: 1
     * - purchase_price: latest market price, otherwise existing purchase price,
     *   otherwise bond face value.
     */
    if (targetHoldingType === "PORTFOLIO") {
      payload.quantity = 1;
      payload.purchase_price =
        item.latest_market_data?.market_price ||
        item.purchase_price ||
        item.bond?.face_value ||
        "100";
    }

    try {
      setIsMovingPosition(true);
      setErrorMessage("");
      setSuccessMessage("");

      const movedItem = await movePosition(item.id, payload);

      if (!movedItem?.id) {
        setErrorMessage(
          "Το backend δεν επέστρεψε έγκυρο position μετά τη μετακίνηση."
        );
        return;
      }

      navigate(targetPath);
    } catch (error) {
      const apiMessage =
        error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.join(" ") ||
        JSON.stringify(error.response?.data || {});

      setErrorMessage(
        `Δεν ήταν δυνατή η μετακίνηση του ομολόγου. ${apiMessage}`
      );
    } finally {
      setIsMovingPosition(false);
    }
  }

  async function handleDeletePosition() {
    if (!detailData?.item) {
      return;
    }

    const confirmed = window.confirm(
      "Θέλεις σίγουρα να αφαιρέσεις αυτό το ομόλογο;"
    );

    if (!confirmed) {
      return;
    }

    try {
      await deletePosition(detailData.item.id);

      if (detailData.item.holding_type === "PORTFOLIO") {
        navigate("/portfolio");
      } else {
        navigate("/watchlist");
      }
    } catch (error) {
      setErrorMessage("Δεν ήταν δυνατή η διαγραφή του ομολόγου.");
    }
  }

  if (errorMessage && !detailData) {
    return (
      <section className="page-section">
        <div className="error-box">{errorMessage}</div>

        <div className="detail-actions">
          <Link to="/portfolio" className="primary-link-button">
            Go to Portfolio
          </Link>

          <Link to="/watchlist" className="secondary-link-button">
            Go to Watchlist
          </Link>
        </div>
      </section>
    );
  }

  if (!detailData) {
    return <div className="loading-text">Loading bond analysis...</div>;
  }

  const item = detailData.item;
  const bond = item.bond;
  const marketData = item.latest_market_data;
  const analysis = item.latest_analysis;
  const cashFlows = analysis?.cash_flows || [];

  return (
    <section className="page-section">
      <div className="page-header page-header-with-actions">
        <div>
          <h1>{bond.name}</h1>
          <p>
            {bond.isin} · {bond.issuer} · {bond.currency}
          </p>
        </div>

        <div className="detail-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => setIsMarketFormVisible((value) => !value)}
          >
            {isMarketFormVisible
              ? "Hide Market Data"
              : "Add / Update Market Data"}
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={handleMovePosition}
            disabled={isMovingPosition}
          >
            {isMovingPosition
              ? "Moving..."
              : item.holding_type === "PORTFOLIO"
                ? "Move to Watchlist"
                : "Move to Portfolio"}
          </button>

          <button
            type="button"
            className="danger-button"
            onClick={handleDeletePosition}
          >
            Delete
          </button>
        </div>
      </div>

      <Disclaimer text={detailData.disclaimer} />

      {successMessage && <div className="info-box">{successMessage}</div>}

      {errorMessage && <div className="warning-box">{errorMessage}</div>}

      {isMarketFormVisible && (
        <MarketDataForm
          formData={marketDataForm}
          isSubmitting={isSubmittingMarketData}
          onChange={handleMarketDataChange}
          onSubmit={handleMarketDataSubmit}
        />
      )}

      <div className="detail-grid">
        <div className="detail-card">
          <h2>Bond Info</h2>

          <InfoRow label="ISIN" value={bond.isin} />
          <InfoRow label="Issuer" value={bond.issuer} />
          <InfoRow label="Type" value={bond.bond_type_label} />
          <InfoRow label="Currency" value={bond.currency} />
          <InfoRow label="Seniority" value={bond.seniority_label} />
          <InfoRow label="Credit Rating" value={bond.credit_rating || "-"} />
          <InfoRow label="Liquidity" value={bond.market_liquidity_label} />
          <InfoRow label="Maturity" value={bond.maturity_date} />
          <InfoRow
            label="Coupon"
            value={formatPercent(bond.annual_coupon_rate, 3)}
          />
          <InfoRow label="Frequency" value={bond.coupon_frequency} />
        </div>

        <div className="detail-card">
          <h2>Latest Market Data</h2>

          {marketData ? (
            <>
              <InfoRow label="Quote Date" value={marketData.quote_date} />

              <InfoRow
                label="Market Price"
                value={formatMoney(marketData.market_price, bond.currency, 4)}
              />

              <InfoRow label="YTM" value={formatPercent(marketData.ytm, 3)} />

              <InfoRow
                label="Discount Rate"
                value={<DiscountRateValue marketData={marketData} />}
              />

              <InfoRow
                label="Bid / Ask"
                value={`${formatDecimal(
                  marketData.bid_price,
                  4
                )} / ${formatDecimal(marketData.ask_price, 4)}`}
              />

              <InfoRow label="Source" value={marketData.source} />
            </>
          ) : (
            <p className="muted-text">
              Δεν υπάρχουν market data. Πρόσθεσε market price και required return.
            </p>
          )}
        </div>
      </div>

      <div className="table-card">
        <h2>Analysis Summary</h2>

        {analysis ? (
          <>
            <div className="metric-grid">
              <MetricCard
                label="Intrinsic Value"
                value={formatMoney(analysis.intrinsic_value, bond.currency, 2)}
              />

              <MetricCard
                label="Current Yield"
                value={formatPercent(analysis.current_yield, 2)}
              />

              <MetricCard
                label="Net YTM"
                value={formatPercent(analysis.net_ytm, 2)}
              />

              <MetricCard
                label="Modified Duration"
                value={formatDecimal(analysis.modified_duration, 2)}
              />

              <MetricCard
                label="Risk Score"
                value={formatDecimal(analysis.risk_score, 2)}
              />

              <div className="metric-card">
                <span>Risk Level</span>
                <RiskBadge
                  riskLevel={analysis.risk_level}
                  label={analysis.risk_level_label}
                />
              </div>

              <div className="metric-card">
                <span>Signal</span>
                <SignalBadge
                  signal={analysis.final_signal}
                  label={analysis.final_signal_label}
                />
              </div>
            </div>

            <div className="analysis-text-grid">
              <div>
                <h3>Reasoning</h3>
                <p>{analysis.reasoning || "-"}</p>
              </div>

              <div>
                <h3>Risk Reasoning</h3>
                <p>{analysis.risk_reasoning || "-"}</p>
              </div>
            </div>
          </>
        ) : (
          <p className="muted-text">
            Δεν υπάρχει ακόμα ανάλυση. Συνήθως χρειάζονται market data και θέση
            στο Portfolio ή Watchlist.
          </p>
        )}
      </div>

      <div className="table-card">
        <h2>Discounted Cash Flows</h2>

        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Payment Date</th>
                <th>Gross Coupon</th>
                <th>Coupon Tax</th>
                <th>Net Coupon</th>
                <th>Principal</th>
                <th>Total Cash Flow</th>
                <th>Discounted Cash Flow</th>
              </tr>
            </thead>

            <tbody>
              {cashFlows.length === 0 ? (
                <tr>
                  <td colSpan="7">Δεν υπάρχουν διαθέσιμες ταμειακές ροές.</td>
                </tr>
              ) : (
                cashFlows.map((cashFlow) => (
                  <tr key={cashFlow.id}>
                    <td>{cashFlow.payment_date}</td>

                    <td>
                      {formatMoney(
                        cashFlow.coupon_gross,
                        bond.currency,
                        2
                      )}
                    </td>

                    <td>
                      {formatMoney(
                        cashFlow.coupon_tax,
                        bond.currency,
                        2
                      )}
                    </td>

                    <td>
                      {formatMoney(
                        cashFlow.coupon_net,
                        bond.currency,
                        2
                      )}
                    </td>

                    <td>
                      {formatMoney(
                        cashFlow.principal,
                        bond.currency,
                        2
                      )}
                    </td>

                    <td>
                      {formatMoney(
                        cashFlow.total_cash_flow,
                        bond.currency,
                        2
                      )}
                    </td>

                    <td>
                      {formatMoney(
                        cashFlow.discounted_cash_flow,
                        bond.currency,
                        2
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <p className="helper-text">
          Οι ταμειακές ροές υπολογίζονται από το backend. Ο πίνακας εμφανίζει
          τα ποσά που επιστρέφει το API: gross coupon, coupon tax, net coupon,
          principal, total cash flow και discounted cash flow.
        </p>
      </div>
    </section>
  );
}

function MarketDataForm({ formData, isSubmitting, onChange, onSubmit }) {
  return (
    <form className="form-card" onSubmit={onSubmit}>
      <h2>Market Data</h2>

      <div className="form-grid">
        <label>
          Quote Date
          <input
            type="date"
            name="quote_date"
            value={formData.quote_date}
            onChange={onChange}
            required
          />
        </label>

        <label>
          Market Price
          <input
            type="number"
            step="0.0001"
            name="market_price"
            value={formData.market_price}
            onChange={onChange}
            required
          />
        </label>

        <label>
          Market Required Return %
          <input
            type="number"
            step="0.00001"
            name="market_required_return"
            value={formData.market_required_return}
            onChange={onChange}
          />
        </label>

        <label>
          YTM %
          <input
            type="number"
            step="0.00001"
            name="ytm"
            value={formData.ytm}
            onChange={onChange}
          />
        </label>

        <label>
          Bid Price
          <input
            type="number"
            step="0.0001"
            name="bid_price"
            value={formData.bid_price}
            onChange={onChange}
          />
        </label>

        <label>
          Ask Price
          <input
            type="number"
            step="0.0001"
            name="ask_price"
            value={formData.ask_price}
            onChange={onChange}
          />
        </label>

        <label>
          Source
          <input
            type="text"
            name="source"
            value={formData.source}
            onChange={onChange}
          />
        </label>
      </div>

      <label>
        Notes
        <textarea
          name="notes"
          value={formData.notes}
          onChange={onChange}
          rows="3"
        />
      </label>

      <button
        type="submit"
        className="primary-link-button"
        disabled={isSubmitting}
      >
        {isSubmitting ? "Saving..." : "Save Market Data"}
      </button>
    </form>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}

function DiscountRateValue({ marketData }) {
  if (!marketData?.effective_discount_rate) {
    return "-";
  }

  return (
    <>
      {formatPercent(marketData.effective_discount_rate, 3)}
      <br />
      <small>{getDiscountRateSourceLabel(marketData)}</small>
    </>
  );
}

function getDiscountRateSourceLabel(marketData) {
  if (marketData?.market_required_return) {
    return "Market required return";
  }

  if (marketData?.ytm) {
    return "YTM fallback";
  }

  return "No rate source";
}

function getEmptyMarketDataForm() {
  return {
    quote_date: new Date().toISOString().slice(0, 10),
    market_price: "",
    market_required_return: "",
    ytm: "",
    bid_price: "",
    ask_price: "",
    source: "manual",
    notes: "",
  };
}

function buildMarketDataForm(item) {
  const marketData = item?.latest_market_data;

  if (!marketData) {
    return getEmptyMarketDataForm();
  }

  return {
    quote_date: marketData.quote_date || new Date().toISOString().slice(0, 10),
    market_price: marketData.market_price || "",
    market_required_return: marketData.market_required_return || "",
    ytm: marketData.ytm || "",
    bid_price: marketData.bid_price || "",
    ask_price: marketData.ask_price || "",
    source: marketData.source || "manual",
    notes: marketData.notes || "",
  };
}

export default BondDetailPage;