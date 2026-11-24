# F1 — Kabul Kriterleri ve Testler

> **Bu dosyadaki değerler henüz elde edilmiş sonuçlar değildir.** Planlanan testler ve hedeflerdir. Bir kutu yalnızca test çalıştırılıp sonucu laboratuvar raporuna (`data/f1/lab-report-*.json`) yazıldıktan sonra işaretlenir. Sentetik testlerin başarılı olması gerçek görüşmelerin başarılı olacağını tek başına kanıtlamaz.

---

## 1. Kalite kapısı

### 1.1 Plandaki hedefler

| # | Metrik | Hedef | Ölçüm tanımı | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K01 | Speech Detection Precision | ≥ %95 | Blok düzeyinde (32 ms), etiketli derlem; etiket sınırlarının ±1 bloğu hariç; SNR koşulu başına ve toplam | T01–T06 | ☐ |
| K02 | Speech Detection Recall | ≥ %95 | Aynı | T04–T06 | ☐ |
| K03 | Speech Detection F1 Score | ≥ %95 | Aynı | T01–T06 | ☐ |
| K04 | Speech Onset Latency p95 | ≤ 100 ms | `onset` olayının örnek zamanı − etiketli konuşma başlangıcı | T04, T05 | ☐ |
| K05 | Kısa konuşma Endpoint Latency p95 | ≤ 500 ms | `FINALIZE` anı − etiketli konuşma sonu; yalnızca `yes_no` ve `option_number` profilleri | T04, T16 | ☐ |
| K06 | Barge-in kontrol sinyali p95 | ≤ 100 ms | Komutun taşıma katmanına yazıldığı an − ilk konuşma örneğinin adaptöre ulaştığı an (spec §5.9) | T13, T14 | ☐ |
| K07 | Duyulabilir ses kesilmesi p95 | ≤ 200 ms | Freya sesinin müşteri tarafında durduğu an − aynı başlangıç; kanal başına ayrı | T14 | ☐ |
| K08 | False Barge-in Rate | ≤ %2 | Gerçek müşteri konuşması olmadan soft pause oluşan Freya konuşmalarının oranı (yankı, gürültü, nefes senaryoları) | T02, T12, T17 | ☐ |
| K09 | Backchannel doğruluğu | ≥ %95 | Etiketli (metin, bağlam) seti; metin girdisiyle ve STT'li uçtan uca olarak ayrı raporlanır | T15, T16 | ☐ |
| K10 | Pre-roll kaynaklı örnek kaybı | 0 | Utterance sesi ile kaynak sinyalin örnek düzeyinde karşılaştırılması | T05, T21 | ☐ |
| K11 | Eski turn ID ile oynatılan ses | 0 | Taşıma katmanında, COMMIT sonrası gönderilen eski turn ID'li çerçeve sayısı | T19 | ☐ |
| K12 | Oturumlar arası VAD karışması | 0 | Çok oturumlu VAD olasılıkları ile tek oturumlu çalıştırma arasındaki fark ≤ 1e−6 | T20 | ☐ |
| K13 | Ek GPU kullanımı | Tercihen 0 MB | VAD CPU'da; spekülatif STT'nin GPU süresi ayrıca raporlanır | T22 | ☐ |

> **K04 ve K06 için not:** Spec §8'deki gecikme bütçesine göre 64 ms en kısa başlangıç ve mevcut F0 gecikmesiyle bu hedefler karşılanamayabilir. F1-T10 ölçümü ve ADR-F1-02 kararından sonra hedef veya yöntem güncellenir; güncelleme bu tabloya gerekçesiyle yazılır.

### 1.2 PoC incelemesine dayanan ek kriterler (öneri)

