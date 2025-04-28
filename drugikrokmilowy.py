# Kamien Milowy 2: Adaptacja i optymalizacja obrazowania

import numpy as np
import matplotlib.pyplot as plt

# Funkcje pomocnicze

def adjust_acquisition_frequency(original_num_images, orbit_frequency_factor=1):
    return int(np.ceil(original_num_images / orbit_frequency_factor))

def simulate_hybrid_acquisition_with_terrain_and_daylight(high_res_data_gb, low_res_data_gb,
                                                           urban_area_percent=10, other_land_area_percent=30,
                                                           ocean_area_percent=60,
                                                           compression_ratio_high_res=2,
                                                           compression_ratio_low_res=10,
                                                           daylight_fraction=0.5):
    compressed_urban_data = (high_res_data_gb * (urban_area_percent / 100)) / compression_ratio_high_res
    compressed_land_data = (low_res_data_gb * (other_land_area_percent / 100)) / compression_ratio_low_res
    compressed_ocean_data = (low_res_data_gb * (ocean_area_percent / 100)) / (compression_ratio_low_res * 2)

    total_data_gb = (compressed_urban_data + compressed_land_data + compressed_ocean_data) * daylight_fraction
    return total_data_gb

def check_transmission_limit(data_volume_gb, daily_limit_gb):
    return data_volume_gb <= daily_limit_gb

def plot_compression_effects(original_data_gb, compression_ratios):
    compressed_data = [original_data_gb / ratio for ratio in compression_ratios]

    plt.figure(figsize=(8,6))
    plt.plot(compression_ratios, compressed_data, marker='o')
    plt.xlabel('Współczynnik kompresji (np. 2 = 2:1)')
    plt.ylabel('Objętość danych po kompresji [GB]')
    plt.title('Wpływ kompresji na objętość danych')
    plt.grid(True)
    plt.savefig('compression_effects.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_scenarios(scenarios, volumes_gb):
    plt.figure(figsize=(10,6))
    bars = plt.bar(scenarios, volumes_gb)
    plt.ylabel('Objętość danych [GB]')
    plt.title('Porównanie objętości danych dla różnych wariantów')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 1, f'{height:.1f} GB', ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    plt.savefig('scenarios_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

# Główna symulacja

def main():
    data_rate_500km_mbps = 13796.3
    data_rate_700km_mbps = 2685.19
    data_rate_800km_mbps = 40.74

    gb_per_day_500km = data_rate_500km_mbps * 0.125 * 86400 / 1024
    gb_per_day_700km = data_rate_700km_mbps * 0.125 * 86400 / 1024
    gb_per_day_800km = data_rate_800km_mbps * 0.125 * 86400 / 1024

    daily_limit_500km = 32 * 750 * 86400 / (1024*1024)
    daily_limit_700km = 24 * 750 * 86400 / (1024*1024)
    daily_limit_800km = 8 * 750 * 86400 / (1024*1024)

    print(f"Szacowana dzienna objętość danych:")
    print(f"500 km: {gb_per_day_500km:.2f} GB")
    print(f"700 km: {gb_per_day_700km:.2f} GB")
    print(f"800 km: {gb_per_day_800km:.2f} GB\n")

    print(f"Limity dzienne transmisji:\n")
    print(f"500 km: {daily_limit_500km:.2f} GB")
    print(f"700 km: {daily_limit_700km:.2f} GB")
    print(f"800 km: {daily_limit_800km:.2f} GB\n")

    high_res_full_data_gb = gb_per_day_500km
    low_res_full_data_gb = gb_per_day_700km

    # Warianty
    min_data_gb = simulate_hybrid_acquisition_with_terrain_and_daylight(
        high_res_data_gb=0,
        low_res_data_gb=low_res_full_data_gb,
        urban_area_percent=0,
        other_land_area_percent=30,
        ocean_area_percent=70,
        compression_ratio_high_res=2,
        compression_ratio_low_res=20,
        daylight_fraction=0.5
    )
    min_data_gb = adjust_acquisition_frequency(min_data_gb, orbit_frequency_factor=5)

    careful_data_gb = simulate_hybrid_acquisition_with_terrain_and_daylight(
        high_res_data_gb=high_res_full_data_gb,
        low_res_data_gb=low_res_full_data_gb,
        urban_area_percent=5,
        other_land_area_percent=30,
        ocean_area_percent=65,
        compression_ratio_high_res=5,
        compression_ratio_low_res=10,
        daylight_fraction=0.5
    )
    careful_data_gb = adjust_acquisition_frequency(careful_data_gb, orbit_frequency_factor=4)

    balanced_data_gb = simulate_hybrid_acquisition_with_terrain_and_daylight(
        high_res_data_gb=high_res_full_data_gb,
        low_res_data_gb=low_res_full_data_gb,
        urban_area_percent=10,
        other_land_area_percent=30,
        ocean_area_percent=60,
        compression_ratio_high_res=2,
        compression_ratio_low_res=4,
        daylight_fraction=0.5
    )
    balanced_data_gb = adjust_acquisition_frequency(balanced_data_gb, orbit_frequency_factor=3)

    scenarios = ['Minimalny', 'Ostrożny', 'Zrównoważony']
    volumes = [min_data_gb, careful_data_gb, balanced_data_gb]

    print("WYNIKI SYMULACJI:\n")
    for s, v in zip(scenarios, volumes):
        fits = check_transmission_limit(v, daily_limit_500km)
        print(f"Wariant {s}: {v:.2f} GB/dziennie --> {'OK' if fits else 'PRZEKROCZENIE'}")

    plot_scenarios(scenarios, volumes)

if __name__ == "__main__":
    main()