// rumba_desk_landing.js — ERP-WS-004 (Landing Per-Role, lapis desk /app)
// ---------------------------------------------------------------------------
// Masalah: `hooks.role_home_page` hanya mengatur rute WEBSITE/pasca-login,
// bukan default desk. Saat pengguna Rumba membuka `/app` polos, ERPNext
// membuka workspace standar ("Stock"). Skrip ini memantulkan pengguna Rumba
// (BUKAN System Manager) yang mendarat di workspace NON-Rumba kembali ke
// `/masuk`, yang lalu me-redirect per-peran (Tutor -> /app/tutor, dst).
//
// Bersifat ROLE-AGNOSTIK: tujuan per-peran ada di `www/masuk.py`, bukan di
// sini. Skrip ini hanya mengenali "mana workspace Rumba" via module, sehingga
// workspace Tutor beserta sub-menunya (Rombel & Sesi Saya, Akademik Saya,
// Izin & Guru Pengganti) — semuanya module "Bimbel Rumba v16" — otomatis
// dianggap Rumba tanpa perlu daftar hardcode.
//
// PEMASANGAN (server):
//   1) taruh file di: apps/rumba16/rumba16/public/js/rumba_desk_landing.js
//   2) hooks.py:  app_include_js = ["/assets/rumba16/js/rumba_desk_landing.js"]
//   3) bench build --app rumba16 && bench --site <site> clear-cache && bench restart
//   4) uji akun tutor: buka /app polos -> mendarat di /app/tutor (bukan Stock);
//      buka /app/tutor langsung -> TIDAK ada pantulan.
// ---------------------------------------------------------------------------

(function () {
  "use strict";

  var RUMBA_MODULE = "Bimbel Rumba v16"; // module penampung semua workspace Rumba
  var SS_KEY = "rumba_desk_landing_hops"; // penghitung anti-loop per sesi tab
  var MAX_HOPS = 2; // pantulan maksimal per sesi (cegah loop bila salah konfigurasi)
  var MASUK_URL = "/masuk"; // rute www/masuk.py yang memetakan peran -> workspace

  // Daftar SLUG workspace Rumba dari boot (mis. ["rumba","operasional","tutor",
  // "rombel-&-sesi-saya", ...]). '&' dipertahankan oleh frappe.router.slug.
  function rumbaWorkspaceSlugs() {
    try {
      var mww = (frappe.boot && frappe.boot.module_wise_workspaces) || {};
      var list = mww[RUMBA_MODULE] || [];
      return list.map(function (w) {
        return frappe.router.slug(w);
      });
    } catch (e) {
      return [];
    }
  }

  // Pengguna Rumba non-admin. System Manager & Administrator dibebaskan
  // (boleh ke semua workspace, termasuk saat build/debug).
  function isRumbaUser() {
    var roles = frappe.user_roles || [];
    if (frappe.session.user === "Administrator") return false;
    if (roles.indexOf("System Manager") !== -1) return false;
    return roles.some(function (r) {
      return r.indexOf("Rumba ") === 0; // prefix role Rumba (mis. "Rumba Tutor")
    });
  }

  // Slug workspace tempat pengguna sekarang berada, atau null jika bukan
  // halaman workspace (form/list/report -> jangan diganggu).
  function currentWorkspaceSlug() {
    var route = (frappe.get_route && frappe.get_route()) || [];
    var head = (route[0] || "").toLowerCase();
    if ((head === "workspaces" || head === "workspace") && route[1]) {
      return frappe.router.slug(route[1]);
    }
    return null;
  }

  function maybeRedirect() {
    if (!isRumbaUser()) return;

    var slug = currentWorkspaceSlug();
    if (!slug) return; // bukan halaman workspace

    var rumbaSlugs = rumbaWorkspaceSlugs();
    if (!rumbaSlugs.length) return; // boot belum lengkap -> jangan ambil risiko

    if (rumbaSlugs.indexOf(slug) !== -1) {
      // sudah di workspace Rumba (mis. "tutor") -> sukses, reset penghitung
      try { sessionStorage.removeItem(SS_KEY); } catch (e) {}
      return;
    }

    // mendarat di workspace NON-Rumba (mis. "stock") -> pantulkan ke /masuk
    var hops = 0;
    try { hops = parseInt(sessionStorage.getItem(SS_KEY) || "0", 10) || 0; } catch (e) {}
    if (hops >= MAX_HOPS) return; // anti-loop
    try { sessionStorage.setItem(SS_KEY, String(hops + 1)); } catch (e) {}
    window.location.href = MASUK_URL;
  }

  // Inisialisasi: tunggu boot + router matang, evaluasi landing awal, dan
  // tangani resolusi rute PERTAMA (bare /app -> default workspace).
  function init() {
    if (!(window.frappe && frappe.boot && frappe.get_route &&
          frappe.router && frappe.router.slug)) {
      return setTimeout(init, 200);
    }
    // landing awal
    setTimeout(maybeRedirect, 0);
    // resolusi rute pertama (sekali saja)
    var handled = false;
    try {
      frappe.router.on("change", function () {
        if (handled) return;
        handled = true;
        maybeRedirect();
      });
    } catch (e) {
      setTimeout(maybeRedirect, 300);
    }
  }

  init();
})();
