# Mevcut durum (PoC taban çizgisi)

Bu belge Freya 2.0 başlarken PoC'un **ölçülmüş** durumunu ve plan hazırlanırken kod incelemesiyle bulunan sorunları tek yerde toplar. Ayrıntılar ilgili aşamanın `spec.md` §3 bölümündedir.

İncelenen PoC sürümü: `FreyaTTS_Automotive_PoC@6273981` (2026-11-21).

## 1. Ölçülmüş değerler

Kaynak: PoC `docs/VERIFICATION.md`, `docs/measured-latency.json` (6 Kasım 2026). Müşteri sesi sentetik TTS sesidir; gecikmeler **tek çalıştırma örneğidir**, p95 veya gerçek telefon gecikmesi değildir.

| Metrik | Değer | Durum |
| --- | --- | --- |
| WER | %18,7 | Eşik içinde (PASS) |
| CER | %7,6 | Eşik içinde (PASS) |
| Otomotiv terim doğruluğu | %48,04 | Hedef %95 (FAIL) |
| ABX, F0 tabanı | Ölçülmedi | HOLD |
| Tepe VRAM | 7478 / 8188 MiB (%91,3) | Ön ısıtmadan önce; masaüstü uygulamaları (~1770 MiB) dahil |
| Ana kabul cümlesi | 6 çalıştırmada 2 başarılı | — |
| Kısa araç cümlesi | 4 çalıştırmada 4 başarılı | — |

| Görüşme adımı | İlk ses (tek örnek) |
| --- | --- |
| Önbellekteki karşılama | ~15 ms |
| Müşteri adı turu | ~1,4 s |
| Araç turu | ~3,2 s |
| Seçim ve onay turu | ~3,2 s |
| LLM gerektiren tur | ~6 s |
| STT | ~0,3–1,5 s |

Gerçek Asterisk/SIP hattı, insan sesi ve operatör aktarımı kabul kapıları **HOLD** durumundadır.

**Önemli:** Terim doğruluğu TTS ve STT'nin birleşik sonucudur (TTS → STT döngüsü). Hatanın hangi modelden kaynaklandığı ayrıştırılmamıştır. F2-T01 ve F4-T03/F4-T33 bunu ayırır.

## 2. Aşama bazında bulgular (özet)

Her satır ilgili `spec.md` bölümündeki doğrulanmış bulguya bağlanır.

### F0 — Ses alma ve iyileştirme ([spec §5](../stages/F0-audio-acquisition/spec.md))
- Giriş 100 ms bloklarla toplanıyor; spektral gürültü bastırıcının algoritmik gecikmesi 8 kHz'de ≈ 24–28 ms.
- Soft AGC'de kazanç rampası etkisiz (başlangıç ve bitiş kazancı aynı); çerçeve sınırında basamaklar. Zaman sabitleri belgelenenle uyuşmuyor.
- Limiter tavanı ≈ −0,04 dBFS (plan −1 dBFS).
- Gürültü kalibrasyonu sırasında ses VAD/STT'ye gitmiyor.
- DTMF, NS/AGC/resample **sonrası** algılanıyor; AudioSocket bant dışı DTMF ile çift sayım riski.
- Tarayıcıda `noiseSuppression` ve `autoGainControl` açık → sunucu DSP'si ile çift işleme.
- `LookbackBuffer` iki yerde dolduruluyor ama STT için okunmuyor.
- Kayıt yalnızca işlenmiş sesi yazıyor.

### F1 — Konuşma ve tur algılama ([spec §3.2](../stages/F1-voice-turn-detection/spec.md), S1–S8)
- **S1** Tek Silero VAD örneği tüm oturumlarda paylaşılıyor; yeni oturum diğerlerinin VAD durumunu sıfırlıyor.
- **S5** Yeni konuşma bölümü önceki bölümün işlenmesini iptal ediyor.
- S2 üç ayrı pre-roll; S3 `check_pause_timeout()` hiç çağrılmıyor; S4 sabit 320 ms sessizlik; S6 barge-in gecikme metriği yanlış; S7 backchannel listesi "evet/tamam" gibi cevapları içeriyor; S8 oynatma yokken de duraklatma olayı.

