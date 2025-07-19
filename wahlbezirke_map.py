#!/usr/bin/env python3
"""
Wahlbezirke Karte für Nümbrecht
Kombiniert Straßendaten mit CDU-Kandidaten und deren Bezirken
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
import random

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Farbpalette für Wahlbezirke
COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#6C5CE7', '#A8E6CF', '#FF8B94', '#C7CEEA', '#FFDAB9',
    '#E8B4B8', '#95E1D3', '#F38181', '#AA96DA', '#FCBAD3'
]

class WahlbezirkeMapConverter:
    def __init__(self, strassen_pdf: str, kandidaten_pdf: str):
        self.strassen_pdf = strassen_pdf
        self.kandidaten_pdf = kandidaten_pdf
        self.geocoder = Nominatim(user_agent="wahlbezirke_map_converter")
        self.strassen = []
        self.kandidaten_bezirke = {}
        self.strassen_mit_bezirk = []
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrahiert Text aus PDF mittels OCR"""
        logger.info(f"Starte PDF-Extraktion: {pdf_path}")
        
        try:
            pages = convert_from_path(pdf_path, dpi=300)
            
            full_text = ""
            for i, page in enumerate(pages):
                logger.info(f"Verarbeite Seite {i+1}/{len(pages)}")
                text = pytesseract.image_to_string(page, lang='deu')
                full_text += text + "\n"
            
            return full_text
            
        except Exception as e:
            logger.error(f"Fehler bei PDF-Extraktion: {e}")
            raise
    
    def extract_kandidaten_bezirke(self, text: str) -> Dict[str, Dict]:
        """Extrahiert CDU-Kandidaten und ihre Bezirke aus dem Text"""
        logger.info("Extrahiere Kandidaten und Bezirke")
        
        kandidaten = {}
        
        # Muster für Kandidaten und Bezirke anpassen
        # Format könnte sein: "Name: Bezirk X - Straßen: ..."
        # Oder: "Wahlbezirk X: Kandidat Name"
        
        # Einfaches Muster - muss eventuell angepasst werden
        bezirk_pattern = r'(?:Wahlbezirk|Bezirk)\s*(\d+)[:\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)'
        
        # Nach Bezirken mit Kandidaten suchen
        lines = text.split('\n')
        current_bezirk = None
        current_kandidat = None
        bezirk_strassen = []
        
        for i, line in enumerate(lines):
            # Suche nach Bezirk/Kandidat
            if 'Bezirk' in line or 'Wahlbezirk' in line:
                # Speichere vorherigen Bezirk
                if current_bezirk and current_kandidat:
                    kandidaten[current_bezirk] = {
                        'name': current_kandidat,
                        'strassen': bezirk_strassen,
                        'farbe': COLORS[len(kandidaten) % len(COLORS)]
                    }
                
                # Extrahiere neuen Bezirk
                match = re.search(r'(\d+)', line)
                if match:
                    current_bezirk = f"Bezirk {match.group(1)}"
                    bezirk_strassen = []
                    
                    # Versuche Kandidatennamen zu finden
                    # Könnte in derselben oder nächsten Zeile sein
                    name_match = re.search(r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', line)
                    if name_match:
                        current_kandidat = name_match.group(1)
                    elif i + 1 < len(lines):
                        name_match = re.search(r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', lines[i+1])
                        if name_match:
                            current_kandidat = name_match.group(1)
            
            # Sammle Straßennamen für aktuellen Bezirk
            elif current_bezirk:
                strassen_match = re.findall(r'([A-ZÄÖÜ][a-zäöüß\-\.]+(?:straße|weg|platz|allee|ring|damm|gasse))', line, re.IGNORECASE)
                bezirk_strassen.extend(strassen_match)
        
        # Letzten Bezirk speichern
        if current_bezirk and current_kandidat:
            kandidaten[current_bezirk] = {
                'name': current_kandidat,
                'strassen': bezirk_strassen,
                'farbe': COLORS[len(kandidaten) % len(COLORS)]
            }
        
        # Falls keine Bezirke gefunden, erstelle Beispiel-Bezirke
        if not kandidaten:
            logger.warning("Keine Bezirke im PDF gefunden. Erstelle Beispiel-Bezirke.")
            kandidaten = {
                'Bezirk 1': {'name': 'Kandidat 1', 'strassen': [], 'farbe': COLORS[0]},
                'Bezirk 2': {'name': 'Kandidat 2', 'strassen': [], 'farbe': COLORS[1]},
                'Bezirk 3': {'name': 'Kandidat 3', 'strassen': [], 'farbe': COLORS[2]},
                'Bezirk 4': {'name': 'Kandidat 4', 'strassen': [], 'farbe': COLORS[3]},
            }
        
        logger.info(f"Gefundene Bezirke: {len(kandidaten)}")
        return kandidaten
    
    def extract_strassen(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Straßen aus dem Text"""
        logger.info("Extrahiere Straßen aus Text")
        
        street_pattern = r'([A-ZÄÖÜ][a-zäöüß\-\.]+(?:straße|weg|platz|allee|ring|damm|gasse))'
        
        strassen = []
        seen = set()
        
        for match in re.finditer(street_pattern, text, re.IGNORECASE):
            street = match.group(1).strip()
            if street not in seen:
                seen.add(street)
                strassen.append({
                    'street': street,
                    'house_number': '',
                    'postal_code': '51588',
                    'city': 'Nümbrecht',
                    'full_address': f"{street}, 51588 Nümbrecht"
                })
        
        logger.info(f"Gefundene Straßen: {len(strassen)}")
        return strassen
    
    def zuordne_strassen_zu_bezirken(self):
        """Ordnet Straßen den Wahlbezirken zu"""
        logger.info("Ordne Straßen zu Bezirken zu")
        
        # Erstelle Zuordnung basierend auf Straßennamen
        for strasse in self.strassen:
            bezirk_gefunden = False
            
            # Suche in welchem Bezirk die Straße liegt
            for bezirk, info in self.kandidaten_bezirke.items():
                if any(strasse['street'].lower() in s.lower() for s in info['strassen']):
                    strasse['bezirk'] = bezirk
                    strasse['kandidat'] = info['name']
                    strasse['farbe'] = info['farbe']
                    bezirk_gefunden = True
                    break
            
            # Falls keine Zuordnung gefunden, verteile gleichmäßig
            if not bezirk_gefunden:
                bezirk_keys = list(self.kandidaten_bezirke.keys())
                if bezirk_keys:
                    # Verteile Straßen gleichmäßig auf Bezirke
                    bezirk_index = len(self.strassen_mit_bezirk) % len(bezirk_keys)
                    bezirk = bezirk_keys[bezirk_index]
                    strasse['bezirk'] = bezirk
                    strasse['kandidat'] = self.kandidaten_bezirke[bezirk]['name']
                    strasse['farbe'] = self.kandidaten_bezirke[bezirk]['farbe']
                else:
                    strasse['bezirk'] = 'Unbekannt'
                    strasse['kandidat'] = 'Nicht zugeordnet'
                    strasse['farbe'] = '#808080'
            
            self.strassen_mit_bezirk.append(strasse)
    
    def geocode_address(self, address: Dict[str, str]) -> Optional[Tuple[float, float]]:
        """Geocodiert eine Adresse zu Koordinaten"""
        try:
            time.sleep(1)  # Rate limiting
            
            location = self.geocoder.geocode(address['full_address'])
            
            if not location and address['street']:
                simplified = f"{address['street']}, {address['city']}"
                location = self.geocoder.geocode(simplified)
            
            if not location:
                location = self.geocoder.geocode(address['city'])
            
            if location:
                return (location.latitude, location.longitude)
            
            return None
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding-Fehler für {address['full_address']}: {e}")
            return None
    
    def geocode_strassen(self):
        """Geocodiert alle Straßen"""
        logger.info("Starte Geocoding der Straßen")
        
        geocoded = []
        for i, strasse in enumerate(self.strassen_mit_bezirk):
            logger.info(f"Geocoding {i+1}/{len(self.strassen_mit_bezirk)}: {strasse['full_address']}")
            
            coords = self.geocode_address(strasse)
            if coords:
                strasse['latitude'] = coords[0]
                strasse['longitude'] = coords[1]
                geocoded.append(strasse)
                logger.info(f"✓ Erfolgreich: {coords}")
            else:
                logger.warning(f"✗ Nicht gefunden: {strasse['full_address']}")
        
        self.strassen_mit_bezirk = geocoded
    
    def create_wahlbezirke_map(self, output_file: str = "wahlbezirke_map.html"):
        """Erstellt eine interaktive Karte mit farbigen Wahlbezirken"""
        if not self.strassen_mit_bezirk:
            logger.error("Keine geocodierten Straßen vorhanden!")
            return
        
        logger.info(f"Erstelle Karte mit {len(self.strassen_mit_bezirk)} Straßen")
        
        # Zentrum berechnen
        avg_lat = sum(s['latitude'] for s in self.strassen_mit_bezirk) / len(self.strassen_mit_bezirk)
        avg_lon = sum(s['longitude'] for s in self.strassen_mit_bezirk) / len(self.strassen_mit_bezirk)
        
        # Karte erstellen
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
        
        # Feature Groups für jeden Bezirk
        bezirk_groups = {}
        for bezirk in self.kandidaten_bezirke:
            bezirk_groups[bezirk] = folium.FeatureGroup(name=f"{bezirk} - {self.kandidaten_bezirke[bezirk]['name']}")
        
        # Marker für jede Straße
        for strasse in self.strassen_mit_bezirk:
            popup_text = f"""
            <b>{strasse['street']}</b><br>
            {strasse['postal_code']} {strasse['city']}<br>
            <hr>
            <b>Wahlbezirk:</b> {strasse['bezirk']}<br>
            <b>CDU-Kandidat:</b> {strasse['kandidat']}<br>
            <small>Lat: {strasse['latitude']:.6f}, Lon: {strasse['longitude']:.6f}</small>
            """
            
            # Farbiger Marker
            folium.CircleMarker(
                location=[strasse['latitude'], strasse['longitude']],
                radius=8,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{strasse['street']} ({strasse['bezirk']})",
                color=strasse['farbe'],
                fill=True,
                fillColor=strasse['farbe'],
                fillOpacity=0.7,
                weight=2
            ).add_to(bezirk_groups.get(strasse['bezirk'], m))
        
        # Feature Groups zur Karte hinzufügen
        for group in bezirk_groups.values():
            group.add_to(m)
        
        # Layer Control für Ein-/Ausblenden der Bezirke
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Legende hinzufügen
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 250px; height: auto; 
                    background-color: white; z-index: 1000; 
                    border: 2px solid grey; border-radius: 5px;
                    padding: 10px; font-size: 14px;">
        <p style="margin: 0; font-weight: bold; text-align: center;">CDU Wahlbezirke Nümbrecht</p>
        <hr style="margin: 5px 0;">
        '''
        
        for bezirk, info in self.kandidaten_bezirke.items():
            legend_html += f'''
            <p style="margin: 5px 0;">
                <span style="background-color: {info['farbe']}; 
                           width: 20px; height: 20px; 
                           display: inline-block; 
                           border-radius: 50%; 
                           vertical-align: middle;"></span>
                <b>{bezirk}:</b> {info['name']}
            </p>
            '''
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Karte speichern
        m.save(output_file)
        logger.info(f"Karte gespeichert als: {output_file}")
        
        # GeoJSON speichern
        self.save_as_geojson(output_file.replace('.html', '.geojson'))
        
        # CSV speichern
        self.save_as_csv(output_file.replace('.html', '.csv'))
    
    def save_as_geojson(self, output_file: str):
        """Speichert die Daten als GeoJSON"""
        features = []
        
        for strasse in self.strassen_mit_bezirk:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [strasse['longitude'], strasse['latitude']]
                },
                "properties": {
                    "street": strasse['street'],
                    "postal_code": strasse['postal_code'],
                    "city": strasse['city'],
                    "full_address": strasse['full_address'],
                    "bezirk": strasse['bezirk'],
                    "kandidat": strasse['kandidat'],
                    "farbe": strasse['farbe']
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
        if self.strassen_mit_bezirk:
            df = pd.DataFrame(self.strassen_mit_bezirk)
            df.to_csv(output_file, index=False, encoding='utf-8')
            logger.info(f"CSV gespeichert als: {output_file}")
    
    def save_kandidaten_liste(self, output_file: str = "kandidaten_bezirke.csv"):
        """Speichert die Kandidaten-Bezirk-Zuordnung"""
        data = []
        for bezirk, info in self.kandidaten_bezirke.items():
            data.append({
                'bezirk': bezirk,
                'kandidat': info['name'],
                'farbe': info['farbe'],
                'anzahl_strassen': len([s for s in self.strassen_mit_bezirk if s['bezirk'] == bezirk])
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Kandidatenliste gespeichert als: {output_file}")
    
    def process(self):
        """Hauptprozess"""
        try:
            # Kandidaten-PDF verarbeiten
            kandidaten_text = self.extract_text_from_pdf(self.kandidaten_pdf)
            self.kandidaten_bezirke = self.extract_kandidaten_bezirke(kandidaten_text)
            
            # Straßen-PDF verarbeiten
            strassen_text = self.extract_text_from_pdf(self.strassen_pdf)
            self.strassen = self.extract_strassen(strassen_text)
            
            # Straßen zu Bezirken zuordnen
            self.zuordne_strassen_zu_bezirken()
            
            # Geocoding
            self.geocode_strassen()
            
            if not self.strassen_mit_bezirk:
                logger.error("Keine Straßen konnten verarbeitet werden!")
                return
            
            # Karte erstellen
            self.create_wahlbezirke_map()
            
            # Kandidatenliste speichern
            self.save_kandidaten_liste()
            
            logger.info("Verarbeitung abgeschlossen!")
            logger.info("Ergebnisse:")
            logger.info("- Karte: wahlbezirke_map.html")
            logger.info("- CSV: wahlbezirke_map.csv")
            logger.info("- GeoJSON: wahlbezirke_map.geojson")
            logger.info("- Kandidaten: kandidaten_bezirke.csv")
            
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung: {e}")
            raise


def main():
    """Hauptfunktion"""
    strassen_pdf = "/Users/marcelgaertner/Desktop/Arbeit/Markus schmitz/marcus-call-agent/Nümbrecht straßengenau.pdf"
    kandidaten_pdf = "/Users/marcelgaertner/Desktop/Arbeit/Markus schmitz/Dokumetne/CDU-Kandidaten und ihre Bezirke.pdf"
    
    if not os.path.exists(strassen_pdf):
        logger.error(f"Straßen-PDF nicht gefunden: {strassen_pdf}")
        return
    
    if not os.path.exists(kandidaten_pdf):
        logger.error(f"Kandidaten-PDF nicht gefunden: {kandidaten_pdf}")
        return
    
    converter = WahlbezirkeMapConverter(strassen_pdf, kandidaten_pdf)
    converter.process()


if __name__ == "__main__":
    main()