/**
 * Core payment processing.
 * executeRawPaymentQuery — has_raw_query=true TAINT SINK
 * chargeCard             — called from sanitized path only (after sanitizePaymentInput)
 * getPaymentRecord       — safe DynamoDB read
 */
import { LambdaClient, InvokeCommand } from "@aws-sdk/client-lambda";

const lambda = new LambdaClient({ region: "us-east-1" });


/**
 * TAINT SINK — has_raw_query=true
 * Executes a raw SQL query against the payments database.
 * Called UNSANITIZED from processPayment → E_taint_path
 * Called via adminOverride with literal string concatenation → E_taint_path
 * sensitivity_class: financial (accesses payment records)
 */
export async function executeRawPaymentQuery(rawQuery: string): Promise<any[]> {
  // VULNERABLE: rawQuery is injected directly without parameterization
  const result = await lambda.send(new InvokeCommand({
    FunctionName: "apex-payment-db-proxy",  // literal → cross-asset invoke
    Payload: Buffer.from(JSON.stringify({ sql: rawQuery })),
  }));
  return JSON.parse(Buffer.from(result.Payload!).toString());
}


/**
 * Charges a card via the payment processor Lambda.
 * Called ONLY from the /charge route which calls sanitizePaymentInput first.
 * pc_sanitization: sanitized (sanitizer upstream)
 * sensitivity_class: financial
 */
export async function chargeCard(cleanCardNum: string, amount: number): Promise<{ id: string; status: string }> {
  const result = await lambda.send(new InvokeCommand({
    FunctionName: "apex-payment-processor",   // literal
    Payload: Buffer.from(JSON.stringify({ card: cleanCardNum, amount })),
  }));
  return JSON.parse(Buffer.from(result.Payload!).toString());
}


/**
 * Reads a payment record from the data store.
 * Called from getPaymentStatus which validates the ID first.
 * pc_sanitization: sanitized (upstream validateCardNumber called)
 * sensitivity_class: financial
 */
export async function getPaymentRecord(cleanId: string): Promise<object> {
  const result = await lambda.send(new InvokeCommand({
    FunctionName: "apex-payment-db-proxy",
    Payload: Buffer.from(JSON.stringify({ action: "get", id: cleanId })),
  }));
  return JSON.parse(Buffer.from(result.Payload!).toString());
}
