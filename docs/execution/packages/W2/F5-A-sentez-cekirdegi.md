# F5-A — Sentez çekirdeği ve ham ses parçası

> F4'ün değiştirilemez `SynthesisPlan`'ını alır, `model_text`'i **değiştirmeden** mevcut kodlayıcıya verir; mevcut süre kestirici ve korumasını, seed'li latent üretimini (Leyla seed 9), Euler32 çözücüsünü, DiT ve AudioVAE kod çözücüsünü M06 üzerinden yürütür; gerçek tamamlanmayı bekler ve sonucu ham 48 kHz mono Float32 M01 `AudioChunk` olarak F6'ya bir kez teslim eder. Sessizlik, fade, EQ, yeniden örnekleme veya yeni çözücü ayarı eklenmez.

| Alan | Değer |
| --- | --- |
| Kimlik | F5-A |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, F4-A, M06 |
| Sonraki | F6-A, W2_GATE, F1-B, F5-B |
| Bayrak | `f5_pipeline_v2` (varsayılan kapalı) |
| Ortam | CPU (gerçek model yalnızca `@pytest.mark.gpu` testlerde; birim testleri sahte sağlayıcıyla) |
| Eski görevler | F5-T03, F5-T05, F5-T08, F5-T09, F5-T10, F5-T26, F4-T27 |
| Kaynak | Bundle `W2/Freya_2_0_F5_A_Agent_Implementation_Package.md`; [F5 spec](../../../stages/F5-neural-synthesis/spec.md), [F5 tasks](../../../stages/F5-neural-synthesis/tasks.md) |
| Durum | NOT_RUN |

## 1. Amaç

PoC'ta F5 metni yeniden temizliyor, sessizlik ve fade ekliyor, seed bazı yollarda sessizce düşüyordu (H01'de kapatıldı), GPU erişimi kendi kilidiyle yapılıyordu. F5-A sentezi **tek sorumluluğa** indirir: plan → ham dalga biçimi. Kalite denetimi, önbellek düzeyleri, ses profilleri ve yığın optimizasyonu F5-B/F5-C'dedir.

## 2. Başlamadan önce

- [ ] CORE_GATE, F4-A, M06 kabul edilmiş; onay; kapsamlı kaynak anlık görüntüsü.
- [ ] Tüm model/kodlayıcı/süre/çözücü/VAE/önbellek/ısıtma/yığın/genel/deneysel giriş noktaları ve özellik kimlikleri sınıflanmış.
- [ ] Mevcut RNG davranışı, latent oranı ve yuvarlama sözleşmesi, Euler32 zaman ızgarası kaynaktan doğrulanmış. Bilinmiyorsa katı yol HOLD (ör. "25 Hz" tahmin edilmez).
- [ ] Leyla referans kümesi (eski F5-T05) yalnızca G4'te gerçek ölçüm için gerekir; bu paketin kabulü için zorunlu değildir.

## 3. Kapsam

**Yapılacak:** Sözleşme eşlemesi; plan doğrulama ve kabul; model/ses görüntüsü bağlama; hazır kodlayıcı adaptörü; süre adaptörü ve koruması; seed'li latent adaptörü; Euler32 taban adaptörü; M06 istek ve kira köprüsü; DiT yürütme adaptörü; AudioVAE kod çözücü adaptörü; sağlayıcı tamamlanması; ham ses doğrulaması; `AudioChunk` oluşturma; önbellek/deney uyumu; atomik teslim; M03/M04; eski kod ve F6 noktası.

**Yapılmayacak:** Gerçek uzunlukta gürültü, öğe başı VAE, ses profilleri, önbellek düzeyleri, ön ısıtma, hızlı kalite denetimi, kontrollü yeniden sentez (F5-B); ODE profil karşılaştırması, kod çözücü optimizasyonu, speaker encoder, drift (F5-C); LoRA (F5-D); FreyaTTS ağırlık değişikliği; yeni ön ısıtma veya eğitim.

## 4. Dosyalar

