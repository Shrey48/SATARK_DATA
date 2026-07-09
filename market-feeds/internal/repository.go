package internal

import (
	"context"
	"os"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb"
	"github.com/aws/aws-sdk-go-v2/service/dynamodb/types"
)

// FeedRepository handles market feed data access.
type FeedRepository struct {
	client    *dynamodb.Client
	tableName string  // env var pattern: from os.Getenv("TABLE_NAME")
}

// NewFeedRepository creates a repository bound to the TABLE_NAME env var.
func NewFeedRepository(client *dynamodb.Client) *FeedRepository {
	return &FeedRepository{
		client:    client,
		tableName: os.Getenv("TABLE_NAME"),  // struct field from env var
	}
}

// QueryRawFeed executes a raw scan without expression attribute values.
// has_raw_query=true — TAINT SINK for GetMarketData.
// Called UNSANITIZED from GetMarketData → E_taint_path.
// sensitivity_class: financial (real-time market pricing data).
//
// BUG H PROBE: Mode 2 should report exactly 1 taint path to QueryRawFeed
// (from GetMarketData). E_taint_path edge count in KG = 1.
func (r *FeedRepository) QueryRawFeed(filterExpr string) ([]map[string]types.AttributeValue, error) {
	result, err := r.client.Scan(context.Background(), &dynamodb.ScanInput{
		TableName:        aws.String(r.tableName),
		FilterExpression: aws.String(filterExpr),  // injection: user-controlled
	})
	if err != nil {
		return nil, err
	}
	return result.Items, nil
}

// GetFeedBySafe retrieves a feed record using parameterized expression.
// Called from GetFeedStatus after SanitizeSymbol — SAFE path.
// E_data_flow_read: → meridian-market-feeds DynamoDB table.
func (r *FeedRepository) GetFeedBySafe(cleanSymbol string) (map[string]types.AttributeValue, error) {
	result, err := r.client.GetItem(context.Background(), &dynamodb.GetItemInput{
		TableName: aws.String(r.tableName),
		Key: map[string]types.AttributeValue{
			"symbol": &types.AttributeValueMemberS{Value: cleanSymbol},
		},
	})
	if err != nil {
		return nil, err
	}
	return result.Item, nil
}
