# F2 — Kabul Kriterleri ve Testler

> **Bu dosyadaki hedefler elde edilmiş sonuçlar değildir; önerilen mühendislik hedefleridir.** Bir kutu yalnızca test çalıştırılıp sonucu laboratuvar raporuna (`data/f2/lab-report-*.json`) yazıldıktan sonra işaretlenir. Sentetik veri kümesindeki başarı, gerçek müşteri konuşmalarındaki başarının kanıtı olarak kullanılmaz.

**Ölçüm kuralları:**
- Her metrik ölçüldüğü **test hattıyla** birlikte raporlanır: metin / akustik sentetik / akustik insan (spec §8.2).
- Akustik metrikler 16 kHz web ve 8 kHz telefon için ayrı raporlanır.
- Ham WER ile düzeltme sonrası WER ayrı raporlanır.
- Gecikme hedefleri kısa turlar (`yes_no`, `option_number`) ve uzun turlar için ayrı ölçülür.
- Mevcut değerler (%18,7 / %7,6 / %48,04) TTS + STT birleşik ölçümüdür; hedeflerle karşılaştırılırken aynı hat ve aynı veri kümesi kullanılır.

---

## 1. Kalite kapısı

### 1.1 Plandaki hedefler

| # | Metrik | Mevcut | Hedef | Ölçüm tanımı | Test | Sonuç |
| --- | --- | --- | --- | --- | --- | --- |
| K01 | WER | %18,7 | ≤ %10 | (S + D + I) / N; akustik hatlar | T01–T05 | ☐ |
| K02 | CER | %7,6 | ≤ %4 | (S_c + D_c + I_c) / N_c | T01–T05 | ☐ |
| K03 | Otomotiv terim doğruluğu | %48,04 | ≥ %95 | N_doğru / N_referans; marka, model, motor terimi ayrı | T09–T13 | ☐ |
| K04 | Telefon numarası tam eşleşmesi | — | ≥ %98 | 11 hanenin tamamı doğru | T17 | ☐ |
| K05 | Plaka tam eşleşmesi | — | ≥ %98 | İl kodu, harf ve rakam grubu tam doğru | T16 | ☐ |
| K06 | Model yılı doğruluğu | — | ≥ %99 | Yıl değeri tam doğru | T15 | ☐ |
| K07 | Yanlış otomatik düzeltme | — | ≤ %1 | Yanlış kanoniğe çevrilen doğru sözcük / uygulanan düzeltme | T23 | ☐ |
| K08 | Negatif örneklerde hallucination | — | ≤ %1 | Sessizlik/gürültü örneklerinde boş olmayan final transkript oranı | T20 | ☐ |
| K09 | Partial Transcript Latency p95 | — | ≤ 800 ms | Kısmi sonucun yayınlandığı an − kapsadığı son ses örneğinin geldiği an | T06, T07 | ☐ |
| K10 | Final STT Latency p95 | — | ≤ 500 ms | Final `ASRResult` yayın anı − F1 `FINALIZE` olayı | T01, T05 | ☐ |
| K11 | STT Real-Time Factor | — | ≤ 0,3 | STT süresi / ses süresi (final çözümleme) | T28 | ☐ |
| K12 | Eski turn ID kabulü | — | 0 | F3'e ulaşan eski turn ID'li sonuç sayısı | T24 | ☐ |

> **K09 için not:** Plan, en kısa ilk çözümleme süresini 800 ms olarak belirliyor. Bu nedenle ilk kısmi sonuç konuşma başlangıcından en erken 800 ms + çözümleme süresi sonra gelebilir. K09 bu yüzden "konuşma başlangıcından" değil, **kısmi sonucun ne kadar bayat olduğu** üzerinden tanımlandı.

### 1.2 PoC incelemesine dayanan ek kriterler (öneri)

