# Vizyon ve kapsam

## Vizyon

Freya; yerel çalışan, Türkçe konuşan, telefon ve mikrofon üzerinden otomotiv servis işlemlerini (randevu, ekspertiz, servis durumu, bilgi, operatöre aktarım) yürüten bir sesli asistandır.

**Freya 2.0'ın hedefi:** Mevcut PoC'u sıfırdan yazmadan, F0–F6 ses hattını ve ortak katmanı derinleştirerek gerçek telefon görüşmesine hazır hale getirmek.

## Temel ilkeler

1. **Local-first / offline-first.** Tüm modeller tek bir RTX 4070 Laptop 8 GB üzerinde çalışır. Bulut API'si zorunlu değildir.
2. **Yeni model yerine mevcut modellerin koordinasyonu.** Whisper, Qwen 2.5 7B ve FreyaTTS'in tek örneği; ortak GPU yöneticisi.
3. **Önce doğruluk, sonra hız.** Otomotiv terim doğruluğu (bugün %48,04, hedef %95) birinci önceliktir.
4. **Ölçülmeden iddia yok.** Her hedef bir ölçüm tanımına, her ölçüm bir rapora bağlıdır.
5. **Güvenli işlem.** Yazma işlemleri onay, idempotency ve uzlaştırma ile; özel kayıtlar kimlik doğrulamasıyla.
6. **Leyla'nın sesi korunur.** Seed 9 ve model ağırlıkları sabit; her değişiklik referans kümesine karşı ölçülür.

## Katmanlar

| Katman | Ad | Öncelik | Belge |
| --- | --- | --- | --- |
| F0 | Audio Acquisition & Enhancement | P1 | [spec](../stages/F0-audio-acquisition/spec.md) |
| F1 | Voice & Turn Detection | P0 | [spec](../stages/F1-voice-turn-detection/spec.md) |
| F2 | Speech Recognition & Understanding | P0 | [spec](../stages/F2-speech-recognition/spec.md) |
| F3 | Dialogue Intelligence & Multi-Agent Orchestration | P0 | [spec](../stages/F3-dialogue-intelligence/spec.md) |
| F4 | Turkish Linguistic Frontend & Prosody | P0 | [spec](../stages/F4-linguistic-frontend/spec.md) |
| F5 | Neural Speech Synthesis & Voice Identity | P0 | [spec](../stages/F5-neural-synthesis/spec.md) |
| F6 | Audio Rendering, DSP & Telephony Transport | P0 | [spec](../stages/F6-rendering-transport/spec.md) |
| Ortak | GPU, oturum, gözlemlenebilirlik, güvenlik, hata kurtarma | P0 | [cross-cutting](../cross-cutting/README.md) |

## Kapsam

**Kapsamda:**
- Web (tarayıcı mikrofonu) ve telefon (Asterisk AudioSocket; ileride chan_websocket) kanalları
- Türkçe konuşma; Türkiye'de satılan araç marka/modelleri
- Randevu, ekspertiz, servis durumu, teknik bilgi, satış/parça bilgisi, operatöre aktarım akışları
- Her katman için Studio arayüzü (React yönetim paneli)
- Sentetik test laboratuvarları ve gerçek koşul kabul testleri

**Kapsam dışı (Freya 2.0 için):**
- Yeni temel model eğitimi; FreyaTTS'in yeniden eğitimi (yalnızca son aşamada, ayrı sürüm olarak kontrollü LoRA denemesi — F5-S26)
- Çok dilli konuşma
- Bulut tabanlı STT/TTS/LLM'e geçiş
- Çok GPU'lu veya sunucu ölçeğinde dağıtım (eşzamanlı görüşme kapasitesi ölçülür, hedef olarak büyütülmez)

## Başarı ölçütleri (Freya 2.0 sonu)

| Ölçüt | Bugün | Hedef | Kaynak |
| --- | --- | --- | --- |
| Otomotiv terim doğruluğu (birleşik TTS→STT) | %48,04 | %95 (tanıma ve seslendirme ayrıca raporlanır) | F2 K03, F4 akustik kabul (F4-T33) |
| WER / CER (sentetik) | %18,7 / %7,6 | ≤ %10 / ≤ %4 | F2 K01, K02 |
| İlk ses (TTFA), LLM gerektirmeyen tur | 1,4–3,2 s (tek örnek) | 1,2 s p95 | [latency-budget](../01-architecture/latency-budget.md) |
| Barge-in duyulabilir kesilme | Ölçülmedi | ≤ 200 ms p95 | F1 K07, F6 K10 |
| Tepe VRAM | 7478 / 8188 MiB (%91,3) | Ölçülmüş bütçe içinde, OOM yok | [gpu-resource-manager](../cross-cutting/gpu-resource-manager.md) |
| Gerçek SIP ve insan sesi kabulü | HOLD | L0–L6 kanıtlı | [acceptance-gates](../testing/acceptance-gates.md) |
