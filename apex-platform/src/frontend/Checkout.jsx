import React, { useState, useCallback } from 'react';
import Cart from './Cart';

export default function Checkout({ orderId, customerId }) {
  const [step, setStep] = useState('cart');
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handlePayment = useCallback(async (paymentDetails) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/payments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ orderId, customerId, ...paymentDetails }),
      });
      const result = await response.json();
      setPaymentStatus(result.success ? 'success' : 'failed');
      if (result.success) setStep('confirmation');
    } catch (err) {
      setPaymentStatus('error');
    } finally {
      setIsLoading(false);
    }
  }, [orderId, customerId]);

  return (
    <div className="checkout">
      {step === 'cart' && (
        <Cart onProceed={() => setStep('payment')} />
      )}
      {step === 'payment' && (
        <div className="payment-form">
          {isLoading && <div className="spinner" />}
          <button disabled={isLoading} onClick={() => handlePayment({ method: 'card' })}>
            Pay Now
          </button>
        </div>
      )}
      {step === 'confirmation' && (
        <div className="confirmation">Order confirmed!</div>
      )}
    </div>
  );
}
