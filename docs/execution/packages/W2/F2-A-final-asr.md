# F2-A — Final ASR ve ham transkript

> F1'den gelen sonlandırılmış sözü doğrular, değiştirilemez yüke dönüştürür, M06 üzerinden mevcut Faster-Whisper tutamacıyla tanır, tembel segment üreticisinin gerçek bitişini bekler ve sonucu **ham metni koruyan**, değiştirilemez bir M01 `ASRResult` (yalnızca FINAL) olarak F3'e bir kez teslim eder. Bağlamsal hotword, düzeltme ve akış tanıma bu paketin işi değildir.

| Alan | Değer |
| --- | --- |
| Kimlik | F2-A |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, F1-A, M05, M06 |
| Sonraki | F3-A, W2_GATE, F2-B |
| Bayrak | `f2_pipeline_v2` (varsayılan kapalı; `off / shadow / strict`) |
| Ortam | CPU (gerçek Whisper yalnızca `@pytest.mark.gpu` testlerde; birim testleri sahte sağlayıcıyla) |
| Eski görevler | F2-T01, F2-T02, F2-T05, F2-T06, F2-T27 |
| Kaynak | Bundle `W2/Freya_2_0_F2_A_Agent_Implementation_Package.md`; [F2 spec](../../../stages/F2-speech-recognition/spec.md), [F2 tasks](../../../stages/F2-speech-recognition/tasks.md) |
| Durum | NOT_RUN |

## 1. Amaç

Bugün `transcribe()` yalnızca düz metin döndürüyor; güven, segment ve sonuç türü kayboluyor; ham metin `.strip()` ve filtrelerle değişiyor; model çağrısı ayrı kilitle GPU'ya gidiyor. F2-A tanıma sonucunu **dürüst** hale getirir: ham metin aynen, güven bilinmiyorsa `null`, konuşma yoksa `NO_SPEECH`, belirsizse `UNKNOWN`. Otomotiv terim doğruluğu iyileştirmesi F2-B'dedir; F2-A onun ölçülebilir zeminidir.

## 2. Başlamadan önce

- [ ] CORE_GATE, F0-A, F1-A, M05, M06 kabul edilmiş; güncel anlık görüntü uyumlu; onay var.
- [ ] Mevcut ASR modeli, yükleyici, çağıranlar, eski `str` birleştirme, korumalar (no_speech/logprob/sıkıştırma), hotword'ler ve GPU atlamaları izlenmiş; özellik kimlikleri eşlenmiş.
- [ ] Gerçek `transcribe` çağrısı, tembel segment yinelemesi, `info` nesnesi, beam, dil, hotword, sıcaklık, `vad_filter` ve eşik parametreleri kaydedilmiş. Etkin varsayılanlar **değişmez**.

## 3. Kapsam

**Yapılacak:** Sözleşme eşlemesi; giriş doğrulaması; yük oluşturma; söz kabulü ve tekilleştirme; M03 yapılandırma/model bağlama; M05 eski hotword köprüsü; M06 istek oluşturucu; Whisper adaptörü; sağlayıcı tamamlanma toplayıcısı; ham transkript koruması; segment ve güven üst verisi; açık tanıma sonuçları; muhafazakâr M05 varlık adayları; final sonuç birleştirme; atomik sonuç kabulü; yaşam döngüsü ve telemetri; eski kod/F3 noktası.

**Yapılmayacak:** Bağlamsal hotword, düzeltme, N-best, güven kalibrasyonu, belirsizlik kapısı (F2-B); kayan pencere/kısmi transkript (F2-C); ikinci yeniden örnekleme veya kırpma; yeni model; otomatik yeniden deneme.

## 4. Dosyalar

```
backend/speech_recognition/
  contracts_map.py  input_validation.py  payload.py  admission.py  binding.py
  hotword_bridge.py  scheduler_request.py  whisper_adapter.py  completion.py
  transcript.py  segments.py  outcomes.py  entities.py  result_builder.py
  delivery.py  telemetry.py  legacy_bridge.py
tests/speech_recognition/
evidence/F2-A/<run_id>/
```

`models.py` içindeki mevcut Whisper adaptörü silinmez; M06 sağlayıcı adaptörü ve bu paketin `whisper_adapter.py`'si onu sarar.

