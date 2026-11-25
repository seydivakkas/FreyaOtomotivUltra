# M01 — Çekirdek veri sözleşmeleri

> Aşamalar arasında taşınan verinin biçimini kesinleştirir: sürümlü, tipli, değiştirilemez üst veri; açık birimler; "bilinmiyor" durumları; doğrulanmış ikili ses yükü sınırları ve eski koda uyum adaptörleri. Hiçbir algoritma uygulamaz, hiçbir genel API'yi değiştirmez.

| Alan | Değer |
| --- | --- |
| Kimlik | M01 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M00, H01 |
| Sonraki | M02, M03, M04, M05, M07, M08, CORE_GATE, F0-A |
| Bayrak | Yok — yeni türler yalnızca yeni testlerde ve dar, pasif dönüşüm noktalarında kullanılır; canlı yol değişmez |
| Ortam | CPU |
| Eski görevler | F0-T04, F1-T04, F2-T04, F3-T06, F4-T06, F5-T06, F6-T04 |
| Kaynak | Bundle `W1/Freya_2_0_M01_Agent_Implementation_Package.md`; [interfaces.md](../../../01-architecture/interfaces.md) |
| Durum | NOT_RUN |

## 1. Amaç

M02–M08 ve F0–F6 uygulanmadan önce verinin temsilini belirsizlikten kurtarmak. Her sınır için **tek bir kanonik tanım** olur; mevcut eşdeğer türler (ör. `backend/supervisor/contracts.py`, `backend/morphology/contracts.py`) kopyalanmaz, yeniden kullanılır veya açık eşlemeyle sarılır.

## 2. Başlamadan önce

- [ ] M00 kanıtı kabul edilmiş: `evidence/M00/<run_id>/` içinde `M01_HANDOFF.md`, `FEATURE_REGISTRY.json`, `REGRESSION_MATRIX.csv`, `API_INVENTORY.json`, `PIPELINE_TRACE.md`, `ACCEPTANCE_MATRIX.json` (genel PASS, `m01_ready: true`).
- [ ] H01 birleştirilmiş; test paketi torch/Ollama olmadan çalışıyor.
- [ ] Birden fazla M00 çalıştırması varsa hangisinin kabul edildiği belli (belli değilse HOLD).
- [ ] Mevcut Python sürümü, dataclass/Pydantic kullanımı ve test düzeni M00'dan okunmuş; **yeni bağımlılık kurulmaz**.
- [ ] [interfaces.md](../../../01-architecture/interfaces.md) okunmuş; §7'deki paket planı ad eşlemesi biliniyor.

## 3. Kapsam

**Yapılacak:** Ortak kimlik/sürüm/zaman türleri; ses biçimi ve yük sınırı; konuşma, tanıma, diyalog, işlem makbuzu, sentez planı, ses parçası ve oynatma sözleşmeleri; saf (yan etkisiz) doğrulayıcılar; güvenli serileştirme; eski koda uyum adaptörleri; şema belgeleri ve testler.

