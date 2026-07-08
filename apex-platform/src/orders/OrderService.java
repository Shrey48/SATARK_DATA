package com.apex.commerce.orders;

import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;
import java.util.HashMap;
import java.util.Map;

public class OrderService {
    private final DynamoDbClient dynamoDbClient;
    private static final String TABLE_NAME = "apex-orders-prod";

    public OrderService(DynamoDbClient dynamoDbClient) {
        this.dynamoDbClient = dynamoDbClient;
    }

    public void createOrder(String orderId, String customerId, long totalCents) {
        Map<String, AttributeValue> item = new HashMap<>();
        item.put("orderId", AttributeValue.builder().s(orderId).build());
        item.put("customerId", AttributeValue.builder().s(customerId).build());
        item.put("totalCents", AttributeValue.builder().n(String.valueOf(totalCents)).build());
        item.put("status", AttributeValue.builder().s("pending").build());

        dynamoDbClient.putItem(PutItemRequest.builder()
            .tableName(TABLE_NAME)
            .item(item)
            .build());
    }

    public void updateOrderStatus(String orderId, String status) {
        Map<String, AttributeValue> key = new HashMap<>();
        key.put("orderId", AttributeValue.builder().s(orderId).build());

        dynamoDbClient.updateItem(UpdateItemRequest.builder()
            .tableName(TABLE_NAME)
            .key(key)
            .updateExpression("SET #s = :status")
            .expressionAttributeNames(Map.of("#s", "status"))
            .expressionAttributeValues(Map.of(":status",
                AttributeValue.builder().s(status).build()))
            .build());
    }

    public boolean orderExists(String orderId) {
        Map<String, AttributeValue> key = new HashMap<>();
        key.put("orderId", AttributeValue.builder().s(orderId).build());
        GetItemResponse response = dynamoDbClient.getItem(
            GetItemRequest.builder().tableName(TABLE_NAME).key(key).build());
        return response.hasItem();
    }
}
