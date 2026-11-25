# F4 — Kabul Kriterleri ve Testler

> **Bu dosyadaki değerler tasarım hedefleridir; elde edilmiş sonuç değildir.** Bir kutu yalnızca test çalıştırılıp sonucu laboratuvar raporuna (`data/f4/lab-report-*.json`) yazıldıktan sonra işaretlenir. Fonem ve vurgu doğruluğunun akustik ölçümü için güvenilir referans transkripsiyonları, gerekirse forced alignment ve uzman dinleme değerlendirmesi gerekir. MOS gibi insan değerlendirmesi gerektiren ölçümler simüle edilmez.

**Ölçüm kuralları:**
- **Metin düzeyi** metrikler ses üretmeden ölçülür (3 000 örneklik küme).
- **Akustik** metrikler F5 ile ortak ölçülür ve ayrı raporlanır. Whisper geri tanıma yardımcı bir sinyaldir; tek başına doğru telaffuz veya doğallık kanıtı değildir.
- "Yaklaşık PER", Whisper transkripti ile hedef metnin G2P çıktıları karşılaştırılarak hesaplanır; gerçek fonem tanıma değildir (spec §5.7).

---

## 1. Kalite kapısı

### 1.1 Plandaki hedefler

| # | Metrik | Hedef | Ölçüm tanımı | Düzey | Test | Sonuç |
| --- | --- | --- | --- | --- | --- | --- |
| K01 | Kritik sayı ve fiyat anlam korunumu | %100 | Tersine ayrıştırma (spec §5.13): kaynak değer = `model_text`'ten geri çözülen değer | Metin | T04–T11, T35 | ☐ |
| K02 | Normalizasyon doğruluğu | ≥ %99 | Beklenen normalize metinle tam eşleşme | Metin | T04–T15 | ☐ |
| K03 | Marka/model metinsel eşleme | ≥ %98 | Sözlük kaydı doğru bulunup `synth_text` uygulandı | Metin | T12, T13 | ☐ |
| K04 | Akustik otomotiv terim doğruluğu | ≥ %95 | Sentez → Whisper → terim bulundu (F2 metriği) + uzman dinlemesi örneklemi | Akustik | T12, T13 (F5 ile) | ☐ |
| K05 | Morfolojik ek doğruluğu | ≥ %98 | Beklenen ek biçimi | Metin | T16–T19 | ☐ |
| K06 | Heceleme doğruluğu | ≥ %98 | Beklenen hece sınırları | Metin | T22 | ☐ |
| K07 | Sözcük vurgu doğruluğu | ≥ %95 | Beklenen birincil vurgu hecesi (hedef düzeyinde) | Metin | T23 | ☐ |
| K08 | Fonem hata oranı (PER) | ≤ %5 | Metin düzeyinde G2P; akustik düzeyde **yaklaşık PER** ayrı raporlanır | Metin / Akustik | T20, T21 | ☐ |
| K09 | Protected Atom ihlali | 0 | Korunan öbeğin iki parçaya bölünmesi | Metin | T29, T30 | ☐ |
| K10 | Model sözlüğü dışı karakter | 0 | `model_text` içinde `char_to_id` dışı karakter | Metin | T01, T32 | ☐ |
| K11 | Çifte normalizasyon | 0 | `normalization_passes > 1` veya F5'te metin dönüşümü | Metin | T02, T03 | ☐ |
| K12 | Yinelenen duraklama uygulaması | 0 | Aynı sınırda F5 ve F6'nın ikisinin de sessizlik eklemesi | Akustik (F5/F6) | T34 | ☐ |
| K13 | Kritik anlam değişikliği | 0 | Olumsuzluk, koşul, değer değişimi | Metin | T35 | ☐ |
| K14 | F4 işlem süresi p95 | ≤ 50 ms | Yanıt başına, CPU | Metin | T30 | ☐ |
| K15 | Ek GPU gereksinimi | 0 MB | — | — | T33 | ☐ |

### 1.2 PoC incelemesine dayanan ek kriterler (öneri)

| # | Metrik | Önerilen hedef | Gerekçe | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K16 | Ara parçada cümle sonu noktalaması | 0 (ADR-F4-01 kararına göre) | PoC her ara parçaya "." ekliyor (spec §3.2 L2) | T30 | ☐ |
| K17 | Tek karakter yüzünden sessiz kalan yanıt | 0 | PoC °, −, é, & karakterlerinde tüm yanıtı düşürüyor (L5) | T01, T32 | ☐ |
| K18 | Sıra sayısı kaynaklı bölünme | 0 | "1. seçenek" → "Bir." ayrı parça (L3) | T04, T31 | ☐ |
| K19 | Çok kısa parça | 0 (en kısa sınırın altında parça yok) | Kısa parçalar modelde tekrar üretebiliyor (L11) | T31 | ☐ |
| K20 | Eğitim ve çıkarım normalizasyon farkı | 0 | `sft_leyla.py` farklı normalizer kullanıyor (L7) | T03 | ☐ |
| K21 | Sözlük kapsamı | Derlenmiş sözlükteki kayıtların %100'ü canlı yolda kullanılabilir (hata 0, `model_text`'te rakam kalan kayıt 0) | Bugün 26 kayıt hata veriyor, 95 kayıtta rakam kalıyor (L4) | T12, T13 | ☐ |
| K22 | Uzman onaylı terim oranı | Raporlanır (hedef değil) | `review_status = approved` olan kayıtların oranı | T12 | ☐ |

