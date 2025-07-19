# Marcus Call Agent - Premium AI Voice Assistant

Ein hochmoderner AI Call Agent basierend auf OpenAI's Realtime API für nahtlose, natürliche Telefongespräche.

## Features

- **Ultra-niedrige Latenz**: ~320ms Antwortzeit (menschenähnlich)
- **Natürliche Konversation**: Speech-to-Speech ohne Zwischenschritte
- **Funktionsaufrufe**: Termine vereinbaren, Tickets erstellen
- **Twilio Integration**: Professionelle Telefonie
- **Mehrsprachig**: Deutsch & Englisch
- **Enterprise-Ready**: Skalierbar, sicher, zuverlässig

## Tech Stack

- **OpenAI Realtime API**: GPT-4o-realtime-preview
- **Twilio**: Telefonie-Integration
- **Node.js**: Backend Server
- **WebSockets**: Echtzeit-Kommunikation

## Installation

1. Repository klonen:
```bash
git clone <repository-url>
cd marcus-call-agent
```

2. Dependencies installieren:
```bash
npm install
```

3. Environment Variables setzen:
```bash
cp .env.example .env
# .env Datei mit echten Credentials ausfüllen
```

4. Server starten:
```bash
npm run dev
```

## Konfiguration

### OpenAI Realtime API
- Model: `gpt-4o-realtime-preview`
- Voice: `alloy` (anpassbar)
- Latenz: ~320ms
- Kosten: $0.06/min Input, $0.24/min Output

### Twilio Setup
1. Twilio Account erstellen
2. Telefonnummer kaufen
3. Webhook URLs konfigurieren:
   - Voice URL: `https://your-domain.com/webhooks/voice`
   - Status Callback: `https://your-domain.com/webhooks/status`

## API Endpoints

### Health Check
```
GET /health
```

### Ausgehender Anruf
```
POST /api/calls/outbound
{
  "phoneNumber": "+491234567890",
  "context": "optional context data"
}
```

## Architektur

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   Twilio    │────▶│  WebSocket   │────▶│ OpenAI         │
│  (Telefon)  │◀────│   Server     │◀────│ Realtime API   │
└─────────────┘     └──────────────┘     └────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Marcus     │
                    │  Software    │
                    └──────────────┘
```

## Nächste Schritte

1. **Testing**: Unit Tests implementieren
2. **Monitoring**: Logging & Analytics ausbauen  
3. **Skalierung**: Load Balancing & Redundanz
4. **Features**: Weitere Funktionen (CRM Integration, etc.)

## Support

Bei Fragen oder Problemen bitte an Marcus wenden.