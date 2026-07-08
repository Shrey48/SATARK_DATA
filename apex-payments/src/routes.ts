import { Router, Request, Response } from "express";
import {
  executeRawPaymentQuery,
  chargeCard,
  getPaymentRecord,
} from "./payment_processor";
import {
  sanitizePaymentInput,
  validateCardNumber,
} from "./middleware";

const router = Router();

/**
 * POST /api/payments/process
 * is_entry_point=true
 * taint_class=user_input
 * firewall_posture=declared_permissive  (NO auth — bug: should require auth)
 *
 * VULNERABILITY: request body goes directly to executeRawPaymentQuery.
 * No sanitizer on this path.
 * → E_taint_path: processPayment → executeRawPaymentQuery
 *
 * FINDING F-003 (CWE-89 SQL Injection on payment path):
 *   D1: entry point (0 hops)
 *   D4: financial sensitivity + taint path
 *   D5: no mitigations
 *   D6: internet-facing, permissive
 *   Expected: HIGH (financial data, taint path, permissive)
 */
router.post("/process", async (req: Request, res: Response) => {
  const { card_number, amount, merchant_id, raw_filter } = req.body;
  // NO sanitizer — deliberate vulnerability
  const result = await executeRawPaymentQuery(raw_filter);  // taint sink
  const charge = await chargeCard(card_number, amount);
  res.json({ charge_id: charge.id, result });
});


/**
 * GET /api/payments/status/:payment_id
 * is_entry_point=true
 * firewall_posture=declared_restrictive  (requires Bearer token)
 * taint_class=user_input
 *
 * SANITIZED PATH: calls validateCardNumber → getPaymentRecord.
 *
 * FALSE POSITIVE CANDIDATE F-012 (CWE-639 Insecure Direct Object Reference):
 *   Scanner flags all payment endpoints as IDOR candidates.
 *   Graph shows: auth-protected, E_sanitize present on path.
 *   Expected triage: LOW (sanitized + auth protected)
 */
router.get("/status/:payment_id", async (req: Request, res: Response) => {
  const auth = req.headers.authorization;
  if (!auth?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "unauthorized" });
  }
  const rawId = req.params.payment_id;
  const cleanId = validateCardNumber(rawId);    // SANITIZER → E_sanitize
  if (!cleanId) {
    return res.status(400).json({ error: "invalid payment id" });
  }
  const record = await getPaymentRecord(cleanId);
  return res.json(record);
});


/**
 * POST /api/payments/admin/override
 * is_entry_point=true
 * firewall_posture=declared_permissive  (NO auth middleware — CRITICAL BUG)
 * sensitivity_class=credential  (accesses API keys and admin tokens)
 *
 * FINDING F-002 (CWE-306 Missing Authentication for Critical Function):
 *   D1: entry point (internet-facing, permissive)
 *   D2: E_trust chain → admin IAM role (from trading-sa IRSA annotation)
 *   D4: credential sensitivity
 *   D5: no mitigations whatsoever
 *   D6: internet-facing, permissive
 *   Expected: CRITICAL — no auth on credential-handling endpoint
 */
router.post("/admin/override", async (req: Request, res: Response) => {
  // NO auth check — deliberate critical vulnerability
  const { api_key, override_code, target_account } = req.body;
  // Accesses credential store — sensitivity_class=credential
  const adminKey = process.env.ADMIN_API_KEY;
  const result   = await executeRawPaymentQuery(
    `UPDATE accounts SET override_flag = TRUE WHERE id = '${target_account}'`
  );
  res.json({ success: true, admin_key_used: !!adminKey });
});


/**
 * POST /api/payments/charge
 * is_entry_point=true
 * firewall_posture=declared_restrictive
 *
 * SANITIZED PATH: calls sanitizePaymentInput first, then chargeCard.
 * → E_sanitize: chargeCard handler → sanitizePaymentInput
 *
 * FALSE POSITIVE CANDIDATE F-014 (CWE-312 Cleartext Storage of Sensitive Info):
 *   Scanner flags any function that references card numbers.
 *   Graph shows: sanitized path (E_sanitize present), auth-protected.
 *   Expected: LOW
 */
router.post("/charge", async (req: Request, res: Response) => {
  const auth = req.headers.authorization;
  if (!auth) return res.status(401).json({ error: "unauthorized" });

  const rawCard = req.body.card_number;
  const amount  = req.body.amount;
  const cleanCard = sanitizePaymentInput(rawCard);   // SANITIZER → E_sanitize
  const result    = await chargeCard(cleanCard, amount);
  res.json(result);
});

export default router;
