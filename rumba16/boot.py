def extend_bootinfo(bootinfo):
    # Arahkan tiap user ke workspace pertama yang boleh ia lihat (per-role),
    # bukan halaman "desktop" legacy.
    skip = {"Buying", "Welcome Workspace"}
    for w in (bootinfo.get("allowed_workspaces") or []):
        name = w.get("name") or ""
        if name in skip or "&" in name:
            continue
        bootinfo.home_page = name
        break
