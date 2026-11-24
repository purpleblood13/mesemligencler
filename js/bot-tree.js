/* Sohbet botunun konuşma ağacı. Belirleyici (deterministik): serbest metin yok, her adım seçeneklerle ilerler.
   Düzenlemek için yalnızca bu dosyayı değiştirmek yeterli; motor js/bot.js.

   Düğüm alanları:
     say      [metin]  botun söyleyeceği mesajlar
     links    [{label, href}]  mesajların altında bağlantı düğmeleri
     summary  true     o ana kadarki cevapların özet kartı
     choices  [{label, next, set?, sum?, say?, links?, action?}]
                set    {anahtar: değer}  cevabı kaydeder
                sum    "..."             özet kartına girecek cümle
                say    [metin]           seçimin hemen ardından tepki
                action "restart" | "close"
     route    {by, map, default}   görünmeyen yönlendirme
     skip     [{when|unless: {anahtar: değer|[değerler]}, to}]  koşul sağlanırsa bu adım atlanır
     check    true     hukuk/bilgi doğrulaması gerekir (yayından önce gözden geçirilecek)
   Rakamlar Emek Gençliği'nin 530 genç ve çocuk işçiyle yaptığı ankete dayanır (Evrensel, 16 Eylül 2026). */
window.MG_BOT = {
  start: "giris",
  submitEnabled: false, // cevapları isimsiz göndermek, sunucu tarafı kararına bağlı
  nodes: {
    giris: {
      say: [
        "Selam! Biz MESEM'li Gençler: MESEM'de, meslek lisesinde ve işte olan gençlerin ağıyız.",
        "Sana birkaç soru soracağım. İsmini sormuyorum; cevapların bu cihazda kalır. İstediğin soruyu atlayabilirsin.",
      ],
      choices: [
        { label: "Başlayalım", next: "mod" },
        { label: "Önce sizi tanıyayım", next: "tanis" },
        { label: "Haklarımı öğrenmek istiyorum", next: "haklar" },
      ],
    },
    tanis: {
      say: [
        "MESEM'i, öğrenciyi haftada en az 4 gün işletmede çalıştıran bir ucuz emek ve çocuk işçiliği düzeni olarak görüyoruz. Amacımız mesleki eğitimin okulda, parasız ve güvenli verilmesi.",
        "Bunun için önce senin neler yaşadığını bilmemiz gerekiyor. Ne kadar çok genç anlatırsa, itirazımız o kadar güçlü olur.",
      ],
      links: [{ label: "Biz kimiz", href: "biz-kimiz.html" }],
      choices: [
        { label: "Sorulara geçelim", next: "mod" },
        { label: "Haklarımı öğrenmek istiyorum", next: "haklar" },
      ],
    },
    mod: {
      say: ["Sohbet ne kadar sürsün?"],
      choices: [
        { label: "Kısa, yaklaşık 2 dakika", next: "durum", set: { mod: "kisa" } },
        { label: "Ayrıntılı, yaklaşık 5 dakika", next: "durum", set: { mod: "uzun" } },
      ],
    },
    durum: {
      say: ["Şu an durumun hangisi?"],
      choices: [
        { label: "MESEM'e gidiyorum", next: "yas", set: { durum: "mesem" }, sum: "MESEM öğrencisisin" },
        { label: "Meslek lisesine gidiyorum, MESEM değil", next: "yas", set: { durum: "meslek" }, sum: "Meslek lisesi öğrencisisin" },
        { label: "Okulu bitirdim, çalışıyorum", next: "yas", set: { durum: "mezun" }, sum: "Okulu bitirdin ve çalışıyorsun" },
        {
          label: "Okula gitmiyorum, çalışıyorum",
          next: "yas",
          set: { durum: "okuldisi" },
          sum: "Okula gitmeden çalışıyorsun",
          say: ["Anlıyorum. Okul çağındaki bir çocuğun çalışması onun suçu değil; bu düzen ucuz emeğe ihtiyaç duyduğu için var."],
        },
        { label: "Veli ya da öğretmenim", next: "veli", set: { durum: "yetiskin" } },
      ],
    },
    veli: {
      say: [
        "Hoş geldiniz. Çocuğunuzun ya da öğrencinizin MESEM deneyimiyle ilgili endişeleriniz varsa bize yazabilirsiniz.",
        "MESEM'deki iş kazaları, ücretler ve çalışma koşullarına dair haberlere ve Meclis önergelerine sitemizden ulaşabilirsiniz.",
      ],
      links: [
        { label: "Haberler", href: "haberler.html" },
        { label: "Meclis önergeleri", href: "onergeler.html" },
        { label: "Kayıplarımız", href: "kayiplar.html" },
      ],
      choices: [
        { label: "Bize ulaşmak istiyorum", next: "ulas" },
        { label: "Baştan başla", action: "restart" },
      ],
    },

    /* ---------- Sorular ---------- */
    yas: {
      skip: [{ unless: { durum: ["okuldisi"] }, to: "gun" }],
      say: ["Kaç yaşındasın?"],
      choices: [
        { label: "14 ya da daha küçük", next: "gun", set: { yas: "14" }, sum: "14 yaşında ya da daha küçüksün", say: ["Bu yaşta çalışmak çocuk işçiliğidir. Seni değil, düzeni suçluyoruz."] },
        { label: "15", next: "gun", set: { yas: "15" }, sum: "15 yaşındasın", say: ["Bu yaşta çalışmak çocuk işçiliğidir. Seni değil, düzeni suçluyoruz."] },
        { label: "16", next: "gun", set: { yas: "16" }, sum: "16 yaşındasın" },
        { label: "17", next: "gun", set: { yas: "17" }, sum: "17 yaşındasın" },
        { label: "18 ve üstü", next: "gun", set: { yas: "18" }, sum: "18 yaşın üstündesin" },
      ],
    },
    gun: {
      say: ["Haftada kaç gün işte ya da işyerindesin?"],
      choices: [
        { label: "1-2 gün", next: "saat", set: { gun: "2" }, sum: "Haftada 1-2 gün işyerindesin" },
        { label: "3 gün", next: "saat", set: { gun: "3" }, sum: "Haftada 3 gün işyerindesin" },
        { label: "4 gün", next: "saat", set: { gun: "4" }, sum: "Haftada 4 gün işyerindesin", say: ["MESEM'de haftada dört gün işletmedesin, bir gün okulda. Bu düzende öğrenci değil, işçi gibi çalıştırıldığını söyleyen çok genç var."] },
        { label: "5 gün", next: "saat", set: { gun: "5" }, sum: "Haftada 5 gün işyerindesin", say: ["Ankete katılan gençlerin yalnızca %34'ü haftada 5 gün çalışıyordu; çoğu bundan fazla."] },
        { label: "6 gün", next: "saat", set: { gun: "6" }, sum: "Haftada 6 gün işyerindesin", say: ["Ankete katılan gençlerin yarısından fazlası senin gibi haftada 6 gün çalışıyor. Haftalık izin senin hakkın."] },
        { label: "7 gün", next: "saat", set: { gun: "7" }, sum: "Haftada 7 gün işyerindesin", say: ["Ankette 38 genç hiç haftalık izin kullanmadan, 7 gün çalıştığını söyledi. Bu kabul edilebilir değil."] },
      ],
    },
    saat: {
      say: ["Bir günde kaç saat çalışıyorsun? Yolu sayma."],
      choices: [
        { label: "8 saat ve altı", next: "ucret", set: { saat: "8" }, sum: "Günde 8 saat ya da daha az çalışıyorsun", say: ["Ankette yalnızca %17'lik bir kesim böyle. Çoğu gencin işi bundan uzun."] },
        { label: "9-10 saat", next: "ucret", set: { saat: "10" }, sum: "Günde 9-10 saat çalışıyorsun", say: ["Ankete katılan gençlerin %44'ü senin gibi günde 9-10 saat çalışıyor."] },
        { label: "11-12 saat", next: "ucret", set: { saat: "12" }, sum: "Günde 11-12 saat çalışıyorsun", say: ["Her dört gençten biri senin gibi günde 11-12 saat çalışıyor. Bu çok uzun; özellikle 18 yaşından küçükler için."] },
        { label: "12 saatten fazla", next: "ucret", set: { saat: "13" }, sum: "Günde 12 saatten fazla çalışıyorsun", say: ["Ankette en az 23 genç günde 12 saatten fazla çalıştığını söyledi; bazıları 16-18 saate kadar. Bu kabul edilebilir değil."] },
      ],
    },
    ucret: {
      say: ["Ücret ya da harçlık alıyor musun?"],
      choices: [
        { label: "Düzenli alıyorum", next: "yol", set: { ucret: "duzenli" }, sum: "Ücretini düzenli alıyorsun", say: ["İyi. Yine de ankette gençlerin %69'u asgari ücret ya da altında kazanıyordu; saatlik hesaba vurunca çoğu zaman çok düşük kalıyor."] },
        {
          label: "Geç ya da eksik alıyorum",
          next: "yol",
          set: { ucret: "gec" },
          sum: "Ücretini geç ya da eksik alıyorsun",
          say: ["Ücretin zamanında ve eksiksiz ödenmesi hakkın. Devlet katkısı kesildiği için yüz binlerce MESEM'linin maaş alamadığı haberleri çıktı."],
          links: [{ label: "Haberlere bak", href: "haberler.html" }],
        },
        { label: "Hiç alamıyorum", next: "yol", set: { ucret: "yok" }, sum: "Ücret alamıyorsun", say: ["Bu, bizim en çok duymak istediğimiz şeylerden biri. Bunu kayda geçirmemiz önemli; devam edelim."] },
        { label: "Ne kadar aldığımı bilmiyorum", next: "yol", set: { ucret: "bilmiyor" }, sum: "Ücretinin ne kadar olduğunu bilmiyorsun", say: ["Bilmemen çok normal; kimse net söylemiyor. Ücretinin ne kadarının devletten, ne kadarının işletmeden geldiğini sorma hakkın var."] },
      ],
    },
    yol: {
      skip: [{ when: { mod: "kisa" }, to: "degistir" }],
      say: ["İşe gidip gelmek nasıl oluyor?"],
      choices: [
        { label: "Servis var", next: "sigorta", set: { yol: "servis" } },
        {
          label: "Yol parasını kendim ödüyorum",
          next: "sigorta",
          set: { yol: "kendim" },
          sum: "Yol parasını kendin ödüyorsun",
          say: ["Ankete katılan gençlerin %30'dan fazlası günün bir saatinden fazlasını yolda geçiriyor; bunların %57'si yol parasını kendisi ödüyor."],
          links: [{ label: "Yol parası mektubunu oku", href: "mektuplar.html" }],
        },
        { label: "Yakın, yürüyorum", next: "sigorta", set: { yol: "yakin" } },
      ],
    },
    sigorta: {
      say: ["Sigortan var mı?"],
      choices: [
        { label: "Var", next: "kaza", set: { sigorta: "var" } },
        { label: "Yok", next: "kaza", set: { sigorta: "yok" }, sum: "Sigortan yok", say: ["MESEM öğrencileri iş kazası ve meslek hastalığı sigortası kapsamında olmak zorunda. Bunu bize yazarsan birlikte bakarız."] },
        { label: "Bilmiyorum", next: "kaza", set: { sigorta: "bilmiyor" }, sum: "Sigortalı olup olmadığını bilmiyorsun", say: ["Bilmemen normal. Sigortalı olup olmadığını e-Devlet'te 'SGK Tescil ve Hizmet Dökümü' ekranından kendin görebilirsin."] },
      ],
      check: true,
    },
    kaza: {
      say: ["İşte hiç yaralandın ya da kaza geçirdin mi?"],
      choices: [
        { label: "Hayır", next: "usta", set: { kaza: "hayir" }, say: ["Ankete katılan gençlerin %55'i en az bir kez iş kazası geçirmiş. Dikkat etmek kadar, hakkını bilmek de önemli."] },
        { label: "Evet, bir kez", next: "kaza_dal", set: { kaza: "bir" }, sum: "Bir kez iş kazası geçirdin" },
        { label: "Evet, birkaç kez", next: "kaza_dal", set: { kaza: "cok" }, sum: "Birkaç kez iş kazası geçirdin" },
        { label: "Söylemek istemiyorum", next: "usta", set: { kaza: "atla" }, say: ["Tamam, geçelim."] },
      ],
    },
    kaza_dal: {
      say: [
        "Geçmiş olsun. Bilmen gerekenler:",
        "Küçük de olsa her yaralanmada doktora git ve kaydın tutulmasını iste. Kaza, işveren tarafından SGK'ya bildirilmek zorunda.",
        "Sık kaza geçiren gençlerin dörtte biri kimseye söylemiyor. Sen söyle; bize de yazabilirsin. Acil durumda 112'yi ara.",
      ],
      check: true,
      choices: [{ label: "Devam", next: "usta" }],
    },
    usta: {
      say: ["Usta ya da yöneticinin sana davranışı nasıl?"],
      choices: [
        { label: "Saygılı", next: "izin", set: { usta: "iyi" } },
        { label: "Bağırıyor, hakaret ediyor", next: "izin", set: { usta: "hakaret" }, sum: "Ustandan bağırma ve hakaret görüyorsun", say: ["Ankette gençlerin %16'sı en çok ustanın ya da ustabaşının davranışının değişmesini istedi. Hakaret 'çıraklığın parçası' değildir."] },
        { label: "Şiddet uyguluyor", next: "siddet_dal", set: { usta: "siddet" }, sum: "İşyerinde şiddet görüyorsun" },
        { label: "Söylemek istemiyorum", next: "izin", set: { usta: "atla" }, say: ["Tamam, geçelim."] },
      ],
    },
    siddet_dal: {
      say: [
        "Şiddet kabul edilemez ve suçtur. Suçlu sen değilsin.",
        "Tehlikedeysen 112'yi ara. Çocuklara yönelik şiddet için ALO 183 Sosyal Destek Hattı'nı da arayabilirsin.",
        "İstersen bize yaz, ne yapılabileceğine birlikte bakalım. Tek başına ustayla ya da patronla yüzleşmeni önermiyoruz.",
      ],
      check: true,
      choices: [{ label: "Devam", next: "izin" }],
    },
    izin: {
      say: ["Tatilde ve izinlerde ne oluyor?"],
      choices: [
        { label: "İzin kullanıyorum", next: "okul", set: { izin: "kullanir" } },
        { label: "Tatilde de çalışıyorum", next: "okul", set: { izin: "calisir" }, sum: "Tatillerde de çalışıyorsun", say: ["Ankette gençlerin neredeyse %40'ı yıllık iznini kullanamıyor. Kanuna göre MESEM'li öğrencilerin tatil aylarında bir ay ücretli izin hakkı var."] },
        { label: "İzin hakkım olduğunu bilmiyordum", next: "okul", set: { izin: "bilmiyor" }, say: ["Çoğu genç bilmiyor; kimse söylemiyor. Şimdi biliyorsun."] },
      ],
      check: true,
    },
    okul: {
      skip: [
        { unless: { durum: ["mesem", "meslek"] }, to: "degistir" },
        { when: { mod: "kisa" }, to: "degistir" },
      ],
      say: ["Okul gününde gerçekten ders yapıyor musun?"],
      choices: [
        { label: "Evet, düzgün ders", next: "ogrenme", set: { okul: "iyi" } },
        { label: "Ders var ama yarım yamalak", next: "ogrenme", set: { okul: "yarim" }, sum: "Okulda dersler yarım yamalak", say: ["Çok yaygın bir şikâyet. Ders eksik kalınca 'meslek eğitimi' de eksik kalıyor."] },
        { label: "Okul gününde de çalıştırılıyorum", next: "ogrenme", set: { okul: "calisir" }, sum: "Okul gününde de çalıştırılıyorsun", say: ["Bu, eğitimle ilgisi olmayan düpedüz çalıştırma. Bunu yazmak isteyebilirsin; bize ulaşabilirsin."] },
        { label: "Okula hiç gitmiyorum", next: "ogrenme", set: { okul: "hic" }, sum: "Okula hiç gitmiyorsun" },
      ],
    },
    ogrenme: {
      skip: [
        { unless: { durum: ["mesem", "meslek"] }, to: "degistir" },
        { when: { mod: "kisa" }, to: "degistir" },
      ],
      say: ["İşyerinde gerçekten meslek öğreniyor musun?"],
      choices: [
        { label: "Evet, öğreniyorum", next: "degistir", set: { ogrenme: "evet" } },
        { label: "Bazen", next: "degistir", set: { ogrenme: "bazen" } },
        { label: "Çoğunlukla temizlik, taşıma, çay ocağı işleri", next: "degistir", set: { ogrenme: "angarya" }, sum: "Meslek yerine daha çok yardımcı işler yapıyorsun", say: ["MESEM'i 'meslek öğrenme' diye anlatıyorlar ama senin gibi birçok genç 'kullan-at çırak' gibi görüldüğünü söylüyor. Bunu kayda geçirmek bizim için çok değerli."] },
        { label: "Hayır, sadece çalışıyorum", next: "degistir", set: { ogrenme: "hayir" }, sum: "Meslek öğrenmiyorsun, sadece çalışıyorsun", say: ["Bunu duymak zor. Tam da bu yüzden itiraz ediyoruz."] },
      ],
    },
    degistir: {
      say: ["İşte ya da işyerinde ilk neyin değişmesini isterdin?"],
      choices: [
        { label: "Çalışma saatleri", next: "his", set: { degistir: "saat" }, sum: "En çok çalışma saatlerinin değişmesini istiyorsun", say: ["Ankete katılan gençlerin %28'i de senin gibi ilk bunu söyledi; en çok verilen cevap buydu."] },
        { label: "Ücret", next: "his", set: { degistir: "ucret" }, sum: "En çok ücretin değişmesini istiyorsun", say: ["Ankette %26 ile ücretler ikinci sıradaydı."] },
        { label: "Ustanın davranışı", next: "his", set: { degistir: "usta" }, sum: "En çok ustanın davranışının değişmesini istiyorsun", say: ["Ankette %16 ile üçüncü sıradaydı. Saygı görmek temel bir haktır."] },
        { label: "İş güvenliği", next: "his", set: { degistir: "guvenlik" }, sum: "En çok iş güvenliğinin değişmesini istiyorsun", say: ["Bunu isteyen çok genç var; ankete katılanların yarısından fazlası en az bir kez iş kazası geçirmişti."] },
        { label: "Öğrenme ve eğitim", next: "his", set: { degistir: "egitim" }, sum: "En çok öğrenme ve eğitimin değişmesini istiyorsun", say: ["Çok haklısın. İstediğimiz de tam bu: okulda, nitelikli, uygulamalı ve güvenli mesleki eğitim."] },
        { label: "Hiçbiri", next: "his", set: { degistir: "hicbiri" } },
      ],
    },
    his: {
      skip: [{ when: { mod: "kisa" }, to: "arkadas" }],
      say: ["Sabah işe ya da okula giderken nasıl hissediyorsun?"],
      choices: [
        { label: "Yorgun", next: "gelecek", set: { his: "yorgun" }, sum: "Sabahları yorgun hissediyorsun", say: ["Ankette en sık verilen cevap 'yorgun' oldu; katılımcıların yaklaşık dörtte biri böyle hissediyor."] },
        { label: "Mutsuz ya da umutsuz", next: "gelecek", set: { his: "mutsuz" }, sum: "Sabahları mutsuz ya da umutsuz hissediyorsun", say: ["Bu duyguyu yalnız taşımak zorunda değilsin. Ankette gençlerin %75'i benzer şeyler söyledi: uykusuz, mutsuz, bitkin."] },
        { label: "İdare eder", next: "gelecek", set: { his: "idare" } },
        { label: "İyi", next: "gelecek", set: { his: "iyi" }, say: ["Güzel. Sen iyi olsan bile arkadaşların aynı durumda olmayabilir."] },
      ],
    },
    gelecek: {
      say: ["Beş yıl sonra kendini nerede görüyorsun?"],
      choices: [
        { label: "Kendi işimin patronu", next: "arkadas", set: { gelecek: "isyeri" }, say: ["Anketteki gençlerin çoğu kendi işini kurmayı ya da okumayı düşünüyor. Ama bu hedefler için önce insanca bir iş ve eğitim gerekiyor."] },
        { label: "Üniversite ya da MYO", next: "arkadas", set: { gelecek: "okul" } },
        { label: "Aynı işyerinde çalışmak", next: "arkadas", set: { gelecek: "ayni" } },
        { label: "Net bir planım yok", next: "arkadas", set: { gelecek: "yok" }, sum: "Geleceğe dair net bir planın yok", say: ["Çok normal. Anketteki gençler arasında net planı olmayanlarda karamsarlık artıyordu. Plan yapabilmek için önce güvenli bir eğitim ve insanca bir iş gerekiyor; mücadelemiz de bunun için."] },
      ],
    },
    arkadas: {
      say: ["Yanında aynı durumda olan arkadaşların var mı?"],
      choices: [
        { label: "Evet, çoğumuz aynı durumdayız", next: "ozet", set: { arkadas: "cok" }, sum: "Çevrende aynı durumda çok arkadaşın var", say: ["Bu çok değerli: birlikte hareket etmenin ilk şartı bu."] },
        { label: "Evet, birkaç kişi", next: "ozet", set: { arkadas: "az" }, sum: "Çevrende aynı durumda birkaç arkadaşın var" },
        { label: "Hayır, yalnız gibiyim", next: "ozet", set: { arkadas: "yok" }, sum: "Kendini yalnız hissediyorsun", say: ["Birçok genç aynı şeyleri yaşadığını birbirine söylemiyor. Oysa 530 gencin anlattıkları birbirine çok benziyor: yalnız değilsin."] },
        { label: "Bilmiyorum, hiç konuşmadık", next: "ozet", set: { arkadas: "bilmiyor" }, say: ["Konuşmak güzel bir başlangıç olabilir. Birazdan nasıl yapılacağını anlatırım."] },
      ],
    },

    /* ---------- Özet ve merkez ---------- */
    ozet: {
      say: ["Teşekkürler, bunları paylaştığın için. Seninle ilgili özet:"],
      summary: true,
      choices: [{ label: "Şimdi ne yapabilirim?", next: "merkez" }],
    },
    merkez: {
      say: ["Seninle şunları yapabiliriz. Hangisini istersin?"],
      choices: [
        { label: "Haklarımı öğrenmek istiyorum", next: "haklar" },
        { label: "Benim gibi gençlerle bağlantı kurmak istiyorum", next: "kanallar" },
        { label: "Çevremdekilerle birlikte hareket etmek istiyorum", next: "birlik" },
        { label: "Bizimle konuşmak, bize ulaşmak istiyorum", next: "ulas" },
        { label: "Şimdilik bu kadar", next: "bitis" },
      ],
    },

    /* ---------- Haklar ---------- */
    haklar: {
      say: ["Hangi konuyu merak ediyorsun?", "Bunlar genel bilgidir, hukuki danışmanlık değildir. Durumun için bize yazabilirsin."],
      choices: [
        { label: "Çalışma saatleri ve izinler", next: "h_saat" },
        { label: "Ücret ve sigorta", next: "h_ucret" },
        { label: "İş kazası ve sağlık", next: "h_kaza" },
        { label: "Şiddet ve kötü muamele", next: "h_siddet" },
        { label: "Okul ve eğitim", next: "h_okul" },
        { label: "Geri dön", next: "merkez" },
      ],
    },
    h_saat: {
      say: [
        "Çocuk ve genç işçiler için çalışma süreleri yetişkinlerden kısadır ve haftalık izin hakkı vardır. 18 yaşından küçükler ağır ve tehlikeli işlerde çalıştırılamaz.",
        "Kanuna göre MESEM'li öğrenciler tatil aylarında bir ay ücretli izin hakkına sahiptir.",
      ],
      check: true,
      choices: [
        { label: "Başka konu", next: "haklar" },
        { label: "Bize yaz", next: "ulas" },
      ],
    },
    h_ucret: {
      say: [
        "Ücretin zamanında ve eksiksiz ödenmesi gerekir. Kime, ne kadar ödendiğini sormaya hakkın var.",
        "Sigortalı olup olmadığını e-Devlet'te 'SGK Tescil ve Hizmet Dökümü' ekranından görebilirsin.",
        "Ücret alamıyorsan ya da eksik alıyorsan bize yaz; benzer durumdaki gençlerle birlikte bakalım.",
      ],
      check: true,
      choices: [
        { label: "Başka konu", next: "haklar" },
        { label: "Bize yaz", next: "ulas" },
      ],
    },
    h_kaza: {
      say: [
        "Küçük de olsa her yaralanmada doktora git ve kaydın tutulmasını iste.",
        "İş kazası SGK'ya bildirilmek zorundadır. Bildirim yapılmıyorsa ya da 'kimseye söyleme' deniyorsa bize yaz.",
        "Acil durumda 112'yi ara.",
      ],
      check: true,
      choices: [
        { label: "Başka konu", next: "haklar" },
        { label: "Bize yaz", next: "ulas" },
      ],
    },
    h_siddet: {
      say: [
        "Bağırma, hakaret ve şiddet 'çıraklığın parçası' değildir; suçtur.",
        "Tehlikedeysen 112'yi ara. ALO 183 Sosyal Destek Hattı çocuklara yönelik şiddet için de aranabilir.",
        "Tek başına usta ya da patronla yüzleşmeni önermiyoruz; önce bizimle konuş.",
      ],
      check: true,
      choices: [
        { label: "Başka konu", next: "haklar" },
        { label: "Bize yaz", next: "ulas" },
      ],
    },
    h_okul: {
      say: [
        "MESEM'de haftada bir gün okulda eğitim görmen gerekir. Okul gününde çalıştırılıyorsan ya da ders yapılmıyorsa bunu bize yaz.",
        "Mesleki eğitim, işletmenin ucuz iş gücü ihtiyacına dönüşmemeli. Eğitimin senin için olması gerekir.",
      ],
      check: true,
      choices: [
        { label: "Başka konu", next: "haklar" },
        { label: "Bize yaz", next: "ulas" },
      ],
    },

    /* ---------- Bağlantı ve birlik ---------- */
    kanallar: {
      say: ["Bizi şuralardan takip edebilirsin. Haberler, mektuplar ve haklarına dair paylaşımlar buradan geliyor:"],
      links: [
        { label: "Instagram", href: "https://www.instagram.com/mesemligencler/", ext: true },
        { label: "TikTok", href: "https://www.tiktok.com/@mesemligencler", ext: true },
        { label: "YouTube", href: "https://www.youtube.com/@MESEMliGencler2024", ext: true },
        { label: "Instagram akışı", href: "akis.html" },
        { label: "Mektuplarımız", href: "mektuplar.html" },
        { label: "Haberler", href: "haberler.html" },
      ],
      choices: [
        { label: "Birlikte hareket etmek istiyorum", next: "birlik" },
        { label: "Başka bir şey yapalım", next: "merkez" },
      ],
    },
    birlik: {
      say: [
        "Yalnız değilsin: anketteki 530 gencin yaşadıkları birbirine çok benziyor. Tek tek susturulan sorunlar, birlikte söylenince duyuluyor.",
        "Beş adımda anlatayım.",
      ],
      choices: [{ label: "Anlat", next: "b1" }],
    },
    b1: {
      say: ["1) Konuş. İşyerindeki ya da okuldaki iki üç arkadaşına 'en çok neyi değiştirmek isterdin' diye sor. Çoğu zaman aynı şeyi söylerler."],
      choices: [{ label: "Devam", next: "b2" }],
    },
    b2: {
      say: ["2) Listeyi yap. Ortak üç şeyi yaz: örneğin 'ücret zamanında yatsın', 'servis olsun', 'mesai dokuz saati geçmesin'. Kısa ve net olsun."],
      choices: [{ label: "Devam", next: "b3" }],
    },
    b3: {
      say: ["3) Tek başına patrona gitme. Tek başına gidenler kolayca hedef olur. Önce hakkını ve neler yapabileceğini bil, mümkünse birlikte hareket et."],
      choices: [{ label: "Peki sonra?", next: "b4" }],
    },
    b4: {
      say: [
        "4) Bize ulaş. Senin gibi durumdaki gençlerle ve emek örgütleriyle bağlantı kurmana yardım ederiz.",
        "5) Duyur. İstersen sorununuzu isimsiz olarak sayfamızda ve Instagram'da paylaşırız; senin iznine bağlı.",
      ],
      links: [{ label: "Bize ulaş", href: "iletisim.html" }],
      choices: [{ label: "Başka bir şey yapalım", next: "merkez" }],
    },
    ulas: {
      say: [
        "Bize ulaşmak için Instagram'dan (@mesemligencler) ya da TikTok'tan DM atman yeterli. Ekipten biri sana geri döner.",
        "Yazdıklarını yalnızca seninle konuşmak için kullanırız; iznin olmadan kimseyle paylaşmayız.",
      ],
      links: [{ label: "Bize ulaş", href: "iletisim.html" }],
      choices: [{ label: "Başka bir şey yapalım", next: "merkez" }],
    },
    bitis: {
      say: ["Teşekkürler! Aklına bir şey gelirse buradayız. Haklarını bil, arkadaşlarınla konuş; yalnız değilsin."],
      choices: [
        { label: "Baştan başla", action: "restart" },
        { label: "Sohbeti kapat", action: "close" },
      ],
    },
  },
};