## 2. Test senaryoları (T01–T36)

**F4 test kontrol listesi: 0 / 36**

### Girdi ve otorite

#### ☐ T01 — Unicode ve Türkçe karakter doğrulama
- **Girdi:** NFC/NFD biçimleri, tipografik tırnak ve kesme, `−`, `°`, `é`, `&`, `…`, görünmez karakterler, küçük `q`.
- **Geçme koşulu:** K10 = 0; K17 = 0; düşürülen karakterler `f4.char_dropped` ile kaydedilir.

#### ☐ T02 — Normalizasyon idempotency testi
- **Geçme koşulu:** `normalize(normalize(x)) == normalize(x)` tüm kümede.

#### ☐ T03 — Çifte normalizasyon engelleme
- **Geçme koşulu:** Plan `normalization_passes == 1`; F5 yolunda `normalize` / `clauses` / noktalama ekleme çağrısı yok (çağrı izleme testi); eğitim yolu aynı çıktıyı verir (K20).

### Sayı, zaman, tanımlayıcı

#### ☐ T04 — Tam sayı okuma
- **Girdi:** 0–999 999 999; "3008 adet"; sıra sayıları ("1. seçenek", "2. sıra").
- **Geçme koşulu:** K01, K02, K18.

#### ☐ T05 — Ondalık sayı okuma
- **Geçme koşulu:** "1,6 litre" → "bir virgül altı litre"; "1.6 TDI" → "bir nokta altı Te De İ".

#### ☐ T06 — Negatif sayı ve yüzde
- **Geçme koşulu:** "−5 °C" → "eksi beş santigrat derece"; "%18" → "yüzde on sekiz".

#### ☐ T07 — Türk lirası ve kuruş
- **Geçme koşulu:** "1.250.000 TL", "150,50 TL", "2.500,75 TL", "1500,00 TL" doğru; K01.

#### ☐ T08 — Tarih normalizasyonu
- **Geçme koşulu:** "24.11.2026" ve "24 Kasım" doğru; tarih öbeği bölünmez.

#### ☐ T09 — Saat normalizasyonu
- **Geçme koşulu:** "14:30" → "öğleden sonra iki buçuk", "10:00" → "sabah on", "9:05" → "sabah dokuzu beş geçe", "14:30'da" → "öğleden sonra iki buçukta" ([ADR-F4-02](../../01-architecture/adr/ADR-F4-02-saat-tarih-okuma.md)); "yarın saat 14:30" → "yarın öğleden sonra iki buçuk", tek öbek.

#### ☐ T10 — Telefon numarası
- **Geçme koşulu:** `05xx xxx xx xx` (4-3-2-2) gruplama: "0532 123 45 67" → "sıfır beş yüz otuz iki, yüz yirmi üç, kırk beş, altmış yedi"; "0212 400 05 07" → "sıfır iki yüz on iki, dört yüz, sıfır beş, sıfır yedi"; "+90 532 …" ulusal biçime getirilir ([ADR-F4-03](../../01-architecture/adr/ADR-F4-03-telefon-numarasi-okuma.md)); grup arası duraklama planda; K01 (tersine ayrıştırma 11 hane).

#### ☐ T11 — Türkiye araç plakası
- **Geçme koşulu:** "61 ABC 123" → "altmış bir A Be Ce yüz yirmi üç"; 2–4 haneli gruplar; K01.

### Otomotiv sözlüğü

#### ☐ T12 — Otomotiv marka telaffuzu
- **Geçme koşulu:** Tüm markalar sözlükten; K03; K21; akustik K04 (F5 ile).

#### ☐ T13 — Araç model kodları
- **Girdi:** "Peugeot 3008", "Togg T10X", "Hyundai i20", "e-208", "ID.4", "GLE 300d", "Alfa Romeo 8C".
- **Geçme koşulu:** `model_text`'te rakam/harf karışımı kalmaz; K21.

#### ☐ T14 — Motor ve şanzıman kodları
- **Girdi:** TDI, TSI, BlueHDi, EcoBoost, dCi, DSG, CVT, EDC.
- **Geçme koşulu:** Her biri sözlükteki okunuşla; kısaltma politikası tutarlı.

#### ☐ T15 — Teknik birimlerin okunması
- **Girdi:** km/h, km/sa, Nm, kW, kWh, HP, °C, litre.
- **Geçme koşulu:** "120 km/h" → "saatte yüz yirmi kilometre"; `/` karakteri kalmaz.

### Morfoloji ve fonoloji

#### ☐ T16 — Büyük ve küçük ünlü uyumu
#### ☐ T17 — Ünsüz yumuşaması ve sertleşmesi
- **Geçme koşulu (T16–T17):** K05; kurallar yalnızca F4'ün ürettiği parçalara uygulanır.

