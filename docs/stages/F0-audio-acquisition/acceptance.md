# F0 — Kabul Kriterleri ve Testler

> **Bu dosyadaki değerler henüz elde edilmiş sonuçlar değildir.** Geliştirme sırasında sınanacak hedeflerdir. Bir kutu yalnızca ilgili test çalıştırılıp sonucu laboratuvar raporuna (`data/f0/lab-report-*.json`) yazıldıktan sonra işaretlenir. İnsan değerlendirmesi gerektiren ölçümler (MOS, ABX) simüle edilerek başarılı gösterilmez.

**Değerlendirme ilkesi:** Her metrik üç sinyal üzerinde ayrı ayrı raporlanır: **ham ses**, **F0 çıkışı** ve **telefon bandına dönüştürülmüş ses**. Gürültü azalırken kelime doğruluğu kötüleşiyorsa filtre başarılı kabul edilmez.

---

## 1. Kabul kriterleri

### 1.1 Plandaki hedefler

| # | Metrik | Hedef | Ölçüm yöntemi | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K01 | Telefon giriş formatı | 8 kHz PCM16 | Adaptör doğrulaması | T12, T13 | ☐ |
| K02 | F0 çıkış formatı | 16 kHz mono | Çıkış çerçevesi denetimi | T12 | ☐ |
| K03 | Telefon çerçeve süresi | 20 ms | Adaptör çerçeveleme | T13 | ☐ |
| K04 | F0 işlem süresi p95 | < 10 ms (20 ms çerçeve başına) | `f0.frame_timing` | T17 | ☐ |
| K05 | Peak limiter tavanı | −1 dBFS | Çıkış tepe değeri | T10 | ☐ |
| K06 | Düşen örnek | 0 (normal çalışma koşullarında) | Giriş/çıkış örnek sayımı | T13, T17 | ☐ |
| K07 | Geçersiz NaN/Inf örnek | 0 | Çıkış denetimi | Tümü | ☐ |
| K08 | DTMF doğruluğu | Kontrollü testlerde %100 | 16 tuş × seviye × gürültü matrisi | T14 | ☐ |
| K09 | Gürültülü konuşmada WER | DSP kapalı tabandan düşük | Eşleştirilmiş karşılaştırma | T18 | ☐ |
| K10 | Temiz konuşmada WER | Anlamlı kötüleşme yok | Eşleştirilmiş karşılaştırma | T18 | ☐ |
| K11 | Ek GPU gereksinimi | Tercihen 0 MB | `nvidia-smi` farkı | T17 | ☐ |

### 1.2 Bu planlamada eklenen öneriler

Aşağıdaki maddeler PoC kodunun incelenmesi sırasında bulunan sorunlara dayanır. Hedef değerler **önerdir**; F0-S01 taban ölçümünden sonra gözden geçirilir.