| # | Metrik | Önerilen hedef | Gerekçe | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K14 | Kaybolan konuşma bölümü | 0 | PoC'ta yeni bölüm önceki bölümün işlenmesini iptal ediyor (spec §3.2 S5) | T11 | ☐ |
| K15 | Oynatma yokken gönderilen duraklatma | 0 | PoC her konuşma başlangıcında duraklatma yayınlıyor (S8) | T04, T14 | ☐ |
| K16 | En uzun soft pause süresi | ≤ `pause_timeout` + karar süresi | PoC'ta zaman aşımı bağlı değil; Freya 20 s'ye kadar susabilir (S3) | T17 | ☐ |
| K17 | Erken sonlandırma oranı | ≤ %5 | Düşünme araları ayrı tura bölünmemeli | T07, T08, T09 | ☐ |
| K18 | Uzun süreli bellek | 60 dakikada RSS artışı ≤ 20 MB | Halka tamponların sınırlı kaldığının kanıtı | T22 | ☐ |

## 2. Test senaryoları (T01–T22)

Sentetik konuşma ve gürültüler F0 ve F1 laboratuvar üreteçleriyle sabit seed kullanılarak üretilir. Aksi belirtilmedikçe senaryolar F0 açık olarak, hem 8 kHz telefon hem 16 kHz web girişiyle çalıştırılır.

**F1 sentetik test kontrolü: 0 / 22**

### ☐ T01 — Saf sessizlik
- **Girdi:** 10 dk dijital sessizlik; 10 dk −60 dBFS beyaz gürültü.
- **Geçme koşulu:** `onset` olayı 0; VAD olasılığı hiçbir blokta başlangıç eşiğini geçmez.

### ☐ T02 — Motor gürültüsü ve VAD yanlış alarmı
- **Girdi:** P2 ve P3 profillerine uygun 10'ar dk motor gürültüsü, konuşma yok; ayrıca Freya konuşurken aynı gürültü.
- **Geçme koşulu:** Blok düzeyinde yanlış pozitif ≤ %2; yanlış `onset` ≤ 1 / 10 dk (öneri); oynatma sırasında soft pause oranı K08 sınırında.

### ☐ T03 — Beyaz ve pembe gürültü
- **Girdi:** −50 / −40 / −30 dBFS beyaz ve pembe gürültü, konuşma yok.
- **Geçme koşulu:** T02 ile aynı; adaptif eşik gürültü seviyesiyle yükselir ve sınır içinde kalır.

### ☐ T04 — Tek kelimelik kısa konuşma
- **Girdi:** "Evet", "Hayır", "Bir", "İki", "Tamam" (200–400 ms), sessizlik ve P2 gürültüsü içinde; `expected_slot = yes_no / option_number`.
- **Geçme koşulu:** Hepsi algılanır (recall %100 bu sette); endpoint gecikmesi p95 ≤ 500 ms (K05); oynatma yokken duraklatma olayı yok (K15).

### ☐ T05 — İlk hece ve pre-roll korunumu
- **Girdi:** Zayıf başlangıçlı sözcükler: "Hyundai", "Fiat", "Seat", "Ford", "şimdi", "saat"; −35 dBFS düzeyinde.
- **Geçme koşulu:**
  - Utterance sesi etiketli başlangıçtan en az 200 ms öncesini kapsar
  - Utterance sesi kaynak sinyalin ilgili aralığıyla örnek düzeyinde aynıdır (çift örnek veya boşluk yok — K10)
  - STT çıktısında ilk hece bulunur (`gpu` alt testi)

### ☐ T06 — Düşük enerjili konuşma
- **Girdi:** F0 sonrası −40 ve −45 dBFS konuşma; gürültülü ortamda adaptif eşiğin yükselmiş olduğu durum.
- **Geçme koşulu:** Recall ≥ %95 (K02); kaçırılan konuşma oranı raporlanır ve sabit eşikli sürümden kötü değildir.

### ☐ T07 — Cümle ortasında 450 ms duraklama
- **Girdi:** "Benim aracım [450 ms] 2021 model Volkswagen Passat"; `expected_slot = vehicle_make_model`.
- **Geçme koşulu:** Tek utterance; `end_reason` ≠ `max_length`; her iki bölüm de transkriptte.

