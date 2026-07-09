package internal

import (
	"encoding/json"
	"net/http"
)

// FeedHandler handles HTTP requests for market feed data.
type FeedHandler struct {
	repo *FeedRepository
}

// NewFeedHandler creates a handler bound to a repository.
func NewFeedHandler(repo *FeedRepository) *FeedHandler {
	return &FeedHandler{repo: repo}
}

// GetMarketData handles GET /api/feeds?filter=<user_input>
// is_entry_point=true, taint_class=user_input
// firewall_posture=declared_permissive (no auth check)
//
// TAINT PATH: r.URL.Query().Get("filter") → QueryRawFeed (has_raw_query=true)
// NO sanitizer on this path.
//
// FINDING F-005 (CWE-89 SQL/NoSQL Injection in Go handler):
// Expected: HIGH (entry point, taint path, financial data, permissive).
// This tests Go language taint path extraction.
func (h *FeedHandler) GetMarketData(w http.ResponseWriter, r *http.Request) {
	rawFilter := r.URL.Query().Get("filter")  // taint source: user-controlled

	// NO sanitizer — deliberate vulnerability
	feeds, err := h.repo.QueryRawFeed(rawFilter)  // taint SINK
	if err != nil {
		http.Error(w, "query failed", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(feeds)
}

// GetFeedStatus handles GET /api/feeds/status?symbol=<ticker>
// is_entry_point=true
// SANITIZED PATH: SanitizeSymbol called before GetFeedBySafe.
// → E_sanitize: GetFeedStatus → SanitizeSymbol
//
// FINDING F-014 (CWE-89 FP on Go sanitized path):
// Scanner flags DB access but symbol is sanitized. Expected: LOW.
func (h *FeedHandler) GetFeedStatus(w http.ResponseWriter, r *http.Request) {
	if r.Header.Get("Authorization") == "" {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	rawSymbol := r.URL.Query().Get("symbol")
	cleanSymbol, err := SanitizeSymbol(rawSymbol)  // SANITIZER → E_sanitize
	if err != nil {
		http.Error(w, "invalid symbol", http.StatusBadRequest)
		return
	}
	feed, err := h.repo.GetFeedBySafe(cleanSymbol)  // safe parameterized
	if err != nil {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(feed)
}

// GetHealth handles GET /api/feeds/health
// is_entry_point=true
// BUG G PROBE: returns ONLY {"status":"ok"} — no data access, no auth.
// sensitivity_class=none — must NOT be classified pii.
func (h *FeedHandler) GetHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"service": "market-feeds",
	})
}