| # | Metrik | Önerilen hedef | Gerekçe | Test | Sonuç |
| --- | --- | --- | --- | --- | --- |
| K13 | Hotword bias | Söylenmeyen katalog adının transkripte girme oranı ≤ %1 | Hotword'ler prompt olarak modeli yönlendirebilir | T10 | ☐ |
| K14 | Ham transkript korunumu | %100 | Her `ASRResult` boş olmayan `raw_transcript` alanı taşır (sessizlikte `""`); her düzeltme `corrections` içinde | T26 | ☐ |
| K15 | Alan içi konuşmada boş transkript | ≤ %1 | PoC düşük güvenli segmentleri sessizce atıyor (spec §3.2 S5) | T04, T22 | ☐ |
| K16 | Güven kalibrasyonu | Beklenen kalibrasyon hatası (ECE) ≤ 0,05; bu sağlanmadan `confidence` alanı `null` | Kalibre edilmemiş skor olasılık gibi sunulmamalı | T22 | ☐ |
| K17 | Teyit / yeniden sorma oranı | Katalog içi temiz konuşmada ≤ %15 | Her şeyi teyit etmek de görüşmeyi bozar | T11, T13 | ☐ |
| K18 | Deterministiklik | FAST/BALANCED/ACCURATE profillerinde aynı ses → aynı transkript (%100) | Sıcaklık geri dönüşü PoC'ta açık (S4) | T01 | ☐ |
| K19 | Gündelik sözcük çakışması alt kümesinde yanlış düzeltme | 0 / ≥ 50 örnek | "fiyat → Fiat", "mini → MINI" PoC'ta doğrulandı | T23 | ☐ |
| K20 | GPU belleği yetersizliğinde oturum kaybı | 0 | Oturum düşmeden `REPROMPT` | T25 | ☐ |

## 2. Test senaryoları (T01–T28)

**F2 test kontrol listesi: 0 / 28**

### Akustik tanıma

#### ☐ T01 — Temiz Türkçe konuşma
- **Girdi:** Akustik sentetik küme, temiz koşul; 16 kHz.
- **Geçme koşulu:** K01, K02 raporlanır; final gecikme (K10) ve deterministiklik (K18).

#### ☐ T02 — 8 kHz telefon bandı
- **Girdi:** T01 kümesinin telefon bandı dönüşümü (`apply_telephony_eq_and_downsample_8k` → 16 kHz).
- **Geçme koşulu:** WER/CER 16 kHz ile yan yana raporlanır; fark gerekçelendirilir.

#### ☐ T03 — Motor gürültülü konuşma
- **Girdi:** F0 derleminden SNR 20/10/5/0 dB motor karışımları; F0 açık ve kapalı.
- **Geçme koşulu:** WER ve terim doğruluğu SNR'a göre eğri olarak raporlanır; F0 açıkken kötüleşme yok (F0 K09 ile tutarlı).

#### ☐ T04 — Düşük ses seviyeli konuşma
- **Girdi:** −40 ve −45 dBFS konuşma.
- **Geçme koşulu:** Boş transkript oranı ≤ %1 (K15).

#### ☐ T05 — Hızlı ve yavaş konuşma
- **Girdi:** %80 ve %130 konuşma hızı.
- **Geçme koşulu:** WER raporlanır; final gecikme kısa ve uzun turlar için ayrı (K10).

### Kısmi transkript ve streaming

#### ☐ T06 — Kısmi transkript kararlılığı
- **Girdi:** "Benim aracım 2020 model Nissan Qashqai" türü cümleler; `event` ve `interval` modları.
- **Geçme koşulu:** Kararlı önek revizyon oranı raporlanır; K09 sağlanır; yalnızca `FINAL` F3'e işlem olarak gider.

#### ☐ T07 — Kayan pencere örtüşmesi
- **Girdi:** 3–10 s konuşmalar; 2/3/5 s pencere, 500 ms örtüşme.
- **Geçme koşulu:** Pencere sınırında bölünen sözcük finalde bütün (final tüm utterance üzerinde çözülür); oturum başına bekleyen kısmi görev ≤ 1.

#### ☐ T08 — İlk ve son kelimenin korunması
- **Girdi:** Zayıf başlangıçlı ve sonlu sözcüklerle başlayan/biten cümleler (F1 T05 sözcükleri).
- **Geçme koşulu:** İlk ve son sözcük finalde %100 bulunur (F1 pre/post-roll ile birlikte).

