#!/usr/bin/env python3
"""
Korrigierte Version der Kreistagskandidaten-Karte
"""

import pandas as pd
import folium
from collections import defaultdict
import json

# Farbschema für Kreistagskandidaten
KREISTAGS_FARBEN = {
    'Marcus Schmitz': '#1976D2',  # Blau für Kreis-WBZ 1
    'Thomas Schlegel': '#D32F2F'   # Rot für Kreis-WBZ 2
}

# Kandidaten-Farben (angepasst an Kreistagskandidaten)
KANDIDATEN_FARBEN = {
    # Marcus Schmitz Gruppe (Blautöne) - Kreis-WBZ 1
    'Gisa Hauschildt': '#0D47A1',      # WBZ 10
    'Jörg Reintsema': '#1565C0',       # WBZ 20
    'Ulrike Herrgesell': '#1976D2',    # WBZ 60
    'Thomas Hellbusch': '#1E88E5',     # WBZ 70
    'Philipp Beck': '#2196F3',         # WBZ 80
    'Manfred Henry Daub': '#42A5F5',   # WBZ 90
    'Christopher Seinsche': '#64B5F6',  # WBZ 100
    'Björn Dittich': '#90CAF9',        # WBZ 110
    
    # Thomas Schlegel Gruppe (Rottöne) - Kreis-WBZ 2
    'Dagmar Schmitz': '#B71C1C',       # WBZ 30
    'Jörg Menne': '#C62828',           # WBZ 40
    'Markus Lang': '#D32F2F',          # WBZ 50
    'Titzian Crisci': '#E53935',       # WBZ 120
    'Stephan Rühl': '#F44336',         # WBZ 130
    'Roger Adolphs': '#EF5350',        # WBZ 140
    'Frank Schmitz': '#E57373',        # WBZ 150
    'Thomas Schlegel': '#EF9A9A'       # WBZ 160
}

