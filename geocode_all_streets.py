#!/usr/bin/env python3
"""
Geocodiert ALLE Straßen aus wahlbezirke_zuordnung.json
"""

import json
import time
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging
import re

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Geocoder
geocoder = Nominatim(user_agent="nuembrecht_geocoder", timeout=10)

def extract_street_name(street_with_numbers):
    """Extrahiert den Straßennamen ohne Hausnummernbereich"""
    # Entferne Hausnummernbereiche wie "- 1-17" oder "- alle"
    clean_street = re.sub(r'\s*-\s*(alle|\d+.*?)$', '', street_with_numbers).strip()
    return clean_street

def geocode_address(street, city="Nümbrecht", postal_code="51588", retry_count=3):
    """Geocodiert eine Adresse mit Retry-Logik"""
    
    for attempt in range(retry_count):
        try:
            # Versuche verschiedene Varianten
            queries = [
                f"{street}, {postal_code} {city}, Deutschland",
                f"{street}, {city}, Deutschland",
                f"{street}, {city}",
                f"{city}, {street}"
            ]
            
            for query in queries:
                time.sleep(1.2)  # Rate limiting
                location = geocoder.geocode(query, country_codes=['de'])
                if location:
                    return {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'display_name': location.raw.get('display_name', ''),
                        'query_used': query
                    }
            
            # Wenn keine direkte Übereinstimmung, versuche Ortsteil
            ortsteil_match = re.search(r'(WBZ \d+) - (.+?)$', street)
            if ortsteil_match:
                ortsteil = ortsteil_match.group(2)
                time.sleep(1.2)
                location = geocoder.geocode(f"{ortsteil}, {city}, Deutschland", country_codes=['de'])
                if location:
                    return {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'display_name': location.raw.get('display_name', ''),
                        'query_used': f"Ortsteil: {ortsteil}"
                    }
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding-Fehler bei {street} (Versuch {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                time.sleep(5)  # Längere Pause bei Fehler
                continue
    
    return None

def main():
    # Lade wahlbezirke_zuordnung.json
    with open('wahlbezirke_zuordnung.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        wahlbezirke = data['wahlbezirke']
    
    # Sammle alle Straßen
    all_streets = []
    for wbz_key, wbz_data in wahlbezirke.items():
        logger.info(f"\nVerarbeite {wbz_key} - {wbz_data['name']} ({wbz_data['kandidat']})")
        
        # Für Ortsteile ohne spezifische Straßen
        if 'strassen' not in wbz_data or len(wbz_data['strassen']) == 0:
            if 'ortsteile' in wbz_data and len(wbz_data['ortsteile']) > 0:
                # Geocodiere den Ortsteil selbst
                for ortsteil in wbz_data['ortsteile']:
                    logger.info(f"  Geocodiere Ortsteil: {ortsteil}")
                    coords = geocode_address(ortsteil, city="Nümbrecht")
                    
                    if coords:
                        all_streets.append({
                            'street': ortsteil,
                            'original': ortsteil,
                            'house_number': '',
                            'postal_code': '51588',
                            'city': 'Nümbrecht',
                            'full_address': f"{ortsteil}, 51588 Nümbrecht",
                            'wbz': wbz_key,
                            'bezirk': f"{wbz_key} - {wbz_data['name']}",
                            'kandidat': wbz_data['kandidat'],
                            'wahlberechtigte': wbz_data['wahlberechtigte'],
                            'latitude': coords['latitude'],
                            'longitude': coords['longitude'],
                            'geocode_info': coords['display_name']
                        })
                        logger.info(f"    ✓ Erfolgreich: {coords['latitude']:.6f}, {coords['longitude']:.6f}")
                    else:
                        logger.warning(f"    ✗ Nicht gefunden: {ortsteil}")
        
        # Normale Straßen
        if 'strassen' in wbz_data:
            for street_raw in wbz_data['strassen']:
                street_clean = extract_street_name(street_raw)
                logger.info(f"  Geocodiere: {street_clean} (von: {street_raw})")
                
                coords = geocode_address(street_clean, city="Nümbrecht")
                
                if coords:
                    all_streets.append({
                        'street': street_clean,
                        'original': street_raw,
                        'house_number': '',
                        'postal_code': '51588',
                        'city': 'Nümbrecht',
                        'full_address': f"{street_clean}, 51588 Nümbrecht",
                        'wbz': wbz_key,
                        'bezirk': f"{wbz_key} - {wbz_data['name']}",
                        'kandidat': wbz_data['kandidat'],
                        'wahlberechtigte': wbz_data['wahlberechtigte'],
                        'latitude': coords['latitude'],
                        'longitude': coords['longitude'],
                        'geocode_info': coords['display_name']
                    })
                    logger.info(f"    ✓ Erfolgreich: {coords['latitude']:.6f}, {coords['longitude']:.6f}")
                else:
                    logger.warning(f"    ✗ Nicht gefunden: {street_clean}")
                    # Trotzdem speichern mit Zentrum von Nümbrecht als Fallback
                    all_streets.append({
                        'street': street_clean,
                        'original': street_raw,
                        'house_number': '',
                        'postal_code': '51588',
                        'city': 'Nümbrecht',
                        'full_address': f"{street_clean}, 51588 Nümbrecht",
                        'wbz': wbz_key,
                        'bezirk': f"{wbz_key} - {wbz_data['name']}",
                        'kandidat': wbz_data['kandidat'],
                        'wahlberechtigte': wbz_data['wahlberechtigte'],
                        'latitude': 50.9033978,  # Zentrum Nümbrecht
                        'longitude': 7.5409481,
                        'geocode_info': 'Fallback: Zentrum Nümbrecht'
                    })
    
    # Speichere als CSV
    df = pd.DataFrame(all_streets)
    df.to_csv('wahlbezirke_all_streets_geocoded.csv', index=False, encoding='utf-8')
    
    # Statistik
    logger.info("\n" + "="*50)
    logger.info("GEOCODING ABGESCHLOSSEN")
    logger.info("="*50)
    logger.info(f"Gesamt Straßen/Ortsteile: {len(all_streets)}")
    
    # Statistik pro Kandidat
    kandidaten_stats = df.groupby('kandidat').agg({
        'street': 'count',
        'wahlberechtigte': 'first'
    }).rename(columns={'street': 'anzahl_strassen'})
    
    logger.info("\nStatistik pro Kandidat:")
    for kandidat, stats in kandidaten_stats.iterrows():
        wbz = df[df['kandidat'] == kandidat]['wbz'].iloc[0]
        logger.info(f"  {kandidat} ({wbz}): {stats['anzahl_strassen']} Straßen/Ortsteile, {stats['wahlberechtigte']} Wahlberechtigte")
    
    # Kreistagskandidaten-Statistik
    kreistagskandidaten = {
        'Marcus Schmitz': ['Gisa Hauschildt', 'Jörg Reintsema', 'Ulrike Herrgesell', 'Thomas Hellbusch',
                          'Philipp Beck', 'Manfred Henry Daub', 'Christopher Seinsche', 'Björn Dittich'],
        'Thomas Schlegel': ['Dagmar Schmitz', 'Jörg Menne', 'Markus Lang', 'Titzian Crisci',
                           'Stephan Rühl', 'Roger Adolphs', 'Frank Schmitz', 'Thomas Schlegel']
    }
    
    logger.info("\nStatistik pro Kreistagkandidat:")
    for kreistagkandidat, kandidaten in kreistagskandidaten.items():
        total_strassen = df[df['kandidat'].isin(kandidaten)]['street'].count()
        total_wahlber = df[df['kandidat'].isin(kandidaten)].groupby('kandidat')['wahlberechtigte'].first().sum()
        logger.info(f"  {kreistagkandidat}: {total_strassen} Straßen/Ortsteile, {total_wahlber} Wahlberechtigte")

if __name__ == "__main__":
    main()