### Hotword ve otomotiv çözümleme

#### ☐ T09 — Hotwords ile marka tanıma
- **Girdi:** Marka/model kategorisi; hotword kapalı / PoC listesi / bağlamsal liste.
- **Geçme koşulu:** Bağlamsal liste terim doğruluğunu artırır; token bütçesi aşılmaz.

#### ☐ T10 — Hotword kaynaklı yanlış yönlendirme
- **Girdi:** Araç adı içermeyen cümleler, hotword açık ve kapalı.
- **Geçme koşulu:** Söylenmeyen katalog adının transkripte girme oranı ≤ %1 (K13).

#### ☐ T11 — Peugeot / Nissan / Škoda gibi marka varyantları
- **Girdi:** Planın fonetik sözlük tablosundaki tüm varyantlar (metin hattı) ve sesli karşılıkları (akustik hat).
- **Geçme koşulu:** Metin hattında %100 doğru kanonik; akustik hatta K03'e katkı raporlanır; teyit oranı (K17).

#### ☐ T12 — Benzer model isimleri
- **Girdi:** Qashqai / Kadjar, Megane / Mégane, i20 / i30, C3 / C4, 2008 / 3008 / 5008.
- **Geçme koşulu:** Aday farkı küçükse `CONFIRM`; yanlış `ACCEPT` 0.

#### ☐ T13 — Fonetik marka ve model eşleme
- **Girdi:** "Nisan kaş kay iki bin yirmi", "Hundai i yirmi", "Blue HDI motor" ve enjekte edilmiş ASR hataları.
- **Geçme koşulu:** `vehicle_make_model` bağlamında doğru kanonik; teyit oranı K17 sınırında.

#### ☐ T14 — Katalog dışı araç
- **Girdi:** Katalogda olmayan marka/model adları.
- **Geçme koşulu:** Ham ad korunur, `catalog_verified: false`; en yakın katalog aracına zorla eşlenmez (`ACCEPT` ile yanlış eşleşme 0).

### Varlık çıkarımı

#### ☐ T15 — Model yılı çözümleme
- **Girdi:** "iki bin yirmi", "yirmi bir model", "2019", "on dokuz model", geçersiz yıllar.
- **Geçme koşulu:** K06; makul aralık dışı yıl `CONFIRM`.

#### ☐ T16 — Türkçe plaka çözümleme
- **Girdi:** Rakamlı ve sözlü biçimler; 2/3/4 haneli gruplar; bölünmüş haneler ("12 3").
- **Geçme koşulu:** K05; PoC'ta çözülemeyen "on altı ka el iki bin beş yüz" ve "34 abc 12 3" doğru.

#### ☐ T17 — Telefon numarası çözümleme
- **Girdi:** 05xx biçimleri, sözlü okuma, gruplu okuma, eksik numara.
- **Geçme koşulu:** K04; eksik numarada sonuç üretilmez ve `REPROMPT` / F1 `WAIT` önerilir.

