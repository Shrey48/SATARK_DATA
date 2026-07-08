# frozen_string_literal: true

require 'json'
require 'aws-sdk-sqs'

module Apex
  module Legacy
    class WebhookHandler
      SQS_QUEUE_URL = ENV.fetch('LEGACY_QUEUE_URL')

      def initialize
        @sqs = Aws::SQS::Client.new(region: 'us-east-1')
      end

      def handle(event)
        payload = parse_event(event)
        forward_to_queue(payload)
      end

      private

      def parse_event(event)
        JSON.parse(event.fetch('body'))
      end

      def forward_to_queue(payload)
        @sqs.send_message(
          queue_url: SQS_QUEUE_URL,
          message_body: payload.to_json
        )
      end
    end
  end
end
