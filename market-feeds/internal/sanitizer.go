package internal

import (
	"fmt"
	"regexp"
	"strings"
)

var (
	symbolRe = regexp.MustCompile(`^[A-Z]{1,5}$`)
	feedIDRe = regexp.MustCompile(`^FEED-[A-Z0-9]{8}$`)
)

// SanitizeSymbol validates and cleans a market ticker symbol.
// Produces E_sanitize edges on paths through this function.
// Called from GetFeedStatus before any DB access.
func SanitizeSymbol(raw string) (string, error) {
	clean := strings.ToUpper(strings.TrimSpace(raw))
	if !symbolRe.MatchString(clean) {
		return "", fmt.Errorf("invalid symbol: %q", raw)
	}
	return clean, nil
}

// ValidateFeedID validates a feed identifier format.
// Also used as a sanitizer for feed-level operations.
func ValidateFeedID(raw string) (string, error) {
	clean := strings.ToUpper(strings.TrimSpace(raw))
	if !feedIDRe.MatchString(clean) {
		return "", fmt.Errorf("invalid feed id: %q", raw)
	}
	return clean, nil
}