### ☐ T08 — Cümle ortasında 800 ms duraklama
- **Girdi:** (a) "Benim aracım… [800 ms] 2021 model Passat" (eksik cümle, `WAIT` beklenir), (b) "Randevu almak istiyorum. [800 ms] Yarın uygun mu?" (iki tam cümle).
- **Geçme koşulu:** (a) tek utterance; (b) iki ayrı tur **veya** birleştirilmiş tek tur — her iki cümle de kaybolmadan F3'e ulaşır. Erken sonlandırma oranı K17 sınırında.

### ☐ T09 — Telefon numarası okuma
- **Girdi:** "0532 [600 ms] 123 [700 ms] 45 [500 ms] 67"; `expected_slot = phone_number`.
- **Geçme koşulu:** Tek utterance; 11 hanenin tamamı transkriptte; eksik hanede `WAIT` (semantik birim testi).

### ☐ T10 — Uzun konuşma ve bölümleme
- **Girdi:** 30 s ve 45 s kesintisiz serbest konuşma (doğal duraklamalarla).
- **Geçme koşulu:** Bölünme doğal duraklamalarda (VAD olasılığı en düşük blokta); bölümler `continuation` ile zincirli; bölümlerin birleşimi tüm konuşma örneklerini kapsar; sözcük ortasında kesim yok.

### ☐ T11 — Ardışık konuşma bölümlerinin korunması
- **Girdi:** PoC'taki S5 hatasını tetikleyen senaryo: ilk bölüm işlenirken (STT sürerken) ikinci bölümün gelmesi; ayrıca F3 yanıt üretirken üçüncü bölüm.
- **Geçme koşulu:** Hiçbir bölüm kaybolmaz (K14); birleştirme ve `follows_turn` kuralları spec §5.10'a uyar.

### ☐ T12 — Freya sesinin yapay yankısı
- **Girdi:** Oynatma referansının 40–250 ms gecikmeli, −6 ile −20 dB zayıflatılmış yankısı; müşteri sessiz.
- **Geçme koşulu:** Soft pause oluşmaz veya oranı K08 sınırında; F1.05 durumu `echo_only`.

### ☐ T13 — Double-talk
- **Girdi:** Oynatma + yankı + müşteri konuşması aynı anda.
- **Geçme koşulu:** F1.05 durumu `double_talk`; soft pause oluşur; kontrol sinyali gecikmesi raporlanır (K06).

### ☐ T14 — Gerçek konuşma kesintisi
- **Girdi:** Freya konuşurken "Bir dakika", "Durun", "Bir şey soracağım".
- **Geçme koşulu:** `COMMIT`; eski ses ve TTS/LLM kuyruğu iptal; turn ID artar; kontrol sinyali (K06) ve duyulabilir kesilme (K07) kanal başına raporlanır.

### ☐ T15 — Hı hı / Anlıyorum rollback
- **Girdi:** Freya bilgi verirken "Hı hı", "Anlıyorum", "Tamam".
- **Geçme koşulu:** `ROLLBACK`; oynatma kaldığı yerden (±1 çerçeve) devam eder; 1 s'den uzun duraklamada kesilen cümleciğin başından başlar.

### ☐ T16 — Evet / Hayır bağlamsal onay
- **Girdi ve beklenen karar:**

| Girdi | Bağlam | Beklenen |
| --- | --- | --- |
| Evet | Randevu onayı bekleniyor | NEW_TURN |
| Hayır | Onay bekleniyor | NEW_TURN |
| Evet | Freya bilgi veriyor | ROLLBACK |
| Hayır | Freya bilgi veriyor | COMMIT |
| Evet ama saati değiştirelim | Herhangi | COMMIT |
| Efendim? | Freya konuşuyor | REPEAT |

- **Geçme koşulu:** Tablonun tamamı doğru; genel backchannel doğruluğu ≥ %95 (K09).

### ☐ T17 — Barge-in timeout
- **Girdi:** Freya konuşurken nefes, öksürük veya kısa gürültü patlaması.
- **Geçme koşulu:** Soft pause en geç `pause_timeout` (3 500 ms) sonunda kalkar ve oynatma devam eder (K16); gerçek konuşma devam ediyorsa zaman aşımı karara kadar uzar.