### F2 — Konuşma tanıma ([spec §3](../stages/F2-speech-recognition/spec.md), S1–S8)
- **S1** "Katalog hotword'leri" katalogdan değil müşteri araç tablosundan; **S2** hotword'ler varsayılan kapalı.
- S3 hotword prompt uzunluğu denetlenmiyor; S4 sıcaklık geri dönüşü açık; S5 düşük güvenli segmentler sessizce atılıyor; S6 dönüş tipi `str` (güven bilgisi kayboluyor); S7 iptal edilen STT GPU'yu meşgul ediyor; S8 Türkçe Whisper sahte metin ("Altyazı M.K.") listesi yok.

### F3 — Diyalog ([spec §3](../stages/F3-dialogue-intelligence/spec.md), P1–P9)
- **P4** Kimlik doğrulaması olmadan, yalnızca arayan numarasıyla garanti ve bakım geçmişi paylaşılıyor.
- **P7** Çoklu araç randevusunda aynı idempotency anahtarı → ikinci araç başarısız olabilir.
- P1 yazma araçları kayıtlı değil; P2 zaman aşımı uzlaştırması yok; P3 Supervisor araç listesi yanlış kaynaktan; P5 her arayana profil açılıyor; P6 LLM bağlamına fazla kişisel veri; P8 bazı testler canlı Ollama gerektiriyor; P9 guarded modda aktarım her zaman "yapılamıyor".

### F4 — Türkçe dilbilim ([spec §3.2](../stages/F4-linguistic-frontend/spec.md), L1–L12)
- **L5** Tek desteklenmeyen karakter ("−5 °C", "Mégane", "Coupé") tüm yanıtı düşürüyor.
- **L3** Sıra sayıları ("1. seçenek") cümleyi bölüyor.
- L1 çift normalizasyon; L2 duraklama planı atılıyor; L4 zengin otomotiv sözlüğü canlı yolda kullanılmıyor (canlı sözlükte tek kayıt); L6 tablodaki okuma hataları; L7/L12 üç ayrı normalizer; L8 morfoloji canlı yolda değil; L9–L10 model kısıtları; L11 kısa parça koruması eksik.

### F5 — Sinirsel sentez ([spec §3.3](../stages/F5-neural-synthesis/spec.md), N1–N11)
- **N3** Seed bazı yollarda sessizce 9'a dönüyor.
- **N5** İptal edilen parçalar yine sentezleniyor.
- N1 latent gürültü yığındaki en uzun öğeye göre; N2 VAE dolgulu latentte; N4 toplu yolda GPU kilidi yok; N6 canlı yolda bozuk ama sessiz olmayan ses geçebilir; N7 F5 içinde sessizlik ve fade; N8 eksik önbellek anahtarı; N9 ölçülmemiş performans iddiaları kodda; N10 `max_concurrent_calls = 50` ölçülmemiş; N11 kısa ifade süre sınırının kanıtı küçük örneklem.

### F6 — Rendering ve aktarım ([spec §3.2](../stages/F6-rendering-transport/spec.md), R1–R12)
- **R6** Ağ yazmasında zaman aşımı yok; bloklanan gönderim barge-in'i de bloklar.
- R1 web ve telefon farklı DSP zincirleri; R2 durumsuz filtreler parça sınırında genliğin ~%29'u kadar sapma; R3 `tanh` doygunlaştırıcısı tüm seviyelerde kazanç ve THD ekliyor; R4 üç pacer; R5 F6 süresi oynatma süresini içeriyor; R7 tarayıcı oynatma makbuzu yok; R8 chan_websocket mesaj biçimi ve XOFF; R9 AudioSocket kimlik doğrulamasız; R10–R12.

## 3. Aşamalar arası bulgular (genel belgeler hazırlanırken)

