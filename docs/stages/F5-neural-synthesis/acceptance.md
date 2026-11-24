# F5 — Kabul Kriterleri ve Testler

> **Bu hedeflerin hiçbiri gerçekleştirilmiş deney sonucu değildir.** Bir kutu yalnızca test çalıştırılıp sonucu laboratuvar raporuna (`data/f5/lab-report-*.json`) yazıldıktan sonra işaretlenir. MOS ve ABX gerçek dinleyicilerle yapılır; simüle edilmez. Özellikle RTX 4070'te bütün modeller yüklüyken kısa cümlecikler için 500 ms hedefinin gerçekçi olup olmadığı benchmark ile belirlenir. Hedef değişirse gerekçesiyle bu dosyaya yazılır.

**Ölçüm kuralları:**
- Her performans metriği şu koşullarla birlikte raporlanır: önbellek isabeti/ıskası, soğuk/sıcak model, metin uzunluğu sınıfı, yığın profili, **tüm modeller yüklü** VRAM durumu.
- **F5 TTFA** (sentez isteğinden ilk kullanılabilir parçaya) ile **uçtan uca TTFA** (müşteri konuşmayı bitirdiğinden ilk sesin karşı uçta duyulmasına) ayrı metriklerdir.
- Akustik kimlik eşikleri Leyla referans kümesinden kalibre edilir; evrensel eşik kullanılmaz.

---

## 1. Kalite kapısı

### 1.1 Plandaki hedefler

| # | Metrik | Önerilen hedef | Ölçüm tanımı | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K01 | Warm F5 TTFA p95 — kısa cümlecik | ≤ 500 ms | Sıcak model, önbellek ıskası, ≤ 15 karakter / ≤ 3 sözcük; tüm modeller yüklü | T31 | ☐ |
| K02 | Önbellekten ilk ses p95 | ≤ 50 ms | L0/L1 isabetinde | T25 | ☐ |
| K03 | RTF p95 | ≤ 0,30 | T_çıkarım / T_ses; Single Call profili | T15, T37 | ☐ |
| K04 | Geçersiz ses örneği | 0 | NaN/Inf içeren çıktı | T17 | ☐ |
| K05 | Sessiz/geçersiz sentezin oynatılması | 0 | Q1 FAIL olup F6'ya giden parça | T18, T20, T36 | ☐ |
| K06 | Kontrolsüz seed değişimi | 0 | Profil değişimi olmadan farklı seed ile üretilen parça | T10, T11, T21 | ☐ |
| K07 | Eski generation ID oynatılması | 0 | F6'ya ulaşan eski generation parçası | T32, T33 | ☐ |
| K08 | GPU OOM — tek görüşme profili | 0 | 60 dk tek görüşme yükünde OOM | T28, T37 | ☐ |
| K09 | Otomotiv terim doğruluğu | ≥ %95 | Sentez → Whisper geri tanıma (F2 metriği) + uzman dinlemesi örneklemi; 48 kHz ve 8 kHz ayrı | T24 | ☐ |
| K10 | Speaker Similarity | Referansla kalibre edilmiş PASS eşiği | Leyla referans dağılımına göre | T23 | ☐ |
| K11 | F0 Drift | Referansla kalibre edilmiş sınır | Median F0 ve F0 std sapması | T22 | ☐ |
| K12 | MOS | İnsan dinleme hedefi ≥ 4 / 5 | Kör test, gerçek dinleyiciler | AŞAMA 4 | ☐ |
| K13 | ABX | İnsan dinleyiciyle doğrulanmalı | Yeni sürüm ile referansın ayırt edilebilirliği | AŞAMA 4 | ☐ |
| K14 | Sentez hata oranı | ≤ %1 | Kurtarma sonrası güvenli hataya düşen parça oranı | T21, T29 | ☐ |

### 1.2 PoC incelemesine dayanan ek kriterler (öneri)

