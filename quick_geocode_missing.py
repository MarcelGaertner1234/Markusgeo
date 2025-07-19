#!/usr/bin/env python3
"""
Schnelles Geocoding für fehlende Ortsteile
"""

import json
import pandas as pd
import time
from geopy.geocoders import Nominatim

# Bekannte Ortsteile in Nümbrecht mit ungefähren Koordinaten
ORTSTEILE_COORDS = {
    'Gaderoth': (50.8849, 7.5680),
    'Breunfeld': (50.8890, 7.5750),
    'Oberbreidenbach': (50.8776, 7.5876),
    'Prombach': (50.8820, 7.5920),
    'Winterborn': (50.9180, 7.5950),
    'Grötzenberg': (50.9250, 7.5780),
    'Hömel': (50.9150, 7.5650),
    'Benroth': (50.8950, 7.5550),
    'Berkenroth': (50.8980, 7.5580),
    'Harscheid': (50.8850, 7.5450),
    'Marienberghausen': (50.8700, 7.5300),
    'Elsenroth': (50.8600, 7.5400)
}

def main():
    # Lade bestehende Daten
    df_existing = pd.read_csv('wahlbezirke_map.csv')
    
    # Lade Wahlbezirk-Zuordnung
    with open('wahlbezirke_zuordnung.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        wahlbezirke = data['wahlbezirke']
    
    # Kreistagskandidaten-Info
    kreistagskandidaten = {
        'Marcus Schmitz': {
            'kandidaten': ['Gisa Hauschildt', 'Jörg Reintsema', 'Ulrike Herrgesell', 'Thomas Hellbusch',
                          'Philipp Beck', 'Manfred Henry Daub', 'Christopher Seinsche', 'Björn Dittich'],
            'farbe': '#1976D2'
        },
        'Thomas Schlegel': {
            'kandidaten': ['Dagmar Schmitz', 'Jörg Menne', 'Markus Lang', 'Titzian Crisci',
                           'Stephan Rühl', 'Roger Adolphs', 'Frank Schmitz', 'Thomas Schlegel'],
            'farbe': '#D32F2F'
        }
    }
    
    # Finde fehlende Bezirke
    vorhandene_wbz = set(df_existing['wbz'].unique())
    alle_wbz = set(wahlbezirke.keys())
    fehlende_wbz = alle_wbz - vorhandene_wbz
    
    print(f"Vorhandene Bezirke: {sorted(vorhandene_wbz)}")
    print(f"Fehlende Bezirke: {sorted(fehlende_wbz)}")
    
    # Ergänze fehlende Bezirke
    neue_eintraege = []
    
    for wbz in fehlende_wbz:
        wbz_data = wahlbezirke[wbz]
        ortsteil = wbz_data['name']
        kandidat = wbz_data['kandidat']
        
        # Finde Kreistagkandidat
        kreistagkandidat = ''
        for kreistag, info in kreistagskandidaten.items():
            if kandidat in info['kandidaten']:
                kreistagkandidat = kreistag
                break
        
        # Verwende bekannte Koordinaten oder Zentrum von Nümbrecht
        if ortsteil in ORTSTEILE_COORDS:
            lat, lon = ORTSTEILE_COORDS[ortsteil]
        else:
            # Fallback: Zentrum Nümbrecht
            lat, lon = 50.9033978, 7.5409481
        
        neue_eintraege.append({
            'street': f"{ortsteil} (Ortszentrum)",
            'original': ortsteil,
            'house_number': '',
            'postal_code': '51588',
            'city': 'Nümbrecht',
            'full_address': f"{ortsteil}, 51588 Nümbrecht",
            'wbz': wbz,
            'bezirk': f"{wbz} - {ortsteil}",
            'kandidat': kandidat,
            'wahlberechtigte': wbz_data['wahlberechtigte'],
            'latitude': lat,
            'longitude': lon,
            'kreistagkandidat': kreistagkandidat
        })
        
        print(f"✓ Ergänzt: {wbz} - {ortsteil} ({kandidat}) bei {lat:.4f}, {lon:.4f}")
    
    # Kombiniere alte und neue Daten
    df_neue = pd.DataFrame(neue_eintraege)
    
    # Füge Kreistagkandidat zu existierenden Daten hinzu
    df_existing['kreistagkandidat'] = ''
    for idx, row in df_existing.iterrows():
        for kreistag, info in kreistagskandidaten.items():
            if row['kandidat'] in info['kandidaten']:
                df_existing.at[idx, 'kreistagkandidat'] = kreistag
                break
    
    # Kombiniere
    df_komplett = pd.concat([df_existing, df_neue], ignore_index=True)
    
    # Speichere
    df_komplett.to_csv('wahlbezirke_complete.csv', index=False, encoding='utf-8')
    
    print(f"\n✓ Gesamt: {len(df_komplett)} Einträge gespeichert")
    print(f"  - Bestehend: {len(df_existing)}")
    print(f"  - Neu ergänzt: {len(df_neue)}")
    
    # Statistik
    print("\nStatistik pro Kreistagkandidat:")
    for kreistag in ['Marcus Schmitz', 'Thomas Schlegel']:
        kandidaten = kreistagskandidaten[kreistag]['kandidaten']
        eintraege = df_komplett[df_komplett['kandidat'].isin(kandidaten)]
        bezirke = eintraege['wbz'].nunique()
        print(f"  {kreistag}: {len(eintraege)} Einträge in {bezirke} Bezirken")

if __name__ == "__main__":
    main()