package com.meridian.compliance.service;

import org.springframework.stereotype.Service;
import com.meridian.compliance.dao.ComplianceDAO;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.core.sync.RequestBody;

import java.util.*;

@Service
public class ComplianceService {

    private final ComplianceDAO dao;
    private final S3Client s3;
    private static final String BUCKET = "meridian-compliance-reports-prod";

    public ComplianceService(ComplianceDAO dao, S3Client s3) {
        this.dao = dao;
        this.s3  = s3;
    }

    /**
     * Builds a compliance report using safe parameterized DynamoDB queries.
     * Called from generateComplianceReport (service token validated upstream).
     * pc_sanitization: sanitized (token check upstream).
     * E_data_flow_read: → meridian-compliance-records DynamoDB table.
     */
    public Map<String, Object> buildComplianceReport(String period, String format) {
        var records = dao.queryByPeriodSafe(period);
        return Map.of("period", period, "format", format, "record_count", records.size());
    }

    /**
     * TAINT SINK proxy — delegates to DAO.executeRawQuery.
     * Called UNSANITIZED from executeRawReport controller.
     * sensitivity_class: financial (regulatory report data).
     */
    public Map<String, Object> executeRawReport(String rawQuery) {
        return dao.executeRawQuery(rawQuery);
    }

    /**
     * Stores a report file to S3.
     * E_data_flow_write: this → meridian-compliance-reports-prod S3 bucket.
     */
    public void storeReport(String path, byte[] data) {
        s3.putObject(
            PutObjectRequest.builder().bucket(BUCKET).key(path).build(),
            RequestBody.fromBytes(data)
        );
    }
}