### ☐ T18 — DTMF önceliği
- **Girdi:** (a) Freya konuşurken DTMF; (b) müşteri konuşurken DTMF; (c) DTMF ile başlayan utterance.
- **Geçme koşulu:** (a) Sınıflandırma beklenmeden `COMMIT`; (b) DTMF olayı F3'e iletilir ve DTMF tonları `onset` üretmez; (c) `end_reason = dtmf` doğru doldurulur.

### ☐ T19 — İptal sonrası eski sesin oynatılmaması
- **Girdi:** T14 senaryoları AudioSocket, chan_websocket ve web kanallarında.
- **Geçme koşulu:** `COMMIT` sonrası taşıma katmanına gönderilen eski turn ID'li çerçeve sayısı 0 (K11).

### ☐ T20 — Eşzamanlı VAD oturum izolasyonu
- **Girdi:** 2, 4 ve 8 oturum; farklı sinyaller iç içe işlenir; çalışma sırasında yeni oturum açılır.
- **Geçme koşulu:** Her oturumun VAD olasılıkları tek başına çalıştırmayla ≤ 1e−6 farklı; yeni oturum açılması diğerlerini etkilemez (K12).

### ☐ T21 — F0–F1–F2 veri sözleşmesi
- **Girdi:** Rastgele çerçeve boyları (10/20/32/100 ms), örnekleme hızları ve paket boşlukları (özellik tabanlı / property-based test).
- **Geçme koşulu:** Örnek indeksleri sürekli; zaman damgaları monoton; `Utterance` alanları tutarlı (`start_sample < end_sample`, bölümler aralık içinde); F0 bayrakları korunur (K10).

### ☐ T22 — Uzun süreli tampon ve bellek testi
- **Girdi:** 60 dk, 4 eşzamanlı oturum, karışık konuşma/gürültü/oynatma.
- **Geçme koşulu:** RSS artışı ≤ 20 MB (K18); tampon doluluğu sınırlı; olay kuyruğu büyümüyor; GPU belleği F1 nedeniyle değişmiyor (K13).

## 3. Aşama kapıları

| Aşama | Kapsam | Geçiş koşulu |
| --- | --- | --- |
| **Aşama 1** — Özelliklerin tamamlanması | F1-S01 … F1-S10 | Görevler bitti; S1 ve S5 düzeltmeleri canlıda; mevcut testler geçiyor |
| **Aşama 2** — F1 arayüzü | F1-S11 | Studio ve alt sayfalar gerçek backend'e bağlı; dürüstlük kuralı sağlanıyor |
| **Aşama 3** — Sentetik test laboratuvarı | F1-S12, F1-S13 | T01–T22 çalıştırıldı ve raporlandı; K01–K18 dolduruldu; regresyon temiz |
| **Aşama 4** — Gerçek ses ve telefon kabulü | F1-S14 | Aşağıdaki tablo ölçülmüş değerlerle dolu |

### Aşama 4 sonuç tablosu (gerçek ses — ölçüldükçe doldurulur)

| Senaryo | Kanal | Detection F1 | Endpoint p95 | Erken sonlandırma | Barge-in sinyali p95 | Duyulabilir kesilme p95 | False barge-in | Backchannel doğruluğu |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hızlı konuşma | Telefon | — | — | — | — | — | — | — |
| Yavaş konuşma, düşünme araları | Telefon | — | — | — | — | — | — | — |
| Farklı Türkçe ağızlar | Telefon | — | — | — | — | — | — | — |
| Kısa onaylar | Telefon | — | — | — | — | — | — | — |
| Nefes ve öksürük | Telefon | — | — | — | — | — | — | — |
| Araç gürültüsü | Telefon | — | — | — | — | — | — | — |
| Yankı | Telefon | — | — | — | — | — | — | — |
| Aynı anda konuşma | Telefon | — | — | — | — | — | — | — |
| Genel | Web | — | — | — | — | — | — | — |
