import numpy as np
import matplotlib.pyplot as plt
from math import pi, cos, radians, sin

# Stałe
EARTH_RADIUS = 6371000  # promień Ziemi w metrach
EARTH_SURFACE_AREA = 4 * pi * EARTH_RADIUS**2  # powierzchnia Ziemi w m²
EARTH_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS  # obwód Ziemi w metrach

def calculate_image_size(resolution, image_width_px, image_height_px, num_channels):
    """
    Oblicza rozmiar pojedynczego zdjęcia w pikselach i MB.
    
    Parametry:
    resolution (float): Rozdzielczość przestrzenna w m/px
    image_width_px (int): Szerokość obrazu w pikselach
    image_height_px (int): Wysokość obrazu w pikselach
    num_channels (int): Liczba kanałów spektralnych
    
    Zwraca:
    tuple: (całkowita liczba pikseli, rozmiar obrazu w MB)
    """
    total_pixels = image_width_px * image_height_px
    # Zakładamy 2 bajty (16 bitów) na piksel na kanał
    image_size_bytes = total_pixels * num_channels * 2
    image_size_mb = image_size_bytes / (1024 * 1024)
    
    return (total_pixels, image_size_mb)

def calculate_ground_coverage(altitude, fov_degrees, sensor_width_mm, sensor_height_mm, pixel_size_um):
    """
    Oblicza obszar pokrycia terenu przez pojedyncze zdjęcie.
    
    Parametry:
    altitude (float): Wysokość orbity w metrach
    fov_degrees (float): Kąt widzenia w stopniach
    sensor_width_mm (float): Szerokość matrycy w mm
    sensor_height_mm (float): Wysokość matrycy w mm
    pixel_size_um (float): Rozmiar piksela w mikrometrach
    
    Zwraca:
    tuple: (szerokość pokrycia w m, wysokość pokrycia w m, szerokość w px, wysokość w px)
    """
    fov_rad = radians(fov_degrees)
    swath_width = 2 * altitude * np.tan(fov_rad / 2)
    
    # Proporcja sensora
    aspect_ratio = sensor_width_mm / sensor_height_mm
    
    # Obliczamy wysokość pokrycia (w kierunku lotu)
    swath_height = swath_width / aspect_ratio
    
    # Obliczamy rozdzielczość w pikselach
    width_px = int(sensor_width_mm * 1000 / pixel_size_um)
    height_px = int(sensor_height_mm * 1000 / pixel_size_um)
    
    return (swath_width, swath_height, width_px, height_px)

def calculate_number_of_images(resolution, swath_width, swath_height, overlap_percent=10):
    """
    Oblicza liczbę zdjęć potrzebnych do pokrycia całej Ziemi.
    
    Parametry:
    resolution (float): Rozdzielczość przestrzenna w m/px
    swath_width (float): Szerokość pasa pokrycia w metrach
    swath_height (float): Wysokość pasa pokrycia w metrach
    overlap_percent (float): Procent nakładania się obrazów
    
    Zwraca:
    int: Liczba zdjęć potrzebnych do pokrycia Ziemi
    """
    effective_width = swath_width * (1 - overlap_percent/100)
    effective_height = swath_height * (1 - overlap_percent/100)
    
    effective_area = effective_width * effective_height
    
    # Uwzględniamy krzywizne Ziemi i inne czynniki - mnożnik korekcyjny
    correction_factor = 1.2
    
    # Liczba zdjęć potrzebnych do pokrycia całej Ziemi
    num_images = (EARTH_SURFACE_AREA / effective_area) * correction_factor
    
    return int(np.ceil(num_images))

