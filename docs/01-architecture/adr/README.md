# Mimari karar kayıtları (ADR)

Bir ADR, ölçüm veya kullanıcı kararı gerektiren bir mimari seçimi kayda geçirir. Kodlama ajanı ölçümü yapar ve taslağı yazar; **karar kullanıcıya aittir.** ADR "Kabul edildi" olmadan sahibi olan görev bitmiş sayılmaz.

Şablon: [`TEMPLATE.md`](TEMPLATE.md). Dosya adı: `ADR-F<aşama>-<no>-<kısa-ad>.md` (aşamalar arası kararlar `ADR-X-<no>`). Kullanıcının karar günlüğündeki numaralar (ADR-001…) ADR başlığında ve dizinde ayrıca belirtilir.

## Durumlar

`Taslak` → `Ölçüm bekleniyor` → `Karar bekleniyor` → `Kabul edildi` / `Reddedildi` / `Yerine geçildi (ADR-…)`

## Dizin

> "Sahibi" sütunundaki eski görev ve AIP kimliklerinin hangi pakette yapıldığı: [legacy-mapping.md](../../execution/legacy-mapping.md). Güncel karar listesi ve güvenli varsayılanlar: [ana plan §Açık kararlar](../../execution/master-plan.md#açık-kararlar).

| ADR | Konu | Sahibi | Karar türü | Durum |
| --- | --- | --- | --- | --- |
| ADR-F0-01 | F0 DSP iç örnekleme hızı: `min(giriş, 16 kHz)`; parametreler ms/Hz cinsinden | F0-S02 (F0-T05/T06) | Ölçüm | Taslak (öneri [F0 §3.1](../../stages/F0-audio-acquisition/spec.md)) |
| ADR-F0-02 | AEC yöntemi ve kütüphanesi; telefon hattında gereklilik | F0-T18 | Ölçüm + lisans | Ölçüm bekleniyor |
| ADR-F0-03 | RNNoise alternatifi (48 kHz köprüsü, lisans) | F0-T20 | Ölçüm + lisans | Ölçüm bekleniyor |
| ADR-F1-01 | Silero VAD oturum izolasyonu: oturum başına model kopyası mı, durum (state) ayrımı mı | F1-T03 | Ölçüm | Ölçüm bekleniyor |
| ADR-F1-02 | Barge-in gecikme bütçesi çatışması (≈ 129 ms vs ≤ 100 ms): seçenek A–D | F1-T10 | Ölçüm + kullanıcı | Ölçüm bekleniyor |
| ADR-F2-01 | N-best: Faster-Whisper / CTranslate2 çoklu hipotez desteği | F2-T10 | Ölçüm | Ölçüm bekleniyor |
| [ADR-F3-01](ADR-F3-01-arayan-kimlik-dogrulama.md) | Arayan kimliği: arayan numarası + doğum yılı (yoksa plaka son 3–4 hanesi) — karar günlüğü ADR-001 | H01, M07, F3-A (F3-T05) | **Kullanıcı** | Kabul edildi (2026-11-26) |
| ADR-F4-01 | Ara parça noktalaması (virgül / noktalamasız) — doğal devam tonlaması, büyük harf kuralıyla birlikte | F4-T24 | Akustik ölçüm | Ölçüm bekleniyor |
| [ADR-F4-02](ADR-F4-02-saat-tarih-okuma.md) | Saat okuma: doğal Türkçe, gün dilimiyle — ADR-003 | F4-A (F4-T11) | **Kullanıcı** | Kabul edildi (2026-11-26) |
| [ADR-F4-03](ADR-F4-03-telefon-numarasi-okuma.md) | Telefon okuma: `05xx xxx xx xx` (4-3-2-2) gruplama — ADR-004 | F4-A | **Kullanıcı** | Kabul edildi (revize, 2026-11-26) |
| ADR-F5-01 | Speaker encoder seçimi ve lisansı (kimlik doğrulama, CPU) | F5-T22 | Ölçüm + lisans | Ölçüm bekleniyor |
| ADR-F6-01 | Çıkış yeniden örnekleyicisi: soxr `ResampleStream` / durumlu polifaz | F6-T13 | Ölçüm | Ölçüm bekleniyor |
| ADR-F6-02 | Hız kontrolü: F5 süre ölçekleme mi, F6 WSOLA mı (ikisi birden değil) | F6-T07 | Ölçüm | Ölçüm bekleniyor |
| ADR-F6-03 | Sentez geciktiğinde telefon kanalına sessizlik / comfort noise çerçevesi | F6-T16 | Ölçüm | Ölçüm bekleniyor |
| ADR-F6-04 | Web oynatma: `AudioBufferSourceNode` / AudioWorklet | F6-T21 | Ölçüm | Ölçüm bekleniyor |
| [ADR-X-01](ADR-X-01-asterisk-dagitim.md) | Asterisk dağıtımı: pilot aynı makine, üretim ayrı sunucu — ADR-006 | F6-A, F6-D, G5 (F6-T20) | **Kullanıcı** | Kabul edildi (2026-11-26) |
| [ADR-X-03](ADR-X-03-yapay-zeka-bildirimi.md) | Karşılamada yapay zekâ bildirimi — ADR-002 | H01, F3-A, G5, PILOT | **Kullanıcı** | Kabul edildi (2026-11-26) |
| [ADR-X-04](ADR-X-04-sozluk-okunus-onayi.md) | Sözlük okunuş onayı: ürün sahibi + iş birimi — ADR-005 | M05, F4-B | **Kullanıcı** | Kabul edildi (2026-11-26) |
| [ADR-F3-02](ADR-F3-02-gomme-modeli.md) | RAG gömme modeli: yalnız bge-m3, CPU — ADR-007 | F3-C | **Kullanıcı** + lisans | Kabul edildi (revize, 2026-11-26) |
| ADR-X-02 | Ortak GPU yöneticisi: VRAM bütçesi, STT/TTS eşzamanlılığı, Ollama `num_gpu` katman sayısı ([gpu-resource-manager](../../cross-cutting/gpu-resource-manager.md) §4) | F5-T16 (AIP-11) | Ölçüm | Ölçüm bekleniyor |

## Kullanıcı kararları (2026-11-26)

Karar günlüğündeki yedi karar kabul edildi; özet ve etkilenen paketler: [ana plan §Verilen kararlar](../../execution/master-plan.md#verilen-kararlar).

| Karar günlüğü | ADR |
| --- | --- |
| ADR-001 Arayan kimliği | [ADR-F3-01](ADR-F3-01-arayan-kimlik-dogrulama.md) |
| ADR-002 Yapay zekâ bildirimi | [ADR-X-03](ADR-X-03-yapay-zeka-bildirimi.md) |
| ADR-003 Saat ve tarih okuma | [ADR-F4-02](ADR-F4-02-saat-tarih-okuma.md) |
| ADR-004 Telefon numarası okuma | [ADR-F4-03](ADR-F4-03-telefon-numarasi-okuma.md) |
| ADR-005 Sözlük okunuş onayı | [ADR-X-04](ADR-X-04-sozluk-okunus-onayi.md) |
| ADR-006 Asterisk dağıtımı | [ADR-X-01](ADR-X-01-asterisk-dagitim.md) |
| ADR-007 Gömme modeli | [ADR-F3-02](ADR-F3-02-gomme-modeli.md) |

Kalan kullanıcı sorusu: belge derlemi lisans ve inceleme yetkilisi ([ana plan §Açık kararlar](../../execution/master-plan.md#açık-kararlar)).
