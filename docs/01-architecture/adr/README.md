# Mimari karar kayıtları (ADR)

Bir ADR, ölçüm veya kullanıcı kararı gerektiren bir mimari seçimi kayda geçirir. Kodlama ajanı ölçümü yapar ve taslağı yazar; **karar kullanıcıya aittir.** ADR "Kabul edildi" olmadan sahibi olan görev bitmiş sayılmaz.

Şablon: [`TEMPLATE.md`](TEMPLATE.md). Dosya adı: `ADR-F<aşama>-<no>-<kısa-ad>.md`.

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
| ADR-F3-01 | Özel kayıt okumada ikinci kimlik etkeni: plaka + ad, tek kullanımlık kod, ya da ikisi | F3-T05 | **Kullanıcı** | Karar bekleniyor |
| ADR-F4-01 | Ara parça noktalaması (virgül / noktalamasız) — doğal devam tonlaması, büyük harf kuralıyla birlikte | F4-T24 | Akustik ölçüm | Ölçüm bekleniyor |
| ADR-F4-02 | Saat okuma biçimi ("9:05" → "dokuz sıfır beş" / "dokuzu beş geçe") | F4-T11 | **Kullanıcı** | Karar bekleniyor |
| ADR-F5-01 | Speaker encoder seçimi ve lisansı (kimlik doğrulama, CPU) | F5-T22 | Ölçüm + lisans | Ölçüm bekleniyor |
| ADR-F6-01 | Çıkış yeniden örnekleyicisi: soxr `ResampleStream` / durumlu polifaz | F6-T13 | Ölçüm | Ölçüm bekleniyor |
| ADR-F6-02 | Hız kontrolü: F5 süre ölçekleme mi, F6 WSOLA mı (ikisi birden değil) | F6-T07 | Ölçüm | Ölçüm bekleniyor |
| ADR-F6-03 | Sentez geciktiğinde telefon kanalına sessizlik / comfort noise çerçevesi | F6-T16 | Ölçüm | Ölçüm bekleniyor |
| ADR-F6-04 | Web oynatma: `AudioBufferSourceNode` / AudioWorklet | F6-T21 | Ölçüm | Ölçüm bekleniyor |
| ADR-X-01 | Üretim topolojisi: Freya (Windows) ve Asterisk (Linux) aynı makinede mi, ayrı mı; AudioSocket güvenliği | F6-T20 | **Kullanıcı** | Karar bekleniyor |
| ADR-F3-02 | RAG gömme modeli (yerel yapıt ve lisans); karara kadar yalnız BM25 | F3-C | **Kullanıcı** + lisans | Karar bekleniyor |
| ADR-X-02 | Ortak GPU yöneticisi: VRAM bütçesi, STT/TTS eşzamanlılığı, Ollama `num_gpu` katman sayısı ([gpu-resource-manager](../../cross-cutting/gpu-resource-manager.md) §4) | F5-T16 (AIP-11) | Ölçüm | Ölçüm bekleniyor |

## Kullanıcı kararı bekleyen sorular

Bunlar ölçümle değil tercihle çözülür. Karar verilene kadar ilgili görev öneriyle ilerler, ama "bitti" sayılmaz.

1. **ADR-F3-01:** İkinci kimlik etkeni. Öneri: varsayılan plaka + ad soyad; yüksek riskli işlemlerde (kayıt değişikliği) ek olarak tek kullanımlık kod.
2. **ADR-F4-02:** "9:05" okuması. Öneri: randevu bağlamında "dokuz sıfır beş"; teyit cümlelerinde aynı biçim (tutarlılık).
3. **Telefon numarası okuma** (F4 spec §12): gruplu (0532 · 123 · 45 · 67) mı, rakam rakam mı? Öneri: gruplu; A/B dinlemeyle doğrulanır.
4. **ADR-X-01:** Üretim topolojisi.
5. **Sözlük onay yetkisi** (F4 spec §12): Hyundai gibi tartışmalı marka okunuşlarını kim onaylar? Sözlükteki `review_status = approved` alanını yalnızca bu kişi/rol değiştirebilir ([shared-lexicon](../../cross-cutting/shared-lexicon.md)).
6. **Karşılamada yapay zekâ bildirimi** ([K-06](../../execution/decisions.md#k-06--yapay-zekâ-bildirimi-açık)): arayanın bir yapay zekâ ile konuştuğu karşılamada söylensin mi, metni ne olsun? Öneri: kısa bildirim; metin kullanıcı onayıyla. G5 ve pilot bu karar olmadan başlamaz.
7. **RAG gömme modeli** (ADR-F3-02): yerel gömme modeli ve lisansı. Öneri: karara kadar yalnız BM25.
