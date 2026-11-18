/* Bize ulaş formu: ad soyad, telefon, okul. Sunucudaki iletisim.php'ye JSON olarak gönderilir. */
(() => {
  "use strict";
  const form = document.querySelector("[data-contact]");
  if (!form) return;
  const okBox = document.querySelector("[data-status-ok]");
  const errBox = document.querySelector("[data-status-error]");
  const submit = form.querySelector("button[type=submit]");
  const ENDPOINT = "iletisim.php";
  const PHONE_DIGITS = 10;
  const MIN_NAME_PARTS = 2;
  const MIN_SCHOOL_CHARS = 2;
  const GENERIC_ERROR = "Gönderemedik. Biraz sonra yeniden dene ya da Instagram'dan bize yaz: @mesemligencler";

  /** Telefonu 10 haneye indirir: "+90 5xx...", "05xx...", "5xx..." hepsi kabul. */
  function normalizePhone(value) {
    let digits = String(value).replace(/\D/g, "");
    if (digits.length === 12 && digits.startsWith("90")) digits = digits.slice(2);
    if (digits.length === 11 && digits.startsWith("0")) digits = digits.slice(1);
    return digits.length === PHONE_DIGITS ? digits : "";
  }

  function validate(data) {
    const errors = {};
    if (data.ad.trim().split(/\s+/).filter(Boolean).length < MIN_NAME_PARTS) errors.ad = "Adını ve soyadını yaz.";
    if (!normalizePhone(data.telefon)) errors.telefon = "Telefon numaranı yaz, örneğin 05xx xxx xx xx.";
    if (data.okul.trim().length < MIN_SCHOOL_CHARS) errors.okul = "Okulunun adını yaz.";
    return errors;
  }

  function showErrors(errors) {
    for (const name of ["ad", "telefon", "okul"]) {
      const input = form.elements[name];
      const slot = form.querySelector(`[data-error-for="${name}"]`);
      slot.textContent = errors[name] || "";
      if (errors[name]) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid");
    }
    const first = Object.keys(errors)[0];
    if (first) form.elements[first].focus();
  }

  async function send(payload) {
    const res = await fetch(ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    let body = {};
    try { body = await res.json(); } catch { /* sunucu JSON dönmediyse genel hata gösterilir */ }
    if (!res.ok || !body.ok) throw new Error(body.hata || GENERIC_ERROR);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errBox.hidden = true;
    const data = { ad: form.elements.ad.value, telefon: form.elements.telefon.value, okul: form.elements.okul.value, web: form.elements.web.value };
    const errors = validate(data);
    showErrors(errors);
    if (Object.keys(errors).length) return;

    submit.disabled = true;
    submit.textContent = "Gönderiliyor";
    try {
      await send({ ad: data.ad.trim(), telefon: normalizePhone(data.telefon), okul: data.okul.trim(), web: data.web });
      form.hidden = true;
      okBox.hidden = false;
      okBox.focus?.();
    } catch (err) {
      errBox.textContent = err.message || GENERIC_ERROR;
      errBox.hidden = false;
      submit.disabled = false;
      submit.textContent = "Gönder";
    }
  });
})();
