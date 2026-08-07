// rumba_login_no_redirect.js — cegah Frappe mendarat ke halaman LAMA sesudah
// login, lewat parameter `redirect-to` di URL /login.
// ---------------------------------------------------------------------------
// MASALAH (ditemukan 6 Agu 2026, dikonfirmasi dari source resmi Frappe):
// setiap kali sesi berakhir — baik lewat tombol "Log out" di desk, maupun
// request API yang gagal karena sesi sudah tidak valid lagi — Frappe
// (perilaku BAWAAN framework, BUKAN kustomisasi Rumba) menaruh path
// terakhir yang sedang terbuka ke query-string /login, misalnya:
//   /login?redirect-to=%2Fdesk%2Ftutor
//
// Ini terbukti dari kode sumber resmi Frappe
// (frappe/templates/includes/login/login.js, handler sukses sesudah
// login):
//   window.location.href =
//     frappe.utils.sanitise_redirect(frappe.utils.get_url_arg("redirect-to"))
//     || data.home_page;
//
// Artinya: KALAU `redirect-to` ADA di URL saat form login disubmit, Frappe
// SELALU memakainya — LEPAS dari siapa pun yang baru login, LEPAS dari
// hook role_home_page / www/masuk.py sama sekali. `data.home_page` (yang
// mestinya = "/masuk" untuk semua role Rumba, lihat hooks.role_home_page)
// baru dipakai kalau `redirect-to` KOSONG.
//
// Inilah akar masalah PALING DASAR dari "ganti role di browser yang sama,
// masih nyasar ke workspace role sebelumnya" — lebih dasar dari
// rumba_desk_landing.js. Guard di rumba_desk_landing.js TETAP dipertahankan
// sebagai lapis kedua (utk kasus orang mengetik/mem-bookmark /app langsung
// tanpa lewat /login), tapi TIDAK bisa menolong kasus redirect-to ini,
// karena browser sudah diperintahkan Frappe sendiri utk lompat LANGSUNG ke
// path lama itu, sebelum boot desk & skrip guard kita sempat jalan sama
// sekali.
//
// FIX: begitu halaman /login dimuat — jauh sebelum pengguna sempat
// menekan tombol Login (yang baru men-trigger pembacaan redirect-to oleh
// login.js) — buang parameter `redirect-to` dari URL browser via
// history.replaceState. Karena login.js membaca ulang window.location.search
// PERSIS saat proses login sukses (bukan sekali di awal render halaman),
// begitu parameter itu sudah kita buang dari address bar, Frappe otomatis
// jatuh ke `data.home_page` — yang lewat role_home_page hook akan berupa
// "/masuk", lalu www/masuk.py yang memutuskan tujuan berdasarkan role yang
// BENAR-BENAR login sekarang.
//
// TRADE-OFF YANG DISADARI: fitur bawaan Frappe "kembali ke halaman persis
// yang sedang dibuka sebelum sesi habis" (mis. sedang buka satu laporan
// spesifik, sesi timeout, login ulang -> otomatis balik ke laporan itu)
// jadi HILANG untuk SEMUA pengguna termasuk Administrator, karena skrip ini
// berjalan sebelum siapa pun login sehingga tidak bisa tahu role/akun
// siapa yang akan dipakai. Ini keputusan sadar: di sistem ini skenario
// ganti-role di browser yang sama jauh lebih sering terjadi & lebih
// mengganggu daripada manfaat "kembali ke halaman terakhir".
//
// PEMASANGAN (server):
//   1) taruh file di: apps/rumba16/rumba16/public/js/rumba_login_no_redirect.js
//   2) hooks.py:
//        web_include_js = "/assets/rumba16/js/rumba_login_no_redirect.js?v=20260806a"
//      (WAJIB naikkan angka/tanggal di ?v= setiap kali file ini diedit &
//      di-deploy ulang — masalah cache browser 1 tahun yang sama persis
//      dengan rumba_desk_landing.js, lihat catatan di hooks.py)
//   3) bench build --app rumba16 && bench --site <site> clear-cache && bench restart
//   4) uji: login sbg Tutor -> buka workspace apa saja -> klik "Log out" ->
//      amati address bar: harus mendarat di /login POLOS (TANPA
//      ?redirect-to=...) -> login sbg role lain (mis. Personalia) -> harus
//      mendarat TEPAT di workspace role itu, BUKAN workspace Tutor.
// ---------------------------------------------------------------------------

(function () {
  "use strict";

  try {
    if (window.location.pathname !== "/login") return;
    if (window.location.search.indexOf("redirect-to") === -1) return;

    var url = new URL(window.location.href);
    url.searchParams.delete("redirect-to");

    // replaceState, BUKAN reload — supaya tidak ada flicker/loop. login.js
    // membaca query-string via frappe.utils.get_url_arg() persis saat form
    // disubmit (bukan sekali di awal render), jadi cukup URL sudah bersih
    // SEBELUM tombol Login ditekan.
    window.history.replaceState(
      {},
      document.title,
      url.pathname + (url.search || "") + (url.hash || "")
    );
  } catch (e) {
    // Gagal diam-diam — jangan sampai skrip ini malah menghalangi halaman
    // login tampil kalau ada API browser yang tak terduga tidak tersedia.
  }
})();
