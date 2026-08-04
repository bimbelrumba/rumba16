def extend_bootinfo(bootinfo):
    # Arahkan tiap user ke workspace pertama yang boleh ia lihat & bisa dibuka
    # (per-role), sebagai slug rute — menggantikan halaman "desktop" legacy.
    bootinfo.home_page = ""
