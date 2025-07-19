#!/usr/bin/env python3
"""
Erstellt eine erweiterte Wahlbezirke-Karte aus bereits geocodierten Daten
"""

import pandas as pd
import folium
from collections import defaultdict
import json

# Kandidaten-Farben
KANDIDATEN_FARBEN = {
    'Gisa Hauschildt': '#FF6B6B',
    'Christopher Seinsche': '#4ECDC4',
    'Björn Dittich': '#45B7D1',
    'Titzian Crisci': '#FFA07A',
    'Stephan Rühl': '#98D8C8',
    'Roger Adolphs': '#6C5CE7',
    'Frank Schmitz': '#A8E6CF',
    'Thomas Schlegel': '#FF8B94',
    'Jörg Reintsema': '#C7CEEA',
    'Dagmar Schmitz': '#FFDAB9',
    'Jörg Menne': '#E8B4B8',
    'Markus Lang': '#95E1D3',
    'Ulrike Herrgesell': '#F38181',
    'Thomas Hellbusch': '#AA96DA',
    'Philipp Beck': '#FCBAD3',
    'Manfred Henry Daub': '#FFD93D'
}

def main():
    # Lade die bereits geocodierten Daten
    df = pd.read_csv('wahlbezirke_map.csv')
    
    # Lade Wahlbezirk-Zuordnung für zusätzliche Infos
    with open('wahlbezirke_zuordnung.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        wahlbezirke = data['wahlbezirke']
    
    # Gruppiere nach Kandidaten
    kandidaten_bezirke = defaultdict(list)
    for wbz_key, wbz_data in wahlbezirke.items():
        kandidaten_bezirke[wbz_data['kandidat']].append(wbz_key)
    
    # Aktualisiere Farben in DataFrame basierend auf Kandidat
    df['kandidat_farbe'] = df['kandidat'].map(KANDIDATEN_FARBEN)
    
    # Zentrum berechnen
    avg_lat = df['latitude'].mean()
    avg_lon = df['longitude'].mean()
    
    # Karte erstellen
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
    
    # Feature Groups für jeden Kandidaten
    kandidaten_groups = {}
    for kandidat in sorted(kandidaten_bezirke.keys()):
        kandidaten_groups[kandidat] = folium.FeatureGroup(name=f"CDU: {kandidat}", show=True)
    
    # Marker für jede Straße
    for _, row in df.iterrows():
        popup_text = f"""
        <b>{row['street']}</b><br>
        {row['original']}<br>
        {row['postal_code']} {row['city']}<br>
        <hr>
        <b>Wahlbezirk:</b> {row['bezirk']}<br>
        <b>CDU-Kandidat/in:</b> {row['kandidat']}<br>
        <b>Wahlberechtigte im Bezirk:</b> {row['wahlberechtigte']}<br>
        <small>Lat: {row['latitude']:.6f}, Lon: {row['longitude']:.6f}</small>
        """
        
        # Marker zum Kandidaten-Group hinzufügen
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['street']} ({row['wbz']})",
            color=row['kandidat_farbe'],
            fill=True,
            fillColor=row['kandidat_farbe'],
            fillOpacity=0.7,
            weight=2
        ).add_to(kandidaten_groups[row['kandidat']])
    
    # Feature Groups zur Karte hinzufügen
    for group in kandidaten_groups.values():
        group.add_to(m)
    
    # Layer Control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Erweiterte interaktive Legende
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 420px; height: 650px; 
                background-color: white; z-index: 1000; 
                border: 2px solid grey; border-radius: 5px;
                padding: 15px; font-size: 12px;
                overflow-y: auto;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);">
    <p style="margin: 0; font-weight: bold; text-align: center; font-size: 18px; color: #333;">
        CDU Wahlbezirke Nümbrecht 2024
    </p>
    <hr style="margin: 10px 0;">
    
    <!-- Schnellauswahl Buttons -->
    <div style="margin: 15px 0;">
        <button onclick="showAllKandidaten()" 
                style="width: 100%; padding: 10px; background: #4CAF50; 
                       color: white; border: none; border-radius: 5px; 
                       cursor: pointer; font-weight: bold; font-size: 14px;
                       margin-bottom: 5px;">
            ✓ Alle Kandidaten anzeigen
        </button>
        <button onclick="hideAllKandidaten()" 
                style="width: 100%; padding: 10px; background: #f44336; 
                       color: white; border: none; border-radius: 5px; 
                       cursor: pointer; font-weight: bold; font-size: 14px;">
            ✗ Alle Kandidaten ausblenden
        </button>
    </div>
    
    <!-- Prominente Kandidaten -->
    <div style="background: #f0f0f0; padding: 10px; border-radius: 5px; margin: 15px 0;">
        <p style="font-weight: bold; margin: 0 0 8px 0; color: #555;">Kreistagskandidaten:</p>
        <div style="display: flex; gap: 5px; flex-wrap: wrap;">
            <button onclick="showOnlyKandidat('Thomas Schlegel')" 
                    style="padding: 8px 15px; background: #FF8B94; 
                           color: white; border: none; border-radius: 5px; 
                           cursor: pointer; font-weight: bold;">
                Thomas Schlegel
            </button>
            <button onclick="showOnlyKandidat('Marcus Schmitz')" 
                    style="padding: 8px 15px; background: #667eea; 
                           color: white; border: none; border-radius: 5px; 
                           cursor: pointer; font-weight: bold;">
                Marcus Schmitz*
            </button>
        </div>
        <small style="color: #666; font-style: italic;">*falls Marcus Schmitz kandidiert</small>
    </div>
    
    <hr style="margin: 15px 0;">
    
    <!-- Kandidaten-Liste -->
    <p style="font-weight: bold; margin: 10px 0 5px 0; color: #333;">Alle CDU-Kandidaten:</p>
    <div style="max-height: 320px; overflow-y: auto; border: 1px solid #ddd; border-radius: 5px; padding: 5px;">
    '''
    
    # Kandidaten mit ihren Bezirken sortiert
    for kandidat in sorted(kandidaten_bezirke.keys()):
        farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
        bezirke = kandidaten_bezirke[kandidat]
        gesamt_wahlberechtigte = sum(wahlbezirke[wbz]['wahlberechtigte'] for wbz in bezirke)
        anzahl_strassen = len(df[df['kandidat'] == kandidat])
        
        legend_html += f'''
        <div style="margin: 5px 0; padding: 8px; border: 1px solid #eee; border-radius: 5px;
                    background: #fafafa; cursor: pointer; transition: all 0.2s;"
             onmouseover="this.style.background='#f0f0f0'"
             onmouseout="this.style.background='#fafafa'"
             onclick="showOnlyKandidat('{kandidat}')">
            <div style="display: flex; align-items: center;">
                <span style="background-color: {farbe}; 
                           width: 25px; height: 25px; 
                           display: inline-block; 
                           border-radius: 50%;
                           margin-right: 12px;
                           border: 2px solid white;
                           box-shadow: 0 0 5px rgba(0,0,0,0.2);"></span>
                <div style="flex: 1;">
                    <b style="font-size: 13px; color: #333;">{kandidat}</b><br>
                    <small style="color: #666;">
                        Bezirke: {', '.join(bezirke)}<br>
                        {gesamt_wahlberechtigte} Wahlberechtigte | {anzahl_strassen} Straßen
                    </small>
                </div>
            </div>
        </div>
        '''
    
    legend_html += '''
    </div>
    
    <div style="margin-top: 15px; padding: 10px; background: #e8f5e9; border-radius: 5px;">
        <small style="color: #666;">
            <b>Tipp:</b> Klicken Sie auf einen Kandidaten, um nur dessen Bezirke anzuzeigen.
            Nutzen Sie die Layer-Kontrolle links für detaillierte Auswahl.
        </small>
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
    
    function hideAllKandidaten() {
        if (!leafletMap) return;
        
        // Alle Layer ausblenden
        for (var layerName in allLayers) {
            leafletMap.removeLayer(allLayers[layerName]);
        }
    }
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Karte speichern
    m.save('wahlbezirke_map_enhanced.html')
    print("✓ Erweiterte Karte erstellt: wahlbezirke_map_enhanced.html")
    
    # Kandidaten-Übersicht erstellen
    kandidaten_data = []
    for kandidat, bezirke in sorted(kandidaten_bezirke.items()):
        gesamt_wahlberechtigte = sum(wahlbezirke[wbz]['wahlberechtigte'] for wbz in bezirke)
        anzahl_strassen = len(df[df['kandidat'] == kandidat])
        
        kandidaten_data.append({
            'kandidat': kandidat,
            'anzahl_bezirke': len(bezirke),
            'bezirke': ', '.join(bezirke),
            'gesamt_wahlberechtigte': gesamt_wahlberechtigte,
            'anzahl_strassen_auf_karte': anzahl_strassen,
            'farbe': KANDIDATEN_FARBEN.get(kandidat, '#808080')
        })
    
    kandidaten_df = pd.DataFrame(kandidaten_data)
    kandidaten_df.to_csv('kandidaten_uebersicht.csv', index=False, encoding='utf-8')
    print("✓ Kandidaten-Übersicht erstellt: kandidaten_uebersicht.csv")

if __name__ == "__main__":
    main()