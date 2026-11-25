# M06 — GPU kaynak zamanlayıcısı

> RTX 4070 Laptop 8 GB üzerinde Whisper (CTranslate2), Qwen (Ollama) ve FreyaTTS (PyTorch) işlerini tek bir kabul otoritesinden geçirir: atomik VRAM rezervasyonu, sınırlı kuyruk, öncelik ve adillik, model yerleşikliği, toplu iş koordinasyonu, M02 iptal köprüsü ve OOM kurtarma. Yeni model yüklemez; kesmeyi (preemption) vaat etmez.

| Alan | Değer |
| --- | --- |
| Kimlik | M06 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M02, M03, M04 (M05 isteğe bağlı nokta) |
| Sonraki | CORE_GATE, F2-A, F5-A, F5-B, F2-C |
| Bayrak | Yönetilen kip aşamalı açılır: `off` (eski) → `shadow` (yalnız gözlem, uygulamaz) → `managed`; varsayılan `off` |
| Ortam | CPU (tüm testler sahte sağlayıcılarla; gerçek GPU kabulü G4'te) |
| Eski görevler | F5-T16, F2-T07, F5-T01 |
| Kaynak | Bundle `W1/Freya_2_0_M06_Agent_Implementation_Package.md`; [gpu-resource-manager](../../../cross-cutting/gpu-resource-manager.md), [constraints.md](../../../00-overview/constraints.md) |
| Durum | NOT_RUN |

## 1. Amaç

Kayıtlı tepe VRAM 7478 / 8188 MiB (%91,3). Üç model aynı GPU'yu paylaşırken bugün temel bir kilit dışında koordinasyon yok; iptal edilen işler GPU'da sürüyor ve kaynak tutuyor. M06, CLAUDE.md'deki "GPU işi ortak yöneticiden geçer" kuralının uygulamasıdır: `backend/runtime_resources/` dışında doğrudan `torch.cuda` veya kilitsiz `to_thread` çağrısı kalmaz.

## 2. Başlamadan önce

- [ ] M02, M03, M04 kabul edilmiş; M05 varsa nokta olarak kullanılır.
- [ ] Tüm GPU tüketicileri izlenmiş: sağlayıcı çağrıları, yükleyiciler, kilitler, kuyruklar, geri düşme/laboratuvar yolları, süreç topolojisi (tek süreç mi, çok işçi mi, Ollama ayrı süreç mi).
- [ ] Gerçek topoloji belirlenmiş. Süreç içi bir asyncio kilidinin çok işçili sunucuyu veya bağımsız Ollama sürecini koordine ettiği **varsayılmaz**; desteklenmeyen topoloji açıkça HOLD.

## 3. Kapsam

**Yapılacak:** İş sözleşmeleri, kaynak gözlem arayüzü, VRAM bütçe modeli, atomik kabul ve kiralar, sınırlı iş kaydı ve kuyruk, öncelik ve adil seçim, zamanlayıcı yaşam döngüsü, model yerleşiklik yöneticisi, CTranslate2/Ollama/PyTorch adaptörleri, dinamik toplu iş koordinasyonu, iptal/son tarih köprüsü, OOM ve kurtarma, M03/M04 bütünleşmesi, eski yol ve atlama (bypass) denetimi.

**Yapılmayacak:** Gerçek GPU çıkarımı, model indirme/kurma, eğitim, gerçek SIP, harici sağlayıcı çağrısı. Diyalog anlamı (F3), ASR (F2), sentez sayısalı ve seed (F5), aktarım (F6). Sağlayıcı kesme yeteneği doğrulanıp ayrıca onaylanmadan öncelikli kesme. Ollama sürecini öldürme, pull/unload.

## 4. Dosyalar

```
backend/runtime_resources/
  contracts.py  scheduler.py  job_registry.py  priority_queue.py  deadline_policy.py
  memory_budget.py  admission.py  resource_probe.py  lease_manager.py  residency.py
  batching.py  cancellation_bridge.py  recovery.py  quarantine.py  telemetry.py
  provider_adapters/  base.py  ctranslate2.py  ollama.py  pytorch.py
tests/runtime_resources/
evidence/M06/<run_id>/
```

Gerçek model/çalışma zamanı giriş noktalarına (`models.py`, `batched_ode.py`, LLM istemcisi) yalnızca M00'da doğrulanmış dar noktalarda, önceden onaylı değişiklik listesiyle dokunulur.

## 5. Tasarım ve sözleşmeler

### 5.1 Değişmez kurallar

1. **Cihaz ve süreç mimarisi başına tek kabul otoritesi.** Gözlenen tek sahipli topoloji desteklenir; diğerleri açıkça belgelenir.
2. İçe aktarma CUDA başlatmaz, ağır sağlayıcıyı gereksiz içe aktarmaz, ağırlık yüklemez, gizli bilgi okumaz, iş parçacığı/süreç/ağ/Ollama/arka plan işçisi başlatmaz.
3. **Kayıt üst verisi yüklü model değildir.** Mevcut tutamaçlar, fabrikalar, istemciler ve model kimlikleri yeniden kullanılır. Eşzamanlı yüklemeler model/çalışma zamanı/revizyon/cihaz/yapılandırma kimliğine göre tekilleştirilir. Gizli model, seed, çözücü, beam, hassasiyet, nicemleme değişikliği yok.
4. **Gönderim veya yüklemeden önce baytlar atomik olarak rezerve edilir.** Cihaz geneli kullanılan/boş, süreç düzeyi gözlem, ayırıcı (allocator) ayrılmış/rezerve verisi, yapılandırılmış pay ve bekleyen rezervasyonlar ayrıdır. Bilinmeyen/bayat/tutarsız okuma sıfır değildir.
5. Her yönetilen iş: sınırlı öğe/bayt/maliyet, açık sınıf, son tarih veya sonlu servis zaman aşımı, doğrulanmış kapsam, terminal durum. Kuyruğa kabul ≠ GPU kabulü ≠ çalıştı ≠ başarılı ≠ teslim edildi.
6. **İptal işbirlikçidir.** M02 iptali teslimi kazanır, yerel iş sürse bile. Çalışan bir CUDA işlemi, senkron üretici, PyTorch yürütücü görevi veya Ollama isteği, bekleyen coroutine iptal edildi diye durmuş sayılmaz. Kira, gerçek terminal kanıta kadar korunur.
7. **Öncelik kesmesizdir.** Yüksek öncelikli STT işinin çalışan bir çekirdeği/toplu işi anında keseceği vaat edilmez. Uygun işin açlığı sınırlı yaşlandırma veya ağırlıklı adillikle önlenir.
8. M06 çıkarımı zamanlar, diyalog anlamını değil. İptal edilen yanıt, commit edilmiş bir randevuyu iptal etmez.
9. **Yol başına tek toplu iş otoritesi.** Mevcut `BatchedODEEngine` yürütme ilkeli olarak kalabilir veya zamanlayıcının verdiği bütçeyle toplu iş oluşturabilir; ikinci bir mikro-bekleme penceresi eklenmez, bekleyen yerel işler çoğaltılmaz.
10. Telemetri ve kanıtta ham ses, transkript, istem, yanıt, müşteri kimliği, telefon, plaka, gizli başlık, kişisel veri içeren yol veya maskesiz istisna yok (M04 izin listesi).
11. Dış davranış, özellik kimlikleri, rotalar, bayraklar, API biçimleri, model kimliği, ses profilleri, DTMF ve iş eylemleri korunur. Yönetilen kip aşamalı açılır.
12. M06 kabulü için fiziksel GPU çıkarımı gerekmez ve yetkilendirilmez; tüm sağlayıcı testleri sahte işçiler, sahte kaynak yoklayıcıları ve sahte saatle yapılır.

### 5.2 Bellek hesabı

```
etkin_boş = min(gözlenen_cihaz_boş, yapılandırılmış_cihaz_üst_sınırı − sahipli_kullanım)
            − güvenlik_payı − bekleyen_rezervasyonlar
kabul     = tahmini_tepe ≤ etkin_boş   (tahmin bilinmiyorsa: sınırlı bekleme veya açık ret)
```

Fikstür: 1800 MiB gözlenen boş − 512 MiB pay − 256 MiB bekleyen = 1032 MiB (GPU07). Zaten yerleşik bir modelin ayak izi iki kez düşülmez (GPU08). Gözlenmemiş baytlar erken uzlaştırılmaz (GPU09). Birimler bayt/MiB olarak açık; yüzde değil. Tahmini tepe değerleri **ölçüm bekleniyor** durumundadır; G4'te gerçek profil ölçülene kadar muhafazakâr yapılandırma değerleri kullanılır ve kanıt olarak raporlanmaz.

### 5.3 Öncelik sınıfları

Kullanıcı genel API üzerinden keyfi öncelik veremez. Düşük indeks yüksek önceliktir; sınıflar canlı gecikme vaadi değildir.

| Sınıf | Tipik iş | Politika |
| --- | --- | --- |
| P0 | Söz kesmeyle ilgili, F1/F2'nin istediği doğrulanmış ASR ihtiyacı | En yüksek etkileşimli öncelik; spekülatif kalıcı tekel yok |
| P1 | Final ASR | Düşük gecikme, son tarihe bağlı |
| P2 | Etkin yanıtın ilk çalınabilir TTS parçası | İlk sese öncelik; yalnızca gerekli F3/F4 çıktısından sonra |
| P3 | Gerekli LLM diyalog çıkarımı | Bağımlılık duyarlı; önkoşul LLM, erişilemeyen TTS yüzünden aç kalmaz |
| P4 | Sonraki TTS parçaları | F6 tampon baskısı dikkate alınır; sınırsız ön üretim yok |
| P5 | Kısmi ASR | Geçersiz kılınan kısmi revizyonlar birleştirilir; kapsam başına sınırlı bekleyen; final asla düşürülmez (GPU23) |
| P6 | Ön ısıtma / önbellek hazırlığı | Yalnızca boş kapasitede; canlı çağrıyı bloklamaz |
| P7 | Benchmark, A/B deneyleri, isteğe bağlı derin kalite | Yalıtılmış laboratuvar kuyruğu/profili; canlı baskıda ertelenir/reddedilir; M06'da eğitim yok |

Aynı öncelikte belirlenimci eşitlik bozucu: kuyruğa giriş sırası, sahip, kararlı iş kimliği. Oturum başına sınırlı bekleyen kuyruk; en uzun bekleme sınırı ve açık zaman aşımı. Bağımlı işlerde üst iş tek yuvayı tutarken alt işi beklemez (GPU24).

### 5.4 Sağlayıcı adaptörleri

| Sağlayıcı | Tamamlanma sınırı | Dikkat |
| --- | --- | --- |
| CTranslate2 / Faster-Whisper | `transcribe` dönüşü değil; tembel segment üreticisinin tüketilmesi/kapatılması ve doğrulanmış bitiş | Dil, beam, hotword, güven ve ham dönüş korunur |
| Ollama / Qwen | Ayrı süreç model yerleşikliğinin sahibi olabilir; HTTP yanıtı/iptali bellek bırakıldı demek değildir | Yalnızca Freya'nın istekleri sayılır; model etiketi, uç nokta, bağlam, akış, zaman aşımı korunur; belirsiz terminal açıkça raporlanır |
| PyTorch / FreyaTTS / AudioVAE | Sağlayıcının gerçek tamamlanma sınırı (ör. senkronizasyon noktası); ana makine geri çağrısı çekirdek bitişi değildir | Tek ve toplu yollar; seed 9 ve açık A/B seed'leri, dtype/cihaz, ODE ve süre varsayılanları, önbellek ve akustik korumalar korunur |

### 5.5 Yerleşiklik ve toplu iş

- `ModelKey` = model_id + çalışma zamanı + model_revision + cihaz + uyumlu yapılandırma kimliği; oturumla karıştırılmaz. Durum makinesi: `UNLOADED → LOADING → READY → DRAINING → UNLOADED`, ayrıca `FAILED` / `UNKNOWN`. Sahiplik: `BORROWED / OWNED / EXTERNAL`. Başlangıçta yüklü tutamaçlar ödünç alınmış sayılır; oturum kapanışı boşaltamaz.
- Toplu iş: yalnızca uyumlu model/revizyon/cihaz/çözücü üyeleri; dolgu hesaba katılmış tepe maliyet; uzun üye bütçeyi aşarsa bölünür veya reddedilir; ilk parçanın son tarihi oluşma gecikmesinden önemliyse tek başına gönderilir; üye kimliği ve hatası üye başına; toplu iş kirası tüm toplu iş terminal olana kadar korunur.

### 5.6 OOM, kurtarma ve kapanış

Tipli hata; belirsiz ayırmalar korunur; küresel sıfırlama yok. Saf çıkarım yeniden denemesi yalnızca: terminal doğrulanmış, yeni kabul, farklı deneme kimliği, model/seed değişmemiş, sınırlı sayı. Belirsiz zaman aşımında kör yeniden deneme veya iş yeniden oynatma yok. Karantina kapasitesi dolarsa güvensiz kabul engellenir; bırakma yalnızca kanıtla. Kapanış: kabulü durdur, çağıranı süreli beklet, izlenen karantina, harici süreç öldürme yok.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M06.01 | Ön kontrol | M00–M04 kabulü, M05 isteğe bağlı nokta, Git anlık görüntüsü | HOLD'da uygulama yok |
| M06.02 | GPU tüketici envanteri | Sağlayıcı çağrıları, yükleyiciler, kilitler, kuyruklar, geri düşme/laboratuvar yolları, süreç topolojisi | `GPU_CONSUMER_INVENTORY.json` (kaynak kanıtıyla) |
| M06.03 | Sahiplik ve eşzamanlılık tasarımı | Tek zamanlayıcı otoritesi, kilit sırası, yaşam döngüsü, eski yol, yazma kapsamı | `SCHEDULER_DECISIONS.md` |
| M06.04 | Çıkarım sözleşmeleri | Yerel istek, karar, tahmin, kira, tamamlanma, sonuç türleri (M01/M02 başvurularıyla) | GPU03–GPU04 |
| M06.05 | Kaynak gözlem arayüzü | Enjekte cihaz/süreç gözlemleri, tazelik, açık bilinmiyor, M04 güvenli alanları | GPU05–GPU06 |
| M06.06 | VRAM bütçe modeli | Birim güvenli bütçe, artımlı tahmin, bekleyen rezervasyon, harici pay | GPU07–GPU10, GPU14 |
| M06.07 | Atomik kabul ve kiralar | Kontrol/rezerve/gönder serileşmesi; sınırlı bekleme; idempotent bırakma | GPU11–GPU13 |
| M06.08 | Sınırlı iş kaydı ve kuyruk | Öğe, tutulan bayt, maliyet, sahip, kapsam sınırları; yinelemeler ve aşırı yük | GPU15–GPU16 |
| M06.09 | Öncelik ve adil zamanlama | Kesmesiz, son tarih duyarlı kararlı seçim; adillik; arka plan erteleme | GPU17–GPU24 |
| M06.10 | Zamanlayıcı yaşam döngüsü | Açık başlat, uyandır, gönder, durdur/boşalt; işçi hatası yalıtımı | GPU25–GPU26 |
| M06.11 | Model yerleşiklik yöneticisi | Tek uçuşlu yükleme, ödünç tutamaçlar, kullanıcılar, güvenli yerleşiklik kararları | GPU27–GPU32 |
| M06.12 | CTranslate2 adaptörü | Mevcut Whisper adaptörü; tembel yineleme ve gerçek terminal anlamı | GPU33–GPU34 |
| M06.13 | Ollama adaptörü | Mevcut istemci; harici sahiplik, kabul, belirsiz sonlanma | GPU35–GPU36 |
| M06.14 | PyTorch adaptörü | Mevcut Freya/AudioVAE ve `BatchedODEEngine`; yürütme tamamlanması; çift yükleme yok | GPU37–GPU38 |
| M06.15 | Dinamik toplu iş koordinasyonu | Uyumlu sınırlı üyeler, dolgu duyarlı tahmin, acil ilk parça, ikinci kuyruk yok | GPU39–GPU45 |
| M06.16 | İptal ve son tarih köprüsü | M02 kapsamlı iptal, atomik çitler, geç sonuç reddi, çalışan kiralar korunur | GPU46–GPU52 |
| M06.17 | OOM ve kurtarma | Tipli hatalar, sınırlı yetkili yeniden deneme, sessiz geri düşme yok, karantina | GPU53–GPU57 |
| M06.18 | M03/M04 bütünleşmesi | Değiştirilemez ayarlar, model revizyonları, gerçek ölçüm sınırları, güvenli olaylar | GPU58–GPU60 |
| M06.19 | Eski yol ve atlama denetimi | Gözlenen her GPU üreticisi tek yönetilen sınırdan geçer veya açık HOLD; varsayılanlar ve API'ler korunur | GPU61–GPU62 |
| M06.20 | Belirlenimci testler | GPU01–GPU64; sahteler ve yarış bariyerleri; gerçek model/GPU yok | Tüm testler çalıştırılmış |
| M06.21 | Regresyon ve kanıt | M00 özellik matrisi, mevcut güvenli testler, bütünlük, sağlayıcı noktaları, benchmark hazırlığı | GPU63–GPU64 |
| M06.22 | Kabul ve devir | M06-G00…G17, hazırlık, geri dönüş, inceleme notları, aşağı akış sözleşmeleri | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| GPU01 | Eksik/belirsiz önceki kanıt | Ön kontrol HOLD; kaynak düzenleme veya sağlayıcı başlatma yok |
| GPU02 | Temiz sahte ortamda içe aktarma | CUDA, model yükleme, ağ, süreç, işçi veya DB başlatılmaz |
| GPU03 | Gerçek M01/M02 başvuruları ve M03 görüntüsü | Yinelenen kanonik tür yok; uyuşmayan kapsam/revizyon reddedilir |
| GPU04 | Geçersiz istek boyutu, birim, sınıf ve son tarih | Negatif, int yerine bool, taşma, bilinmeyen kapsam ve geçersiz saat reddedilir |
| GPU05 | Eksik/bayat/çelişkili yoklama | Açık bilinmiyor/erişilemez; iyimser bellek kabulü yok |
| GPU06 | Cihaz ile süreç/ayırıcı gözlemi | Ayrı kapsamlar; ilgisiz çıkarma veya sahte sıfır yok |
| GPU07 | Bayt/MiB ve pay aritmetiği | 1800 − 512 − 256 = 1032 MiB; tam sınır durumu doğru |
| GPU08 | Zaten gözlenen yerleşik bellek | Yerleşik ayak izi iki kez düşülmez |
| GPU09 | Bekleyen rezervasyon ve harici ayırma | Gözlenmemiş baytlar erken uzlaştırılmaz |
| GPU10 | Bilinmeyen tahmin / aşırı büyük iş | Sınırlı bekleme veya açık ret; bütçesiz çalıştırma asla |
| GPU11 | Yalnız tek başına sığan iki eşzamanlı istek | Atomik rezervasyon yalnızca birine izin verir; aşırı taahhüt yok |
| GPU12 | Rezervasyon alındı, gönderim başlamadı | İptal/sona ermede gönderilmediği doğrulanır, tam bir kez bırakılır |
| GPU13 | Belirsiz gönderim hatası | Kira korunur/karantinaya alınır; çift gönderim yok |
| GPU14 | Cihaz/profil üst sınırı gözlenen boştan küçük | Yapılandırılmış üst sınıra uyulur; örtük geçersiz kılma yok |
| GPU15 | Kuyruk öğe/bayt/maliyet ve sahip sınırları | Tutulan her üye sayılır; taşma açık |
| GPU16 | Yinelenen iş/deneme kimliği | Ret veya idempotent mevcut sonuç; tek gerçek gönderim |
| GPU17 | Kararlı kuyruk sırası | Aynı öncelikte belirlenimci eşitlik bozma |
| GPU18 | P0/P1 ile kuyruktaki laboratuvar (P7) işi | Uygun canlı iş önce gönderilir; laboratuvar ertelenir |
| GPU19 | Yerel iş sırasında acil iş | Kesme iddiası yok; aktif kira kalır |
| GPU20 | Etkileşimli iş açlığı senaryosu | Sınırlı adil seçim veya açık son tarih aşımı; sessiz süresiz bekleme yok |
| GPU21 | Kuyruktayken son tarih aşıldı | Sağlayıcı başlatılmadan çıkarılır; rezervasyon hesaplanır |
| GPU22 | Çalışırken son tarih aşıldı | Teslim çitlenir, işbirlikçi iptal istenir, fiziksel kira korunur |
| GPU23 | Geçersiz kılınan kısmi ASR | Yalnızca izinli revizyon birleştirilir; final ASR asla düşürülmez |
| GPU24 | Bağımlılık ve iç içe kabul | Üst iş tek yuvayı tutarken alt işi beklemez; önkoşul ilerler |
| GPU25 | Açık başlat, tekrar başlat ve uyandırma | Tek zamanlayıcı işçisi/otoritesi; kayıp uyandırma yok |
| GPU26 | İşçi geri çağrısı hata fırlatır | Diğer uygun işler yalıtılmış; güvenli hata ve izlenen kira |
| GPU27 | Aynı model için iki eşzamanlı yükleme isteği | Tek uçuşlu fabrika bir kez çağrılır; çift tutamaç yok |
| GPU28 | Paylaşılan yüklemeyi bekleyenlerden birinin iptali | Diğer bekleyen sürer; paylaşılan yükleme körce iptal edilmez |
| GPU29 | Yanlış revizyon/yapılandırma/cihaz yerleşikliği | Uyumsuz tutamaç yeniden kullanılmaz; sessiz model değişimi yok |
| GPU30 | Ödünç/harici model tutamacı | Oturum kapanışı boşaltamaz; sahiplik korunur |
| GPU31 | Yükleme tepesi ve aktif kira | Yükleme bütçesi uygulanır; aktif model tahliye edilmez |
| GPU32 | Başarısız/belirsiz yükleme | Doğru FAILED/UNKNOWN/karantina; sahte READY yok |
| GPU33 | CTranslate2 tembel üretici | Kira `transcribe` dönüşüne değil, yineleme/doğrulanmış bitişe kadar tutulur |
| GPU34 | CTranslate2 yineleme hatası/terk | Gerçek terminal veya karantina; izlenmeyen iş sızmaz |
| GPU35 | Ollama harici süreç ve sahte istemci | Yalnızca yönetilen çağrılar sayılır; öldürme/pull/unload veya küresel kontrol iddiası yok |
| GPU36 | Sunucu durumu bilinmeyen iptal edilmiş Ollama HTTP beklemesi | Erken bırakma veya yeniden deneme yok; açık belirsizlik |
| GPU37 | Cihaz bitişinden önce PyTorch ana makine geri çağrısı | Kira adaptörün terminal kanıtına kadar tutulur |
| GPU38 | Freya tek ve toplu yollar | Mevcut tutamaç yeniden kullanılır; seed 9 ve açık A/B seed/yapılandırma korunur |
| GPU39 | Uyumsuz model/çözücü/revizyon toplu işi | Karışık uyumsuz toplu iş yok |
| GPU40 | Dolgu duyarlı tepe/maliyet | Uzun üye bütçeyi aşabilir; güvenle bölünür veya reddedilir |
| GPU41 | İlk parça son tarihi ile oluşma gecikmesi | Gerekirse tek başına gönderim; çift mikro pencere yok |
| GPU42 | Mevcut toplu iş oluşturma kuyruğu | Tek etkin kuyruk/kabul; çift rezervasyon veya çift gönderim yok |
| GPU43 | Oluşmadan önce iptal edilen üye | Diğerlerine zarar vermeden çıkarılır |
| GPU44 | Gönderim sırasında iptal edilen üye | Üye çitlenir; paylaşılan kira tüm toplu iş bitene kadar |
| GPU45 | Üye hatası / yeniden sıralanmış çıktı | Üye başına kimlik ve hata güvenli; oturumlar arası veri yok |
| GPU46 | Oturum, tur ve generation iptali | Doğru kapsam; ilgisiz generation iptali bağımsız ASR/sistem işini etkilemez |
| GPU47 | Gönderimden önce iptal yarışı | İptal kazanırsa yerel başlatma olmadığını bariyer kanıtlar |
| GPU48 | Gönderimden sonra iptal yarışı | Mantıksal iptal anında; kira korunur; geç sonuç reddedilir |
| GPU49 | Eski oturum/tur/generation veya yanlış deneme geri çağrısı | Reddedilir; güncel sonucu veya kirayı etkileyemez |
| GPU50 | Yinelenen terminal geri çağrısı ve eşzamanlı kapanış | Tek bırakma, doğru sahiplik |
| GPU51 | Sahte yerel iş sürerken çağıranın beklemesi iptal | Güçlü başvuru/defter korunur; sahte serbest bırakma yok |
| GPU52 | Yumuşak duraklatma ile kesin commit | Duraklatma iptal etmez; iptal edilen generation devam edemez; medya F6'nın |
| GPU53 | Sentetik ayırıcı OOM | Güvenli tipli hata; belirsiz ayırmalar korunur; küresel sıfırlama yok |
| GPU54 | Yetkili saf çıkarım yeniden denemesi | Terminal doğrulanmış, yeni kabul, farklı deneme, değişmemiş model/seed, sınırlı sayı |
| GPU55 | Belirsiz zaman aşımı / güvensiz yeniden deneme | Kör yeniden deneme, iş yeniden oynatma veya sahte tamamlanma yok |
| GPU56 | Karantina kapasitesi ve uzlaştırma | Doygunluk güvensiz kabulü engeller; bırakma yalnızca kanıtla |
| GPU57 | Aktif/kuyruktaki işle kapanış | Kabul durur, süreli bekleme, izlenen karantina, harici süreç öldürme yok |
| GPU58 | Canlı iş sırasında M03 görüntü revizyonu değişir | Sabitlenmiş revizyon bozulmaz; canlı değişim yok |
| GPU59 | M04 telemetri geri basıncı/hatası | Kontrol kararları olay tesliminden bağımsız; güvenli sınırlı alanlar |
| GPU60 | Metrik kapsamı/kökeni ve bilinmeyen değer | Doğru saat/birim/durum; sahte sonuç donanım metriği değil; kişisel veri yok |
| GPU61 | Eski off/shadow/managed uyumu | Çift gönderim yok; genel API/varsayılanlar korunur; gölge kip uygulamaz |
| GPU62 | GPU tüketici atlama denetimi | Gözlenen her aktif yönetilen giriş noktasının kabul noktası var veya açık engelleyici HOLD |
| GPU63 | Regresyon ve kaynak bütünlüğü | M00 özellik kimlikleri, güvenli mevcut testler, yalnız izinli değişiklik; model/DB değişikliği yok |
| GPU64 | Topoloji ve donanım kabul sınırı | Çok işçili/harici belirsizlik açık; gerçek GPU/SIP/insan testleri NOT_RUN |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M06-G00 | Ön kontrol | M00–M04 gerçek kanıtı, doğru doğrudan bağımlılıklar, açıklanamayan sapma yok |
| M06-G01 | Tek otorite | Gözlenen yönetilen topolojide tek zamanlayıcı, güvenli içe aktarma, onaylı kapsam |
| M06-G02 | Sözleşmeler | M01/M02/M03 başvurularıyla geçerli istek/karar/kira sözleşmeleri |
| M06-G03 | Gözlemler | Kapsamı doğru kaynak gözlemleri, açık bilinmiyor/tazelik, doğru birimler |
| M06-G04 | Bellek | Doğru bellek hesabı, atomik rezervasyon, tek sahipli kira |
| M06-G05 | Kuyruk | Sınırlı kuyruklar, öncelik, adillik, son tarihler ve bağımlılık güvenliği |
| M06-G06 | Yerleşiklik | Tek uçuşlu model yerleşikliği; izinsiz yükleme/boşaltma/değişim yok |
| M06-G07 | CTranslate2 | Adaptör ve tembel tamamlanma anlamı enjekte testlerle doğrulanmış |
| M06-G08 | Ollama | Adaptör, harici süreç sınırlamaları ve belirsiz terminal işleme |
| M06-G09 | PyTorch | Freya adaptörü; çift yükleme veya desteksiz tamamlanma varsayımı yok |
| M06-G10 | Toplu iş | Tek uyumlu toplu iş otoritesi; sınırlı üye ve tepe hesabı |
| M06-G11 | İptal | M02 iptal/çit bütünleşmesi; erken kira bırakma veya bayat teslim yok |
| M06-G12 | Kurtarma | OOM/yeniden deneme/karantina/kapanış güvenli ve test edilmiş |
| M06-G13 | M03/M04 | Görüntü/varsayılanlar ve güvenli ölçüm/kanıt anlamı |
| M06-G14 | Atlama denetimi | Gözlenen tüm yönetilen GPU tüketicileri hesaplanmış; kontrolsüz aktif atlama yok; eski API/özellikler korunmuş |
| M06-G15 | Test kanıtı | GPU01–GPU64 gerçekten çalıştırılmış ve geçmiş; günlükler incelenebilir |
| M06-G16 | Bütünlük | Regresyon/kaynak bütünlüğü, onaylı farklar, kanıt ve yıkıcı olmayan geri dönüş |
| M06-G17 | Devir | Gerçek aşağı akış arayüzleri, sağlayıcı sınırları ve kabul sınırları belgelenmiş ve incelenmiş |

## 9. Kanıt

`evidence/M06/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `GPU_CONSUMER_INVENTORY.json`, `SCHEDULER_DECISIONS.md`, `BYPASS_AUDIT.csv` (her GPU giriş noktası: yönetilen / HOLD / laboratuvar), `PROVIDER_COMPLETION_SEMANTICS.md`, `MEMORY_BUDGET_PROFILE.json` (yapılandırılmış değerler; ölçülmüş tepe değerleri `null` + "ölçüm bekleniyor"), `TEST_MATRIX.json`, `DOWNSTREAM_HANDOFF.md`.

## 10. Geri dönüş

Kip bayrağı `off`'a alınır: eski çağrı yolları aynen çalışır. Yönetilen noktalar ayrı commit'lerdir ve `git revert` ile geri alınır. Kip değişikliği oturum sınırında etkili olur; canlı işi bozmaz.

## 11. Devir

- **F2-A / F2-C:** final ASR P1, kesmeyle ilgili ASR P0, kısmi ASR P5; kısmi revizyon birleştirme kuralı.
- **F5-A / F5-B:** sentez işleri; ilk parça P2, sonraki parçalar P4; toplu iş otoritesi; adaptif ODE adımı M03 profiliyle ve F5 kalite kanıtıyla.
- **F3:** LLM istekleri P3; Ollama sınırlamaları (harici süreç belleği) açık.
- **G4:** gerçek VRAM tepe profili ve eşzamanlı çağrı ölçümleri; kapasite iddiası yalnızca orada.

## 12. Başlatma komutu

```
M06 paketini uygula: docs/execution/packages/W1/M06-gpu-zamanlayici.md.
Kuralları CLAUDE.md'den oku; M02, M03, M04 kanıtını doğrula ve gerçek süreç topolojisini belirle.
backend/runtime_resources/ altında tek kabul otoritesini kur; varsayılan kip "off" kalsın,
gerçek GPU veya model kullanma. Her GPU giriş noktasını yönet ya da HOLD olarak raporla.
GPU01–GPU64'ü çalıştır, M06-G00…G17'yi değerlendir, paket/M06 dalında PR aç ve dur.
```
