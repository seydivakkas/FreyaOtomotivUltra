# F1-C — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel

> F1-A'nın tek akustik karar sahibini genişletir: F0-B akustik kanıtı, F2-C kısmi/kararlı ipucu ve F3-A'nın beklenen slot türüyle **sınırlı ve uyarlanır** bir endpoint eşiği; Türkçe devam ipuçları ("ve", "ama", "çünkü", "saat on dört…"); her düşük dizi için değiştirilemez anlamsal son tarih; yankı/double-talk'u temkinli yorumlama; "hı hı", "evet", "dur", "tamam tamam" gibi sözleri ayırt eden muhafazakâr backchannel sınıflaması. Gerçek düşük sessizlik olmadan kesim yok; kısmi sonuç hiçbir iş etkisi üretmez.

| Alan | Değer |
| --- | --- |
| Kimlik | F1-C |
| Dalga | W4 |
| Öncelik | P1 |
| Önkoşullar | W2_GATE, F1-B, F2-C, F3-A, F0-B |
| Sonraki | G2 |
| Bayrak | `f1_pipeline_v2` + M03 profili `f1.semantic_endpoint` (`OFF / SHADOW / STRICT`; varsayılan OFF) |
| Ortam | CPU (sahte saat, sahte sağlayıcılar); gerçek kayıt protokolü G5 |
| Eski görevler | F1-T12, F1-T13, F1-T15, F1-T16, F1-T17, F1-T18, F1-T19 |
| Kaynak | Bundle `W4/Freya_2_0_F1_C_Agent_Implementation_Package.md`; [F1 spec](../../../stages/F1-voice-turn-detection/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Müşteri model yılını söyledikten sonra düşünmek için durduğunda Freya araya girmemeli; ama kısa ve açık bir "evet"ten sonra da gereksiz yere beklememeli. Freya konuşurken müşterinin "hı hı" demesi kesme sayılmamalı, "dur" ise sayılmalı. F1-C bu kararları **danışma** düzeyinde kanıtla zenginleştirir; son söz her zaman F1-A/F1-B'nin akustik ve M02 otoritesindedir.

## 2. Başlamadan önce

- [ ] W2_GATE PASS; F1-B, F2-C, F3-A, F0-B gerçek kabul; onay. (F6-B geçişli bağımlılık; F3-B isteğe bağlı uyum — yeni zorunlu kenar yok.)
- [ ] Mevcut Silero/Endpoint/lookback, F1-B, ipucu/bağlam/kanıt noktaları ve eski web/telefon yolları izlenmiş; mevcut anlamsal bayrak/sınıflandırıcı varsa yeniden kullanılır, ikinci otorite yok.
- [ ] Benchmark korpusu (temiz, gürültülü, devam, backchannel katmanları), etiketler, tabanlar, metrikler, tolerans ve ayrılmış test protokolü dondurulmuş; gerçek ölçüm G4/G5.

## 3. Kapsam

**Yapılacak:** Sözleşmeler ve konuşma kapsamı; sabit profil ve bütçeler; akustik kanıt birleştirme; anlamsal ipucu alımı; beklenen slot izdüşümü; Türkçe devam kuralları; uyarlanır endpoint politikası; anlamsal son tarihler; sonlandırma ve örnek bütünlüğü; yankı farkındalıklı karar; backchannel sınıflaması; F1-B bütünleşmesi; devam/kesme yarışları; iptal ve yaşam döngüsü; yalnız-final güvenliği; kaynak/telemetri; entegrasyon; benchmark protokolü.

**Yapılmayacak:** Yeni VAD veya dil modeli; kısmi sonuçtan F3/LLM/TTS/onay; F1-B duraklatma son tarihinin uzatılması; gerçek konuşma kaydı (G5).

## 4. Dosyalar

```
backend/voice_activity/semantic/
  scope.py  profile.py  acoustic_join.py  hint_intake.py  expected_slot.py
  turkish_continuation.py  adaptive_endpoint.py  deadlines.py  finalization_guard.py
  echo_aware.py  backchannel.py  f1b_bridge.py  resume_commit.py  lifecycle.py
  final_only_guard.py  telemetry.py
tests/voice_activity/semantic/
evidence/F1-C/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Bütçeler (32 ms pencere nicemlemesi)

| Parametre | İstenen | Etkin |
| --- | --- | --- |
| Asgari anlamsal bekleme | 250 ms | 256 ms (8 pencere); ikisi de raporlanır |
| Azami tam pencere bütçesi | 1 200 ms | en fazla 37 pencere = 1 184 ms |
| Post-roll | asgari bütçeden büyük olamaz | aksi halde profil reddedilir |

Negatif son tarih veya sınırsız üst sınır reddedilir; son kabul edilen profil korunur. Etkin söz içinde yapılandırma yeniden yüklemesi sabit politikayı değiştirmez. Profil OFF iken anlamsal ipuçları olsa bile eski karar paritesi.

### 5.2 Girdiler

- **F0-B akustik kanıtı:** F0'ın 20 ms blokları ile F1'in 32 ms penceresi gerçek aralıklarla birleştirilir (geri çağrı sayısıyla değil). Yanlış hız/dönemden eşlenmiş kanıt ret/bilinmiyor; geçerli saat eşlemeli taze örtüşme uygundur ama doğru kabul edilmez; farklı alanlarda saat eşlemesi yoksa bilinmiyor; referans eksik/geçmiş yetersizse yankı etiketi yok, taban kullanılır; kısmi kapsam sınırlaması kaydedilir.
- **F2-C ipucu:** aynı kapsam, kabul edilmiş revizyon, yaş, kapsama ve iptal bağlı; en yenisi birleştirilir, bloklama yok. TTL'de tam süre dolumu reddedilir (zamanlayıcı sıfırlanmaz); önceki konuşma kapsamından ipucu, sırasız eski revizyon, iptal edilmiş kararlı önek, ses ötesi kapsam, çok geride kalmış kapsam, mühürlü hat ipucu reddedilir.
- **F3-A beklenen slot:** yalnız tür ve revizyon (ör. `PHONE`), değer değil; özne değişimi eski bağlamı geçersiz kılar; bayat beklenti reddedilir; bağlam yoksa korunan arama yok; tam sunulmamış onay sorusu sırasında anlamlı yanıt adayı (onay değil); güvenilmeyen metnin kimlik/durum revizyonu iddiası reddedilir.

### 5.3 Türkçe devam kuralları (sınırlı, belirlenimci)

| Fikstür | Yorum |
| --- | --- |
| Sondaki "ve" / "ama" | Olası devam; kesin bitmemiş söz değil |
| Sondaki "çünkü" / "eğer" | Tazelik koşuluyla sınırlı devam ipucu |
| "Saat on dört" (beklenen saat) | Eksik aday; dakika uydurulmaz |
| Kısmi plaka veya telefon rakamları | Yalnız eksik kategori; rakam çıkarımı yok |
| "Qashqai değil, Juke" | Olumsuzluk/düzeltme korunur; erken kabul yok |
| "Evet ama" | Devam/karşıtlık; saf onay veya backchannel değil |
| Yalnız noktalama, belirsiz jetonlar | UNKNOWN; zorla anlamsal tamamlanma yok |

Eşleşme görünümünde Unicode I/ı ve İ/i Türkçe kurallarıyla; ham metin dokunulmaz.

### 5.4 Uyarlanır endpoint ve son tarihler

- Tamamlanma ipucu olsa bile gerçek düşük dizi olmadan erken kesim yok. Taze eksik slot + geçerli düşük dizi → yalnız seçili sınırlı eşik kadar bekle. Onaylı bağlamla kısa açık yanıt → gerçek geçerli düşük + post-roll sonrası daha erken eşik. Taban düşük eşikten sonra kullanılabilir ipucu yok → akustik geri düşme bir kez sonlandırma ister. Uzatma sırasında ipucu geçersizleşirse güncel gerçek düşük sayısıyla, taban sağlandıysa sonlandır. Konuşma sonlandırma talebinden önce dönerse aynı kapsam, düşük dizi iptal, geçmiş korunur.
- Son tarih düşük dizi başına **değiştirilemez**; yeni devam ipuçları özgün son tarihi sıfırlamaz. Geçerli düşük örnek olmadan duvar saati son tarihi gelirse uydurma sessizlik/final yok (F1-A takılma politikası). Kesin eşik ile sert sınır çakışmasında F1-A'ya göre `MAX_DURATION` önceliği. Sonlu olmayan skor ve dolgulu kuyruk gerçek sessizlik sayılmaz. Boşluk/dönem süreksizliği F1 sahibince iptal/sıfırlama. EOS veya sahip son tarihi anlamsal bütçeden önce gelirse sahip terminal davranışı öncelikli.

### 5.5 Sonlandırma, yankı ve backchannel

- Uzatılmış beklemede bile final ses kabul edilen kesimde (ilk düşük + post-roll) biter; artık uygun geçmiş korunur. Devam eden konuşmada ön kayıt bir kez. İki eşzamanlı endpoint geri çağrısı → tek atomik final rezervasyonu/tur/gönderim. Final kuyruğu doluysa açık geri basınç; sahte tur veya kısmi terfisi yok. Sonlandırma ile yeni konuşma yarışında sahip sıralaması. Final mühründen sonra F2-C geç P5 sonucu yayımlanmaz.
- **Yankı:** güvenilir eşleşen referanslı yalnız-uzak-uç ve inandırıcı yakın uç yoksa → yalnız onaylı politikada uygun geçici ret. Yalnız-uzak-uç etiketi ama geçerli yakın uç başlangıcı → gerçek giriş korunur. Double-talk + net yakın uç başlangıcı → F1-B tabanı hemen kesinleştirir, anlamsal bekleme yok. Referans eksik yakın uç olasılığı → akustik kanıt, giriş korunur. Çelişen kategoriler/yetersiz kapsam → UNKNOWN ve taban. Önceki generation'a ait geçerli yankı kuyruğu yalnız uygun kapsamlı kanıt.
- **Backchannel:** çıkış sırasında zamanında güvenilir kanıtla "hı hı" → backchannel adayı; devam yalnız onaylı önkesinleştirme noktasından. Çıkış yokken "hı hı" → normal giriş. Yanıt/onay beklenirken "evet" → anlamlı yanıt adayı (onay değil; geri bildirim gibi atılmaz). Çıkış etkinken "bir dakika"/"dur" → kesme adayı korunur. "Tamam tamam" veya "hı hı, hayır" → belirsiz/düzeltme; koşulsuz devam asla. Kesin kesmeden sonra tanınan backchannel yalnız tanılama; generation dirilmez.

### 5.6 F1-B uyumu ve güvenlik

- 64 ms başlangıç onayı ile 800 ms asgari kısmi birikim: varsayılan onaylı başlangıç kesmesi gelecekteki ASR'den bağımsızdır. 250 ms duraklatma son tarihi ile 750 ms ipucu TTL'si: TTL duraklatma son tarihini **uzatamaz**. İsteğe bağlı backchannel erteleme noktası yoksa o alt profil HOLD; F1-B tabanı kullanılabilir. Taze geçerli önkesinleştirme ipucu yalnız danışmadır; gerçek F1-B/M02 politikası doğrular.
- Devam: kesin canlı jeton, son tarihten önce, yalnız hiç talep edilmemiş imleç; F4/F5 tekrar veya DSP sıfırlama yok. Son tarihte/sonra devam reddedilir. Yeni deneme etkinken eski dönem geri çağrısı etkisiz. Bilinmeyen uçuştaki teslim veya boşaltılmış hedefte kör tekrar yok.
- İptal: çıkış generation'ı iptal edilirken yeni giriş sürer; anlamsal gözlemci kuyruktayken oturum kapanışı → kapsam geçersiz, sınırlı temizlik; iptalden sonra yerel tamamlanma bilinmiyorsa M06 kirası tutar/karantina, F1-C bırakmaz.
- **Yalnız-final:** kısmi "evet" veya randevu isteği F3 gönderimi, slot yazması, onay veya araç çağrısı üretmez; talimat benzeri/özel sorgu içeren kısmi LLM/RAG/korunan okuma/TTS/etki üretmez; commit edilmiş randevudan sonra kesme M07 makbuzunu değiştirmez.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F1-C.01 | Ön kontrol ve soy | Çekirdek ve W2 kapıları, dört doğrudan önkoşul, onaylar, kaynak bildirimleri | SC01–SC04 |
| F1-C.02 | Envanter ve sahiplik | Silero/Endpoint/lookback, F1-B, ipucu/bağlam/kanıt noktaları, eski web/telefon | SC05–SC08 |
| F1-C.03 | Sözleşmeler ve konuşma kapsamı | Kesin M01/M02/F2-C final öncesi korelasyon; değiştirilemez özel danışma ve kanıt | SC09–SC16 |
| F1-C.04 | Sabit profil ve bütçeler | M03 etkin değerler, birimler, nicemleme, azami sınır, tazelik, sınırlar ve kipler | SC17–SC22 |
| F1-C.05 | Akustik kanıt birleştirme | F0-B eşlenmiş aralıklar, geçerli örtüşme, referans durumu ve saatler; desteksiz birleştirme reddi | SC23–SC28 |
| F1-C.06 | Anlamsal ipucu alımı | F2-C revizyon, kapsam, yaş, kapsama ve iptal; en yeniyi birleştir, bloklama yok | SC29–SC36 |
| F1-C.07 | Beklenen slot izdüşümü | Yetkili önceki F3-A bağlamı; kişisel değerler çıkarılır; durum/soru/özne doğrulaması | SC37–SC42 |
| F1-C.08 | Türkçe devam kuralları | Sınırlı belirlenimci ipuçları, Unicode duyarlı eşleşme, olumsuzluk ve korumalı değerler | SC43–SC50 |
| F1-C.09 | Uyarlanır endpoint politikası | Tek F1-A düşük dizi kararını genişlet; geçerli kanıttan sınırlı eşik; taban korunur | SC51–SC56 |
| F1-C.10 | Anlamsal son tarihler | Düşük dizi başına değiştirilemez monoton bütçe; ipucuyla sıfırlama yok; sert sınır ve gerçek sessizlik | SC57–SC62 |
| F1-C.11 | Sonlandırma ve örnek bütünlüğü | F1-A kesin kesim/post-roll, tek M02 rezervasyonu/tur/gönderim ve F2-C mühürü | SC63–SC68 |
| F1-C.12 | Yankı farkındalıklı karar | Uzak uç/yakın uç/double-talk temkinli yorum; bilinmeyende taban; yakın uç kaybı yok | SC69–SC74 |
| F1-C.13 | Backchannel sınıflaması | Yanıt, geri bildirim, dur/düzeltme ve bilinmeyen ayrımı; bağlamsal/zamansal doğrulama | SC75–SC80 |
| F1-C.14 | F1-B bütünleşmesi | Gerçek duraklatma son tarihi ve onaylı başlangıç kesmesi korunur; yalnız isteğe bağlı önkesinleştirme ayrımı | SC81–SC84 |
| F1-C.15 | Devam ve kesme yarışları | Kesin jeton/imleç ve terminal çit; F6-B'ye devir; tekrar/uzak iddia yok | SC85–SC88 |
| F1-C.16 | İptal ve yaşam döngüsü | Çıkış iptalini yeni konuşmadan ayır; kapanış/dönem/zaman aşımı temizliği ve M06 sahipliği | SC89–SC91 |
| F1-C.17 | Yalnız-final güvenliği | Kısmiden türetilen okuma, yazma, LLM, TTS veya onay reddi; M07 uzlaştırması korunur | SC92–SC94 |
| F1-C.18 | Kaynak ve telemetri | Kapsam/ipucu/uyanma/kira sınırları; güvenli M04 skaler izdüşüm ve saat anlamı | SC95–SC96 |
| F1-C.19 | Entegrasyon | Tek rota; F0-B/F2-C/F3-A/F6-B ile gerçek F1-A/B orkestrasyonu; sahte sağlayıcılar | SC97–SC98 |
| F1-C.20 | Benchmark korpus protokolü | Katmanlar, etiketler, tabanlar, metrikler, tolerans ve ayrılmış protokol dondurulur; gerçek ölçüm yok | SC99 |
| F1-C.21 | Aşağı akış devri | F3-C/F2-C bağlamı, F1/F6 kontrolü ve M08 kanıtı; desteklenmeyen isteğe bağlı profiller kayıtlı | Devir notu |
| F1-C.22 | Belirlenimci doğrulama | SC01–SC100 ve uygulanabilir önceki testler entegre kaynakta; gerçek sonuçlar | Tüm testler çalıştırılmış |
| F1-C.23 | Regresyon ve geri dönüş | Özellik paydaları, güvenlik regresyonları, önceki paket bütünlüğü, OFF anahtarı | SC100 |
| F1-C.24 | Kabul ve durma | F1-C-G00…G19 bağımsız; kanıt bütünlüğü ve hazırlık; sonraki paket uygulanmaz | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| SC01 | Sahip kodlama yetkisi yok | Ön kontrol HOLD; repo yazması yok |
| SC02 | Çekirdek kapı false veya bayat soy | HOLD; plan asla kabul diye yorumlanmaz |
| SC03 | W2 yalnız `vertical_slice_ready`, WG PASS yok | HOLD; uydurma W2 kabulü yok |
| SC04 | Dört doğrudan bağımlılıktan biri yok | Kesin eksik sahip yapıtıyla HOLD |
| SC05 | Eski ve katı VAD yolları envanteri | Tek mevcut akustik sahip; her özellik eşlenmiş |
| SC06 | Mevcut anlamsal bayrak veya sınıflandırıcı bulunur | Yeniden kullan veya uzlaştır; ikinci otorite yok |
| SC07 | F6-B geçişli bağımlılık ve F3-B isteğe bağlı uyum | DAG değişmez; yeni zorunlu kenar yok |
| SC08 | M01/M02 noktası uyumsuz | Açık sahip değişiklik isteği ve HOLD; sahte sözleşme yok |
| SC09 | `TurnRef`'siz final öncesi konuşma adayı | Yalnız opak konuşma kapsamı; tur oluşturulmaz |
| SC10 | İki oturumda aynı akış kimliği | Oturumlar arası kanıt veya durum yeniden kullanımı yok |
| SC11 | İpucu teslimi sırasında giriş dönemi değişir | Eski ipucu reddedilir; yeni durum sağlam |
| SC12 | Bool veya NaN sayısal üst veri | Bozuk kanıt reddedilir; geri düşme |
| SC13 | Ters veya kabul edilen sesi aşan yarı açık aralık | Geçersiz kapsama reddedilir; sessizlik eklenmez |
| SC14 | Sahte üretici/kaynak başvurusu | Politika yetkisi veya aşağı akış eylemi yok |
| SC15 | Aynı gözlemin yinelenmesi | İdempotent; yeni karar dönemi veya tur yok |
| SC16 | Değiştirilmiş içerikli aynı gözlem kimliği | Çakışma; üzerine yazma veya etki yok |
| SC17 | Anlamsal ipuçlarıyla profil OFF | Eski karar paritesi; ek etki yok |
| SC18 | Negatif son tarih veya sınırsız üst sınır | Yapılandırma reddedilir; son kabul edilen profil korunur |
| SC19 | 32 ms pencerelerle istenen 250 ms asgari | 256 ms'ye nicemlenir; ikisi de raporlanır |
| SC20 | 1200 ms azami tam pencere bütçesi | En fazla 37 pencere/1184 ms; aşma yok |
| SC21 | Asgari bütçeden büyük post-roll | Geçersiz profil reddedilir |
| SC22 | Etkin sözde yapılandırma yeniden yüklemesi | Kabul edilen sınıra kadar sabit politika değişmez |
| SC23 | F0 20 ms blokları ile F1 32 ms penceresi | Gerçek aralıklar birleştirilir; geri çağrı sayısı hizalaması yok |
| SC24 | Yanlış hız/dönemden eşlenmiş F0 kanıtı | Ret veya bilinmiyor; uyumsuz alanlarda aritmetik yok |
| SC25 | Geçerli saat eşlemeli taze örtüşme | Kanıt uygun ama doğru kabul edilmez |
| SC26 | Farklı alanlar için saat eşlemesi yok | Bilinmiyor; uydurma yaş veya hizalama yok |
| SC27 | F0 referansı yok veya geçmiş yetersiz | Yankı etiketi yok; taban kullanılır |
| SC28 | F0 gözlemi VAD penceresini kısmen kapsar | Kapsam sınırlaması kaydedilir; sahte kesinlik yok |
| SC29 | Kabul edilmiş revizyonda taze aynı kapsamlı F2-C ipucu | Yapılandırılmış sınırlarda bir kez uygun |
| SC30 | Tam TTL'de süresi dolan ipucu | Dolumda reddedilir; zamanlayıcı sıfırlanmadan geri düşme |
| SC31 | Önceki konuşma kapsamından ipucu | Ret; durum değişikliği yok |
| SC32 | Sırasız daha eski kısmi revizyon | En son kabul edilmiş ipucunun yerini alamaz |
| SC33 | Yeni revizyonla iptal edilen kararlı önek | Önbellekteki değerlendirme hemen geçersiz |
| SC34 | Güncel sesin ötesinde ipucu kapsamı | Gelecek kanıt reddedilir |
| SC35 | Kabul edilen örnek sonunun çok gerisinde ipucu | Bayat kapsam; geri düşme |
| SC36 | Mühürlü kısmi hattan geç ipucu | Endpoint uzatması veya yeni karar yok |
| SC37 | Önceki kabul edilmiş F3'te beklenen PHONE slotu | Yalnız tür ve revizyon okunur; telefon değeri yok |
| SC38 | F3 bağlamında özne değişimi | Eski bağlam geçersiz; müşteriler arası taşıma yok |
| SC39 | Beklenen slot revizyonu geçersiz kılınmış | Bayat beklenti reddedilir; güvenli geri düşme |
| SC40 | Diyalog bağlamı yok | Korunan arama yok; akustik veya onaylı genel geri düşme |
| SC41 | Tam sunulmamış bekleyen onay sorusu | Yalnız anlamlı yanıt adayı; onay veya çıkarılmış sunum yok |
| SC42 | Güvenilmeyen metin müşteri kimliği veya durum revizyonu iddia eder | Sahte bağlam reddedilir; politika yetkisi yok |
| SC43 | Sondaki "ve" / "ama" fikstürü | Olası devam; kesin bitmemiş söz değil |
| SC44 | Sondaki "çünkü" / "eğer" fikstürü | Tazeliğe bağlı sınırlı devam ipucu |
| SC45 | Beklenen saatle "Saat on dört" | Eksik aday; dakika uydurulmaz |
| SC46 | Kısmi plaka veya telefon rakamları | Yalnız eksik kategori; çıkarılmış rakam yok |
| SC47 | "Qashqai değil, Juke" fikstürü | Olumsuzluk/düzeltme korunur; erken kabul yok |
| SC48 | "Evet ama" fikstürü | Devam/karşıtlık; saf onay veya backchannel değil |
| SC49 | Türkçe noktalamayla Unicode I/ı ve İ/i | Yalnız eşleşme görünümü; kesin ham dokunulmaz |
| SC50 | Yalnız noktalama ve belirsiz jetonlar | UNKNOWN; zorla anlamsal tamamlanma yok |
| SC51 | Tamamlanma ipuçlu onaylı etkin konuşma | Gerçek düşük diziden önce erken kesim yok |
| SC52 | Taze eksik slot + geçerli düşük dizi | Yalnız seçili sınırlı eşik kadar beklenir |
| SC53 | Onaylı bağlamla kısa açık yanıt | Yalnız gerçek geçerli düşük/post-roll sonrası daha erken eşik |
| SC54 | Taban düşük eşikten sonra kullanılabilir ipucu yok | Akustik geri düşme bir kez sonlandırma ister |
| SC55 | Uzatma sırasında taze ipucu geçersizleşir | Güncel gerçek düşük sayısı; taban sağlandıysa sonlandır |
| SC56 | Final talebinden önce gerçek konuşma döner | Aynı kapsam sürer; düşük dizi iptal; geçmiş korunur |
| SC57 | Tekrarlanan daha yeni devam ipuçları | Özgün anlamsal son tarih sıfırlanmaz |
| SC58 | Geçerli düşük örnek olmadan duvar son tarihine ulaşıldı | Uydurma sessizlik/final yok; F1-A takılma politikası |
| SC59 | Kesin örnek eşiği ile sert sınır çakışması | F1-A'ya göre MAX_DURATION önceliği |
| SC60 | Sonlu olmayan skor ve dolgulu kuyruk | İkisi de gerçek sessizlik sayılmaz |
| SC61 | Bekleme sırasında boşluk / dönem süreksizliği | F1 sahibince iptal/sıfırlama; gizli süreklilik yok |
| SC62 | Anlamsal bütçeden önce EOS veya sahip son tarihi | Kabul edilmiş sahip terminal davranışı öncelikli |
| SC63 | Uzatılmış bekleme ama ilk düşük + post-roll kesimi | Final ses kabul edilen kesimde biter; artık uygun geçmiş korunur |
| SC64 | Devam eden konuşmada ön kayıt bir kez | Benzersiz kaynak aralıkları; yinelenen ekleme yok |
| SC65 | İki eşzamanlı endpoint geri çağrısı | Tek atomik final rezervasyonu/tur/gönderim |
| SC66 | Talepte final kuyruğu dolu | Açık ret/geri basınç; sahte tur veya kısmi terfisi yok |
| SC67 | Sonlandırma yeni konuşmayla yarışır | Sahip sıralaması karar verir; yinelenen veya kaybolan aralık yok |
| SC68 | Final mühründen sonra F2-C geç P5 sonucu | Kısmi yayın yok; yerel kira gerçek tamamlanmaya kadar |
| SC69 | Güvenilir eşleşen referanslı yalnız-uzak-uç, inandırıcı yakın uç yok | Yalnız onaylı politikada uygun geçici ret |
| SC70 | Yalnız-uzak-uç etiketi ama geçerli yakın uç başlangıcı | Gerçek giriş korunur; yalnız etikete dayalı bastırma yok |
| SC71 | Double-talk artı net yakın uç başlangıcı | F1-B tabanı hemen kesinleştirir; anlamsal bekleme yok |
| SC72 | Referans eksik olası yakın uç | Akustik kanıt; giriş korunur |
| SC73 | Çelişen akustik kategoriler veya yetersiz kapsam | UNKNOWN ve taban; uydurma güven yok |
| SC74 | Geçerli yankı kuyruğuyla önceki generation'a ait referans | Yalnız uygun kapsamlı kanıt; güncel generation yok |
| SC75 | Güvenilir zamanında kanıtla çıkış sırasında "hı hı" | Backchannel adayı; devam yalnız onaylı önkesinleştirme noktasından |
| SC76 | Etkin çıkış yokken "hı hı" | Normal giriş; çıkış bastırma yok |
| SC77 | Yanıt/onay beklenirken "evet" | Anlamlı yanıt adayı; onay veya otomatik geri bildirim atma değil |
| SC78 | Çıkış etkinken "bir dakika" / "dur" | Kesme adayı ve taban güvenliği korunur |
| SC79 | "Tamam tamam" veya "hı hı, hayır" | Belirsiz/düzeltme; asla koşulsuz devam |
| SC80 | Kesin kesmeden sonra tanınan backchannel | Yalnız tanılama; generation dirilmez |
| SC81 | 64 ms başlangıç ile 800 ms asgari kısmi birikim | Varsayılan onaylı başlangıç kesmesi gelecekteki ASR'den bağımsız |
| SC82 | 250 ms duraklatma son tarihi ile 750 ms ipucu TTL'si | TTL duraklatma son tarihini uzatamaz; zaman aşımı değişmez |
| SC83 | İsteğe bağlı backchannel erteleme noktası yok | O alt profil HOLD; F1-B tabanı kullanılabilir kalır |
| SC84 | Kalan duraklatma/kapasite içinde taze geçerli önkesinleştirme ipucu | Yalnız danışma; gerçek F1-B/M02 politikası doğrular |
| SC85 | Son tarihten önce kesin canlı jetonla devam | Yalnız hiç talep edilmemiş imleç; F4/F5 tekrarı veya DSP sıfırlaması yok |
| SC86 | Duraklatma son tarihinde/sonra devam | Ret; kontrollü zaman aşımı; yeniden açma yok |
| SC87 | Yeni deneme etkinken geç eski duraklatma dönemi geri çağrısı | Yeni hedefe etkisi yok |
| SC88 | Bilinmeyen uçuştaki teslim veya zaten boşaltılmış hedef | Kör tekrar yok; kabul edilmiş F6-B hata politikası |
| SC89 | Yeni giriş sürerken çıkış generation'ı iptal | Giriş kapsamı ve ses geçmişi korunur |
| SC90 | Anlamsal gözlemci kuyruktayken oturum kapanışı | Kapsam geçersiz; sınırlı temizlik; geç çıktı yok |
| SC91 | İptalden sonra yerel tamamlanma bilinmiyor | M06 kirayı tutar veya karantinaya alır; F1-C bırakmaz |
| SC92 | Kısmi "evet" diyor veya randevu istiyor | F3 gönderimi, slot yazması, onay veya araç çağrısı yok |
| SC93 | Kısmi talimat benzeri istem veya özel sorgu içerir | LLM/RAG/korunan okuma/TTS/etki yok |
| SC94 | Commit edilmiş randevu ardından kesme | Kalıcı M07 makbuzu değişmez; uzlaştırma konuşmadan bağımsız |
| SC95 | Dolu medya kuyruğunda ipucu/revizyon/kapsam seli | Sınırlı birleştirme; kontrol açlığı yok; geri düşme |
| SC96 | Zamanlaması bilinmeyen kişisel veri içeren sentetik iz | Yalnız güvenli skaler günlük; bilinmeyen null; saatler arası gecikme iddiası yok |
| SC97 | Sahte yerel sınırlarla web ve telefon gerçek orkestrasyonu | Doğru final ve kesme rotaları; DTMF ve örnek muhasebesi |
| SC98 | OFF/SHADOW regresyonu ve geri dönüş | Eski parite; onaylı bütçe dışında ek yan etki/kısmi iş yok |
| SC99 | Temiz/gürültülü/devam/backchannel katmanlı dondurulmuş benchmark bildirimi | Tüm paydalar, etiketler, eşikler ve ayrılmış küme tanımlı |
| SC100 | Entegre kaynak ve kanıt kurcalama / devir kontrolü | Tüm uygulanabilir gerçek testler/sahip kanıtı gerekli; eksikse PASS yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F1-C-G00 | Ön kontrol | Çekirdek/W2 ve doğrudan önkoşullar; gerçek soy ve onay; SC01–SC04 |
| F1-C-G01 | Tek sahip | Tek F1 sahibi; yinelenen model/kuyruk/oturum yok; envanter ve kip eşlemesi; SC05–SC08 |
| F1-C-G02 | Sözleşme | Özel sözleşme eşlemesi, gerçek kapsam, doğrulama, spekülatif `TurnRef` yok; SC09–SC16 |
| F1-C-G03 | Profil | Sabit M03 yapılandırması, doğru asgari/azami nicemleme ve taban uyumu; SC17–SC22 |
| F1-C-G04 | Akustik kanıt | F0-B eşlenmiş kanıt geçerliliği ve dürüst saat/kapsam; SC23–SC28 |
| F1-C-G05 | İpucu | F2-C en son revizyon, TTL, kapsam, iptal; mühürlü ipucu yok; SC29–SC36 |
| F1-C-G06 | Bağlam | F3-A asgari önceki bağlam, revizyon ve gizlilik; SC37–SC42 |
| F1-C-G07 | Devam kuralları | Sınırlı Türkçe devam ve korumalı anlam; SC43–SC50 |
| F1-C-G08 | Uyarlanır endpoint | Yalnız gerçek akustik kanıtla uyarlanır endpoint; geri düşme; SC51–SC56 |
| F1-C-G09 | Son tarihler | Bağımsız son tarihler ve sert sınır; sentetik sessizlik yok; SC57–SC62 |
| F1-C-G10 | Sonlandırma | Tek final kabulü, post-roll/örnek muhasebesi ve F2-C mühürü; SC63–SC68 |
| F1-C-G11 | Yankı | Yankı/double-talk kanıtı yakın ucu silemez; SC69–SC74 |
| F1-C-G12 | Backchannel | Muhafazakâr backchannel ve anlamlı yanıt koruması; SC75–SC80 |
| F1-C-G13 | F1-B uyumu | F1-B son tarih uyumu ve isteğe bağlı nokta yetenek doğruluğu; SC81–SC84 |
| F1-C-G14 | Devam/kesme | Kesin aynı generation devamı, kesme ve bayat jeton yarış güvenliği; SC85–SC88 |
| F1-C-G15 | İptal | Çıkış/giriş iptal yalıtımı; gerçek yerel sahiplik; SC89–SC91 |
| F1-C-G16 | Yalnız-final | Yalnız-final M07 etkileri ve uzlaştırma; sınırlı kaynaklar ve gizlilik; SC92–SC96 |
| F1-C-G17 | Test kanıtı | SC01–SC100 gerçek kanıt ve zorunlu önceki testler; sahte PASS yok |
| F1-C-G18 | Regresyon | Entegre eski regresyon, geri dönüş ve dondurulmuş benchmark protokolü; SC97–SC99 |
| F1-C-G19 | Devir | Bağımsız inceleme, bildirim bütünlüğü, gerçek hazırlık ve devir; SC100 |

## 9. Kanıt

`evidence/F1-C/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F1_C_INVENTORY.json`, `PROFILE_QUANTIZATION.md`, `EVIDENCE_JOIN_SPEC.md`, `HINT_INTAKE_SPEC.md`, `TURKISH_CONTINUATION_RULES.md`, `ADAPTIVE_ENDPOINT_POLICY.md`, `BACKCHANNEL_MATRIX.csv`, `BENCHMARK_PROTOCOL.md` (erken kesim/geç kesim oranı, yanlış kesme, backchannel doğruluğu — G4/G5), `TEST_MATRIX.json`.

## 10. Geri dönüş

`f1.semantic_endpoint=OFF`: F1-A/F1-B akustik tabanı tek aktif. Kod `git revert`.

## 11. Devir

- **G2/G4/G5:** kısa endpoint p95 ≤ 500 ms, yanlış söz kesme ≤ %2 hedefleri; gerçek konuşma kayıt protokolü (eski F1-T29) ve kabul (eski F1-T30).
- **F3-C:** beklenen slot bağlamı çoklu niyet planlayıcısından da gelebilir; arayüz (yalnız tür + revizyon) değişmez.
- **F2-C:** ipucu sözleşmesi geri bildirimleri.

## 12. Başlatma komutu

```
F1-C paketini uygula: docs/execution/packages/W4/F1-C-anlamsal-tur-sonu.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F1-B, F2-C, F3-A ve F0-B kabulünü doğrula; benchmark korpusunu dondur.
F1-A tek karar sahibi içinde F0-B kanıtı, F2-C ipucu ve F3-A slot türüyle sınırlı uyarlanır endpoint, Türkçe devam kuralları,
yankı farkındalığı ve muhafazakâr backchannel'ı f1.semantic_endpoint (varsayılan OFF) altında kur; gerçek sessizlik olmadan kesme.
SC01–SC100'ü çalıştır, F1-C-G00…G19'u değerlendir, paket/F1-C dalında PR aç ve dur.
```