```
backend/neural_synthesis/
  contracts_map.py  admission.py  binding.py  encoder_adapter.py  duration.py
  duration_guard.py  latent.py  solver_euler.py  scheduler_bridge.py  dit_adapter.py
  vae_adapter.py  completion.py  raw_audio.py  chunk_builder.py  cache_compat.py
  delivery.py  telemetry.py  legacy_bridge.py
tests/neural_synthesis/
evidence/F5-A/<run_id>/
```

`models.py` ve `batched_ode.py` silinmez; adaptörler mevcut tutamaçları ve ilkelleri yeniden kullanır.

## 5. Tasarım ve sözleşmeler

### 5.1 Hat

```
SynthesisPlan (F4, normalization_passes=1) ─► doğrulama/kabul ─► M03 model/ses/seed bağlama
  ─► kodlayıcı (model_text aynen) ─► süre kestirimi + koruma ─► seed'li latent
  ─► M06 iş (ilk parça P2, sonrakiler P4) ─► DiT + Euler32 ─► AudioVAE ─► gerçek tamamlanma
  ─► ham ses doğrulama (48 kHz mono FLOAT32_LE) ─► AudioChunk ─► M02 atomik teslim ─► F6
```

### 5.2 Değişmez kurallar

1. **Normalizasyon yok.** `normalization_passes` `null/0/2` olan plan katı yolda sentezlenmez. F5 hiçbir eski normalizasyon yolunu çağırmaz (casus sayısı 0, NS14). Kodlayıcıdaki gizli temizleme/ikame veya "zaten normalize" bayrağı katı yolda reddedilir. Desteklenmeyen kod noktası → güvenli ret; sessiz karakter düşürme yok.
2. **Plan değişmez.** İç içe değişim denemesi etkisiz; yetkisiz generation'da yeniden kullanım reddedilir; sözlük görüntüsü değişirse plan yeniden normalize edilmez.
3. **Seed:** M03 Leyla profili seed 9 mevcut RNG'ye aynen ulaşır; deneysel 42/77/123 bağımsız korunur, 9'a geri düşmez; eksik/geçersiz/bool seed tahsisten önce ret. Profil/model/yetenek revizyon uyuşmazlığı → ret/HOLD; sessiz model değişimi yok.
4. **Süre:** mevcut kestirici ve koruma anlamı ve birimleri korunur. Sıfır/negatif/NaN/Inf süre veya aşırı latent boyutu, latent tahsisinden **önce** reddedilir. Mevcut belgeli kırpma senaryosu etkin değeri ve nedeni korur. Latent oranı/yuvarlama bilinmiyorsa katı süre eşlemesi HOLD. Tahmin edilen bellek "gerçek VRAM" diye adlandırılmaz.
5. **Latent ve çözücü:** mevcut RNG davranışı, kesin seed/şekil/dtype/cihaz. Eski RNG güvenle yalıtılamıyorsa ilgili katı kip HOLD. Yanlış rank/kanal/düzen/dtype/cihaz → DiT'ten önce ret; düzleştirme/tahmin yok. Euler32 taban ayarları sağlayıcıya aynen gider; onaysız alternatif çözücü/adım reddedilir; eski açık alternatif profil yalnız özgün kapsamında kalır.
6. **GPU:** yalnız M06 (ilk parça **P2**, sonraki parçalar **P4**); başlangıçta generation başına tek bekleyen parça; doğrudan yerel çağrı yok. Kira, DiT + VAE + CPU'ya aktarım tamamlanana kadar tutulur. İptal mantıksal sonucu hemen çitler, kira terminal kanıta kadar korunur. Belirsiz cihaz durumu → M06 karantinası; sıfırlama veya süreç öldürme yok. OOM'da bağımsız yeniden deneme yok. Mevcut toplu iş motoru ile katı tek iş yolu: tek yığın/kabul otoritesi, ikinci kuyruk yok.
7. **Ham ses:** 48 kHz mono `FLOAT32_LE`; sonlu, sınırlı bayt; gerçek geçerli örnek sayısı. Beklenmeyen örnekleme hızı → HOLD/hata, F5 içinde yeniden etiketleme veya yeniden örnekleme yok. Çok kanal/çok yığın öğesi belirsizse ret. Boş/NaN/Inf dalga → ret; sıfır doldurma veya sahte ton yok. Süre gerçek baytlardan türetilir. Mevcut çökme koruması reddederse teslim yok.
8. **Kalite iddiası yok.** Yapısal doğrulama ayrı kaydedilir; akustik kalite `UNKNOWN/PENDING`. Plan duraklama/hız ipuçları üst veri olarak taşınır; sessizlik/fade eklenmez (F6).
9. **Önbellek:** revizyon/kökeni kesin olmayan eski önbellek katı yolda `BYPASS`; uydurma `HIT` yok. Onaylı uyumlu ham önbellek isabeti taze kapsamlı üst veri ve sahipli ses verir; oturumlar arası özel isabet yasak. Render edilmiş veya yanlış seed/hızlı girdi yeniden kullanılmaz. A/B, ısıtma, SFT/LoRA envanteri korunur; yeni etkinleştirme yok.
10. **Teslim:** M02 karşılaştır-ve-ekle atomik; bayat/revizyon/sıra çiti; tam bir kez talep; sınırlı tamponlar; fiziksel tamamlanma ayrı izlenir. Yinelenen/sırasız parça yayımlanmaz.

