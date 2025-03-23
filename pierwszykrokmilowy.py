import numpy as np
import matplotlib.pyplot as plt
from math import pi, cos, radians

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

def visualize_imaging_intervals(high_res_intervals, low_res_intervals):
    """
    Wizualizuje interwały robienia zdjęć dla różnych rozdzielczości.
    
    Parametry:
    high_res_intervals (dict): Wyniki obliczeń interwałów dla wysokiej rozdzielczości
    low_res_intervals (dict): Wyniki obliczeń interwałów dla niskiej rozdzielczości
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Dane do wykresu odstępów czasowych
    scenarios = ['Wysoka rozdzielczość\n(1 m/px)', 'Niska rozdzielczość\n(250 m/px)']
    time_intervals = [high_res_intervals["time_interval_seconds"], low_res_intervals["time_interval_seconds"]]
    
    bars1 = ax1.bar(scenarios, time_intervals, color=['darkred', 'navy'])
    ax1.set_ylabel('Interwał czasowy między zdjęciami [s]')
    ax1.set_title('Odstęp czasowy między kolejnymi zdjęciami')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Dodanie etykiet wartości na słupkach
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.2f} s', ha='center', va='bottom', fontweight='bold')
    
    # Dane do wykresu odstępów przestrzennych
    distance_intervals = [high_res_intervals["distance_interval_along_track_km"], 
                         low_res_intervals["distance_interval_along_track_km"]]
    
    bars2 = ax2.bar(scenarios, distance_intervals, color=['darkred', 'navy'])
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
                               satellite_model="Nieokreślony", # Dodany parametr modelu satelity
                               overlap_percent=10, orbital_period_minutes=90):
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
        "satellite_model": satellite_model,  # Dodanie modelu satelity do wyników
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
        "imaging_intervals": imaging_intervals
    }
    
    return results

def visualize_comparison(high_res_results, low_res_results):
    """
    Wizualizuje porównanie scenariuszy wysokiej i niskiej rozdzielczości.
    
    Parametry:
    high_res_results (dict): Wyniki analizy scenariusza wysokiej rozdzielczości
    low_res_results (dict): Wyniki analizy scenariusza niskiej rozdzielczości
    """
    # Dane do wykresu
    scenarios = [f"{high_res_results['satellite_model']}\n(1 m/px)", 
                f"{low_res_results['satellite_model']}\n(250 m/px)"]
    data_tb = [high_res_results["total_data_tb"], low_res_results["total_data_tb"]]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(scenarios, data_tb, color=['darkred', 'navy'])
    
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
        "orbital_period_minutes": 95      # okres orbitalny 95 minut
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
        "orbital_period_minutes": 100     # okres orbitalny 100 minut
    }
    
    # Analiza scenariuszy
    high_res_results = analyze_resolution_scenario(**high_res_params)
    low_res_results = analyze_resolution_scenario(**low_res_params)
    
    # Wizualizacja porównania ilości danych
    data_fig = visualize_comparison(high_res_results, low_res_results)
    
    # Wizualizacja porównania interwałów obrazowania
    intervals_fig = visualize_imaging_intervals(
        high_res_results["imaging_intervals"], 
        low_res_results["imaging_intervals"]
    )
    
    # Wydrukowanie podsumowania w formie raportu
    print("RAPORT Z ANALIZY PARAMETRÓW OBRAZOWANIA SATELITARNEGO\n")
    print(f"1. SCENARIUSZ WYSOKIEJ ROZDZIELCZOŚCI (1 m/px) - SATELITA: {high_res_results['satellite_model']}")
    print(f"   Wysokość orbity: {high_res_results['altitude']/1000:.0f} km")
    print(f"   Kąt widzenia: {high_res_results['fov_degrees']:.1f}°")
    print(f"   Rozmiar matrycy: {high_res_results['sensor_width_mm']:.1f} x {high_res_results['sensor_height_mm']:.1f} mm")
    print(f"   Rozmiar piksela: {high_res_results['pixel_size_um']:.1f} µm")
    print(f"   Liczba kanałów spektralnych: {high_res_results['num_channels']}")
    print(f"   Obszar pokrycia pojedynczego zdjęcia: {high_res_results['swath_width_km']:.2f} x {high_res_results['swath_height_km']:.2f} km")
    print(f"   Rozdzielczość zdjęcia: {high_res_results['image_width_px']} x {high_res_results['image_height_px']} pikseli")
    print(f"   Rozmiar pojedynczego zdjęcia: {high_res_results['image_size_mb']:.2f} MB")
    print(f"   Liczba zdjęć do pokrycia Ziemi: {high_res_results['num_images']}")
    print(f"   Całkowita dzienna ilość danych: {high_res_results['total_data_tb']:.2f} TB")
    print("\n   INTERWAŁY OBRAZOWANIA:")
    print(f"   Prędkość naziemna: {high_res_results['imaging_intervals']['ground_velocity_km_h']:.2f} km/h")
    print(f"   Odstęp czasowy między zdjęciami: {high_res_results['imaging_intervals']['time_interval_seconds']:.2f} s")
    print(f"   Odstęp przestrzenny wzdłuż toru lotu: {high_res_results['imaging_intervals']['distance_interval_along_track_km']:.2f} km")
    print(f"   Odstęp przestrzenny między pasami: {high_res_results['imaging_intervals']['distance_interval_cross_track_km']:.2f} km")
    print(f"   Liczba pasów potrzebna do pokrycia równika: {high_res_results['imaging_intervals']['num_strips_equator']:.0f}")
    print(f"   Liczba orbit potrzebna do pełnego pokrycia: {high_res_results['imaging_intervals']['num_orbits_for_coverage']:.2f}")
    print(f"   Czas potrzebny na pełne pokrycie: {high_res_results['imaging_intervals']['time_for_full_coverage_hours']:.2f} h")
    
    print(f"\n2. SCENARIUSZ NISKIEJ ROZDZIELCZOŚCI (250 m/px) - SATELITA: {low_res_results['satellite_model']}")
    print(f"   Wysokość orbity: {low_res_results['altitude']/1000:.0f} km")
    print(f"   Kąt widzenia: {low_res_results['fov_degrees']:.1f}°")
    print(f"   Rozmiar matrycy: {low_res_results['sensor_width_mm']:.1f} x {low_res_results['sensor_height_mm']:.1f} mm")
    print(f"   Rozmiar piksela: {low_res_results['pixel_size_um']:.1f} µm")
    print(f"   Liczba kanałów spektralnych: {low_res_results['num_channels']}")
    print(f"   Obszar pokrycia pojedynczego zdjęcia: {low_res_results['swath_width_km']:.2f} x {low_res_results['swath_height_km']:.2f} km")
    print(f"   Rozdzielczość zdjęcia: {low_res_results['image_width_px']} x {low_res_results['image_height_px']} pikseli")
    print(f"   Rozmiar pojedynczego zdjęcia: {low_res_results['image_size_mb']:.2f} MB")
    print(f"   Liczba zdjęć do pokrycia Ziemi: {low_res_results['num_images']}")
    print(f"   Całkowita dzienna ilość danych: {low_res_results['total_data_tb']:.2f} TB")
    print("\n   INTERWAŁY OBRAZOWANIA:")
    print(f"   Prędkość naziemna: {low_res_results['imaging_intervals']['ground_velocity_km_h']:.2f} km/h")
    print(f"   Odstęp czasowy między zdjęciami: {low_res_results['imaging_intervals']['time_interval_seconds']:.2f} s")
    print(f"   Odstęp przestrzenny wzdłuż toru lotu: {low_res_results['imaging_intervals']['distance_interval_along_track_km']:.2f} km")
    print(f"   Odstęp przestrzenny między pasami: {low_res_results['imaging_intervals']['distance_interval_cross_track_km']:.2f} km")
    print(f"   Liczba pasów potrzebna do pokrycia równika: {low_res_results['imaging_intervals']['num_strips_equator']:.0f}")
    print(f"   Liczba orbit potrzebna do pełnego pokrycia: {low_res_results['imaging_intervals']['num_orbits_for_coverage']:.2f}")
    print(f"   Czas potrzebny na pełne pokrycie: {low_res_results['imaging_intervals']['time_for_full_coverage_hours']:.2f} h")
    
    print("\nPODSUMOWANIE DLA ZESPOŁÓW KOMUNIKACYJNYCH:")
    print(f"Satelita wysoka rozdzielczość: {high_res_results['satellite_model']}")
    print(f"Satelita niska rozdzielczość: {low_res_results['satellite_model']}")
    print(f"Dzienna ilość danych - {high_res_results['satellite_model']} (1 m/px): {high_res_results['total_data_tb']:.2f} TB")
    print(f"Dzienna ilość danych - {low_res_results['satellite_model']} (250 m/px): {low_res_results['total_data_tb']:.2f} TB")
    print(f"Odstęp między zdjęciami - {high_res_results['satellite_model']}: {high_res_results['imaging_intervals']['distance_interval_along_track_km']:.2f} km")
    print(f"Odstęp między zdjęciami - {low_res_results['satellite_model']}: {low_res_results['imaging_intervals']['distance_interval_along_track_km']:.2f} km")
    
    return high_res_results, low_res_results, data_fig, intervals_fig

if __name__ == "__main__":
    high_res_results, low_res_results, data_fig, intervals_fig = main()