import React, { useState } from 'react';

export default function Cart({ onProceed }) {
  const [items, setItems] = useState([]);

  const removeItem = (sku) => {
    setItems((prev) => prev.filter((item) => item.sku !== sku));
  };

  const total = items.reduce((sum, item) => sum + item.priceCents * item.quantity, 0);

  return (
    <div className="cart">
      <h2>Your Cart</h2>
      {items.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <ul>
          {items.map((item) => (
            <li key={item.sku}>
              {item.name} x {item.quantity}
              <button onClick={() => removeItem(item.sku)}>Remove</button>
            </li>
          ))}
        </ul>
      )}
      <p>Total: ${(total / 100).toFixed(2)}</p>
      <button disabled={items.length === 0} onClick={onProceed}>
        Proceed to Checkout
      </button>
    </div>
  );
}