## 5. Tasarım ve sözleşmeler

### 5.1 Sahiplik

| Sahip | Sorumluluk |
| --- | --- |
| F1-A | Kesin kabul edilmiş ses aralığı, ön/son kayıt, sonlandırma, tek giriş turu kabulü |
| M01 | Paylaşılan veri şemaları ve doğrulama |
| M02 | Oturum/akış/tur kimliği, iptal, kapsamlı sonuç çitleri, kaynak defteri |
| M03 | Değiştirilemez yapılandırma/model revizyonu, yetenekler, bayrak etkinleştirme |
| M04 | Güvenli olay kataloğu, metrik tanımları, köken |
| M05 | Değiştirilemez sözcük görüntüleri; onaylı kanonik ve takma ad okuma arayüzleri |
| M06 | Zamanlayıcı, yerel tamamlanma, GPU rezervasyonu/yerleşiklik/kira |
| **F2-A** | Final ASR girdi/çıktısı, sınırlı yük oluşturma, ham transkript ve sonuç işleme |
| F2-B / F2-C | Bağlamsal hotword, düzeltme, güven kararları / kısmi ve akış tanıma |
| F3 / M07 | Diyalog ve eylem uygunluğu, müşteri/operasyon onayı, kalıcı iş etkileri |

### 5.2 Tanıma işi

| Alan | Kural |
| --- | --- |
| `utterance_ref` | M01/M02 oturum, akış, dönem, tur, `utterance_id` |
| `recognition_job_id` | Kabul edilmiş M06 iş protokolünden opak kimlik |
| `attempt_index` | İlk istek 0; yeni otomatik yeniden deneme politikası yok |
| `model_ref` / `config_ref` / `lexicon_ref` | Kabul anında yakalanan değiştirilemez görüntüler |
| `cancellation_ref` | Giriş turu kapsamı; ilgisiz oynatma generation'ı değil |
| `deadline_ns` / `clock_domain` | M02 monoton alanı; duvar saati aritmetiği yok |
| `input_samples` / kodlama | Kesin sınırlı üst veri, tahmin değil |
| `decode_profile_ref` | M03'te doğrulanmış mevcut dil/beam/hotword ve koruma yapılandırması |
| `payload_handle` | Sahipli veya kiralanmış değiştirilemez veri; günlüğe serileştirilmez |
| `result_delivery_state` | Yerel tamamlanmadan ve ASR sonucundan bağımsız |

M06 sınıfı: final ASR = **P1**.

### 5.3 `ASRResult` (FINAL)

| Alan | Kural |
| --- | --- |
| zarf | Gerçek şema sürümü, oturum/tur kimliği, sıra, iz, zaman, saat alanı |
| `utterance_id`, `revision` | Kesin giriş kimliği; ilk final revizyon; F2-A'da kısmi revizyon yok |
| `status` | Yalnızca `FINAL`; eylem yetkisi değildir |
| `language` | Gerçek bilinen dil veya `null`; istenen dil "algılanan dil" ölçümü değildir |
| `raw_transcript` | Düzeltme veya kırpmadan önce sağlayıcının birleştirilmiş özgün metni (harfi harfine) |
| `normalized_transcript` | Belgeli, yıkıcı olmayan mevcut normalizasyon açıkça eşlenmediyse `null` |
| `canonical_transcript` | Yeni katı temelde `null` (onaylı eski eşleme yalnızca aday olarak korunabilir) |
| `stable_prefix` | `null` |
| `segments` | İsteğe bağlı değiştirilemez segment kayıtları; doğrulanmış metin ve ofsetler |
| `entities` | Değiştirilemez muhafazakâr M05 adayları veya boş liste |
| `confidence` | Gerçek model üst verisi (`ConfidenceEstimate`); bilinmiyorsa `null`. `avg_logprob` ham puandır, olasılık değildir |
| `outcome` | `OK / NO_SPEECH / REJECTED / ERROR / UNKNOWN` |
| `requires_confirmation` | Açık değer veya `null`; belirsizlik rıza vermez |
| `error`, `metrics` | Güvenli `ErrorInfo`; gerçek kapsamlı `MetricSample`; eksikse `null` |

