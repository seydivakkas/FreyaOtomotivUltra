# Gözlemlenebilirlik (AP10 — ortak kısım)

**Kod:** `backend/observability/`. Olay biçimi PoC'taki `EventEnvelope` (`automotive_voice/core/events.py`, `contracts/event.schema.json`) ile aynıdır.

## 1. PoC'taki durum

| Yapı | Not |
| --- | --- |
| `backend/pipeline_telemetry.make_pipeline_event` | F0–F6 olayları; canlı oturumda kullanılıyor. F6 süresi oynatma süresini içeriyor (F6 R5); barge-in metriği yanlış noktadan ölçülüyor (F1 S6) |
| `EventEnvelope` + `EventEnvelope.create` | `schema_version`, `event_id`, `event_type`, `session_id`, `turn_id`, `generation_id`, `sequence`, UTC + monotonic zaman, `payload` |
| `realtime_dashboard_metrics.py`, `qa_telemetry_operator.py`, `gpu_health_circuit_breaker.py` | Gözlem paneli ve operatör QA |
| `ab_testing.py` | Oturum başına istem/karşılama varyantı (X7) |

## 2. Olay modeli

Tüm aşama olayları `EventEnvelope` olarak yayımlanır. Mevcut `EventType` listesi genişletilir:

| Aşama | Örnek olay türleri | Önemli payload alanları |
| --- | --- | --- |
| F0 | `f0.frame_timing`, `f0.profile_changed`, `f0.quality_snapshot` | `stage_us`, `algorithmic_delay_ms`, SNR (`null` olabilir) |
| F1 | `user_speech_started`, `f1.endpoint_candidate`, `f1.finalize`, `f1.bargein` | `t_detect_ns`, `end_reason`, profil |
| F2 | `transcript_partial`, `transcript_final` | `decision`, `stt_ms`, `queue_ms`, `hotword_set`; **metin yalnızca KVKK kuralına göre** |
| F3 | `f3.route`, `f3.tool_call`, `response_started` | `source_path`, LLM kullanıldı mı, araç sonucu |
| F4 | `f4.plan_ready` | `plan_id`, `warnings`, `review_required` |
| F5 | `audio_chunk_enqueued`, `f5.recovery` | `cache_hit`, `queue_wait_ms`, `ode_ms`, `rtf`, `quality_status` |
| F6 | `playout_started`, `playout_finished`, `interrupted`, `interruption_completed` | T1–T6, `source` (server/browser/asterisk), `stale_dropped` |
| Ortak | `gpu.job`, `gpu.oom`, `session_failed` | `priority`, `wait_ms`, `run_ms`, `peak_mib` |

**Kurallar:**
- Olay yayını **bloklamaz**. `EventBus` doluysa olay düşürülür ve düşürme sayacı artar; ses yolu hiçbir zaman telemetri yüzünden beklemez.
- Kişisel veri (ad, telefon, plaka, transkript metni) olaylara yalnızca [security-and-privacy](security-and-privacy.md) kurallarına göre ve maskelenerek girer. Varsayılan: metin yok, uzunluk ve hash var (mevcut `tts_input.safe_metadata()` örneği).
- Her olay A/B varyantını (`ab_variant`) ve etkin bayrakları (`fN_pipeline_v2`) taşır; ablation ve kalite karşılaştırmaları bunsuz yapılmaz.

## 3. Gecikme profili

`latency_profiler` olay zaman damgalarından tur başına şu süreleri hesaplar ([latency-budget](../01-architecture/latency-budget.md)):

`endpoint_wait` · `stt` · `f3` · `f4` · `f5_first_chunk` · `f6_dsp` · `transport_to_playback` · **TTFA** · **içerik TTFA** · barge-in kontrol · duyulabilir kesilme

- p50/p95/p99, örnek sayısı; kanal ve yol (`source_path`) bazında.
- Tek örnek "p95" diye gösterilmez.

## 4. Ses kalitesi izleme (canlı)

| Nokta | Metrik | Kaynak |
| --- | --- | --- |
| F0 giriş/çıkış | RMS, tepe, kırpılma, gürültü tabanı, SNR | F0 Quality Analyzer |
| F2 | düşük güven oranı, `REPROMPT` oranı, sahte metin bayrakları | F2 |
| F5 | Q1 denetim sonucu, kurtarma sayısı | F5 Quality Guard |
| F6 çıkış | tepe, limiter kazanç düşürmesi, underrun, gönderim sapması | F6 |

Canlı izleme alarm üretir, karar vermez. Ayrıntılı değerlendirme (MOS, WER, speaker similarity) laboratuvardadır ([measurement-plan](../testing/measurement-plan.md)).

## 5. Studio veri kaynağı

Yedi aşama Studio sayfası aynı olay akışını (WebSocket) ve aynı REST uçlarının biçimini kullanır. Ortak kurallar:
- Simülasyon, mock veya demo veri **etiketli** gösterilir.
- AMI/SIP "bağlı" durumu yalnızca gerçek bağlantıyla gösterilir.
- Studio değerleri ölçüm raporu yerine geçmez; kabul kanıtı `data/<aşama>/lab-report-*.json` dosyasıdır.

## 6. Görevler

| Görev | İçerik |
| --- | --- |
| CC-T03 | `backend/observability/` + `pipeline_telemetry`'nin `EventEnvelope`'a taşınması (eski fonksiyon sarmalayıcı) |
| CC-T04 | Gecikme profili ve p50/p95/p99 raporu |
| F0-T26, F1-T22, F2-T28, F3-T34, F4-T29, F5-T27, F6-T23 | Aşama telemetrisi bu modeli kullanır |
