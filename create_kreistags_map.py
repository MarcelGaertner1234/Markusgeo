#!/usr/bin/env python3
"""
Erstellt eine erweiterte Wahlbezirke-Karte mit Kreistagskandidaten-Zuordnung
"""

import pandas as pd
import folium
from collections import defaultdict
import json

# Farbschema
KREISTAGS_FARBEN = {
    'Marcus Schmitz': '#1976D2',  # Blau für Kreis-WBZ 1
    'Thomas Schlegel': '#D32F2F'   # Rot für Kreis-WBZ 2
}

# Kandidaten-Farben (innerhalb der Kreistagskandidaten-Gruppen)
KANDIDATEN_FARBEN = {
    # Marcus Schmitz Gruppe (Blautöne)
    'Gisa Hauschildt': '#0D47A1',
    'Jörg Reintsema': '#1565C0',
    'Ulrike Herrgesell': '#1976D2',
    'Thomas Hellbusch': '#1E88E5',
    'Philipp Beck': '#2196F3',
    'Manfred Henry Daub': '#42A5F5',
    'Christopher Seinsche': '#64B5F6',
    'Björn Dittich': '#90CAF9',
    
    # Thomas Schlegel Gruppe (Rottöne)
    'Dagmar Schmitz': '#B71C1C',
    'Jörg Menne': '#C62828',
    'Markus Lang': '#D32F2F',
    'Titzian Crisci': '#E53935',
    'Stephan Rühl': '#F44336',
    'Roger Adolphs': '#EF5350',
    'Frank Schmitz': '#E57373',
    'Thomas Schlegel': '#EF9A9A'
}