Eski genel `str` sözleşmesi ayrı bir **eski izdüşüm** olarak korunur (`.strip()`/filtre davranışı aynen); ham transkript bundan etkilenmez.

### 5.4 Sonuç ve teslim kuralları

| Durum | İç sonuç / teslim |
| --- | --- |
| Terminal sağlayıcıdan geçerli boş olmayan final, güncel tur | `OK`; tek atomik diyalog kabulü |
| Sağlayıcı bitti, mevcut korumalardan sonra geçerli konuşma yok | `NO_SPEECH`; iş diyaloğu metni yok; mevcut güvenli işleme |
| Geçersiz giriş, zamanlayıcı kabulü reddedildi | `REJECTED`; çıkarım veya normal diyalog yok |
| Doğrulanmış sağlayıcı hatası | `ERROR`; güvenli hata yolu; uydurma transkript yok |
| Sağlayıcı terminal durumu belirsiz | `UNKNOWN`; gerekirse M06 karantinası; normal diyalog yok |
| İptal/geçersiz kılma/son tarihten sonra yerel başarı | Sağlayıcı sonucu içeride tutulur; teslim çitlenir; F3 sonucu yok |
| Tüketici dolu/kapalı | Açık teslim reddi/geri basınç; sahte "teslim edildi" yok |
| Yinelenen geri çağrı | İlk terminal durum korunur; yinelenen teslim veya kira bırakma yok |

### 5.5 Faster-Whisper tamamlanma anlamı

`transcribe` dönüşü iş bitti demek değildir: segment üreticisi tüketilirken yerel hesaplama sürer. Kira, sınırlı yineleme bitene veya üretici kapanıp terminal kanıt alınana kadar tutulur. İlk segmentten sonra hata → `OK` kısmi final yok. Segment/metin bütçesi aşılırsa güvenli durdurma; kira terminal kanıta kadar korunur. OOM yalnızca M06 kurtarma politikasıyla; yerel kör yeniden deneme yok.

### 5.6 Varlık adayları

