# Birleşik veri sözleşmeleri

Bu belge F0–F6 ve ortak katman arasındaki tüm sözleşmelerin **tek referansıdır**. Alanların tam tanımı ilgili `spec.md` bölümündedir; burada kimlik kuralları, zincir, sürümleme ve PoC'taki mevcut şemalarla eşleme bulunur.

> Sözleşme değişikliği önce bu belgede ve ilgili `spec.md` dosyasında yapılır (ayrı PR), sonra kodda.

## 1. Genel kurallar

| Kural | Açıklama |
| --- | --- |
| Python tipi | `backend/<paket>/contracts.py` içinde `@dataclass(frozen=True, slots=True)` |
| JSON Schema | PoC'taki `contracts/` klasöründe, Draft 2020-12 (mevcut 31 şemayla aynı biçim). Ad: `f<aşama>_<ad>.schema.json` |
| Sürüm alanı | `schema_version`: `"f<aşama>.<ad>.v<N>"` (ör. `f2.asr_result.v1`) |
| İkili veri | Ses verisi JSON'a girmez; metadata ile ilişkilendirilmiş ikili yük olarak taşınır (mevcut `audio_frame.metadata` ilkesi) |
| Zaman | Süreç içi zamanlar `time.monotonic_ns()`; kayıt ve denetim için ek olarak UTC ISO 8601 |
| Ölçülmemiş değer | `null`. Varsayılan sayı (ör. `confidence: 0.0`) uydurulmaz |
| Doğrulama | Her sözleşme için şema testi: `tests/contracts/test_<aşama>_contracts.py` (`jsonschema` opsiyonel bağımlılık; mevcut `tests/milestones/test_m05_contracts.py` örneği) |

## 2. Kimlikler

Kimlik tipleri PoC'taki `automotive_voice/core/identifiers.py` dosyasından alınır (`SessionId`, `TurnId`, `GenerationId`). Yeni kimlikler aynı dosyaya eklenir.

| Kimlik | Kapsam | Kim üretir | Ne zaman artar / oluşur |
| --- | --- | --- | --- |
| `session_id` | Görüşme | Oturum yöneticisi | Görüşme başında; 1–128 güvenli ASCII karakter |
| `turn_id` | Müşteri–Freya alışverişi | Oturum durum makinesi (`Session.new_turn`) | F1 müşterinin yeni bir sözünü `FINALIZE` ettiğinde |
| `generation_id` | Freya'nın iptal edilebilir tek yanıt üretimi | Oturum durum makinesi + `CancellationController.advance` | (a) `new_turn` ile birlikte; (b) barge-in `FLUSH` (`Session.interrupt`); (c) Freya henüz konuşmadan müşteri devam ettiğinde (`THINKING → LISTENING`, F1 `CONTINUE`) — [session-and-state](../cross-cutting/session-and-state.md) §3 |
| `utterance_id` | Tek söz (STT girdisi) | F1 | Utterance oluştuğunda |
| `plan_id` | F4 sentez planı | F4 | `model_text` dizisi + ses profili + seed + sözlük sürümü + normalizer sürümü hash'i |
| `chunk_id`, `chunk_index` | Sentez parçası | F4 / F5 | Plan içinde sıralı |
| `seq` | Çerçeve | F0 (giriş), F6 (çıkış) | Oturum içinde monoton |
| `event_id`, `sequence` | Telemetri olayı | Olay yolu | Mevcut `EventEnvelope` kuralı |

**Kurallar:**
- `turn_id` ile `generation_id` **ayrıdır** (PoC canlı yolunda tek sayaç — bulgu X1). Bir turda birden fazla generation olabilir (barge-in sonrası yeniden üretim). Aynı yanıtın parçaları (önbellekli onay cümlesi + içerik) aynı generation'dadır.
- **Soft pause generation'ı ilerletmez**; yalnızca `FLUSH` ilerletir.
- Eskime denetimi yalnızca `generation_id` ile yapılır: `CancellationController.is_current(generation_id)`.
- F2'den F6'ya kadar her çıktı `session_id`, `turn_id` ve `generation_id` taşır.
- Web istemcisine giden oynatma mesajlarındaki `turn_id` alanı geçiş süresince korunur, yanına `generation_id` eklenir; istemci `generation_id` ile karar verir.

## 3. Sözleşme zinciri

