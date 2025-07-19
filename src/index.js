import express from 'express';
import { WebSocketServer } from 'ws';
import dotenv from 'dotenv';
import CallHandler from './services/call-handler.js';
import TwilioIntegration from './services/twilio-integration.js';
import logger from './utils/logger.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const WS_PORT = process.env.WEBSOCKET_PORT || 3001;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Services
const twilioIntegration = new TwilioIntegration();
const activeCallHandlers = new Map();

// REST API Endpoints
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    version: '1.0.0',
    uptime: process.uptime()
  });
});

// Twilio Voice Webhook
app.post('/webhooks/voice', async (req, res) => {
  logger.info('Incoming call:', req.body);
  
  const twiml = twilioIntegration.generateTwiML(
    'Willkommen bei Marcus Software. Ich verbinde Sie mit unserem KI-Assistenten.'
  );
  
  res.type('text/xml');
  res.send(twiml);
});

// Twilio Status Callback
app.post('/webhooks/status', (req, res) => {
  logger.info('Call status update:', req.body);
  res.sendStatus(200);
});

// API für ausgehende Anrufe
app.post('/api/calls/outbound', async (req, res) => {
  try {
    const { phoneNumber, context } = req.body;
    
    if (!phoneNumber) {
      return res.status(400).json({ error: 'Phone number required' });
    }

    const webhookUrl = `${req.protocol}://${req.get('host')}/webhooks/voice`;
    const call = await twilioIntegration.makeOutboundCall(phoneNumber, webhookUrl);
    
    res.json({
      success: true,
      callSid: call.sid,
      status: call.status
    });
  } catch (error) {
    logger.error('Outbound call error:', error);
    res.status(500).json({ error: error.message });
  }
});

// WebSocket Server für Twilio Media Streams
const wss = new WebSocketServer({ port: WS_PORT });

wss.on('connection', (ws, req) => {
  const path = req.url;
  logger.info('WebSocket connection:', path);
  
  if (path === '/media-stream') {
    let callHandler;
    let callSid;
    
    ws.on('message', async (message) => {
      const data = JSON.parse(message);
      
      if (data.event === 'start') {
        callSid = data.start.callSid;
        
        // Neuen Call Handler erstellen
        callHandler = new CallHandler();
        activeCallHandlers.set(callSid, callHandler);
        
        // Audio Output Handler
        callHandler.on('audio.output', (audioData) => {
          twilioIntegration.sendAudioToCall(ws, audioData);
        });
        
        // Transcript Updates
        callHandler.on('transcript.update', (transcript) => {
          logger.info('Transcript:', transcript);
        });
        
        // Call starten
        await callHandler.startCall();
        
      } else if (data.event === 'media' && callHandler) {
        // Audio von Twilio an OpenAI weiterleiten
        const audioBuffer = Buffer.from(data.media.payload, 'base64');
        callHandler.processAudioInput(audioBuffer);
        
      } else if (data.event === 'stop' && callHandler) {
        await callHandler.endCall();
        activeCallHandlers.delete(callSid);
      }
    });
    
    ws.on('close', () => {
      if (callHandler) {
        callHandler.endCall();
        activeCallHandlers.delete(callSid);
      }
    });
  }
});

// Server starten
app.listen(PORT, () => {
  logger.info(`HTTP Server running on port ${PORT}`);
  logger.info(`WebSocket Server running on port ${WS_PORT}`);
  logger.info('Marcus Call Agent ready!');
});

// Graceful Shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  
  // Alle aktiven Calls beenden
  activeCallHandlers.forEach((handler, callSid) => {
    handler.endCall();
  });
  
  process.exit(0);
});

export default app;