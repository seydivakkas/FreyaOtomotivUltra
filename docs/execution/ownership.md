# Sahiplik ve sözleşme sınırları

> Hangi paketin hangi dizinin ve hangi kararın tek sahibi olduğu. Yollar plan önerisidir; gerçek dosya ve sembol sahipliği M00'da çıkarılan envantere göre kesinleşir. Bir dosyaya aynı anda tek yazar; paylaşılan bileşim dosyalarına (aşağıda) yalnız seri, incelenmiş ve en küçük değişiklik.

## Paket → dizin → tek yetki

| Sahip | Dizinler (PoC reposu) | Tek yetkili olduğu konu | Tüketiciler |
| --- | --- | --- | --- |
| M00 | `evidence/M00/` | Taban özellik kimlikleri, rota ve kaynak envanteri | Hepsi (salt okunur) |
| H01 | Mevcut dosyalarda en küçük düzeltmeler | Bayraktan bağımsız hata/güvenlik düzeltmeleri | Hepsi |
| M01 | `backend/core/contracts/`, `backend/core/adapters/` | Kanonik değiştirilemez iç şemalar, birimler, sürüm ve doğrulama | M02–M08, F0–F6 |
| M02 | `backend/core/runtime/` | Oturum/enkarnasyon, tur/generation kabulü, iptal, duraklatma jetonu, kaynak sahipliği | Hepsi; özellikle F1, F6, M06, M07 |
| M03 | `backend/core/configuration/`, `backend/core/model_registry/`, `config/` | Tipli ayarlar, istenen/etkin anlık görüntü, model/ses/uyarlayıcı/yetenek kaydı | M05, M06, F4, F5, F6, F5-D |
| M04 | `backend/observability/` | Olay yolu, iz ve güvenli metrikler (kalıcı iş denetimi değil) | Hepsi; kontrol bağımlılığı yok |
| M05 | `backend/shared_lexicon/`, `config/linguistics/` | Kanonik otomotiv kimlikleri, takma adlar, telaffuzlar, inceleme/revizyon | F2, F3, F4 (iş kataloğu değil) |
| M06 | `backend/runtime_resources/` | Kabul, yerleşim, sağlayıcı yürütme kirası, GPU adaleti | F2, F3, F5; F5-D özel bakım |
| M07 | `backend/supervisor/security/` + mevcut Supervisor geçit/politika noktaları | Kimlik doğrulama, onay, kalıcı talep/idempotency/makbuz/denetim | F3, F6-D (F2 son sonucu yetki değildir) |
| M08 | `tests/harness/`, `tests/fixtures/`, `tests/golden/`, `tests/integration/`, `scripts/run_gate.py` | Güvenli çalıştırıcı, fikstür protokolü, entegrasyon ve regresyon kanıtı | Hepsi |
| F0-A/B | `backend/audio_frontend/`, `backend/car_denoiser.py` | Giriş koşullandırma, ham DTMF musluğu, örnek defteri, AEC/kalite | F1, F2; F6 referansını okur |
| F1-A/B/C | `backend/voice_activity/`, `backend/audio.py` içindeki endpoint | VAD durumu, geri bakış, konuşma sınırları, söz kesme kontrolü | M02 geçiş yetkisi; F2 kısmi ipucu; F3 bağlam; F0 akustik |
| F2-A/B/C | `backend/speech_recognition/`, `experimental/asr_mapper.py` | Tek çözücü adaptörü; ham/normalize/kanonik ASR; pencere revizyonları; son karar | F1 yalnız ipucu; F3 yalnız kabul edilmiş son sonuç |
| F3-A/B/C | `backend/supervisor/dialogue/`, `backend/supervisor/knowledge/`, `backend/dialogue.py`, `backend/db.py`, `backend/caller_memory.py` | Diyalog durumu, iş akışı, doğrulanmış bilgiler, RAG, yönlendirme, sağlayıcı adaptörleri | M07 uygulayıcı; F4 anlamsal yanıt |
| F4-A/B/C | `backend/linguistic_frontend/`, `backend/text.py`, `backend/automotive_frontend.py`, `backend/normalizer_rules.py`, `backend/morphology/` | Tek normalizasyon, korumalı atomlar, G2P, prozodi, değiştirilemez plan | F5 model metni; F6 sınır kontrolleri |
| F5-A/B/C | `backend/neural_synthesis/`, `backend/batched_ode.py` | Ham model çıkarımı, öğe başı RNG, süre/önbellek/kalite, kalibre profiller | M06 yürütme; F4 kesin plan; F6 ham parça |
| F6-A/B/C/D | `backend/audio_rendering/`, `backend/media_transport/`, `backend/dsp.py`, `backend/audiosocket_server.py`, `backend/telephony.py` | Tek render, oynatma kuyruğu/imleç, gönderim çiti, kodek laboratuvarı, isteğe bağlı aktarım | F1-B kontrol; F0 referans; M07 korumalı çağrı eylemleri |
| F5-D | `backend/neural_synthesis/research/adapters/` | Ayrı araştırma; haklar, bölümler, checkpoint, değerlendirme | M03 etkinleştirme; M06 kaynak; F5-B kimlik — asla kendiliğinden canlı değil |
| Bileşim sahibi | `backend/session.py`, `backend/models.py`, herkese açık router'lar, yapılandırma/kilit dosyaları, uygulama bileşim kökü | En küçük ortak bağlama (ikinci alan sahibi değil) | Etkilenen her sahibin seri, incelenmiş yamaları |
| G3 | `frontend/` | Dört alanlı kokpit, UI rota/eylem eşlemesi | Tüm arka uç sahipleri, gerçek yetenekler ve M07 |