#### ☐ T18 — Tarih ve saat belirsizliği
- **Girdi:** "yarın saat iki", "on beş nisanda", "öğleden sonra üçte", "Nisan'da Nissan'ımı getireceğim".
- **Geçme koşulu:** İfadeler `DATE_EXPRESSION` / `TIME_EXPRESSION` olarak aktarılır, **çözülmez** (02.00/14.00 F3'te); "nisan" tarih bağlamında araç adayı üretmez, aynı cümlede "Nissan'ımı" araç olarak çözülür.

#### ☐ T19 — Evet / Hayır / İptal
- **Girdi:** Onay, ret, iptal ifadeleri ve "evet ama…" türü karışık cevaplar.
- **Geçme koşulu:** `YES_NO` varlığı doğru; karışık cevaplarda ek içerik kaybolmaz.

### Koruma ve güven

#### ☐ T20 — Sessizlikten sahte transkript üretme
- **Girdi:** 100 negatif örnek: sessizlik, motor, fan, nefes, Freya yankısı.
- **Geçme koşulu:** K08 ≤ %1; bilinen Türkçe Whisper kalıpları yakalanır.

#### ☐ T21 — Tekrarlı transkript
- **Girdi:** Whisper tekrar döngüsü örnekleri ve doğal tekrarlar ("evet evet", "hayır hayır, öyle değil").
- **Geçme koşulu:** Döngüler temizlenir; doğal tekrarlar korunur.

#### ☐ T22 — Düşük güven ve yeniden çözümleme
- **Girdi:** Düşük SNR ve zor marka adları.
- **Geçme koşulu:** `RE_DECODE` utterance başına en fazla 1; boş transkript oranı K15; kalibrasyon sonrası ECE (K16).

#### ☐ T23 — Yanlış otomatik düzeltme
- **Girdi:** Gündelik sözcük çakışması alt kümesi (≥ 50) ve genel metin hattı.
- **Geçme koşulu:** K07 ≤ %1; K19 = 0.

#### ☐ T24 — Eski turn ID iptali
- **Girdi:** STT sürerken F1 tarafından yeni tur açılması; gecikmiş sonuçlar.
- **Geçme koşulu:** K12 = 0; iptal edilen işin sonucu Utterance Manager'a birleştirme için verilir.

### Kaynak ve sözleşme

#### ☐ T25 — GPU bellek yetersizliği
- **Girdi:** Yapay CUDA OOM enjeksiyonu; TTS ve LLM eşzamanlı yük.
- **Geçme koşulu:** Oturum düşmez (K20); `FAST` ile tek yeniden deneme; olay kaydı.

#### ☐ T26 — F1–F2–F3 veri sözleşmesi
- **Girdi:** Şema doğrulamalı rastgele girdiler (özellik tabanlı test).
- **Geçme koşulu:** Tüm sonuçlar JSON Schema'ya uyar; K14 %100; `status != final` ile F3 işlem başlatamaz.

#### ☐ T27 — Eşzamanlı STT oturumları
- **Girdi:** 2 ve 4 oturum aynı anda konuşuyor.
- **Geçme koşulu:** Öncelik sırası korunur; oturumlar arası sonuç karışması 0; kuyruk bekleme süreleri raporlanır.

#### ☐ T28 — Uzun süreli performans testi
- **Girdi:** 60 dk, 4 oturum, karışık senaryolar.
- **Geçme koşulu:** RTF (K11); VRAM tepe değeri ve sızıntı yok; gecikme p95 kayması yok.

## 3. Aşama kapıları

| Aşama | Kapsam | Geçiş koşulu |
| --- | --- | --- |
| **Aşama 1** — Özelliklerin tamamlanması | F2-S01 … F2-S14 | Görevler bitti; mevcut testler geçiyor; `ASRResult` canlıda bayrak arkasında |
| **Aşama 2** — F2 arayüzü | F2-S15 | Studio gerçek backend'e bağlı; dürüstlük kuralı sağlanıyor |
| **Aşama 3** — Sentetik test laboratuvarı | F2-S16 … F2-S18 | T01–T28 çalıştırıldı; K01–K20 hat bazında dolduruldu; ablation tablosu yayımlandı |
| **Aşama 4** — Gerçek insan sesi ve telefon kabulü | F2-S19 | Aşağıdaki tablo ölçülmüş değerlerle dolu |

### Aşama 4 sonuç tablosu (gerçek insan sesi — ölçüldükçe doldurulur)

| Koşul | Kanal | WER | CER | Marka/model doğruluğu | Plaka | Telefon | Yıl | Teyit oranı | Final STT p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sessiz ortam | Web | — | — | — | — | — | — | — | — |
| Sessiz ortam | Telefon | — | — | — | — | — | — | — | — |
| Araç içi | Telefon | — | — | — | — | — | — | — | — |
| Farklı Türkçe ağızlar | Telefon | — | — | — | — | — | — | — | — |
| Yabancı marka telaffuzları | Telefon | — | — | — | — | — | — | — | — |

**Terim bazında gerçek ses sonuçları** (Qashqai, Peugeot, Citroën, Volkswagen, Hyundai, Škoda…): `docs/stages/F2-speech-recognition/field-terms.md` dosyasında, konuşmacı sayısıyla birlikte raporlanır.
