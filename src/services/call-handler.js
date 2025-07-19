import { EventEmitter } from 'events';
import RealtimeClient from './realtime-client.js';
import logger from '../utils/logger.js';

export class CallHandler extends EventEmitter {
  constructor() {
    super();
    this.realtimeClient = new RealtimeClient();
    this.audioBuffer = [];
    this.isActive = false;
    
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.realtimeClient.on('session.created', (session) => {
      logger.info('Call session ready:', session.id);
      this.emit('ready', session);
    });

    this.realtimeClient.on('audio.delta', (audioData) => {
      // Audio-Daten an Twilio weiterleiten
      this.emit('audio.output', audioData);
    });

    this.realtimeClient.on('text.delta', (textDelta) => {
      // Transkription für Monitoring
      this.emit('transcript.update', textDelta);
    });

    this.realtimeClient.on('error', (error) => {
      logger.error('Realtime API error in call:', error);
      this.emit('error', error);
    });
  }

  async startCall() {
    try {
      this.isActive = true;
      await this.realtimeClient.connect();
      logger.info('Call handler started successfully');
    } catch (error) {
      logger.error('Failed to start call handler:', error);
      this.isActive = false;
      throw error;
    }
  }

  processAudioInput(audioData) {
    if (!this.isActive) return;
    
    // Audio an OpenAI Realtime API senden
    this.realtimeClient.sendAudio(audioData);
  }

  commitAudioAndRespond() {
    if (!this.isActive) return;
    
    this.realtimeClient.commitAudio();
    this.realtimeClient.createResponse();
  }

  async endCall() {
    this.isActive = false;
    this.realtimeClient.disconnect();
    logger.info('Call ended');
    this.emit('call.ended');
  }

  // Methoden für Call-Metriken
  getCallMetrics() {
    return {
      duration: this.callDuration,
      transcriptLength: this.transcriptLength,
      functionsTriggered: this.functionsTriggered
    };
  }
}

export default CallHandler;