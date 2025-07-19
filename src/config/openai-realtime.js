import dotenv from 'dotenv';
dotenv.config();

export const REALTIME_CONFIG = {
  model: 'gpt-4o-realtime-preview',
  voice: 'alloy', // verfügbare Stimmen: alloy, echo, fable, onyx, nova, shimmer
  instructions: `Du bist ein professioneller Call Agent für Marcus' Software.
Du sprichst natürlich und freundlich auf Deutsch.
Deine Aufgaben:
- Kundenanfragen entgegennehmen
- Termine vereinbaren
- Produktinformationen geben
- Support-Tickets erstellen
Sei hilfsbereit, professionell und effizient.`,
  
  turn_detection: {
    type: 'server_vad', // server_vad für automatische Spracherkennung
    threshold: 0.5,
    prefix_padding_ms: 300,
    silence_duration_ms: 500
  },
  
  input_audio_format: 'pcm16',
  output_audio_format: 'pcm16',
  
  tools: [
    {
      type: 'function',
      function: {
        name: 'schedule_appointment',
        description: 'Vereinbart einen Termin für den Kunden',
        parameters: {
          type: 'object',
          properties: {
            customer_name: { type: 'string' },
            date: { type: 'string', format: 'date' },
            time: { type: 'string', format: 'time' },
            purpose: { type: 'string' }
          },
          required: ['customer_name', 'date', 'time', 'purpose']
        }
      }
    },
    {
      type: 'function', 
      function: {
        name: 'create_support_ticket',
        description: 'Erstellt ein Support-Ticket',
        parameters: {
          type: 'object',
          properties: {
            customer_name: { type: 'string' },
            issue: { type: 'string' },
            priority: { type: 'string', enum: ['low', 'medium', 'high'] }
          },
          required: ['customer_name', 'issue']
        }
      }
    }
  ]
};

export const WEBSOCKET_URL = 'wss://api.openai.com/v1/realtime';
export const API_KEY = process.env.OPENAI_API_KEY;