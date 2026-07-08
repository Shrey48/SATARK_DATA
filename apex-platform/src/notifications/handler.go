package notifications

import (
	"context"
	"fmt"

	"github.com/aws/aws-sdk-go-v2/service/sns"
)

// NotificationHandler sends order and payment events to SNS.
type NotificationHandler struct {
	snsClient *sns.Client
	topicARN  string
}

// NewNotificationHandler creates a new handler.
func NewNotificationHandler(client *sns.Client, topicARN string) *NotificationHandler {
	return &NotificationHandler{snsClient: client, topicARN: topicARN}
}

// SendOrderUpdate publishes an order status change to SNS.
func (h *NotificationHandler) SendOrderUpdate(ctx context.Context, orderID string, status string) error {
	message := fmt.Sprintf("Order %s status changed to %s", orderID, status)
	return h.publish(ctx, message)
}

// SendPaymentAlert publishes a payment event to SNS.
func (h *NotificationHandler) SendPaymentAlert(ctx context.Context, paymentID string, amountCents int64) error {
	message := fmt.Sprintf("Payment %s processed: %d cents", paymentID, amountCents)
	return h.publish(ctx, message)
}

func (h *NotificationHandler) publish(ctx context.Context, message string) error {
	_, err := h.snsClient.Publish(ctx, &sns.PublishInput{
		TopicArn: &h.topicARN,
		Message:  &message,
	})
	return err
}
