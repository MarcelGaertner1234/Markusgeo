#!/usr/bin/env python3
"""
Erweiterte Wahlbezirke-Karte mit individuellen Kandidaten-Checkboxen
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

# Kandidaten-Farben
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
    # Lade Daten
    df = pd.read_csv('wahlbezirke_map.csv')
    
    with open('wahlbezirke_zuordnung.json', 'r', encoding='utf-8') as f:
        wahlbezirke_data = json.load(f)
        wahlbezirke = wahlbezirke_data['wahlbezirke']
    
    # Kreistagskandidaten-Zuordnung
    kreistagskandidaten = {
        'Marcus Schmitz': {
            'kreis_wbz': 1,
            'wahlbezirke': ['WBZ 10', 'WBZ 20', 'WBZ 60', 'WBZ 70', 'WBZ 80', 'WBZ 90', 'WBZ 100', 'WBZ 110'],
            'kandidaten': [
                'Gisa Hauschildt', 'Jörg Reintsema', 'Ulrike Herrgesell', 'Thomas Hellbusch',
                'Philipp Beck', 'Manfred Henry Daub', 'Christopher Seinsche', 'Björn Dittich'
            ],
            'farbe': '#1976D2'
        },
        'Thomas Schlegel': {
            'kreis_wbz': 2,
            'wahlbezirke': ['WBZ 30', 'WBZ 40', 'WBZ 50', 'WBZ 120', 'WBZ 130', 'WBZ 140', 'WBZ 150', 'WBZ 160'],
            'kandidaten': [
                'Dagmar Schmitz', 'Jörg Menne', 'Markus Lang', 'Titzian Crisci',
                'Stephan Rühl', 'Roger Adolphs', 'Frank Schmitz', 'Thomas Schlegel'
            ],
            'farbe': '#D32F2F'
        }
    }
    
    # Erweitere DataFrame
    df['kandidat_farbe'] = df['kandidat'].map(KANDIDATEN_FARBEN)
    df['kreistagkandidat'] = ''
    df['kreistag_farbe'] = ''
    
    for kreistagkandidat, info in kreistagskandidaten.items():
        for kandidat in info['kandidaten']:
            df.loc[df['kandidat'] == kandidat, 'kreistagkandidat'] = kreistagkandidat
            df.loc[df['kandidat'] == kandidat, 'kreistag_farbe'] = info['farbe']
    
    # Karte erstellen
    avg_lat = df['latitude'].mean()
    avg_lon = df['longitude'].mean()
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)
    
    # Feature Groups für jeden einzelnen Kandidaten/Bezirk
    kandidaten_layers = {}
    
    # Erstelle Layer für jeden Kandidaten
    alle_kandidaten = []
    for kreistagkandidat, info in kreistagskandidaten.items():
        for i, kandidat in enumerate(info['kandidaten']):
            wbz = info['wahlbezirke'][i]
            alle_kandidaten.append({
                'name': kandidat,
                'wbz': wbz,
                'kreistagkandidat': kreistagkandidat,
                'farbe': KANDIDATEN_FARBEN[kandidat]
            })
            
            # Feature Group für diesen Kandidaten
            kandidaten_layers[kandidat] = folium.FeatureGroup(
                name=f"{kandidat} ({wbz})",
                show=True
            )
    
    # Erstelle Marker
    for _, row in df.iterrows():
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
            <small style="color: #999;">Koordinaten: {row['latitude']:.6f}, {row['longitude']:.6f}</small>
        </div>
        """
        
        # Marker zum entsprechenden Kandidaten-Layer hinzufügen
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
        ).add_to(kandidaten_layers[row['kandidat']])
    
    # Alle Layer zur Karte hinzufügen
    for layer in kandidaten_layers.values():
        layer.add_to(m)
    
    # Layer Control (versteckt, da wir eigene Controls haben)
    folium.LayerControl(collapsed=True, position='topleft').add_to(m)
    
    # Erweiterte Legende mit Checkboxen
    legend_html = '''
    <div id="legend-container" style="position: fixed; 
                bottom: 20px; right: 20px; width: 520px;
                background-color: white; z-index: 1000; 
                border: 3px solid #333; border-radius: 10px;
                box-shadow: 0 0 25px rgba(0,0,0,0.4);
                font-family: Arial, sans-serif;">
        
        <!-- Header -->
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
        <div id="legend-content" style="padding: 20px; max-height: 700px; overflow-y: auto;">
            
            <!-- Kreistagskandidaten Schnellauswahl -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border: 2px solid #e9ecef; margin-bottom: 15px;">
                <h4 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">
                    🏛️ Kreistagskandidaten - Schnellauswahl
                </h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                    <button id="btn-marcus-only" 
                            style="padding: 15px; background: #1976D2; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        NUR Marcus Schmitz<br>
                        <small style="font-weight: normal; font-size: 11px;">
                            8 Bezirke anzeigen
                        </small>
                    </button>
                    <button id="btn-thomas-only" 
                            style="padding: 15px; background: #D32F2F; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        NUR Thomas Schlegel<br>
                        <small style="font-weight: normal; font-size: 11px;">
                            8 Bezirke anzeigen
                        </small>
                    </button>
                </div>
            </div>
            
            <!-- Individuelle Kandidaten-Auswahl -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border: 2px solid #e9ecef; margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">
                    ✅ Individuelle Kandidaten-Auswahl
                </h4>
                
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    <button id="btn-select-all" 
                            style="flex: 1; padding: 10px; background: #4CAF50; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 13px;">
                        ✓ Alle auswählen
                    </button>
                    <button id="btn-select-none" 
                            style="flex: 1; padding: 10px; background: #f44336; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 13px;">
                        ✗ Keine auswählen
                    </button>
                </div>
                
                <!-- Marcus Schmitz Gruppe -->
                <div style="margin-bottom: 15px;">
                    <div style="background: #E3F2FD; padding: 8px; border-radius: 5px; margin-bottom: 8px;">
                        <label style="display: flex; align-items: center; cursor: pointer; font-weight: bold;">
                            <input type="checkbox" id="group-marcus" style="margin-right: 8px; width: 18px; height: 18px;">
                            <span style="color: #1976D2;">Marcus Schmitz - Alle 8 Bezirke</span>
                        </label>
                    </div>
                    <div style="padding-left: 20px;">
    '''
    
    # Marcus Schmitz Kandidaten-Checkboxen
    marcus_info = kreistagskandidaten['Marcus Schmitz']
    for i, kandidat in enumerate(marcus_info['kandidaten']):
        wbz = marcus_info['wahlbezirke'][i]
        farbe = KANDIDATEN_FARBEN[kandidat]
        
        # Prüfe ob Kandidat Straßen hat
        hat_strassen = len(df[df['kandidat'] == kandidat]) > 0
        status = "✓" if hat_strassen else "○"
        
        legend_html += f'''
        <label style="display: flex; align-items: center; margin: 5px 0; cursor: pointer; 
                      padding: 5px; border-radius: 4px; transition: background 0.2s;"
               class="kandidat-checkbox-label">
            <input type="checkbox" class="kandidat-checkbox" data-kandidat="{kandidat}" 
                   data-gruppe="marcus" checked
                   style="margin-right: 8px; width: 16px; height: 16px;">
            <span style="background-color: {farbe}; width: 18px; height: 18px; 
                       display: inline-block; border-radius: 50%; margin-right: 8px;
                       border: 2px solid white; box-shadow: 0 0 3px rgba(0,0,0,0.3);"></span>
            <span style="flex: 1;">
                <b>{kandidat}</b> <small>({wbz})</small>
                <span style="color: #666; font-size: 11px;"> {status}</span>
            </span>
        </label>
        '''
    
    legend_html += '''
                    </div>
                </div>
                
                <!-- Thomas Schlegel Gruppe -->
                <div>
                    <div style="background: #FFEBEE; padding: 8px; border-radius: 5px; margin-bottom: 8px;">
                        <label style="display: flex; align-items: center; cursor: pointer; font-weight: bold;">
                            <input type="checkbox" id="group-thomas" style="margin-right: 8px; width: 18px; height: 18px;">
                            <span style="color: #D32F2F;">Thomas Schlegel - Alle 8 Bezirke</span>
                        </label>
                    </div>
                    <div style="padding-left: 20px;">
    '''
    
    # Thomas Schlegel Kandidaten-Checkboxen
    thomas_info = kreistagskandidaten['Thomas Schlegel']
    for i, kandidat in enumerate(thomas_info['kandidaten']):
        wbz = thomas_info['wahlbezirke'][i]
        farbe = KANDIDATEN_FARBEN[kandidat]
        
        # Prüfe ob Kandidat Straßen hat
        hat_strassen = len(df[df['kandidat'] == kandidat]) > 0
        status = "✓" if hat_strassen else "○"
        
        legend_html += f'''
        <label style="display: flex; align-items: center; margin: 5px 0; cursor: pointer;
                      padding: 5px; border-radius: 4px; transition: background 0.2s;"
               class="kandidat-checkbox-label">
            <input type="checkbox" class="kandidat-checkbox" data-kandidat="{kandidat}" 
                   data-gruppe="thomas" checked
                   style="margin-right: 8px; width: 16px; height: 16px;">
            <span style="background-color: {farbe}; width: 18px; height: 18px; 
                       display: inline-block; border-radius: 50%; margin-right: 8px;
                       border: 2px solid white; box-shadow: 0 0 3px rgba(0,0,0,0.3);"></span>
            <span style="flex: 1;">
                <b>{kandidat}</b> <small>({wbz})</small>
                <span style="color: #666; font-size: 11px;"> {status}</span>
            </span>
        </label>
        '''
    
    legend_html += '''
                    </div>
                </div>
            </div>
            
            <!-- Status -->
            <div style="margin-top: 15px; padding: 12px; background: #e8f5e9; 
                        border-radius: 6px; text-align: center; border: 1px solid #c8e6c9;">
                <span id="status-text" style="color: #2e7d32; font-weight: bold; font-size: 14px;">
                    Alle 16 Bezirke aktiv
                </span>
            </div>
            
            <!-- Legende -->
            <div style="margin-top: 10px; padding: 10px; background: #f5f5f5; 
                        border-radius: 6px; font-size: 12px;">
                <b>Legende:</b> ✓ = Mit Straßen | ○ = Ohne geocodierte Straßen
            </div>
        </div>
    </div>
    
    <style>
    .kandidat-checkbox-label:hover {
        background-color: #f0f0f0 !important;
    }
    </style>
    
    <script>
    // Globale Variablen
    var mymap = null;
    var allLayers = {};
    var kandidatenLayers = {};
    
    // Warte bis Karte geladen ist
    window.addEventListener('load', function() {
        setTimeout(initializeMap, 500);
    });
    
    function initializeMap() {
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
                    
                    // Extrahiere Kandidaten-Namen aus Layer-Namen
                    var match = layer.options.name.match(/^(.+?)\\s*\\(WBZ/);
                    if (match) {
                        kandidatenLayers[match[1]] = layer;
                    }
                }
            });
            
            setupEventListeners();
            updateStatus();
        }
    }
    
    function setupEventListeners() {
        // Toggle Legende
        document.getElementById('legend-header').addEventListener('click', toggleLegend);
        
        // Kreistagskandidaten-Buttons
        document.getElementById('btn-marcus-only').addEventListener('click', function() {
            showOnlyKreistagkandidat('Marcus Schmitz');
        });
        
        document.getElementById('btn-thomas-only').addEventListener('click', function() {
            showOnlyKreistagkandidat('Thomas Schlegel');
        });
        
        // Alle/Keine Buttons
        document.getElementById('btn-select-all').addEventListener('click', selectAll);
        document.getElementById('btn-select-none').addEventListener('click', selectNone);
        
        // Gruppen-Checkboxen
        document.getElementById('group-marcus').addEventListener('change', function() {
            toggleGroup('marcus', this.checked);
        });
        
        document.getElementById('group-thomas').addEventListener('change', function() {
            toggleGroup('thomas', this.checked);
        });
        
        // Individuelle Checkboxen
        var checkboxes = document.querySelectorAll('.kandidat-checkbox');
        checkboxes.forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                toggleKandidat(this.getAttribute('data-kandidat'), this.checked);
                updateGroupCheckbox(this.getAttribute('data-gruppe'));
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
            container.style.width = '520px';
        } else {
            content.style.display = 'none';
            icon.innerHTML = '◀';
            container.style.width = 'auto';
        }
    }
    
    function showOnlyKreistagkandidat(kreistagkandidat) {
        // Erst alle deaktivieren
        selectNone();
        
        // Dann nur die gewünschte Gruppe aktivieren
        var gruppe = kreistagkandidat === 'Marcus Schmitz' ? 'marcus' : 'thomas';
        var checkboxes = document.querySelectorAll('.kandidat-checkbox[data-gruppe="' + gruppe + '"]');
        checkboxes.forEach(function(checkbox) {
            checkbox.checked = true;
            toggleKandidat(checkbox.getAttribute('data-kandidat'), true);
        });
        
        // Gruppen-Checkbox aktualisieren
        document.getElementById('group-' + gruppe).checked = true;
        updateStatus();
    }
    
    function selectAll() {
        var checkboxes = document.querySelectorAll('.kandidat-checkbox');
        checkboxes.forEach(function(checkbox) {
            checkbox.checked = true;
            toggleKandidat(checkbox.getAttribute('data-kandidat'), true);
        });
        document.getElementById('group-marcus').checked = true;
        document.getElementById('group-thomas').checked = true;
        updateStatus();
    }
    
    function selectNone() {
        var checkboxes = document.querySelectorAll('.kandidat-checkbox');
        checkboxes.forEach(function(checkbox) {
            checkbox.checked = false;
            toggleKandidat(checkbox.getAttribute('data-kandidat'), false);
        });
        document.getElementById('group-marcus').checked = false;
        document.getElementById('group-thomas').checked = false;
        updateStatus();
    }
    
    function toggleGroup(gruppe, checked) {
        var checkboxes = document.querySelectorAll('.kandidat-checkbox[data-gruppe="' + gruppe + '"]');
        checkboxes.forEach(function(checkbox) {
            checkbox.checked = checked;
            toggleKandidat(checkbox.getAttribute('data-kandidat'), checked);
        });
        updateStatus();
    }
    
    function toggleKandidat(kandidat, show) {
        if (!mymap || !kandidatenLayers[kandidat]) return;
        
        if (show) {
            mymap.addLayer(kandidatenLayers[kandidat]);
        } else {
            mymap.removeLayer(kandidatenLayers[kandidat]);
        }
    }
    
    function updateGroupCheckbox(gruppe) {
        var groupCheckboxes = document.querySelectorAll('.kandidat-checkbox[data-gruppe="' + gruppe + '"]');
        var allChecked = true;
        
        groupCheckboxes.forEach(function(checkbox) {
            if (!checkbox.checked) {
                allChecked = false;
            }
        });
        
        document.getElementById('group-' + gruppe).checked = allChecked;
        updateStatus();
    }
    
    function updateStatus() {
        var checkedCount = document.querySelectorAll('.kandidat-checkbox:checked').length;
        var statusText = '';
        
        if (checkedCount === 0) {
            statusText = 'Keine Bezirke ausgewählt';
        } else if (checkedCount === 16) {
            statusText = 'Alle 16 Bezirke aktiv';
        } else {
            statusText = checkedCount + ' von 16 Bezirken aktiv';
        }
        
        document.getElementById('status-text').innerHTML = statusText;
    }
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Karte speichern
    m.save('wahlbezirke_individual_map.html')
    print("✓ Individuelle Kandidaten-Karte erstellt: wahlbezirke_individual_map.html")

if __name__ == "__main__":
    main()