| # | Metrik | Önerilen hedef | Gerekçe | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K15 | Yığın bağımsızlığı | Aynı metin + seed, tek başına ve yığın içinde: dalga formu SNR ≥ 40 dB **ve** speaker similarity farkı REVIEW eşiğinin altında | Gürültü en uzun öğeye göre üretiliyor, VAE dolgulu latent üzerinde çalışıyor (spec §3.3 N1, N2) | T12, T13 | ☐ |
| K16 | Planlanmamış eşzamanlı TTS GPU yığını | 0 | Toplu yolda kilit yok (N4) | T28, T29 | ☐ |
| K17 | İptal sonrası sentezlenen parça | Yığına alınmadan önce iptal edilen parçalardan 0 | İptal edilenler yine sentezleniyor (N5) | T32 | ☐ |
| K18 | F5 tarafından eklenen sessizlik/fade | 0 | F5 ve F6 çakışması (N7) | T03, T38 | ☐ |
| K19 | Q1 süresi p95 | ≤ 5 ms | Canlıda pYIN çok yavaş (N6) | T20 | ☐ |
| K20 | Q1 yanlış alarm oranı | Raporlanır; kalibrasyon kümesinde ≤ %1 (öneri) | Ucuz seslilik denetimi yanlış alarm üretebilir | T20 | ☐ |
| K21 | Koddaki ölçülmemiş performans iddiası | 0 | N9 | T01 | ☐ |
| K22 | Ana kabul cümlesi kararlılığı | 10 / 10 uçtan uca çalıştırma (F2 ile ortak) | Mevcut kayıt 2 / 6 | F5-T03, F5-T31 | ☐ |
| K23 | Ölçülmüş eşzamanlı görüşme kapasitesi | Raporlanır; `max_concurrent_calls` bu değere göre ayarlanır | 50 yapılandırılmış sınır, ölçüm değil (N10) | T29, T37 | ☐ |

## 2. Test senaryoları (T01–T40)

**F5 test kontrol listesi: 0 / 40**

Her test önce **sahte motorla** (`unit`), uygulanabiliyorsa **gerçek modelle** (`gpu`) çalışır.

### Model, sözleşme ve giriş

| Test | Geçme koşulu |
| --- | --- |
| ☐ T01 — Model checkpoint ve hash doğrulaması | Onaylı checkpoint ve vendor commit eşleşir; onaysız checkpoint uyarı verir; K21 |
| ☐ T02 — F4 SynthesisPlan veri sözleşmesi | Şema doğrulanır; eksik alan veya `normalization_passes ≠ 1` reddedilir |
| ☐ T03 — Çifte normalizasyon engelleme | F5 yolunda `normalize` / `clauses` / `prepare_tts_clause` çağrısı yok (çağrı izleme); K18 |
| ☐ T04 — 48 kHz Float32 çıkış doğrulama | `sample_rate = 48000`, `float32`, mono; `num_samples = kare × 1 920` |
| ☐ T05 — Karakter sözlüğü uyumluluğu | Sözlük dışı karakter içeren plan reddedilir ve dönüştürülmez |

### Süre

| Test | Geçme koşulu |
| --- | --- |
| ☐ T06 — Minimum latent frame sınırı | Çok kısa metinde ≥ 8 kare ve hece tabanlı alt sınır |
| ☐ T07 — Maksimum latent frame sınırı | Kısa metinde üst sınır (karakter × 1,8 + 2 veya kalibre değer); uzun metinde ≤ 300 kare |
| ☐ T08 — Kısa ifadelerde tekrar problemi | 250 kısa cümlecikte Whisper geri tanımada tekrar eden sözcük oranı raporlanır; A0'dan kötü değil |
| ☐ T09 — Uzun cümlecik sentezi | 270 karakterlik parçada kesilme veya süre taşması yok |

### Seed ve yığın

| Test | Geçme koşulu |
| --- | --- |
| ☐ T10 — Seed 9 tekrarlanabilirliği | Aynı girdi 10 kez: tanımlı tolerans içinde |
| ☐ T11 — A/B seed korunumu | Seed 42 profili hata ve kurtarma yollarında 42 kalır; K06 |
| ☐ T12 — Batch sırası bağımsızlığı | Sıra değişiminde K15 |
| ☐ T13 — Batch padding bağımsızlığı | Kısa öğe uzun öğelerle aynı yığında: K15 |
| ☐ T14 — Oturumlar arası RNG izolasyonu | İç içe oturumlar tek başına çalıştırmayla aynı tolerans içinde |

### Çözücü ve kod çözücü

| Test | Geçme koşulu |
| --- | --- |
| ☐ T15 — 16/24/32/48 ODE adım karşılaştırması | Gecikme, RTF, Whisper geri tanıma, speaker similarity tablosu; karar ölçüme dayalı |
| ☐ T16 — AudioVAE decoder doğrulaması | Çözücü ve kod çözücü süreleri ayrı; optimizasyon sonrası referansa göre fark K15 sınırında |

### Kalite ve kurtarma

| Test | Geçme koşulu |
| --- | --- |
| ☐ T17 — NaN ve Inf çıkış kontrolü | Enjekte NaN yakalanır; K04 |
| ☐ T18 — Sessiz ses algılama | Enjekte sessiz çıktı yakalanır; K05 |
| ☐ T19 — Clipping ve genlik kontrolü | Tepe ≥ 0,999 oranı eşik üstünde ise FAIL |
| ☐ T20 — Fısıltı çökmesi tespiti | Ucuz seslilik denetimi etiketli çökme örneklerini yakalar; K19, K20 |
| ☐ T21 — Aynı seed ile kontrollü yeniden sentez | En fazla 1 deneme; seed değişmez; ikinci FAIL → güvenli hata olayı |

