# PDF zu Karte Konverter

Dieses Script extrahiert Adressen aus einem PDF mittels OCR und erstellt eine interaktive Karte.

## Installation

1. **System-Abhängigkeiten installieren:**
   ```bash
   # macOS
   brew install tesseract tesseract-lang poppler
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr tesseract-ocr-deu poppler-utils
   ```

2. **Python-Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

## Verwendung

```bash
python pdf_to_map.py
```

Das Script wird:
1. Text aus dem PDF mittels OCR extrahieren
2. Adressen im Text finden (speziell für deutsche Adressen optimiert)
3. Die Adressen über Nominatim (OpenStreetMap) geocodieren
4. Eine interaktive HTML-Karte erstellen

## Ausgabe

- `Nümbrecht straßengenau_map.html` - Interaktive Karte
- `Nümbrecht straßengenau_addresses.csv` - Adressliste mit Koordinaten
- `Nümbrecht straßengenau_map.geojson` - GeoJSON für GIS-Software

## Anpassungen

Das Script sucht nach deutschen Adressmustern. Für Nümbrecht wird automatisch die PLZ 51588 verwendet, falls keine gefunden wird.