**Yapılmayacak:** F0–F6 algoritmaları; olay yolu, GPU zamanlayıcı, oturum çalışma zamanı, sözlük, kodek, ORM, gerçek işlem, saklama motoru, arayüz ekranı (bunlar M02–M08'in işidir). Genel HTTP/WS yanıtlarına `schema_version` eklemek, metin serileştirmesini veya WS çerçevelemesini değiştirmek. Bağımlılık dosyası, kilit dosyası, model dosyası, DB göçü değişikliği.

## 4. Dosyalar

Önerilen düzen (M00 bulgularına göre uyarlanır; mevcut bir `core` modülünün üzerine yazılmaz):

```
backend/core/__init__.py
backend/core/contracts/{__init__,common,audio,speech,recognition,dialogue,synthesis,playback,validation,serialization}.py
backend/core/adapters/{__init__,legacy_audio,legacy_asr,legacy_dialogue,legacy_synthesis,legacy_playback}.py
contracts/                     # mevcut JSON Schema klasörü — yeni şemalar buraya
tests/contracts/               # M00'da bulunan gerçek test konumu
evidence/M01/<run_id>/
```

Mevcut dosyalara dokunmak yalnızca dar, eklemeli bir yeniden dışa aktarma veya pasif dönüşüm noktası için ve önceden değişiklik listesine yazılarak yapılır. Tercih: mevcut çalışma zamanı modüllerinde **sıfır değişiklik**.

## 5. Tasarım ve sözleşmeler

Alan adlarının ve sözleşme kimliklerinin (C1–C15) kesin listesi [interfaces.md](../../../01-architecture/interfaces.md)'dedir. Bu bölüm, M01'in o sözleşmeleri kodlarken uyacağı **anlamsal kuralları** verir. interfaces.md ile kod arasında çelişki çıkarsa önce plan reposunda interfaces.md güncellenir (ayrı PR), sonra kod.

### 5.1 Değişmez kurallar

1. M00'daki her özellik kimliği ve regresyon yükümlülüğü korunur.
2. Her sınır için tek kanonik tanım. Mevcut eşdeğer tür varsa yeniden kullanılır veya adaptörle sarılır.
3. Çekirdek sözleşme modüllerini içe aktarmak **hiçbir şey başlatmaz**: CUDA, Ollama, Whisper, FreyaTTS, ağ, veritabanı, iş parçacığı yok. Çekirdek, üst katmanları içe aktarmaz. Küresel monkey-patch yok.
4. Üst veri **derinlemesine** değiştirilemez (iç içe koleksiyonlar dahil: tuple / frozen kayıtlar). İkili yükün sahipliği açıktır: varsayılan değiştirilemez `bytes`; ölçülmüş ihtiyaç varsa belgeli salt-okunur tampon adaptörü. 20 ms'lik sıcak yolda gereksiz kopya zorlanmaz; kopyalama davranışı belgelenir.
5. Sözleşme kümesi sürümü `ContractVersion` ile taşınır (başlangıç `2.0`); her nesnenin `schema_version` dizgisi interfaces.md §1 biçimindedir ([§7](../../../01-architecture/interfaces.md#7-paket-planı-ad-eşlemesi-freya-20)). Sürümler genel API sürümünden, model ve sözlük sürümlerinden bağımsızdır. Bilinmeyen ana sürüm reddedilir. Güvenlik alanlarında, boolean'larda, sayısal dizgilerde ve geçersiz enum'larda örtük dönüştürme yoktur. Sessiz kırpma yoktur.
6. Kimlikler opak ve kapsamlıdır. M01 biçimi ve tutarlılığı doğrular; zaman içinde benzersizliği, generation tahsisini ve iptali **M02** yapar. Eksik kimlik asla sessizce `0` veya uydurma bir kimlik olmaz.
7. Ses biçimi ve zaman açıktır. "Örnek" kanal başına çerçeve demektir; bayt uzunluğu = örnek sayısı × kanal × örnek başına bayt. PCM16 her zaman işaretli little-endian; Float32 sınırı açıkça `f32le`. Hedefler: F0 çıkışı 16 kHz mono; F5 çıkışı 48 kHz mono float32; F6 web 16 kHz / AudioSocket 8 kHz PCM16. 32 ms VAD penceresi 20 ms aktarım çerçevesi değildir. M01'de yeniden örnekleme veya kodek dönüşümü yoktur.
8. Ölçülmemiş = `null` + neden; `0`, `false`, boş dizgi veya uydurma olasılık değildir. Sıfır geçerli bir ölçümdür. JSON'da ve doğrulanan sayılarda NaN/Inf reddedilir. Aralık dışı güven sessizce kırpılmaz. Ham log-olasılık kalibre olasılık değildir. Testleri geçirmek için sıfır dalga biçimi eklenmez.
9. Kısmi/kararlı ASR sonucu dış yazma işlemi başlatamaz; son (final) sonuç gereklidir ama yeterli değildir. `ToolReceipt` durumu `UNKNOWN/PENDING/FAILED/BLOCKED` başarı değildir. Sözleşme kuralları gerçek yetki, duruma bağlı onay, işlem, idempotency ve makbuz doğrulamasının yerini tutmaz (M07/F3). Model çıktıları güvenilmeyen öneridir. `authorized=true` gibi politikayı atlayan varsayılan yoktur.
10. Ham transkript, normalize transkript, kanonik aday, kullanıcı onaylı bilgi, görüntülenen metin ve TTS model metni **ayrı temsillerdir**. Ham veri ve kaynak aralıkları korunur; çift normalizasyon yoktur. `SynthesisPlan`'ın sahibi F4'tür; kurtarma yeni revizyon üretir, eski planı değiştirmez. Duraklama, fade ve son rendering F6'nındır; planlanan prozodi "uygulandı" anlamına gelmez.
11. Seed 9 (Leyla) eski davranışın varsayılanıdır; açık deney seed'i (42/77/123) değiştirilmez; seed'den konuşmacı kimliği çıkarılmaz. İstenen ve gerçekleşen ayarlar ayrı tutulur. Sessiz seed değişimi yoktur.
12. `monotonic_ns` süreç/makine kapsamlıdır; farklı makinelerin saatleri birbirinden çıkarılmaz. Duvar saati için saat dilimli UTC. Süre alanları birim sonekiyle (`_ms`, `_ns`). Ses örnek ofsetleri akışa ve biçim dönemine (format epoch) bağlıdır. Oynatma makbuzları gözlem kapsamını ayırır: `SERVER`, `CLIENT`, `PBX`, `ENDPOINT`; sunucuda boşaltma "uçta sessizlik" demek değildir.
13. İkili yük genel bir JSON alanı değildir. Günlüklere giden serileştirme bir **izin listesi** izdüşümüdür: tür/sürüm, opak kimlikler, hassas olmayan durum, sayısal metrikler, biçim/uzunluk, kodlar. Ham/normalize/kanonik transkript, özel varlıklar, müşteri kimlikleri, araç girdi/çıktıları, ikili yük, model yolları dışarıda kalır. Özel kayıtlarda genel `asdict()`/`model_dump()` ile günlükleme yok; `repr` güvenlidir.
14. Varsayılan davranış eski davranıştır. Yeni türler yalnızca yeni testlerde veya incelenmiş dar pasif noktalarda kullanılır. Yeni bir hat veya rota otomatik açılmaz.

### 5.2 Ortak kimlik, sürüm, hata ve zaman

| Tür | Kural |
| --- | --- |
| `ContractVersion` | İç ana/alt sürüm, başlangıç `2.0`; açık ayrıştırıcı ve politika |
| `SessionIdentity` | Boş olmayan opak `session_id`; `trace_id` yalnızca eski eşlemede açıkça yok olabilir; telefon numarası veya ad kimlik olarak kullanılmaz |
| `TurnRef` | `session_id` + negatif olmayan `turn_id` (tanımlıysa); bool reddedilir; yalnız oturum düzeyi olayda `null` |
| `GenerationRef` | `TurnRef` + `generation_id`; F5/F6 çıktısında zorunlu; adaptörde uydurulmaz |
| `StreamRef` | `session_id`, `stream_id`, yön, `format_epoch`; örnek ofsetinin başlangıcı akış/dönem başına |
| `EventEnvelope` | `schema_version`, `event_type`, `session_id`, `trace_id`, `turn_id` (oturum olayında null), `generation_id` (uygun değilse null), `sequence`, `monotonic_ns`, `clock_domain`, isteğe bağlı UTC zaman, üretici; varsayılan olarak yük içermez |
| `CancellationReference` | Kapsamlı generation başvurusu ve neden; değiştirilebilir jeton, iş parçacığı veya `cancel()` yok (gerçek jeton M02'de) |
| `ErrorInfo` | Kararlı kod, kategori, yeniden deneme sınıfı (bilinmiyorsa `UNKNOWN`), güvenli açıklama; ham istisna, kişisel veri, kimlik bilgisi yok; kör yazma yeniden denemesi yok |
| `MetricSample` | Ad, değer (sonlu veya null), birim, gözlem kapsamı, durum, neden, kaynak; yüzde/oran belirsizliği yok |
| `CapabilityDescriptor` | `declared` / `verified` / `unsupported` / `unknown`, sürüm, kanıt; istenen ve etkin yetenek ayrımı (kayıt M03'te) |

Monoton saat için tam sayı nanosaniye, ses için tam sayı örnek ofseti. `sequence` üretici/akış kapsamlıdır, küresel saat değildir. Eski kodda bulunmayan üst veri bilinmiyor olarak kalır; zorunlu alanı olan katı bir nesne uydurma kimlik/zamanla oluşturulamaz — dönüşüm, eksik alanları bildiren bir sonuç nesnesi döndürür. Olaylar test fikstürü dışında `monotonic_ns=0` ile oluşturulmaz.

### 5.3 Ses biçimi ve `AudioFrame` (F0 → F1)

```
AudioFormat:  sample_rate_hz (>0), channels (>0), encoding: PCM_S16LE | FLOAT32_LE
AudioFrame:   schema_version, stream_ref, sequence, format, sample_count (veri çerçevesinde >0),
              sample_offset, captured_monotonic_ns (gerçekten yoksa null), clock_domain,
              payload (değiştirilemez bytes veya belgeli sahipli tampon),
              valid_sample_count (yalnız açık son dolgu için), flags (discontinuity, final_frame)
```

Doğrulama: bilinen kodlama genişliği; tam yük uzunluğu; tek bayt sayılı PCM16 yok; taşma/güvensiz bellek ayırma yok; float32'de sonlu değerler; boş veri yalnızca ayrı tipli kontrol/EOS olayında; `valid_sample_count ≤ sample_count`; katı profilde bilinmeyen kanal/hız örtük dönüştürülmez, reddedilir. Her giriş çerçevesi 20 ms olmak zorunda değildir. Örnek hesaplar: AudioSocket 8 kHz PCM16 20 ms = 160 örnek / 320 bayt; web 16 kHz PCM16 20 ms = 320 örnek / 640 bayt; F1 VAD 16 kHz'te 512 örnek = 32 ms. `repr` ikili veriyi göstermez; günlük ve fikstürlerde ses base64'lenmez.

### 5.4 `SpeechEvent` ve `Utterance` (F1 → F2, F1 → F5/F6)

| Alan | Kural |
| --- | --- |
| zarf | İlgili oturum/tur/generation; söz kesme komutu gerçek generation'ı hedefler |
| `kind` | `SPEECH_CANDIDATE`, `SPEECH_START`, `SPEECH_END`, `UTTERANCE_FINALIZED`, `SOFT_PAUSE`, `RESUME`, `COMMIT_INTERRUPT` veya açıkça eşlenmiş gözlenen eşdeğeri |
| `stream_id` / `sample_offset` | Negatif olmayan, akışa göre konum; biçim dönemi ve saat alanı |
| `vad_score` | Varsa [0,1] sonlu, yoksa null; kalibre güven sayılmaz |
| `reason` | Açık kod veya `UNKNOWN` (zaman aşımı, azami süre, iptal dahil) |
| `utterance_id` | Boş olmayan opak kimlik |
| `start_sample` / `end_sample_exclusive` | Sıralı yarı açık aralık; aynı akış/dönem; boşluklar açıkça belirtilir |
| `finalized`, `finalization_reason` | Açık durum; tamamlanmış sözde neden zorunlu |
| `frame_refs` | Sıralı değiştirilemez koleksiyon veya doğrulanmış yük tutamacı |

Ön/son kayıt (pre/post-roll) üst verisi, istenen süre ile gerçekte eklenen örnekleri ayırır. M01 tamponları birleştirmez, eşik ayarlamaz, VAD uygulamaz. F1 karar sözlüğü ile F6 oynatma olay sözlüğü ilişkilidir ama birbirinin yerine kullanılmaz.

### 5.5 `ASRResult` ve `EntityCandidate` (F2 → F1/F3)

```
ASRResult:  zarf, utterance_id, revision (≥0), status: PARTIAL | STABLE_PREFIX | FINAL,
            language (gerçek dil etiketi veya null), raw_transcript, normalized_transcript (null olabilir),
            canonical_transcript (aday; kullanıcı onaylı gerçek değil), stable_prefix, segments,
            entities: [EntityCandidate], confidence: ConfidenceEstimate | null,
            outcome: OK | NO_SPEECH | REJECTED | ERROR | UNKNOWN,
            requires_confirmation (bilinmiyor → işlem yetkisi vermez), error, metrics
EntityCandidate: entity_id, entity_type, raw_value, canonical_value (null olabilir),
            source_span (yarı açık, Unicode kod noktası, temsil = RAW veya beyan edilen kaynak),
            score + score_kind + scorer_revision, alternatives,
            catalog_status: VERIFIED | NOT_FOUND | UNVERIFIED | NOT_APPLICABLE,
            confirmation_status: CANDIDATE | CONFIRMED | REJECTED | UNKNOWN
```

`ConfidenceEstimate` şunları ayırır: ham `avg_logprob` ([0,1] olasılık değildir), `no_speech_prob` (model puanı), aday sıralama puanı ve kalibrasyon sürümü/kanıtıyla birlikte kalibre olasılık. Evrensel güven eşiği burada tanımlanmaz. Kelime zaman damgaları açık başlangıç ve birimle. Varlık aralıkları beyan edilen metin temsiline işaret eder. Doğrulayıcılar ASR düzeltmesi yapmaz. Boş ham transkript `NO_SPEECH` olarak meşru olabilir ama başarılı transkript sayılmaz.

### 5.6 `DialogueResponse` ve `ToolReceipt` (F3 → F4)

Önce mevcut Supervisor sözleşmeleri, geçidi, politikası ve makbuz anlamları incelenir; uyumluysa mevcut makbuz kimliği ve durumu yeniden kullanılır. Doğrulanmış işlem kanıtı olmayan eski bir `success` boolean'ı yalnızca eski gidiş-dönüş için korunur; iç durum `UNKNOWN` olur. Sahte (mock) durum asla gerçek işleme yükseltilmez.

| Sözleşme | Gerekli bilgi |
| --- | --- |
| `DialogueResponse` | zarf, `response_id`, `display_text` (isteğe bağlı), `speech_text`, `speech_act`, `segments` (anlamsal etiketli; interfaces.md C7), odak varlık başvuruları, doğrulanmış bilgi başvuruları, `state_revision`, `source_asr_revision`, `tool_receipt_refs`, sonuç, hata |
| `VerifiedFactRef` | Kaynak (katalog / onaylı slot / araç / belge), başvuru kimliği, durum, revizyon |
| `ConfirmationReference` | `state_revision`, işlem/yük parmak izi, onay kaynağı kimliği, isteğe bağlı son geçerlilik; gerçek yetkilendirici veya kimlik bilgisi yok |
| `ToolReceipt` | `operation_id`, `tool_id`, `idempotency_key` (eskide yoksa açıkça yok), `status`: `PENDING / COMMITTED / FAILED / UNKNOWN / BLOCKED`, `provider_mode`: `MOCK / REAL / UNKNOWN`, kanıt, güvenli sonuç alanları, hata |

Onay, işlem içeriğine ve durum revizyonuna bağlıdır; karşılaştırmayı M07 yapar. `UNKNOWN` sonuç kör yeniden deneme değil uzlaştırma gerektirir. `COMMITTED` gerçek işlem kanıtı ister; sentetik kipte sahte işlem commit olabilir ama asla `REAL` sayılmaz. Fikstürlerde açıkça sentetik olmayan fiyat, randevu kimliği, müşteri bilgisi uydurulmaz.

### 5.7 `SynthesisPlan` ve `ChunkPlan` (F4 → F5/F6)

```
SynthesisPlan: schema_version, generation_ref, plan_id, plan_revision, response_id,
               source_text, normalized_text, language, voice_profile, seed,
               model_revision | null, lexicon_revision | null, capability_revision | null,
               normalization_passes (eskide null olabilir; yeni katı yolda tam 1),
               speech_act, chunks: tuple[ChunkPlan], validation_status, warnings
ChunkPlan:     chunk_id, chunk_index, model_text, source_span veya açık eşleme,
               protected_entity_refs, requested_speed (null veya sonlu pozitif oran),
               requested_emphasis, post_pause_ms (null veya ≥0), requested_controls (yetenek etiketli)
```

Plan ve iç parçalar oluşturulduktan sonra değiştirilemez. Kesinleşmiş planda benzersiz ve ardışık parça sıraları, benzersiz kimlikler, konuşma parçasında boş olmayan model metni, negatif duraklama veya sonlu olmayan hız yok. Korumalı öbek, açık "çözülemedi/desteklenmiyor" durumu olmadan parçalara bölünemez. Model sözcük dağarcığı geçerliliği ve prozodinin gerçekleşmesi F4/F5 doğrulamasına kadar `UNKNOWN`'dur.

### 5.8 `AudioChunk` (F5 → F6)

| Alan | Kural |
| --- | --- |
| `generation_ref`, `plan_id`, `plan_revision` | Katı yolda zorunlu; `SynthesisPlan` ile aynı oturum/tur/generation |
| `chunk_id`, `chunk_index` | İstenen parçayla eşleşir |
| `format`, `sample_count`, `payload` | Hedef 48 kHz mono `FLOAT32_LE`, değişken süre, doğrulanmış bayt sayısı |
| `actual_duration_ms` | Örnek sayısından türetilir; istenen süre değildir |
| `voice_profile`, `seed` | Gerçek değerler; izinsiz değişim yok |
| `model_revision`, `solver`, `ode_steps` | İstenen ve etkin ayarlar; eskide bilinmiyor olabilir; adım varsa pozitif |
| `cache_status` | `HIT / MISS / BYPASS / UNKNOWN` |
| `quality_status` | `PENDING / PASS / FAIL / UNKNOWN`; PASS gerçek dünya ses kalitesini kanıtlamaz |
| `post_pause_ms`, prozodi ipuçları | Plandan aktarılır; F5 eklemez |
| `metrics` | Kuyruk/çıkarım/kod çözücü/denetim süresi, RTF; kaynak ve birimle; yoksa null |

Sıfır olmayan dalga biçimi kalite kanıtı değildir. M01'de fade, konfor gürültüsü, yeniden örnekleme, adım ayarı, yeniden deneme veya önbellek yoktur; yalnızca plan–parça tutarlılık doğrulayıcısı (saf fonksiyon).

### 5.9 `RenderedFrame` ve `PlaybackEvent` (F6)

| Tür / alan | Kural |
| --- | --- |
| `RenderedFrame` | `generation_ref`, `stream_ref`, `sequence`, `sample_offset`, kanal profili, biçim, `frame_duration_ms`, `sample_count`, `valid_sample_count`, sahipli yük, son çerçeve bayrağı |
| Profil | `WEB` PCM16 16 kHz / `AUDIOSOCKET` PCM16 8 kHz, hedef 20 ms; gelecekteki biçimler yetenekle açılır |
| `PlaybackEvent` | zarf, olay türü, `generation_ref`, `observation_scope`, `queue_depth` (null olabilir), örnek ilerlemesi (null olabilir), zaman/saat alanı, hata/neden |
| Olay türleri | `QUEUED`, `PLAYBACK_STARTED`, `PAUSE_REQUESTED`, `PAUSED`, `RESUMED`, `FLUSH_REQUESTED`, `FLUSHED`, `DRAINED`, `COMPLETED`, `CANCELED`, `FAILED`; eski olaylar yeniden yorumlanmadan eşlenir |
| Gözlem kapsamı | `SERVER`, `CLIENT`, `PBX`, `ENDPOINT`, `UNKNOWN`; "komut kabul edildi" ile "etki gözlendi" ayrıdır |

İkili aktarım (AudioSocket başlığı, little-endian PCM, web protokolü) değişmez. DTMF verisi ses çerçevesinden ayrıdır ve ham yolu korunur.

### 5.10 Sürüm, hata ve uyum politikası

- Tek iç sürüm `2.0`; spekülatif sürümler arası göç yok. Alt sürüm eklemeleri belgeli uyumlu okuyucu kurallarıyla (bilinmeyen isteğe bağlı alanlar, güvenli ayrıştırma). Katı çekirdek/güvenlik kayıtları beklenmeyen alanı varsayılan olarak reddeder. Bilinmeyen alan hiçbir zaman yazma/yetki anlamını değiştirmez.
- Dönüşümler varsayılan uydurma üst veri yerine sonuç nesnesi döndürür: `value`, `missing_fields`, `warnings`, `error`, `lossy`, `source_ref`. İstisna yutulmaz, alan sessizce düşürülmez. Eski genel yanıtların alan atlama/`null` farkı, enum yazımları, sayı türleri, anahtarlar, kodlama, istisnalar ve durum kodları korunur.
- Girdi doğrulama hataları çalışma hatalarından ayrıdır. Hata mesajlarında ham metin/ses/gizli bilgi yoktur.
- JSON fikstürleri UTF-8, belirli anahtar düzeni, NaN/Infinity yok, `null` ile "alan yok" ayrımı açık. Pydantic varsa şema uygulamadan türetilir ve sapma testi yapılır; dataclass ise el ile tutulan şema testle korunur.

### 5.11 Eski koda uyum eşlemesi

| Sınır | İncelenecek (M00'dan doğrula) | Adaptör davranışı | Yasak |
| --- | --- | --- | --- |
| F0/F1 | `audio.py`, `car_denoiser.py`, `session.py`, AudioSocket girişi | Gerçek ndarray/bytes/PCM → `AudioFrame`, gerçek biçim ve ofsetle veya eksik üst veriyi açıkça bildirerek | Yeniden örnekleme, DTMF dalını değiştirme, DSP'yi değiştirme |
| F1/F2 | `audio.py`, `session.py` endpoint akışı | Mevcut söz ve konuşma üst verisi → `Utterance`; özgün dalga biçimi ve zamanlama korunur | VAD ayarı, model sıfırlama, endpoint değişikliği |
| F2/F3 | `models.py`, `dialogue.py`, supervisor | Mevcut dizgi veya yapılı sonuç → `ASRResult`; ham metin korunur; güven yoksa bilinmiyor | Beam/hotword değişikliği, otomatik düzeltme, gerçekte final değilse FINAL'e zorlama |
| F3/F4 | `dialogue.py`, `supervisor/contracts.py`, geçit/çalışma zamanı | Eski yanıt ve makbuz yeniden kullanılır; tüm genel alanlar korunur | Araç çalıştırma, sahte doğrulanmış makbuz, iş akışı tasarımı |
| F4/F5 | `text.py`, `automotive_frontend.py`, morphology, `models.py` | Mevcut hazırlanmış metin/parçalar → `SynthesisPlan` (köken yeterliyse), değilse açık eksik/kayıplı sonuç | İki kez normalize etme, duraklamanın uygulandığını varsayma, desteklenmeyen fonem ekleme |
| F5/F6 | `models.py`, `batched_ode.py`, `session.py` | Ham ses/biçim dönüşümü; bilinen seed/model/generation; eskiden DSP işlenmiş çıktıyı "ham F5" diye adlandırmama | Model yükleme/çıkarım, mevcut fade'i kaldırma, sesi yeniden işleme |
| F6/istemci/PBX | `dsp.py`, `audiosocket_server.py`, `telephony.py`, tarayıcı protokolü | Gerçek biçimi doğrula, mevcut olayları kapsamlarıyla eşle; tel biçimi değişmez | Gerçek arama, protokol değişikliği, uçta oynatma iddiası |

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M01.01 | M00 ön kontrolü | Kabul edilmiş taban başvurusu; taban ile güncel durum farkı; ilk Git anlık görüntüsü. | `M01_READY` veya HOLD kaydı |
| M01.02 | Mevcut tür ve sınır denetimi | Gerçek üretici/tüketici imzaları, mevcut türler ve alanlar, senkron/asenkron, birimler, genel/iç ayrımı, eşdeğer sözleşmeler, özellik kimlikleri. | Yeniden kullan / adaptör kararları yazılı |
| M01.03 | Değişiklik kapsamı ve uyum tasarımı | İzinli yollar ve sahiplik; uyum eşlemesi; değiştirilemezlik; sürüm politikası; korunacak taban testleri; kararlar. interfaces.md ile farklar varsa plan reposuna ayrı PR. | `CHANGE_SCOPE.json`, `CONTRACT_DECISIONS.md` |
| M01.04 | Ortak temel | Sürüm türü, kimlik/başvuru türleri, `EventEnvelope`, `ErrorInfo`, `MetricSample`, `CapabilityDescriptor`, ortak doğrulama; yan etkisiz içe aktarma. | §5.2 türleri + testler |
| M01.05 | Ses biçimi ve ikili sınır | `AudioFormat`, sahipli yük temsili, `AudioFrame`; bayt/örnek kontrolleri, akış/ofset, son çerçeve politikası; eski ses dönüşümü. | §5.3 + CT06–CT11 |
| M01.06 | Konuşma sözleşmeleri | `SpeechEvent`, `Utterance`; örnek aralığı, isteğe bağlı VAD puanı, sonlandırma nedeni, sıralı başvurular; söz kesme kararları yalnız üst veri. | §5.4 + CT12–CT13 |
| M01.07 | Tanıma sözleşmeleri | `ASRResult`, revizyonlar ve durumlar, aralıklar, varlık adayları, güven türü/kaynağı; final ile kısmi ayrımı; ham metin korunur. | §5.5 + CT14–CT18 |
| M01.08 | Diyalog ve işlem sözleşmeleri | Mevcut Supervisor türlerini yeniden kullan/sar; `DialogueResponse`, onaylı bilgiler, `ToolReceipt`, onay başvurusu; bilinmeyen/başarısız başarı değil; gerçek araç çağrısı yok. | §5.6 + CT19–CT20 |
| M01.09 | Dilbilim sözleşmeleri | Değiştirilemez `SynthesisPlan` ve `ChunkPlan`; kaynak/normalize/model metni ayrımı; korumalı öbekler, revizyonlar, istenen prozodi, model yetenekleri. | §5.7 + CT21–CT23 |
| M01.10 | Sentez sözleşmeleri | `AudioChunk`, generation, parça sırası, F5 biçimi, seed/model/çözücü/önbellek/kalite üst verisi; rendering veya çıkarım yok. | §5.8 + CT24–CT26 |
| M01.11 | Oynatma ve aktarım sözleşmeleri | `RenderedFrame`, `PlaybackEvent`, gözlem kapsamı, çerçeve/yük bütünlüğü, duraklat/devam/boşalt/tükendi ayrımı; protokol değişmez. | §5.9 + CT27–CT28 |
| M01.12 | Eski adaptörler ve genel uyum | Gerçek M00 sınırları için saf dönüşümler; açık bilinmeyen değerler; yalnızca belgeli birim dönüşümleri; eski dönüş biçimleri ve hatalar sabit; sahte üst veri yok. | §5.11 + CT31–CT32 |
| M01.13 | Serileştirme ve belgeler | Sürümlü üst veri şemaları (`contracts/`), güvenli günlük izdüşümü, gidiş-dönüş fikstürleri, uyum/göç tablosu, sentetik olarak işaretli örnekler. | CT29–CT30, CT34 |
| M01.14 | Birim ve sözleşme testleri | Olumlu/olumsuz, değişim, iç içe sahiplik, JSON, ikili, sürüm, kimlik ve eski gidiş-dönüş testleri; güvenli fikstürler; gerçek komut ve günlük. | CT01–CT36 çalıştırılmış |
| M01.15 | Regresyon ve kaynak bütünlüğü | İncelenmiş mevcut güvenli testleri yalıtılmış çalıştır; taban özellik/API/arayüz biçimleri ve çalışma ağacı değişiklikleri karşılaştır; gizli değişiklik yok. | CT35–CT36 |
| M01.16 | Kabul ve M02 devri | M01-G00…G12, özet, açık sorular, geri dönüş talimatı, M02 hazır olma durumu; M01'den sonra dur. | `decision.json`, `M02_HANDOFF.md` |

## 7. Testler

Fikstürler sentetik ve belirlenimcidir (ör. `test-session-a`, kısa sessizlik baytı). "Nisan kaş kay iki bin yirmi" gibi örnekler sentetik dizgidir, gözlenmiş model çıktısı değildir.

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| CT01 | Çekirdeğin yalıtılmış ortamda içe aktarılması | Model/GPU/ağ/DB/iş parçacığı başlatılmaz |
| CT02 | Sürüm 2.0 ayrıştırma ve gidiş-dönüş | İç sürüm tutarlı; bozuk veya desteklenmeyen sürüm reddedilir |
| CT03 | Kimlikler ve katı tam sayılar | Boş kimlik, negatif sıra, int yerine bool, sayısal dizgi (katı alanlarda) reddedilir |
| CT04 | İsteğe bağlı metrik | `null` sıfırdan ayrı; NaN/Inf reddedilir; bilinmiyor nedeni korunur |
| CT05 | Zaman damgası ve saat alanı | UTC saat dilimi doğrulanır; monoton alan zorunlu; alanlar arası süre hesaplanmaz |
| CT06 | PCM 8 kHz 20 ms | 160 örnek, 320 bayt, kesin biçim |
| CT07 | PCM 16 kHz 20 ms | 320 örnek, 640 bayt |
| CT08 | VAD 32 ms | 16 kHz'te 512 örnek; her girişin 20 ms olduğu varsayılmaz |
| CT09 | Float32 48 kHz | Değişken parça, örnek başına 4 bayt; sonlu değerler |
| CT10 | Bozuk yük | Yanlış bayt sayısı, tek uzunluklu PCM, hatalı kanal/kodlama, geçersiz son dolgu reddedilir |
| CT11 | Tampon sahipliği | Dönüşümden sonra kaynağı değiştirmek sonucu etkilemez; `repr` yük göstermez |
| CT12 | Söz aralığı ve boşluk | Yarı açık aralık, sıra ve açık süreksizlik; geçersiz sınırlar reddedilir |
| CT13 | Konuşma/söz kesme hedefi | Açık başvurular karşılaştırılırken yanlış oturum/generation reddedilir; çalışma zamanı iptal iddiası yok |
| CT14 | ASR kısmi/kararlı | Durum ve ham metin korunur; yazma işlemine uygun değil |
| CT15 | ASR final, konuşma yok, hata | Final otomatik onaylı değil; boş "konuşma yok" başarılı transkript değil; null güven korunur |
| CT16 | Güven anlamı | Log-olasılık olasılığa dönüştürülmez; kalibre olasılık sınırları ve kökeni |
| CT17 | Unicode varlık aralıkları | Türkçe karakterler, kaynak temsil ve sınırlar; kanonik metin ham metnin üzerine yazmaz |
| CT18 | Aday durumu | Katalogda doğrulanmış ≠ kullanıcı onaylı; bilinmiyor onaylı değil |
| CT19 | İşlem makbuzu durumları | UNKNOWN/FAILED/PENDING/BLOCKED asla gerçek başarı değil; mock gerçek değil; uydurma işlem kimliği yok |
| CT20 | Onay başvurusu | Durum revizyonu/yük uyuşmazlığı tespit edilir; gerçek yetki kanıtı yok |
| CT21 | Değiştirilemez plan | Dış ve iç değişim engellenir; girdi listesini değiştirmek planı etkilemez |
| CT22 | Parça planı yapısı | Yinelenen sıra/kimlik, negatif duraklama, sonlu olmayan hız reddedilir; korumalı aralıklar korunur |
| CT23 | Eski planda eksik köken | Normalizasyon sayısı, yetenek veya seed uydurulmaz; açık dönüşüm sonucu |
| CT24 | Seed korunumu | 9/42/77/123 açık seed'leri sentetik eşlemede değişmez; yedek ikame yok |
| CT25 | Plan/parça kimliği | Uyuşmayan oturum/tur/generation/plan revizyonu tespit edilir; yeniden normalizasyon yok |
| CT26 | Gerçek süre | Örnekten türetilen milisaniye; uyuşmazlık tespit edilir; bilinmiyor sıfır değil |
| CT27 | Render çerçeve profili | Çerçeve uzunluğu, son geçerli örnekler, web/AudioSocket profili kontrol edilir |
| CT28 | Oynatma gözlem kapsamları | Sunucuda boşaltma/tükenme uçta onay değil; bilinmeyen kapsam korunur |
| CT29 | JSON üst veri gidiş-dönüşü | Enum'lar, Unicode, null ve değiştirilemez koleksiyonlar; üst veride yük yok |
| CT30 | Güvenli izdüşüm | Sentetik kişisel veri işareti, ham metin, baytlar, gizli bilgi benzeri dizgi telemetri/hata/`repr`'den dışlanır |
| CT31 | Eski dönüş/API biçimi | Temsili gerçek M00 çıktıları alan/tür/durum/tel değişikliği olmadan gidiş-dönüş yapar |
| CT32 | Eski hata davranışı | Test edilen adaptörlerde mevcut istisna/HTTP durumu korunur |
| CT33 | Yalıtım | İki sentetik oturum ve generation başvurusu bağımsız; küresel değiştirilebilir varsayılan yok |
| CT34 | Şema sapması | Uygulama, belge ve şema fikstürü uyumlu; bilinmeyen alanlar belgeli politikaya uyar |
| CT35 | Özellik korunumu | Eşlenen M00 özellik kimlikleri ve regresyon yükümlülükleri korunur; güvenli mevcut test sonuçları dürüstçe karşılaştırılır |
| CT36 | Kapsam bütünlüğü | Beklenmeyen kaynak/DB/yapılandırma/ağırlık/bağımlılık/arayüz değişikliği yok; model başlatılmaz |

## 8. Kabul kapıları

Tüm kapılar engelleyicidir. Biri FAIL ise genel FAIL; FAIL yok ama HOLD/NOT_RUN varsa HOLD.

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M01-G00 | Ön kontrol | M00 genel PASS, `m01_ready: true`, doğrulanmış taban kanıtı, açıklanamayan kaynak sapması yok |
| M01-G01 | Kapsam/bütünlük | Yalnızca izinli eklemeler; özgün kaynak ve kullanıcı değişiklikleri korunmuş; DB/ağırlık/arayüz/bağımlılık değişikliği yok |
| M01-G02 | Sözleşme sahipliği | Mevcut türler denetlenmiş; sınır başına tek kanonik tanım veya gerekçeli adaptör; döngüsel içe aktarma ve yapay zekâ yan etkisi yok |
| M01-G03 | Sürüm/kimlik/zaman | Katı kapsamlı kimlikler, açık iç sürüm, saat ve birimler, yokluk yönetimi; CT02–CT05 PASS |
| M01-G04 | Ses | Geçerli biçim/yük/sahiplik, kesin örnek/bayt anlamı, son çerçeve politikası; CT06–CT12 PASS |
| M01-G05 | Konuşma/ASR | Doğru olay/söz anlamı, ham metin korunumu, kısmi/final ve güven ayrımı; CT13–CT18 PASS |
| M01-G06 | Diyalog/güvenlik anlamı | Makbuz durumları ve mock/gerçek ayrımı, onay başvuruları, sözleşmeden yetki çıkarılmaması; CT19–CT20 PASS |
| M01-G07 | Sentez | Derin değiştirilemez plan, korumalı aralıklar, seed korunumu, parça kimliği/süresi; CT21–CT26 PASS |
| M01-G08 | Oynatma | Çerçeve profili, kapsama uygun makbuzlar, protokol değişikliği yok; CT27–CT28 PASS |
| M01-G09 | Serileştirme/gizlilik | Güvenilir iç üst veri ile güvenli telemetri izdüşümü ayrı; CT29–CT30 ve CT34 PASS |
| M01-G10 | Uyum | Zorunlu M00 sınır eşlemeleri tam; eski biçim/hatalar ve özellik kimlikleri korunmuş; CT31–CT33 ve CT35 PASS; yeni regresyon yok |
| M01-G11 | Test kanıtı | Tüm zorunlu testler gerçek günlükle çalıştırılmış; CT01 ve CT36 PASS; atlanan zorunlu test HOLD |
| M01-G12 | Devir | Katalog, şemalar, eşleme tablosu, rapor, kanıt, geri dönüş ve M02 devri tam; açık konuların sahibi var ve M02'yi engellemiyor |

`m02_ready: true` yalnızca genel PASS ve kimlik/iptal sözleşmeleri net ise.

## 9. Kanıt

`evidence/M01/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `EXISTING_CONTRACT_INVENTORY.json` (gözlenen türler), `CHANGE_SCOPE.json`, `CONTRACT_DECISIONS.md`, `CONTRACT_CATALOG.json` (tüm türler, alanlar, sahip, doğrulama, gizlilik), `LEGACY_COMPATIBILITY_MATRIX.csv`, `TEST_MATRIX.json` (CT01–CT36 → gerçek test adları), `FEATURE_REGRESSION_MATRIX.csv`, `M02_HANDOFF.md`. JSON Schema dosyaları PoC'taki `contracts/` klasörüne, tek kaynak olarak.

## 10. Geri dönüş

Değişiklikler eklemelidir ve küçük commit'lerdir; geri dönüş M01 commit'lerinin `git revert`'üdür. Veritabanı veya model geri dönüşü gerekmez (değişmezler). Yıkıcı Git komutu kullanılmaz.

## 11. Devir

`M02_HANDOFF.md` şunları içerir: içe aktarma yolları ve sözleşme sürümü; `SessionIdentity`, `TurnRef`, `GenerationRef`, `StreamRef`, `EventEnvelope`, `CancellationReference` kuralları; bugünkü eski oturum yolları ve iptal/kuyruk/tur/generation davranışı; henüz uygulanmamış çalışma zamanı işleri (oturum başına monoton tur/generation tahsisi, iptal jetonu ve çiti, VAD tampon sahipliği, atomik durum, temizlik, oturum yalıtımı, iptal yarışları, eski sonuç bastırma — iptal edilen generation F5/F6 gönderiminde yeniden kontrol edilir; gönderilmiş ses geri alınamaz); `sequence` ve saat alanı sahipliği (M02/M04); M03 (model/yapılandırma alanları), M04 (güvenli olay izdüşümü), M05 (sözlük revizyonu), M06 (GPU iş kimliği), M07 (makbuz/onay), M08 (fikstürler) için notlar.

## 12. Başlatma komutu

```
M01 paketini uygula: docs/execution/packages/W1/M01-cekirdek-sozlesmeler.md.
Kuralları CLAUDE.md'den, sözleşme alanlarını docs/01-architecture/interfaces.md'den oku.
Önce kabul edilmiş M00 kanıtını doğrula; yoksa HOLD raporu yaz ve dur.
Mevcut genel davranışı değiştirmeden tipli iç sözleşmeleri ve eski kod adaptörlerini ekle.
CT01–CT36'yı çalıştır, M01-G00…G12'yi değerlendir, paket/M01 dalında PR aç ve dur.
```
