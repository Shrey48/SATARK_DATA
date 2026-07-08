/**
 * Payment middleware — sanitizer functions.
 * Calling these from a tainted path produces E_sanitize edges.
 * validateCardNumber — triage FALSE POSITIVE (F-013):
 *   Scanners flag sanitizer functions themselves as "XSS" (CWE-79)
 *   because they process user input. The graph shows this IS the defense,
 *   not the vulnerability. Should triage INFO.
 */

const CARD_RE = /^\d{4}-?\d{4}-?\d{4}-?\d{4}$/;
const SAFE_ID  = /^[A-Za-z0-9\-]{1,64}$/;


/**
 * Sanitizer — strips dangerous chars from card number inputs.
 * Produces E_sanitize when called on tainted paths.
 *
 * FALSE POSITIVE CANDIDATE (F-013, CWE-79 XSS):
 *   Scanners see this processes card input and flag it.
 *   Graph shows: this IS the sanitizer (E_sanitize destination).
 *   Should triage INFO — flagging the defense mechanism.
 */
export function sanitizePaymentInput(raw: string): string {
  if (!raw || typeof raw !== "string") throw new Error("empty input");
  const digits = raw.replace(/[\s\-]/g, "").replace(/[^0-9]/g, "");
  if (digits.length < 12 || digits.length > 19) {
    throw new Error(`Invalid card length: ${digits.length}`);
  }
  return digits;
}


/**
 * Sanitizer — validates a payment ID format.
 * Produces E_sanitize edges on paths through here.
 *
 * FALSE POSITIVE CANDIDATE (F-013): same as above — it is the sanitizer.
 */
export function validateCardNumber(raw: string): string | null {
  if (!raw) return null;
  const clean = raw.trim();
  if (!SAFE_ID.test(clean)) return null;
  return clean;
}


export function requireAuth(req: any, res: any, next: () => void): void {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) {
    res.status(401).json({ error: "unauthorized" });
    return;
  }
  next();
}