Yalnızca tam veya onaylı takma ad eşleşmesi (M05); ham aralık (yarı açık, Unicode kod noktası); `catalog_status=UNVERIFIED`, `confirmation_status=CANDIDATE`. Bilinmeyen araç adı zorla düzeltilmez. Plaka, motor kodu, yıl, fiyat yeniden yazılmaz. M05 görüntüsü yoksa açık güvenli sonuç; uydurma revizyon yok.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F2-A.01 | Çekirdek/F1/M05/M06 ön kontrolü | Kapı kanıtı, devir ve anlık görüntü doğrulaması | Eksikse değişiklikten önce HOLD |
| F2-A.02 | Tanıma envanteri | ASR modeli, yükleyici, çağıranlar, eski `str` birleştirme, korumalar, hotword'ler, GPU atlamaları; özellik kimlikleri | `F2_INVENTORY.json` |
| F2-A.03 | Sahiplik ve geçiş tasarımı | Tek katı rota, uyum bayrağı, kapsam, kilit sırası; geri dönüş kararı | `F2_DECISIONS.md` |
| F2-A.04 | Sözleşme eşlemesi | M01 `Utterance`/`ASRResult`/`ConfidenceEstimate`, M02/M06 eşlemeleri; hata/sonuç/teslim matrisi | AS04 |
| F2-A.05 | Giriş doğrulaması | Sonlandırılmış 16 kHz mono, sınırlar, kesin aralık, dönem, süreksizlik | AS05–AS15 |
| F2-A.06 | Yük oluşturma | Kararlı değiştirilemez tampon, gerekirse tek dönüşüm, kesin ofsetler ve yaşam süresi | AS16 |
| F2-A.07 | Söz kabulü | Kapsamlı tekilleştirme/talep, güncel tur çiti, sınırlı kayıt | AS17–AS23 |
| F2-A.08 | Yapılandırma ve model bağlama | Sabitlenmiş M03 revizyonları, mevcut etkin çözücü profili, yeni model yükleme yok | AS24–AS26 |
| F2-A.09 | M05 eski hotword köprüsü | Gerçek sıra/sınır/önbellek/seçim korunur; yeni bağlamsal hotword veya kişisel veri yok | AS27–AS29 |
| F2-A.10 | M06 istek oluşturucu | Final P1; gerçek kapsam/son tarih/maliyet ve kabul sonuçları | AS30–AS33 |
| F2-A.11 | Whisper adaptörü | Mevcut CTranslate2 tutamacı; tek yürütme yolu; bağımsız kilit/zamanlayıcı yok | AS33 |
| F2-A.12 | Sağlayıcı tamamlanma toplayıcısı | Sınırlı tembel yineleme, terminal kanıt, hata ve karantina koordinasyonu | AS34–AS40 |
| F2-A.13 | Ham transkript koruması | Kesin segment metni ve sırası; ayrı eski izdüşüm | AS41–AS44 |
| F2-A.14 | Segment ve güven üst verisi | Doğrulanmış zaman damgaları, yerel puanlar ve kaynak; eksikse `null` | AS45–AS50 |
| F2-A.15 | Açık tanıma sonuçları | `OK/NO_SPEECH/REJECTED/ERROR/UNKNOWN` teslimden ayrı; mevcut korumalar | AS51–AS52 |
| F2-A.16 | Muhafazakâr M05 varlık adayları | Yalnız tam/onaylı takma ad, ham aralıklar, belirsizlik, doğrulama iddiası yok | AS53–AS58 |
| F2-A.17 | Final sonuç birleştirme | Değiştirilemez M01 `ASRResult`, yalnız final; değişiklik yetkisi yok | AS59–AS60 |
| F2-A.18 | Atomik sonuç kabulü | Tamamlanma, kuyruğa ekleme ve tüketimde M02 çitleri; tek uygun sonuç | AS61–AS67 |
| F2-A.19 | Yaşam döngüsü ve telemetri | Sınırlı kuyruklar, iptal, giriş sahipliği, güvenli M04 gözlemi | AS68–AS70 |
| F2-A.20 | Eski kod/F3 noktası | Mevcut `str` sözleşmesi ve özellikler korunur; yalnız F3-A arayüz devri | AS71 |
| F2-A.21 | Belirlenimci test ve regresyon | AS01–AS72 gerçek sonuçlar; taban özellik eşlemesi; geri dönüş provası | AS72 |
| F2-A.22 | Kabul ve devir | F2-A-G00…G17; F3-A/F2-B/F2-C noktaları; açık hazırlık; dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| AS01 | Çekirdek kapı veya onay yok | Kaynak değişikliğinden önce HOLD |
| AS02 | Bayat F1-A/M05/M06 kabul bildirimi | Belirli tutarsızlıkla HOLD |
| AS03 | Yalnız CPU'lu yalıtılmış ortamda F2 içe aktarma | Model yükleme, ağ veya GPU başlatma yok |
| AS04 | Kabul edilmiş M01 sözleşme gidiş-dönüşü | Paylaşılan şema ve kimlikler korunur; yinelenen tanım yok |
| AS05 | Geçerli sonlandırılmış 16 kHz float32 mono söz | Talep edilebilir; kesin aralık korunur |
| AS06 | Geçerli 16 kHz PCM16 LE fikstürü | Gerekirse doğru sınırlı float dönüşümü |
| AS07 | PCM16 uçları −32768, 0, 32767 | −1, 0, 32767/32768; kırpma sarması yok |
| AS08 | Final olmayan söz veya aday `SpeechEvent` | Çıkarım gönderimi yok |
| AS09 | EOS üst verili boş ses | Uydurma konuşma veya otomatik OK yok |
| AS10 | Tek PCM bayt sayısı, tutarsız çerçeve sayısı | Sağlayıcıdan önce ret |
| AS11 | NaN/Inf veya desteklenmeyen kodlama | Güvenli ret |
| AS12 | F1 sözleşmesi 16 kHz mono isterken 8k/48k veya stereo | Ret; ikinci yeniden örnekleme/downmix yok |
| AS13 | Onaysız boşluklu ardışık olmayan örnekler | Ret; sessiz birleştirme yok |
| AS14 | Ön/son kayıt ve gerçek bitiş örneği fikstürü | Kesin giriş örnekleri korunur; ikinci kırpma yok |
| AS15 | Yapılandırılmış sınırı aşan boyut/süre | Sınırsız kopyadan önce ret |
| AS16 | Kabulden sonra değişen çağıran tamponu | Sağlayıcı girdisi değişmez |
| AS17 | Yanlış oturum/akış/dönem/tur | Zamanlayıcıdan önce kabul reddi |
| AS18 | Aynı sözün yinelenen gönderimi | Tek mantıksal talep ve tek GPU isteği |
| AS19 | Aynı söz kimliği, değişen üst veri/yük | Çakışma; ikinci tanıma değil |
| AS20 | Bariyerle eşzamanlı talepler | Tam olarak bir kabul edilmiş talep |
| AS21 | Oturum başı/küresel iş sınırı doldu | Açık sınırlı kabul sonucu; görev sızıntısı yok |
| AS22 | Aynı yerel söz kimlikli iki oturum | Bağımsız kapsamlı talepler |
| AS23 | Önceki finalden sonra geç yineleme | İkinci gönderim veya teslim yok |
| AS24 | Eski ayarların M03 profiline eşlenmesi | Mevcut etkin dil, beam, koruma değerleri korunur |
| AS25 | İstek kuyruktayken yapılandırma değişir | Sabitlenmiş görüntü korunur |
| AS26 | Eksik/desteklenmeyen model revizyonu veya yeteneği | Açık erişilemez/HOLD; sessiz model değişimi yok |
| AS27 | Eski hotword listesi ve sınır/TTL fikstürü | Aynı etkin sıralı liste ve seçim anlamı |
| AS28 | İş çalışırken M05 görüntüsü değişir | Adaylar için özgün görüntü kullanılır |
| AS29 | Olası hotword girdisinde kişisel veri | Küresel/müşteri hotword sızıntısı yok |
| AS30 | M06'ya geçerli final iş isteği | Doğru kapsam, revizyon, son tarih ve maliyetle P1 |
| AS31 | Zamanlayıcı `WAITING` ile `ADMITTED` | Kuyruk makbuzu yürütmeyle karıştırılmaz |
| AS32 | M06 reddetti/süresi doldu/erişilemez | Güvenli sonuç; yerel atlama yok |
| AS33 | Paylaşılan mevcut modele iki istek | M06 otoritesi ve tek tutamaç korunur |
| AS34 | Sağlayıcı `transcribe` tembel üretici döndürür | Kira dönüşte değil, yineleme boyunca tutulur |
| AS35 | Üretici ilk segmentten sonra hata fırlatır | OK kısmi final yok; gerçek terminal kanıt veya karantina |
| AS36 | Yineleyici segment/metin bütçesini aşar | Güvenli durdurma; sınırsız ayırma yok; kira terminal kanıta kadar |
| AS37 | Yerel yineleme sırasında işbirlikçi iptal | Bayat sonuç yok; ödünç tampon ve kira güvenli olana kadar tutulur |
| AS38 | Sağlayıcı terminal geri çağrısını iki kez verir | Tek tamamlanma; çift bırakma yok |
| AS39 | Sağlayıcı tamamlanması doğrulanamıyor | UNKNOWN/karantina; normal diyalog yok |
| AS40 | Yerel sağlayıcıdan OOM | Yalnız M06 kurtarma politikası; kör yerel yeniden deneme yok |
| AS41 | Baştaki boşluklu ve noktalamalı çoklu sıralı segmentler | Ham metin harfi harfine birleştirilir |
| AS42 | Türkçe I/İ/ı/i, aksanlar ve ayrışık karakterler | Ham kod noktaları değişmez |
| AS43 | Eski `.strip()`/filtrelenmiş izdüşüm | Geçmiş genel dizgi davranışı korunur; ham değişmez |
| AS44 | Tekrarlı sözcükler ve ASR yazım hatası | Sessiz düzeltme veya tekilleştirme yok |
| AS45 | Geçerli segment zaman damgaları | Açık göreli başlangıç ve birimler; doğru sınırlar |
| AS46 | Negatif, NaN, ters veya aralık dışı zaman damgaları | Ret veya açık güvenli durumla isteğe bağlı üst veri atlanır |
| AS47 | Eksik sözcük/zaman damgası/dil bilgisi | Şemaya göre `null` veya yok; uydurma değer yok |
| AS48 | Negatif ortalama log-olasılık | Ham puan olarak korunur, olasılık değil |
| AS49 | Geçerli `no_speech_prob` ve geçersiz sonlu olmayan puan | Geçerli puan tipli; bozuk puan kabul edilmez |
| AS50 | Kalibre güven üst verisi yok | `confidence` `null` veya yalnız yerel tipli kanıt |
| AS51 | Boş/yalnız boşluklu sağlayıcı sonucu | `NO_SPEECH` veya açık kabul edilmiş OK dışı sonuç |
| AS52 | Mevcut konuşma yok/logprob/sıkıştırma reddi | Koruma anlamı korunur; uydurma metin yok |
| AS53 | Geçerli tam onaylı M05 varlık eşleşmesi | Ham aralıklı aday, katalog UNVERIFIED |
| AS54 | Belirsiz onaylı takma ad | Sınırlı alternatifler; onaylı doğru seçilmez |
| AS55 | Bilinmeyen araç adı veya onaysız takma ad | Zorla düzeltme/etkinleştirme yok |
| AS56 | Korumalı plaka, motor kodu, sayısal yıl veya fiyat | Yeniden yazma veya yanlış alt dizgi eşleşmesi yok |
| AS57 | Ham metinde Unicode aralık ofseti | Yarı açık kod noktası ofsetleri ham alt dizgiyle tam eşleşir |
| AS58 | M05 görüntüsü eksik/erişilemez | Açık güvenli politika sonucu; uydurma revizyon yok |
| AS59 | Geçerli fikstürden M01 final `ASRResult` | FINAL, kesin söz ve tur başvuruları, değiştirilemez varlıklar |
| AS60 | Çağıran PARTIAL'ı final olarak göndermeye çalışır | Ret; normal F3 teslimi yok |
| AS61 | Zamanlayıcı kabulünden önce iptal | Yerel yürütme yok; güvenli giriş temizliği |
| AS62 | Gönderimden önce kuyruktaki işin iptali | M06 işi çıkarır; bayat tamamlanma teslim edilmez |
| AS63 | Yerel çıkarım sürerken tur geçersiz kılınır | Sonuç çitlenir; yürütme kirası terminale kadar |
| AS64 | Sonuç oluşturma ile kuyruğa ekleme arasında bariyerli iptal | Atomik ret; bayat kuyruk ekleme yok |
| AS65 | Kuyruğa eklendikten sonra, tüketimden önce iptal | Tüketici çiti bayat çıktıyı düşürür |
| AS66 | İlgisiz oynatma generation'ı iptal edilir | Güncel uygun giriş tanıması yalnız generation yüzünden iptal edilmez |
| AS67 | Dolu/kapalı aşağı akış kuyruğu ve oturum kapanışı | Açık ret/geri basınç; sızıntı veya sahte başarı yok |
| AS68 | Aynı saat ve saatler arası zamanlama üst verisi | Doğru metrik sınırları; alanlar arası geçersiz fark bilinmiyor |
| AS69 | M04 kuyruk taşması veya istisnası | ASR yaşam döngüsü ve iptal bağımsız kalır |
| AS70 | Transkript, ses, hata ve hotword'lerde kişisel veri işareti | Günlük, iz, metrik veya kanıtta sızıntı yok |
| AS71 | Eski ile isteğe bağlı katı rota, sahte diyalog tüketicisi | Tek teslim; eski genel sözleşme ve taban özellikleri korunur; gölge yan etkisi yok |
| AS72 | Entegre F1-A fikstürü → gerçek F2-A + M02/M05/M06 → sahte F3, geri dönüş provası | Doğru final devri, iptal ve uyum; dış yazma veya gerçek model yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F2-A-G00 | Ön kontrol | CG00–CG11, F0-A/F1-A, M05/M06 kabul edilmiş; güncel anlık görüntü uyumlu; onay var |
| F2-A-G01 | Tek otorite | Tek ASR/model otoritesi, incelenmiş kapsam, güvenli içe aktarma, üretimde sahte yok |
| F2-A-G02 | Giriş sınırı | Gerçek M01/F1-A/M02 eşlemesi ve sonlandırılmış giriş sınırı doğrulanmış |
| F2-A-G03 | Doğrulama | Biçim/örnek/sınır/yük doğrulaması ve değiştirilemez sahiplik |
| F2-A-G04 | Kabul | Atomik kapsamlı talep, tekilleştirme ve sınırlı kuyruk |
| F2-A-G05 | Varsayılanlar | M03 görüntüsü ve mevcut çözücü/hotword varsayılanları korunmuş |
| F2-A-G06 | GPU | Her katı GPU yolu M06 kabulünü ve tek mevcut model tutamacını kullanır |
| F2-A-G07 | Tamamlanma | Tembel yineleyici ve tamamlanma anlamı kaynak/API denetimi ve enjekte testlerle kanıtlanmış; erken kira bırakma yok |
| F2-A-G08 | Ham metin | Harfi harfine ham transkript, segmentler ve ayrı eski izdüşüm doğrulanmış |
| F2-A-G09 | Dürüst sonuç | Güven/dil üst verisi ve açık sonuçlar doğru; sahte konuşma yok |
| F2-A-G10 | Adaylar | M05 muhafazakâr adaylar, ham aralıklar, korumalı yeniden yazma yok, belirsizlik güvenli |
| F2-A-G11 | Final sonuç | Değiştirilemez final M01 `ASRResult`; PARTIAL veya çıkarılmış yetki yok |
| F2-A-G12 | Çit | M02 bayat sonuç reddi, atomik ekleme/tüketim ve temizlik doğrulanmış |
| F2-A-G13 | Gözlem | M04 kapsamlı ölçümler ve gizlilik; telemetri hatası yalıtılmış |
| F2-A-G14 | Test kanıtı | AS01–AS72 gerçek kanıtla çalıştırılmış ve geçmiş |
| F2-A-G15 | Regresyon | M00 özellik/API regresyonu ve önceki kabul edilmiş test uyumu |
| F2-A-G16 | Bütünlük | Kaynak bütünlüğü ve geri dönüş provası; izinsiz değişiklik yok |
| F2-A-G17 | Devir | F3-A/F2-B/F2-C devri incelenmiş; yapısal ile donanım hazırlığı ayrımı açık |