| # | Üretici → Tüketici | Sözleşme | `schema_version` | Tanım | PoC'taki ilgili şema |
| --- | --- | --- | --- | --- | --- |
| C1 | Adaptör → F0 | `AudioFrame` | `f0.audio_frame.v1` | [F0 §4](../stages/F0-audio-acquisition/spec.md) | `audio_frame.metadata`, `m06_media_format` |
| C2 | F0 → F1 | `F0Output` (+ `FrameQuality`, `FrameFlags`) | `f0.output.v1` | F0 §4 | — |
| C3 | F1 → F2 | `Utterance` | `f1.utterance.v1` | [F1 §6](../stages/F1-voice-turn-detection/spec.md) | — |
| C4 | F1 → hat | `SpeechEvent`, `SpeechFrame` | `f1.speech_event.v1` | F1 §6 | `conversation_signal` |
| C5 | F2 → F3 | `ASRResult` | `f2.asr_result.v1` | [F2 §6](../stages/F2-speech-recognition/spec.md) | `nlu_diagnostics` (F3 tarafı) |
| C6 | F3 → F1, F2 | `TurnContext` | `f3.turn_context.v1` | F1 §6, [F3 §5.10](../stages/F3-dialogue-intelligence/spec.md) | — |
| C7 | F3 → F4 | `ResponsePlan`, `ResponseSegment`, `SemanticTag` | `f3.response_plan.v1` | F3 §5.10 | `policy_decision`, `booking_receipt` |
| C8 | F4 → F5 | `SynthesisPlan` | `f4.synthesis_plan.v1` | [F4 §6](../stages/F4-linguistic-frontend/spec.md) | `tts_input`, `phrase_boundary`, `clause_plan_diagnostics`, `normalization_result` |
| C9 | F5 → F6 | `AudioChunk` | `f5.audio_chunk.v1` | [F5 §6](../stages/F5-neural-synthesis/spec.md) | `m06_audio_chunk_metadata` |
| C10 | F6 → transport | `RenderedFrame` | `f6.rendered_frame.v1` | [F6 §7](../stages/F6-rendering-transport/spec.md) | `audio_frame.metadata` |
| C11 | F6 ↔ F1, istemci, PBX | `PlaybackEvent`, `PlaybackState` | `f6.playback_event.v1` | F6 §7, F1 §6 | `m06_flush_request`, `m06_flush_ack`, `m07_stream_receipt` |
| C12 | F6 → F0 | Oynatma referansı (halka tampon) | süreç içi | F6 §5.15, F0 §5.2 | — |
| C13 | Herkes → gözlem | `EventEnvelope` | mevcut `event.schema.json` | [observability](../cross-cutting/observability.md) | `event` |
| C14 | Oturum → kalıcılık | Oturum anlık görüntüsü | mevcut | [session-and-state](../cross-cutting/session-and-state.md) | `session_snapshot`, `m10_durable_snapshot` |

