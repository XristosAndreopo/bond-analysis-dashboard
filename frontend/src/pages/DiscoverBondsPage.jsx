/**
 * Discover Bonds page.
 *
 * Purpose:
 * - Show active candidate bonds that can be added to My Watchlist.
 * - Support only two candidate sources:
 *   1. CSV Provider
 *   2. AI Research Provider
 *
 * The frontend never invents bond data. It either uploads CSV data or asks
 * Puter.js to produce structured AI research JSON. The Django backend remains
 * responsible for validation, user ownership, duplicate checks, import, and
 * backend-calculated YTM/duration when enough verified fields exist.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  addDiscoveredBondToWatchlist,
  clearCurrentDiscoveryResults,
  fetchDiscoveredBonds,
  fetchDiscoveryProviderStatus,
  ignoreDiscoveredBond,
  importAIResearchDiscoveryJson,
  runBondDiscovery,
  uploadDiscoveryCsv,
} from "../api/discoveryApi";
import RiskBadge from "../components/RiskBadge";
import SignalBadge from "../components/SignalBadge";
import { generateDiscoveryResearchJson } from "../services/puterAIResearchService";
import {
  formatDecimal,
  formatMoney,
  formatPercent,
} from "../utils/formatters";

const AI_RESEARCH_SOURCE = "ai_research_agent";
const CSV_PROVIDER_SOURCE = "csv_provider";

const SOURCE_OPTIONS = [
  { value: CSV_PROVIDER_SOURCE, label: "CSV Provider" },
  { value: AI_RESEARCH_SOURCE, label: "AI Research Provider" },
];

const MINIMUM_RATING_OPTIONS = [
  "BBB-",
  "BBB",
  "BBB+",
  "A-",
  "A",
  "A+",
  "AA-",
  "AA",
  "AA+",
  "AAA",
];

const CURRENCY_OPTIONS = [
  { value: "EUR", label: "EUR" },
  { value: "USD", label: "USD" },
  { value: "GBP", label: "GBP" },
  { value: "CHF", label: "CHF" },
  { value: "JPY", label: "JPY" },
];

const COUNTRY_OPTIONS = [
  { value: "GR", label: "Greece" },
  { value: "US", label: "United States" },
  { value: "DE", label: "Germany" },
  { value: "FR", label: "France" },
  { value: "IT", label: "Italy" },
  { value: "ES", label: "Spain" },
  { value: "NL", label: "Netherlands" },
];

const BOND_TYPE_OPTIONS = [
  { value: "GOVERNMENT", label: "Government" },
  { value: "CORPORATE", label: "Corporate" },
  { value: "TREASURY", label: "Treasury" },
  { value: "MUNICIPAL", label: "Municipal" },
  { value: "OTHER", label: "Other" },
];

const DEFAULT_FILTERS = {
  source: CSV_PROVIDER_SOURCE,
  minRating: "BBB-",
  currencies: [],
  countries: [],
  bondTypes: [],
};

const CSV_TEMPLATE_COLUMNS = [
  "isin",
  "name",
  "issuer",
  "country",
  "currency",
  "bond_type",
  "coupon_rate",
  "coupon_frequency",
  "maturity_date",
  "credit_rating",
  "rating_source",
  "market_price",
  "ytm",
  "duration",
  "source",
  "source_url",
];

const CSV_TEMPLATE_ROWS = [
  [
    "US91282CQU89",
    "U.S. Treasury Note 4.125% 2031",
    "United States Treasury",
    "US",
    "USD",
    "TREASURY",
    "4.125",
    "2",
    "2031-05-31",
    "AA+",
    "Manual CSV",
    "100.5000",
    "4.1000",
    "4.4500",
    "csv_provider",
    "",
  ],
  [
    "GR0114033583",
    "GGB 3.875% 2028",
    "Hellenic Republic",
    "GR",
    "EUR",
    "GOVERNMENT",
    "3.875",
    "1",
    "2028-06-15",
    "BBB-",
    "Manual CSV",
    "99.7500",
    "3.9500",
    "2.1000",
    "csv_provider",
    "",
  ],
];

function DiscoverBondsPage() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedCsvFile, setSelectedCsvFile] = useState(null);
  const [aiResearchJsonText, setAIResearchJsonText] = useState("");
  const [aiQualityWarnings, setAIQualityWarnings] = useState([]);

  const [candidates, setCandidates] = useState([]);
  const [lastDiscoveryRun, setLastDiscoveryRun] = useState(null);
  const [lastCsvUpload, setLastCsvUpload] = useState(null);
  const [lastAIResearchImport, setLastAIResearchImport] = useState(null);
  const [providerStatus, setProviderStatus] = useState(null);

  const [isProviderStatusExpanded, setIsProviderStatusExpanded] =
    useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingProviderStatus, setIsLoadingProviderStatus] = useState(false);
  const [isRunningDiscovery, setIsRunningDiscovery] = useState(false);
  const [isUploadingCsv, setIsUploadingCsv] = useState(false);
  const [isGeneratingAIResearchJson, setIsGeneratingAIResearchJson] =
    useState(false);
  const [isImportingAIResearchJson, setIsImportingAIResearchJson] =
    useState(false);
  const [isClearingResults, setIsClearingResults] = useState(false);
  const [candidateActionId, setCandidateActionId] = useState(null);

  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const isAIResearchSource = filters.source === AI_RESEARCH_SOURCE;
  const isDiscovering =
    isRunningDiscovery ||
    isGeneratingAIResearchJson ||
    isImportingAIResearchJson;

  useEffect(() => {
    loadProviderStatus();
    loadCandidates();
  }, []);

  async function loadProviderStatus() {
    setIsLoadingProviderStatus(true);

    try {
      const data = await fetchDiscoveryProviderStatus();
      setProviderStatus(data);
    } catch (error) {
      setProviderStatus(null);
    } finally {
      setIsLoadingProviderStatus(false);
    }
  }

  async function loadCandidates(discoveryRunId = null) {
    setIsLoading(true);

    try {
      setErrorMessage("");

      const params = discoveryRunId
        ? { discovery_run_id: discoveryRunId }
        : {};

      const data = await fetchDiscoveredBonds(params);
      setCandidates(Array.isArray(data) ? data : []);
    } catch (error) {
      setErrorMessage("Could not load discovered bond candidates.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleFilterChange(event) {
    const { name, value } = event.target;

    setFilters((currentFilters) => ({
      ...currentFilters,
      [name]: value,
    }));

    setSuccessMessage("");
    setErrorMessage("");
  }

  function handleCheckboxFilterChange(groupName, optionValue, isChecked) {
    setFilters((currentFilters) => {
      const currentValues = currentFilters[groupName] || [];
      const nextValues = isChecked
        ? [...new Set([...currentValues, optionValue])]
        : currentValues.filter((value) => value !== optionValue);

      return {
        ...currentFilters,
        [groupName]: nextValues,
      };
    });

    setSuccessMessage("");
    setErrorMessage("");
  }

  function handleCheckboxFilterClear(groupName) {
    setFilters((currentFilters) => ({
      ...currentFilters,
      [groupName]: [],
    }));

    setSuccessMessage("");
    setErrorMessage("");
  }

  function handleResetFilters() {
    setFilters(DEFAULT_FILTERS);
    setSelectedCsvFile(null);
    setLastCsvUpload(null);
    setLastAIResearchImport(null);
    setAIResearchJsonText("");
    setAIQualityWarnings([]);
    setSuccessMessage("");
    setErrorMessage("");
  }

  function handleCsvFileChange(event) {
    const file = event.target.files?.[0] || null;

    setSelectedCsvFile(file);
    setLastCsvUpload(null);
    setSuccessMessage("");
    setErrorMessage("");
  }

  function handleDownloadCsvTemplate() {
    const csvContent = buildCsvTemplateContent();
    const blob = new Blob([csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = downloadUrl;
    link.download = "bond_universe_template.csv";
    link.click();

    URL.revokeObjectURL(downloadUrl);
  }

  function buildDiscoveryPayload() {
    return {
      source: CSV_PROVIDER_SOURCE,
      min_rating: filters.minRating,
      currencies: filters.currencies,
      countries: filters.countries,
      bond_types: filters.bondTypes,
    };
  }

  function buildAIResearchFilters() {
    return {
      countries: filters.countries,
      currencies: filters.currencies,
      minimum_rating: filters.minRating || null,
      maturity_from: null,
      maturity_to: null,
      issuer_types: [],
      bond_types: filters.bondTypes,
    };
  }

  async function handleUploadCsv() {
    if (!selectedCsvFile) {
      setErrorMessage("Please choose a CSV file first.");
      return;
    }

    setIsUploadingCsv(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const result = await uploadDiscoveryCsv(selectedCsvFile);

      setLastCsvUpload(result.upload || null);
      setSuccessMessage(
        "CSV uploaded successfully. Press Discovery to load candidates."
      );

      await loadProviderStatus();
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error, "Could not upload CSV file."));
    } finally {
      setIsUploadingCsv(false);
    }
  }

  async function handleDiscover() {
    if (isAIResearchSource) {
      await handleAIResearchDiscovery();
      return;
    }

    await handleCsvDiscovery();
  }

  async function handleCsvDiscovery() {
    setIsRunningDiscovery(true);
    setSuccessMessage("");
    setErrorMessage("");
    setAIQualityWarnings([]);

    try {
      const result = await runBondDiscovery(buildDiscoveryPayload());
      const discoveryRun = result.run || null;

      setLastDiscoveryRun(discoveryRun);
      setCandidates(Array.isArray(result.candidates) ? result.candidates : []);
      setSuccessMessage("Discovery completed successfully from CSV Provider.");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not run CSV bond discovery.")
      );
    } finally {
      setIsRunningDiscovery(false);
    }
  }

  async function handleAIResearchDiscovery() {
    setIsGeneratingAIResearchJson(true);
    setIsImportingAIResearchJson(false);
    setSuccessMessage("");
    setErrorMessage("");
    setLastAIResearchImport(null);
    setAIQualityWarnings([]);

    try {
      const generatedPayload = await generateDiscoveryResearchJson(
        buildAIResearchFilters()
      );

      setAIResearchJsonText(JSON.stringify(generatedPayload, null, 2));
      setAIQualityWarnings(buildAIQualityWarnings(generatedPayload));

      setIsGeneratingAIResearchJson(false);
      setIsImportingAIResearchJson(true);

      const result = await importAIResearchDiscoveryJson(generatedPayload);
      const importSummary = result.import_summary || null;

      setLastAIResearchImport(importSummary);

      if (importSummary?.discovery_run_id) {
        setLastDiscoveryRun({
          id: importSummary.discovery_run_id,
          total_found: importSummary.total_found,
          total_saved:
            Number(importSummary.total_created || 0) +
            Number(importSummary.total_updated || 0),
          total_skipped: importSummary.total_skipped,
          status: "COMPLETED",
          status_label: "Completed",
        });

        await loadCandidates(importSummary.discovery_run_id);
      } else {
        await loadCandidates();
      }

      setSuccessMessage(
        "AI Research Provider completed. The backend imported valid candidates and calculated missing YTM/duration where possible."
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not complete AI Research discovery.")
      );
    } finally {
      setIsGeneratingAIResearchJson(false);
      setIsImportingAIResearchJson(false);
    }
  }

  async function handleClearCurrentResults() {
    if (candidates.length === 0) {
      setErrorMessage("There are no current discovery results to clear.");
      return;
    }

    setIsClearingResults(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const result = await clearCurrentDiscoveryResults(
        lastDiscoveryRun?.id || null
      );

      setCandidates([]);
      setSuccessMessage(
        `Current results cleared. Ignored candidates: ${result.ignored_count}.`
      );
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not clear current results.")
      );
    } finally {
      setIsClearingResults(false);
    }
  }

  async function handleAddToWatchlist(candidateId) {
    setCandidateActionId(candidateId);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      await addDiscoveredBondToWatchlist(candidateId);
      await loadCandidates(lastDiscoveryRun?.id || null);

      setSuccessMessage("Candidate added to My Watchlist.");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not add candidate to Watchlist.")
      );
    } finally {
      setCandidateActionId(null);
    }
  }

  async function handleIgnore(candidateId) {
    setCandidateActionId(candidateId);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      await ignoreDiscoveredBond(candidateId);
      await loadCandidates(lastDiscoveryRun?.id || null);

      setSuccessMessage("Candidate ignored.");
    } catch (error) {
      setErrorMessage(
        getApiErrorMessage(error, "Could not ignore candidate.")
      );
    } finally {
      setCandidateActionId(null);
    }
  }

  return (
    <section className="page-section">
      <div className="page-header page-header-with-actions">
        <div>
          <h1>Discover Bonds</h1>
          <p>
            Find active bond candidates from CSV import or AI Research and add
            them to your Watchlist for further analysis.
          </p>
        </div>

        <div className="portfolio-header-actions">
          <Link className="secondary-button" to="/watchlist">
            My Watchlist
          </Link>
        </div>
      </div>

      <div className="disclaimer-box">
        Discovery candidates are educational analytical data only. They are not
        investment advice and they do not represent a recommendation to buy or
        sell securities.
      </div>

      <ProviderStatusSection
        providerStatus={providerStatus}
        isExpanded={isProviderStatusExpanded}
        isLoading={isLoadingProviderStatus}
        onRefresh={loadProviderStatus}
        onToggle={() => setIsProviderStatusExpanded((current) => !current)}
      />

      <DiscoveryFiltersSection
        filters={filters}
        onFilterChange={handleFilterChange}
        onCheckboxFilterChange={handleCheckboxFilterChange}
        onCheckboxFilterClear={handleCheckboxFilterClear}
      />

      {isAIResearchSource ? (
        <AIResearchProviderSection
          isGenerating={isGeneratingAIResearchJson}
          isImporting={isImportingAIResearchJson}
          generatedJsonText={aiResearchJsonText}
          qualityWarnings={aiQualityWarnings}
          lastImport={lastAIResearchImport}
        />
      ) : (
        <CSVProviderSection
          selectedCsvFile={selectedCsvFile}
          lastCsvUpload={lastCsvUpload}
          isUploadingCsv={isUploadingCsv}
          onCsvFileChange={handleCsvFileChange}
          onDownloadCsvTemplate={handleDownloadCsvTemplate}
          onUploadCsv={handleUploadCsv}
        />
      )}

      <div className="toolbar-card discovery-action-card">
        <div className="form-actions">
          <button
            type="button"
            className="primary-button"
            onClick={handleDiscover}
            disabled={isDiscovering}
          >
            {getDiscoveryButtonLabel({
              isAIResearchSource,
              isGeneratingAIResearchJson,
              isImportingAIResearchJson,
              isRunningDiscovery,
            })}
          </button>

          <button
            type="button"
            className="secondary-button"
            onClick={handleResetFilters}
            disabled={isDiscovering}
          >
            Reset
          </button>
        </div>

        <p className="helper-text">
          The backend filters matured bonds, ratings below the selected minimum,
          duplicate ISINs, and bonds already active in your Portfolio or
          Watchlist.
        </p>
      </div>

      {errorMessage && <div className="error-box">{errorMessage}</div>}
      {successMessage && <div className="success-box">{successMessage}</div>}

      {lastDiscoveryRun && (
        <div className="summary-card-grid">
          <DiscoveryRunCard title="Found" value={lastDiscoveryRun.total_found} />
          <DiscoveryRunCard title="Saved" value={lastDiscoveryRun.total_saved} />
          <DiscoveryRunCard
            title="Skipped"
            value={lastDiscoveryRun.total_skipped}
          />
          <DiscoveryRunCard
            title="Status"
            value={lastDiscoveryRun.status_label || lastDiscoveryRun.status}
          />
        </div>
      )}

      <CandidateBondsTable
        candidates={candidates}
        isLoading={isLoading}
        isClearingResults={isClearingResults}
        isDiscovering={isDiscovering}
        candidateActionId={candidateActionId}
        onClearCurrentResults={handleClearCurrentResults}
        onAddToWatchlist={handleAddToWatchlist}
        onIgnore={handleIgnore}
      />
    </section>
  );
}

function ProviderStatusSection({
  providerStatus,
  isExpanded,
  isLoading,
  onRefresh,
  onToggle,
}) {
  return (
    <div className={`toolbar-card collapsible-card ${isExpanded ? "is-open" : ""}`}>
      <div className="section-header section-header-with-actions">
        <div>
          <h2>Provider Status</h2>
          <p>
            Status for CSV Provider and AI Research Provider.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button icon-button"
          onClick={onToggle}
          aria-expanded={isExpanded}
        >
          {isExpanded ? "▲" : "▼"}
        </button>
      </div>

      {isExpanded && (
        <>
          <div className="form-actions compact-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={onRefresh}
              disabled={isLoading}
            >
              {isLoading ? "Refreshing..." : "Refresh Status"}
            </button>
          </div>

          {!providerStatus ? (
            <p className="helper-text">Provider status is not available yet.</p>
          ) : (
            <>
              <p className="helper-text">
                Default source: {providerStatus.default_source}. Supported
                sources: {providerStatus.supported_sources?.join(", ")}.
              </p>

              <div className="summary-card-grid">
                {providerStatus.providers?.map((provider) => (
                  <ProviderStatusCard
                    provider={provider}
                    key={provider.source}
                  />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function ProviderStatusCard({ provider }) {
  const configuration = provider.configuration || {};

  return (
    <div className="summary-card">
      <span>{provider.label}</span>

      <strong>{provider.available ? "Available" : "Needs attention"}</strong>

      <p className="helper-text">Mode: {provider.mode}</p>
      <p className="helper-text">{provider.detail}</p>

      {provider.file_name && (
        <p className="helper-text">File: {provider.file_name}</p>
      )}

      {provider.candidate_count !== null &&
        provider.candidate_count !== undefined && (
          <p className="helper-text">
            Candidates: {provider.candidate_count}
          </p>
        )}

      {configuration.backend_calculates_missing_ytm_duration && (
        <p className="helper-text">
          Backend calculates missing YTM/duration when price, coupon and
          maturity exist.
        </p>
      )}
    </div>
  );
}

function DiscoveryFiltersSection({
  filters,
  onFilterChange,
  onCheckboxFilterChange,
  onCheckboxFilterClear,
}) {
  return (
    <div className="toolbar-card">
      <div className="section-header">
        <div>
          <h2>Discovery Filters</h2>
          <p>
            Choose source, minimum rating, currencies, countries and bond types.
            Leave a checkbox group empty to include all values in that group.
          </p>
        </div>
      </div>

      <div className="form-grid discovery-main-filter-grid">
        <label>
          Source
          <select
            name="source"
            value={filters.source}
            onChange={onFilterChange}
          >
            {SOURCE_OPTIONS.map((source) => (
              <option value={source.value} key={source.value}>
                {source.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Minimum Rating
          <select
            name="minRating"
            value={filters.minRating}
            onChange={onFilterChange}
          >
            {MINIMUM_RATING_OPTIONS.map((rating) => (
              <option value={rating} key={rating}>
                {rating}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="checkbox-filter-grid">
        <CheckboxFilterGroup
          title="Currency"
          allLabel="All currencies"
          options={CURRENCY_OPTIONS}
          selectedValues={filters.currencies}
          onChange={(optionValue, isChecked) =>
            onCheckboxFilterChange("currencies", optionValue, isChecked)
          }
          onClear={() => onCheckboxFilterClear("currencies")}
        />

        <CheckboxFilterGroup
          title="Country"
          allLabel="All countries"
          options={COUNTRY_OPTIONS}
          selectedValues={filters.countries}
          onChange={(optionValue, isChecked) =>
            onCheckboxFilterChange("countries", optionValue, isChecked)
          }
          onClear={() => onCheckboxFilterClear("countries")}
        />

        <CheckboxFilterGroup
          title="Bond Type"
          allLabel="All bond types"
          options={BOND_TYPE_OPTIONS}
          selectedValues={filters.bondTypes}
          onChange={(optionValue, isChecked) =>
            onCheckboxFilterChange("bondTypes", optionValue, isChecked)
          }
          onClear={() => onCheckboxFilterClear("bondTypes")}
        />
      </div>
    </div>
  );
}

function CheckboxFilterGroup({
  title,
  allLabel,
  options,
  selectedValues,
  onChange,
  onClear,
}) {
  const activeValues = selectedValues || [];
  const isAllSelected = activeValues.length === 0;

  return (
    <fieldset className="checkbox-filter-group">
      <legend>{title}</legend>

      <label className={`checkbox-pill ${isAllSelected ? "is-selected" : ""}`}>
        <input
          type="checkbox"
          checked={isAllSelected}
          onChange={onClear}
        />
        {allLabel}
      </label>

      <div className="checkbox-pill-list">
        {options.map((option) => {
          const isSelected = activeValues.includes(option.value);

          return (
            <label
              className={`checkbox-pill ${isSelected ? "is-selected" : ""}`}
              key={option.value}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={(event) =>
                  onChange(option.value, event.target.checked)
                }
              />
              {option.label}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

function CSVProviderSection({
  selectedCsvFile,
  lastCsvUpload,
  isUploadingCsv,
  onCsvFileChange,
  onDownloadCsvTemplate,
  onUploadCsv,
}) {
  return (
    <div className="toolbar-card">
      <div className="section-header">
        <div>
          <h2>CSV Provider</h2>
          <p>
            Upload a CSV file to replace the local CSV bond universe. Then
            press Discovery.
          </p>
        </div>
      </div>

      <div className="form-grid">
        <label>
          CSV File
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={onCsvFileChange}
          />
        </label>

        <label>
          Selected File
          <input
            type="text"
            value={selectedCsvFile?.name || "No file selected"}
            readOnly
          />
        </label>
      </div>

      <div className="form-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={onDownloadCsvTemplate}
        >
          Download CSV Template
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={onUploadCsv}
          disabled={isUploadingCsv || !selectedCsvFile}
        >
          {isUploadingCsv ? "Uploading..." : "Upload CSV"}
        </button>
      </div>

      {lastCsvUpload && (
        <p className="helper-text">
          Uploaded rows: {lastCsvUpload.row_count}. Stored as CSV Provider
          universe.
        </p>
      )}
    </div>
  );
}

function AIResearchProviderSection({
  isGenerating,
  isImporting,
  generatedJsonText,
  qualityWarnings,
  lastImport,
}) {
  return (
    <div className="toolbar-card">
      <div className="section-header">
        <div>
          <h2>AI Research Provider</h2>
          <p>
            Press Discovery to search the web through Puter.js, generate
            structured JSON, import it into Django and display valid candidates.
          </p>
        </div>
      </div>

      <div className="warning-box">
        AI-researched data is not an official live market feed. The backend
        validates the JSON and calculates missing YTM/duration only when
        market price, coupon and maturity exist.
      </div>

      {(isGenerating || isImporting) && (
        <div className="loading-text">
          {isGenerating
            ? "AI Research Agent is searching for active bonds..."
            : "Backend is validating and importing AI research results..."}
        </div>
      )}

      {qualityWarnings.length > 0 && (
        <div className="warning-box">
          <strong>Quality warnings:</strong>
          <ul>
            {qualityWarnings.map((warning, index) => (
              <li key={`${warning}-${index}`}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {lastImport && (
        <div className="summary-card-grid">
          <DiscoveryRunCard title="Found" value={lastImport.total_found} />
          <DiscoveryRunCard title="Created" value={lastImport.total_created} />
          <DiscoveryRunCard title="Updated" value={lastImport.total_updated} />
          <DiscoveryRunCard title="Skipped" value={lastImport.total_skipped} />
        </div>
      )}

      {lastImport?.errors?.length > 0 && (
        <div className="error-box">
          <strong>Import errors:</strong>
          <ul>
            {lastImport.errors.map((error, index) => (
              <li key={`${error}-${index}`}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {generatedJsonText && (
        <details className="json-details">
          <summary>Generated AI JSON</summary>
          <textarea value={generatedJsonText} rows="10" readOnly />
        </details>
      )}
    </div>
  );
}

function CandidateBondsTable({
  candidates,
  isLoading,
  isClearingResults,
  isDiscovering,
  candidateActionId,
  onClearCurrentResults,
  onAddToWatchlist,
  onIgnore,
}) {
  return (
    <div className="table-card">
      <div className="section-header section-header-with-actions">
        <div>
          <h2>Candidate Bonds</h2>
          <p>
            Active candidates that passed backend validation and are not already
            in your Portfolio or Watchlist.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={onClearCurrentResults}
          disabled={
            isClearingResults ||
            isDiscovering ||
            candidates.length === 0
          }
        >
          {isClearingResults ? "Clearing..." : "Clear Current Results"}
        </button>
      </div>

      {isLoading ? (
        <div className="loading-text">Loading discovered bonds...</div>
      ) : (
        <div className="table-scroll candidate-table-scroll">
          <table className="wide-table candidate-bonds-table">
            <thead>
              <tr>
                <th>Bond</th>
                <th>ISIN</th>
                <th>Country</th>
                <th>Issuer</th>
                <th>Currency</th>
                <th>Rating</th>
                <th>Maturity</th>
                <th>Coupon</th>
                <th>Market Price</th>
                <th>YTM</th>
                <th>Duration</th>
                <th>Source</th>
                <th>Confidence</th>
                <th>Review</th>
                <th>Risk</th>
                <th>Signal</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {candidates.length === 0 ? (
                <tr>
                  <td colSpan="17">
                    No candidates are available. Adjust filters, upload CSV or
                    run AI Research Provider.
                  </td>
                </tr>
              ) : (
                candidates.map((candidate) => (
                  <tr key={candidate.id}>
                    <td className="candidate-name-cell">{candidate.name}</td>
                    <td className="candidate-isin-cell">{candidate.isin}</td>
                    <td>{candidate.country || "-"}</td>
                    <td className="candidate-issuer-cell">
                      {candidate.issuer}
                    </td>
                    <td>{candidate.currency}</td>
                    <td>{candidate.credit_rating}</td>
                    <td>{candidate.maturity_date}</td>
                    <td>{formatPercent(candidate.coupon_rate, 3)}</td>

                    <td>
                      {candidate.market_price
                        ? formatMoney(
                            candidate.market_price,
                            candidate.currency,
                            4
                          )
                        : "-"}
                    </td>

                    <td>{formatPercent(candidate.ytm, 2)}</td>
                    <td>{formatDecimal(candidate.duration, 4)}</td>

                    <td className="candidate-source-cell">
                      <CandidateSource candidate={candidate} />
                    </td>

                    <td>
                      {candidate.confidence_label ||
                        candidate.confidence ||
                        "-"}
                    </td>

                    <td>
                      {candidate.review_status_label ||
                        candidate.review_status ||
                        "-"}
                    </td>

                    <td className="candidate-risk-cell">
                      <RiskBadge
                        riskLevel={candidate.preview_risk_level}
                        label={candidate.preview_risk_label}
                      />
                    </td>

                    <td className="candidate-signal-cell">
                      <SignalBadge
                        signal={candidate.preview_signal}
                        label={candidate.preview_signal_label}
                      />
                    </td>

                    <td>
                      <div className="table-action-buttons">
                        <button
                          type="button"
                          className="primary-button small-button"
                          disabled={candidateActionId === candidate.id}
                          onClick={() => onAddToWatchlist(candidate.id)}
                        >
                          {candidateActionId === candidate.id
                            ? "Adding..."
                            : "Add"}
                        </button>

                        <button
                          type="button"
                          className="secondary-button small-button"
                          disabled={candidateActionId === candidate.id}
                          onClick={() => onIgnore(candidate.id)}
                        >
                          Ignore
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function CandidateSource({ candidate }) {
  const dataOrigin =
    candidate.data_origin_label || candidate.data_origin || candidate.source;

  if (!candidate.source_url) {
    return (
      <>
        <div>{candidate.source || "-"}</div>
        <small>{dataOrigin || "-"}</small>
      </>
    );
  }

  return (
    <>
      <a href={candidate.source_url} target="_blank" rel="noreferrer">
        {candidate.source || "Open source"}
      </a>
      <br />
      <small>{dataOrigin || "-"}</small>
    </>
  );
}

function DiscoveryRunCard({ title, value }) {
  return (
    <div className="summary-card">
      <span>{title}</span>
      <strong>{value ?? "-"}</strong>
    </div>
  );
}

function buildCsvTemplateContent() {
  /**
   * Build a CSV template file with headers and example rows.
   */
  const rows = [CSV_TEMPLATE_COLUMNS, ...CSV_TEMPLATE_ROWS];

  return rows.map((row) => row.map(escapeCsvValue).join(",")).join("\n");
}