def main():
    # Lade die Daten
    df = pd.read_csv('wahlbezirke_map.csv')
    
    with open('wahlbezirke_zuordnung.json', 'r', encoding='utf-8') as f:
        wahlbezirke_data = json.load(f)
        wahlbezirke = wahlbezirke_data['wahlbezirke']
    
    # Korrekte Kreistagskandidaten-Zuordnung basierend auf PDF
    kreistagskandidaten = {
        'Marcus Schmitz': {
            'kreis_wbz': 1,
            'wahlbezirke': ['WBZ 10', 'WBZ 20', 'WBZ 60', 'WBZ 70', 'WBZ 80', 'WBZ 90', 'WBZ 100', 'WBZ 110'],
            'kandidaten': [
                'Gisa Hauschildt',      # WBZ 10
                'Jörg Reintsema',       # WBZ 20
                'Ulrike Herrgesell',    # WBZ 60
                'Thomas Hellbusch',     # WBZ 70
                'Philipp Beck',         # WBZ 80
                'Manfred Henry Daub',   # WBZ 90
                'Christopher Seinsche', # WBZ 100
                'Björn Dittich'        # WBZ 110
            ],
            'farbe': '#1976D2'
        },
        'Thomas Schlegel': {
            'kreis_wbz': 2,
            'wahlbezirke': ['WBZ 30', 'WBZ 40', 'WBZ 50', 'WBZ 120', 'WBZ 130', 'WBZ 140', 'WBZ 150', 'WBZ 160'],
            'kandidaten': [
                'Dagmar Schmitz',    # WBZ 30
                'Jörg Menne',        # WBZ 40
                'Markus Lang',       # WBZ 50
                'Titzian Crisci',    # WBZ 120
                'Stephan Rühl',      # WBZ 130
                'Roger Adolphs',     # WBZ 140
                'Frank Schmitz',     # WBZ 150
                'Thomas Schlegel'    # WBZ 160
            ],
            'farbe': '#D32F2F'
        }
    }
    
    # Aktualisiere Farben basierend auf Kandidat
    df['kandidat_farbe'] = df['kandidat'].map(KANDIDATEN_FARBEN)
    
    # Füge Kreistagskandidaten-Info hinzu
    df['kreistagkandidat'] = ''
    for kreistagkandidat, info in kreistagskandidaten.items():
        for kandidat in info['kandidaten']:
            df.loc[df['kandidat'] == kandidat, 'kreistagkandidat'] = kreistagkandidat
            df.loc[df['kandidat'] == kandidat, 'kreistag_farbe'] = info['farbe']
    
    # Zentrum berechnen
    avg_lat = df['latitude'].mean()
    avg_lon = df['longitude'].mean()
    
    # Karte erstellen
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
    
    # Feature Groups erstellen
    kreistags_groups = {
        'Marcus Schmitz': folium.FeatureGroup(name='Kreistagkandidat: Marcus Schmitz'),
        'Thomas Schlegel': folium.FeatureGroup(name='Kreistagkandidat: Thomas Schlegel')
    }
    
    kandidaten_groups = {}
    
    # Marker für alle Straßen erstellen
    for _, row in df.iterrows():
        # Feature Group für einzelne Kandidaten erstellen wenn noch nicht vorhanden
        if row['kandidat'] not in kandidaten_groups:
            kandidaten_groups[row['kandidat']] = folium.FeatureGroup(
                name=f"CDU: {row['kandidat']}"
            )
        
        popup_text = f"""
        <div style="font-family: Arial, sans-serif;">
            <b style="font-size: 14px;">{row['street']}</b><br>
            <span style="color: #666;">{row['original']}</span><br>
            <span style="color: #666;">{row['postal_code']} {row['city']}</span><br>
            <hr style="margin: 5px 0;">
            <b>Wahlbezirk:</b> {row['bezirk']}<br>
            <b>CDU-Kandidat/in:</b> {row['kandidat']}<br>
            <b>Kreistagkandidat:</b> <span style="color: {row['kreistag_farbe']}; font-weight: bold;">{row['kreistagkandidat']}</span><br>
            <b>Wahlberechtigte:</b> {row['wahlberechtigte']}<br>
            <small style="color: #999;">Lat: {row['latitude']:.6f}, Lon: {row['longitude']:.6f}</small>
        </div>
        """
        
        # Marker für Kreistagskandidaten-Ansicht
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['street']} ({row['wbz']})",
            color=row['kreistag_farbe'],
            fill=True,
            fillColor=row['kandidat_farbe'],
            fillOpacity=0.8,
            weight=3
        ).add_to(kreistags_groups[row['kreistagkandidat']])
        
        # Marker für Kandidaten-Ansicht
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['street']} ({row['wbz']})",
            color=row['kandidat_farbe'],
            fill=True,
            fillColor=row['kandidat_farbe'],
            fillOpacity=0.8,
            weight=2
        ).add_to(kandidaten_groups[row['kandidat']])
    
    # Alle Feature Groups zur Karte hinzufügen
    for group in kreistags_groups.values():
        group.add_to(m)
    for group in kandidaten_groups.values():
        group.add_to(m)
    
    # Layer Control
    folium.LayerControl(collapsed=True, position='topleft').add_to(m)
    
    # Erweiterte Legende mit funktionierenden Buttons
    legend_html = '''
    <div id="legend-container" style="position: fixed; 
                bottom: 20px; right: 20px; width: 480px;
                background-color: white; z-index: 1000; 
                border: 3px solid #333; border-radius: 10px;
                box-shadow: 0 0 25px rgba(0,0,0,0.4);
                font-family: Arial, sans-serif;">
        
        <!-- Header mit Toggle -->
        <div id="legend-header" style="background: linear-gradient(135deg, #1976D2 0%, #D32F2F 100%); 
                    color: white; padding: 15px; border-radius: 7px 7px 0 0;
                    cursor: pointer; user-select: none;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 20px; font-weight: bold;">
                    CDU Wahlbezirke Nümbrecht 2024
                </h3>
                <span id="toggle-icon" style="font-size: 24px; font-weight: bold;">▼</span>
            </div>
        </div>
        
        <!-- Inhalt -->
        <div id="legend-content" style="padding: 20px; max-height: 650px; overflow-y: auto;">
            
            <!-- Kreistagskandidaten Hauptkontrolle -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border: 2px solid #e9ecef; margin-bottom: 15px;">
                <h4 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">
                    🏛️ Kreistagskandidaten - Direkte Auswahl
                </h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                    <button id="btn-marcus" 
                            style="padding: 15px; background: #1976D2; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 16px;
                                   transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        Marcus Schmitz<br>
                        <small style="font-weight: normal; font-size: 12px;">
                            Kreis-WBZ 1 • 8 Bezirke<br>
                            WBZ: 10, 20, 60, 70, 80, 90, 100, 110
                        </small>
                    </button>
                    <button id="btn-thomas" 
                            style="padding: 15px; background: #D32F2F; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 16px;
                                   transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        Thomas Schlegel<br>
                        <small style="font-weight: normal; font-size: 12px;">
                            Kreis-WBZ 2 • 8 Bezirke<br>
                            WBZ: 30, 40, 50, 120, 130, 140, 150, 160
                        </small>
                    </button>
                </div>
                
                <div style="display: flex; gap: 8px;">
                    <button id="btn-both" 
                            style="flex: 1; padding: 12px; background: #4CAF50; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        ✓ Beide Kreistagskandidaten
                    </button>
                    <button id="btn-none" 
                            style="flex: 1; padding: 12px; background: #f44336; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        ✗ Alle ausblenden
                    </button>
                </div>
            </div>
            
            <!-- Anzeigemodus -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border: 2px solid #e9ecef; margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #333; font-size: 16px;">
                    🔍 Anzeigemodus
                </h4>
                <label style="display: flex; align-items: center; margin-bottom: 8px; cursor: pointer;">
                    <input type="radio" name="viewMode" id="mode-kreistag" value="kreistag" checked 
                           style="margin-right: 8px; width: 16px; height: 16px;">
                    <span style="font-size: 14px;">Nach Kreistagskandidaten gruppiert</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="radio" name="viewMode" id="mode-kandidaten" value="kandidaten" 
                           style="margin-right: 8px; width: 16px; height: 16px;">
                    <span style="font-size: 14px;">Einzelne Kandidaten anzeigen</span>
                </label>
            </div>
            
            <!-- Kandidaten-Details -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border: 2px solid #e9ecef;">
                <h4 style="margin: 0 0 15px 0; color: #333; font-size: 16px;">
                    👥 Alle Kandidaten im Detail
                </h4>
                
                <!-- Marcus Schmitz Gruppe -->
                <div style="margin-bottom: 15px;">
                    <h5 style="color: #1976D2; margin: 10px 0; font-size: 15px; font-weight: bold;">
                        Marcus Schmitz - Kreis-WBZ 1
                    </h5>
                    <div style="background: white; border: 1px solid #1976D2; 
                                border-radius: 5px; padding: 8px;">
    '''
    
    # Marcus Schmitz Kandidaten mit Details
    marcus_info = kreistagskandidaten['Marcus Schmitz']
    for i, kandidat in enumerate(marcus_info['kandidaten']):
        wbz = marcus_info['wahlbezirke'][i]
        kandidat_rows = df[df['kandidat'] == kandidat]
        
        if len(kandidat_rows) > 0:
            kandidat_data = kandidat_rows.iloc[0]
            farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            wahlber = kandidat_data['wahlberechtigte']
            anzahl_str = len(kandidat_rows)
            status = f"{anzahl_str} Straßen" if anzahl_str > 0 else "Keine Straßen geocodiert"
        else:
            # Daten aus wahlbezirke für fehlende Kandidaten
            wbz_data = wahlbezirke.get(wbz, {})
            farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            wahlber = wbz_data.get('wahlberechtigte', 0)
            anzahl_str = 0
            status = "Keine Straßen geocodiert"
        
        legend_html += f'''
        <div class="kandidat-item" data-kandidat="{kandidat}"
             style="margin: 3px; padding: 8px; background: #f9f9f9; 
                    border-radius: 4px; cursor: pointer; transition: all 0.2s;
                    border: 1px solid #e0e0e0;">
            <div style="display: flex; align-items: center;">
                <span style="background-color: {farbe}; width: 20px; height: 20px; 
                           display: inline-block; border-radius: 50%; margin-right: 10px;
                           border: 2px solid white; box-shadow: 0 0 3px rgba(0,0,0,0.3);"></span>
                <div style="flex: 1;">
                    <b style="font-size: 13px;">{kandidat}</b><br>
                    <small style="color: #666;">
                        {wbz} • {wahlber} Wahlberechtigte • {status}
                    </small>
                </div>
            </div>
        </div>
        '''
    
    legend_html += '''
                    </div>
                </div>
                
                <!-- Thomas Schlegel Gruppe -->
                <div>
                    <h5 style="color: #D32F2F; margin: 10px 0; font-size: 15px; font-weight: bold;">
                        Thomas Schlegel - Kreis-WBZ 2
                    </h5>
                    <div style="background: white; border: 1px solid #D32F2F; 
                                border-radius: 5px; padding: 8px;">
    '''
    
    # Thomas Schlegel Kandidaten mit Details
    thomas_info = kreistagskandidaten['Thomas Schlegel']
    for i, kandidat in enumerate(thomas_info['kandidaten']):
        wbz = thomas_info['wahlbezirke'][i]
        kandidat_rows = df[df['kandidat'] == kandidat]
        
        if len(kandidat_rows) > 0:
            kandidat_data = kandidat_rows.iloc[0]
            farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            wahlber = kandidat_data['wahlberechtigte']
            anzahl_str = len(kandidat_rows)
            status = f"{anzahl_str} Straßen" if anzahl_str > 0 else "Keine Straßen geocodiert"
        else:
            # Daten aus wahlbezirke für fehlende Kandidaten
            wbz_data = wahlbezirke.get(wbz, {})
            farbe = KANDIDATEN_FARBEN.get(kandidat, '#808080')
            wahlber = wbz_data.get('wahlberechtigte', 0)
            anzahl_str = 0
            status = "Keine Straßen geocodiert"
            
        legend_html += f'''
        <div class="kandidat-item" data-kandidat="{kandidat}"
             style="margin: 3px; padding: 8px; background: #f9f9f9; 
                    border-radius: 4px; cursor: pointer; transition: all 0.2s;
                    border: 1px solid #e0e0e0;">
            <div style="display: flex; align-items: center;">
                <span style="background-color: {farbe}; width: 20px; height: 20px; 
                           display: inline-block; border-radius: 50%; margin-right: 10px;
                           border: 2px solid white; box-shadow: 0 0 3px rgba(0,0,0,0.3);"></span>
                <div style="flex: 1;">
                    <b style="font-size: 13px;">{kandidat}</b><br>
                    <small style="color: #666;">
                        {wbz} • {wahlber} Wahlberechtigte • {status}
                    </small>
                </div>
            </div>
        </div>
        '''
    
    legend_html += '''
                    </div>
                </div>
            </div>
            
            <!-- Status -->
            <div style="margin-top: 15px; padding: 12px; background: #e8f5e9; 
                        border-radius: 6px; text-align: center; border: 1px solid #c8e6c9;">
                <span id="status-text" style="color: #2e7d32; font-weight: bold; font-size: 14px;">
                    Zeige beide Kreistagskandidaten
                </span>
            </div>
        </div>
    </div>
    
    <script>
    // Karten-Referenz und Layer-Verwaltung
    var mymap = null;
    var allLayers = {};
    var currentMode = 'kreistag';
    
    // Warte bis die Karte vollständig geladen ist
    window.addEventListener('load', function() {
        setTimeout(initializeMap, 500);
    });
    
    function initializeMap() {
        // Finde die Leaflet-Karte
        var mapDivs = document.querySelectorAll('.folium-map');
        if (mapDivs.length > 0) {
            var mapId = mapDivs[0].id;
            mymap = window[mapId];
            
            if (!mymap) {
                console.error('Karte nicht gefunden');
                return;
            }
            
            // Sammle alle Layer
            mymap.eachLayer(function(layer) {
                if (layer instanceof L.FeatureGroup && layer.options && layer.options.name) {
                    allLayers[layer.options.name] = layer;
                    
                    // Verstecke initial alle Kandidaten-Layer
                    if (layer.options.name.startsWith('CDU:')) {
                        mymap.removeLayer(layer);
                    }
                }
            });
            
            // Event-Listener hinzufügen
            setupEventListeners();
        }
    }
    
    function setupEventListeners() {
        // Toggle für Legende
        document.getElementById('legend-header').addEventListener('click', toggleLegend);
        
        // Kreistagskandidaten-Buttons
        document.getElementById('btn-marcus').addEventListener('click', function() {
            showKreistagkandidat('Marcus Schmitz');
        });
        
        document.getElementById('btn-thomas').addEventListener('click', function() {
            showKreistagkandidat('Thomas Schlegel');
        });
        
        document.getElementById('btn-both').addEventListener('click', showBothKreistagkandidaten);
        document.getElementById('btn-none').addEventListener('click', hideAllLayers);
        
        // Radio-Buttons für Anzeigemodus
        document.getElementById('mode-kreistag').addEventListener('change', function() {
            if (this.checked) switchToKreistagMode();
        });
        
        document.getElementById('mode-kandidaten').addEventListener('change', function() {
            if (this.checked) switchToKandidatenMode();
        });
        
        // Kandidaten-Items
        var kandidatenItems = document.querySelectorAll('.kandidat-item');
        kandidatenItems.forEach(function(item) {
            item.addEventListener('click', function() {
                var kandidatName = this.getAttribute('data-kandidat');
                showSingleKandidat(kandidatName);
            });
            
            item.addEventListener('mouseover', function() {
                this.style.background = '#e3f2fd';
                this.style.borderColor = '#1976D2';
            });
            
            item.addEventListener('mouseout', function() {
                this.style.background = '#f9f9f9';
                this.style.borderColor = '#e0e0e0';
            });
        });
    }
    
    function toggleLegend() {
        var content = document.getElementById('legend-content');
        var icon = document.getElementById('toggle-icon');
        var container = document.getElementById('legend-container');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            icon.innerHTML = '▼';
            container.style.width = '480px';
        } else {
            content.style.display = 'none';
            icon.innerHTML = '◀';
            container.style.width = 'auto';
        }
    }
    
    function showKreistagkandidat(name) {
        if (!mymap) return;
        
        hideAllLayers();
        var layerName = 'Kreistagkandidat: ' + name;
        if (allLayers[layerName]) {
            mymap.addLayer(allLayers[layerName]);
            updateStatus('Zeige ' + name + ' (Kreis-WBZ ' + (name === 'Marcus Schmitz' ? '1' : '2') + ')');
        }
    }
    
    function showBothKreistagkandidaten() {
        if (!mymap) return;
        
        hideAllLayers();
        
        if (allLayers['Kreistagkandidat: Marcus Schmitz']) {
            mymap.addLayer(allLayers['Kreistagkandidat: Marcus Schmitz']);
        }
        if (allLayers['Kreistagkandidat: Thomas Schlegel']) {
            mymap.addLayer(allLayers['Kreistagkandidat: Thomas Schlegel']);
        }
        
        updateStatus('Zeige beide Kreistagskandidaten');
    }
    
    function showSingleKandidat(name) {
        if (!mymap) return;
        
        // Wechsle automatisch zu Kandidaten-Modus
        document.getElementById('mode-kandidaten').checked = true;
        switchToKandidatenMode();
        
        hideAllLayers();
        var layerName = 'CDU: ' + name;
        if (allLayers[layerName]) {
            mymap.addLayer(allLayers[layerName]);
            updateStatus('Zeige nur ' + name);
        } else {
            updateStatus(name + ' hat keine geocodierten Straßen');
        }
    }
    
    function switchToKreistagMode() {
        currentMode = 'kreistag';
        hideAllLayers();
        showBothKreistagkandidaten();
    }
    
    function switchToKandidatenMode() {
        currentMode = 'kandidaten';
        hideAllLayers();
        
        // Zeige alle Kandidaten-Layer
        for (var layerName in allLayers) {
            if (layerName.startsWith('CDU:')) {
                mymap.addLayer(allLayers[layerName]);
            }
        }
        updateStatus('Zeige alle einzelnen Kandidaten');
    }
    
    function hideAllLayers() {
        if (!mymap) return;
        
        for (var layerName in allLayers) {
            mymap.removeLayer(allLayers[layerName]);
        }
        updateStatus('Alle Layer ausgeblendet');
    }
    
    function updateStatus(text) {
        document.getElementById('status-text').innerHTML = text;
    }
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Karte speichern
    m.save('wahlbezirke_kreistag_map_fixed.html')
    print("✓ Korrigierte Kreistagskandidaten-Karte erstellt: wahlbezirke_kreistag_map_fixed.html")
    
    # Aktualisierte Übersicht speichern
    overview_data = []
    
    # Statistiken für beide Kreistagskandidaten
    for kreistagkandidat, info in kreistagskandidaten.items():
        total_wahlber = 0
        total_strassen = 0
        kandidaten_mit_strassen = []
        kandidaten_ohne_strassen = []
        
        for kandidat in info['kandidaten']:
            kandidat_df = df[df['kandidat'] == kandidat]
            if len(kandidat_df) > 0:
                kandidaten_mit_strassen.append(kandidat)
                total_strassen += len(kandidat_df)
                # Hole Wahlberechtigte aus erster Zeile des Kandidaten
                total_wahlber += kandidat_df.iloc[0]['wahlberechtigte']
            else:
                kandidaten_ohne_strassen.append(kandidat)
                # Hole Wahlberechtigte aus wahlbezirke.json für fehlende
                for i, k in enumerate(info['kandidaten']):
                    if k == kandidat:
                        wbz = info['wahlbezirke'][i]
                        wbz_data = wahlbezirke.get(wbz, {})
                        total_wahlber += wbz_data.get('wahlberechtigte', 0)
        
        overview_data.append({
            'Kreistagkandidat': kreistagkandidat,
            'Kreis-WBZ': info['kreis_wbz'],
            'Anzahl Bezirke': len(info['wahlbezirke']),
            'Wahlbezirke': ', '.join(info['wahlbezirke']),
            'Gesamt Wahlberechtigte': total_wahlber,
            'Straßen auf Karte': total_strassen,
            'Kandidaten mit Straßen': ', '.join(kandidaten_mit_strassen),
            'Kandidaten ohne Straßen': ', '.join(kandidaten_ohne_strassen) if kandidaten_ohne_strassen else 'Keine'
        })
    
    overview_df = pd.DataFrame(overview_data)
    overview_df.to_csv('kreistagskandidaten_statistik.csv', index=False, encoding='utf-8')
    print("✓ Statistik gespeichert: kreistagskandidaten_statistik.csv")

if __name__ == "__main__":
    main()