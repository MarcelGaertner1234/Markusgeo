#!/usr/bin/env python3
"""
Einfache, garantiert funktionierende Karte mit direkter Marker-Kontrolle
"""

import pandas as pd
import folium
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
    # Lade Daten
    df = pd.read_csv('wahlbezirke_complete.csv')
    print(f"✓ Verwende {len(df)} Datenpunkte")
    
    # Kreistagskandidaten
    kreistagskandidaten = {
        'Marcus Schmitz': ['Gisa Hauschildt', 'Jörg Reintsema', 'Ulrike Herrgesell', 'Thomas Hellbusch',
                          'Philipp Beck', 'Manfred Henry Daub', 'Christopher Seinsche', 'Björn Dittich'],
        'Thomas Schlegel': ['Dagmar Schmitz', 'Jörg Menne', 'Markus Lang', 'Titzian Crisci',
                           'Stephan Rühl', 'Roger Adolphs', 'Frank Schmitz', 'Thomas Schlegel']
    }
    
    # Farben hinzufügen
    df['kandidat_farbe'] = df['kandidat'].map(KANDIDATEN_FARBEN)
    
    # Kreistagkandidat zuordnen
    for kreistagkandidat, kandidaten in kreistagskandidaten.items():
        df.loc[df['kandidat'].isin(kandidaten), 'kreistagkandidat'] = kreistagkandidat
        df.loc[df['kandidat'].isin(kandidaten), 'kreistag_farbe'] = KREISTAGS_FARBEN[kreistagkandidat]
    
    # Karte erstellen
    m = folium.Map(
        location=[df['latitude'].mean(), df['longitude'].mean()], 
        zoom_start=12,
        prefer_canvas=True  # Wichtig für Performance
    )
    
    # JavaScript-Code für Marker-Verwaltung
    marker_js = '''
    <script>
    var markers = [];
    var markerData = ''' + df[['kandidat', 'kreistagkandidat', 'latitude', 'longitude', 'street', 'wbz', 'kandidat_farbe', 'kreistag_farbe', 'wahlberechtigte']].to_json(orient='records') + ''';
    var kreistagskandidaten = ''' + json.dumps(kreistagskandidaten) + ''';
    var mymap = null;
    
    // Warte bis Karte geladen ist
    window.addEventListener('load', function() {
        setTimeout(function() {
            initMap();
        }, 500);
    });
    
    function initMap() {
        // Finde Leaflet-Karte
        var mapElements = document.getElementsByClassName('folium-map');
        if (mapElements.length > 0) {
            var mapId = mapElements[0].id;
            mymap = window[mapId];
            
            if (!mymap) {
                console.error('Karte nicht gefunden!');
                return;
            }
            
            console.log('Karte gefunden, erstelle Marker...');
            
            // Erstelle alle Marker
            markerData.forEach(function(data, index) {
                var marker = L.circleMarker([data.latitude, data.longitude], {
                    radius: 8,
                    color: data.kreistag_farbe,
                    fillColor: data.kandidat_farbe,
                    fillOpacity: 0.8,
                    weight: 3
                });
                
                var popupContent = '<div style="font-family: Arial; width: 250px;">' +
                    '<b>' + data.street + '</b><br>' +
                    'Wahlbezirk: ' + data.wbz + '<br>' +
                    'Kandidat: ' + data.kandidat + '<br>' +
                    'Kreistagkandidat: <b style="color: ' + data.kreistag_farbe + '">' + data.kreistagkandidat + '</b><br>' +
                    'Wahlberechtigte: ' + data.wahlberechtigte +
                    '</div>';
                
                marker.bindPopup(popupContent);
                marker.bindTooltip(data.street + ' (' + data.wbz + ')');
                
                // Speichere Referenz
                marker._customData = {
                    kandidat: data.kandidat,
                    kreistagkandidat: data.kreistagkandidat,
                    index: index
                };
                
                marker.addTo(mymap);
                markers.push(marker);
            });
            
            console.log('Erstellt: ' + markers.length + ' Marker');
            updateStatus();
        } else {
            console.error('Keine Karte gefunden!');
        }
    }
    
    function showOnlyMarcus() {
        console.log('Zeige nur Marcus Schmitz');
        markers.forEach(function(marker) {
            if (marker._customData.kreistagkandidat === 'Marcus Schmitz') {
                marker.addTo(mymap);
            } else {
                mymap.removeLayer(marker);
            }
        });
        
        // Update Checkboxen
        document.querySelectorAll('.kandidat-check').forEach(function(cb) {
            var kandidat = cb.getAttribute('data-kandidat');
            cb.checked = kreistagskandidaten['Marcus Schmitz'].includes(kandidat);
        });
        
        document.getElementById('group-marcus').checked = true;
        document.getElementById('group-thomas').checked = false;
        
        updateStatus();
    }
    
    function showOnlyThomas() {
        console.log('Zeige nur Thomas Schlegel');
        markers.forEach(function(marker) {
            if (marker._customData.kreistagkandidat === 'Thomas Schlegel') {
                marker.addTo(mymap);
            } else {
                mymap.removeLayer(marker);
            }
        });
        
        // Update Checkboxen
        document.querySelectorAll('.kandidat-check').forEach(function(cb) {
            var kandidat = cb.getAttribute('data-kandidat');
            cb.checked = kreistagskandidaten['Thomas Schlegel'].includes(kandidat);
        });
        
        document.getElementById('group-marcus').checked = false;
        document.getElementById('group-thomas').checked = true;
        
        updateStatus();
    }
    
    function showAll() {
        console.log('Zeige alle Marker');
        markers.forEach(function(marker) {
            marker.addTo(mymap);
        });
        
        document.querySelectorAll('.kandidat-check').forEach(function(cb) {
            cb.checked = true;
        });
        document.getElementById('group-marcus').checked = true;
        document.getElementById('group-thomas').checked = true;
        
        updateStatus();
    }
    
    function hideAll() {
        console.log('Verstecke alle Marker');
        markers.forEach(function(marker) {
            mymap.removeLayer(marker);
        });
        
        document.querySelectorAll('.kandidat-check').forEach(function(cb) {
            cb.checked = false;
        });
        document.getElementById('group-marcus').checked = false;
        document.getElementById('group-thomas').checked = false;
        
        updateStatus();
    }
    
    function toggleKandidat(kandidat, show) {
        console.log('Toggle Kandidat:', kandidat, show);
        markers.forEach(function(marker) {
            if (marker._customData.kandidat === kandidat) {
                if (show) {
                    marker.addTo(mymap);
                } else {
                    mymap.removeLayer(marker);
                }
            }
        });
        updateGroupCheckbox();
        updateStatus();
    }
    
    function toggleGroup(group, show) {
        console.log('Toggle Gruppe:', group, show);
        var kandidaten = group === 'marcus' ? kreistagskandidaten['Marcus Schmitz'] : kreistagskandidaten['Thomas Schlegel'];
        
        kandidaten.forEach(function(kandidat) {
            var checkbox = document.querySelector('.kandidat-check[data-kandidat="' + kandidat + '"]');
            if (checkbox) {
                checkbox.checked = show;
                toggleKandidat(kandidat, show);
            }
        });
    }
    
    function updateGroupCheckbox() {
        // Marcus Gruppe
        var marcusKandidaten = kreistagskandidaten['Marcus Schmitz'];
        var marcusAllChecked = true;
        marcusKandidaten.forEach(function(kandidat) {
            var cb = document.querySelector('.kandidat-check[data-kandidat="' + kandidat + '"]');
            if (cb && !cb.checked) marcusAllChecked = false;
        });
        document.getElementById('group-marcus').checked = marcusAllChecked;
        
        // Thomas Gruppe
        var thomasKandidaten = kreistagskandidaten['Thomas Schlegel'];
        var thomasAllChecked = true;
        thomasKandidaten.forEach(function(kandidat) {
            var cb = document.querySelector('.kandidat-check[data-kandidat="' + kandidat + '"]');
            if (cb && !cb.checked) thomasAllChecked = false;
        });
        document.getElementById('group-thomas').checked = thomasAllChecked;
    }
    
    function updateStatus() {
        var total = markers.length;
        var visible = 0;
        markers.forEach(function(marker) {
            if (mymap && mymap.hasLayer(marker)) {
                visible++;
            }
        });
        
        var text = '';
        if (visible === 0) {
            text = 'Keine Punkte sichtbar';
        } else if (visible === total) {
            text = 'Alle ' + total + ' Punkte sichtbar';
        } else {
            text = visible + ' von ' + total + ' Punkten sichtbar';
        }
        
        document.getElementById('status-text').innerHTML = text;
    }
    </script>
    '''
    
    # Control Panel HTML
    control_html = '''
    <div id="control-panel" style="position: fixed; 
                bottom: 20px; right: 20px; width: 500px;
                background-color: white; z-index: 1000; 
                border: 3px solid #333; border-radius: 10px;
                box-shadow: 0 0 25px rgba(0,0,0,0.4);
                font-family: Arial, sans-serif;">
        
        <div style="background: linear-gradient(135deg, #1976D2 0%, #D32F2F 100%); 
                    color: white; padding: 15px; border-radius: 7px 7px 0 0;">
            <h3 style="margin: 0; font-size: 20px; text-align: center;">
                CDU Wahlbezirke Nümbrecht 2024
            </h3>
        </div>
        
        <div style="padding: 20px; max-height: 600px; overflow-y: auto;">
            
            <!-- Kreistagskandidaten -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h4 style="margin: 0 0 15px 0;">🏛️ Kreistagskandidaten</h4>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <button onclick="showOnlyMarcus()" 
                            style="padding: 12px; background: #1976D2; color: white; 
                                   border: none; border-radius: 6px; cursor: pointer; 
                                   font-weight: bold;">
                        NUR Marcus Schmitz<br>
                        <small>8 Bezirke</small>
                    </button>
                    <button onclick="showOnlyThomas()" 
                            style="padding: 12px; background: #D32F2F; color: white; 
                                   border: none; border-radius: 6px; cursor: pointer; 
                                   font-weight: bold;">
                        NUR Thomas Schlegel<br>
                        <small>8 Bezirke</small>
                    </button>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                    <button onclick="showAll()" 
                            style="padding: 10px; background: #4CAF50; color: white; 
                                   border: none; border-radius: 6px; cursor: pointer;">
                        ✓ Alle anzeigen
                    </button>
                    <button onclick="hideAll()" 
                            style="padding: 10px; background: #f44336; color: white; 
                                   border: none; border-radius: 6px; cursor: pointer;">
                        ✗ Alle ausblenden
                    </button>
                </div>
            </div>
            
            <!-- Kandidaten -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                <h4 style="margin: 0 0 10px 0;">✅ Einzelne Kandidaten</h4>
                
                <!-- Marcus Gruppe -->
                <div style="margin-bottom: 15px;">
                    <label style="font-weight: bold; color: #1976D2;">
                        <input type="checkbox" id="group-marcus" checked 
                               onchange="toggleGroup('marcus', this.checked)">
                        Marcus Schmitz Gruppe
                    </label>
                    <div style="padding-left: 20px; margin-top: 5px;">
    '''
    
    # Marcus Kandidaten
    for kandidat in kreistagskandidaten['Marcus Schmitz']:
        anzahl = len(df[df['kandidat'] == kandidat])
        control_html += f'''
                        <label style="display: block; margin: 3px 0;">
                            <input type="checkbox" class="kandidat-check" 
                                   data-kandidat="{kandidat}" checked
                                   onchange="toggleKandidat('{kandidat}', this.checked)">
                            {kandidat} ({anzahl})
                        </label>
        '''
    
    control_html += '''
                    </div>
                </div>
                
                <!-- Thomas Gruppe -->
                <div>
                    <label style="font-weight: bold; color: #D32F2F;">
                        <input type="checkbox" id="group-thomas" checked 
                               onchange="toggleGroup('thomas', this.checked)">
                        Thomas Schlegel Gruppe
                    </label>
                    <div style="padding-left: 20px; margin-top: 5px;">
    '''
    
    # Thomas Kandidaten
    for kandidat in kreistagskandidaten['Thomas Schlegel']:
        anzahl = len(df[df['kandidat'] == kandidat])
        control_html += f'''
                        <label style="display: block; margin: 3px 0;">
                            <input type="checkbox" class="kandidat-check" 
                                   data-kandidat="{kandidat}" checked
                                   onchange="toggleKandidat('{kandidat}', this.checked)">
                            {kandidat} ({anzahl})
                        </label>
        '''
    
    control_html += '''
                    </div>
                </div>
            </div>
            
            <!-- Status -->
            <div style="margin-top: 15px; padding: 10px; background: #e8f5e9; 
                        border-radius: 6px; text-align: center;">
                <span id="status-text" style="color: #2e7d32; font-weight: bold;">
                    Initialisiere...
                </span>
            </div>
        </div>
    </div>
    '''
    
    # Füge JavaScript und HTML zur Karte hinzu
    m.get_root().html.add_child(folium.Element(marker_js))
    m.get_root().html.add_child(folium.Element(control_html))
    
    # Speichern
    m.save('wahlbezirke_simple_working.html')
    print("✓ Karte erstellt: wahlbezirke_simple_working.html")

if __name__ == "__main__":
    main()