def main():
    # Lade die Daten
    df = pd.read_csv('wahlbezirke_map.csv')
    
    with open('wahlbezirke_zuordnung.json', 'r', encoding='utf-8') as f:
        wahlbezirke_data = json.load(f)
        wahlbezirke = wahlbezirke_data['wahlbezirke']
    
    with open('kreistagskandidaten_zuordnung.json', 'r', encoding='utf-8') as f:
        kreistags_data = json.load(f)
        kreistagskandidaten = kreistags_data['kreistagskandidaten']
    
    # Aktualisiere Farben basierend auf Kreistagskandidaten-Zuordnung
    df['kandidat_farbe'] = df['kandidat'].map(KANDIDATEN_FARBEN)
    
    # Füge Kreistagskandidaten-Info hinzu
    df['kreistagkandidat'] = ''
    for kreistagkandidat, info in kreistagskandidaten.items():
        for kandidat in info['kandidaten']:
            df.loc[df['kandidat'] == kandidat, 'kreistagkandidat'] = kreistagkandidat
    
    # Zentrum berechnen
    avg_lat = df['latitude'].mean()
    avg_lon = df['longitude'].mean()
    
    # Karte erstellen
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
    
    # Feature Groups für Kreistagskandidaten
    kreistags_groups = {}
    for kreistagkandidat in kreistagskandidaten.keys():
        kreistags_groups[kreistagkandidat] = folium.FeatureGroup(
            name=f"Kreistagkandidat: {kreistagkandidat}", 
            show=True
        )
    
    # Feature Groups für einzelne Kandidaten
    kandidaten_groups = {}
    for _, row in df.iterrows():
        if row['kandidat'] not in kandidaten_groups:
            kandidaten_groups[row['kandidat']] = folium.FeatureGroup(
                name=f"CDU: {row['kandidat']}", 
                show=False
            )
    
    # Marker erstellen
    for _, row in df.iterrows():
        popup_text = f"""
        <b>{row['street']}</b><br>
        {row['original']}<br>
        {row['postal_code']} {row['city']}<br>
        <hr>
        <b>Wahlbezirk:</b> {row['bezirk']}<br>
        <b>CDU-Kandidat/in:</b> {row['kandidat']}<br>
        <b>Kreistagkandidat:</b> {row['kreistagkandidat']}<br>
        <b>Wahlberechtigte:</b> {row['wahlberechtigte']}<br>
        <small>Lat: {row['latitude']:.6f}, Lon: {row['longitude']:.6f}</small>
        """
        
        marker = folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['street']} ({row['wbz']})",
            color=row['kandidat_farbe'],
            fill=True,
            fillColor=row['kandidat_farbe'],
            fillOpacity=0.7,
            weight=2
        )
        
        # Zu beiden Groups hinzufügen
        marker.add_to(kreistags_groups[row['kreistagkandidat']])
        marker_copy = folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['street']} ({row['wbz']})",
            color=row['kandidat_farbe'],
            fill=True,
            fillColor=row['kandidat_farbe'],
            fillOpacity=0.7,
            weight=2
        )
        marker_copy.add_to(kandidaten_groups[row['kandidat']])
    
    # Groups zur Karte hinzufügen
    for group in kreistags_groups.values():
        group.add_to(m)
    for group in kandidaten_groups.values():
        group.add_to(m)
    
    # Layer Control
    folium.LayerControl(collapsed=True).add_to(m)
    
    # Erweiterte einklappbare Legende
    legend_html = '''
    <div id="legend-container" style="position: fixed; 
                bottom: 20px; right: 20px; width: 450px;
                background-color: white; z-index: 1000; 
                border: 2px solid #333; border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.3);
                transition: all 0.3s ease;">
        
        <!-- Header mit Toggle -->
        <div style="background: linear-gradient(135deg, #1976D2 0%, #D32F2F 100%); 
                    color: white; padding: 15px; border-radius: 8px 8px 0 0;
                    cursor: pointer; user-select: none;"
             onclick="toggleLegend()">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 18px;">CDU Wahlbezirke Nümbrecht 2024</h3>
                <span id="toggle-icon" style="font-size: 20px;">▼</span>
            </div>
        </div>
        
        <!-- Inhalt -->
        <div id="legend-content" style="padding: 15px; max-height: 600px; overflow-y: auto;">
            
            <!-- Kreistagskandidaten Hauptkontrolle -->
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">🏛️ Kreistagskandidaten</h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                    <button onclick="showKreistagkandidat('Marcus Schmitz')" 
                            style="padding: 12px; background: #1976D2; 
                                   color: white; border: none; border-radius: 5px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   transition: all 0.2s;">
                        Marcus Schmitz<br>
                        <small style="font-weight: normal;">Kreis-WBZ 1 (8 Bezirke)</small>
                    </button>
                    <button onclick="showKreistagkandidat('Thomas Schlegel')" 
                            style="padding: 12px; background: #D32F2F; 
                                   color: white; border: none; border-radius: 5px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   transition: all 0.2s;">
                        Thomas Schlegel<br>
                        <small style="font-weight: normal;">Kreis-WBZ 2 (8 Bezirke)</small>
                    </button>
                </div>
                
                <div style="display: flex; gap: 5px;">
                    <button onclick="showBothKreistagkandidaten()" 
                            style="flex: 1; padding: 10px; background: #4CAF50; 
                                   color: white; border: none; border-radius: 5px; 
                                   cursor: pointer; font-weight: bold;">
                        ✓ Beide anzeigen
                    </button>
                    <button onclick="hideAllLayers()" 
                            style="flex: 1; padding: 10px; background: #f44336; 
                                   color: white; border: none; border-radius: 5px; 
                                   cursor: pointer; font-weight: bold;">
                        ✗ Alle ausblenden
                    </button>
                </div>
            </div>
            
            <!-- Filter-Optionen -->
            <div style="margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #333;">🔍 Anzeigeoptionen</h4>
                <label style="display: flex; align-items: center; margin-bottom: 5px; cursor: pointer;">
                    <input type="radio" name="viewMode" value="kreistag" checked 
                           onchange="updateViewMode()" style="margin-right: 8px;">
                    Nach Kreistagskandidaten gruppiert
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="radio" name="viewMode" value="kandidaten" 
                           onchange="updateViewMode()" style="margin-right: 8px;">
                    Einzelne Kandidaten anzeigen
                </label>
            </div>
            
            <hr style="margin: 15px 0;">
            
            <!-- Kandidaten-Details -->
            <div id="kandidaten-details">
                <h4 style="margin: 0 0 10px 0; color: #333;">👥 Kandidaten nach Kreistagkandidat</h4>
                
                <!-- Marcus Schmitz Gruppe -->
                <div style="margin-bottom: 15px;">
                    <h5 style="color: #1976D2; margin: 10px 0;">Marcus Schmitz - Kreis-WBZ 1</h5>
                    <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; 
                                border-radius: 5px; padding: 5px;">
    '''
    
    # Marcus Schmitz Kandidaten
    marcus_kandidaten = kreistagskandidaten['Marcus Schmitz']['kandidaten']
    for kandidat in marcus_kandidaten:
        kandidat_data = df[df['kandidat'] == kandidat].iloc[0] if len(df[df['kandidat'] == kandidat]) > 0 else None
        if kandidat_data is not None:
            farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            wbz = kandidat_data['wbz']
            wahlber = kandidat_data['wahlberechtigte']
            anzahl_str = len(df[df['kandidat'] == kandidat])
            
            legend_html += f'''
            <div style="margin: 3px; padding: 5px; background: #f9f9f9; 
                        border-radius: 3px; cursor: pointer;"
                 onclick="showSingleKandidat('{kandidat}')"
                 onmouseover="this.style.background='#e9e9e9'"
                 onmouseout="this.style.background='#f9f9f9'">
                <span style="background-color: {farbe}; width: 15px; height: 15px; 
                           display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
                <small><b>{kandidat}</b> ({wbz}) - {wahlber} Wahlber. | {anzahl_str} Str.</small>
            </div>
            '''
    
    legend_html += '''
                    </div>
                </div>
                
                <!-- Thomas Schlegel Gruppe -->
                <div>
                    <h5 style="color: #D32F2F; margin: 10px 0;">Thomas Schlegel - Kreis-WBZ 2</h5>
                    <div style="max-height: 200px; overflow-y: auto; border: 1px solid #ddd; 
                                border-radius: 5px; padding: 5px;">
    '''
    
    # Thomas Schlegel Kandidaten
    thomas_kandidaten = kreistagskandidaten['Thomas Schlegel']['kandidaten']
    for kandidat in thomas_kandidaten:
        kandidat_data = df[df['kandidat'] == kandidat].iloc[0] if len(df[df['kandidat'] == kandidat]) > 0 else None
        if kandidat_data is not None:
            farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            wbz = kandidat_data['wbz']
            wahlber = kandidat_data['wahlberechtigte']
            anzahl_str = len(df[df['kandidat'] == kandidat])
            
            legend_html += f'''
            <div style="margin: 3px; padding: 5px; background: #f9f9f9; 
                        border-radius: 3px; cursor: pointer;"
                 onclick="showSingleKandidat('{kandidat}')"
                 onmouseover="this.style.background='#e9e9e9'"
                 onmouseout="this.style.background='#f9f9f9'">
                <span style="background-color: {farbe}; width: 15px; height: 15px; 
                           display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
                <small><b>{kandidat}</b> ({wbz}) - {wahlber} Wahlber. | {anzahl_str} Str.</small>
            </div>
            '''
    
    legend_html += '''
                    </div>
                </div>
            </div>
            
            <!-- Status -->
            <div style="margin-top: 15px; padding: 10px; background: #e8f5e9; 
                        border-radius: 5px; text-align: center;">
                <small id="status-text" style="color: #388E3C; font-weight: bold;">
                    Zeige alle Kreistagskandidaten
                </small>
            </div>
        </div>
    </div>
    
    <script>
    // Globale Variablen
    var leafletMap = null;
    var allLayers = {};
    var kreistagLayers = {};
    var kandidatenLayers = {};
    var legendExpanded = true;
    var currentViewMode = 'kreistag';
    
    // Warte bis die Karte geladen ist
    setTimeout(function() {
        var mapElements = document.getElementsByClassName('folium-map');
        if (mapElements.length > 0) {
            var mapId = mapElements[0].id;
            leafletMap = window[mapId];
            
            // Sammle alle Layer
            leafletMap.eachLayer(function(layer) {
                if (layer instanceof L.FeatureGroup && layer.options && layer.options.name) {
                    allLayers[layer.options.name] = layer;
                    
                    if (layer.options.name.includes('Kreistagkandidat:')) {
                        kreistagLayers[layer.options.name] = layer;
                    } else if (layer.options.name.includes('CDU:')) {
                        kandidatenLayers[layer.options.name] = layer;
                        // Verstecke Kandidaten-Layer initial
                        leafletMap.removeLayer(layer);
                    }
                }
            });
        }
    }, 1000);
    
    function toggleLegend() {
        legendExpanded = !legendExpanded;
        var content = document.getElementById('legend-content');
        var icon = document.getElementById('toggle-icon');
        var container = document.getElementById('legend-container');
        
        if (legendExpanded) {
            content.style.display = 'block';
            icon.innerHTML = '▼';
            container.style.width = '450px';
        } else {
            content.style.display = 'none';
            icon.innerHTML = '◀';
            container.style.width = 'auto';
        }
    }
    
    function updateViewMode() {
        var radios = document.getElementsByName('viewMode');
        for (var i = 0; i < radios.length; i++) {
            if (radios[i].checked) {
                currentViewMode = radios[i].value;
                break;
            }
        }
        
        if (currentViewMode === 'kreistag') {
            // Zeige Kreistag-Layer, verstecke Kandidaten-Layer
            for (var layer in kandidatenLayers) {
                leafletMap.removeLayer(kandidatenLayers[layer]);
            }
            showBothKreistagkandidaten();
        } else {
            // Zeige Kandidaten-Layer, verstecke Kreistag-Layer
            for (var layer in kreistagLayers) {
                leafletMap.removeLayer(kreistagLayers[layer]);
            }
            for (var layer in kandidatenLayers) {
                leafletMap.addLayer(kandidatenLayers[layer]);
            }
            updateStatus('Zeige alle einzelnen Kandidaten');
        }
    }
    
    function showKreistagkandidat(name) {
        hideAllLayers();
        var layerName = 'Kreistagkandidat: ' + name;
        if (kreistagLayers[layerName]) {
            leafletMap.addLayer(kreistagLayers[layerName]);
        }
        updateStatus('Zeige nur ' + name);
    }
    
    function showBothKreistagkandidaten() {
        hideAllLayers();
        for (var layer in kreistagLayers) {
            leafletMap.addLayer(kreistagLayers[layer]);
        }
        updateStatus('Zeige beide Kreistagskandidaten');
    }
    
    function showSingleKandidat(name) {
        // Wechsle zu Kandidaten-Ansicht
        document.querySelector('input[name="viewMode"][value="kandidaten"]').checked = true;
        updateViewMode();
        
        // Verstecke alle und zeige nur den gewählten
        for (var layer in kandidatenLayers) {
            leafletMap.removeLayer(kandidatenLayers[layer]);
        }
        
        var layerName = 'CDU: ' + name;
        if (kandidatenLayers[layerName]) {
            leafletMap.addLayer(kandidatenLayers[layerName]);
        }
        updateStatus('Zeige nur ' + name);
    }
    
    function hideAllLayers() {
        for (var layer in allLayers) {
            leafletMap.removeLayer(allLayers[layer]);
        }
        updateStatus('Alle Layer ausgeblendet');
    }
    
    function updateStatus(text) {
        document.getElementById('status-text').innerHTML = text;
    }
    
    // Speichere Zustand in localStorage
    function saveLegendState() {
        localStorage.setItem('legendExpanded', legendExpanded);
    }
    
    // Lade gespeicherten Zustand
    window.onload = function() {
        var saved = localStorage.getItem('legendExpanded');
        if (saved !== null) {
            legendExpanded = saved === 'true';
            if (!legendExpanded) {
                toggleLegend();
            }
        }
    }
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Karte speichern
    m.save('wahlbezirke_kreistag_map.html')
    print("✓ Kreistagskandidaten-Karte erstellt: wahlbezirke_kreistag_map.html")
    
    # Kreistagskandidaten-Übersicht
    kreistag_data = []
    for kreistagkandidat, info in kreistagskandidaten.items():
        total_wahlber = 0
        total_strassen = 0
        
        for kandidat in info['kandidaten']:
            kandidat_df = df[df['kandidat'] == kandidat]
            if len(kandidat_df) > 0:
                total_wahlber += kandidat_df.iloc[0]['wahlberechtigte']
                total_strassen += len(kandidat_df)
        
        kreistag_data.append({
            'kreistagkandidat': kreistagkandidat,
            'kreis_wbz': info['kreis_wbz'],
            'anzahl_bezirke': len(info['wahlbezirke']),
            'wahlbezirke': ', '.join(info['wahlbezirke']),
            'kandidaten': ', '.join(info['kandidaten']),
            'gesamt_wahlberechtigte': total_wahlber,
            'anzahl_strassen_auf_karte': total_strassen,
            'farbe': info['farbe']
        })
    
    kreistag_df = pd.DataFrame(kreistag_data)
    kreistag_df.to_csv('kreistagskandidaten_uebersicht.csv', index=False, encoding='utf-8')
    print("✓ Kreistagskandidaten-Übersicht: kreistagskandidaten_uebersicht.csv")

if __name__ == "__main__":
    main()