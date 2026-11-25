# PoC'tan geçiş

Freya 2.0 PoC'u sıfırdan yazmaz. Bu belge, aşama `spec.md` dosyalarının "PoC'tan taşıma" bölümlerini tek yerde toplar ve sırayı belirler.

## 1. İlkeler

1. **Silme yok, sarmalama var.** Mevcut fonksiyon yeni pakete taşınır; eski adı uyumluluk sarmalayıcısı olarak kalır (ör. `models.transcribe() -> str`, `text.normalize`, `dsp.apply_telephony_eq_and_downsample_8k`). Eski ad, tüm çağıranlar yeni yola geçtikten sonra ayrı PR ile kaldırılır.
2. **Bayrak arkasında geçiş.** Yeni yol `fN_pipeline_v2` bayrağıyla seçilir; legacy yol aynı sürümde çalışmaya devam eder.
3. **Önce karakterizasyon testi.** Taşınan her modülün mevcut davranışı önce test olarak kaydedilir (her aşamanın T01'i). Davranış değişikliği bu testin gerekçeli güncellenmesiyle yapılır.
4. **Milestone paketinden yararlan.** `automotive_voice/` altında canlı yolda kullanılmayan ama tasarlanmış ve test edilmiş yapılar (çekirdek kimlikler, iptal, olay yolu, kuyruk, sahte transport, şemalar) yeni paketlerin temelidir.
5. **Tek yerde uygulama.** Birden fazla yerde yapılan iş (normalizasyon, duraklama, pacing, pre-roll, GPU kilitleri) taşınırken tekilleştirilir ([ownership.md §Tekilleştirilmiş bileşenler](../execution/ownership.md#tekilleştirilmiş-bileşenler)).

## 2. Modül eşlemesi (özet)

Ayrıntılı tablolar: [F0 §9](../stages/F0-audio-acquisition/spec.md) · [F1 §10](../stages/F1-voice-turn-detection/spec.md) · [F2 §9](../stages/F2-speech-recognition/spec.md) · [F3 §9](../stages/F3-dialogue-intelligence/spec.md) · [F4 §10](../stages/F4-linguistic-frontend/spec.md) · [F5 §11](../stages/F5-neural-synthesis/spec.md) · [F6 §11](../stages/F6-rendering-transport/spec.md)

| PoC modülü | Yeni yer | Aşama |
| --- | --- | --- |
| `backend/car_denoiser.py` | `audio_frontend/` (highpass, spectral_denoiser, gain_controller, limiter) | F0 |
| `backend/dtmf.py` | `audio_frontend` ham yol (F0-T24) | F0 |
| `backend/audio.py` (`Endpoint`, `resample`, `frames`, `pace`) | `voice_activity/` (Endpoint), `audio_rendering/` (resample, frames, pace) | F1, F6 |
| `backend/semantic_turn_detector.py` | `voice_activity/semantic_turn.py` | F1 |
| `backend/models.py` (Whisper, Silero, FreyaTTS, Ollama, kilitler) | `speech_recognition/whisper_engine.py`, `voice_activity/vad_engine.py`, `neural_synthesis/freya_engine.py`, `runtime_resources/` | F1, F2, F5, ortak |
| `experimental/asr_mapper.py` | `speech_recognition/asr_mapper.py` | F2 |
| `backend/dialogue.py` (1 827 satır) | `supervisor/` (context, slot, workflows, agents); `extract_phone_number` → F2 | F3, F2 |
| `backend/supervisor/` | Yerinde genişletilir | F3 |
| `automotive_voice/dialogue/booking_state.py` | Yerinde genişletilir | F3 |
| `backend/caller_memory.py` | `supervisor/memory/` | F3 |
| `backend/text.py`, `normalizer_rules.py`, `automotive_frontend.AutomotiveTextNormalizer`, `automotive_voice/nlp/normalizer.py`, `automotive_voice/prosody/planner.py` | `linguistic_frontend/` | F4 |
| `backend/morphological_pre_checker.py`, `backend/morphology/` | Yerinde; F4 `pipeline` çağırır | F4 |
| `config/*lexicon*.json` | `config/linguistics/automotive_lexicon.json` | F2, F4 |
| `backend/batched_ode.py`, `models._synth` | `neural_synthesis/` | F5 |
| `backend/dsp.py`, `automotive_frontend.AutomotiveDSPChain` | `audio_rendering/` | F6 |
| `backend/audiosocket_server.py`, `websocket_adapter.py` | `media_transport/` | F6 |
| `experimental/prosody_wsola_streamer.WSOLATimeStretch` | `audio_rendering/wsola.py` | F6 |
| `automotive_voice/audio/queue.MediaBuffer`, `telephony/transport.py` | `audio_rendering/playback_queue.py`, `media_transport/gateway.py` | F6 |
| `automotive_voice/core/*`, `resilience/durable.py` | `session_state/` temeli | Ortak |
| `backend/pipeline_telemetry.py` | `observability/` | Ortak |
| `backend/gpu_health_circuit_breaker.py` | `runtime_resources/memory_budget.py` girdisi | Ortak |
| `backend/session.py` | Orkestratör olarak incelir | Tümü |

## 3. Geçiş sırası

Sıra master plandaki fazları izler:

1. **Faz 0:** Karakterizasyon testleri; bayraktan bağımsız düzeltmeler legacy kodda yapılır.
2. **Faz 1:** `automotive_voice/core` canlı `Session`'a bağlanır (kimlikler ayrılır, davranış aynı); sözleşmeler ve şemalar; telemetri `EventEnvelope`'a; GPU kilitleri tek yöneticiye.
3. **Faz 2:** Sözlük birleştirme → F2 adaptörü ve resolver → F4 tek normalizasyon → **tek sentez yolu** (AIP-20: F4 plan tüketimi, F5 sessizlik eklemeyi bırakır, F6 duraklamayı uygular — birlikte).
4. **Faz 3:** F0/F1 giriş yolu, F5 çekirdeği, F6 rendering ve transport.
5. **Faz 4:** `dialogue.py` iş mantığı Supervisor'a taşınır (Shadow → Guarded, F3 spec §6).
6. **Faz 6:** Bayraklar varsayılan açılır; legacy yollar uyumluluk sarmalayıcısına indirgenir.

## 4. Taşınmayacaklar

| Öğe | Neden |
| --- | --- |
| `experimental/...ModelHashAndSeedGuard.get_conditioned_noise_seed` | Denemeye göre seed değiştiriyor; Leyla kimliği kuralına aykırı (F5) |
| `experimental/...PreOnsetRingBuffer` | Birleşik lookback tamponu yerini alır (F1) |
| `experimental/normalizer.py` | Davranışı testlerle karşılaştırılıp arşivlenir (F4) |
| F5 içindeki `normalize` / `clauses` / `prepare_tts_clause` çağrıları | Normalizasyon yalnızca F4'te |
| F5 içindeki duraklama sıfırları ve `apply_fade_and_comfort_noise` | Duraklama ve fade yalnızca F6'da |
| Yedek yoldaki seed 9 dönüşü, `except TypeError` seed düşürmeleri | N3 |
| `batched_ode.py` docstring'indeki RTX 4090 / RTF / F0 iddiaları | Ölçülmemiş (N9); kaldırılır veya "ölçülmedi" diye etiketlenir |
| Deneysel `RESUME_MEDIA` komutu | Asterisk komutu `CONTINUE_MEDIA` (F6 R8) |
| `config/freyatts_automotive_lexicon.json` kopyaları | Tek sözlük dosyası |

## 5. Korunacak testler

Her aşamanın `spec.md` dosyasındaki "Korunması gereken mevcut testler" listesi geçerlidir. Toplu kural:

- `tests/` ve `experimental/tests/` altındaki tüm testler her PR'da çalışır (`pytest -m "not llm and not gpu and not pbx"` en az).
- `tests/milestones/` testleri (M01–M11) ve `tests/milestones/test_m05_contracts.py` şema testi korunur; şema değişiklikleri sürümlenir.
- `test_voice_path_honesty.py` ölçüm dürüstlüğü kuralının testidir; hiçbir aşama bu testi gevşetmez.
