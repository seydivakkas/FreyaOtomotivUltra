# F5-B — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma

> F5-A'nın sentez çekirdeğini güvenilir ölçeğe taşır: öğe başına RNG (toplu işte komşudan bağımsız gürültü), dolgudan önce gerçek uzunlukta latent çekimi, maske ve dolgu doğrulaması, öğe başına VAE çözümü, sürümlü önbellek kimliği, kişisel veri için varsayılan önbellek bypass'ı, sınırlı önbellek kapasitesi ve geçersiz kılma, yapısal kalite koruması ve **aynı seed ile en fazla bir** yeniden deneme. Yeni model, yeni çözücü veya yeni aktarım yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F5-B |
| Dalga | W3 |
| Öncelik | P0 |
| Önkoşullar | W2_GATE, F5-A, M03, M06 |
| Sonraki | F5-C, F6-C |
| Bayrak | `f5_pipeline_v2` + M03 profilleri `f5.batch_isolation`, `f5.cache`, `f5.recovery` (varsayılan kapalı; özel önbellek ayrıca kapalı) |
| Ortam | CPU (sahte yerel sağlayıcı, sahte saat); gerçek GPU doğrulaması G4 |
| Eski görevler | F5-T12, F5-T13, F5-T14, F5-T15, F5-T20, F5-T21, F5-T25 |
| Kaynak | Bundle `W3/Freya_2_0_F5_B_Agent_Implementation_Package.md`; [F5 spec](../../../stages/F5-neural-synthesis/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Toplu sentezde bir öğenin gürültüsü komşusunun uzunluğuna veya sırasına bağlı olursa aynı cümle farklı seslenir ve Leyla kimliği kayar. Önbellek yanlış anahtarla eski sesi verirse yanlış bilgi okunur; kişisel veri önbellekte kalırsa KVKK ihlali olur. F5-B bu riskleri kapatır; ODE profil karşılaştırması ve kimlik doğrulama F5-C'dedir.

## 2. Başlamadan önce

- [ ] W2_GATE, F5-A, M03, M06 kabul edilmiş; onay; uyumlu soy.
- [ ] RNG, latent, toplu iş, VAE, önbellek, koruma, doğrudan TTS ve deneysel yollar envanterde; tek toplu iş oluşturma/gönderme otoritesi (M06) izlenmiş.
- [ ] Sağlayıcının maske eksenleri/kutupluluğu ve RNG yalıtım yeteneği kaynaktan doğrulanmış; doğrulanamıyorsa ilgili katı toplu profil HOLD (küresel kilitle "güvenli" taklidi yapılmaz).
- [ ] Ses profilleri (eski F5-T13) M03 kaydındadır; bu paket profili **bağlar**, yeni profil oluşturmaz. Ön ısıtma (eski F5-T15) mevcut davranışıyla korunur ve M06 P6 sınıfına bağlanır; yeni ısıtma etkinleştirilmez.

## 3. Kapsam

**Yapılacak:** Sahiplik ve geçiş; sözleşme ve kabul eşlemesi; sabitlenmiş yürütme şartnamesi; RNG yalıtımı; gerçek uzunlukta latent; toplu iş uyumu ve bütçe; dolgu ve maske; VAE dolgu kaldırma; önbellek kimliği; gizlilik uygunluğu; önbellek kapasitesi ve yaşam döngüsü; önbellek geçersiz kılma; süre ve kalite koruması; aynı seed'le kurtarma; M06 yürütme kirası; M02 çıkış kabulü; F6 bağlantısı ve geri basınç; telemetri; F5-C devri.

**Yapılmayacak:** ODE adım profili karşılaştırması, kod çözücü optimizasyonu, speaker encoder ve kimlik eşiği, drift (F5-C); LoRA (F5-D); yeni ses profili; insan değerlendirmesi; gerçek akustik kalite iddiası.

## 4. Dosyalar

```
backend/neural_synthesis/
  execution_spec.py  rng_isolation.py  latent_length.py  batch_compat.py  masking.py
  vae_unpad.py  cache/  key.py  privacy.py  capacity.py  invalidation.py  store.py
  quality_guard.py  recovery.py  completion_lease.py  output_admission.py  f6_handoff.py
tests/neural_synthesis/batch/  tests/neural_synthesis/cache/
evidence/F5-B/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 RNG ve gerçek uzunluk

- Öğe başına üreteç; tam çekim envanteri. Aynı profil ve seed'le iki tekil çağrı aynı gerçek uzunluk gürültüsünü verir (orkestrasyon testi). İki üyeli toplu işte sıra ters çevrilse, komşunun seed'i veya uzunluğu değişse bile sabit öğenin gürültüsü değişmez. Aynı seed'li eşzamanlı oturumlar bağımsız; küresel seed değişmez.
- Leyla seed 9 (M03'ten) ve açık 42/77/123 korunur; yeni varsayılan enjeksiyonu yok; eksik/bool seed reddedilir.
- Süre kestirici sonlu ve bilinen uzunlukta gerçek yuvarlama ve şekil verir; negatif/sıfır/NaN/sonsuz süre veya hız, şekil çarpımı taşması → tahsisten önce ret. Karışık 4 ve 7 uzunluk fikstüründe her RNG kendi şeklinde, belirlenimci dolgudan **önce** çekilir. Yalnız belgeli güvenli kırpma; aksi halde hata/yeniden planlama, metin değişmez.

### 5.2 Toplu iş, maske, VAE

- Uyumsuz çözücü/dtype veya model/ses koşullandırması aynı toplu işe girmez. Dolgulu tepe bütçeyi aşarsa M06 oluşturma sırasında böler/reddeder. İlk parça P2, sonrakiler P4; ek mikro bekleme yok.
- Maske eksenleri ve kutupluluğu bilinen fikstürde doğru; sağlayıcı desteği bilinmiyorsa katı toplu iş HOLD. Dolgu anahtarlarına dikkat sızıntısı, ODE ara adımlarında dolgu kirlenmesi ve konum/koşullandırma sızıntısı testlerle kontrol edilir. Düzen dondurulduktan sonra bir üye iptal edilirse yeniden indeksleme/yeniden seed yok.
- VAE gerçek dolgusuz latenti alır; toplu çözmede sınır sızıntısı varsa toplu çözme desteklenmez (gizlemek için kırpma yok). Çıktı kimlikle eşlenir; eksik/yinelenen/yabancı kimlik reddedilir. 48 kHz mono Float32, N = 96 000 örnek = 384 000 bayt = 2 000 ms; yeniden örnekleme yok; yanlış hız/stereo/belirsiz eksen reddedilir; meşru kod çözücü kuyruğu korunur (sessizliğe göre kırpma yok).

### 5.3 Önbellek

| Konu | Kural |
| --- | --- |
| Kimlik | Sürümlü etkin davranış tanımlayıcısı + kanonik serileştirme: model/VAE/kodlayıcı/dağarcık revizyonu, seed, ses koşullandırması, çözücü/zaman ızgarası/RNG/dtype/düzen, F4 etkin kural/sözlük/model kontrol revizyonu. Değişen her alan farklı kimlik (veya kanıtlanmış eşdeğerlik). Çakışma/belirsiz serileştirme/eksik zorunlu alan → ret/karantina/bypass; tam tanımlayıcı karşılaştırılır |
| Gizlilik | **Varsayılan bypass.** Paylaşılan önbellek yalnız güvenilir politikayla onaylı statik kişisel olmayan şablonlar (regex tek başına yetmez). Telefon/plaka/VIN/ad/randevu içeren metin paylaşılan önbelleğe girmez, özeti dışa verilmez. Kökeni bilinmeyen genel metin bile bypass. Özel önbellek varsayılan kapalı; açıkça onaylı özel kapsamda başka oturum aynı metinle isabet alamaz; iptal edilen/kapanan kapsamda arama hemen geçersiz, tutulan baytlar bırakılana kadar sayılır |
| Kapasite | Sayı/bayt/TTL/ödünç alan sınırları; atomik rezervasyon; bayt sınırını aşan girdi tahsisten önce atlanır; TTL sahte monoton saatle; ödünçteki yük tahliyede aramadan çıkar ama baytları bırakılana kadar sayılır; bekleyen/kopya/çalışma alanı sınırı → sınırlı ret; aynı kapsamlı yinelenen istek tek mantıksal talep (paylaşılan birleştirme ayrıca onaylanmadıkça kapalı) |
| Geçersiz kılma | Kalite politikası revizyonu değişince MISS veya açık onaylı yeniden doğrulama; yalnız F6 duraklaması değişirse ham kimlik değişmez (model etkisi yoksa), duraklama üst verisi tazelenir; ilgisiz arayüz ayarı kimliği değiştirmez; eski generation sabit plana bağlı kalır; bozulmuş girdi/bütünlük hatası → HIT teslimi yok, karantina; önbellek doldurma sıralanmadan önce iptal kazanırsa bayat yazma yok |

### 5.4 Kalite koruması ve kurtarma

- Yapısal: boş/tek bayt sayısı/yanlış sayı, NaN/Inf → önbellek/depolama/teslimden önce ret, onarım yok. Tamamen sıfır konuşma → çökme koruması reddeder. Neredeyse sabit/tekrarlı dalga → yapılandırılmış sınırlı sezgisel tespit (etiketli fikstür; gerçek akustik iddia yok). Meşru sessiz kısa konuşma fikstürü toptan reddedilmez; sınırlar raporlanır. Tahmini süre farklı ama gerçek uzunluk geçerliyse gerçek N/hız raporlanır; zorla kırpma yok. Kalibre sezgisel eşik yoksa geliştirilmiş politika `UNKNOWN/HOLD`, yapısal kontroller çalışır. Sonlu tepe nominal aralık dışındaysa gerçek onaylı sözleşme; sabit kodlu kırpma veya F6 DSP'si yok.
- Kurtarma: geçici onaylı hata + yerel terminal kanıtlanmış → **en fazla bir** yeni kabul, aynı plan/seed/ayarlar. Belirlenimci yeniden denenemez hata → ikinci deneme yok. Yeniden deneme de başarısız → açık terminal hata; üçüncü yasak. Deneysel seed başarısızlığında aynı seed veya hata; asla Leyla 9'a geri düşme. OOM/zaman aşımı ve yerel tamamlanma bilinmiyor → M06 karantinası; uzlaştırılana kadar yeniden deneme yok. Kurtarma için çözücü/süre/model değişmesi gerekiyorsa aynı plan reddedilir; yalnız yeni yetkili revizyon. Zaten kabul edilmiş veya belirsiz önceki çıktıda yeniden deneme/yinelenen teslim yok.

### 5.5 Kira, teslim ve F6

Toplu iş sırasında bir öğe iptal edilir, komşusu güncel kalır → bayat öğe bastırılır, komşu korunur, ortak kira terminale kadar. CUDA bitmeden ana makine dönüşü → kira doğrulanmış terminal/CPU somutlaştırmasına kadar. Doğrulanmış CPU sonucu F6 kapasitesine takılırsa yürütme kirası gerçek bitişte bırakılabilir; sahipli CPU tamponu sınırlı kalır. Aynı generation'da yumuşak duraklat/devam → yeniden seed veya yeniden sentez yok. Kalite ile yayın arasında kesin kesme → M02 eski parçayı reddeder, yalnız onun kaynaklarını bırakır. Yeni generation'da doğrulanmış önbellek isabeti → yeni M01 zarfı, yerel çağrı yok, eski generation/zaman yok. Eksik önceki veya yinelenen parça geri çağrısı → sıra dışı/yinelenen yayın yok.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F5-B.01 | Ön kontrol | Çekirdek/W2/F5-A/M03/M06 gerçek kabul yapıtları, onay, uyumlu soy | `PREFLIGHT`; RQ01–RQ04 |
| F5-B.02 | Sentez ve önbellek envanteri | RNG, latent, toplu iş, VAE, önbellek, koruma, doğrudan TTS ve deneysel yollar | `INVENTORY`; RQ05–RQ08 |
| F5-B.03 | Sahiplik ve geçiş | Mevcut F5/M06 sahibi; onaylı değişiklikler ve güvenli etkinleştirme profilleri; çift yükleyici yok | Karar kaydı |
| F5-B.04 | Sözleşme ve kabul | M01/M02/M03/M06 ve değiştirilemez F4 planı; hazır kodlayıcı yeniden normalize etmez | `PLAN_EXECUTION_MAPPING`; RQ09–RQ16 |
| F5-B.05 | Sabit yürütme şartnamesi | Gerçek etkin ayarlar, model/ses/dağarcık ve seed; bilinmeyen zorunlu kimlik reddi | `EXECUTION_PROFILE_MATRIX`; RQ17–RQ18 |
| F5-B.06 | RNG yalıtımı | Öğe başı üreteç, tam çekim envanteri; taban ve açık deney seed'leri korunur | `RNG_ISOLATION_SPEC.md`; RQ19–RQ24 |
| F5-B.07 | Gerçek uzunlukta latent | Süre ve şekil koruması; dolgudan önce çekim; kesin seed ve çekim sırası | `LATENT_LENGTH_SPEC.md`; RQ25–RQ32 |
| F5-B.08 | Toplu iş uyumu ve bütçe | M06 toplu iş sahibi; dolgulu tepe, üye kimlikleri; ikinci bekleme yok | `BATCH_COMPATIBILITY_MATRIX`; RQ33–RQ36 |
| F5-B.09 | Dolgu ve maske | Gerçek eksenler/kutupluluk ve sağlayıcı desteği; belirlenimci yalıtım veya HOLD | `MASK_CAPABILITY_SPEC.md`; RQ37–RQ42 |
| F5-B.10 | VAE dolgu kaldırma | Gerçek uzunlukta VAE çözümü, gerçek dalga uzunlukları, üye eşlemesi; ham DSP yok | `VAE_UNPADDING_SPEC.md`; RQ43–RQ48 |
| F5-B.11 | Önbellek kimliği | Sürümlü etkin davranış tanımlayıcısı ve kanonik serileştirme; çakışma tespiti | `CACHE_KEY_SCHEMA`; RQ49–RQ54 |
| F5-B.12 | Gizlilik uygunluğu | Varsayılan bypass; yalnız güvenilir genel şablonlar; isteğe bağlı oturuma kapalı önbellek | `CACHE_PRIVACY_POLICY`; RQ55–RQ60 |
| F5-B.13 | Önbellek kapasitesi | Sayı/bayt/TTL/ödünç alan sınırları, atomik rezervasyon, tutulan bayt, tahliye | `CACHE_CAPACITY_SPEC`; RQ61–RQ66 |
| F5-B.14 | Önbellek geçersiz kılma | Revizyon değişimi, süre/iptal, atomik arama, bayat yazma koruması | `CACHE_INVALIDATION_MATRIX`; RQ67–RQ72 |
| F5-B.15 | Süre ve kalite koruması | Onaylı koruma; sınırlı sonluluk/şekil/sessizlik/çökme kontrolleri; açık kanıt ve eşikler | `QUALITY_POLICY_MATRIX`; RQ73–RQ80 |
| F5-B.16 | Aynı seed'le kurtarma | Tipli yeniden deneme politikası; en fazla bir ek; seed/profil ikamesi yok; tekrar yok | `RECOVERY_DECISION_MATRIX.csv`; RQ81–RQ87 |
| F5-B.17 | M06 yürütme kirası | Paylaşılan toplu iş terminali, karantina, CPU devri ayrımı, yeniden kabul | `COMPLETION_LEASE_SPEC.md`; RQ88–RQ90 |
| F5-B.18 | M02 çıkış kabulü | İsabet ve ıskada taze kapsamlı `AudioChunk`; ardışık teslim, bayat bastırma | `DELIVERY_SPEC.md`; RQ91–RQ94 |
| F5-B.19 | F6 bağlantısı ve geri basınç | CPU yükü kabul edilmiş F6 noktasına; duraklat/kesme/kapasite anlamı; yeni aktarım yok | `F6_HANDOFF_SPEC` |
| F5-B.20 | Telemetri ve gizlilik | Güvenli metrikler ve sahte kanıt; tüm kipler ve hata maskeleme korunur | `TELEMETRY_MAPPING.csv`; RQ95–RQ96 |
| F5-B.21 | F5-C devri | Sayısal profil, önbellek kimliği, koruma ve yeniden deneme tabanları, desteklenmeyen yetenekler | `DOWNSTREAM_HANDOFF.md` |
| F5-B.22 | Belirlenimci doğrulama | RQ01–RQ100 gerçek kabul edilmiş sahipler ve M08 sınırlarıyla; başarısız vakalar saklanır | `FIXTURE_MANIFEST` |
| F5-B.23 | Regresyon, geri dönüş, benchmark | Kapsamlı taban/özellik regresyonları, yalıtılmış geri dönüş, gelecek karşılaştırma protokolü | RQ97–RQ99 |
| F5-B.24 | Kabul ve durma | F5-B-G00…G19 ve bağımsız inceleme; gerçek durum; F0-B'den önce dur | RQ100; `ACCEPTANCE_MATRIX` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| RQ01 | W2 PASS yok veya yalnız hazırlık bayrağı | Düzenlemeden önce HOLD; görev başlamaz |
| RQ02 | F5-A kabul kaynak hash'i uyuşmazlığı | Açık uyumlu soy incelemesine kadar HOLD |
| RQ03 | Gerçek M03/M06 kabulü yok | HOLD; önkoşul uygulanmaz veya ikame edilmez |
| RQ04 | Onay yok veya yalnız plan durumu | Kaynak, yapılandırma, önbellek veya model yazması yok |
| RQ05 | Tüm doğrudan TTS/eski/ısıtma/deney yollarının envanteri | Her gözlenen özellik kimliği ve atlama sınıflanır; uydurma sağlayıcı yok |
| RQ06 | Sahte yerel tuzakla modül içe aktarma | İçe aktarmada model yükleme, ağ, işçi, önbellek doldurma veya GPU yok |
| RQ07 | Mevcut toplu iş sahibi ve zamanlayıcı izlenir | Tam bir oluşturma/gönderme otoritesi; ikinci zamanlayıcı yok |
| RQ08 | Gölge ve güvensiz eski atlama fikstürü | Ek yerel iş/önbellek değişikliği yok; güvensiz etkinleştirme HOLD |
| RQ09 | Kesin hazır metinli geçerli değiştirilemez F4 planı | Kodlayıcıya aynı baytlar; normalizasyon casusu F4'te bir, F5'te sıfır |
| RQ10 | Plan normalizasyon sayısı 2 veya katı yolda bilinmiyor | Önbellek/yerel gönderimden önce ret |
| RQ11 | İç içe parça veya görüntü değişikliği denemesi | Reddedilir veya sabit yürütmeye etkisiz |
| RQ12 | Yanlış model/dağarcık/yetenek revizyonlu plan | Ret veya HOLD; geri düşme yok |
| RQ13 | Eksik seed veya bool seed | Ret; varsayılan enjeksiyonu yok |
| RQ14 | Konuşma yok planı | GPU/önbellek konuşma üretimi yok; açık yanıt yok yolu |
| RQ15 | Yinelenen mantıksal parça talebi | Tek uygun deneme zinciri ve tek sonuç teslimi |
| RQ16 | Girişte bayat oturum/tur/generation | Arama/gönderimden önce ret |
| RQ17 | Leyla onaylı varsayılan seed fikstürü | M03 gerçek seed 9 yeni varsayılan olmadan korunur |
| RQ18 | Açık seed 42/77/123 | Her gerçek üreteç kendi seed'ini kullanır; sessiz 9 yok |
| RQ19 | Aynı profilli iki tekil sahte üreteç çağrısı | Aynı gerçek uzunluk başlangıç gürültüsü; yalnız orkestrasyon testi |
| RQ20 | İki üye sırası ters | Aynı öğe başı başlangıç gürültüsü ve üye eşlemesi |
| RQ21 | Komşu üyenin seed'i değişir | Diğer üyenin gürültüsü değişmez |
| RQ22 | Komşu üyenin uzunluğu değişir | Sabit öğenin gerçek gürültüsü değişmez |
| RQ23 | Aynı seed'li eşzamanlı oturumlar | Bağımsız üreteçler; oturumlar arası durum veya küresel seed değişikliği yok |
| RQ24 | Yalıtım kanıtı olmadan yalnız küresel RNG'li sağlayıcı | Etkilenen katı toplu iş HOLD; küresel kilitle güvenlik taklit edilmez |
| RQ25 | Bilinen uzunlukta sonlu süre kestirici | Beklenen gerçek yuvarlama ve gerçek şekil; tahmini latent oranı yok |
| RQ26 | Negatif/sıfır konuşma süresi | Latent tahsisinden önce ret |
| RQ27 | NaN/sonsuz süre veya hız | Ret; tipli güvenli hata |
| RQ28 | Şekil çarpımı taşması veya aşırı latent uzunluğu | Tensör tahsisi veya GPU atlaması yok |
| RQ29 | Karışık gerçek uzunluk 4 ve 7 fikstürü | Her RNG kendi şeklinde, belirlenimci dolgudan önce çekilir |
| RQ30 | Parça seed türetimi eski fikstürü | Gerçek onaylı politika korunur; istenen/etkin köken açık |
| RQ31 | GPU süre kestirici yolu | Yerel kestiriciden önce kira alınır; dolgulu tahsis rezervasyon içinde |
| RQ32 | Onaylı kırpma ile güvensiz kesme | Yalnız belgeli güvenli kırpma; aksi halde hata/yeniden planlama; metin değişmez |
| RQ33 | Uyumsuz çözücü veya dtype üyeleri | Karışık toplu iş yok; ayrı uygun kabul veya ret |
| RQ34 | Model/ses koşullandırma uyumsuzluğu | Uyum anahtarı ayırır; latent paylaşımı yok |
| RQ35 | Küçük gerçek toplamlara rağmen dolgulu tepe bütçeyi aşar | M06 oluşturmada böler/reddeder; tahsis yok |
| RQ36 | Yük altında ilk ve sonraki parçalar | P2/P4 eşlemesi; ek mikro bekleme yok; sınırlı bekleyen |
| RQ37 | Bilinen maske ekseni ve kutupluluk fikstürü | Doğru jeton ve latent maskeleri; geçerli uzunluklar ayrı |
| RQ38 | Bilinmeyen sağlayıcı maske desteği | Katı toplu iş HOLD; sahte API gerçek kanıt değildir |
| RQ39 | Dikkat fikstürüne dolgu işareti enjeksiyonu | Geçerli sorgu dolgulu anahtarlara dikkat etmez; koruma ihlali tespit eder |
| RQ40 | ODE ara adım dolgu kirlenmesi fikstürü | Gerekli adımlarda maske davranışı kontrol edilir; geçersiz profil reddedilir |
| RQ41 | Konum/koşullandırma sızıntısı testi | Komşu uzunluğu öğe koşullandırmasını onaylı sayısal sözleşmenin ötesinde değiştiremez |
| RQ42 | Düzen dondurulduktan sonra bir üye iptali | Yeniden indeksleme/seed yok; kalan üye kimliği korunur |
| RQ43 | VAE dolgusuz gerçek latenti alır | Öğe başı gerçek şekil doğrulanır; geçersiz dolgu çözümü yok |
| RQ44 | Dolgulu kod çözücü sınır sızıntısı fikstürü | Desteklenmeyen toplu çözme reddedilir; yapıtı gizlemek için kırpma yok |
| RQ45 | Yeniden sıralanmış kod çözücü çıktı kimlikleri | Doğrulanmış kimlikle eşleme; eksik/yinelenen/yabancı kimlik reddi |
| RQ46 | 48k mono Float32 yük N=96000 | 384000 bayt ve 2000 ms; yeniden örnekleme yok |
| RQ47 | Yanlış hız/stereo veya belirsiz toplu eksen | Ret; düzleştirme, downmix veya yeniden etiketleme yok |
| RQ48 | Meşru kod çözücü kuyruğu ile dolgu | Gerçek geçerli örnekler korunur; sessizliğe dayalı kırpma yok |
| RQ49 | Aynı onaylı kesin genel tanımlayıcı | Kararlı kanonik kimlik; doğrulamadan sonra isabete uygun |
| RQ50 | Model/VAE/kodlayıcı/dağarcık revizyonu değişir | Farklı kimlik; bayat isabet yok |
| RQ51 | Seed veya gerçek ses koşullandırması değişir | Farklı kimlik; ikame yok |
| RQ52 | Çözücü/zaman ızgarası/RNG/dtype/düzen değişir | Farklı kimlik veya açık kanıtlanmış eşdeğerlik; aksi halde bypass |
| RQ53 | F4 etkin kural/sözlük/model kontrol revizyonu değişir | Geçmiş metin/seed anahtarı eşleşse bile farklı kimlik |
| RQ54 | Anahtar çakışması, belirsiz serileştirme, eksik zorunlu alan | Ret/karantina veya bypass; tam tanımlayıcı karşılaştırılır |
| RQ55 | Onaylı statik kişisel olmayan şablon | Güvenilir politikayla paylaşılan uygunluk; yalnız regex değil |
| RQ56 | Kişisel metin (telefon/plaka/VIN/ad/randevu) | Paylaşılan BYPASS; dışa verilen özet yok |
| RQ57 | Genel metne rağmen bilinmeyen köken | Varsayılan BYPASS |
| RQ58 | Özel önbellek varsayılan kapalı | Kişisel önbellek tahsisi yok |
| RQ59 | Açık onaylı özel kapsam, aynı metinle başka oturum | Oturumlar arası isabet veya birleştirme yok; yalnız güncel kapsam |
| RQ60 | Ödünç alanı olan iptal edilmiş/kapanmış özel kapsam | Arama hemen geçersiz; tutulan baytlar bırakılana kadar sayılır |
| RQ61 | Girdi bayt sınırını aşar | Tahsisten önce ekleme atlanır; geçerli çıktı devam edebilir |
| RQ62 | Eşzamanlı eklemede girdi sayı/bayt sınırı | Atomik muhasebe; aşırı abonelik yok |
| RQ63 | Sahte monoton saatte TTL dolar | Arama MISS; duvar saati uzatması yok |
| RQ64 | Ödünç alınmış değiştirilemez yükün tahliyesi | Aramadan çıkar; tutulan baytlar bırakılana kadar sayılır |
| RQ65 | Bekleyen/kopya/çalışma alanı sınırı tükendi | Sınırlı ret/geri basınç; gizli kuyruk veya sınırsız görev yok |
| RQ66 | Yinelenen eşzamanlı aynı kapsamlı istek | Mantıksal talep tekilleşir; çoklu sonuç yok; paylaşılan birleştirme ayrıca onaylanmadıkça kapalı |
| RQ67 | Kalite politikası revizyonu değişir | MISS veya açık onaylı yeniden doğrulama; bayat PASS yok |
| RQ68 | Yalnız F6 duraklaması değişir, model metni/davranışı aynı | Model etkisi yoksa ham kimlik değişmez; taze duraklama üst verisi |
| RQ69 | İlgisiz arayüz yapılandırması değişir | Kanıtlanmış ilgisizlikte sahte davranış kimliği değişimi yok |
| RQ70 | Eski generation sabitken yeni M03 görüntüsü | Eski plan değişmez; yeni revizyon uyumsuz girdiyi kullanamaz |
| RQ71 | Önbellek girdisi bozulması veya bütünlük kontrolü hatası | HIT teslimi yok; karantina ve yetkili olağan ıska yolu |
| RQ72 | İptal önbellek doldurma sıralanmasından önce kazanır | Bayat önbellek yazması veya bayat yayın yok |
| RQ73 | Boş, tek bayt uzunluklu veya yanlış sayılı çıktı | Önbellek/depolama/teslimden önce ret |
| RQ74 | Ham örnekte gömülü NaN veya sonsuz | Ret; onarım/normalizasyon yok |
| RQ75 | Tamamen sıfır boş olmayan konuşma fikstürü | Onaylı çökme koruması reddeder; sahte sessizlik oynatması yok |
| RQ76 | Neredeyse sabit/tekrarlı dalga test fikstürü | Yapılandırılmış sınırlı sezgisel etiketli hatayı bulur; gerçek akustik iddia yok |
| RQ77 | Meşru sessiz kısa konuşma biçimli fikstür | Onaylı fikstür eşiğinde toptan yanlış ret yok; sınırlar raporlanır |
| RQ78 | Tahmini süre farklı ama gerçek uzunluk geçerli | Gerçek N/hız raporlanır; onaylı eşik uygulanır; zorla kırpma yok |
| RQ79 | Kalibre sezgisel eşik yok | Etkilenen geliştirilmiş politika UNKNOWN/HOLD; yapısal kontroller çalışır |
| RQ80 | Nominal aralık dışında geçerli sonlu tepe | Gerçek onaylı sözleşme; sabit kodlu kırpma veya F6 DSP'si yok |
| RQ81 | Geçici onaylı hata, yerel terminal kanıtlanmış | En fazla bir yeni kabul; aynı plan/seed/etkin ayarlar |
| RQ82 | Belirlenimci yeniden denenemez hata | İkinci yerel deneme yok |
| RQ83 | İlk hatadan sonra yeniden deneme de başarısız | Açık terminal hata; üçüncü deneme yasak |
| RQ84 | Alternatif deney seed'i hatası | Aynı seed'le yeniden deneme veya hata; asla Leyla 9'a geri düşme |
| RQ85 | Yerel tamamlanma bilinmeyen OOM / zaman aşımı | M06 karantinası; gerçek terminal uzlaştırılana kadar yeniden deneme yok |
| RQ86 | Kurtarma değişen çözücü/süre/model gerektirir | Aynı plan yeniden denemesi reddedilir; yalnız yeni yetkili revizyon |
| RQ87 | Zaten kabul edilmiş veya belirsiz önceki çıktı | Yeniden deneme veya yinelenen parça teslimi yok |
| RQ88 | Yerel toplu iş sırasında iptal; bir komşu güncel | Bayat öğe bastırılır; komşu korunur; ortak kira terminale kadar |
| RQ89 | CUDA bitmeden ana makine dönüşü fikstürü | Kira doğrulanmış terminal/CPU somutlaştırmasına kadar tutulur |
| RQ90 | Doğrulanmış CPU sonucu F6 kapasitesine takılır | Yürütme kirası gerçek bitişten sonra bırakılabilir; sahipli CPU tamponu sınırlı kalır |
| RQ91 | Yumuşak duraklatma sonra aynı generation devamı | Yeniden seed veya yeniden sentez yok; kabul edilmiş sonuç sınırlar içinde tutulur |
| RQ92 | Kalite ile yayın arasında kesin kesme | M02 atomik çiti eski parçayı reddeder; yalnız onun kaynaklarını bırakır |
| RQ93 | Yeni generation'da doğrulanmış önbellek isabeti | Yeni M01 zarfı; eski generation/zaman yok; yerel çağrı yok |
| RQ94 | Eksik önceki veya yinelenen parça geri çağrısı | Sıra dışı veya yinelenen yayın yok; tipli hata/temizlik |
| RQ95 | Metin/ses/latent/anahtar/hatada kişisel veri işaretleri | Metrik/günlük/kanıt/paylaşılan önbellekte ham veya türetilmiş özel kimlik yok |
| RQ96 | Önbellek isabet/ıska ve sahte saat metrikleri | Kapsam/payda doğru; isabette yerel çıkarım metriği null; sahte gerçek ölçüm değil |
| RQ97 | Sahte modelle gerçek kabul edilmiş F4/F5/M02/M06/F6 noktaları | Tek normalizasyon, tek toplu iş sahibi, doğrulanmış ham ses, çitli teslim |
| RQ98 | Eski doğrudan TTS/önbellek/A-B/toplu iş ve deney regresyonu | Yetkili kapsamda gerçek taban davranışı korunur; güvensiz yol HOLD |
| RQ99 | Geri dönüş fikstürü ve önceki bildirimler | Yalnız sahipli değişiklikler; ağırlık/özel veri/toptan önbellek silme yok; önceki plan hash'leri sağlam |
| RQ100 | Eksik/başarısız/çalıştırılmamış testli kapı raporu | Uydurma PASS yok; bağımsız gözden geçiren; hazırlık false; sonraki paketten önce dur |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F5-B-G00 | Ön kontrol | Gerçek çekirdek/W2 ve F5-A/M03/M06 kabulü, onay, uyumlu kaynak; RQ01–RQ04 |
| F5-B-G01 | Tek sahip | Tek model, F5, önbellek ve M06 toplu iş sahibi; güvensiz atlama yok; RQ05–RQ08 |
| F5-B-G02 | Plan | M01/M02 değiştirilemez hazır plan ve tek mantıksal talep; RQ09–RQ16 |
| F5-B-G03 | Profil | Sabit M03 kesin ses/model/seed/etkin profil; RQ09–RQ19 |
| F5-B-G04 | RNG | Öğe başı RNG ve sıra/komşu yalıtımı; gerçek yetenek sınırları; RQ17–RQ24 |
| F5-B-G05 | Süre | Süre koruması ve gerçek uzunlukta denetimli tahsis; RQ25–RQ32 |
| F5-B-G06 | Toplu iş | Tek M06 sahibi altında uyumlu toplu iş ve dolgulu bütçe; RQ33–RQ36 |
| F5-B-G07 | Maske | Doğrulanmış maske eksenleri/anlamı; desteklenen profilde kirlenme yok; RQ37–RQ42 |
| F5-B-G08 | VAE | Gerçek VAE geçerli aralığı ve ham 48k mono Float32; RQ43–RQ48 |
| F5-B-G09 | Önbellek kimliği | Sürümlü etkin önbellek kimliği ve çakışma koruması; RQ49–RQ54 |
| F5-B-G10 | Önbellek gizliliği | Güvenilir uygunluk, oturum yalıtımı ve gizlilik; RQ55–RQ60 |
| F5-B-G11 | Önbellek kapasitesi | Sınırlı rezervasyon, saklama ve eşzamanlılık; RQ61–RQ66 |
| F5-B-G12 | Geçersiz kılma | Revizyon geçersiz kılma, kalite revizyonu ve bayat doldurma koruması; RQ67–RQ72 |
| F5-B-G13 | Kalite | Yapısal ve yapılandırılmış sezgisel kalite/süre doğrulaması; RQ73–RQ80 |
| F5-B-G14 | Kurtarma | Sınırlı aynı seed kurtarma ve tekrar yok; RQ81–RQ87 |
| F5-B-G15 | Kira ve teslim | M06 terminal kira, M02 çiti ve F6 geri basıncı; RQ88–RQ94 |
| F5-B-G16 | Telemetri ve entegrasyon | Güvenli telemetri, gerçek katmanlar arası bütünleşme ve eski uyum; RQ95–RQ98 |
| F5-B-G17 | Test kanıtı | RQ01–RQ100 zorunluların tamamı gerçek kanıtla |
| F5-B-G18 | Regresyon | Özellik regresyonu, bütünlük ve geri dönüş doğrulanmış; RQ98–RQ100 |
| F5-B-G19 | Devir | Bağımsız inceleme, aşağı akış devri ve doğru durum; RQ100 |

## 9. Kanıt

`evidence/F5-B/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `INVENTORY.json`, `PLAN_EXECUTION_MAPPING.csv`, `EXECUTION_PROFILE_MATRIX.csv`, `RNG_ISOLATION_SPEC.md`, `LATENT_LENGTH_SPEC.md`, `BATCH_COMPATIBILITY_MATRIX.csv`, `MASK_CAPABILITY_SPEC.md`, `VAE_UNPADDING_SPEC.md`, `CACHE_KEY_SCHEMA.json`, `CACHE_PRIVACY_POLICY.md`, `CACHE_CAPACITY_SPEC.md`, `CACHE_INVALIDATION_MATRIX.csv`, `QUALITY_POLICY_MATRIX.csv`, `RECOVERY_DECISION_MATRIX.csv`, `COMPLETION_LEASE_SPEC.md`, `DELIVERY_SPEC.md`, `F6_HANDOFF_SPEC.md`, `TELEMETRY_MAPPING.csv`, `DOWNSTREAM_HANDOFF.md`, `FIXTURE_MANIFEST.json`, `TEST_MATRIX.json`.

## 10. Geri dönüş

M03 profilleri (`f5.batch_isolation`, `f5.cache`, `f5.recovery`) kapatılır: F5-A tek iş yolu tek aktif. Önbellek temizliği yalnızca F5-B'nin sahip olduğu girdiler için yapılır; toptan silme yok. Kod `git revert`.

## 11. Devir

- **F5-C:** sayısal profil (Euler32 tabanı), önbellek kimliği alanları, kalite koruması ve yeniden deneme tabanları, desteklenmeyen yetenekler (maske/RNG yalıtımı HOLD olduysa) ODE profil karşılaştırması ve kimlik doğrulama için girdi.
- **F6-C:** ham parçalar ve duraklama üst verisi; birleştirme/WSOLA F6-C'de.
- **G4:** toplu iş ve önbellek açıkken TTFA/RTF ve VRAM tepe ölçümleri; seed 9 kimlik kararlılığı.

## 12. Başlatma komutu

```
F5-B paketini uygula: docs/execution/packages/W3/F5-B-ses-profili-onbellek.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F5-A, M03 ve M06 kabulünü doğrula; sağlayıcının maske ve RNG yalıtımını kaynaktan denetle.
Öğe başı RNG, gerçek uzunlukta latent, toplu iş maske/VAE doğrulaması, varsayılan-bypass güvenli önbellek ve
aynı seed'le en fazla bir yeniden denemeyi kur; Leyla seed 9'a asla geri düşme, kişisel veriyi önbelleğe alma.
RQ01–RQ100'ü çalıştır, F5-B-G00…G19'u değerlendir, paket/F5-B dalında PR aç ve dur.
```
