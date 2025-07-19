#!/usr/bin/env python3
"""
Erweiterte Wahlbezirke Karte für Nümbrecht
Mit Kandidaten-Gruppierung und interaktiven Kontrollen
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
from collections import defaultdict

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Farbpalette für Kandidaten (nicht mehr für einzelne Bezirke)
KANDIDATEN_FARBEN = {
    'Gisa Hauschildt': '#FF6B6B',
    'Christopher Seinsche': '#4ECDC4',
    'Björn Dittich': '#45B7D1',
    'Titzian Crisci': '#FFA07A',
    'Stephan Rühl': '#98D8C8',
    'Roger Adolphs': '#6C5CE7',
    'Frank Schmitz': '#A8E6CF',
    'Thomas Schlegel': '#FF8B94',  # Hervorgehoben
    'Jörg Reintsema': '#C7CEEA',
    'Dagmar Schmitz': '#FFDAB9',
    'Jörg Menne': '#E8B4B8',
    'Markus Lang': '#95E1D3',
    'Ulrike Herrgesell': '#F38181',
    'Thomas Hellbusch': '#AA96DA',
    'Philipp Beck': '#FCBAD3',
    'Manfred Henry Daub': '#FFD93D'
}

class EnhancedWahlbezirkeMapConverter:
    def __init__(self, strassen_pdf: str, zuordnung_json: str):
        self.strassen_pdf = strassen_pdf
        self.zuordnung_json = zuordnung_json
        self.geocoder = Nominatim(user_agent="wahlbezirke_map_converter")
        self.strassen = []
        self.wahlbezirke = {}
        self.strassen_mit_bezirk = []
        self.kandidaten_bezirke = defaultdict(list)  # Kandidat -> Liste von Bezirken
        
    def load_wahlbezirke_zuordnung(self):
        """Lädt die Wahlbezirk-Zuordnung aus JSON"""
        logger.info(f"Lade Wahlbezirk-Zuordnung aus: {self.zuordnung_json}")
        
        with open(self.zuordnung_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.wahlbezirke = data['wahlbezirke']
        
        # Kandidaten gruppieren
        for wbz_key, wbz_data in self.wahlbezirke.items():
            kandidat = wbz_data['kandidat']
            self.kandidaten_bezirke[kandidat].append(wbz_key)
            # Farbe basierend auf Kandidat zuweisen
            wbz_data['farbe'] = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            
        logger.info(f"Geladen: {len(self.wahlbezirke)} Wahlbezirke für {len(self.kandidaten_bezirke)} Kandidaten")
    
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
    
    def create_enhanced_wahlbezirke_map(self, output_file: str = "wahlbezirke_map_enhanced.html"):
        """Erstellt eine erweiterte interaktive Karte mit Kandidaten-Gruppierung"""
        if not self.strassen_mit_bezirk:
            logger.error("Keine geocodierten Straßen vorhanden!")
            return
        
        logger.info(f"Erstelle erweiterte Karte mit {len(self.strassen_mit_bezirk)} Straßen")
        
        # Zentrum berechnen
        avg_lat = sum(s['latitude'] for s in self.strassen_mit_bezirk) / len(self.strassen_mit_bezirk)
        avg_lon = sum(s['longitude'] for s in self.strassen_mit_bezirk) / len(self.strassen_mit_bezirk)
        
        # Karte erstellen
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
        
        # Feature Groups für jeden Kandidaten
        kandidaten_groups = {}
        for kandidat in sorted(self.kandidaten_bezirke.keys()):
            kandidaten_groups[kandidat] = folium.FeatureGroup(name=f"CDU: {kandidat}", show=True)
        
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
            
            # Marker zum Kandidaten-Group hinzufügen
            folium.CircleMarker(
                location=[strasse['latitude'], strasse['longitude']],
                radius=8,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{strasse['street']} ({strasse['wbz']})",
                color=strasse['farbe'],
                fill=True,
                fillColor=strasse['farbe'],
                fillOpacity=0.7,
                weight=2
            ).add_to(kandidaten_groups[strasse['kandidat']])
        
        # Feature Groups zur Karte hinzufügen
        for group in kandidaten_groups.values():
            group.add_to(m)
        
        # Layer Control
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Erweiterte interaktive Legende mit Kandidaten-Buttons
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 400px; height: 600px; 
                    background-color: white; z-index: 1000; 
                    border: 2px solid grey; border-radius: 5px;
                    padding: 15px; font-size: 12px;
                    overflow-y: auto;">
        <p style="margin: 0; font-weight: bold; text-align: center; font-size: 16px;">
            CDU Wahlbezirke Nümbrecht 2024
        </p>
        <hr style="margin: 10px 0;">
        
        <!-- Prominente Kandidaten -->
        <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <p style="font-weight: bold; margin: 0 0 5px 0;">Kreistagskandidaten:</p>
            <button onclick="showOnlyKandidat('Thomas Schlegel')" 
                    style="margin: 2px; padding: 5px 10px; background: #FF8B94; 
                           color: white; border: none; border-radius: 3px; cursor: pointer;">
                Thomas Schlegel
            </button>
        </div>
        
        <!-- Alle Kandidaten Buttons -->
        <div style="margin: 10px 0;">
            <button onclick="showAllKandidaten()" 
                    style="width: 100%; padding: 8px; background: #4CAF50; 
                           color: white; border: none; border-radius: 3px; 
                           cursor: pointer; font-weight: bold;">
                Alle Kandidaten anzeigen
            </button>
        </div>
        
        <hr style="margin: 10px 0;">
        
        <!-- Kandidaten-Liste -->
        <p style="font-weight: bold; margin: 10px 0 5px 0;">Kandidaten nach Wahlbezirk:</p>
        <div style="max-height: 350px; overflow-y: auto;">
        '''
        
        # Kandidaten mit ihren Bezirken
        for kandidat in sorted(self.kandidaten_bezirke.keys()):
            farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            bezirke = self.kandidaten_bezirke[kandidat]
            gesamt_wahlberechtigte = sum(self.wahlbezirke[wbz]['wahlberechtigte'] for wbz in bezirke)
            
            legend_html += f'''
            <div style="margin: 5px 0; padding: 5px; border: 1px solid #ddd; border-radius: 3px;">
                <div style="display: flex; align-items: center; cursor: pointer;"
                     onclick="showOnlyKandidat('{kandidat}')">
                    <span style="background-color: {farbe}; 
                               width: 20px; height: 20px; 
                               display: inline-block; 
                               border-radius: 50%;
                               margin-right: 10px;"></span>
                    <div style="flex: 1;">
                        <b>{kandidat}</b><br>
                        <small>Bezirke: {', '.join(bezirke)}<br>
                        Wahlberechtigte: {gesamt_wahlberechtigte}</small>
                    </div>
                </div>
            </div>
            '''
        
        legend_html += '''
        </div>
        </div>
        
        <script>
        // Globale Referenz zur Karte
        var leafletMap = null;
        var allLayers = {};
        
        // Warte bis die Karte geladen ist
        setTimeout(function() {
            // Finde die Leaflet-Karte
            var mapElements = document.getElementsByClassName('folium-map');
            if (mapElements.length > 0) {
                var mapId = mapElements[0].id;
                leafletMap = window[mapId];
                
                // Sammle alle Layer
                leafletMap.eachLayer(function(layer) {
                    if (layer instanceof L.FeatureGroup && layer.options && layer.options.name) {
                        allLayers[layer.options.name] = layer;
                    }
                });
            }
        }, 1000);
        
        function showOnlyKandidat(kandidatName) {
            if (!leafletMap) return;
            
            // Alle Layer ausblenden
            for (var layerName in allLayers) {
                leafletMap.removeLayer(allLayers[layerName]);
            }
            
            // Nur den gewählten Kandidaten anzeigen
            var targetLayerName = 'CDU: ' + kandidatName;
            if (allLayers[targetLayerName]) {
                leafletMap.addLayer(allLayers[targetLayerName]);
            }
        }
        
        function showAllKandidaten() {
            if (!leafletMap) return;
            
            // Alle Layer wieder anzeigen
            for (var layerName in allLayers) {
                leafletMap.addLayer(allLayers[layerName]);
            }
        }
        </script>
        '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Karte speichern
        m.save(output_file)
        logger.info(f"Erweiterte Karte gespeichert als: {output_file}")
        
        # GeoJSON speichern
        self.save_as_geojson(output_file.replace('.html', '.geojson'))
        
        # CSV speichern
        self.save_as_csv(output_file.replace('.html', '.csv'))
        
        # Kandidaten-Übersicht speichern
        self.save_kandidaten_uebersicht()
    
    def save_kandidaten_uebersicht(self, output_file: str = "kandidaten_uebersicht.csv"):
        """Speichert eine Übersicht der Kandidaten mit ihren Bezirken"""
        data = []
        for kandidat, bezirke in sorted(self.kandidaten_bezirke.items()):
            gesamt_wahlberechtigte = sum(self.wahlbezirke[wbz]['wahlberechtigte'] for wbz in bezirke)
            anzahl_strassen = len([s for s in self.strassen_mit_bezirk if s['kandidat'] == kandidat])
            
            data.append({
                'kandidat': kandidat,
                'anzahl_bezirke': len(bezirke),
                'bezirke': ', '.join(bezirke),
                'gesamt_wahlberechtigte': gesamt_wahlberechtigte,
                'anzahl_strassen_auf_karte': anzahl_strassen,
                'farbe': KANDIDATEN_FARBEN.get(kandidat, '#808080')
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Kandidaten-Übersicht gespeichert als: {output_file}")
    
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
    
    def process(self):
        """Hauptprozess"""
        try:
            # Wahlbezirk-Zuordnung laden
            self.load_wahlbezirke_zuordnung()
            
            # Straßen aus Zuordnung extrahieren
            strassen_text = self.extract_text_from_pdf(self.strassen_pdf)
            self.strassen = self.extract_strassen(strassen_text)
            
            # Straßen zu Bezirken zuordnen
            self.zuordne_strassen_zu_bezirken()
            
            # Geocoding
            self.geocode_strassen()
            
            if not self.strassen_mit_bezirk:
                logger.error("Keine Straßen konnten verarbeitet werden!")
                return
            
            # Erweiterte Karte erstellen
            self.create_enhanced_wahlbezirke_map()
            
            logger.info("Verarbeitung abgeschlossen!")
            logger.info("Ergebnisse:")
            logger.info("- Erweiterte Karte: wahlbezirke_map_enhanced.html")
            logger.info("- CSV: wahlbezirke_map_enhanced.csv")
            logger.info("- GeoJSON: wahlbezirke_map_enhanced.geojson")
            logger.info("- Kandidaten-Übersicht: kandidaten_uebersicht.csv")
            
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
    
    converter = EnhancedWahlbezirkeMapConverter(strassen_pdf, zuordnung_json)
    converter.process()


if __name__ == "__main__":
    main()