export type PaymentStatus =
  | 'pending'
  | 'authorized'
  | 'captured'
  | 'failed'
  | 'refunded';

export type PaymentMethod = 'card' | 'wallet' | 'bank_transfer';

export interface PaymentRequest {
  paymentId: string;
  orderId: string;
  amountCents: number;
  currency: string;
  method: PaymentMethod;
}

export interface PaymentResult {
  success: boolean;
  paymentId: string;
  message: string;
  transactionRef?: string;
}

export interface InventoryItem {
  sku: string;
  quantity: number;
  reservedQuantity: number;
  lastUpdated: string;
}

export interface OrderSummary {
  orderId: string;
  customerId: string;
  totalCents: number;
  status: string;
  placedAt: string;
}