### Kimlik ve telaffuz

| Test | Geçme koşulu |
| --- | --- |
| ☐ T22 — F0 referans analizi | Median F0, std, seslilik oranı, hece/s referans dağılımında; K11 |
| ☐ T23 — Speaker embedding benzerliği | 48 kHz ve 8 kHz için ayrı eşik; K10 |
| ☐ T24 — Otomotiv telaffuz geri tanıma | K09 (F4 sözlüğüyle birlikte) |

### Önbellek

| Test | Geçme koşulu |
| --- | --- |
| ☐ T25 — Cache hit ve cache miss | K02; isabette çıkarım çağrısı yok |
| ☐ T26 — Model/sözlük değişimi sonrası cache invalidation | Sözlük, adım, süre profili veya checkpoint değişince eski kayıt dönmez |
| ☐ T27 — Kişisel seslerin önbellekten korunması | `cacheable=false` parçalar L0–L2'ye yazılmaz |

### GPU ve kuyruk

| Test | Geçme koşulu |
| --- | --- |
| ☐ T28 — GPU bellek taşması | Enjekte OOM'da oturum düşmez; K08; K16 |
| ☐ T29 — STT–LLM–TTS kaynak rekabeti | Öncelik sırası korunur; K16; K23 |
| ☐ T30 — Sentez kuyruğu kapasitesi | Kabul denetimi bekletir, reddetmez; bekleme süresi raporlanır |
| ☐ T31 — İlk cümlecik önceliği | İlk parça sonraki parçalardan ve ön ısıtmadan önce; K01 |
| ☐ T32 — Barge-in sonrası iptal | İptal edilen parçalar yığına alınmaz (K17); başlamış iş sonucu atılır |
| ☐ T33 — Eski generation ID sonuçlarının reddi | K07 |
| ☐ T34 — Batch içindeki hatalı öğenin izolasyonu | Bozuk öğe diğerlerini düşürmez (mevcut davranış korunur) |
| ☐ T35 — Circuit Breaker recovery | Ardışık hatalarda devre açılır, prob ile kapanır; mevcut testler geçer |
| ☐ T36 — Sahte test sesinin canlı hatta girmemesi | Üretim yapılandırmasında `allow_sine_fallback=True` veya sahte motor yüklenirse uygulama başlamaz |

### Süreklilik ve sürümler

| Test | Geçme koşulu |
| --- | --- |
| ☐ T37 — Uzun süreli bellek ve performans testi | 60 dk; VRAM sızıntısı yok; RTF p95 kayması yok; K03, K08 |
| ☐ T38 — F5–F6 ses sözleşmesi | `AudioChunk` şemaya uyar; ham ses; K18 |
| ☐ T39 — LoRA modelinin ayrı kabulü | LoRA ayrı sürüm; referans kümede kimlik ve terim doğruluğu karşılaştırması |
| ☐ T40 — Base checkpoint'e güvenli geri dönüş | Tek ayarla base modele dönülür; önbellek ilgili kayıtları geçersiz kılar |

## 3. Aşama kapıları

| Aşama | Kapsam | Geçiş koşulu |
| --- | --- | --- |
| **Aşama 1** — Özelliklerin tamamlanması | F5-S01 … F5-S20 | Görevler bitti; F5-T11 ve F5-T17 iptal filtresi canlıda; Leyla referans kümesi onaylı; mevcut testler geçiyor |
| **Aşama 2** — F5 arayüzü | F5-S21 | Studio gerçek backend'e bağlı; dürüstlük kuralı |
| **Aşama 3** — Sentetik test laboratuvarı | F5-S22 … F5-S24 | T01–T40 çalıştırıldı (sahte + gerçek); K01–K23 dolduruldu; ablation ve kapasite raporu yayımlandı |
| **Aşama 4** — Gerçek akustik kabul | F5-S25 | Önce otomatik ölçümler, sonra kör dinleme, en son gerçek görüşme ve SIP kabulü |

### Aşama 4 sonuç tablosu (ölçüldükçe doldurulur)

| Değerlendirme | Yöntem | Kanal | Sonuç | Dinleyici / örnek sayısı |
| --- | --- | --- | --- | --- |
| Otomatik akustik | Speaker similarity, F0 drift, Whisper geri tanıma | 48 kHz | — | — |
| Otomatik akustik | Aynı | 8 kHz telefon | — | — |
| Kör dinleme | MOS | 48 kHz | — | — |
| Kör dinleme | MOS | 8 kHz telefon | — | — |
| Kimlik | ABX (yeni sürüm ↔ referans) | 48 kHz | — | — |
| Gerçek görüşme | Uçtan uca TTFA p95, anlaşılabilirlik | SIP | — | — |
