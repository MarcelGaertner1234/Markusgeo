#!/usr/bin/env python3
"""
Erstellt eine funktionierende Karte mit korrekter Layer-Synchronisation
"""

import pandas as pd
import folium
import json

# Farbschema
KREISTAGS_FARBEN = {
    'Marcus Schmitz': '#1976D2',  # Blau
    'Thomas Schlegel': '#D32F2F'   # Rot
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
    # Verwende die komplette Datei
    df = pd.read_csv('wahlbezirke_complete.csv')
    print(f"✓ Verwende vollständige Datei mit {len(df)} Einträgen")
    
    # Kreistagskandidaten-Zuordnung
    kreistagskandidaten = {
        'Marcus Schmitz': ['Gisa Hauschildt', 'Jörg Reintsema', 'Ulrike Herrgesell', 'Thomas Hellbusch',
                          'Philipp Beck', 'Manfred Henry Daub', 'Christopher Seinsche', 'Björn Dittich'],
        'Thomas Schlegel': ['Dagmar Schmitz', 'Jörg Menne', 'Markus Lang', 'Titzian Crisci',
                           'Stephan Rühl', 'Roger Adolphs', 'Frank Schmitz', 'Thomas Schlegel']
    }
    
    # Füge Farben und Kreistagkandidat-Info hinzu
    df['kandidat_farbe'] = df['kandidat'].map(KANDIDATEN_FARBEN)
    
    # Kreistagkandidat zuordnen
    df['kreistagkandidat'] = ''
    for kreistagkandidat, kandidaten in kreistagskandidaten.items():
        df.loc[df['kandidat'].isin(kandidaten), 'kreistagkandidat'] = kreistagkandidat
    
    # Karte erstellen
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    
    # Erstelle Marker für jeden Punkt
    for idx, row in df.iterrows():
        # Eindeutige ID für jeden Marker
        marker_id = f"marker_{idx}_{row['wbz']}_{row['kandidat'].replace(' ', '_')}"
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <b style="font-size: 14px;">{row['street']}</b><br>
            <span style="color: #666;">{row.get('original', row['street'])}</span><br>
            <span style="color: #666;">{row['postal_code']} {row['city']}</span><br>
            <hr style="margin: 5px 0;">
            <b>Wahlbezirk:</b> {row.get('bezirk', row['wbz'])}<br>
            <b>CDU-Kandidat/in:</b> {row['kandidat']}<br>
            <b>Kreistagkandidat:</b> <span style="color: {KREISTAGS_FARBEN.get(row['kreistagkandidat'], '#000')}; font-weight: bold;">{row['kreistagkandidat']}</span><br>
            <b>Wahlberechtigte:</b> {row['wahlberechtigte']}<br>
            <small style="color: #999;">Koordinaten: {row['latitude']:.6f}, {row['longitude']:.6f}</small>
        </div>
        """
        
        # Erstelle Marker mit custom Icon
        marker = folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['street']} ({row['wbz']})",
            color=KREISTAGS_FARBEN.get(row['kreistagkandidat'], '#808080'),
            fill=True,
            fillColor=row['kandidat_farbe'],
            fillOpacity=0.8,
            weight=3,
            className=f"kandidat-marker kandidat-{row['kandidat'].replace(' ', '_')} kreistag-{row['kreistagkandidat'].replace(' ', '_')} {marker_id}"
        )
        
        marker.add_to(m)
    
    # Custom HTML/CSS/JS für die Kontrollen
    custom_html = '''
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
                    <button id="btn-marcus-only" class="kreistag-btn"
                            style="padding: 15px; background: #1976D2; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 14px;
                                   transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                        NUR Marcus Schmitz<br>
                        <small style="font-weight: normal; font-size: 11px;">
                            8 Bezirke anzeigen
                        </small>
                    </button>
                    <button id="btn-thomas-only" class="kreistag-btn"
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
                    <button id="btn-all" class="control-btn"
                            style="flex: 1; padding: 10px; background: #4CAF50; 
                                   color: white; border: none; border-radius: 6px; 
                                   cursor: pointer; font-weight: bold; font-size: 13px;">
                        ✓ Alle anzeigen
                    </button>
                    <button id="btn-none" class="control-btn"
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
                            <input type="checkbox" class="group-check" data-group="Marcus_Schmitz" checked
                                   style="margin-right: 8px; width: 18px; height: 18px;">
                            <span style="color: #1976D2;">Marcus Schmitz - Alle 8 Bezirke</span>
                        </label>
                    </div>
                    <div style="padding-left: 20px;">
    '''
    
    # Marcus Schmitz Kandidaten
    for kandidat in kreistagskandidaten['Marcus Schmitz']:
        farbe = KANDIDATEN_FARBEN[kandidat]
        anzahl = len(df[df['kandidat'] == kandidat])
        custom_html += f'''
        <label style="display: flex; align-items: center; margin: 5px 0; cursor: pointer;">
            <input type="checkbox" class="kandidat-check" data-kandidat="{kandidat.replace(' ', '_')}" 
                   data-group="Marcus_Schmitz" checked
                   style="margin-right: 8px;">
            <span style="background-color: {farbe}; width: 18px; height: 18px; 
                       display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
            <span>{kandidat} ({anzahl} Punkte)</span>
        </label>
        '''
    
    custom_html += '''
                    </div>
                </div>
                
                <!-- Thomas Schlegel Gruppe -->
                <div>
                    <div style="background: #FFEBEE; padding: 8px; border-radius: 5px; margin-bottom: 8px;">
                        <label style="display: flex; align-items: center; cursor: pointer; font-weight: bold;">
                            <input type="checkbox" class="group-check" data-group="Thomas_Schlegel" checked
                                   style="margin-right: 8px; width: 18px; height: 18px;">
                            <span style="color: #D32F2F;">Thomas Schlegel - Alle 8 Bezirke</span>
                        </label>
                    </div>
                    <div style="padding-left: 20px;">
    '''
    
    # Thomas Schlegel Kandidaten
    for kandidat in kreistagskandidaten['Thomas Schlegel']:
        farbe = KANDIDATEN_FARBEN[kandidat]
        anzahl = len(df[df['kandidat'] == kandidat])
        custom_html += f'''
        <label style="display: flex; align-items: center; margin: 5px 0; cursor: pointer;">
            <input type="checkbox" class="kandidat-check" data-kandidat="{kandidat.replace(' ', '_')}" 
                   data-group="Thomas_Schlegel" checked
                   style="margin-right: 8px;">
            <span style="background-color: {farbe}; width: 18px; height: 18px; 
                       display: inline-block; border-radius: 50%; margin-right: 8px;"></span>
            <span>{kandidat} ({anzahl} Punkte)</span>
        </label>
        '''
    
    custom_html += '''
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
    
    <style>
    .kandidat-marker {
        transition: opacity 0.3s ease;
    }
    .kandidat-marker.hidden {
        opacity: 0 !important;
        pointer-events: none !important;
    }
    </style>
    
    <script>
    // Warte bis die Karte geladen ist
    window.addEventListener('load', function() {
        setTimeout(initControls, 1000);
    });
    
    function initControls() {
        console.log('Initialisiere Kontrollen...');
        
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
        
        // Kreistagskandidaten Buttons
        document.getElementById('btn-marcus-only').addEventListener('click', function() {
            showOnlyKreistag('Marcus_Schmitz');
        });
        
        document.getElementById('btn-thomas-only').addEventListener('click', function() {
            showOnlyKreistag('Thomas_Schlegel');
        });
        
        // Alle/Keine Buttons
        document.getElementById('btn-all').addEventListener('click', showAll);
        document.getElementById('btn-none').addEventListener('click', hideAll);
        
        // Gruppen-Checkboxen
        document.querySelectorAll('.group-check').forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                var group = this.dataset.group;
                var checked = this.checked;
                
                // Alle Kandidaten dieser Gruppe
                document.querySelectorAll('.kandidat-check[data-group="' + group + '"]').forEach(function(kandidatCheck) {
                    kandidatCheck.checked = checked;
                    updateMarkerVisibility(kandidatCheck.dataset.kandidat, checked);
                });
                
                updateStatus();
            });
        });
        
        // Kandidaten-Checkboxen
        document.querySelectorAll('.kandidat-check').forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                updateMarkerVisibility(this.dataset.kandidat, this.checked);
                updateGroupCheckbox(this.dataset.group);
                updateStatus();
            });
        });
    }
    
    function showOnlyKreistag(kreistag) {
        console.log('Zeige nur:', kreistag);
        
        // Alle Checkboxen deaktivieren
        document.querySelectorAll('.kandidat-check').forEach(function(checkbox) {
            checkbox.checked = false;
        });
        document.querySelectorAll('.group-check').forEach(function(checkbox) {
            checkbox.checked = false;
        });
        
        // Alle Marker verstecken
        document.querySelectorAll('.kandidat-marker').forEach(function(marker) {
            marker.classList.add('hidden');
        });
        
        // Nur gewünschte Gruppe aktivieren
        document.querySelector('.group-check[data-group="' + kreistag + '"]').checked = true;
        document.querySelectorAll('.kandidat-check[data-group="' + kreistag + '"]').forEach(function(checkbox) {
            checkbox.checked = true;
            updateMarkerVisibility(checkbox.dataset.kandidat, true);
        });
        
        updateStatus();
    }
    
    function showAll() {
        document.querySelectorAll('.kandidat-check').forEach(function(checkbox) {
            checkbox.checked = true;
            updateMarkerVisibility(checkbox.dataset.kandidat, true);
        });
        document.querySelectorAll('.group-check').forEach(function(checkbox) {
            checkbox.checked = true;
        });
        updateStatus();
    }
    
    function hideAll() {
        document.querySelectorAll('.kandidat-check').forEach(function(checkbox) {
            checkbox.checked = false;
            updateMarkerVisibility(checkbox.dataset.kandidat, false);
        });
        document.querySelectorAll('.group-check').forEach(function(checkbox) {
            checkbox.checked = false;
        });
        updateStatus();
    }
    
    function updateMarkerVisibility(kandidat, visible) {
        var markers = document.querySelectorAll('.kandidat-' + kandidat);
        markers.forEach(function(marker) {
            if (visible) {
                marker.classList.remove('hidden');
            } else {
                marker.classList.add('hidden');
            }
        });
    }
    
    function updateGroupCheckbox(group) {
        var allChecked = true;
        document.querySelectorAll('.kandidat-check[data-group="' + group + '"]').forEach(function(checkbox) {
            if (!checkbox.checked) {
                allChecked = false;
            }
        });
        document.querySelector('.group-check[data-group="' + group + '"]').checked = allChecked;
    }
    
    function updateStatus() {
        var visible = document.querySelectorAll('.kandidat-check:checked').length;
        var total = document.querySelectorAll('.kandidat-check').length;
        
        var text = '';
        if (visible === 0) {
            text = 'Keine Punkte sichtbar';
        } else if (visible === total) {
            text = 'Alle Punkte sichtbar';
        } else {
            text = visible + ' von ' + total + ' Kandidaten sichtbar';
        }
        
        document.getElementById('status-text').innerHTML = text;
    }
    </script>
    '''
    
    m.get_root().html.add_child(folium.Element(custom_html))
    
    # Speichern
    m.save('wahlbezirke_working_map.html')
    print("✓ Funktionierende Karte erstellt: wahlbezirke_working_map.html")

if __name__ == "__main__":
    main()