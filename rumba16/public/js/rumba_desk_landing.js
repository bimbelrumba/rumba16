// rumba_desk_landing.js — ERP-WS-004 (Landing Per-Role, lapis desk /app)
// ---------------------------------------------------------------------------
// Masalah #1 (lama): `hooks.role_home_page` hanya mengatur rute WEBSITE/
// pasca-login, bukan default desk. Saat pengguna Rumba membuka `/app` polos,
// ERPNext membuka workspace standar ("Stock"). Skrip ini memantulkan
// pengguna Rumba (BUKAN System Manager) yang mendarat di workspace
// NON-Rumba kembali ke `/masuk`, yang lalu me-redirect per-peran
// (Tutor -> /app/tutor, dst).
//
// Masalah #2 (ditemukan 6 Agu 2026): ERPNext juga otomatis MENGINGAT
// "workspace terakhir yang dibuka" — via localStorage `current_workspace`
// (per-browser, TIDAK terikat ke user/session) dan/atau field
// `default_workspace` di User doctype — lalu memakainya lagi saat `/app`
// dibuka polos, LEPAS dari siapa yang sedang login. Karena cek lama di
// bawah cuma menanyakan "apakah workspace ini SALAH SATU milik Rumba",
// bukan "apakah ini BENAR untuk user yang login SEKARANG", user yang
// ganti akun/role di browser yang sama bisa "mewarisi" workspace milik
// role sebelumnya (mis. login SDM tapi masih mendarat di workspace Tutor
// sisa sesi lama) — karena "tutor" tetap lolos cek "salah satu milik
// Rumba", padahal salah untuk user yang baru ini.
//
// FIX #2: skrip sekarang membedakan permintaan URL AWAL (persis saat
// halaman dimuat, ditangkap sebelum Frappe boot/router sempat berjalan):
//   - URL awal SPESIFIK (mis. "/app/tutor", hasil redirect eksplisit dari
//     masuk.py, atau klik link workspace tertentu) -> dipercaya apa
//     adanya (perilaku lama untuk kasus ini dipertahankan — tetap
//     dipantulkan kalau ternyata bukan workspace Rumba sama sekali,
//     mis. "stock").
//   - URL awal POLOS ("/app" atau "/app/", tanpa nama workspace) -> JANGAN
//     percaya workspace apa pun yang dipilih ERPNext sendiri (localStorage/
//     default_workspace bisa basi) — SELALU pantulkan ke `/masuk` supaya
//     `www/masuk.py` yang memutuskan berdasarkan role user yang login
//     SEKARANG, bukan cache lama.
//
// FIX #2b (dikoreksi 6 Agu 2026 setelah uji live di dev.bimbelrumba.id):
// versi pertama FIX #2 di atas MASIH mensyaratkan currentWorkspaceSlug()
// mengembalikan sebuah slug (route berbentuk ["workspaces", nama]) sebelum
// mau memutuskan apa pun. Di live test, `/app` polos ternyata TIDAK
// mendarat di workspace lain (Stock dsb) tapi malah TOTAL BLANK — karena
// workspace fallback bawaan sudah disembunyikan (is_hidden) oleh
// perubahan lain di server, ERPNext tidak berhasil memilih workspace
// default SAMA SEKALI, dan `frappe.get_route()` tetap `[""]` (kosong).
// Akibatnya syarat "harus ada slug dulu" itu tidak pernah terpenuhi, dan
// skrip tidak pernah memantulkan ke /masuk. FIX #2b memindahkan
// keputusan "URL awal polos -> selalu pantulkan" ke PALING AWAL, SEBELUM
// syarat slug apa pun — jadi kasus blank total pun tetap tertangani.
//
// Bersifat ROLE-AGNOSTIK: tujuan per-peran tetap hanya ada di
// `www/masuk.py` — skrip ini tidak menduplikasi peta role->workspace.
//
// PEMASANGAN (server):
//   1) taruh file di: apps/rumba16/rumba16/public/js/rumba_desk_landing.js
//   2) hooks.py:  app_include_js = ["/assets/rumba16/js/rumba_desk_landing.js"]
//   3) bench build --app rumba16 && bench --site <site> clear-cache && bench restart
//   4) uji akun tutor: buka /app polos -> mendarat di /app/tutor (bukan Stock/blank);
//      buka /app/tutor langsung -> TIDAK ada pantulan.
//   5) uji BARU: di browser SAMA (bukan incognito) logout dari Tutor -> login
//      role lain (mis. SDM) -> buka /app polos -> HARUS mendarat di /app/sdm,
//      BUKAN tersisa di workspace Tutor / BUKAN blank.
// ---------------------------------------------------------------------------

(function () {
  "use strict";

  var RUMBA_MODULE = "Bimbel Rumba v16"; // module penampung semua workspace Rumba
  var SS_KEY = "rumba_desk_landing_hops"; // penghitung anti-loop per sesi tab
  var MAX_HOPS = 2; // pantulan maksimal per sesi (cegah loop bila salah konfigurasi)
  var MASUK_URL = "/masuk"; // rute www/masuk.py yang memetakan peran -> workspace

  // Ditangkap SEKALI di sini, saat script dievaluasi (di <head>, sebelum
  // frappe boot/router jalan) -> merekam persis apa yang diminta browser,
  // bukan hasil olahan client-side yang mungkin sudah "diam-diam" diganti
  // ERPNext ke workspace default/cache.
  var INITIAL_APP_SLUG = (function () {
    try {
      var m = (window.location.pathname || "").match(/^\/app\/([^\/?#]+)/i);
      return m ? m[1] : null; // null = URL awal polos ("/app" atau "/app/")
    } catch (e) {
      return null;
    }
  })();

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

  function bounceToMasuk() {
    var hops = 0;
    try { hops = parseInt(sessionStorage.getItem(SS_KEY) || "0", 10) || 0; } catch (e) {}
    if (hops >= MAX_HOPS) return; // anti-loop
    try { sessionStorage.setItem(SS_KEY, String(hops + 1)); } catch (e) {}
    window.location.href = MASUK_URL;
  }

  function maybeRedirect() {
    if (!isRumbaUser()) return;

    if (!INITIAL_APP_SLUG) {
      // URL awal POLOS ("/app" atau "/app/") -> DIPUTUSKAN DI SINI, PALING
      // AWAL, TANPA syarat slug apa pun. Apa pun yang ditampilkan ERPNext
      // sekarang (workspace lain yang kebetulan "milik Rumba" sisa sesi
      // sebelumnya, workspace non-Rumba, ATAU blank total karena tidak
      // berhasil memilih default sama sekali) TIDAK dipercaya — selalu
      // pantulkan ke /masuk supaya role user yang login SEKARANG yang
      // menentukan, bukan cache/kegagalan pilih default.
      bounceToMasuk();
      return;
    }

    // URL awal SUDAH menyebut workspace spesifik (redirect eksplisit dari
    // masuk.py, atau navigasi/klik eksplisit) -> percayai, kecuali ternyata
    // mendarat di workspace non-Rumba (mis. "stock").
    var slug = currentWorkspaceSlug();
    if (!slug) return; // bukan halaman workspace (form/list/report) -> jangan diganggu

    var rumbaSlugs = rumbaWorkspaceSlugs();
    if (!rumbaSlugs.length) return; // boot belum lengkap -> jangan ambil risiko

    if (rumbaSlugs.indexOf(slug) !== -1) {
      try { sessionStorage.removeItem(SS_KEY); } catch (e) {}
      return;
    }
    bounceToMasuk();
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
