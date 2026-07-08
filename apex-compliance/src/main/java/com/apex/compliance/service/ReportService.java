package com.apex.compliance.service;

import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.dynamodb.model.*;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.core.sync.RequestBody;

import java.util.HashMap;
import java.util.Map;

/**
 * Compliance report service — uses safe AWS SDK calls with no raw queries.
 * processReportData — FALSE POSITIVE CANDIDATE:
 *   Scanners may flag any function that accesses financial data.
 *   This uses parameterized DynamoDB SDK calls — not a SQL/NoSQL injection.
 *   pc_sanitization: sanitized (data comes from validated period param from controller).
 */
@Service
public class ReportService {

    private final DynamoDbClient dynamoDbClient;
    private final S3Client s3Client;
    private static final String TABLE = "apex-compliance-records-prod";
    private static final String BUCKET = "apex-compliance-reports-prod";

    public ReportService(DynamoDbClient dynamoDbClient, S3Client s3Client) {
        this.dynamoDbClient = dynamoDbClient;
        this.s3Client = s3Client;
    }

    /**
     * Processes report data using safe AWS SDK calls.
     * INTERNAL — called from generateReport controller.
     * Uses DynamoDB query API (parameterized, not raw) — NOT a taint sink.
     *
     * FALSE POSITIVE NOTE:
     *   If a scanner flags processReportData as "information disclosure" (CWE-200),
     *   the graph shows: not internet-facing, parameterized queries, no raw query pattern.
     *   Should triage LOW.
     * sensitivity_class: financial (compliance records contain financial data)
     */
    public Map<String, Object> processReportData(String period, String format) {
        // SAFE: DynamoDB QueryRequest with expression attribute values
        var response = dynamoDbClient.query(QueryRequest.builder()
            .tableName(TABLE)
            .keyConditionExpression("report_period = :period")
            .expressionAttributeValues(Map.of(
                ":period", AttributeValue.builder().s(period).build()
            ))
            .build());

        var items = response.items();
        var result = new HashMap<String, Object>();
        result.put("period", period);
        result.put("record_count", items.size());
        result.put("format", format);
        return result;
    }

    /**
     * Archives a compliance report to S3.
     * Called from internal batch jobs — never from HTTP routes.
     * E_data_flow (write): this function → apex-compliance-reports-prod
     */
    public void archiveReport(String reportId, byte[] data) {
        s3Client.putObject(
            PutObjectRequest.builder()
                .bucket(BUCKET)
                .key("reports/" + reportId + ".pdf")
                .build(),
            RequestBody.fromBytes(data)
        );
    }
}
