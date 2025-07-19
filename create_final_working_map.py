#!/usr/bin/env python3
"""
Finale funktionierende Karte mit korrekter Marker-Verwaltung über Leaflet
"""

import pandas as pd
import folium
from folium import plugins
import json

# Farbschema
KREISTAGS_FARBEN = {
    'Marcus Schmitz': '#1976D2',
    'Thomas Schlegel': '#D32F2F'
}

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
    # Lade vollständige Daten
    df = pd.read_csv('wahlbezirke_complete.csv')
    print(f"✓ Verwende vollständige Datei mit {len(df)} Einträgen")
    
    # Kreistagskandidaten-Zuordnung
    kreistagskandidaten = {
        'Marcus Schmitz': ['Gisa Hauschildt', 'Jörg Reintsema', 'Ulrike Herrgesell', 'Thomas Hellbusch',
                          'Philipp Beck', 'Manfred Henry Daub', 'Christopher Seinsche', 'Björn Dittich'],
        'Thomas Schlegel': ['Dagmar Schmitz', 'Jörg Menne', 'Markus Lang', 'Titzian Crisci',
                           'Stephan Rühl', 'Roger Adolphs', 'Frank Schmitz', 'Thomas Schlegel']
    }
    
    # Füge Farben hinzu
    df['kandidat_farbe'] = df['kandidat'].map(KANDIDATEN_FARBEN)
    
    # Kreistagkandidat Info
    for kreistagkandidat, kandidaten in kreistagskandidaten.items():
        mask = df['kandidat'].isin(kandidaten)
        df.loc[mask, 'kreistagkandidat'] = kreistagkandidat
        df.loc[mask, 'kreistag_farbe'] = KREISTAGS_FARBEN[kreistagkandidat]
    
    # Karte erstellen
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Erstelle separate FeatureGroups für jeden Kandidaten
    kandidaten_layers = {}
    
    for kandidat in df['kandidat'].unique():
        kandidaten_layers[kandidat] = folium.FeatureGroup(name=kandidat, show=True)
    
    # Marker-Counter für JavaScript
    marker_data = []
    marker_id = 0
    
    # Erstelle Marker
    for idx, row in df.iterrows():
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <b style="font-size: 14px;">{row['street']}</b><br>
            <span style="color: #666;">{row.get('original', row['street'])}</span><br>
            <span style="color: #666;">{row['postal_code']} {row['city']}</span><br>
            <hr style="margin: 5px 0;">
            <b>Wahlbezirk:</b> {row.get('bezirk', row['wbz'])}<br>
            <b>CDU-Kandidat/in:</b> {row['kandidat']}<br>
            <b>Kreistagkandidat:</b> <span style="color: {row['kreistag_farbe']}; font-weight: bold;">{row['kreistagkandidat']}</span><br>
            <b>Wahlberechtigte:</b> {row['wahlberechtigte']}<br>
            <small style="color: #999;">Koordinaten: {row['latitude']:.6f}, {row['longitude']:.6f}</small>
        </div>
        """
        
        # Erstelle Marker
        marker = folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['street']} ({row['wbz']})",
            color=row['kreistag_farbe'],
            fill=True,
            fillColor=row['kandidat_farbe'],
            fillOpacity=0.8,
            weight=3
        )
        
        # Füge zu entsprechender FeatureGroup hinzu
        marker.add_to(kandidaten_layers[row['kandidat']])
        
        # Sammle Marker-Daten für JavaScript
        marker_data.append({
            'id': marker_id,
            'kandidat': row['kandidat'],
            'kreistagkandidat': row['kreistagkandidat'],
            'lat': row['latitude'],
            'lng': row['longitude']
        })
        marker_id += 1
    
    # Füge alle FeatureGroups zur Karte hinzu
    for layer in kandidaten_layers.values():
        layer.add_to(m)
    
    # Custom Control Panel
    control_html = '''
    <div id="control-panel" style="position: fixed; 
                bottom: 20px; right: 20px; width: 520px;
                background-color: white; z-index: 1000; 
                border: 3px solid #333; border-radius: 10px;
                box-shadow: 0 0 25px rgba(0,0,0,0.4);
                font-family: Arial, sans-serif;">
        
        <!-- Header -->
        <div id="panel-header" style="background: linear-gradient(135deg, #1976D2 0%, #D32F2F 100%); 
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
        <div id="panel-content" style="padding: 20px; max-height: 700px; overflow-y: auto;">
            
            <!-- Kreistagskandidaten Buttons -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border: 2px solid #e9ecef; margin-bottom: 15px;">
                <h4 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">
                    🏛️ Kreistagskandidaten - Schnellauswahl
                </h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                    <button onclick="showOnlyMarcus()" 
                            style="padding: 15px; background: #1976D2; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        NUR Marcus Schmitz<br>
                        <small style="font-weight: normal; font-size: 11px;">
                            8 Bezirke anzeigen
                        </small>
                    </button>
                    <button onclick="showOnlyThomas()" 
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
            
            <!-- Kontrollen -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; 
                        border: 2px solid #e9ecef; margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #333; font-size: 18px;">
                    ✅ Individuelle Kandidaten-Auswahl
                </h4>
                
                <div style="display: flex; gap: 8px; margin-bottom: 12px;">
                    <button onclick="showAll()"
                            style="flex: 1; padding: 10px; background: #4CAF50; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 13px;">
                        ✓ Alle anzeigen
                    </button>
                    <button onclick="hideAll()"
                            style="flex: 1; padding: 10px; background: #f44336; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 13px;">
                        ✗ Alle ausblenden
                    </button>
                </div>
                
                <!-- Marcus Schmitz Gruppe -->
                <div style="margin-bottom: 15px;">
                    <div style="background: #E3F2FD; padding: 8px; border-radius: 5px; margin-bottom: 8px;">
                        <label style="display: flex; align-items: center; cursor: pointer; font-weight: bold;">
                            <input type="checkbox" id="group-marcus" checked onchange="toggleGroup('marcus', this.checked)"
                                   style="margin-right: 8px; width: 18px; height: 18px;">
                            <span style="color: #1976D2;">Marcus Schmitz - Alle 8 Bezirke</span>
                        </label>
                    </div>
                    <div style="padding-left: 20px;">
    '''
    
    # Marcus Schmitz Kandidaten
    marcus_kandidaten = kreistagskandidaten['Marcus Schmitz']
    for kandidat in marcus_kandidaten:
        farbe = KANDIDATEN_FARBEN[kandidat]
        anzahl = len(df[df['kandidat'] == kandidat])
        kandidat_id = kandidat.replace(' ', '_').replace('.', '')
        
        control_html += f'''
        <label style="display: flex; align-items: center; margin: 5px 0; cursor: pointer;">
            <input type="checkbox" class="kandidat-check marcus-gruppe" 
                   data-kandidat="{kandidat}" 
                   id="check-{kandidat_id}" checked
                   onchange="toggleKandidat('{kandidat}', this.checked)"
                   style="margin-right: 8px;">
            <span style="background-color: {farbe}; width: 18px; height: 18px; 
                       display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
            <span>{kandidat} ({anzahl} Punkte)</span>
        </label>
        '''
    
    control_html += '''
                    </div>
                </div>
                
                <!-- Thomas Schlegel Gruppe -->
                <div>
                    <div style="background: #FFEBEE; padding: 8px; border-radius: 5px; margin-bottom: 8px;">
                        <label style="display: flex; align-items: center; cursor: pointer; font-weight: bold;">
                            <input type="checkbox" id="group-thomas" checked onchange="toggleGroup('thomas', this.checked)"
                                   style="margin-right: 8px; width: 18px; height: 18px;">
                            <span style="color: #D32F2F;">Thomas Schlegel - Alle 8 Bezirke</span>
                        </label>
                    </div>
                    <div style="padding-left: 20px;">
    '''
    
    # Thomas Schlegel Kandidaten
    thomas_kandidaten = kreistagskandidaten['Thomas Schlegel']
    for kandidat in thomas_kandidaten:
        farbe = KANDIDATEN_FARBEN[kandidat]
        anzahl = len(df[df['kandidat'] == kandidat])
        kandidat_id = kandidat.replace(' ', '_').replace('.', '')
        
        control_html += f'''
        <label style="display: flex; align-items: center; margin: 5px 0; cursor: pointer;">
            <input type="checkbox" class="kandidat-check thomas-gruppe" 
                   data-kandidat="{kandidat}"
                   id="check-{kandidat_id}" checked
                   onchange="toggleKandidat('{kandidat}', this.checked)"
                   style="margin-right: 8px;">
            <span style="background-color: {farbe}; width: 18px; height: 18px; 
                       display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
            <span>{kandidat} ({anzahl} Punkte)</span>
        </label>
        '''
    
    control_html += '''
                    </div>
                </div>
            </div>
            
            <!-- Status -->
            <div style="margin-top: 15px; padding: 12px; background: #e8f5e9; 
                        border-radius: 6px; text-align: center;">
                <span id="status-text" style="color: #2e7d32; font-weight: bold;">
                    Alle Punkte sichtbar
                </span>
            </div>
        </div>
    </div>
    
    <script>
    // Globale Referenzen
    var mymap = null;
    var featureGroups = {};
    var kandidatenZuordnung = ''' + json.dumps(kreistagskandidaten) + ''';
    
    // Warte bis Karte geladen ist
    window.addEventListener('DOMContentLoaded', function() {
        setTimeout(function() {
            initializeControls();
        }, 1000);
    });
    
    function initializeControls() {
        console.log('Initialisiere Kontrollen...');
        
        // Finde die Leaflet-Karte
        var mapElements = document.getElementsByClassName('folium-map');
        if (mapElements.length > 0) {
            var mapId = mapElements[0].id;
            mymap = window[mapId];
            
            if (!mymap) {
                console.error('Karte nicht gefunden!');
                return;
            }
            
            console.log('Karte gefunden, sammle FeatureGroups...');
            
            // Sammle alle FeatureGroups
            mymap.eachLayer(function(layer) {
                if (layer instanceof L.FeatureGroup && layer.options && layer.options.name) {
                    featureGroups[layer.options.name] = layer;
                    console.log('FeatureGroup gefunden:', layer.options.name);
                }
            });
            
            console.log('Gefundene FeatureGroups:', Object.keys(featureGroups).length);
        }
        
        // Toggle Panel
        document.getElementById('panel-header').addEventListener('click', function() {
            var content = document.getElementById('panel-content');
            var icon = document.getElementById('toggle-icon');
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.innerHTML = '▼';
            } else {
                content.style.display = 'none';
                icon.innerHTML = '◀';
            }
        });
    }
    
    function toggleKandidat(kandidat, show) {
        console.log('Toggle Kandidat:', kandidat, show);
        if (!mymap || !featureGroups[kandidat]) {
            console.error('Kandidat nicht gefunden:', kandidat);
            return;
        }
        
        if (show) {
            mymap.addLayer(featureGroups[kandidat]);
        } else {
            mymap.removeLayer(featureGroups[kandidat]);
        }
        
        updateStatus();
    }
    
    function toggleGroup(group, show) {
        console.log('Toggle Gruppe:', group, show);
        var kandidaten = group === 'marcus' ? kandidatenZuordnung['Marcus Schmitz'] : kandidatenZuordnung['Thomas Schlegel'];
        
        kandidaten.forEach(function(kandidat) {
            var checkbox = document.querySelector('#check-' + kandidat.replace(/ /g, '_').replace(/\\./g, ''));
            if (checkbox) {
                checkbox.checked = show;
                toggleKandidat(kandidat, show);
            }
        });
        
        updateStatus();
    }
    
    function showOnlyMarcus() {
        console.log('Zeige nur Marcus Schmitz');
        hideAll();
        document.getElementById('group-marcus').checked = true;
        toggleGroup('marcus', true);
    }
    
    function showOnlyThomas() {
        console.log('Zeige nur Thomas Schlegel');
        hideAll();
        document.getElementById('group-thomas').checked = true;
        toggleGroup('thomas', true);
    }
    
    function showAll() {
        console.log('Zeige alle');
        document.querySelectorAll('.kandidat-check').forEach(function(checkbox) {
            checkbox.checked = true;
            toggleKandidat(checkbox.getAttribute('data-kandidat'), true);
        });
        document.getElementById('group-marcus').checked = true;
        document.getElementById('group-thomas').checked = true;
        updateStatus();
    }
    
    function hideAll() {
        console.log('Verstecke alle');
        document.querySelectorAll('.kandidat-check').forEach(function(checkbox) {
            checkbox.checked = false;
            toggleKandidat(checkbox.getAttribute('data-kandidat'), false);
        });
        document.getElementById('group-marcus').checked = false;
        document.getElementById('group-thomas').checked = false;
        updateStatus();
    }
    
    function updateStatus() {
        var total = document.querySelectorAll('.kandidat-check').length;
        var checked = document.querySelectorAll('.kandidat-check:checked').length;
        
        var text = '';
        if (checked === 0) {
            text = 'Keine Punkte sichtbar';
        } else if (checked === total) {
            text = 'Alle Punkte sichtbar';
        } else {
            text = checked + ' von ' + total + ' Kandidaten aktiv';
        }
        
        document.getElementById('status-text').innerHTML = text;
    }
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(control_html))
    
    # Speichern
    m.save('wahlbezirke_final_map.html')
    print("✓ Finale funktionierende Karte erstellt: wahlbezirke_final_map.html")
    
    # Statistik
    print("\nStatistik:")
    for kreistag, kandidaten in kreistagskandidaten.items():
        total = len(df[df['kandidat'].isin(kandidaten)])
        print(f"  {kreistag}: {total} Punkte")

if __name__ == "__main__":
    main()