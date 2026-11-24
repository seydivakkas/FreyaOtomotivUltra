# Ölçüm planı (ses laboratuvarı)

Bu belge laboratuvarda ölçülecek metrikleri, ölçüm kurallarını ve hangi aşamanın hangi metrikten sorumlu olduğunu toplar. Hedef değerler aşamaların `acceptance.md` dosyalarındadır.

## 1. Metrikler

| Kategori | Metrik | Sorumlu aşama | Araç |
| --- | --- | --- | --- |
| Sinyal kalitesi | RMS, tepe, SNR, kırpılma, DC | F0, F6 | F0 Quality Analyzer, F6 telemetri |
| Gürültü temizleme | SI-SDR, STOI, gürültü bastırma (dB) | F0 | F0 laboratuvarı (F0-T30) |
| Konuşma tanıma | WER, CER, **entity accuracy** (marka, model, yıl, plaka, telefon) | F2 | F2 benchmark (F2-T32) |
| Telaffuz | PER (yaklaşık, F4 G2P), marka/model seslendirme doğruluğu | F4 | F4 akustik kabul (F4-T33) |
| Ses doğallığı | MOS (insan), F0 eğrisi, konuşma hızı | F5, F6 | Dinleme testi, pitch analizörü |
| Ses kimliği | Speaker similarity, ABX (insan) | F5 | Speaker encoder (F5-T22), dinleme testi |
| Performans | TTFA, RTF, aşama süreleri, p50/p95/p99 | Tümü | Gecikme profili ([observability](../cross-cutting/observability.md)) |
| Kesinti | Barge-in kontrol gecikmesi, duyulabilir kesilme, yanlış kesinti oranı | F1, F6 | F1 laboratuvarı, istemci makbuzları, loopback |
| Telefoni | Jitter, paket kaybı, underrun, gönderim sapması | F6 | F6 telemetri |
| Donanım | VRAM, GPU kullanımı, CPU, RAM (60 dk sızıntı testi) | Ortak, tümü | GPU yöneticisi, `nvidia-smi` |
| Diyalog | Görev tamamlama, yanlış işlem, doğrulanmamış başarı iddiası, LLM çağrı oranı | F3 | F3 değerlendiricileri (F3-T32) |

## 2. Ölçüm kuralları

1. **Üç ses noktası ayrı değerlendirilir:** ham ses, işlenmiş ses, telefon bandına dönüştürülmüş ses (ve gerektiğinde G.711 gidiş-dönüşü).
2. **İnsan değerlendirmesi simüle edilmez.** MOS, ABX ve uzman telaffuz değerlendirmesi gerçek dinleyicilerle yapılır; dinleyici sayısı, koşullar ve güven aralığı raporlanır.
3. **Kalibrasyon ve test kümeleri ayrıdır** (F2-T33). Eşikler, ağırlıklar ve profiller yalnızca kalibrasyon kümesinde ayarlanır.
4. **Dağılım raporlanır.** p50/p95/p99 ve örnek sayısı; tek çalıştırma "örnek" diye etiketlenir.
5. **Koşullar kaydedilir:** donanım, sürücü, model sürümleri, etkin bayraklar, A/B varyantı, masaüstü uygulamalarının durumu, `num_gpu`.
6. **Birleşik metrik ayrıştırılır.** TTS → STT döngüsü (bugünkü terim doğruluğu) tanıma ve seslendirme hatalarını ayrı göstermez; ayrıştırma [shared-lexicon](../cross-cutting/shared-lexicon.md) §3'tedir.
7. **Sonuçlar dosyaya yazılır:** `data/<aşama>/lab-report-<tarih>.json` (PoC reposu). Belgeye ve Studio'ya yalnızca bu dosyadan değer taşınır.

## 3. Rapor biçimi

```json
{
  "schema_version": "lab_report.v1",
  "stage": "F2",
  "date": "2026-12-01",
  "git_commit": "<PoC commit>",
  "hardware": {"gpu": "RTX 4070 Laptop 8 GB", "driver": "…", "desktop_apps": "closed"},
  "flags": {"f2_pipeline_v2": true},
  "dataset": {"name": "f2_acoustic_synth", "version": "1", "split": "test", "n": 0},
  "metrics": [
    {"id": "K03", "name": "Otomotiv terim doğruluğu", "value": null, "unit": "%", "p50": null, "p95": null, "n": 0}
  ],
  "notes": []
}
```

`value: null` "ölçülmedi" demektir; sıfır değildir.

## 4. Sentetik test motoru

Her aşamanın kendi sentetik üreteci vardır; ortak kurallar:

| Üreteç | Aşama | Görev |
| --- | --- | --- |
| Sinyal üreteci (ton, gürültü, yankı, kırpılma, DTMF) | F0 | F0-T29 |
| Gürültü karışımları (kabin, rüzgâr, fan; SNR seviyeleri) | F0 → F1, F2 | F0-T03 |
| Etiketli konuşma derlemi (başlangıç/bitiş, backchannel, barge-in) | F1 | F1-T02 |
| Metin hattı ve akustik sentetik küme (otomotiv terimleri) | F2 | F2-T30, F2-T31 |
| 2 000 senaryoluk diyalog kümesi | F3 | F3-T40 |
| 3 000 örneklik dilbilim kümesi | F4 | F4-T30 |
| 2 000 girdilik sentez kümesi | F5 | F5-T28 |
| Sentetik görüşme (uçtan uca, AudioSocket istemcisi) | F6 | F6-T28 |

**Dikkat:** FreyaTTS ile üretilmiş "müşteri sesi" STT'yi ölçmek için tek başına yeterli değildir (aynı modelin hataları iki yönde birbirini gizleyebilir veya büyütebilir). STT ölçümünde insan kaydı veya farklı bir referans ses kaynağı bulunmalıdır (F2-T31, F2-T36).
