/**
 * Client Portal — Express Routes.
 *
 * BUG B TEST: ALL handlers are anonymous arrow functions.
 * Format: router.post('/path', async (req, res) => { ... })
 *
 * Current parser behaviour: routes.ts → 1 file node, 0 function nodes.
 * After Bug B fix: each arrow handler must produce a synthesised function
 * node with stable ID (file + line + route-path) and is_entry_point=true.
 *
 * FINDINGS targeting this file are currently all ORPHAN.
 * After Bug B fix: they should anchor and score HIGH/CRITICAL/LOW.
 */
import { Router } from 'express';
import { verifyToken, sanitizePortfolioId } from './middleware';
import { LambdaClient } from './services/client';

const router = Router();
const lambdaClient = new LambdaClient();


/**
 * POST /api/client/orders/submit
 * BUG B: arrow function — currently 0 nodes.
 * NO auth middleware. req.body.rawFilter sent directly to Lambda (taint path).
 * firewall_posture=declared_permissive
 *
 * FINDING F-002 (CWE-89): ORPHAN now, CRITICAL after Bug B fix.
 * D1=1.0 (entry), D6=1.0 (permissive), D4=0.8 (taint+financial), D5=1.0
 */
router.post('/orders/submit', async (req, res) => {
  const { rawFilter, symbol, quantity } = req.body;
  // NO sanitizer — deliberate vulnerability: rawFilter taint flows to Lambda
  const result = await lambdaClient.invokeOrderProcessor({ rawFilter, symbol, quantity });
  res.json(result);
});


/**
 * GET /api/client/portfolio
 * BUG B: arrow function — currently 0 nodes.
 * Uses verifyToken middleware + sanitizePortfolioId.
 *
 * FINDING F-006 (CWE-639 IDOR FP): scanner flags. Has auth + sanitizer.
 * After Bug B fix: should score LOW (D5=0.5 sanitized, D6=0.6 protected).
 */
router.get('/portfolio', verifyToken, async (req, res) => {
  const rawId = req.query.portfolio_id as string;
  const cleanId = sanitizePortfolioId(rawId);           // E_sanitize
  const data = await lambdaClient.getPortfolioData(cleanId);
  res.json(data);
});


/**
 * POST /api/client/admin/reset
 * BUG B: arrow function — currently 0 nodes.
 * NO auth middleware. Accesses admin_key from env. CRITICAL VULNERABILITY.
 * sensitivity_class=credential
 *
 * FINDING F-016 (CWE-306): ORPHAN now, CRITICAL after Bug B fix.
 * D1=1.0, D6=1.0 (permissive), D4=1.0 (credential sensitivity), D5=1.0
 */
router.post('/admin/reset', (req, res) => {
  // NO auth guard — deliberate critical vulnerability
  const { targetAccount, adminCode } = req.body;
  const adminKey = process.env.MERIDIAN_ADMIN_KEY;    // credential access
  res.json({ reset: true, account: targetAccount, auth: !!adminKey });
});


/**
 * GET /api/client/health
 * BUG B: arrow function — currently 0 nodes.
 * BUG G: returns ONLY {"status":"ok"} — no PII, no financial data.
 * sensitivity_class=none
 *
 * FINDING F-019 (health check probe): After Bug B fix, should anchor
 * and score INFO (D4=0.3 no sensitivity despite D1=1.0, D6=1.0).
 */
router.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'client-portal', version: '4.1.0' });
});

export default router;
