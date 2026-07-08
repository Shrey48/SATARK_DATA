using Amazon.S3;
using Amazon.S3.Model;
using System.Text;

namespace Apex.Commerce.Reporting;

public class ReportGenerator
{
    private readonly IAmazonS3 _s3Client;
    private const string ReportsBucket = "apex-reports-prod";

    public ReportGenerator(IAmazonS3 s3Client)
    {
        _s3Client = s3Client;
    }

    public async Task GenerateSalesReport(string reportId, IEnumerable<SalesRecord> records)
    {
        var csv = BuildCsv(records);
        await UploadReport(reportId, csv);
    }

    public async Task GenerateInventoryReport(string reportId, IEnumerable<InventoryRecord> records)
    {
        var csv = BuildInventoryCsv(records);
        await UploadReport($"inventory/{reportId}", csv);
    }

    private string BuildCsv(IEnumerable<SalesRecord> records)
    {
        var sb = new StringBuilder();
        sb.AppendLine("OrderId,Amount,Currency,Date");
        foreach (var r in records)
            sb.AppendLine($"{r.OrderId},{r.Amount},{r.Currency},{r.Date:yyyy-MM-dd}");
        return sb.ToString();
    }

    private string BuildInventoryCsv(IEnumerable<InventoryRecord> records)
    {
        var sb = new StringBuilder();
        sb.AppendLine("SKU,Quantity,Reserved");
        foreach (var r in records)
            sb.AppendLine($"{r.Sku},{r.Quantity},{r.Reserved}");
        return sb.ToString();
    }

    private async Task UploadReport(string key, string content)
    {
        await _s3Client.PutObjectAsync(new PutObjectRequest
        {
            BucketName = ReportsBucket,
            Key = $"reports/{key}.csv",
            ContentBody = content,
        });
    }
}

public record SalesRecord(string OrderId, decimal Amount, string Currency, DateTime Date);
public record InventoryRecord(string Sku, int Quantity, int Reserved);
