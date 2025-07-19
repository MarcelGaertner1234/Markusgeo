#!/usr/bin/env python3
"""
Wahlbezirke Karte für Nümbrecht
Korrekte Zuordnung der 16 CDU-Kandidaten zu ihren Wahlbezirken
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

# Farbpalette für 16 Wahlbezirke
COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#6C5CE7', '#A8E6CF', '#FF8B94', '#C7CEEA', '#FFDAB9',
    '#E8B4B8', '#95E1D3', '#F38181', '#AA96DA', '#FCBAD3',
    '#FFD93D'  # 16. Farbe
]

class WahlbezirkeMapConverter:
    def __init__(self, strassen_pdf: str, zuordnung_json: str):
        self.strassen_pdf = strassen_pdf
        self.zuordnung_json = zuordnung_json
        self.geocoder = Nominatim(user_agent="wahlbezirke_map_converter")
        self.strassen = []
        self.wahlbezirke = {}
        self.strassen_mit_bezirk = []
        
    def load_wahlbezirke_zuordnung(self):
        """Lädt die Wahlbezirk-Zuordnung aus JSON"""
        logger.info(f"Lade Wahlbezirk-Zuordnung aus: {self.zuordnung_json}")
        
        with open(self.zuordnung_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.wahlbezirke = data['wahlbezirke']
        
        # Farben zuweisen
        for i, (wbz_key, wbz_data) in enumerate(self.wahlbezirke.items()):
            wbz_data['farbe'] = COLORS[i % len(COLORS)]
            
        logger.info(f"Geladen: {len(self.wahlbezirke)} Wahlbezirke")
    
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
    
    def extract_strassen(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Straßen aus dem Text"""
        logger.info("Extrahiere Straßen aus Text")
        
        street_pattern = r'([A-ZÄÖÜ][a-zäöüß\-\.]+(?:straße|weg|platz|allee|ring|damm|gasse))'
        
        strassen = []
        seen = set()
        
        # Sammle alle Straßen aus den Wahlbezirken
        for wbz_key, wbz_data in self.wahlbezirke.items():
            if 'strassen' in wbz_data:
                for strasse in wbz_data['strassen']:
                    # Normalisiere Straßennamen (entferne Hausnummernbereiche)
                    clean_strasse = re.sub(r'\s*-.*$', '', strasse).strip()
                    if clean_strasse and clean_strasse not in seen:
                        seen.add(clean_strasse)
                        strassen.append({
                            'street': clean_strasse,
                            'original': strasse,
                            'house_number': '',
                            'postal_code': '51588',
                            'city': 'Nümbrecht',
                            'full_address': f"{clean_strasse}, 51588 Nümbrecht",
                            'wbz': wbz_key
                        })
        
        # Zusätzlich aus PDF-Text extrahieren
        for match in re.finditer(street_pattern, text, re.IGNORECASE):
            street = match.group(1).strip()
            if street not in seen:
                seen.add(street)
                strassen.append({
                    'street': street,
                    'original': street,
                    'house_number': '',
                    'postal_code': '51588',
                    'city': 'Nümbrecht',
                    'full_address': f"{street}, 51588 Nümbrecht",
                    'wbz': None  # Wird später zugeordnet
                })
        
        logger.info(f"Gefundene Straßen: {len(strassen)}")
        return strassen
    
    def zuordne_strassen_zu_bezirken(self):
        """Ordnet Straßen den korrekten Wahlbezirken zu"""
        logger.info("Ordne Straßen zu Wahlbezirken zu")
        
        for strasse in self.strassen:
            if strasse.get('wbz'):
                # Bereits zugeordnet
                wbz_key = strasse['wbz']
                wbz_data = self.wahlbezirke[wbz_key]
                strasse['bezirk'] = f"{wbz_key} - {wbz_data['name']}"
                strasse['kandidat'] = wbz_data['kandidat']
                strasse['farbe'] = wbz_data['farbe']
                strasse['wahlberechtigte'] = wbz_data['wahlberechtigte']
                self.strassen_mit_bezirk.append(strasse)
            else:
                # Versuche Zuordnung über Straßennamen
                zugeordnet = False
                for wbz_key, wbz_data in self.wahlbezirke.items():
                    if 'strassen' in wbz_data:
                        for wbz_strasse in wbz_data['strassen']:
                            # Normalisiere für Vergleich
                            clean_wbz_strasse = re.sub(r'\s*-.*$', '', wbz_strasse).strip()
                            if strasse['street'].lower() == clean_wbz_strasse.lower():
                                strasse['bezirk'] = f"{wbz_key} - {wbz_data['name']}"
                                strasse['kandidat'] = wbz_data['kandidat']
                                strasse['farbe'] = wbz_data['farbe']
                                strasse['wahlberechtigte'] = wbz_data['wahlberechtigte']
                                strasse['wbz'] = wbz_key
                                self.strassen_mit_bezirk.append(strasse)
                                zugeordnet = True
                                break
                    if zugeordnet:
                        break
                
                if not zugeordnet:
                    logger.warning(f"Straße nicht zugeordnet: {strasse['street']}")
    
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
        """Erstellt eine interaktive Karte mit den 16 Wahlbezirken"""
        if not self.strassen_mit_bezirk:
            logger.error("Keine geocodierten Straßen vorhanden!")
            return
        
        logger.info(f"Erstelle Karte mit {len(self.strassen_mit_bezirk)} Straßen")
        
        # Zentrum berechnen
        avg_lat = sum(s['latitude'] for s in self.strassen_mit_bezirk) / len(self.strassen_mit_bezirk)
        avg_lon = sum(s['longitude'] for s in self.strassen_mit_bezirk) / len(self.strassen_mit_bezirk)
        
        # Karte erstellen
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
        
        # Feature Groups für jeden Wahlbezirk
        bezirk_groups = {}
        for wbz_key, wbz_data in self.wahlbezirke.items():
            group_name = f"{wbz_key} - {wbz_data['name']} ({wbz_data['kandidat']})"
            bezirk_groups[wbz_key] = folium.FeatureGroup(name=group_name)
        
        # Marker für jede Straße
        for strasse in self.strassen_mit_bezirk:
            popup_text = f"""
            <b>{strasse['street']}</b><br>
            {strasse['original']}<br>
            {strasse['postal_code']} {strasse['city']}<br>
            <hr>
            <b>Wahlbezirk:</b> {strasse['bezirk']}<br>
            <b>CDU-Kandidat/in:</b> {strasse['kandidat']}<br>
            <b>Wahlberechtigte im Bezirk:</b> {strasse['wahlberechtigte']}<br>
            <small>Lat: {strasse['latitude']:.6f}, Lon: {strasse['longitude']:.6f}</small>
            """
            
            # Farbiger Marker
            folium.CircleMarker(
                location=[strasse['latitude'], strasse['longitude']],
                radius=8,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{strasse['street']} ({strasse['kandidat']})",
                color=strasse['farbe'],
                fill=True,
                fillColor=strasse['farbe'],
                fillOpacity=0.7,
                weight=2
            ).add_to(bezirk_groups.get(strasse['wbz'], m))
        
        # Feature Groups zur Karte hinzufügen
        for group in bezirk_groups.values():
            group.add_to(m)
        
        # Layer Control für Ein-/Ausblenden der Bezirke
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Legende hinzufügen
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 350px; height: 500px; 
                    background-color: white; z-index: 1000; 
                    border: 2px solid grey; border-radius: 5px;
                    padding: 10px; font-size: 12px;
                    overflow-y: auto;">
        <p style="margin: 0; font-weight: bold; text-align: center; font-size: 14px;">
            CDU Wahlbezirke Nümbrecht 2024
        </p>
        <hr style="margin: 5px 0;">
        <table style="width: 100%; font-size: 11px;">
        '''
        
        for wbz_key, wbz_data in sorted(self.wahlbezirke.items()):
            legend_html += f'''
            <tr>
                <td style="width: 20px;">
                    <span style="background-color: {wbz_data['farbe']}; 
                               width: 15px; height: 15px; 
                               display: inline-block; 
                               border-radius: 50%;"></span>
                </td>
                <td style="padding-left: 5px;">
                    <b>{wbz_key}</b> - {wbz_data['name']}<br>
                    <span style="font-size: 10px;">{wbz_data['kandidat']} ({wbz_data['wahlberechtigte']} Wahlber.)</span>
                </td>
            </tr>
            '''
        
        legend_html += '''
        </table>
        </div>
        '''
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
                    "original": strasse['original'],
                    "postal_code": strasse['postal_code'],
                    "city": strasse['city'],
                    "full_address": strasse['full_address'],
                    "wbz": strasse['wbz'],
                    "bezirk": strasse['bezirk'],
                    "kandidat": strasse['kandidat'],
                    "wahlberechtigte": strasse['wahlberechtigte'],
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
        for wbz_key, wbz_data in sorted(self.wahlbezirke.items()):
            anzahl_strassen = len([s for s in self.strassen_mit_bezirk if s['wbz'] == wbz_key])
            data.append({
                'wbz': wbz_key,
                'name': wbz_data['name'],
                'kandidat': wbz_data['kandidat'],
                'wahlberechtigte': wbz_data['wahlberechtigte'],
                'farbe': wbz_data['farbe'],
                'anzahl_strassen_auf_karte': anzahl_strassen
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Kandidatenliste gespeichert als: {output_file}")
    
    def process(self):
        """Hauptprozess"""
        try:
            # Wahlbezirk-Zuordnung laden
            self.load_wahlbezirke_zuordnung()
            
            # Straßen aus Zuordnung und PDF extrahieren
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
    zuordnung_json = "/Users/marcelgaertner/Desktop/Arbeit/Markus schmitz/marcus-call-agent/wahlbezirke_zuordnung.json"
    
    if not os.path.exists(strassen_pdf):
        logger.error(f"Straßen-PDF nicht gefunden: {strassen_pdf}")
        return
    
    if not os.path.exists(zuordnung_json):
        logger.error(f"Zuordnungs-JSON nicht gefunden: {zuordnung_json}")
        return
    
    converter = WahlbezirkeMapConverter(strassen_pdf, zuordnung_json)
    converter.process()


if __name__ == "__main__":
    main()