### 5.3 `AudioChunk`

M01 sözleşmesi (§M01 5.8): `generation_ref`, `plan_id`, `plan_revision`, `chunk_id`, `chunk_index`, biçim (48 kHz mono f32), `sample_count`, `actual_duration_ms` (gerçek örnekten), `voice_profile`, `seed`, istenen/etkin `model_revision`/`solver`/`ode_steps`, `cache_status`, `quality_status=PENDING/UNKNOWN`, `post_pause_ms` ve prozodi ipuçları (plandan, uygulanmamış), metrikler (`f5.queue_wait_ms`, `f5.inference_ms`, `f5.ttfa_ms`, `f5.rtf` — sahte saatte fikstür değeri, gerçek ölçüm değil).

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F5-A.01 | Çekirdek/F4/M06 ön kontrolü | Kapı yapıtları, soy, onay, kapsamlı anlık görüntü | Geçersizse düzenlemeden önce HOLD |
| F5-A.02 | Sentez envanteri | Model/kodlayıcı/süre/çözücü/VAE/önbellek/ısıtma/yığın/genel/deneysel giriş noktaları ve özellik kimlikleri | `F5_INVENTORY.json` |
| F5-A.03 | Sahiplik ve geçiş tasarımı | Tek katı giriş; tek model/yerleşiklik/zamanlayıcı otoritesi; kilit sırası; ham çıkış noktası; eski yönlendirme | `F5_DECISIONS.md` |
| F5-A.04 | Sözleşme eşlemesi | M01 plan/parça, M02/M06/M03 arayüzleri; yinelenen tür yok; açık eski bilinmeyenler | NS04 |
| F5-A.05 | Plan doğrulama ve kabul | Doğrulanmış değiştirilemez plan, kapsam, kesin revizyonlar, sınırlı benzersiz parçalar, konuşma yok işleme, tekilleştirme | NS05–NS12 |
| F5-A.06 | Model/ses görüntüsü bağlama | Onaylı M03 tanımlayıcıları, ödünç tutamaç kimliği, seed/profil kontrolleri | NS19–NS25 |
| F5-A.07 | Hazır kodlayıcı adaptörü | `model_text` aynen kodlayıcıya; F5 normalizasyon sayısı sıfır; eski metin yolu değişmez | NS13–NS18 |
| F5-A.08 | Süre adaptörü | Gerçek birimler, kestirici, jeton ve çerçeve anlamı; mevcut varsayılanlar | NS26, NS30–NS32 |
| F5-A.09 | Süre koruması | Latent oluşturmadan önce sonlu/sınırlı süre, şekil ve tahsis koruması; açık güvenli hatalar | NS27–NS29, NS33 |
| F5-A.10 | Seed'li latent adaptörü | Mevcut RNG, kesin seed/şekil/dtype/cihaz; güvenli katı tek yol veya HOLD | NS34–NS38 |
| F5-A.11 | Euler32 taban adaptörü | Mevcut Euler32 ayarları, zaman ızgarası ve çağrı sayısı anlamı statik doğrulanır; ayar yok | NS39–NS42 |
| F5-A.12 | M06 istek ve kira köprüsü | P2/P4, son tarih, tahminler, gerçek zamanlayıcı; başlangıçta generation başına bir bekleyen parça | NS43–NS46 |
| F5-A.13 | DiT yürütme adaptörü | Tutamaç/koşullandırma ve taban tek/toplu ilkeller; doğrudan GPU atlaması yok | NS53 |
| F5-A.14 | AudioVAE kod çözücü adaptörü | Gerçek çözme düzeni, ölçek, hız, dtype ve çıktı sahipliği | NS54–NS56 |
| F5-A.15 | Sağlayıcı tamamlanması | Yerel çözme/somutlaştırma boyunca kira; geç iptal ve belirsiz tamamlanma/karantina | NS47–NS52 |
| F5-A.16 | Ham ses doğrulaması | 48k mono FLOAT32_LE, sonlu sınırlı bayt, gerçek geçerli örnekler, eski çökme koruması; DSP yok | NS57–NS61 |
| F5-A.17 | `AudioChunk` oluşturma | Değiştirilemez M01 plan/parça kimliği, gerçek süre, etkin üst veri, kalite kapsamı ve kontrol ipuçları | NS62–NS63 |
| F5-A.18 | Önbellek ve deney uyumu | Mevcut yollar envanteri; kanıtlanmamışsa açık katı bypass; eski bayraklar/A/B/SFT/LoRA korunur | NS64–NS67 |
| F5-A.19 | Atomik teslim ve temizlik | M02 bayat/revizyon/sıra çiti, tam bir kez talep, sınırlı tamponlar, fiziksel tamamlanma ayrı | NS68–NS74 |
| F5-A.20 | Yapılandırma ve telemetri | Sabitlenmiş M03 başvuruları, M04 güvenli metrikler, kişisel veri yok, sahteden ölçüm iddiası yok | NS75–NS77 |
| F5-A.21 | Eski kod/F6 noktası | Mevcut dış sözleşme, F6 test alıcısı, yinelenen konuşma veya DSP yok, katı atlama denetimi | NS78–NS79 |
| F5-A.22 | Belirlenimci testler | NS01–NS80; gerçek F5 orkestrasyonu ve kabul edilmiş çekirdek; yalnız yerel/sağlayıcı sahte | Tüm testler çalıştırılmış |
| F5-A.23 | Regresyon ve geri dönüş | M00 özellik eşlemesi, etkilenen testler, güvenli geri dönüş provası, bütünlük | NS80 |
| F5-A.24 | Kabul ve devir | F5-A-G00…G19, bağımsız inceleme, F6-A/F5-B/F5-C devri; dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| NS01 | Onay veya çekirdek kapı kanıtı yok | Kaynak düzenleme veya model erişiminden önce HOLD |
| NS02 | F4-A veya M06 kabulü yok/bayat/uyuşmayan kaynak | Gerçek engelle HOLD; sahte hazırlık yok |
| NS03 | Model yükleme, GPU ve ağ tuzaklarıyla temiz içe aktarma | Yan etki veya ikinci kayıt yok |
| NS04 | Mevcut M01/M02/M06 tür eşlemesi ve geçersiz şema | Gerçek kabul edilmiş türler; uyumsuz şema reddedilir |
| NS05 | Geçerli değiştirilemez katı plan ve ardışık parçalar | Kapsamlı plan; kesin kimlikler ve sıralı işler |
| NS06 | Doğrulanmamış/bilinmeyen katı plan | Yerel istekten önce ret |
| NS07 | `normalization_passes` null, 0 veya 2 | Katı sentez yok; eski köken yükseltilmez |
| NS08 | Yinelenen parça kimlikleri veya ardışık olmayan indeksler | Gönderimden önce ret |
| NS09 | Boş açık "konuşma yok" planı | Model işi yok; sahte ses yok |
| NS10 | Konuşma parçasında boş `model_text` | Tipli hata; GPU tahsisi yok |
| NS11 | Aşırı büyük plan/parça veya desteklenmeyen kontrol | Sınırlı ret; sessiz kırpma yok |
| NS12 | Yinelenen plan/parça talebi, aynı kimlik farklı içerik | Yinelenen iş yok; çakışan yük reddedilir |
| NS13 | Korumalı para/tarih/model jetonlu geçerli F4 metni | Kesin `model_text` kodlayıcıya; kaynak ve plan değişmez |
| NS14 | F4 normalizasyonu bir kez, sonra F5 (tüm eski yollarda casus) | F5 hiçbirini çağırmaz (idempotent girdi dahil) |
| NS15 | Kodlayıcıda gizli temizleme/ikame veya genel "zaten normalize" bayrağı | Katı yol çözülmemiş dönüşümü/güvenilmeyen atlamayı reddeder |
| NS16 | Doğrulamadan sonra desteklenmeyen dağarcık/kod noktası | Güvenli ret; yeniden yazma veya sessiz düşürme yok |
| NS17 | Plan, parça veya eşlemede iç içe değişim denemesi | Kabul edilmiş plan değişmez/takma ad yok |
| NS18 | Geçerli planın yetkisiz generation'da yeniden kullanımı | Ret; yeniden etiketleme veya tekrar yok |
| NS19 | M03 onaylı Leyla profili seed 9 | Kesin seed mevcut RNG'ye ulaşır; gerçek üst veriyle eşleşir |
| NS20 | Onaylı deneysel seed 42/77/123 | Her biri bağımsız korunur; 9'a geri düşme yok |
| NS21 | Eksik/geçersiz/aralık dışı/bool seed | Tahsisten önce katı plan reddedilir |
| NS22 | Profil/model/yetenek revizyon uyuşmazlığı | Ret veya HOLD; sessiz model değişimi yok |
| NS23 | Generation sırasında sözlük görüntüsü değişir | Mevcut plan sabit kalır; yeniden normalizasyon yok |
| NS24 | Aynı onaylı modele eşzamanlı istekler | Kabul edilmiş M06 yerleşiklik tutamacı; ek yükleme yok |
| NS25 | Bir oturum kapanınca ödünç tutamaç bırakılır | Diğer oturumun modeli kullanılabilir kalır; sahip saygısı |
| NS26 | Geçerli jeton sayısı ve sonlu süre tahmini | Mevcut kestirici/koruma anlamı ve birimleri korunur |
| NS27 | Sıfır veya negatif tahmini konuşma süresi | Belgeli eski koruma yoksa latent tahsisinden önce ret; sahte konuşma yok |
| NS28 | NaN/Inf süre veya desteklenmeyen birimler | Ret, güvenli hata; bozuk metrik yok |
| NS29 | Aşırı süre/latent uzunluğu/şekil çarpımı | Tahsisten önce sınır kontrolü; bellek patlaması yok |
| NS30 | Mevcut belgeli süre kırpma senaryosu | İsteği gizlemeden etkin değer ve koruma nedeni korunur |
| NS31 | Bilinmeyen latent oranı/yuvarlama sözleşmesi | Katı süre eşlemesi HOLD; tahmini 25 Hz yok |
| NS32 | M06 bütçesi altında geçerli tahmin | Doğru istenen/etkin çerçeve ve bayt tahmini; "gerçek VRAM" denmez |
| NS33 | Önceden etkin yanıt varken süre koruması reddi | Yeni dalga biçimi veya geri düşme seed'i yok; güvenli hata ve temizlik |
| NS34 | Aynı seed ve aynı belirlenimci sahte tek iş latent girdileri | Fikstür beklenen seed'li diziyi üretir; gerçek akustik iddia yok |
| NS35 | Kontrollü sahte RNG durumuyla araya girmiş oturumlar | Etkin katı yolda oturumlar arası RNG kirlenmesi yok |
| NS36 | Eski RNG güvenle yalıtılamıyor | Etkilenen katı kip HOLD; eski yol açıkça sınıflanır |
| NS37 | Yanlış latent rank/kanal/düzen/dtype/cihaz | DiT/çözmeden önce ret veya HOLD; düzleştirme/tahmin yok |
| NS38 | Sonlu olmayan latent veya bozuk koşul tensörü | Ret; uydurma geçerli çıktı yok |
| NS39 | Kabul edilmiş Euler32 profili | Gerçek taban ayarları sağlayıcıya aynen; ızgara/adım anlamı doğrulanır |
| NS40 | Onaysız alternatif çözücü/adım isteği | Sessiz değişim yok; katı yol reddeder |
| NS41 | Eski açık alternatif profil | Yalnız özgün yetkili kapsamda kalır |
| NS42 | Sağlayıcı ODE ortasında hata verir | Kısmi sonuç tamamlanmış konuşma sayılmaz; belirsizlik izlenir |
| NS43 | İlk konuşma parçası kabul edildi | Gerçek kapsam, son tarih ve maliyetle P2 M06 isteği |
| NS44 | Sonraki konuşma parçası | P4; önceki/sıra ve sınırlı bekleyen iş uygulanır |
| NS45 | Son tarih geçti veya zamanlayıcı kabulü reddedildi | Yerel gönderim yok; açık neden |
| NS46 | GPU bütçesi yok veya tahmin geçersiz | Gerçek M06 güvenli kabul/HOLD; doğrudan yerel çağrı yok |
| NS47 | Sahte sağlayıcı erken tensör/future döndürür | Kira doğrulanmış tamamlanma ve somutlaştırmaya kadar tutulur |
| NS48 | Yerel DiT çalışırken iptal | Mantıksal sonuç çitlenir; kira tutulur |
| NS49 | AudioVAE çözme veya CPU aktarımı sırasında iptal | Çıktı teslimi yok; kira terminal kanıta kadar |
| NS50 | Yinelenen tamamlanma geri çağrısı | Tam bir muhasebe bırakması; yinelenen `AudioChunk` yok |
| NS51 | Sağlayıcı belirsiz cihaz durumuyla hata fırlatır | M06 karantinası; erken bırakma/sıfırlama/süreç öldürme yok |
| NS52 | OOM ve izinli M06 kurtarması | Bağımsız yeniden deneme yok; yalnız gerçek tamamlanmadan sonra taze kabul, değişmemiş plan/ayarlar |
| NS53 | Mevcut toplu iş motoru rotası ve katı tek iş yolu | Tek yığın/kabul otoritesi; ek bekleme/ikinci kuyruk yok; eski korunur |
| NS54 | Geçerli sahte VAE tekil mono çıktı | Doğru ham 48k f32 eşlemesi ve kesin baytlar |
| NS55 | Kod çözücü beklenmeyen örnekleme hızı bildirir | HOLD/hata; F5 içinde yeniden etiketleme veya yeniden örnekleme yok |
| NS56 | Bir parça için çok kanal veya çok yığın öğesi | Belirsiz düzen reddedilir; kör sıkıştırma/düzleştirme yok |
| NS57 | Boş/NaN/Inf dalga biçimi | Ret; sıfır doldurma veya sahte ton yok |
| NS58 | Dtype dönüşümü veya bayt sırası | Açık doğru FLOAT32_LE baytlar, dönüşüm sonrası sonlu, özgün örnek anlamı |
| NS59 | Gerçek örnek sayısı tahminden farklı | Süre gerçek baytlardan; belgeli koruma/tolerans; uydurma eşleşme yok |
| NS60 | Devasa yük veya bayt uzunluğu uyuşmazlığı | Sınırlı ret; bozuk `AudioChunk` yok |
| NS61 | Mevcut çökme koruması çıktıyı reddeder | Teslim yok; gerçek koruma sonucu kaydedilir; akustik PASS yok |
| NS62 | Geçerli ama ölçülmemiş akustik dalga | Yapısal doğrulama ayrı; kalite UNKNOWN/PENDING |
| NS63 | Plan duraklama/hız ipuçları | Üst veri korunur; eklenen sessizlik/fade veya yetkisiz yeni hız yok; uygulanmış mevcut kontrol açıkça kaydedilir |
| NS64 | Eski önbellekte kesin revizyon/köken yok | Katı BYPASS; eski değişmez; uydurma HIT yok |
| NS65 | Onaylı mevcut uyumlu ham önbellek isabeti | Taze kapsamlı üst veri, sahipli ses, yerel iş yok; oturumlar arası özel isabet yasak |
| NS66 | Render edilmiş veya yanlış seed/hızlı önbellek girdisi | Katı yeniden kullanım reddedilir; yeniden etiketleme veya anlamsal ikame yok |
| NS67 | A/B, ısıtma ve isteğe bağlı SFT/LoRA envanteri | Özgün özellik/bayraklar korunur; yeni etkinleştirme veya gerçek model çalıştırma yok |
| NS68 | Çıktı eklenmeden hemen önce generation iptali | Atomik karşılaştır-ve-ekle bayat çıktıyı reddeder |
| NS69 | Yeni tur veya plan revizyonu tamamlanmış parçayı geçersiz kılar | Eski sonuç güncel planı değiştirmeden reddedilir |
| NS70 | Aynı parça indeksli araya girmiş iki oturum | Kapsamlı kimlikler/yük sahipliği yalıtılmış |
| NS71 | Yinelenen/sırasız parça gelişi | Yinelenen veya sıra dışı yayın yok; sınırlı hata/bekletme |
| NS72 | Yerel iş sürerken oturum kapanışı | Yeniden giriş yok; fiziksel tamamlanma/karantina sahipliği korunur |
| NS73 | Tüketici geri basıncı/kopma | Sınırlı tampon ve temizlik; sahte teslim/oynatma yok |
| NS74 | Yumuşak duraklatma veya eski çıktı iptali ile yeni giriş | Mevcut M02 kapsam anlamı korunur; ilgisiz girişe dokunulmaz |
| NS75 | Sahte zamanlama örnekleri ve eksik üst veri | M04 doğru aynı saat sınırları; RTF gerçek fikstür paydası; bilinmeyen null; duyulan TTFA iddiası yok |
| NS76 | Telemetri abonesi taşması/hatası | Yerel tamamlanma ve çit etkilenmez; güvenli gözlem kaybı kaydedilir |
| NS77 | Sentetik kişisel veri metin/ses/latent/hata yükü | Günlük, metrik, kanıt veya paylaşılan önbellekte ham/hassas veri veya hash yok |
| NS78 | Gerçek F4 planı → gerçek F5 orkestrasyonu → kaydeden F6 alıcısı | Kesin `model_text` ve değiştirilemez `AudioChunk`; F6 DSP veya gerçek aktarım yok; gerçek F6 entegrasyonu NOT_RUN |
| NS79 | Mevcut genel TTS yolları, model varsayılanları, önbellek, yığın, ses, özellik kimlikleri ve katı GPU atlama denetimi | Beyan edilen kapsamda uyum doğrulanmış; çözülmemiş kritik atlama engelleyici |
| NS80 | Yalıtılmış kopyada regresyon, bütünlük ve geri dönüş provası | İlgisiz düzenleme/veri değişikliği yok; gerçek kanıt hash'leri ve doğru kabul değerlendirmesi |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F5-A-G00 | Ön kontrol | Onay ve gerçek CG00–CG11/F4-A/M06 önkoşulları kaynak soyuna uygun |
| F5-A-G01 | Tek giriş | Tek katı sentez girişi/model yerleşiklik otoritesi; tüm yollar envanterde; içe aktarma yan etkisiz |
| F5-A-G02 | Sözleşme | Gerçek M01/M02/M06 sözleşmeleri; değiştirilemez plan ve kapsamlı sınırlı kabul |
| F5-A-G03 | Görüntü ve seed | M03 görüntüsü, kesin ses/seed ve gerçek yapıt/yetenek uyumu; sessiz ikame yok |
| F5-A-G04 | Metin | Hazır `model_text` değişmez; katı yolda F5 normalizasyon çağrısı sıfır; eski korunur |
| F5-A-G05 | Süre | Mevcut süre kestirici/koruma; açık birim/sınırlar; geçersiz tahsis engellenir |
| F5-A-G06 | Latent | Mevcut seed'li latent anlamı ve güvenli katı RNG yalıtımı; doğrulanmamış yığın kipleri kapalı |
| F5-A-G07 | Çözücü | Onaylı taban Euler32 ayarları, gerçek adım anlamı; gizli çözücü değişikliği yok |
| F5-A-G08 | Zamanlayıcı | Gerçek M06 P2/P4 bütünleşmesi; sınırlı işler; katı yerel atlama yok |
| F5-A-G09 | Tamamlanma | VAE/somutlaştırma boyunca sağlayıcı tamamlanması; kira ve karantina anlamı doğru |
| F5-A-G10 | Kod çözücü | Gerçek biçim/düzen eşlemesi; ham 48k mono f32; hız yeniden etiketleme yok |
| F5-A-G11 | Yapısal ses | Yapısal ses koruması ve M01 `AudioChunk` tutarlılığı; ölçülmemiş akustik başarı iddiası yok |
| F5-A-G12 | Önbellek/deney | Önbellek/deney uyumu; güvensiz katı yeniden kullanım engelli; yeni eğitim veya ısıtma etkinleştirmesi yok |
| F5-A-G13 | Teslim | M02 atomik generation çiti, sıralı tekilleştirilmiş teslim ve güvenli yaşam döngüsü |
| F5-A-G14 | Gözlem/gizlilik | M04 güvenli metrikler, M07 gizlilik, gözlem hatası yalıtımı |
| F5-A-G15 | Uyum | Eski API/özellikler korunmuş; katı atlama denetimi temiz veya güvenle engellenmiş |
| F5-A-G16 | Uçtan uca | Gerçek F4 planı → F5 orkestrasyonu → test F6 alıcısı; render ertelenmiş ve açık etiketli |
| F5-A-G17 | Test kanıtı | NS01–NS80 zorunlu testler geçerli kanıtla çalıştırılmış ve geçmiş |
| F5-A-G18 | Regresyon | Etkilenen regresyon, kaynak bütünlüğü, yalıtılmış geri dönüş provası, izinsiz değişiklik yok |
| F5-A-G19 | Devir | Bağımsız inceleme, tam devir, kapsamlı hazırlık; ertelenen performans/akustik durumu açık |