def calculate_sso_orbit_parameters(altitude, inclination_degrees=98):
    """
    Oblicza dodatkowe parametry dla orbity heliosynchronicznej (SSO).
    
    Parametry:
    altitude (float): Wysokość orbity w metrach
    inclination_degrees (float): Inklinacja orbity w stopniach
    
    Zwraca:
    dict: Słownik z parametrami orbity SSO
    """
    # Parametry orbity
    orbital_radius = EARTH_RADIUS + altitude
    
    # Przesunięcie węzła orbity na dzień (przesunięcie precesyjne)
    # Dla SSO to około 0.9856° na dzień (360° / 365.25 dni)
    nodal_precession_deg_per_day = 0.9856
    
    # Obliczenie okresu orbitalnego
    # T = 2π * sqrt(a^3 / μ), gdzie μ = GM
    earth_gravitational_parameter = 3.986004418e14  # m^3/s^2
    orbital_period_seconds = 2 * pi * np.sqrt(orbital_radius**3 / earth_gravitational_parameter)
    orbital_period_minutes = orbital_period_seconds / 60
    
    # Liczba orbit na dzień
    orbits_per_day = 24 * 60 * 60 / orbital_period_seconds
    
    # Rozdzielczość czasowa powtórzeń (rewizyt) dla danego obszaru
    # Satellite ground track repeat cycle
    repeat_cycle_days = np.ceil(orbits_per_day)  # zaokrąglenie w górę do pełnego dnia
    
    # Obliczenie kąta separacji między kolejnymi orbitami na równiku
    longitude_separation_degrees = 360 / orbits_per_day
    
    results = {
        "orbital_radius_km": orbital_radius / 1000,
        "orbital_period_minutes": orbital_period_minutes,
        "orbits_per_day": orbits_per_day,
        "repeat_cycle_days": repeat_cycle_days,
        "longitude_separation_degrees": longitude_separation_degrees,
        "inclination_degrees": inclination_degrees,
        "nodal_precession_deg_per_day": nodal_precession_deg_per_day
    }
    
    return results

def calculate_imaging_intervals(altitude, swath_width, swath_height, overlap_percent=10, orbital_period_minutes=90):
    """
    Oblicza interwały czasowe i odległościowe między kolejnymi zdjęciami.
    
    Parametry:
    altitude (float): Wysokość orbity w metrach
    swath_width (float): Szerokość pasa pokrycia w metrach
    swath_height (float): Wysokość pokrycia w metrach (w kierunku lotu)
    overlap_percent (float): Procent nakładania się obrazów
    orbital_period_minutes (float): Okres orbitalny w minutach
    
    Zwraca:
    dict: Słownik z obliczonymi interwałami
    """
    # Obliczenia dla pokrycia wzdłuż toru lotu (along-track)
    effective_height = swath_height * (1 - overlap_percent/100)
    
    # Obliczenie prędkości naziemnej satelity
    orbital_radius = EARTH_RADIUS + altitude
    orbital_circumference = 2 * pi * orbital_radius  # obwód orbity w metrach
    orbital_period_seconds = orbital_period_minutes * 60
    satellite_velocity = orbital_circumference / orbital_period_seconds  # m/s
    ground_velocity = satellite_velocity * (EARTH_RADIUS / orbital_radius)  # m/s
    
    # Obliczenie co ile sekund należy wykonać zdjęcie wzdłuż toru lotu
    time_interval_seconds = effective_height / ground_velocity
    
    # Obliczenie co ile metrów należy wykonać zdjęcie wzdłuż toru lotu
    distance_interval_along_track = effective_height
    
    # Obliczenia dla pokrycia w poprzek toru lotu (cross-track)
    effective_width = swath_width * (1 - overlap_percent/100)
    
    # Ile pasów potrzeba, aby pokryć cały równik
    num_strips_equator = np.ceil(EARTH_CIRCUMFERENCE / effective_width)
    
    # Co ile stopni długości geograficznej powinien przechodzić tor orbity
    longitude_interval_degrees = 360 / num_strips_equator
    
    # Co ile metrów na równiku należy wykonać pas zdjęć
    distance_interval_cross_track = EARTH_CIRCUMFERENCE / num_strips_equator
    
    # Ile orbit potrzeba, aby pokryć całą Ziemię
    num_orbits_for_coverage = num_strips_equator / 2  # Zakładając orbitę polarną
    
    # Ile czasu zajmie pełne pokrycie Ziemi (w godzinach)
    time_for_full_coverage_hours = (num_orbits_for_coverage * orbital_period_minutes) / 60
    
    results = {
        "satellite_velocity_km_h": satellite_velocity * 3.6,  # km/h
        "ground_velocity_km_h": ground_velocity * 3.6,  # km/h
        "time_interval_seconds": time_interval_seconds,
        "distance_interval_along_track_km": distance_interval_along_track / 1000,
        "distance_interval_cross_track_km": distance_interval_cross_track / 1000,
        "longitude_interval_degrees": longitude_interval_degrees,
        "num_strips_equator": num_strips_equator,
        "num_orbits_for_coverage": num_orbits_for_coverage,
        "time_for_full_coverage_hours": time_for_full_coverage_hours
    }
    
    return results