function escapeCsvValue(value) {
  /**
   * Escape one value for safe CSV output.
   */
  const stringValue = String(value ?? "");

  if (
    stringValue.includes(",") ||
    stringValue.includes('"') ||
    stringValue.includes("\n")
  ) {
    return `"${stringValue.replaceAll('"', '""')}"`;
  }

  return stringValue;
}

function buildAIQualityWarnings(payload) {
  /**
   * Build client-side quality warnings before backend import.
   */
  const warnings = [];
  const items = Array.isArray(payload?.items) ? payload.items : [];

  items.forEach((item, index) => {
    const itemLabel = item?.isin || item?.name || `Item ${index + 1}`;
    const missingFields = Array.isArray(item?.missing_fields)
      ? item.missing_fields
      : [];

    if (!item?.market_price) {
      warnings.push(`${itemLabel}: missing market_price.`);
    }

    if (!item?.credit_rating) {
      warnings.push(`${itemLabel}: missing credit_rating.`);
    }

    if (!item?.primary_source_url) {
      warnings.push(`${itemLabel}: missing primary_source_url.`);
    }

    if (missingFields.length > 3) {
      warnings.push(`${itemLabel}: has more than 3 missing fields.`);
    }
  });

  return warnings.slice(0, 12);
}

function getDiscoveryButtonLabel({
  isAIResearchSource,
  isGeneratingAIResearchJson,
  isImportingAIResearchJson,
  isRunningDiscovery,
}) {
  /**
   * Return the main Discovery button label.
   */
  if (isAIResearchSource) {
    if (isGeneratingAIResearchJson) {
      return "Searching...";
    }

    if (isImportingAIResearchJson) {
      return "Importing...";
    }

    return "Discovery";
  }

  if (isRunningDiscovery) {
    return "Running...";
  }

  return "Discovery";
}

function getApiErrorMessage(error, fallbackMessage) {
  /**
   * Extract a safe API or client-side error message for user-facing alerts.
   */
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.non_field_errors?.[0] ||
    error?.message ||
    fallbackMessage
  );
}

export default DiscoverBondsPage;