## 9. Kanıt

`evidence/F5-A/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F5_INVENTORY.json`, `F5_DECISIONS.md`, `SOLVER_AND_DURATION_AUDIT.md` (Euler32 ızgarası, latent oranı, yuvarlama — kaynaktan), `RNG_ISOLATION.md`, `CACHE_COMPATIBILITY.csv`, `STRICT_BYPASS_AUDIT.csv`, `TEST_MATRIX.json`. Belirleyicilik ve kabul cümlesi kararlılığı analizi (eski F5-T03) gerçek modelle yapılırsa `data/F5/lab-report-determinism-*.json` (`@pytest.mark.gpu`).

## 10. Geri dönüş

`f5_pipeline_v2=off`: eski sentez yolu tek aktif. Adaptörler mevcut tutamaçları ödünç aldığı için model durumu etkilenmez; kod değişiklikleri `git revert` ile geri alınır.

## 11. Devir

- **F6-A:** ham 48 kHz mono f32 `AudioChunk`; sessizlik/fade/EQ/yeniden örnekleme yapılmamış; duraklama ve prozodi yalnızca ipucu. F6 bunları **bir kez** uygular.
- **F1-B:** generation kimlikleri ve iptal çiti söz kesme orkestrasyonuna girdi.
- **F5-B:** gerçek uzunlukta gürültü, öğe başı VAE, ses profilleri, önbellek düzeyleri, ön ısıtma, hızlı kalite denetimi, parça dağıtıcı.
- **F5-C:** ODE profil karşılaştırması (16/24/32/48), kod çözücü optimizasyonu, speaker encoder ve kimlik eşiği, drift.
- **G4:** warm kısa parça TTFA p95 ≤ 500 ms, RTF p95 ≤ 0,30 hedeflerinin gerçek ölçümü.

## 12. Başlatma komutu

```
F5-A paketini uygula: docs/execution/packages/W2/F5-A-sentez-cekirdegi.md.
Kuralları CLAUDE.md'den oku; CORE_GATE, F4-A ve M06 kabulünü doğrula; Euler32, latent oranı ve RNG'yi kaynaktan denetle.
backend/neural_synthesis/ altında plan → ham AudioChunk yolunu f5_pipeline_v2 arkasında kur;
model_text'i değiştirme, seed 9'u koru, GPU'ya yalnız M06'dan git, DSP ekleme.
NS01–NS80'i çalıştır, F5-A-G00…G19'u değerlendir, paket/F5-A dalında PR aç ve dur.
```
