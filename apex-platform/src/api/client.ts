import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { PaymentRequest, PaymentResult, InventoryItem } from './types';

export class ApexApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string, apiKey: string) {
    this.client = axios.create({
      baseURL,
      headers: { 'X-Api-Key': apiKey },
    });
  }

  async processPayment(request: PaymentRequest): Promise<PaymentResult> {
    const response: AxiosResponse<PaymentResult> = await this.client.post(
      '/payments',
      request
    );
    return response.data;
  }

  async getInventory(sku: string): Promise<InventoryItem> {
    const response: AxiosResponse<InventoryItem> = await this.client.get(
      `/inventory/${sku}`
    );
    return response.data;
  }

  async reserveInventory(sku: string, quantity: number): Promise<boolean> {
    const response = await this.client.post('/inventory/reserve', {
      sku,
      quantity,
    });
    return response.status === 200;
  }
}
