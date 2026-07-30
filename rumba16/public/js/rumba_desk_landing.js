// RUMBA — arahkan pengguna desk ber-role Rumba ke workspace unit-nya saat masuk desk.
// Masalah: /app (desk) untuk System User default membuka workspace standar (mis. Stock),
// karena role_home_page/masuk.py hanya mengatur route website ("/"), bukan desk ("/app").
// Solusi: bila pengguna Rumba mendarat di workspace NON-Rumba, alihkan sekali ke /masuk,
// yang me-redirect per-peran ke /app/<workspace> (logika di www/masuk.py — satu sumber kebenaran).
// Aman: hanya sekali per masuk desk, ada pengaman anti-loop, dan tidak mengganggu admin.
(function () {
  function slugify(x) {
    return (window.frappe && frappe.router && frappe.router.slug)
      ? frappe.router.slug(x)
      : String(x || "").toLowerCase().replace(/ /g, "-");
  }

  function check() {
    if (window.__rumba_landing_done) return;
    try {
      if (!window.frappe || !frappe.boot || !frappe.get_route) return setTimeout(check, 300);

      var roles = (frappe.boot.user && frappe.boot.user.roles) || frappe.user_roles || [];
      var isRumba = roles.some(function (r) { return String(r).indexOf("Rumba ") === 0; });
      var privileged = roles.indexOf("System Manager") > -1 ||
        (frappe.session && frappe.session.user === "Administrator");
      if (!isRumba || privileged) { window.__rumba_landing_done = true; return; }

      var route = frappe.get_route() || [];
      // tunggu sampai route workspace ter-resolve
      if (!(route[0] === "Workspaces" && route[1])) return setTimeout(check, 300);

      window.__rumba_landing_done = true;

      var mww = frappe.boot.module_wise_workspaces || {};
      var rumbaWs = (mww["Bimbel Rumba v16"] || []).map(slugify);
      var cur = slugify(route[1]);

      if (rumbaWs.indexOf(cur) > -1) {
        sessionStorage.removeItem("rumba_landing_redirects");
        return; // sudah di workspace Rumba — biarkan
      }

      var n = parseInt(sessionStorage.getItem("rumba_landing_redirects") || "0", 10);
      if (n >= 2) return; // pengaman anti-loop
      sessionStorage.setItem("rumba_landing_redirects", String(n + 1));
      window.location.href = "/masuk";
    } catch (e) {
      window.__rumba_landing_done = true;
    }
  }

  if (window.frappe && frappe.after_ajax) frappe.after_ajax(check);
  setTimeout(check, 1000);
})();
