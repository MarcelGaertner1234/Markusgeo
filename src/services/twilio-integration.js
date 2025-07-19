import twilio from 'twilio';
import { EventEmitter } from 'events';
import logger from '../utils/logger.js';

export class TwilioIntegration extends EventEmitter {
  constructor() {
    super();
    this.client = twilio(
      process.env.TWILIO_ACCOUNT_SID,
      process.env.TWILIO_AUTH_TOKEN
    );
    this.phoneNumber = process.env.TWILIO_PHONE_NUMBER;
  }

  async initializeWebhooks(baseUrl) {
    try {
      // Webhook URLs für Twilio
      const voiceUrl = `${baseUrl}/webhooks/voice`;
      const statusCallbackUrl = `${baseUrl}/webhooks/status`;

      logger.info('Twilio webhooks initialized:', { voiceUrl, statusCallbackUrl });
      
      return {
        voiceUrl,
        statusCallbackUrl
      };
    } catch (error) {
      logger.error('Failed to initialize Twilio webhooks:', error);
      throw error;
    }
  }

  async makeOutboundCall(toNumber, webhookUrl) {
    try {
      const call = await this.client.calls.create({
        to: toNumber,
        from: this.phoneNumber,
        url: webhookUrl,
        record: true, // Für Qualitätssicherung
        machineDetection: 'DetectMessageEnd', // Erkennt Anrufbeantworter
        machineDetectionTimeout: 3000
      });

      logger.info('Outbound call initiated:', call.sid);
      return call;
    } catch (error) {
      logger.error('Failed to make outbound call:', error);
      throw error;
    }
  }

  generateTwiML(message) {
    const twiml = new twilio.twiml.VoiceResponse();
    
    if (message) {
      twiml.say({
        voice: 'alice',
        language: 'de-DE'
      }, message);
    }

    // WebSocket Stream für Realtime Audio
    const stream = twiml.stream({
      url: `wss://${process.env.WEBSOCKET_HOST || 'localhost'}:${process.env.WEBSOCKET_PORT || 3001}/media-stream`
    });
    
    stream.parameter({
      name: 'customerNumber',
      value: 'customer_phone_number'
    });

    return twiml.toString();
  }

  async getCallDetails(callSid) {
    try {
      const call = await this.client.calls(callSid).fetch();
      return call;
    } catch (error) {
      logger.error('Failed to get call details:', error);
      throw error;
    }
  }

  async endCall(callSid) {
    try {
      const call = await this.client.calls(callSid).update({
        status: 'completed'
      });
      logger.info('Call ended:', callSid);
      return call;
    } catch (error) {
      logger.error('Failed to end call:', error);
      throw error;
    }
  }

  // Verarbeitet Audio-Stream von Twilio
  processMediaStream(ws, callSid) {
    let streamSid;
    
    ws.on('message', (msg) => {
      const data = JSON.parse(msg);
      
      switch (data.event) {
        case 'start':
          streamSid = data.start.streamSid;
          logger.info('Media stream started:', streamSid);
          this.emit('stream.started', { streamSid, callSid });
          break;
          
        case 'media':
          // Audio-Daten (base64 encoded mulaw)
          const audioBuffer = Buffer.from(data.media.payload, 'base64');
          this.emit('audio.received', {
            callSid,
            streamSid,
            audio: audioBuffer,
            timestamp: data.media.timestamp
          });
          break;
          
        case 'stop':
          logger.info('Media stream stopped:', streamSid);
          this.emit('stream.stopped', { streamSid, callSid });
          break;
      }
    });

    ws.on('close', () => {
      logger.info('WebSocket closed for call:', callSid);
      this.emit('stream.closed', { callSid });
    });
  }

  // Sendet Audio zurück an Twilio
  sendAudioToCall(ws, audioData) {
    const mediaMessage = {
      event: 'media',
      streamSid: this.currentStreamSid,
      media: {
        payload: audioData.toString('base64')
      }
    };
    
    ws.send(JSON.stringify(mediaMessage));
  }
}

export default TwilioIntegration;