| # | Bulgu | Kanıt | Plan |
| --- | --- | --- | --- |
| X1 | **Canlı oturumda tur kimliği ile generation kimliği aynı sayaç** | `session.py`: `self.generation` hem iptal sayacı hem oynatma mesajlarındaki `"turn_id"` | [`interfaces.md`](../01-architecture/interfaces.md) §2: `turn_id` ve `generation_id` ayrı |
| X2 | **Milestone paketinde hazır ortak çekirdek var, canlı yol kullanmıyor** | `automotive_voice/core/`: tipli kimlikler (`SessionId`, `TurnId`, `GenerationId`), `CancellationController`, `EventEnvelope` + `EventBus` (sıra ve kapasite denetimli), `resilience/durable.DurableJournal`. Canlı `session.py` kendi sayaçlarını ve `pipeline_telemetry` olaylarını kullanıyor | Ortak katman bunları temel alır ([session-and-state](../cross-cutting/session-and-state.md)) |
| X3 | **PoC'ta 31 JSON Schema sözleşmesi var** | `contracts/*.schema.json` (Draft 2020-12; `tests/milestones/test_m05_contracts.py` doğruluyor). `tts_input`, `m06_audio_chunk_metadata`, `m06_flush_request/ack`, `event`, `conversation_signal`, `session_snapshot` yeni sözleşmelerle örtüşüyor | Yeni sözleşmeler de `contracts/` altında yayımlanır; örtüşenler sürümlenir, kopyalanmaz |
| X4 | **Milestone paketinde F6'nın hedeflediği kuyruk ve sahte transport hazır** | `automotive_voice/audio/queue.MediaBuffer`, `telephony/transport.FakeTransport` (XOFF/XON, flush onayı) | F6 spec §11 |
| X5 | **Üçüncü normalizer ve prozodi planlayıcısı** | `automotive_voice/nlp/normalizer`, `prosody/planner` | F4 spec L12 |
| X6 | **GPU sağlık izleyicisi zamanlamaya bağlı değil** | `backend/gpu_health_circuit_breaker.py` (`nvidia-smi` + `torch.cuda.mem_get_info`) yalnızca gözlem panelinde | Ortak GPU yöneticisinin bellek bütçesi girdisi ([gpu-resource-manager](../cross-cutting/gpu-resource-manager.md)) |
| X7 | **A/B deneyi oturum başına istem ve karşılama şablonu atıyor** | `backend/ab_testing.assign_conversation_variant` canlı oturumda | Ablation ve kalite ölçümlerinde varyant kaydı zorunlu ([observability](../cross-cutting/observability.md)) |
| X8 | **Test dosyalarının yaklaşık yarısı torch kurulu olmadan toplanamıyor** | 85 test dosyasının 43'ü toplama aşamasında düşüyor (toplanabilen 1 079 test bunların dışında): `backend.main` → `routers/text_speech.py` → `sft_leyla.py` modül düzeyinde `import torch`. API ve oturum testleri dolaylı olarak GPU yığınına bağımlı | AIP-01: `sft_leyla` ve router'larda ağır içe aktarmalar tembel (lazy) yapılır; testler torch, CUDA ve Ollama olmadan toplanır ve çalışır |

## 4. Korunacak güçlü yanlar

- Kural öncelikli diyalog yönetimi ve Supervisor yapısı
- Sabit ses kimliği (Leyla, seed 9), model ön ısıtma, karşılama önbelleği
- Sınırlı sentez kuyruğu ve eski turun iptali (`turn == generation` kontrolü)
- Silero VAD, 20 ms çerçeve sözleşmesi, deadline re-clamp'li pacing
- AudioSocket el sıkışma ve kapasite kontrolleri; tek kullanımlık web oturum bileti
- `normalizer_rules.py` (para, tarih, saat, plaka, sonek uyumu), `backend/morphology/`
- KVKK modülleri (`kvkk_compliance`, `redaction_kvkk_guard`, `audio_archive_compliance`)
- Ölçüm dürüstlüğü kültürü: VERIFICATION.md'de HOLD/FAIL açıkça yazılı