## 9. Kanıt

`evidence/F2-A/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F2_INVENTORY.json`, `F2_DECISIONS.md`, `PROVIDER_COMPLETION_AUDIT.md` (kurulu Faster-Whisper sürümünde tembel yineleme davranışı), `LEGACY_PROJECTION.md`, `TEST_MATRIX.json`. Taban WER/CER/terim doğruluğunun yeniden üretimi (eski F2-T01) yapılırsa `data/F2/lab-report-baseline-*.json`; bu paketin kabulü için zorunlu değildir.

## 10. Geri dönüş

`f2_pipeline_v2=off`: eski `transcribe() → str` yolu tek aktif teslim. Katı rota ayrı commit'lerde; `git revert` ile geri alınır. Gölge kip yan etki üretmediği için geri dönüşte veri temizliği gerekmez.

## 11. Devir

- **F3-A:** yalnızca `OK` final sonuçlar normal diyaloğa girer; `NO_SPEECH/REJECTED/ERROR/UNKNOWN` mevcut güvenli yollara. `entities` adaydır, doğrulanmış bilgi değildir.
- **F2-B:** bağlamsal hotword, düzeltme, N-best ve güven kalibrasyonu bu sonuç türünün üzerine; ham metin değişmez kalır, düzeltme ayrı alanda.
- **F2-C:** kısmi/kararlı revizyonlar aynı sözleşmeyle (P5); F2-A final yolu değişmez.

## 12. Başlatma komutu

```
F2-A paketini uygula: docs/execution/packages/W2/F2-A-final-asr.md.
Kuralları CLAUDE.md'den oku; CORE_GATE, F1-A, M05, M06 kabulünü doğrula.
backend/speech_recognition/ altında final ASR yolunu f2_pipeline_v2 bayrağı arkasında kur;
mevcut Whisper tutamacını M06 üzerinden kullan, ham metni değiştirme, güveni uydurma.
AS01–AS72'yi çalıştır, F2-A-G00…G17'yi değerlendir, paket/F2-A dalında PR aç ve dur.
```