def calculate_total_data_volume(resolution, num_images, image_size_mb):
    """
    Oblicza całkowitą ilość danych generowanych w ciągu doby.
    
    Parametry:
    resolution (float): Rozdzielczość przestrzenna w m/px
    num_images (int): Liczba zdjęć potrzebnych do pokrycia Ziemi
    image_size_mb (float): Rozmiar pojedynczego zdjęcia w MB
    
    Zwraca:
    tuple: (całkowita ilość danych w MB, całkowita ilość danych w GB, całkowita ilość danych w TB)
    """
    total_data_mb = num_images * image_size_mb
    total_data_gb = total_data_mb / 1024
    total_data_tb = total_data_gb / 1024
    
    return (total_data_mb, total_data_gb, total_data_tb)

def visualize_imaging_intervals(high_res_intervals, low_res_intervals, sso_intervals):
    """
    Wizualizuje interwały robienia zdjęć dla różnych rozdzielczości i typów orbity.
    
    Parametry:
    high_res_intervals (dict): Wyniki obliczeń interwałów dla wysokiej rozdzielczości
    low_res_intervals (dict): Wyniki obliczeń interwałów dla niskiej rozdzielczości
    sso_intervals (dict): Wyniki obliczeń interwałów dla orbity SSO
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Dane do wykresu odstępów czasowych
    scenarios = [
        'Wysoka rozdzielczość\n(1 m/px)', 
        'Niska rozdzielczość\n(250 m/px)',
        'SSO\n(10 m/px)'
    ]
    time_intervals = [
        high_res_intervals["time_interval_seconds"], 
        low_res_intervals["time_interval_seconds"],
        sso_intervals["time_interval_seconds"]
    ]
    
    bars1 = ax1.bar(scenarios, time_intervals, color=['darkred', 'navy', 'green'])
    ax1.set_ylabel('Interwał czasowy między zdjęciami [s]')
    ax1.set_title('Odstęp czasowy między kolejnymi zdjęciami')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Dodanie etykiet wartości na słupkach
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.2f} s', ha='center', va='bottom', fontweight='bold')
    
    # Dane do wykresu odstępów przestrzennych
    distance_intervals = [
        high_res_intervals["distance_interval_along_track_km"], 
        low_res_intervals["distance_interval_along_track_km"],
        sso_intervals["distance_interval_along_track_km"]
    ]
    
    bars2 = ax2.bar(scenarios, distance_intervals, color=['darkred', 'navy', 'green'])
    ax2.set_ylabel('Odstęp między zdjęciami [km]')
    ax2.set_title('Odstęp przestrzenny między kolejnymi zdjęciami')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Dodanie etykiet wartości na słupkach
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.2f} km', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('interwaly_obrazowania.png', dpi=300, bbox_inches='tight')
    
    return fig

def analyze_resolution_scenario(resolution, altitude, fov_degrees, 
                               sensor_width_mm, sensor_height_mm, 
                               pixel_size_um, num_channels, 
                               satellite_model="Nieokreślony",
                               overlap_percent=10, orbital_period_minutes=90,
                               inclination_degrees=None, ltan=None):
    """
    Przeprowadza pełną analizę scenariusza rozdzielczości.
    
    Parametry:
    resolution (float): Rozdzielczość przestrzenna w m/px
    altitude (float): Wysokość orbity w metrach
    fov_degrees (float): Kąt widzenia w stopniach
    sensor_width_mm (float): Szerokość matrycy w mm
    sensor_height_mm (float): Wysokość matrycy w mm
    pixel_size_um (float): Rozmiar piksela w mikrometrach
    num_channels (int): Liczba kanałów spektralnych
    satellite_model (str): Model użytej satelity
    overlap_percent (float): Procent nakładania się obrazów
    orbital_period_minutes (float): Okres orbitalny w minutach
    inclination_degrees (float): Inklinacja orbity w stopniach (opcjonalne)
    ltan (str): Czas lokalny węzła wstępującego (opcjonalne)
    
    Zwraca:
    dict: Słownik z wynikami analizy
    """
    # Obliczenia pokrycia terenu
    swath_width, swath_height, width_px, height_px = calculate_ground_coverage(
        altitude, fov_degrees, sensor_width_mm, sensor_height_mm, pixel_size_um
    )
    
    # Obliczenia rozmiaru obrazu
    total_pixels, image_size_mb = calculate_image_size(
        resolution, width_px, height_px, num_channels
    )
    
    # Obliczenia liczby obrazów
    num_images = calculate_number_of_images(
        resolution, swath_width, swath_height, overlap_percent
    )
    
    # Obliczenia parametrów orbity SSO jeśli podano inklinację
    if inclination_degrees is not None:
        sso_params = calculate_sso_orbit_parameters(
            altitude, inclination_degrees
        )
        orbital_period_minutes = sso_params["orbital_period_minutes"]
    else:
        sso_params = None
    
    # Obliczenia interwałów obrazowania
    imaging_intervals = calculate_imaging_intervals(
        altitude, swath_width, swath_height, overlap_percent, orbital_period_minutes
    )
    
    # Całkowita ilość danych
    total_data_mb, total_data_gb, total_data_tb = calculate_total_data_volume(
        resolution, num_images, image_size_mb
    )
    
    # Przygotowanie wyników
    results = {
        "satellite_model": satellite_model,
        "resolution": resolution,
        "altitude": altitude,
        "fov_degrees": fov_degrees,
        "sensor_width_mm": sensor_width_mm,
        "sensor_height_mm": sensor_height_mm,
        "pixel_size_um": pixel_size_um,
        "num_channels": num_channels,
        "orbital_period_minutes": orbital_period_minutes,
        "swath_width_km": swath_width / 1000,
        "swath_height_km": swath_height / 1000,
        "image_width_px": width_px,
        "image_height_px": height_px,
        "total_pixels": total_pixels,
        "image_size_mb": image_size_mb,
        "num_images": num_images,
        "total_data_mb": total_data_mb,
        "total_data_gb": total_data_gb,
        "total_data_tb": total_data_tb,
        "imaging_intervals": imaging_intervals,
        "sso_params": sso_params,  # Dodane parametry SSO
        "inclination_degrees": inclination_degrees,  # Dodana inklinacja
        "ltan": ltan  # Dodany LTAN
    }
    
    return results

def visualize_comparison(high_res_results, low_res_results, sso_results):
    """
    Wizualizuje porównanie scenariuszy wysokiej i niskiej rozdzielczości oraz SSO.
    
    Parametry:
    high_res_results (dict): Wyniki analizy scenariusza wysokiej rozdzielczości
    low_res_results (dict): Wyniki analizy scenariusza niskiej rozdzielczości
    sso_results (dict): Wyniki analizy scenariusza dla orbity SSO
    """
    # Dane do wykresu
    scenarios = [
        f"{high_res_results['satellite_model']}\n(1 m/px)", 
        f"{low_res_results['satellite_model']}\n(250 m/px)",
        f"{sso_results['satellite_model']}\n(10 m/px)"
    ]
    data_tb = [
        high_res_results["total_data_tb"], 
        low_res_results["total_data_tb"],
        sso_results["total_data_tb"]
    ]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(scenarios, data_tb, color=['darkred', 'navy', 'green'])
    
    # Dodanie etykiet wartości na słupkach
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.2f} TB', ha='center', va='bottom', fontweight='bold')
    
    ax.set_ylabel('Dzienna ilość danych [TB]')
    ax.set_title('Porównanie dziennej ilości danych dla różnych satelitów i rozdzielczości')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Ustawienie logarytmicznej skali dla osi Y jeśli różnica jest duża
    if max(data_tb) / min(data_tb) > 100:
        ax.set_yscale('log')
        ax.set_ylabel('Dzienna ilość danych [TB] (skala logarytmiczna)')
    
    plt.tight_layout()
    plt.savefig('porownanie_ilosci_danych.png', dpi=300, bbox_inches='tight')
    
    return fig

def visualize_sso_orbits(sso_results):
    """
    Wizualizuje orbity SSO.
    
    Parametry:
    sso_results (dict): Wyniki analizy scenariusza dla orbity SSO
    """
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Rysowanie kuli ziemskiej
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = EARTH_RADIUS * np.outer(np.cos(u), np.sin(v)) / 1000000  # konwersja na tysiące km
    y = EARTH_RADIUS * np.outer(np.sin(u), np.sin(v)) / 1000000
    z = EARTH_RADIUS * np.outer(np.ones(np.size(u)), np.cos(v)) / 1000000
    
    # Przezroczysty glob ziemski
    ax.plot_surface(x, y, z, color='b', alpha=0.1)
    
    # Rysowanie orbity SSO
    orbital_radius = sso_results["sso_params"]["orbital_radius_km"]
    inclination = np.radians(sso_results["inclination_degrees"])
    
    theta = np.linspace(0, 2 * np.pi, 100)
    orbit_x = orbital_radius * np.cos(theta) / 1000  # konwersja na tysiące km
    orbit_y = orbital_radius * np.sin(theta) * np.cos(inclination) / 1000
    orbit_z = orbital_radius * np.sin(theta) * np.sin(inclination) / 1000
    
    ax.plot(orbit_x, orbit_y, orbit_z, 'r-', linewidth=2)
    
    # Rysowanie wektora LTAN (kierunek Słońca)
    if sso_results["ltan"]:
        # Konwersja LTAN (np. 10:30) na kąt
        ltan_parts = sso_results["ltan"].split(":")
        ltan_hours = int(ltan_parts[0])
        ltan_minutes = int(ltan_parts[1]) if len(ltan_parts) > 1 else 0
        ltan_angle = (ltan_hours + ltan_minutes/60) * 15  # 15 stopni na godzinę
        ltan_rad = np.radians(ltan_angle)
        
        # Wektor kierunku Słońca
        sun_x = 1.5 * orbital_radius * np.cos(ltan_rad) / 1000
        sun_y = 1.5 * orbital_radius * np.sin(ltan_rad) / 1000
        sun_z = 0
        
        ax.quiver(0, 0, 0, sun_x, sun_y, sun_z, color='y', arrow_length_ratio=0.1, label='Słońce (LTAN)')
    
    # Ustawienia wykresu
    ax.set_xlabel('X [tysiące km]')
    ax.set_ylabel('Y [tysiące km]')
    ax.set_zlabel('Z [tysiące km]')
    ax.set_title(f'Orbita SSO - {sso_results["satellite_model"]} (wysokość: {sso_results["altitude"]/1000:.0f} km)')
    
    # Legendy i informacje
    info_text = (
        f'Wysokość: {sso_results["altitude"]/1000:.0f} km\n'
        f'Inklinacja: {sso_results["inclination_degrees"]}°\n'
        f'LTAN: {sso_results["ltan"]}\n'
        f'Orbity/dzień: {sso_results["sso_params"]["orbits_per_day"]:.2f}\n'
        f'Okres: {sso_results["sso_params"]["orbital_period_minutes"]:.2f} min'
    )
    plt.figtext(0.02, 0.02, info_text, fontsize=9, bbox=dict(facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('wizualizacja_orbity_sso.png', dpi=300, bbox_inches='tight')
    
    return fig

# Główna funkcja wykonująca wszystkie obliczenia
def main():
    # SCENARIUSZ 1: Wysoka rozdzielczość (1 m/px)
    high_res_params = {
        "satellite_model": "WorldView-4",  # Przykładowa satelita wysokiej rozdzielczości
        "resolution": 1.0,                # 1 m/px
        "altitude": 500000,               # 500 km
        "fov_degrees": 5.0,               # 5 stopni kąta widzenia
        "sensor_width_mm": 36.0,          # szerokość matrycy 36 mm (format pełnoklatkowy)
        "sensor_height_mm": 24.0,         # wysokość matrycy 24 mm
        "pixel_size_um": 5.0,             # rozmiar piksela 5 mikrometrów
        "num_channels": 4,                # 4 kanały (RGB + NIR)
        "overlap_percent": 10,            # 10% nakładania się obrazów
        "orbital_period_minutes": 95,     # okres orbitalny 95 minut
        "inclination_degrees": 98,        # Dodane - inklinacja dla SSO
        "ltan": "10:30"                   # Dodane - czas lokalny węzła wstępującego
    }
    
    # SCENARIUSZ 2: Niska rozdzielczość (250 m/px)
    low_res_params = {
        "satellite_model": "MODIS Terra",  # Przykładowa satelita niskiej rozdzielczości
        "resolution": 250.0,              # 250 m/px
        "altitude": 800000,               # 800 km
        "fov_degrees": 15.0,              # 15 stopni kąta widzenia
        "sensor_width_mm": 30.0,          # szerokość matrycy 30 mm
        "sensor_height_mm": 20.0,         # wysokość matrycy 20 mm
        "pixel_size_um": 20.0,            # rozmiar piksela 20 mikrometrów
        "num_channels": 7,                # 7 kanałów (wielospektralne)
        "overlap_percent": 5,             # 5% nakładania się obrazów
        "orbital_period_minutes": 100,    # okres orbitalny 100 minut
        "inclination_degrees": 98,        # Dodane - inklinacja dla SSO
        "ltan": "10:30"                   # Dodane - czas lokalny węzła wstępującego
    }
    
    # SCENARIUSZ 3: Kamień Milowy 1 - Orbita SSO (10 m/px)
    sso_params = {
        "satellite_model": "Sentinel-2",   # Przykładowa satelita z orbitą SSO
        "resolution": 10.0,               # 10 m/px (typowa dla Sentinel-2)
        "altitude": 700000,               # 700 km (zgodnie z kamieniem milowym)
        "fov_degrees": 10.0,              # 10 stopni kąta widzenia (przykładowe)
        "sensor_width_mm": 35.0,          # przykładowe wartości
        "sensor_height_mm": 23.0,
        "pixel_size_um": 7.0,             # przykładowa wartość
        "num_channels": 13,               # 13 kanałów (wielospektralne)
        "overlap_percent": 10,
        "inclination_degrees": 98,        # zgodnie z kamieniem milowym
        "ltan": "10:30"                   # zgodnie z kamieniem milowym
    }
    
    # Analiza scenariuszy
    high_res_results = analyze_resolution_scenario(**high_res_params)
    low_res_results = analyze_resolution_scenario(**low_res_params)
    sso_results = analyze_resolution_scenario(**sso_params)
    
    # Wizualizacja porównania ilości danych
    data_fig = visualize_comparison(high_res_results, low_res_results, sso_results)
    
    # Wizualizacja porównania interwałów obrazowania
    intervals_fig = visualize_imaging_intervals(
        high_res_results["imaging_intervals"], 
        low_res_results["imaging_intervals"],
        sso_results["imaging_intervals"]
    )
    
    # Wizualizacja orbit SSO dla wszystkich trzech scenariuszy
    high_res_orbit_fig = visualize_sso_orbits(high_res_results)
    low_res_orbit_fig = visualize_sso_orbits(low_res_results)
    sso_orbit_fig = visualize_sso_orbits(sso_results)
    
    # Wydrukowanie podsumowania w formie raportu
    print("RAPORT Z ANALIZY PARAMETRÓW OBRAZOWANIA SATELITARNEGO\n")
    print(f"1. SCENARIUSZ WYSOKIEJ ROZDZIELCZOŚCI (1 m/px) - SATELITA: {high_res_results['satellite_model']}")
    print(f"   Wysokość orbity: {high_res_results['altitude']/1000:.0f} km")
    print(f"   Typ orbity: Heliosynchroniczna (SSO)")
    print(f"   Inklinacja: {high_res_results['inclination_degrees']}°")
    print(f"   LTAN: {high_res_results['ltan']}")
    print(f"   Rozmiar pojedynczego obrazu: {high_res_results['image_size_mb']:.2f} MB")
    print(f"   Pokrycie terenu (szerokość x wysokość): {high_res_results['swath_width_km']:.2f} x {high_res_results['swath_height_km']:.2f} km")
    print(f"   Wymiary obrazu: {high_res_results['image_width_px']} x {high_res_results['image_height_px']} pikseli")
    print(f"   Liczba kanałów spektralnych: {high_res_results['num_channels']}")
    print(f"   Liczba zdjęć na pokrycie całej Ziemi: {high_res_results['num_images']:,}")
    print(f"   Całkowita ilość danych: {high_res_results['total_data_tb']:.2f} TB")
    print(f"   Interwał czasowy między zdjęciami: {high_res_results['imaging_intervals']['time_interval_seconds']:.2f} s")
    print(f"   Czas na pełne pokrycie Ziemi: {high_res_results['imaging_intervals']['time_for_full_coverage_hours']:.2f} godzin")
    print(f"   Okres orbitalny: {high_res_results['orbital_period_minutes']:.2f} minut")
    print(f"   Liczba orbit na dzień: {high_res_results['sso_params']['orbits_per_day']:.2f}")
    print()
    
    print(f"2. SCENARIUSZ NISKIEJ ROZDZIELCZOŚCI (250 m/px) - SATELITA: {low_res_results['satellite_model']}")
    print(f"   Wysokość orbity: {low_res_results['altitude']/1000:.0f} km")
    print(f"   Typ orbity: Heliosynchroniczna (SSO)")
    print(f"   Inklinacja: {low_res_results['inclination_degrees']}°")
    print(f"   LTAN: {low_res_results['ltan']}")
    print(f"   Rozmiar pojedynczego obrazu: {low_res_results['image_size_mb']:.2f} MB")
    print(f"   Pokrycie terenu (szerokość x wysokość): {low_res_results['swath_width_km']:.2f} x {low_res_results['swath_height_km']:.2f} km")
    print(f"   Wymiary obrazu: {low_res_results['image_width_px']} x {low_res_results['image_height_px']} pikseli")
    print(f"   Liczba kanałów spektralnych: {low_res_results['num_channels']}")
    print(f"   Liczba zdjęć na pokrycie całej Ziemi: {low_res_results['num_images']:,}")
    print(f"   Całkowita ilość danych: {low_res_results['total_data_tb']:.2f} TB")
    print(f"   Interwał czasowy między zdjęciami: {low_res_results['imaging_intervals']['time_interval_seconds']:.2f} s")
    print(f"   Czas na pełne pokrycie Ziemi: {low_res_results['imaging_intervals']['time_for_full_coverage_hours']:.2f} godzin")
    print(f"   Okres orbitalny: {low_res_results['orbital_period_minutes']:.2f} minut")
    print(f"   Liczba orbit na dzień: {low_res_results['sso_params']['orbits_per_day']:.2f}")
    print()
    
    print(f"3. SCENARIUSZ ORBITY SSO (10 m/px) - SATELITA: {sso_results['satellite_model']}")
    print(f"   Wysokość orbity: {sso_results['altitude']/1000:.0f} km")
    print(f"   Typ orbity: Heliosynchroniczna (SSO)")
    print(f"   Inklinacja: {sso_results['inclination_degrees']}°")
    print(f"   LTAN: {sso_results['ltan']}")
    print(f"   Rozmiar pojedynczego obrazu: {sso_results['image_size_mb']:.2f} MB")
    print(f"   Pokrycie terenu (szerokość x wysokość): {sso_results['swath_width_km']:.2f} x {sso_results['swath_height_km']:.2f} km")
    print(f"   Wymiary obrazu: {sso_results['image_width_px']} x {sso_results['image_height_px']} pikseli")
    print(f"   Liczba kanałów spektralnych: {sso_results['num_channels']}")
    print(f"   Liczba zdjęć na pokrycie całej Ziemi: {sso_results['num_images']:,}")
    print(f"   Całkowita ilość danych: {sso_results['total_data_tb']:.2f} TB")
    print(f"   Interwał czasowy między zdjęciami: {sso_results['imaging_intervals']['time_interval_seconds']:.2f} s")
    print(f"   Czas na pełne pokrycie Ziemi: {sso_results['imaging_intervals']['time_for_full_coverage_hours']:.2f} godzin")
    print(f"   Okres orbitalny: {sso_results['orbital_period_minutes']:.2f} minut")
    print(f"   Liczba orbit na dzień: {sso_results['sso_params']['orbits_per_day']:.2f}")
    print()
    
    print("PODSUMOWANIE I WNIOSKI:")
    print(f"1. Satelita wysokiej rozdzielczości ({high_res_results['resolution']} m/px) generuje {high_res_results['total_data_tb']:.2f} TB danych dziennie.")
    print(f"2. Satelita niskiej rozdzielczości ({low_res_results['resolution']} m/px) generuje {low_res_results['total_data_tb']:.2f} TB danych dziennie.")
    print(f"3. Satelita na orbicie SSO ({sso_results['resolution']} m/px) generuje {sso_results['total_data_tb']:.2f} TB danych dziennie.")
    print(f"4. Stosunek ilości danych wysokiej do niskiej rozdzielczości: {high_res_results['total_data_tb']/low_res_results['total_data_tb']:.2f}x")
    print(f"5. Dla pełnego pokrycia Ziemi potrzeba odpowiednio: {high_res_results['imaging_intervals']['time_for_full_coverage_hours']:.2f}, {low_res_results['imaging_intervals']['time_for_full_coverage_hours']:.2f} i {sso_results['imaging_intervals']['time_for_full_coverage_hours']:.2f} godzin.")
    
    print("\nWygenerowane wykresy zostały zapisane jako:")
    print("- porownanie_ilosci_danych.png")
    print("- interwaly_obrazowania.png")
    print("- wizualizacja_orbity_sso.png")
    
    # Dodanie wywołania funkcji main() na końcu pliku
if __name__ == "__main__":
    main()