#### ☐ T18 — Yabancı marka ekleri
- **Girdi:** spec §5.5 tablosu ve 450 örneklik ek kümesi.
- **Geçme koşulu:** "ABS'nin" → "A Be Senin"; "DSG'li" → "De Se Geli"; K05.

#### ☐ T19 — Morfem ayrıştırma
- **Girdi:** "Görüştürülemedi" ve benzeri çok ekli sözcükler.
- **Geçme koşulu:** Kök ve ek dizisi beklenenle eşleşir.

#### ☐ T20 — Türkçe G2P
#### ☐ T21 — Ğ karakteri ve bağlamsal fonetik
- **Geçme koşulu (T20–T21):** K08 metin düzeyi; yaklaşık PER akustik düzeyde raporlanır.

#### ☐ T22 — Heceleme doğruluğu
- **Geçme koşulu:** K06; "Arabalarımız" → a-ra-ba-la-rı-mız.

#### ☐ T23 — Sözcük vurgu istisnaları
- **Geçme koşulu:** K07; yer adları, yabancı sözcükler, olumsuzluk ekleri.

### Clitic ve prozodi

#### ☐ T24 — Soru parçacığı mi
#### ☐ T25 — Bağlaç ve ek ayrımı: de/da
#### ☐ T26 — Ulama ve konuşma ritmi
- **Geçme koşulu (T24–T26):** Analiz doğru; mikro duraklama yalnızca A/B ile onaylanmış bağlamda.

#### ☐ T27 — Fiyat odaklı prozodi
#### ☐ T28 — Randevu onay tonlaması
- **Geçme koşulu (T27–T28):** Doğru profil (PRICING / CONFIRMATION) ve odak hedefleri planda; akustik gerçekleşme ayrı ölçülür ve doğrulanana kadar `prosody_realization_verified: null`.

### Bölümleme ve sözleşme

#### ☐ T29 — Protected Atoms bütünlüğü
- **Geçme koşulu:** K09 = 0.

#### ☐ T30 — Uzun metin ve cümlecik bölme
- **Girdi:** spec §3.2 L2'deki uzun cümle ve F3 şablonları.
- **Geçme koşulu:** Ara parçalar ADR-F4-01 biçiminde (K16); "yarın öğleden sonra iki buçuk" bölünmez; K14.

#### ☐ T31 — Çok kısa cümlecik kontrolü
- **Geçme koşulu:** K19 = 0; "Bir." / "Evet." gibi parçalar komşusuyla birleşir.

#### ☐ T32 — Model karakter sözlüğü uyumu
- **Geçme koşulu:** K10 = 0; `char_to_id` ↔ `freya_vocab.json` farkı başlatmada raporlanır.

#### ☐ T33 — F4–F5 veri sözleşmesi
- **Geçme koşulu:** `SynthesisPlan` şemaya uyar; frozen; `plan_id` deterministik; F3 `ResponsePlan` etiketleri korunur.

#### ☐ T34 — Duraklamaların tek kez uygulanması
- **Geçme koşulu:** K12 = 0 (F5 çıkışında sondaki sessizlik yok; F6 `post_pause_ms` uygular; ölçülen sessizlik planla ±10 ms).

#### ☐ T35 — Anlam ve kritik bilgi korunumu
- **Geçme koşulu:** K01 %100; K13 = 0.

#### ☐ T36 — Sözlük değişimi ve önbellek geçersizleştirme
- **Geçme koşulu:** Sözlük sürümü değişince `plan_id` değişir; F5 önbelleği eski sesi döndürmez.

## 3. Aşama kapıları

| Aşama | Kapsam | Geçiş koşulu |
| --- | --- | --- |
| **Aşama 1** — Özelliklerin tamamlanması | F4-S01 … F4-S19 | Görevler bitti; F4-T04 ve F4-T05 canlıda; mevcut testler geçiyor |
| **Aşama 2** — F4 arayüzü | F4-S20 | Studio gerçek backend'e bağlı; dürüstlük kuralı sağlanıyor |
| **Aşama 3** — Sentetik test laboratuvarı | F4-S21, F4-S22 | T01–T36 çalıştırıldı; K01–K22 dolduruldu; ablation yayımlandı |
| **Aşama 4** — Gerçek ses ve telaffuz kabulü | F4-S23 | Aşağıdaki tablo ölçülmüş değerlerle dolu |

### Aşama 4 sonuç tablosu (ölçüldükçe doldurulur)

| Değerlendirme | Yöntem | Kanal | Sonuç | Değerlendirici sayısı |
| --- | --- | --- | --- | --- |
| Pronunciation | Uzman dinlemesi + Whisper geri tanıma | 48 kHz | — | — |
| Pronunciation | Uzman dinlemesi + Whisper geri tanıma | 8 kHz telefon | — | — |
| Naturalness | MOS (gerçek dinleyiciler) | 48 kHz | — | — |
| Speaker Identity | Leyla referansına benzerlik + ABX (gerçek dinleyiciler) | 48 kHz | — | — |
| Intelligibility | Telefon bandında kritik bilgi (fiyat, saat, plaka) anlaşılma oranı | 8 kHz telefon | — | — |