| # | Metrik | Önerilen hedef | Gerekçe | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K12 | Toplam algoritmik gecikme (RNNoise hariç) | ≤ 40 ms, bileşen bazında raporlanmış | PoC NS'si 24–28 ms gecikme ekliyor ve bu hiçbir yerde görünmüyor | T02, T17 | ☐ |
| K13 | Başlangıçta çıkışa eklenen sıfır boşluğu | 0 | PoC NS'si çağrı başında 160 + 32 + 32 örnek boşluk ekliyor | T01, T13 | ☐ |
| K14 | AGC kazanç basamağı | Ardışık örnekler arası ≤ 0,1 dB | PoC'ta kazanç rampası etkisiz (her 20 ms'de basamak) | T09 | ☐ |
| K15 | "Anlamlı kötüleşme yok" tanımı (K10) | Temiz konuşmada WER farkı ≤ +0,5 puan ve %95 güven aralığı 0'ı kapsıyor | K10'u ölçülebilir hale getirmek için | T18 | ☐ |
| K16 | Otomotiv terim doğruluğu | DSP açıkken DSP kapalıdan düşük değil (temiz ve gürültülü) | Projenin en büyük sorunu terim doğruluğu (%48,04) | T18 | ☐ |
| K17 | Oturum izolasyonu | Çok oturumlu çıktılar tek oturumlu çıktılarla aynı (≤ 1e−6) | Eşzamanlı çağrılara hazırlık | T16 | ☐ |
| K18 | Uzun süreli bellek | 60 dakikada RSS artışı ≤ 20 MB | Sızıntı tespiti | T17 | ☐ |
| K19 | Kalibrasyon sırasında ses kaybı | 0 (ses VAD/STT'ye gitmeye devam eder) | PoC kalibrasyon süresince sesi düşürüyor | F0-T14 entegrasyon testi | ☐ |

## 2. Test senaryoları (T01–T18)

Her senaryo için: **Amaç**, **Girdi**, **Prosedür**, **Geçme koşulu**, **Otomasyon**. Sentetik sinyaller `synthetic_signals.py` ile sabit seed kullanılarak üretilir. Aksi belirtilmedikçe her test hem 8 kHz telefon hem 16/48 kHz web girişiyle çalıştırılır.

**F0 test kontrol listesi: 0 / 18**

### ☐ T01 — Sessiz giriş
- **Amaç:** Sessizlikte AGC'nin gürültüyü yükseltmemesi ve kestiricinin uydurma değer üretmemesi.
- **Girdi:** (a) 10 s dijital sıfır, (b) 10 s −70 dBFS beyaz gürültü.
- **Geçme koşulu:** Çıkış RMS ≤ giriş RMS; NaN/Inf yok; (a) için SNR alanı `None`; başlangıçta sıfır boşluğu yok (K13).
- **Otomasyon:** `tests/audio_frontend/lab/test_t01_silence.py` · `lab`

### ☐ T02 — Saf sinüs ve frekans taraması
- **Amaç:** HPF frekans tepkisi ve zincirin genlik/gecikme davranışı.
- **Girdi:** −6 dBFS sinüsler (50, 100, 120, 200, 1000, 3000 Hz); 50 Hz'den Nyquist'in %95'ine logaritmik tarama.
- **Prosedür:** NS kapalı, yalnızca HPF + limiter; ardından tam zincir.
- **Geçme koşulu:**
  - 120 Hz kesimde 50 Hz zayıflaması ≥ 28 dB (teorik ≈ 30,4 dB)
  - 2 × kesim frekansının üstünde tepki ±1 dB
  - Ölçülen gecikme, raporlanan `algorithmic_delay_ms` ile ±1 örnek uyumlu (K12)
- **Otomasyon:** `test_t02_sine_sweep.py` · `lab`

### ☐ T03 — Motor gürültüsü
- **Amaç:** Düşük frekanslı motor uğultusunun konuşma bandına zarar vermeden bastırılması.
- **Girdi:** 30/60/90/120 Hz harmonikler + düşük seviyeli geniş bant; ayrıca konuşma ile karışık hali.
- **Geçme koşulu:** 100 Hz altı enerji ≥ 20 dB azalır; NS kapalıyken 300–3400 Hz bandındaki konuşma enerjisi değişimi ≤ 1 dB.
- **Otomasyon:** `test_t03_engine.py` · `lab`

### ☐ T04 — Beyaz gürültü
- **Amaç:** Geniş bant gürültüde NS'nin STT'ye etkisi.
- **Girdi:** Konuşma + beyaz gürültü, SNR 20 / 10 / 5 / 0 dB.
- **Geçme koşulu:** Her SNR'da SI-SDR iyileşmesi raporlanır; WER(DSP açık) < WER(DSP kapalı) (T18 ile birlikte değerlendirilir).
- **Otomasyon:** `test_t04_white.py` · `lab` (WER kısmı `gpu`)

### ☐ T05 — Pembe gürültü
- **Girdi:** Konuşma + 1/f gürültü, SNR 20 / 10 / 5 / 0 dB.
- **Geçme koşulu:** T04 ile aynı.
- **Otomasyon:** `test_t05_pink.py`

### ☐ T06 — Değişken fan gürültüsü
- **Amaç:** Gürültü kestiricinin değişen ortamı takip etmesi ve profil seçicinin kararlılığı.
- **Girdi:** 60 s fan/klima gürültüsü; seviye 0,2 Hz ile ±6 dB modüle; 30. saniyede +10 dB adım.
- **Geçme koşulu:**
  - Gürültü tabanı adımdan sonra en geç 2 s içinde ±3 dB doğrulukla takip edilir
  - Profil 5 s'den sık değişmez
  - Yalnızca gürültü içeren bölümlerde F1 yanlış VAD tetiklenmesi DSP kapalı tabandan az
- **Otomasyon:** `test_t06_fan.py`

### ☐ T07 — Yapay konuşma + rüzgâr
- **Girdi:** Konuşma + rüzgâr (alçak geçiren gürültü + rastgele patlamalar), SNR 10 / 5 / 0 dB.
- **Geçme koşulu:** WER(DSP açık) ≤ WER(DSP kapalı); patlama anlarında limiter tavanı aşılmaz.
- **Otomasyon:** `test_t07_wind.py`

### ☐ T08 — Yapay konuşma + motor
- **Girdi:** Konuşma + T03 motor gürültüsü, SNR 10 / 5 / 0 dB; ayrıca Freya konuşurken (playback) yalnızca motor gürültüsü.
- **Geçme koşulu:** WER(DSP açık) ≤ WER(DSP kapalı); playback sırasında yanlış barge-in sayısı DSP kapalı tabandan az.
- **Otomasyon:** `test_t08_speech_engine.py`

### ☐ T09 — Düşük ses seviyesi
- **Amaç:** Kısık konuşmanın kontrollü yükseltilmesi ve kelime sonlarının korunması.
- **Girdi:** −40 dBFS ve −30 dBFS konuşma; ek sonları zayıf telaffuz edilen Türkçe cümleler.
- **Geçme koşulu:**
  - Çıkış RMS 1 s içinde hedefe ±3 dB yaklaşır
  - En yüksek kazanç (+12 dB) aşılmaz
  - Kazanç basamağı ≤ 0,1 dB (K14)
  - WER(DSP açık) ≤ WER(DSP kapalı)
- **Otomasyon:** `test_t09_low_level.py`

### ☐ T10 — Clipping ve aşırı genlik
- **Girdi:** +12 dB aşırı yüklenmiş konuşma; ±1,0'da sert kırpılmış sinüs ve konuşma.
- **Geçme koşulu:** Çıkış tepe değeri ≤ −1 dBFS + 0,1 dB (K05); kırpılmış çerçevelerin ≥ %95'inde `INPUT_CLIPPED` bayrağı; `f0.hard_clip` olayı 0.
- **Otomasyon:** `test_t10_clipping.py`

### ☐ T11 — Yapay akustik yankı
- **Amaç:** AEC'nin Freya'nın kendi sesini bastırması ve müşteriyi bastırmaması.
- **Girdi:** Oynatma referansı + yankısı (gecikme 40–250 ms, zayıflatma −6 ile −20 dB); (a) müşteri sessiz, (b) çift konuşma.
- **Geçme koşulu (öneri):**
  - (a) Yakınsama sonrası ERLE ≥ 20 dB, yakınsama ≤ 2 s
  - (a) Playback sırasında yanlış VAD tetiklenmesi AEC kapalıya göre azalır
  - (b) Müşteri konuşmasının WER'i AEC kapalıya göre kötüleşmez
- **Not:** Telefon yolu için F0-T17 ölçümü AEC'nin gerekmediğini gösterirse bu test yalnızca web yolunda koşulur.
- **Otomasyon:** `test_t11_echo.py`

### ☐ T12 — 8 / 16 / 24 / 44,1 / 48 kHz dönüşümü
- **Girdi:** Her hızda 1 kHz sinüs; yeni Nyquist frekansının üstünde bir ton (ör. 48 kHz girişte 10 kHz); değişken boyutlu parçalar.
- **Geçme koşulu:**
  - 1 kHz genliği ±0,1 dB korunur
  - Nyquist üstü ton ≥ 60 dB bastırılır
  - Akışlı (streaming) ve tek seferlik dönüşüm farkı ≤ 1e−4
  - Çıkış uzunluğu, beklenen uzunluk ± raporlanan gecikme
  - Oturum ortasında hız değişiminde `f0.rate_changed` olayı üretilir ve resampler sıfırlanır
- **Otomasyon:** `test_t12_resample.py` · `unit`

### ☐ T13 — Eksik veya düzensiz ses paketleri
- **Girdi:** AudioSocket akışı; %1 ve %5 gecikmeli paket, 200 ms'lik takılmalar, düzensiz paket boyları, tek bayt eksik paket.
- **Geçme koşulu:** İstisna yok (tek bayt eksik paket mevcut `ValueError` davranışını korur); `seq` monoton; `GAP_FILLED` doğru işaretlenir; filtre durumu bozulmaz (NaN yok, takılma sonrası çıkış en geç 100 ms'de normale döner); düşen örnek 0 (K06).
- **Otomasyon:** `test_t13_irregular_packets.py`

### ☐ T14 — DTMF korunumu
- **Girdi:** 16 tuş × seviye (−10 / −20 / −30 dBFS) × süre (40 / 60 / 100 ms) × gürültü (yok / P2 / P3), 8 kHz telefon girişi. Ayrıca aynı tuşun hem bant içi hem bant dışı (AudioSocket `0x03`) gelmesi.
- **Geçme koşulu:**
  - Algılama %100 (K08)
  - Mevcut konuşma derleminde yanlış pozitif 0 (`test_dtmf_false_positive.py`)
  - Bant içi + bant dışı aynı tuş tek olay
  - Temizlenmiş yolda kalan ton enerjisi, susturulmamış tona göre ≤ −40 dB (maske hizalaması)
- **Otomasyon:** `test_t14_dtmf.py` + mevcut `tests/test_dtmf*.py`

### ☐ T15 — DSP Bypass doğruluğu
- **Geçme koşulu:** Bypass çıktısı ile yalnızca adaptör + resampler çıktısı arasındaki fark ≤ 1 LSB; çalışma sırasında açma/kapama anında, çapraz geçiş dışında ardışık örnek sıçraması sinyal genliğinin %5'ini aşmaz.
- **Otomasyon:** `test_t15_bypass.py` · `unit`

### ☐ T16 — Oturum izolasyonu
- **Girdi:** 2 ve 4 oturum; her biri farklı sinyal ve profil; çerçeveler iç içe işlenir; bir oturumda ortada `reset()`.
- **Geçme koşulu:** Her oturumun çıktısı, aynı sinyalin tek başına işlendiği çıktıyla ≤ 1e−6 farklı (K17); bir oturumun `reset()` çağrısı diğerlerini etkilemez.
- **Otomasyon:** `test_t16_isolation.py` · `unit` (mevcut `tests/test_isolation.py` ile birlikte)

### ☐ T17 — Uzun süreli CPU/RAM testi
- **Girdi:** 60 dakika, 4 eşzamanlı oturum, karışık sinyaller.
- **Geçme koşulu:** İşlem süresi p95 < 10 ms (K04); RSS artışı ≤ 20 MB (K18); kuyruk büyümesi yok; düşen örnek 0; GPU belleği değişmez (K11).
- **Otomasyon:** `test_t17_soak.py` · `slow`

### ☐ T18 — STT doğruluğuna etkisi
- **Amaç:** F0'ın asıl başarı ölçütü.
- **Girdi:** Temiz test derlemi + T04–T08 gürültülü karışımlar × profiller; otomotiv terimi içeren cümleler (marka, model, yıl).
- **Prosedür:** Her kayıt DSP kapalı ve DSP açık olarak aynı STT ile tanınır; kayıt bazında eşleştirilmiş karşılaştırma; bootstrap ile %95 güven aralığı.
- **Geçme koşulu:**
  - Gürültülü koşullarda WER(açık) < WER(kapalı) (K09)
  - Temiz koşulda K15 tanımına göre anlamlı kötüleşme yok (K10)
  - Otomotiv terim doğruluğu her iki koşulda da düşmez (K16)
- **Raporlama:** Sonuçlar ham, F0 çıkışı ve telefon bandı için ayrı tabloda; NS motorları (spectral / wiener / rnnoise) yan yana.
- **Otomasyon:** `test_t18_stt_impact.py` · `gpu`, `slow`

## 3. Aşama kapıları

| Aşama | Kapsam | Geçiş koşulu |
| --- | --- | --- |
| **AŞAMA 1** — Özelliklerin tamamlanması | F0-S01 … F0-S07 | Tüm görevler bitti; birim testleri geçiyor; mevcut testler kırılmadı |
| **AŞAMA 2** — F0 arayüzü | F0-S08 | Studio gerçek backend'e bağlı; dürüstlük kuralı sağlanıyor |
| **AŞAMA 3** — Sentetik testler | F0-S09, F0-S10 | T01–T18 çalıştırıldı ve raporlandı; K01–K19 için sonuçlar dolduruldu; regresyon temiz |
| **AŞAMA 4** — Gerçek ses ve telefon kabulü | F0-S11 | Aşağıdaki tablo ölçülmüş değerlerle dolu; başarısız koşullar için karar yazıldı |

### AŞAMA 4 sonuç tablosu (gerçek ses — ölçüldükçe doldurulur)

| Koşul | Kanal | WER kapalı | WER açık | Terim doğruluğu kapalı | Terim doğruluğu açık | Yanlış barge-in kapalı | Yanlış barge-in açık | Karar |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sessiz oda | Web | — | — | — | — | — | — | — |
| Sessiz oda | Telefon | — | — | — | — | — | — | — |
| Park halindeki araç | Telefon | — | — | — | — | — | — | — |
| Motor çalışırken | Telefon | — | — | — | — | — | — | — |
| Klima açık | Telefon | — | — | — | — | — | — | — |
| Rüzgâr (cam açık) | Telefon | — | — | — | — | — | — | — |
| Yoğun trafik | Telefon | — | — | — | — | — | — | — |
