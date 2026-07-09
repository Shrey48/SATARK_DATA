package com.meridian.compliance.dao;

import org.springframework.stereotype.Repository;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;

import java.sql.*;
import java.util.*;

@Repository
public class ComplianceDAO {

    private final DynamoDbClient dynamoDb;
    private static final String TABLE = "meridian-compliance-records-prod";

    public ComplianceDAO(DynamoDbClient dynamoDb) {
        this.dynamoDb = dynamoDb;
    }

    /**
     * TAINT SINK — has_raw_query=true.
     * Executes a raw NoSQL FilterExpression without validation.
     * Called from ComplianceService.executeRawReport which is called
     * from ComplianceController.executeRawReport — NO sanitizer on path.
     * → E_taint_path: executeRawReport (controller) → executeRawQuery (DAO)
     *
     * BUG H PROBE: exactly 1 E_taint_path edge should point to this method.
     * Mode 2 count in triage must equal 1.
     * sensitivity_class: financial
     */
    public Map<String, Object> executeRawQuery(String rawFilterExpression) {
        // VULNERABLE: rawFilterExpression injected into FilterExpression
        var response = dynamoDb.scan(ScanRequest.builder()
            .tableName(TABLE)
            .filterExpression(rawFilterExpression)   // NoSQL injection
            .build());
        return Map.of("count", response.count(), "items", response.items());
    }

    /**
     * SAFE — parameterized DynamoDB query using ExpressionAttributeValues.
     * Called from ComplianceService.buildComplianceReport (safe path).
     * E_data_flow_read: → meridian-compliance-records DynamoDB.
     *
     * FALSE POSITIVE TARGET (F-005 CWE-89 safe path probe):
     * Scanner may flag any DB access. System should score LOW
     * (parameterized, sanitized upstream).
     */
    public List<Map<String, AttributeValue>> queryByPeriodSafe(String period) {
        var response = dynamoDb.query(QueryRequest.builder()
            .tableName(TABLE)
            .keyConditionExpression("report_period = :p")
            .expressionAttributeValues(Map.of(
                ":p", AttributeValue.builder().s(period).build()
            ))
            .build());
        return response.items();
    }
}
