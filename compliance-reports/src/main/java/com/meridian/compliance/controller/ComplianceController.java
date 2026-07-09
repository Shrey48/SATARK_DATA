package com.meridian.compliance.controller;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import com.meridian.compliance.service.ComplianceService;

/**
 * Meridian Compliance Reporting Controller.
 *
 * BUG C TEST: All 4 public endpoints have @GetMapping or @PostMapping
 * directly on the method. After Bug C fix ALL should have is_entry_point=true.
 *
 * This service is NOT in the K8s Ingress (internal-only compliance service).
 * D6 should be 0.1 (internal) after fix, NOT 1.0.
 * Expected post-fix scores: HIGH (KEV CVEs) not CRITICAL (internal).
 *
 * CVE-2021-44228 (Log4Shell): logger.info() with user-supplied input
 * CVE-2022-22965 (Spring4Shell): DataBinder on this endpoint
 */
@RestController
@RequestMapping("/internal/v2/compliance")
public class ComplianceController {

    private static final Logger logger = LogManager.getLogger(ComplianceController.class);
    private final ComplianceService complianceService;

    public ComplianceController(ComplianceService complianceService) {
        this.complianceService = complianceService;
    }

    /**
     * GET /internal/v2/compliance/report?period=2026-Q2&format=pdf
     *
     * BUG C: @GetMapping on method — currently is_entry_point=null.
     * After fix: is_entry_point=true, taint_class=user_input.
     *
     * CVE-2021-44228: period param logged via log4j 2.14.1 (Log4Shell).
     * LAZARUS-GROUP targets this CVE in financial systems.
     *
     * FINDING F-003 (CVE-2021-44228):
     *   Pre-fix:  LOW (D1=0.1, D6=0.1 — not entry point)
     *   Post-fix: HIGH (D1=1.0, D3=1.0 KEV, D7=1.0 LAZARUS, D6=0.1 internal)
     */
    @GetMapping("/report")
    public ResponseEntity<?> generateComplianceReport(
            @RequestParam String period,
            @RequestParam(defaultValue = "json") String format,
            @RequestHeader(value = "X-Internal-Token", required = false) String token) {

        if (token == null || token.isBlank()) {
            return ResponseEntity.status(403).body("missing internal token");
        }
        // CVE-2021-44228 TRIGGER: user-supplied period logged via log4j 2.14.1
        logger.info("Generating compliance report for period: {}", period);  // Log4Shell
        var result = complianceService.buildComplianceReport(period, format);
        return ResponseEntity.ok(result);
    }

    /**
     * POST /internal/v2/compliance/upload
     *
     * BUG C: @PostMapping on method — currently is_entry_point=null.
     * After fix: is_entry_point=true.
     *
     * FINDING F-007 (CWE-22 Path Traversal):
     *   uploadPath validated for extension but not ../ sequences.
     *   Post-fix: MEDIUM (entry point, internal, partial mitigation).
     */
    @PostMapping("/upload")
    public ResponseEntity<?> uploadRegulatoryReport(
            @RequestParam String uploadPath,
            @RequestBody byte[] reportData,
            @RequestHeader(value = "X-Internal-Token", required = false) String token) {

        if (token == null) return ResponseEntity.status(403).body("unauthorized");
        // Partial validation — extension check only, no path traversal check
        if (!uploadPath.endsWith(".pdf") && !uploadPath.endsWith(".csv")) {
            return ResponseEntity.badRequest().body("unsupported format");
        }
        // VULNERABILITY: no normalization — ../../../etc/passwd.pdf possible
        complianceService.storeReport(uploadPath, reportData);
        return ResponseEntity.ok("stored: " + uploadPath);
    }

    /**
     * POST /internal/v2/compliance/raw-query
     *
     * BUG C: @PostMapping on method — currently is_entry_point=null.
     * After fix: is_entry_point=true, taint_class=user_input.
     *
     * TAINT PATH: rawQuery → ComplianceDAO.executeRawQuery (has_raw_query=true)
     * No sanitizer on this path.
     *
     * BUG H PROBE: E_taint_path edge count for executeRawQuery should = 1.
     * Mode 2 must report exactly 1 structural taint path.
     *
     * FINDING F-004 (CWE-89 SQL Injection):
     *   Pre-fix:  LOW (D1=0.1, not entry point)
     *   Post-fix: HIGH (D1=1.0, D4=0.8 taint+financial, internal D6=0.1)
     */
    @PostMapping("/raw-query")
    public ResponseEntity<?> executeRawReport(
            @RequestBody String rawQuery,
            @RequestHeader(value = "X-Internal-Token", required = false) String token) {

        if (token == null) return ResponseEntity.status(403).body("unauthorized");
        // NO sanitizer — deliberate vulnerability
        logger.info("Executing raw compliance query");
        var result = complianceService.executeRawReport(rawQuery);  // taint → sink
        return ResponseEntity.ok(result);
    }

    /**
     * GET /internal/v2/compliance/healthz
     *
     * BUG C: @GetMapping on method — currently is_entry_point=null.
     * BUG G: Returns ONLY {"status":"ok"} — must NOT get sensitivity_class=pii.
     *
     * FINDING F-009 (health check probe): After Bug C fix, entry=True
     * but D4=0.3 (sensitivity=none) should keep score at INFO/LOW.
     */
    @GetMapping("/healthz")
    public ResponseEntity<?> healthz() {
        return ResponseEntity.ok(
            java.util.Map.of("status", "ok", "service", "compliance-reports", "version", "2.4.1")
        );
    }
}