## Paylaşılan dosyalar (çakışma riski)

`session.py` F0–F6 ve M02'yi kapsar; `models.py` M03/M06/F2/F3/F5'i; `audio.py` VAD ve ortak dönüşümleri; `supervisor/` M07/F3'ü; `db.py` ve migration'lar M07/F3'ü; `dsp.py` ve aktarım yolları F6 ile F0 referansını. Bu dosyalara dokunan paket, değişikliği en küçük tutar ve PR açıklamasında hangi sahibin alanına dokunduğunu yazar.

## Sözleşme sınırları (üretici ve tüketici gerçek kaynakla test edilir)

| Sınır | Veri | Değişmezler / negatif kontroller | İlgili test aileleri |
| --- | --- | --- | --- |
| M00 → hepsi | Özellik kaydı ve taban soyu | Tam kimlik eşlemesi; çözülmemiş kritik özellik HOLD | M00-G00…G10; CI01, CI22, CI24; WI01, WI23, WI24 |
| M01 → M02/M04 | SessionIdentity, TurnRef, GenerationRef, StreamRef, EventEnvelope | Kapsam, monoton sıra, sahte başvuru yok, saat alanı, bayat ret, kişisel veri yok | CT, RT, OB; CI02–CI04 |
| M03 → M02/M05/M06/M07 | Değiştirilemez yapılandırma/model/ses/sözlük/yetenek revizyonları | İstenen/etkin; sabit anlık görüntü; eksik = bilinmiyor; atomik yayın; tur ortasında etkinleştirme yok | CR, LX, GPU, SEC; CI05–CI10, CI19 |
| M02 → M06 | İş kapsamı, iptal, kira | Gerçek yerel terminal; mantıksal iptal fiziksel değildir; karantina; bir kez bırakma | RT, GPU; CI11–CI13 |
| M02 → M07 | Kabul, talep, commit, uzlaştırma | Kabulden önce bayat yok; commit sonrası uzlaştırma; kalıcı denetim ayrı | RT, SEC; CI14–CI19 |
| F0 → F1 | 16 kHz mono AudioFrame, kesin kaynak/çıkış eşlemesi | Durum/hız/dönem, geçerli örnek sayısı, süreksizlik/EOS, DTMF musluğu DSP'den önce | AI, VA, AD, SC |
| F1 → F2 | Değiştirilemez sonlanmış Utterance / ön-son görünüm | Tek sahip; kesin ön/son pay; tek kabul edilmiş tur; ikinci kırpma/yeniden örnekleme yok | VA, AS, PS |
| F2-C → F1-C | Özel SpeechScopeRef, kısmi revizyon, kararlı önek, anlamsal ipucu | Aynı konuşma/dönem; kapsam; yaş/TTL; geri alınabilir önek; sahte TurnRef yok | PS, SC |
| F3 → F1/F2 | Önceki commit edilmiş beklenen slot/bağlam, sınırlı herkese açık ipuçları | Aynı kapsam, durum revizyonu, TTL; hotword bağlamında özel müşteri verisi yok | DF, AE, PS, SC |
| F0-B → F1-C/F2 | AcousticEvidence | Kalite tahmini ASR güveninden ayrı; referans kökeni; hizalama belirsizliği; yakın uç korunur | AD, SC, PS |
| F2 → F3 | Kabul edilmiş SON ASRResult | Ham korunur; adaylar ayrı; tek teslim; kısmi/kararlı/konuşmasız/hata normal iş girdisi değil | AS, AE, PS, DF, MI, RW |
| M05 → F2/F4 | Kanonik kimlik, takma ad, telaffuz, incelenmiş sürüm | Kritik değerde bulanık düzeltme yok; aday ≠ doğrulanmış katalog; Unicode aralıkları; onaysız varyant yok | LX, AE, MG, PC |
| F3 → F4 | DialogueResponse, VerifiedFactRef, ToolReceipt | Anlam/görünüm ayrımı; kesin değerler/olumsuzluk; yalnız doğrulanmış commit başarı sayılır | DF, MI, RW, LN, MG, PC |
| F4 → F5 | Değiştirilemez SynthesisPlan, ChunkPlan | Tek normalizasyon; kesin model metni; sabit revizyonlar; gerçek sözcük dağarcığı; seed 9; kontrol sahibi | LN, MG, PC, NS, RQ, OS |
| F5 → F6 | AudioChunk, yürütme/kontrol yan kaydı | 48k mono float32 LE; gerçek bayt/örnek/süre; geçersiz/bayat yok; ham (DSP'siz); uygulanan ≠ istenen hız | NS, RQ, OS, AR, DC |
| F1-B → M02 → F6-B | PauseRef, geri alma, boşaltma niyeti | Aynı generation devamı kesin gönderilmemişten; süresi dolmuş/commit edilmiş devam edemez; G/Ç üzerinde kilit yok | BI, RT, PB, SC, TD |
| F6 → F0 | DSP sonrası talep edilmiş PCM referansı | Kesin akış/generation/sıra/hız/ofset/geçerli örnek/zaman; gönderilmemiş yok; duyulur iddiası yok | PB, AD, DC, TD |
| F6 → aktarım | RenderedFrame, PlaybackEvent | Web 16k/320 örnek/640 B, telefon 8k/160 örnek/320 B (20 ms PCM16); AudioSocket uzunluğu BE, örnekler LE | AR, PB, DC, TD |
| F6-D → M07 | Korumalı originate/aktarım makbuzu | AMI kabul ≠ yanıtlandı; ARI oluşturuldu ≠ köprü/duyulur; bilinmeyen etki uzlaştırılır | TD, SEC, MI |
| F5-D → M03/F5-B/M06 | Uyarlayıcı bildirimi | Haklar; kesin taban + uyarlayıcı özeti; önbellek ad alanı; özel bakım; geri dönüş; otomatik etkinleştirme yok | LR, CR, RQ, GPU |

## Tekilleştirilmiş bileşenler

Eski planlarda birden fazla katmanda geçen bileşenler tek sahibe bağlanır; diğer paketler onu kullanır, kopyalamaz. Parantez içi kimlikler teknik ayrıntının bulunduğu eski görevlerdir ([legacy-mapping.md](legacy-mapping.md)).

| Bileşen | Geçtiği yerler | Tek sahibi | Kullananlar |
| --- | --- | --- | --- |
| Zarf tabanlı limiter | F0 §5.7, F6 §10 | `backend/dsp_common/` — F0-B (F0-T16) | F6-C (F6-T11) |
| Durumlu filtre ve yeniden örnekleyici | F0 §3/§8, F6 §7/§9 | `backend/dsp_common/` — F0-A (F0-T21) | F6-A (F6-T10, F6-T13; ADR-F6-01) |
| Türkçe sayı ayrıştırma / okuma | F2 (dört ayrıştırıcı), F4 sayı/para/tarih, `normalizer_rules.py` | F2-B (F2-T11, ayrıştırma) + F4-A (F4-T10, okuma), ortak tablo | F2, F4 |
| Otomotiv sözlüğü | F2 katalog, F4 Lexicon 2.0, üç JSON kopyası | M05 ([shared-lexicon](../cross-cutting/shared-lexicon.md)) | F2, F3, F4 |
| GPU zamanlaması | F2 çıkarım zamanlayıcı, F3 LLM, F5 zamanlayıcı, F1 spekülatif STT | M06 (`backend/runtime_resources/`) | F1, F2, F3, F5 |
| Generation / iptal | F1 söz kesme, F2 S7, F5 N5, F6 eski çerçeve | M02 (`CancellationController`) | Tüm katmanlar |
| Ön pay / geri bakış tamponu | `Endpoint.pre`, iki `LookbackBuffer` | F1-A (F1-T06 tek tampon, F1-T07 eskilerin kaldırılması) | F1, F2 |
| DTMF algılama ve tekilleştirme | F0 Goertzel, AudioSocket 0x03, F3 §5.13, F6 hata tablosu | F0-A (F0-T24) | F3, F6-A (F6-T20) |
| Tempo (pacing) | `audio.pace`, web döngüsü, `AudioPacer` | F6-A (F6-T16) | Tüm çıkış kanalları |
| Oynatma kuyruğu | `session` kuyruğu, `automotive_voice/audio/queue.MediaBuffer`, deneysel denetleyici | F6-B (F6-T17, `MediaBuffer` temelli) | F1, F5 |
| Fade / sessizlik / duraklama | F5 `_synth`, `batched_ode`, `dsp.apply_fade_and_comfort_noise`, F4 planı | F6 (F6-A taban, F6-C gelişmiş); taşıma F5-A (F4-T27, F5-T09) | — |
| Metin normalizasyonu | `text.normalize`, `AutomotiveTextNormalizer`, `automotive_voice` normalizer, `experimental/normalizer.py`, `batched_ode` | F4-A | F5 (yalnız doğrulama), SFT veri hazırlığı |
| Anlamsal tur sonu | `semantic_turn_detector.py`, F1 §7 | F1-C (F1-T15) | F1 |
| Onay sesi (backchannel) | `BACKCHANNEL_WORDS`, F1 §9 | F1-C (F1-T19) | F1 |
| Telemetri | `pipeline_telemetry`, `EventEnvelope`, pano metrikleri | M04 | Tüm katmanlar, G3 kokpiti |
| Devre kesiciler | `models.breakers`, `gpu_health_circuit_breaker` | [fault-recovery](../cross-cutting/fault-recovery.md) | F2, F3, F5, F6 |
| Konuşmacı gömüsü (speaker encoder) | F5 kimlik doğrulama, F6 WSOLA perde/kimlik kontrolü | F5-C (F5-T22) | F6-C (F6-T07) |
| Leyla referans kümesi | F5 iyileştirmeleri, F4 ADR-F4-01, F6 kimlik kontrolü | F5-A (F5-T05) | F4, F6 |
| Benchmark / Whisper geri tanıma | F2 benchmark, F4 akustik kabul, F5 Q2, F6 kodek laboratuvarı | G4 (F2-T32) | G5 (F4-T33), F5, F6-C (F6-T14) |
