import AWS from 'aws-sdk';

/**
 * LambdaClient — wraps AWS Lambda SDK calls.
 * E_data_flow: invokeOrderProcessor → meridian-order-processor Lambda
 * E_data_flow_read: getPortfolioData → meridian-portfolio-reader Lambda
 */
export class LambdaClient {
  private lambda: AWS.Lambda;

  constructor() {
    this.lambda = new AWS.Lambda({ region: process.env.AWS_REGION || 'us-east-1' });
  }

  async invokeOrderProcessor(payload: object): Promise<object> {
    const result = await this.lambda.invoke({
      FunctionName: 'meridian-order-processor',    // literal → cross-asset link
      Payload: JSON.stringify(payload),
    }).promise();
    return JSON.parse(result.Payload as string);
  }

  async getPortfolioData(cleanId: string): Promise<object> {
    const result = await this.lambda.invoke({
      FunctionName: 'meridian-portfolio-reader',   // literal → cross-asset link
      Payload: JSON.stringify({ portfolio_id: cleanId }),
    }).promise();
    return JSON.parse(result.Payload as string);
  }
}