**PoC şemalarıyla ilişki:** Örtüşen mevcut şemalar silinmez. Yeni sözleşme ya mevcut şemanın yeni sürümüdür (`tts_input` → `f4.synthesis_plan.v1` parçası) ya da mevcut şemayı içerir (`AudioChunk` metadata'sı `m06_audio_chunk_metadata` alanlarını kapsar). Hangisinin seçildiği sözleşmenin `spec.md` bölümünde yazılır; milestone testleri (`tests/milestones/`) geçmeye devam eder.

## 4. Sözleşme özetleri

### C2 — `F0Output`
`enhanced` (16 kHz `AudioFrame`, F1'e), `raw` (giriş hızında), `quality_in` / `quality_out` (`FrameQuality`: RMS, tepe, kırpılma oranı, gürültü tabanı, SNR — kestirici hazır değilse `null`), `stage_us`, `algorithmic_delay_ms`. Bayraklar: `GAP_FILLED`, `INPUT_CLIPPED`, `DSP_BYPASSED`, `DURING_PLAYBACK`, `DTMF_MUTED`, `CALIBRATING`, `INVALID_SAMPLES`.

### C3 — `Utterance`
`utterance_id`, `session_id`, `turn_id`, `follows_turn`, örnek aralığı (pre/post-roll dahil), 16 kHz ses, birleştirilen bölümler, `end_reason` (`silence`, `semantic`, `silence_max`, `max_length`, `dtmf`, `hangup`), `continuation`, `during_playback`, `speculative_transcript`.

### C4 — `SpeechEvent`
`kind`: `onset`, `endpoint_candidate`, `continue`, `finalize`, `bargein_pause`, `bargein_resume`, `bargein_flush`, `timeout`; örnek zamanı ve algılama zamanı.

### C5 — `ASRResult`
`raw_transcript` (her zaman dolu), `normalized_transcript`, `canonical_transcript` (yalnızca listelenen `corrections` ile), `entities` (tür, değer, ham aralık, kaynak, `catalog_verified`, alternatifler), `segments`, `confidence` (kalibre edilene kadar `null`), `confidence_features`, `decision` (`ACCEPT`, `CONFIRM`, `RE_DECODE`, `REPROMPT`), `decision_basis`, `hallucination_flags`, `decode` profili, `metrics`, `status` (`partial` / `final`). **F3 `status != "final"` ile işlem başlatmaz.** Eski `models.transcribe() -> str` uyumluluk için `raw_transcript` döndürür.

### C6 — `TurnContext`
`expected_slot` (`yes_no`, `option_number`, `customer_name`, `vehicle_make_model`, `phone_number`, `plate`, `free_text`, `none`), `awaiting_confirmation`, `freya_utterance_kind` (`info`, `question`, `confirmation`, `none`), `require_year`. F3 her `ResponsePlan` ile birlikte yayımlar; F1 endpoint profilini, F2 hotword kümesi ve karar kapısını buna göre seçer.

### C7 — `ResponsePlan`
`segments[]` (`text`, `tags: SemanticTag[]` — brand/model/plate/phone/price/date/time/number aralıkları, `kind`: info/question/confirmation/safety/filler, `interruptible`, `cacheable`, `focus_entities` — odak etiketlerin indeksleri, F4 vurgusu için), `turn_context`, `source_path` (`fast`, `standard`, `knowledge`, `complex`). Metin F3 Response Validator'dan geçmiştir; F4 metni anlamca değiştirmez.

### C8 — `SynthesisPlan`
Değişmez. `plan_id`, `source_text`, `normalized_text`, `speech_act`, `lexicon_version`, `normalizer_version`, `normalization_passes = 1`, `voice_profile`, `seed`, `chunks[]` (`model_text`, `source_span`, `target_speed`, `post_pause_ms`, `emphasis_targets`, `protected_entities`, `cacheable`, `interruptible`), `warnings`, `validation`. **F5 normalize etmez, bölmez, sessizlik eklemez.**

### C9 — `AudioChunk`
Metadata + ikili 48 kHz float32 mono. `generation_id`, `plan_id`, `chunk_id`, `chunk_index`, `is_last`, `voice_profile`, `seed`, `model_revision`, `solver`, `ode_steps`, `post_pause_ms` ve `target_speed` (F4'ten aynen; **F6 uygular**), `cache_hit`, `recovery_attempts`, `metrics`, `quality_status`. Ses ham gider: fade, sessizlik, 8 kHz dönüşümü yoktur.

### C10–C11 — `RenderedFrame`, `PlaybackEvent`
Çerçeve: `generation_id`, `seq`, `chunk_id`, `sample_rate` (16000/8000), `pcm16` (640/320 B), `planned_send_ns`, `is_padding`. Olay: `PLAY`, `SOFT_PAUSE`, `RESUME`, `FLUSH`, `CANCEL`, `DRAINED`, `PLAYBACK_STARTED`, `PLAYBACK_COMPLETED`, `MARK_PROCESSED`; `source` (`server`, `browser`, `asterisk`), `position_frames`.

## 5. Barge-in komut eşlemesi

| F1 olayı | F6 `PlaybackEvent` | F5 | F3 | Web istemcisi | AudioSocket | chan_websocket |
| --- | --- | --- | --- | --- | --- | --- |
| `bargein_pause` | `SOFT_PAUSE` (konum kaydı) | Devam (kuyruk tutulur) | — | `AudioContext.suspend()` | Gönderim durur | `PAUSE_MEDIA` |
| `bargein_resume` | `RESUME` | — | — | `resume()` | Gönderim sürer | `CONTINUE_MEDIA` |
| `bargein_flush` | `FLUSH` + `CANCEL` | Kuyruktaki eski generation iptal | Yarım kalan yanıt bilgisi (hangi segmente kadar duyuldu) | Kaynaklar durdurulur | Gönderim durur; gönderilmiş ses geri alınamaz | `FLUSH_MEDIA` |

`FLUSH` sonrası `generation_id` ilerler. Transport'un flush'ı onaylaması (`m06_flush_ack.confirmed_by_adapter`) ile müşterinin sesi duymayı bırakması ayrı ölçülür (F6 K10, F1 K07).

## 6. Sürümleme

- Geriye uyumlu ekleme (yeni opsiyonel alan): aynı ana sürüm, şema güncellenir.
- Alan silme, tür veya anlam değişikliği: yeni ana sürüm (`v2`); üretici bir geçiş süresi boyunca iki sürümü de yayımlayabilir.
- Her sözleşme değişikliği ilgili aşamanın regresyon testini ve uçtan uca regresyonu (F0-S10, F1-S13, …) yeniden çalıştırır.
