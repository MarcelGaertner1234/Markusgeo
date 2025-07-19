#!/usr/bin/env python3
"""
PDF zu interaktiver Karte Konverter
Extrahiert Adressinformationen aus PDF und erstellt eine interaktive Karte
"""

import os
import re
import json
import time
from typing import List, Dict, Tuple, Optional
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFToMapConverter:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.geocoder = Nominatim(user_agent="pdf_to_map_converter")
        self.addresses = []
        self.geocoded_addresses = []
        
    def extract_text_from_pdf(self) -> str:
        """Extrahiert Text aus PDF mittels OCR"""
        logger.info(f"Starte PDF-Extraktion: {self.pdf_path}")
        
        try:
            # PDF in Bilder konvertieren
            pages = convert_from_path(self.pdf_path, dpi=300)
            
            full_text = ""
            for i, page in enumerate(pages):
                logger.info(f"Verarbeite Seite {i+1}/{len(pages)}")
                # OCR auf jeder Seite ausführen
                text = pytesseract.image_to_string(page, lang='deu')
                full_text += text + "\n"
            
            return full_text
            
        except Exception as e:
            logger.error(f"Fehler bei PDF-Extraktion: {e}")
            raise
    
    def extract_addresses(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Adressen aus dem Text"""
        logger.info("Extrahiere Adressen aus Text")
        
        # Muster für deutsche Adressen
        # Format: Straßenname Hausnummer, PLZ Ort
        address_pattern = r'([A-ZÄÖÜ][a-zäöüß\-\.]+(?:\s+[A-ZÄÖÜ]?[a-zäöüß\-\.]+)*)\s+(\d+[a-zA-Z]?),?\s*(\d{5})\s+([A-ZÄÖÜ][a-zäöüß\-\.]+(?:\s+[A-ZÄÖÜ]?[a-zäöüß\-\.]+)*)'
        
        # Zusätzliches Muster für Straßennamen ohne Hausnummer
        street_pattern = r'([A-ZÄÖÜ][a-zäöüß\-\.]+(?:straße|weg|platz|allee|ring|damm|gasse))'
        
        addresses = []
        
        # Nach vollständigen Adressen suchen
        for match in re.finditer(address_pattern, text, re.MULTILINE):
            address = {
                'street': match.group(1).strip(),
                'house_number': match.group(2).strip(),
                'postal_code': match.group(3).strip(),
                'city': match.group(4).strip(),
                'full_address': f"{match.group(1)} {match.group(2)}, {match.group(3)} {match.group(4)}"
            }
            addresses.append(address)
        
        # Nach Straßennamen suchen (falls keine vollständigen Adressen gefunden)
        if not addresses:
            for match in re.finditer(street_pattern, text, re.IGNORECASE):
                # Versuche Nümbrecht als Standardort zu verwenden
                address = {
                    'street': match.group(1).strip(),
                    'house_number': '',
                    'postal_code': '51588',  # PLZ von Nümbrecht
                    'city': 'Nümbrecht',
                    'full_address': f"{match.group(1)}, 51588 Nümbrecht"
                }
                addresses.append(address)
        
        # Duplikate entfernen
        unique_addresses = []
        seen = set()
        for addr in addresses:
            if addr['full_address'] not in seen:
                seen.add(addr['full_address'])
                unique_addresses.append(addr)
        
        logger.info(f"Gefundene Adressen: {len(unique_addresses)}")
        return unique_addresses
    
    def geocode_address(self, address: Dict[str, str]) -> Optional[Tuple[float, float]]:
        """Geocodiert eine Adresse zu Koordinaten"""
        try:
            time.sleep(1)  # Rate limiting für Nominatim
            
            # Zuerst vollständige Adresse versuchen
            location = self.geocoder.geocode(address['full_address'])
            
            # Falls nicht gefunden, nur Straße und Stadt versuchen
            if not location and address['street']:
                simplified = f"{address['street']}, {address['city']}"
                location = self.geocoder.geocode(simplified)
            
            # Falls immer noch nicht gefunden, nur Stadt
            if not location:
                location = self.geocoder.geocode(address['city'])
            
            if location:
                return (location.latitude, location.longitude)
            
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding-Fehler für {address['full_address']}: {e}")
            return None
    
    def geocode_addresses(self):
        """Geocodiert alle gefundenen Adressen"""
        logger.info("Starte Geocoding der Adressen")
        
        for i, address in enumerate(self.addresses):
            logger.info(f"Geocoding {i+1}/{len(self.addresses)}: {address['full_address']}")
            
            coords = self.geocode_address(address)
            if coords:
                address['latitude'] = coords[0]
                address['longitude'] = coords[1]
                self.geocoded_addresses.append(address)
                logger.info(f"✓ Erfolgreich: {coords}")
            else:
                logger.warning(f"✗ Nicht gefunden: {address['full_address']}")
    
    def create_map(self, output_file: str = "map.html"):
        """Erstellt eine interaktive Karte mit den geocodierten Adressen"""
        if not self.geocoded_addresses:
            logger.error("Keine geocodierten Adressen vorhanden!")
            return
        
        logger.info(f"Erstelle Karte mit {len(self.geocoded_addresses)} Adressen")
        
        # Zentrum der Karte berechnen
        avg_lat = sum(addr['latitude'] for addr in self.geocoded_addresses) / len(self.geocoded_addresses)
        avg_lon = sum(addr['longitude'] for addr in self.geocoded_addresses) / len(self.geocoded_addresses)
        
        # Karte erstellen
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
        
        # Marker-Cluster hinzufügen
        marker_cluster = MarkerCluster().add_to(m)
        
        # Marker für jede Adresse
        for addr in self.geocoded_addresses:
            popup_text = f"""
            <b>{addr['street']} {addr['house_number']}</b><br>
            {addr['postal_code']} {addr['city']}<br>
            <small>Lat: {addr['latitude']:.6f}, Lon: {addr['longitude']:.6f}</small>
            """
            
            folium.Marker(
                location=[addr['latitude'], addr['longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=addr['full_address']
            ).add_to(marker_cluster)
        
        # Karte speichern
        m.save(output_file)
        logger.info(f"Karte gespeichert als: {output_file}")
        
        # Zusätzlich als GeoJSON speichern
        geojson_file = output_file.replace('.html', '.geojson')
        self.save_as_geojson(geojson_file)
    
    def save_as_geojson(self, output_file: str):
        """Speichert die Daten als GeoJSON für weitere Verwendung"""
        features = []
        
        for addr in self.geocoded_addresses:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [addr['longitude'], addr['latitude']]
                },
                "properties": {
                    "street": addr['street'],
                    "house_number": addr['house_number'],
                    "postal_code": addr['postal_code'],
                    "city": addr['city'],
                    "full_address": addr['full_address']
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        logger.info(f"GeoJSON gespeichert als: {output_file}")
    
    def save_as_csv(self, output_file: str):
        """Speichert die Daten als CSV"""
        if self.geocoded_addresses:
            df = pd.DataFrame(self.geocoded_addresses)
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"CSV gespeichert als: {output_file}")
    
    def process(self):
        """Hauptprozess: PDF -> Text -> Adressen -> Geocoding -> Karte"""
        try:
            # Text aus PDF extrahieren
            text = self.extract_text_from_pdf()
            
            # Adressen extrahieren
            self.addresses = self.extract_addresses(text)
            
            if not self.addresses:
                logger.warning("Keine Adressen im PDF gefunden!")
                return
            
            # Adressen geocodieren
            self.geocode_addresses()
            
            if not self.geocoded_addresses:
                logger.error("Keine Adressen konnten geocodiert werden!")
                return
            
            # Karte erstellen
            base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
            map_file = f"{base_name}_map.html"
            self.create_map(map_file)
            
            # Zusätzliche Formate speichern
            self.save_as_csv(f"{base_name}_addresses.csv")
            
            logger.info("Verarbeitung abgeschlossen!")
            logger.info(f"Ergebnisse:")
            logger.info(f"- Karte: {map_file}")
            logger.info(f"- CSV: {base_name}_addresses.csv")
            logger.info(f"- GeoJSON: {base_name}_map.geojson")
            
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung: {e}")
            raise


def main():
    """Hauptfunktion"""
    pdf_path = "/Users/marcelgaertner/Desktop/Arbeit/Markus schmitz/marcus-call-agent/Nümbrecht straßengenau.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF-Datei nicht gefunden: {pdf_path}")
        return
    
    converter = PDFToMapConverter(pdf_path)
    converter.process()


if __name__ == "__main__":
    main()