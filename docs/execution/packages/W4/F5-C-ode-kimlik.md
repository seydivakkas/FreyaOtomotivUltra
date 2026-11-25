# F5-C — ODE profil seçimi, son tarih duyarlı toplu iş, ses kimliği ve perde ölçümü

> F5-B'nin üzerine: taban Euler32'yi koruyarak isteğe bağlı ayrık ODE profilleri (yalnız kalibre ve etkinleştirilmişse), sürümlü maliyet modeli, son tarih duyarlı sınırlı toplu iş oluşturma ve uzunluk kovaları, öğe başı RNG'nin toplu işte korunması, F4-C kontrol sahipliğinin uygulanması, önbellek kimliği genişletmesi, hakları temizlenmiş referanslarla **laboratuvar** ECAPA konuşmacı benzerliği ve perde ölçümleri, ayrık kalibrasyon/test protokolü. Kalibre edilmemiş hızlı profil asla sessizce seçilmez; kalite iddiası yalnız ölçümle.

| Alan | Değer |
| --- | --- |
| Kimlik | F5-C |
| Dalga | W4 |
| Öncelik | P1 |
| Önkoşullar | W2_GATE, F5-B, F4-C |
| Sonraki | G2, F5-D |
| Bayrak | `f5_pipeline_v2` + M03 profilleri `f5.ode_profiles`, `f5.deadline_batching` (varsayılan kapalı; taban Euler32) + laboratuvar kipi |
| Ortam | CPU (sahte yerel sağlayıcı); gerçek ODE/ECAPA/perde ölçümleri G4 ve `@pytest.mark.gpu` |
| Eski görevler | F5-T17 (kalan kısım), F5-T18, F5-T19, F5-T22, F5-T23, F5-T24 |
| Kaynak | Bundle `W4/Freya_2_0_F5_C_Agent_Implementation_Package.md`; [F5 spec](../../../stages/F5-neural-synthesis/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

İlk ses hedefi 1,2 s; sentez süresinin büyük kısmı ODE adımlarında. Adım sayısını azaltmak hızlandırır ama Leyla'nın sesini ve telaffuzu bozabilir. F5-C, daha hızlı profilleri yalnızca **kalibrasyon kanıtıyla ve kapsamında** kullanılabilir kılar; Leyla kimliğinin kaymasını ölçmek için güvenli bir laboratuvar düzeneği kurar. Hiçbir canlı karar düşük kosinüs skoruna dayanarak seed veya konuşmacı değiştirmez.

## 2. Başlamadan önce

- [ ] W2_GATE, F5-B, F4-C gerçek kabul; onaylı soy ve izin; önceki plan hash'leri onaylı bildirimle eşleşir.
- [ ] Yükleyici, Euler zaman ızgarası, toplu iş işçileri ve sağlayıcı yolları izlenmiş; iki aday toplu iş işçisi bulunursa belgeli mevcut sahip seçilir veya HOLD.
- [ ] **Model kuralı:** ECAPA konuşmacı kodlayıcısı yalnız **laboratuvar değerlendiricisi**dir, canlı yola girmez. Yerel yapıt ve lisans yoksa laboratuvar HOLD, indirme yok; ekleme CLAUDE.md kural 4 gereği kullanıcı kararıdır (eski F5-T22 "speaker encoder seçimi ve lisansı").
- [ ] Referans ses dosyalarının hakları ve gizliliği (M07) doğrulanmış; hakları temizlenmemiş referans okunmaz.

## 3. Kapsam

**Yapılacak:** Yürütme sözleşmesi; sabit profiller; maliyet modeli; uyarlanır seçici; son tarih bütçeleri; toplu iş oluşturma sahibi; uzunluk kovaları; RNG koruması; yerel adaptör; kontrol sahipliği; önbellek uyumu; konuşmacı referans politikası; ECAPA metrikleri; perde metrikleri; kalibrasyon protokolü; kira ve kurtarma; F6 teslimi; gözlem ve kipler; benchmark tasarımı.

**Yapılmayacak:** Gerçek GPU ölçümünün sahte veriyle yerine konması; FreyaTTS ağırlık değişikliği; LoRA/ince ayar (F5-D); düşük benzerlikte otomatik yeniden deneme veya seed değişimi; MOS/ABX simülasyonu.

## 4. Dosyalar

```
backend/neural_synthesis/
  ode_profiles.py  cost_model.py  profile_selector.py  deadline_budget.py
  batch_formation.py  length_buckets.py  rng_layout_check.py  native_profile_adapter.py
  control_application.py  cache_identity_ext.py  f6_delivery.py
backend/neural_synthesis/lab/
  speaker_reference.py  ecapa_metrics.py  pitch_metrics.py  calibration.py
tests/neural_synthesis/profiles/  tests/neural_synthesis/lab/
evidence/F5-C/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Profiller ve seçim

| Profil | Durum | Kural |
| --- | --- | --- |
| Euler32 | Taban, onaylı | Eski çağrı aynen; geliştirilmiş kapalıyken tek yol |
| Euler16 / Euler24 / Euler48 | İsteğe bağlı ayrık profiller | Yalnız yerel sağlayıcı kabul ederse **ve** kapsamlı kalibrasyon revizyonu geçerliyse; aksi halde devre dışı |
| Euler8 | Beyan edilse bile | Sağlayıcı reddederse desteklenmiyor |

- Yalnız Euler32 onaylıysa yalnız o seçilir; kalibre olmamış hızlı profil asla. Kısa karşılamaya kalibre edilmiş Euler16, uzun kritik kod içeren metne genellenmez. Gerçek yerel NFE nominal adımdan farklıysa gerçek NFE ve ızgara kaydedilir. Eşit tahmini maliyetli iki uygun profil → belirlenimci onaylı öncelik. Tüm profiller son tarihi kaçırıyorsa yetkisiz düşük kalite yok; M06 üzerinden erteleme/hata. Model güncellemesinden sonra bayat kalibrasyon → yeni profil etkinleşmesi geçersiz. Etkinleştirilmemiş Euler48 isteği gönderilmez. Maliyet tahmini null ve taban uygunsa muhafazakâr taban kabulü. Yerel iş sırasında profil tercihi değişirse sabit etkin yürütme etkilenmez.
- Yürütme sözleşmesi: `normalization_passes=2` → önbellek/GPU'dan önce ret; kanonik Leyla profilinde `seed=42` → yetkisiz seed reddi (ikame yok); onaylı A/B `seed=77` deney kapsamında korunur; model/dağarcık revizyon uyuşmazlığı → ret; aynı metin farklı koşullandırma → ayrı yürütme; desteklenmeyen IPA kontrolü yalnız rehber veya tipli zorunlu-kontrol reddi.

### 5.2 Maliyet, son tarih ve toplu iş

- Maliyet modeli sürümlü, muhafazakâr, bayatlığa duyarlı; sahte ölçüm yok. Saat alanı uyuşmazlığı → karşılaştırma reddi; NaN/negatif tahmin reddi; geçmiş son tarih → yeni gönderim yok.
- Fikstür: aday maliyeti 60 ms, kalan pay 63 ms, güvenlik marjı 5 ms → oluşturma beklemesi yok ve uygulanabilir değil. Eklemeyle en erken üye son tarihi kısalırsa sınır yeniden hesaplanır. Mikro bekleme sırasında daha yüksek öncelikli final ASR gelirse M06 politikasına göre bekleme durur. Akransız acil ilk parça → kabul edildiyse tekil gönderim, dolu toplu iş beklenmez. Bölünme sonrası yeniden ekleme özgün kuyruk/son tarihi korur.
- Oluşturma: tek sahip (M06 D6 veya mevcut `BatchedODEEngine`); P2 ilk parça ile P4 sonrakiler varsayılan profilde karışmaz; P7 laboratuvar ve P2 canlı asla birlikte değil; farklı çözücü ızgarası uyumsuz; bağımsız doğrulanmış koşullandırma aynı alanlarla gruplanabilir. Fikstür: gerçek uzunluk 40 ve 44 → dolgulu 88, geçerli 84, dolgu 4 (tahmini VRAM yok); 4 ve 100, dolgu sınırı 0,25 → bölme veya tekil, kırpma yok. Uzun uygun işin sürekli atlanması adillik/azami bekleme ile engellenir; bilinmeyen sağlayıcı uzunluk boyutu → tahmin reddi/HOLD; azami toplu iş 4 ve beş uyumlu iş → dördü, fazlası kalır; küresel bekleyen sınırı; F6 rezervasyonu yoksa GPU F6'yı beklerken tutulmaz; aynı iş için eşzamanlı oluşturma → tek M06 talebi.

### 5.3 RNG, düzen ve önbellek

Seed 9 gerçek şekli sabitken akran uzunluğu değişse, sıra ters çevrilse, akran seed'i 42→123 değişse bile hedef latent değişmez; gönderimden önce iptal edilen akran → kalan latent değişmez, düzen güvenle yeniden hesaplanır; gönderimden sonra iptal → akran teslimi bastırılır, ortak kira tutulur. Ters maske kutupluluğu → koruma reddeder; geçerli sınırda dolgu değeri değişimi → sayısal sızıntı tespiti veya doğrulanmış maske; dolgu içeren VAE çıktısı yalnız doğrulanmış eşlemeyle kırpılır; tamsayı taşması tahsisten önce reddedilir; yinelenen üye başvurusu → toplu iş reddi.

Önbellek: aynı metin/seed için Euler16 ile Euler32 farklı kimlik; aynı adım farklı ızgara revizyonu → ıska/bypass; F4-C model uygulamalı hız değişirse kimlik değişir; yalnız F6 duraklaması değişip ham değişmezlik kanıtlıysa ham yeniden kullanım (taze sınır üst verisi); tekile eşdeğer kalibre edilmemiş karışık düzen → düzene özgü anahtar veya bypass; özel fiyat/plaka metni → paylaşılan önbellek bypass; eski generation zarflı isabet → yalnız ham yük ödünç, taze güncel zarf; kalibrasyon iptal edilirse etkilenen isabet engellenir; F4-C kontrol üst verisi yoksa açık yalnız-ipucu/uyumlu taban veya HOLD; desteklenmeyen perde isteği → perde kaydırma veya jeton enjeksiyonu yok.

### 5.4 Kontrol sahipliği

F4-C hızı F6'ya atadıysa F5 hız uygulamaz; durum iletilir. F4-C hızı 0,90 ve yerel destek bilinmiyor, WSOLA asgarisi 0,94 → sessiz kırpma yok; açık desteklenmiyor veya onaylı indirme. İstenen/desteklenen/planlanan/uygulanan ayrı kaydedilir; çift hız/duraklama/normalizasyon yok.

### 5.5 Laboratuvar: konuşmacı kimliği ve perde

- Referans: hakları temizlenmemiş dosya → değerlendirme yok, korunan içerik okunmadan HOLD. Test ile aynı modelden üretilmiş referans → "öz-tutarlılık" etiketi, insan kimliği değil. ECAPA yerel yapıtı yoksa indirme yok, laboratuvar HOLD; taban sentez etkilenmez.
- ECAPA metrikleri: [1,0]–[1,0] → kosinüs 1 (yalnız fikstür; kimlik doğrulama değil); [1,0]–[0,1] → kosinüs 0 (uydurma eşik yok); sıfır norm/sonlu olmayan gömme → nedenle null; yanlış boyut → karşılaştırma reddi (kırpma/dolgu hilesi yok); çoklu referans skorları 0,8/0,9/0,7 → önceden beyan edilen ortalama 0,8 ve kapsam (en yüksek seçilmez).
- Perde: tamamen sessiz harfli klip → uygun çerçeve varsa F0 null, ses oranı 0; uygun çerçeve yok → kapsam ve F0 null (0 Hz değil); p10/p90'da 100/200 Hz fikstürü → 12 yarım ton aralık, açık birimler; sesli çerçevede NaN/negatif F0 → geçersiz işaret, kapsam raporu; farklı prozodili eşleşen metin → yalnız hizalı geçerli bölgeler karşılaştırılır.
- Kalibrasyon: kalibrasyon ve test aynı anlamsal şablon grubunu paylaşırsa sızıntı → protokol reddi. Onaylı aynı/farklı konuşmacı etiketleri yoksa FAR/FRR iddiası yok, yalnız skor dağılımı. Düşük kosinüs tek başına canlı yeniden deneme, seed değişimi veya konuşmacı değişimi tetiklemez. Model güncellemesi kalibrasyonu geçersiz kılar. Sentetik gidiş-dönüş hatasındaki iyileşme insan MOS'u değildir.

### 5.6 Kira, kurtarma, teslim

Generation commit'inden sonra gelen yerel geri çağrı yayımlanmaz, gerçek kira bırakılır; ana makine dönüşü cihaz bitişi değildir; yinelenen toplu iş tamamlanmasında eşleşen kira tek bırakılır; CPU somutlaştırmasından sonra F6 kuyruğu dolu → CPU sahipliği izlenir, yeniden çıkarım yok; yeniden denenebilir koruma hatası → en fazla bir deneme (aynı seed/plan), ikincisi de başarısızsa terminal; terminali bilinmeyen OOM → karantina. Metrikler: geçerli 2 s süre, 0,4 s duvar → tanımlı sınır için RTF 0,2; süresi dolan/iptal edilen vakalar gecikme örneğinden sessizce çıkarılmaz (denenen/süresi dolan sayıları raporlanır); ayırıcı rezerve ile cihaz kullanılan ayrı kaynaklar.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F5-C.01 | Ön kontrol ve soy | Giriş yetkisi; DAG; kabul edilmiş çekirdek/W2 ve F5-B/F4-C raporları | `preflight.md`; OS01–OS08 |
| F5-C.02 | Envanter ve otorite | Yükleyici, Euler ızgarası, toplu iş işçisi ve sağlayıcı yolları | `inventory.md` |
| F5-C.03 | Yürütme sözleşmesi | Özel kayıtları değiştirilemez kapsamlı sözleşmelere eşle | `contract_mapping.md`; OS09–OS16 |
| F5-C.04 | Sabit profiller | İsteğe bağlı ayrık Euler profilleri; yetenek ve etkinleştirme | `solver_profiles.md`; OS17–OS20 |
| F5-C.05 | Maliyet modeli | Sürümlü muhafazakâr maliyet/tepe tahmini; M06 yoklamaları ve onaylı kalibrasyon girdileri | `cost_model.md` |
| F5-C.06 | Uyarlanır seçici | Yetenek, maliyet ve F4 kritik konuşma eylemine göre filtreleme | `selection_policy.md`; OS21–OS26 |
| F5-C.07 | Son tarih bütçeleri | Muhafazakâr en geç başlangıç ve sınırlı bekleme; M02 saat ve M06 kuyruk son tarihleri | `deadline_policy.md`; OS27–OS34 |
| F5-C.08 | Oluşturma sahibi | Tek oluşturma sahibi (M06 D6 veya mevcut `BatchedODEEngine`); çift mikro bekleme yok | OS35–OS38 |
| F5-C.09 | Uzunluk kovaları | Belirlenimci kovalar, dolgu sınırı, adillik | `bucketing.md`; OS39–OS46 |
| F5-C.10 | RNG koruması | F5-B öğe başı gerçek şekil seed üretimi; permütasyon testleri | `rng_layout.md`; OS47–OS51 |
| F5-C.11 | Yerel adaptör | Kesin profil ızgarası/kontrol; gerçek NFE kaydı | `native_adapter.md`; OS52–OS56 |
| F5-C.12 | Kontrol sahipliği | F4-C istenen/desteklenen/planlanan/uygulanan eşlemesi | `prosody_controls.md` |
| F5-C.13 | Önbellek uyumu | Gerçek etkin kimliği profil seçimiyle genişlet | `cache_identity.md`; OS57–OS66 |
| F5-C.14 | Konuşmacı referans politikası | Sınırlı referans bildirimi; M03 yapıt hakları ve M07 gizlilik | OS67–OS68 |
| F5-C.15 | ECAPA metrikleri | Ön işleme, normalizasyon, kosinüs, kapsam; yerel değerlendirici yeteneği | OS69–OS74 |
| F5-C.16 | Perde metrikleri | Gerçek çıkarıcı üst verisi, sesli/null anlamı, yarım ton aralığı | OS75–OS79 |
| F5-C.17 | Kalibrasyon protokolü | Ayrık kalibrasyon/test kümeleri dondurulur; sızıntı denetimi | `calibration.md`; OS80–OS84 |
| F5-C.18 | Kira ve kurtarma | Kapsam yeniden kontrolü; tüm toplu iş kirası; aynı seed'le sınırlı yeniden deneme | `completion_recovery.md`; OS85–OS91 |
| F5-C.19 | F6 teslimi | Taze değiştirilemez `AudioChunk`, kesin sıra/örnek; rezervasyon | `f6_handoff.md` |
| F5-C.20 | Gözlem ve kipler | Güvenli toplu metrikler ve kanıt sınıfları; KAPALI/gölge/laboratuvar | `telemetry_modes.md`; OS92–OS94 |
| F5-C.21 | Benchmark tasarımı | Gelecek donanım/iş yükü, hedef matrisi ve önceki tabanlar dondurulur | `benchmark_protocol.md` |
| F5-C.22 | Belirlenimci doğrulama | OS01–OS102 gerçek eşlenmiş uygulamalar ve M08 sahteleriyle | `test_results.json` |
| F5-C.23 | Regresyon ve geri dönüş | Taban uyumu, yalıtılmış geri dönüş | `regression_rollback.md`; OS95–OS102 |
| F5-C.24 | Kabul ve devir | F5-C-G00…G19 gerçek kanıt ve gözden geçiren; F5-D devri | `acceptance.md` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| OS01 | W2 hazırlığı true ama WG kabulü yok | Düzenlemeden önce HOLD; yerel veya kaynak değişikliği yok |
| OS02 | F4-C kabulken F5-B kapısı yok | Eksik bağımlılıkla HOLD; uygulama yok |
| OS03 | Önceki plan hash'leri onaylı bildirimden farklı | HOLD ve kesin uyuşmazlık raporu |
| OS04 | Onaylı entegre anlık görüntüde ilgisiz kirli dosyalar | Envanter ve koruma; sıfırlama yok |
| OS05 | İki aday toplu iş işçisi bulunur | Belgeli mevcut sahip seçilir veya HOLD |
| OS06 | Geliştirilmiş kapalıyken eski Euler32 çağrısı | Tam olarak mevcut kabul edilmiş sağlayıcı çağrısı |
| OS07 | Gölge üst veri açık | Yerel çağrı, önbellek yazması, yayın veya ek oynatma yok |
| OS08 | Yerel yetenek yalnız beyan edilmiş | Doğrulanmış değil; deneysel profil kapalı kalır |
| OS09 | Plan `normalization_passes=2` | Önbellek veya GPU'dan önce ret |
| OS10 | Kanonik Leyla profilinde plan `seed=42` | Yetkisiz seed reddi; ikame yok |
| OS11 | Onaylı A/B seed 77 | Seed ve deney kapsamı korunur; üretim etkinleşmesi yok |
| OS12 | Model veya dağarcık revizyonu sabit planla uyuşmaz | Bayat veya uyumsuz plan reddedilir |
| OS13 | Eşit metinli ama farklı koşullandırmalı iki değiştirilemez plan | Ayrı yürütme |
| OS14 | Desteklenmeyen IPA kontrol isteği | Yalnız rehber veya tipli zorunlu kontrol reddi |
| OS15 | F4-C hızı F6'ya atadı | F5 hız uygulamaz; güncel durum iletilir |
| OS16 | F4-C hızı 0,90, yerel destek bilinmiyor, WSOLA asgari 0,94 | Sessiz kırpma yok; açık desteklenmiyor veya onaylı indirme |
| OS17 | Yalnız Euler32 onaylı | Yalnız taban seçilir; kalibre olmamış hızlı profil asla |
| OS18 | Euler8 beyan edilmiş ama sağlayıcı 8 adımı reddeder | Profil yeteneği desteklenmiyor |
| OS19 | Euler16 yalnız kısa karşılama için geçerli; uzun kritik kod | Kalibrasyon genellenmez |
| OS20 | Gerçek yerel NFE nominal adımdan farklı | Gerçek NFE ve ızgara kaydedilir; yeniden etiketleme yok |
| OS21 | Eşit tahmini maliyetli iki kalibre uygun profil | Belirlenimci onaylı öncelik |
| OS22 | Tüm profiller son tarih tahminini kaçırır | Yetkisiz düşük kalite yok; M06 üzerinden erteleme/hata |
| OS23 | Model güncellemesinden sonra bayat kalibrasyon revizyonu | Yeni işler için profil etkinleşmesi geçersiz |
| OS24 | Etkinleştirilmemiş Euler48 isteği | Gönderim yok; kapalı raporlanır |
| OS25 | Maliyet tahmini null, taban uygun | Muhafazakâr taban kabulü; sahte ölçüm yok |
| OS26 | Yerel iş sırasında profil tercihi değişir | Sabit etkin yürütme etkilenmez |
| OS27 | İş ile tahmin arasında saat alanı uyuşmazlığı | Karşılaştırma reddi; tipli bilinmiyor |
| OS28 | Maliyet tahmini NaN veya negatif | Tahmin reddi; güvensiz kabul yok |
| OS29 | Son tarih geçmiş | Yeni gönderim yok; süresi dolmuş sonuç |
| OS30 | Aday maliyeti 60 ms, pay 63 ms, güvenlik marjı 5 ms | Oluşturma beklemesi yok ve uygulanabilir değil |
| OS31 | Eklemeyle en erken üye son tarihi kısalır | Sınır yeniden hesaplanır; ekleme reddi veya gönderim |
| OS32 | Mikro bekleme sırasında daha yüksek öncelikli final ASR | M06 politikaya göre beklemeyi durdurur |
| OS33 | Akransız acil ilk parça | Kabul edildiyse tekil gönderim; dolu toplu iş beklenmez |
| OS34 | Bölünmeden sonra kuyruğa yeniden ekleme | Özgün kuyruk/son tarih korunur; yenilenmiş bekleme bütçesi yok |
| OS35 | Varsayılan profilde P2 ilk ve P4 sonraki adaylar | Karışık öncelikli toplu iş yok |
| OS36 | P7 laboratuvar ve P2 canlı aday | Asla birlikte toplu işlenmez |
| OS37 | Eşit uzunluk ama farklı çözücü ızgarası | Uyumsuz; ayrı gönderim |
| OS38 | Aynı uyum alanları ama bağımsız doğrulanmış koşullandırma | Gruplanabilir |
| OS39 | Gerçek uzunluk 40 ve 44 | Dolgulu 88, geçerli 84, dolgu 4; tahmini VRAM yok |
| OS40 | Gerçek uzunluk 4 ve 100, dolgu sınırı 0,25 | Bölme veya tekil; asla kırpma |
| OS41 | Uzun uygun iş daha kısa kova tarafından sürekli atlanır | Adillik/azami bekleme uygulanır |
| OS42 | Bilinmeyen sağlayıcı uzunluk boyutu | Tahmin reddi/etkilenen toplu iş gönderimden önce HOLD |
| OS43 | Azami toplu iş 4 ve beş uyumlu iş | Sınırlı oluşturma en fazla 4; fazlası kalır |
| OS44 | Oturumlar arası küresel bekleyen sınırı doldu | Gizli taşma olmadan ret/erteleme |
| OS45 | F6 rezervasyonu yok | GPU F6'yı beklerken tutulmaz; uygun iş ertelenir |
| OS46 | Aynı iş için eşzamanlı oluşturma geri çağrıları | Tek M06 talebi/gönderimi; yineleme reddi |
| OS47 | Seed 9 gerçek şekli sabit, akran uzunluğu değişir | Aynı sahte üreteçte aynı başlangıç latenti |
| OS48 | Ters toplu iş sırası | Aynı öğe latenti ve doğru çıktı indeksi eşlemesi |
| OS49 | Akran seed'i 42'den 123'e değişir | Seed 9 hedef latenti değişmez |
| OS50 | Gönderimden önce akran iptali | Kalan gerçek latent değişmez; düzen güvenle yeniden hesaplanır |
| OS51 | Gönderimden sonra akran iptali | Akran teslimi bastırılır; ortak kira tutulur; diğer öğe geçerli |
| OS52 | Sağlayıcı eşleme fikstüründe ters maske kutupluluğu | Koruma reddeder; dalga kabul edilmez |
| OS53 | Geçerli sınırda dolgu değeri değişimi | Sayısal sızıntı tespiti veya doğrulanmış maske gerekir |
| OS54 | VAE çıktı uzunluğu dolgu içerir | Yalnız doğrulanmış eşlemeyle kırpma; belirsiz kırpma reddi |
| OS55 | Latent tahsisinde tamsayı taşması | Yerel tahsisten önce ret |
| OS56 | Yinelenen üye başvurusu | Toplu iş reddi; çift teslim yok |
| OS57 | Aynı metin/seed Euler16 ile Euler32 | Farklı etkin önbellek kimliği; çapraz isabet yok |
| OS58 | Aynı adım sayısı ama zaman ızgarası revizyonu değişir | Iska veya bypass; bayat dalga yok |
| OS59 | F4-C model uygulamalı hız değişir | Önbellek kimliği değişir |
| OS60 | Yalnız F6 duraklama üst verisi değişir ve ham değişmezlik kanıtlı | Uygun ham yeniden kullanım; taze sınır üst verisi |
| OS61 | Tekile eşdeğer kalibre edilmemiş karışık düzen | Düzene özgü anahtar veya bypass |
| OS62 | Özel fiyat/plaka metni önceki girdiyle eşleşir | Paylaşılan önbellek bypass; özel anahtar ifşası yok |
| OS63 | Eski generation zarflı önbellek isabeti | Yalnız ham yük ödünç; taze güncel zarf |
| OS64 | Önbellek kabulünden önce profil kalibrasyonu iptal | Etkilenen isabet engellenir; önceki plan değişmez |
| OS65 | F4-C kontrol üst verisi yok | Açık yalnız-ipucu/uyumlu taban veya HOLD |
| OS66 | Desteklenmeyen perde isteği | Perde kaydırma veya jeton enjeksiyonu yok; durum kaydedilir |
| OS67 | Hakları temizlenmemiş referans dosyası | Değerlendirme yok; korunan içerik okunmadan HOLD |
| OS68 | Testle aynı modelden referans | Öz-tutarlılık etiketi; insan kimliği değil |
| OS69 | ECAPA yerel yapıtı yok | İndirme yok; laboratuvar HOLD; taban sentez etkilenmez |
| OS70 | Geçerli vektörler [1,0] ve [1,0] | Yalnız fikstür kosinüs 1; konuşmacı doğrulaması yok |
| OS71 | Geçerli vektörler [1,0] ve [0,1] | Fikstür kosinüs 0; uydurma eşik yok |
| OS72 | Sıfır norm veya sonlu olmayan gömme | Nedenle null skor; metrik reddi |
| OS73 | Yanlış gömme boyutu | Karşılaştırma reddi; kırpma/dolgu hilesi yok |
| OS74 | Çoklu referans skorları 0,8/0,9/0,7 | Önceden beyan edilen ortalama 0,8 ve kapsam; en yüksek seçilmez |
| OS75 | Tamamen sessiz harfli klip fikstürü | Uygun çerçeve varsa F0 null, ses oranı 0 |
| OS76 | Uygun çerçeve yok | Kapsam ve F0 null; 0 Hz değil |
| OS77 | p10/p90'da geçerli sesli F0 100/200 Hz fikstürü | 12 yarım ton aralık; açık birimler ve uç noktalar |
| OS78 | Sesli çerçevede NaN/negatif F0 | Geçersiz işaret; kapsam raporu; uydurma ikame yok |
| OS79 | Farklı prozodili eşleşen metin | Yalnız hizalı geçerli bölgeler karşılaştırılır |
| OS80 | Kalibrasyon ve test aynı anlamsal şablon grubunu paylaşır | Sızıntı tespit edilir; protokol reddi |
| OS81 | Onaylı aynı/farklı konuşmacı etiketi yok | FAR/FRR iddiası yok; skor dağılımı raporlanır |
| OS82 | Geçerli dalga için yalnız düşük kosinüs | Otomatik canlı yeniden deneme, seed veya konuşmacı değişimi yok |
| OS83 | Kalibrasyondan sonra model güncellemesi | Yeni revizyon için kalibrasyon geçersiz; profil kapalı kalır |
| OS84 | Sentetik gidiş-dönüş hatası iyileşir | Yalnız birleşik metrik raporlanır; insan MOS iddiası yok |
| OS85 | Generation commit'inden sonra yerel geri çağrı | Yayın yok; gerçek kira bırakılır |
| OS86 | Sağlayıcı cihaz bitmeden ana makineye döner | Kira doğrulanmış bitişe kadar tutulur |
| OS87 | Yinelenen toplu iş tamamlanma geri çağrısı | Eşleşen kira için tam bir bırakma |
| OS88 | CPU somutlaştırmasından sonra F6 kuyruğu dolu | CPU sahipliği izlenir; yeniden çıkarım yok |
| OS89 | Yeniden denenebilir koruma hatası, terminal doğrulanmış, güncel kapsam | En fazla bir deneme |
| OS90 | İkinci deneme başarısız | Terminal hata; üçüncü deneme yok |
| OS91 | Terminali bilinmeyen OOM | Karantina; hemen yeniden deneme veya zorla sıfırlama yok |
| OS92 | Geçerli süre 2 s ve duvar 0,4 s olan toplu iş | Tanımlı sınır için RTF 0,2 |
| OS93 | Gecikme örneğinde olmayan süresi dolmuş veya iptal edilmiş vakalar | Denenen/süresi dolan sayıları raporlanır; sessiz dışlama yok |
| OS94 | Yoklayıcı ayırıcı rezerve ve cihaz kullanılan bildirir | Ayrı kaynaklar; çift sayım yok |
| OS95 | Sahte yerelle gerçek F5-B/C/M02/M06 üzerinden F4-C planı | Kesin metin, profil/seed ve tek teslim |
| OS96 | F6-B noktası üzerinden F1-B duraklatma sonra aynı generation devamı | Yeniden seed veya yinelenen parça yok |
| OS97 | Eşzamanlı F2-C P5 ve P1 artı ilk TTS P2 | Gerçek M06 önceliği/kabulü ve adillik |
| OS98 | Bir sentetik hata ama kalıcı gerçek hata kanıtı yok | F5-D araştırma uygunluğu yok |
| OS99 | Yerel iş sürerken geliştirilmiş profilin geri alınması | Etkilenen çıktı çitlenir; sonuçlandır/karantina |
| OS100 | Özel metin, gömme ve hash içeren telemetri fikstürü | Yalnız güvenli izin listeli alanlar |
| OS101 | Tüm zorunlu yapısal vakalar geçti ama gerçek benchmark yok | Yapısal profil hazır; performans NOT_RUN |
| OS102 | Regresyon paketinde açıklanamayan taban hatası | Kapı FAIL/HOLD; toptan PASS yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F5-C-G00 | Ön kontrol | Gerçek çekirdek/W2 ve F5-B/F4-C kabulü, onaylı soy ve sahip izni; OS01–OS08 |
| F5-C-G01 | Tek sahip | Tek yükleyici, oluşturma sahibi, önbellek ve zamanlayıcı; envanter eşlenmiş |
| F5-C-G02 | Plan | Değiştirilemez kesin hazır plan, revizyon/seed ve özel sözleşmeler doğrulanmış; OS09–OS16 |
| F5-C-G03 | Profiller | Sabit taban Euler32 ve ayrık profil yeteneği/etkinleşmesi; desteklenmeyen profiller kapalı; OS17–OS20 |
| F5-C-G04 | Maliyet | Tipli, muhafazakâr, bayatlığa duyarlı maliyet tahminleri; sahte ölçüm yok; OS27–OS34 |
| F5-C-G05 | Seçim | Belirlenimci seçim, kalibre kalite tabanı, sessiz düşürme yok; OS17–OS26 |
| F5-C-G06 | Son tarih | Son tarih duyarlı sınırlı bekleme, P1/P2 önceliği, çift mikro bekleme yok; OS27–OS34 |
| F5-C-G07 | Toplu iş | Uyumlu oluşturma, uzunluk kovaları, adil küresel/oturum başı sınırlar; OS35–OS46 |
| F5-C-G08 | RNG ve düzen | Öğe başı gerçek uzunluk RNG, maske ve kod çözücü sözleşmesi; doğrulanmamış toplu yerel kapalı; OS47–OS56 |
| F5-C-G09 | Yerel adaptör | Mevcut sağlayıcı eşlemesi, gerçek ızgara/NFE anlamı, ham çıktı doğrulaması; OS47–OS56 |
| F5-C-G10 | Kontrol sahipliği | F4-C istenen/desteklenen/uygulanan sahipliği; çift hız/duraklama/normalizasyon yok; OS57–OS66 |
| F5-C-G11 | Önbellek | F5-B kesin önbellek kimliği, gizlilik ve ödünç alan yalıtımı; OS57–OS66 |
| F5-C-G12 | Konuşmacı kimliği | Referans hakları, ECAPA adaptör/metrik yapısal doğruluğu; gerçek değerlendirici yoksa isteğe bağlı HOLD; OS67–OS74 |
| F5-C-G13 | Perde ve kalibrasyon | Perde sesli/null anlamı ve kalibrasyon protokolü; gerçek akustik kanıt onaylanana kadar NOT_RUN; OS75–OS84 |
| F5-C-G14 | Tamamlanma | M06 fiziksel tamamlanma ve M02 iptali; sınırlı aynı seed yeniden deneme; OS85–OS94 |
| F5-C-G15 | F6 ve gizlilik | Ham F6 devri, geri basınç, telemetri gizliliği ve uyum; OS95–OS102 |
| F5-C-G16 | Entegrasyon | Gerçek entegre sahipler çalıştırılmış; sahte tam katman yok; laboratuvar/canlı kipler güvenli; OS95–OS102 |
| F5-C-G17 | Test kanıtı | OS01–OS102 zorunlu belirlenimci vakalar kayıtlı; açıklanamayan güvenlik hatası yok |
| F5-C-G18 | Regresyon | Önceki regresyonlar ve geri dönüş doğrulanmış; gelecek benchmark protokolü dondurulmuş |
| F5-C-G19 | Devir | Bağımsız kanıt incelemesi, kesin hazırlık ve aşağı akış devri; desteklenmeyen etkinleştirme yok |

## 9. Kanıt

`evidence/F5-C/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `preflight.md`, `inventory.md`, `contract_mapping.md`, `solver_profiles.md`, `cost_model.md`, `selection_policy.md`, `deadline_policy.md`, `bucketing.md`, `rng_layout.md`, `native_adapter.md`, `prosody_controls.md`, `cache_identity.md`, `calibration.md`, `completion_recovery.md`, `f6_handoff.md`, `telemetry_modes.md`, `benchmark_protocol.md` (ODE 16/24/32/48 karşılaştırması: TTFA/RTF, konuşmacı benzerliği, perde, insan ABX — G4), `test_results.json`, `regression_rollback.md`, `acceptance.md`. Laboratuvar sonuçları `data/F5/lab-report-*.json`.

## 10. Geri dönüş

`f5.ode_profiles` ve `f5.deadline_batching` kapalı: taban Euler32 ve F5-B toplu iş. Kalibrasyon revizyonları ve laboratuvar sonuçları korunur. Kod `git revert`.

## 11. Devir

- **F5-D:** yalnızca gerçek, atfedilmiş, kalıcı bir hata kanıtı varsa (OS98) LoRA araştırması uygun olur; sentetik tek hata yeterli değildir.
- **F6-C:** hız sahibi F6 ise uygulama F6-C'de; F5 uygulamaz.
- **G4:** profil kalibrasyonu gerçek GPU'da; warm kısa parça TTFA p95 ≤ 500 ms, RTF p95 ≤ 0,30; konuşmacı benzerliği ve ABX insan değerlendirmesiyle.

## 12. Başlatma komutu

```
F5-C paketini uygula: docs/execution/packages/W4/F5-C-ode-kimlik.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F5-B ve F4-C kabulünü doğrula; ECAPA yerel yapıtı ve referans hakları yoksa laboratuvarı HOLD bırak.
Taban Euler32'yi koruyarak kalibrasyon kanıtlı ayrık ODE profilleri, son tarih duyarlı toplu iş ve uzunluk kovalarını kapalı profiller
altında kur; laboratuvar konuşmacı/perde metriklerini yalnız yapısal doğrula; düşük skorla canlı karar verme.
OS01–OS102'yi çalıştır, F5-C-G00…G19'u değerlendir, paket/F5-C dalında PR aç ve dur.
```
