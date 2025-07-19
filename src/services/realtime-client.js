import WebSocket from 'ws';
import { EventEmitter } from 'events';
import { v4 as uuidv4 } from 'uuid';
import logger from '../utils/logger.js';
import { WEBSOCKET_URL, API_KEY, REALTIME_CONFIG } from '../config/openai-realtime.js';

export class RealtimeClient extends EventEmitter {
  constructor() {
    super();
    this.ws = null;
    this.sessionId = null;
    this.isConnected = false;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(WEBSOCKET_URL, {
          headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'OpenAI-Beta': 'realtime=v1'
          }
        });

        this.ws.on('open', () => {
          logger.info('WebSocket connection established');
          this.isConnected = true;
          this.sendSessionUpdate();
          resolve();
        });

        this.ws.on('message', (data) => {
          const event = JSON.parse(data.toString());
          this.handleEvent(event);
        });

        this.ws.on('error', (error) => {
          logger.error('WebSocket error:', error);
          this.emit('error', error);
          reject(error);
        });

        this.ws.on('close', () => {
          logger.info('WebSocket connection closed');
          this.isConnected = false;
          this.emit('disconnected');
        });

      } catch (error) {
        logger.error('Connection error:', error);
        reject(error);
      }
    });
  }

  sendSessionUpdate() {
    const sessionUpdate = {
      type: 'session.update',
      session: {
        modalities: ['text', 'audio'],
        instructions: REALTIME_CONFIG.instructions,
        voice: REALTIME_CONFIG.voice,
        input_audio_format: REALTIME_CONFIG.input_audio_format,
        output_audio_format: REALTIME_CONFIG.output_audio_format,
        turn_detection: REALTIME_CONFIG.turn_detection,
        tools: REALTIME_CONFIG.tools,
        tool_choice: 'auto',
        temperature: 0.8
      }
    };

    this.sendEvent(sessionUpdate);
  }

  sendEvent(event) {
    if (!this.isConnected || !this.ws) {
      logger.error('Cannot send event: not connected');
      return;
    }

    const eventWithId = {
      ...event,
      event_id: event.event_id || uuidv4()
    };

    this.ws.send(JSON.stringify(eventWithId));
    logger.debug('Sent event:', eventWithId.type);
  }

  handleEvent(event) {
    logger.debug('Received event:', event.type);

    switch (event.type) {
      case 'session.created':
        this.sessionId = event.session.id;
        logger.info('Session created:', this.sessionId);
        this.emit('session.created', event.session);
        break;

      case 'conversation.item.created':
        this.emit('conversation.item.created', event.item);
        break;

      case 'response.audio.delta':
        this.emit('audio.delta', event.delta);
        break;

      case 'response.audio.done':
        this.emit('audio.done');
        break;

      case 'response.text.delta':
        this.emit('text.delta', event.delta);
        break;

      case 'response.function_call_arguments.done':
        this.handleFunctionCall(event);
        break;

      case 'error':
        logger.error('Realtime API error:', event.error);
        this.emit('error', event.error);
        break;

      default:
        this.emit(event.type, event);
    }
  }

  async handleFunctionCall(event) {
    const { name, arguments: args } = event;
    logger.info(`Function call: ${name}`, args);

    let result;
    try {
      const parsedArgs = JSON.parse(args);
      
      switch (name) {
        case 'schedule_appointment':
          result = await this.scheduleAppointment(parsedArgs);
          break;
        case 'create_support_ticket':
          result = await this.createSupportTicket(parsedArgs);
          break;
        default:
          result = { error: 'Unknown function' };
      }

      this.sendFunctionCallResult(event.call_id, result);
    } catch (error) {
      logger.error('Function call error:', error);
      this.sendFunctionCallResult(event.call_id, { error: error.message });
    }
  }

  async scheduleAppointment(args) {
    // Hier würde die Integration mit Marcus' Software stattfinden
    logger.info('Scheduling appointment:', args);
    return {
      success: true,
      appointment_id: uuidv4(),
      message: `Termin für ${args.customer_name} am ${args.date} um ${args.time} wurde erfolgreich vereinbart.`
    };
  }

  async createSupportTicket(args) {
    // Integration mit Ticketing-System
    logger.info('Creating support ticket:', args);
    return {
      success: true,
      ticket_id: `TICKET-${Date.now()}`,
      message: `Support-Ticket für ${args.customer_name} wurde erstellt.`
    };
  }

  sendFunctionCallResult(callId, result) {
    this.sendEvent({
      type: 'conversation.item.create',
      item: {
        type: 'function_call_output',
        call_id: callId,
        output: JSON.stringify(result)
      }
    });
  }

  sendAudio(audioData) {
    this.sendEvent({
      type: 'input_audio_buffer.append',
      audio: audioData.toString('base64')
    });
  }

  commitAudio() {
    this.sendEvent({
      type: 'input_audio_buffer.commit'
    });
  }

  createResponse() {
    this.sendEvent({
      type: 'response.create'
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }
}

export default RealtimeClient;