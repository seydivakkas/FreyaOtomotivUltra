# M03 — Yapılandırma, model ve ses profili kaydı

> Mevcut ayarlar ve model yükleyicileri etrafında tek, tipli, revizyonlu bir iç yapılandırma ve model üst veri kaydı kurar. Ortam değişkeni adları, varsayılanlar, öncelik sırası, genel API'ler ve Leyla seed 9 aynen korunur; hiçbir model yüklenmez, indirilmez.

| Alan | Değer |
| --- | --- |
| Kimlik | M03 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M01 (M02 varsa onun devri de okunur) |
| Sonraki | M05, M06, CORE_GATE, F5-B |
| Bayrak | Yok — kayıt pasiftir; mevcut ayarlar etkin kaynak olarak kalır, yeni deney bayrakları varsayılan KAPALI |
| Ortam | CPU |
| Eski görevler | — (F5-A'daki tek sentez yolu işinin model revizyonu kısmı bu pakete dayanır) |
| Kaynak | Bundle `W1/Freya_2_0_M03_Agent_Implementation_Package.md`; [configuration](../../../cross-cutting/configuration.md) |
| Durum | NOT_RUN |

## 1. Amaç

Bugün ayarlar `config.py`, ortam değişkenleri, model yükleyicileri ve yönlendiricilere dağınık; hangi modelin, hangi revizyonun, hangi seed'in etkin olduğu tek yerden okunamıyor. M03 şunları tek otoriteye bağlar: ayar kataloğu ve öncelik çözümleyici, doğrulama, güvenli izdüşüm, özellik bayrakları, değiştirilemez anlık görüntü ve revizyon, model/yapıt üst verisi, yetenek kanıtı, ses profilleri ve çevrimdışı hazırlık kontrolü.

## 2. Başlamadan önce

- [ ] M01 kabul edilmiş. M02 çalıştırılmışsa kabul kanıtı ve devri okunmuş; çalıştırılmamışsa M03 yalnızca enjekte edilen arayüzlerle bağımsız ilerler ve bu durum yazılır.
- [ ] M00 `CONFIG_MODEL_INVENTORY.json`, `EXPERIMENT_INVENTORY.json` ve özellik kayıtları okunmuş.
- [ ] Her ayar bildirimden etkin değere kadar izlenmiş: öncelik, ayrıştırıcı, türetilmiş değer, varsayılan, tüketiciler, genel okuma/yazma API'si. Aday dosyalar: `config.py`, `models.py`, `batched_ode.py`, `session.py`, `supervisor/`, `morphology/`, `automotive_frontend.py`, `dsp.py`, `audiosocket_server.py`, `telephony.py`, ilgili yönlendiriciler, başlatma betikleri, örnek ortam dosyaları.
- [ ] Gizli bilgi dosyaları yalnızca **varlık/yol** olarak kaydedilir; `.env`, üretim ortamı, süreç ortamının tamamı veya gizli değerler okunmaz/dökülmez. Testlerde örnek anahtarlar ve sentetik haritalar kullanılır.
- [ ] Gerçek ağırlıkların yokluğu çevrimdışı dağıtım için HOLD'dur; yalnızca üst veri birim testlerini engellemez. Bu iki kapsam ayrı raporlanır.

## 3. Kapsam

**Yapılacak:** Ayar kataloğu, kaynak çözümleyici, alan ve alanlar arası doğrulama, güvenli izdüşüm, bayrak kaydı, anlık görüntü/revizyon/geri alma, model kaydı, yapıt bütünlüğü (SHA-256), yetenek kaydı, ses profilleri, çevrimdışı hazırlık, eski koda pasif adaptör, testler.

**Yapılmayacak:** Model yükleme, indirme, Ollama pull, HF önbelleği, ağ yoklaması; canlı model değişimi (hot swap); GPU ölçümü veya kabulü (M06); olay yolu (M04); sözlük içeriği (M05); yetki (M07). Ortam değişkeni adlarını, varsayılanları, genel yanıt anahtarlarını değiştirmek. Seed, dtype, cihaz, çözücü adımı veya bayrağı sessizce değiştirmek. Yeni bağımlılık.

## 4. Dosyalar

```
backend/core/configuration/
  contracts.py  setting_catalog.py  sources.py  resolver.py  validation.py
  feature_flags.py  snapshots.py  revision.py  safe_projection.py  legacy_adapter.py
backend/core/model_registry/
  contracts.py  registry.py  artifact_verifier.py  capabilities.py
  voice_profiles.py  offline_preflight.py  activation_policy.py  legacy_adapter.py
config/models/  config/voices/  config/profiles/  config/features/   # gizli olmayan bildirimler
tests/configuration/
evidence/M03/<run_id>/
```

Her anahtar için **tek tanım otoritesi**: JSON ile Python'da yarışan varsayılan olmaz; diğer gösterimler üretilir veya ona karşı doğrulanır. Mevcut eşdeğer modül varsa önce o uyarlanır.

## 5. Tasarım ve sözleşmeler

### 5.1 Değişmez kurallar

1. Tek çözümleyici; anahtar/model/profil/bayrak başına tek kanonik tanım. Kayıt modüllerini içe aktarmak dosya okumaz, ağırlık yüklemez, CUDA ayırmaz, süreç/iş parçacığı başlatmaz, DB/soket açmaz, indirme yapmaz. Tüm yoklamalar açık çağrı ve enjeksiyonla.
2. Gözlenen eski öncelik, adlar, varsayılanlar, ayrıştırma (geçmişte kabul edilen değerler dahil), genel yanıt anahtarları ve HTTP/WS sözleşmeleri korunur. Yeni iç arayüzlerde doğrulama daha katı olabilir; eski adaptör kabul edilen anlamı korur ve farklar belgelenir.
3. Otomatik indirme, uzaktan doğrulama, ağ yoklaması yok. Yeni çevrimdışı yollar sessizce buluta veya başka modele düşmez. Gizli seed ikamesi, dtype/cihaz değişimi, çözücü azaltma veya bayrak çevirme yok.
4. Model kaydı; üst veri, değişmez kimlikler, yapıt başvuruları, beyan edilen/doğrulanan yetenekler, köken, beklenen/gözlenen değerler, kullanılabilirlik ve etkinleştirme onayını **ayrı ayrı** tutar. Ağırlıklar yüklenmez; güvenilmeyen pickle açılmaz. Yalnızca onaylı, gizli olmayan yerel yapıtlar akışlı okumayla hash'lenir; checkpoint'ler repoya veya rapor klasörüne kopyalanmaz.
5. M01 `schema_version`'ı; `config_revision`, `model_revision`, `voice_revision`, `lexicon_revision`'dan bağımsızdır. Parmak izi kanonik ve belirlenimcidir: zaman damgası, mutlak makine yolu, sözlük sırası, istek kimliği veya geçici hazırlık durumu revizyonu değiştirmez. Kimlik bilgisi, ham ses, müşteri metni hash'lenmez. Gizli bilgi döndürülünce opak sağlayıcı revizyonu kullanılır.
6. Yayımlanan anlık görüntü derinlemesine değiştirilemez. Yayın atomiktir: eski ya da yeni tam görüntü, karışık değil. Başarısız yayında son bilinen iyi revizyon kalır. Yapılandırma/model/ses başvuruları M02 ile birlikte oturum veya generation sınırında sabitlenir; tur ortasında sessiz değişim yok. Model etkinleştirme yeniden başlatmada veya onaylı adımda olur.
7. Bayrağın istenen/etkin durumu, yetenek, bağımlılıklar, yayılım kapsamı, onay ve neden ayrı görünür. Mevcut varsayılanlar (açık olanlar dahil) korunur; yeni deney bayrakları varsayılan KAPALI. Kapalı bayrak özelliği silmez. Bilinmeyen yetenek destek değildir. Bayrak tek başına yetki değildir (M07/F3). Gölge kip yan etki üretmez.
8. Tüm test verisi sentetik. Gizli içerik, kişisel veri, ham arama sesi veya rastgele istisna metni toplanmaz. Durumlar `PASS`, `FAIL`, `HOLD`, `NOT_RUN`.

### 5.2 Ayar tanımı ve çözümleme

`SettingDefinition`: `key` (kararlı noktalı iç kimlik), `legacy_keys` (benzersiz takma adlar), `value_type`, `unit` (açık veya null), `declared_default` (gizli olmayan değer veya null), `required_scope`, `nullable`, `sensitivity` (`PUBLIC / INTERNAL / SECRET_REF / PERSONAL`), `owner` (aşama/paket), `restart_policy` (`PROCESS / SESSION_BOUNDARY / GENERATION_BOUNDARY / LIVE_SAFE`), `feature_ids`, `source_refs`.

`ResolvedSetting`: `key`, `effective_value` (tipli değer veya opak gizli başvuru), güvenliyse `requested_value`, `source_kind`, `source_ref` (güvenli göreli kimlik), `resolution_status`, `warnings`, `revision`. **Yok**, **boş**, `false`, `0` ve `null` birbirinden ayrıdır; doğruluk değerine dayalı geri düşme yoktur.

Öncelik: önce her anahtarın gözlenen eski önceliği belgelenir. Yeni iç yapılandırmada (yalnızca uyumlu ve kabul edilmişse) tipik sıra: açık onaylı geçersiz kılma > mevcut ortam geçersiz kılması > seçilen yerel profil > beyan edilen varsayılan. Eski ayar nesnesi ortamı zaten çözüyorsa etkin değeri **bir kez** uyarlanır; aynı ortam iki kez birleştirilmez.

Örnek kayıt (mevcut anahtar olduğu iddiası değildir; M00'dan gerçek takma ad ve özellik kimlikleriyle doldurulur):

```json
{"key":"tts.ode_steps","value_type":"integer","unit":"steps","declared_default":32,
 "owner":"F5","sensitivity":"PUBLIC","restart_policy":"GENERATION_BOUNDARY",
 "legacy_keys":[],"source_refs":[],"feature_ids":[]}
```

Eşdeğer eski anahtar yoksa önerilen ve etkin olmayan olarak sınıflanır. Toplu boyut 1, çözücü 16/24/48, WSOLA, konfor gürültüsü veya önerilen GPU bütçeleri **otomatik etkinleşmez**.

### 5.3 Alanlar arası doğrulama

| Alan | Yeni etkin yapılandırma kuralı | Eski kısıt |
| --- | --- | --- |
| Ses | Pozitif örnekleme hızı/kanal; beyan edilen kodlama; gerektiğinde tam çerçeve/örnek aritmetiği | AudioSocket PCM16 8 kHz ve mevcut web çerçevelemesi korunur |
| VAD | Eşik [0,1] sonlu; pozitif pencere; uyarlanır başlangıç/bitiş sırası yalnız uyarlanır kip açıksa | Mevcut tek eşik geçerli; Silero 512 örnek/32 ms VAD penceresidir, 20 ms aktarım çerçevesi değil |
| ASR | Bilinen motor/cihaz/dtype profili; pozitif beam, dil ve çözücü kısıtları | Mevcut Faster-Whisper yapılandırması korunur |
| LLM | Sağlayıcı türü, model etiketi, uç nokta üst verisi, pozitif zaman aşımları | Dış yoklama yok; yerel/uzak kip açık; sağlayıcı korunur |
| TTS | Yükleyiciye göre geçerli seed alanı; pozitif çözücü adımı/çerçeve sınırı; izinli dtype/cihaz | Leyla 9; açık A/B seed'i korunur; yetenek anahtardan çıkarılmaz |
| GPU | Açık MiB/bayt kapasiteleri, bilinmeyen gözlemler | VRAM ölçümü veya kabul yok; M06'nın işi |
| Aktarım | Port aralıkları, kanal kodlama/çerçeve uyumu | AudioSocket/AMI/ARI ayarları korunur; bağlantı yok |
| Zaman aşımı/kuyruk | Sonlu, sınırlı, birimli; taşma politikası üst verisi | Gözlenen kuyruk varsayılanları ve M02 sahipliği değişmez |
| İş/sağlayıcılar | Kip tutarlılığı, mock/canlı, bağımlılık ve onay üst verisi | İşlem, SMS, dış çağrı yapılmaz; yetki M07'de |

Sözdizimsel geçerlilik dağıtım hazırlığından ayrıdır: geçerli bir yapılandırma, yerel yapıtlar eksik olduğu için HOLD olabilir. Hatalar M01 `ErrorInfo` ile, gizli değer içermeden.

### 5.4 Anlık görüntü ve revizyon

`ConfigSnapshot`: `schema_version`, `config_revision`, `profile_id`, `source_manifest` (güvenli köken), değiştirilemez gizli olmayan etkin ayarlar, ayrı tutulan gizli başvurular, seçili model/ses revizyonları (veya bilinmiyor), bayrak kararları, yetenek başvuruları, doğrulama durumu, sınırlamalar. Model nesnesi, GPU tutamacı, DB bağlantısı tutmaz.

Parmak izi: şema etiketli kanonik UTF-8 JSON, sıralı anahtarlar, sonlu değerler, açık birimler, mantıksal yapıt kimlikleri (mutlak yol değil), SHA-256. `config_revision` etkin davranışı yansıtır; yakalama/yayın zamanı hash girdisi değildir. Yeni yapılandırma yalnızca `restart_policy`'ye uygun gelecek oturum/generation'ları etkiler; eski görüntüler yalnızca gerektiği sürece, sınırlı ve sahipli tutulur.

### 5.5 Bayraklar, modeller, yapıtlar, yetenekler, sesler

- **Bayrak tanımı:** `flag_id`, `legacy_key`, `owner`, `existing_default`, `proposed_default` (yalnız yeni bayrak), `value_domain`, `allowed_scopes`, `prerequisite_flags`, `required_capabilities`, `approval_required`, `experimental`, `restart_policy`, `feature_ids`, `source_refs`. Yineleme, eksik bağımlılık ve döngü yayından önce reddedilir. Karar: istenen, etkin (veya bilinmiyor), neden kodu, kapsam. `f0_pipeline_v2 … f6_pipeline_v2` bayrakları burada kayıtlıdır, varsayılan KAPALI.
- **`ModelDescriptor`:** `model_id`, motor ailesi, rol (`VAD / ASR / LLM / TTS / EMBEDDING / OTHER`), sağlayıcı/çalışma zamanı, yapıt başvuruları, mantıksal revizyon, beklenen/gözlenen digest bildirimi, istenen/etkin cihaz ve dtype (kanıt gelene kadar bilinmiyor), kaynak profili başvurusu, beyan edilen giriş/çıkış biçimi, yetenekler. Aday temel modeller (M00'da doğrulanır): Silero VAD, Faster-Whisper Large V3 Turbo (CTranslate2), Qwen 2.5 7B (Ollama), FreyaTTS DiT/AudioVAE. E5/ECAPA/RNNoise gibi öneriler etkin olmayan aday olarak kalır.
- **`ArtifactRef`:** `artifact_id`, `model_id`, mantıksal göreli yol, tür, `expected_sha256` (null olabilir) ve kökeni, `observed_sha256`, `observed_size_bytes`, `verification_status`: `MISSING / UNREADABLE / UNVERIFIED / OBSERVED_ONLY / MATCH / MISMATCH / CHANGED_DURING_CHECK / UNSUPPORTED_LOCATOR`. İlk gözlenen digest yeniden üretilebilirlik tabanıdır, **orijinallik kanıtı değildir**. Uyuşmazlıkta beklenen değer yeniden yazılmaz.
- **Yetenekler:** M01 `CapabilityDescriptor`; kapsam (`MODEL / VOICE / TRANSPORT / RUNTIME`), beyan/doğrulanmış durum, kanıt, geçerli revizyon, yöntem, sınırlama. Statik kod incelemesi gerçek ses kalitesini kanıtlamaz. Revizyon değişince eski doğrulama yeni profili yetkilendirmez. IPA/SSML/yerel akış desteği istek veya ipucundan çıkarılmaz.
- **`VoiceProfile`:** `voice_id`, `display_name`, `voice_revision`, `model_id`, `model_revision`, `seed`, `solver_profile_ref`, `duration_profile_ref`, diller, izinli kapsam, onay durumu, başvuru yapıtları, yetenekler. Varsayılan Leyla seed 9; 42/77/123 deneysel. Laboratuvar geçersiz kılması yalnızca yalıtılmış istek/oturumu etkiler. Yapıt eksikse başka seed'e veya harici TTS'e otomatik geçiş yok. F5 önbellek anahtarı girdileri (revizyon, normalize metin, seed, çözücü, süre, biçim) buradan sağlanır.

```json
{"voice_id":"leyla","seed":9,"model_id":"freya_tts","model_revision":null,
 "solver_profile_ref":"legacy_baseline","allowed_scope":"LIVE_BASELINE",
 "approval_status":"UNVERIFIED","speaker_similarity":null}
```

### 5.6 Çevrimdışı hazırlık

Açık çağrıyla, enjekte edilen üst veri/yapıt/dosya sistemi adaptörleri üzerinden: yapılandırma geçerliliği, seçili profil ve bağımlılıkları, beklenen yerel yapıtlar, onaylı kök dizinler, doğrulama durumu, yetenek kısıtları, sağlayıcı kipleri. Ağ ve GPU yoklaması yok; ağır çalışma zamanı içe aktarılmaz. Sonuç kapsamlıdır: "üst veri HAZIR" ≠ "çıkarım çalıştı" (`NOT_RUN`).

### 5.7 Eski kodla uyum

Mevcut ayar sınıfı, model yükleyicileri ve genel rotalar etrafında adaptör; tercihen açık önyükleme veya test sınırında zaten çözülmüş ayarların pasif izdüşümü. İkinci bir ortam okuyucu veya gölge varsayılan nesnesi yok. Genel API ve frontend eylem şemaları değişmez. Uyum tablosu satırı: anahtar/model/bayrak kimliği, özellik kimlikleri, eski yol/sembol/tür/varsayılan, gözlenen öncelik, yeni tanım, adaptör, eşdeğer sentetik girdide yeni etkin değer, farklar, testler. Eski üst veri yoksa "bilinmiyor"; tahmin yok.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M03.01 | Ön kontrol | Kabul edilmiş M00/M01, M02 uyum durumu, HEAD, kapsam, kanıt | Ön kontrol kaydı veya HOLD |
| M03.02 | Eski yapılandırma envanteri | Genel anahtar adları/varsayılanlar/türler/takma adlar/tüketiciler, model yapıtları, bayraklar | `CONFIG_INVENTORY.json` |
| M03.03 | Sahiplik ve geçiş tasarımı | Kesin kaynak önceliği, yazma kapsamı, uyum seçimleri, pasif içe aktarma, tek otorite | `CHANGE_SCOPE.json`, `CONFIG_DECISIONS.md` |
| M03.04 | Tipli ayar kataloğu | Birimler, null/bilinmiyor, hassasiyet; benzersiz anahtar/takma ad sahipliği | CR02–CR03 |
| M03.05 | Kaynak çözümleyici | Varsayılanlar, profiller, eski ayar/ortam, açık geçersiz kılmalar; gözlenen öncelik ve köken; yok/boş ayrımı | CR04–CR05, CR09 |
| M03.06 | Doğrulama ve kısıtlar | Yeni geçersiz veriyi ve imkânsız birleşimleri reddet; eski anlam adaptörle korunur; zorlamasız açık hatalar | CR06–CR12 |
| M03.07 | Güvenli izdüşüm | Gizli başvuruları genel veriden ayır; izin listeli tanılama; gizli/kişisel veri hash'i yok | CR13–CR15 |
| M03.08 | Bayrak kaydı | Mevcut kipler/varsayılanlar korunur; bağımlılıklar, yetenek kontrolü, deney yalıtımı, istenen/etkin ve neden | CR16–CR20 |
| M03.09 | Anlık görüntü ve revizyon | Derin değiştirilemezlik, kanonik parmak izi, atomik yayın, bilinen iyiye geri dönüş, sabitleme noktası | CR21–CR26 |
| M03.10 | Model üst veri kaydı | Mevcut STT/LLM/TTS/VAD ve isteğe bağlı bileşenler (M00 kanıtından); yapıt, çalışma zamanı, revizyon | CR27–CR29 |
| M03.11 | Yapıt bütünlüğü | Açık yerel yol kontrolleri, akışlı hash, beklenen/gözlenen, eksik/değişmiş ayrımı | CR30–CR36 |
| M03.12 | Yetenek kaydı | Beyan/doğrulanmış/desteklenmiyor/bilinmiyor; istenen/etkin; kanıt kesin yapıt/yapılandırma kapsamına bağlı | CR37–CR39 |
| M03.13 | Ses profilleri | Leyla seed 9 korunur; deneyler yalıtılmış; model/çözücü/süre/önbellek kimliği başvuruları | CR40–CR42 |
| M03.14 | Çevrimdışı hazırlık | Yerel yapıtların, çalışma zamanı önkoşullarının, sağlayıcı yapılandırmasının ağsız/yüklemesiz statik kontrolü | CR43–CR44 |
| M03.15 | Eski kod bütünleşmesi | Yan etkisiz dar adaptör; tüm dış arayüzler korunur; canlı model etkinleşmez | CR45–CR46 |
| M03.16 | Sözleşme ve uyum testleri | CR01–CR48; sahte yükleyiciler, geçici dosyalar, sentetik ayarlar | Tüm testler çalıştırılmış |
| M03.17 | Regresyon ve bütünlük | M00 özellik kimlikleri ve API/bayrak/varsayılan tabanları, izinli fark, geri dönüş | CR47–CR48 |
| M03.18 | Kabul ve devir | M03-G00…G13, hazırlık, aşağı akış arayüzleri; M03'ten sonra dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| CR01 | Kabul edilmiş önkoşul fikstürü, geçersiz/eksik kanıt | Geçerli üst veri kabul; geçersiz önkoşul HOLD, kaynak değişmez |
| CR02 | Kanonik anahtar ve takma ad benzersizliği | Yinelenen ve belirsiz eşlemeler reddedilir |
| CR03 | Mevcut varsayılanlar ve genel ortam adları | Gözlenen varsayılan ve adlar eşdeğer fikstürde korunur |
| CR04 | Kaynaklar arası öncelik | Gerçek eski öncelik korunur; yeni çözümleyici belirlenimci |
| CR05 | Yok / boş / false / sıfır / null | Doğruluk değerine dayalı geri düşme veya örtük varsayılan yok |
| CR06 | Boolean/tür/enum ayrıştırma | Yeni yolda katı doğrulama; eski kabul edilen ayrıştırma uyumlu |
| CR07 | Geçersiz sayı, NaN/Inf, birim sınırları | Yapılı ret; yanıltıcı zorlama yok |
| CR08 | Bilinmeyen anahtar / bozuk veya yinelenen anahtarlı profil | Katı yeni profil reddedilir; ilgisiz ortam güvenle yok sayılır |
| CR09 | Çakışan eski takma adlar | Gözlenen öncelik veya açık çakışma; sessiz yeni kazanan yok |
| CR10 | Ses biçimi ve çerçeve aritmetiği | Geçerli PCM boyutları; VAD/aktarım ayrımı; geçersiz birleşim reddedilir |
| CR11 | VAD/ASR/TTS alanlar arası ayarlar | Etkin kipe özgü kurallar; kapalı eski yol bozulmaz |
| CR12 | Cihaz/dtype/zaman aşımı/kuyruk | Birimler açık; desteklenmiyor/bilinmiyor ayrı |
| CR13 | Tanılamaya, `repr`'e ve hataya gizli bilgi sızdırma denemesi | Gizli bayt, düşük entropili gizli hash veya ham ortam dökümü yok |
| CR14 | Gizli bilgi benzeri içerikli bilinmeyen iç içe alan | İzin listeli izdüşüm onu dışlar veya güvenle reddeder |
| CR15 | Gizli bilgi döndürme ve revizyon | Opak revizyon/yeniden yükleme sinyali; gizli bilgiden türetilmiş hash yok |
| CR16 | Mevcut bayraklar ve kipler | Gözlenen varsayılanlar ve enum anlamı aynen korunur |
| CR17 | Yeni deney bayrağı | Varsayılan kapalı; laboratuvar kapsamı yalıtılmış |
| CR18 | Önkoşulu eksik veya desteklenmeyen yetenekli bayrak | İstenen/etkin durum ve neden doğru |
| CR19 | Bayrak bağımlılık döngüsü / yineleme | Yayından önce doğrulama başarısız |
| CR20 | Gölge/korumalı kip ve yetki sınırı | Üst veri yazma yetkisi vermez, sağlayıcı çağırmaz |
| CR21 | Derin değiştirilemez anlık görüntü | İç içe değişim yayımlanmış durumu etkilemez |
| CR22 | Belirlenimci revizyon | Eşdeğer sıra/zaman damgası/yol üst verisi aynı anlamsal hash'i verir |
| CR23 | Değişen etkin ayarlar | İlgili revizyon değişir; model/ses/şema revizyonları ayrı kalır |
| CR24 | Eşzamanlı yayın ve bayat yazıcı | Ya hep ya hiç; bayat karşılaştır-değiştir reddedilir |
| CR25 | Geçersiz aday ve geri dönüş | Önceki bilinen iyi etkin kalır; etkinleşme iması yok |
| CR26 | Oturum/generation'a sabitlenmiş görüntü fikstürü | Eski kapsam değişmez; yeni uygun kapsam onaylı revizyonu görür |
| CR27 | Kayıt araması ve bilinmeyen model | Açık bilinmiyor; yükleyici veya alternatif model seçilmez |
| CR28 | Yinelenen model/revizyon kimlikleri | Çakışma reddedilir; tanımlayıcı sessizce değiştirilmez |
| CR29 | İstenen/etkin model/cihaz/dtype | Kapsamlı gerçek kanıta kadar bilinmiyor; üst veri yüklü durum değildir |
| CR30 | Akışlı yapıt digest eşleşmesi | Küçük fikstür hash'i güvenilir beklenen digest'le eşleşir |
| CR31 | Beklenen digest yok | Yalnızca gözlendi; orijinallik veya onay iddiası yok |
| CR32 | Hash uyuşmazlığı, beklenen yeniden yazılmaz | Uyuşmazlık raporlanır, aday etkinleştirme reddedilir |
| CR33 | Eksik/okunamaz yapıt | Güvenli tipli durum; indirme yok |
| CR34 | Çok dosyalı yapıt bildirimi | Belirlenimci sıra; eksik zorunlu dosya hazırlığı engeller |
| CR35 | Yol geçişi/sembolik bağ veya yetkisiz kök | Reddedilir veya açık HOLD; izinli kapsam dışında okuma yok |
| CR36 | Doğrulama sırasında değişen dosya | Geçersiz gözlem atılır; sınırlı yeniden deneme/HOLD |
| CR37 | Yetenek bilinmiyor / beyan / doğrulanmış | Uygun kanıt olmadan yükseltme yok |
| CR38 | Revizyon yetenek kanıtını geçersiz kılar | Bayat doğrulama yeni profili yetkilendiremez |
| CR39 | Desteklenmeyen IPA/SSML/yerel akış | Üst veri, istek veya ipucuna dayanarak destek iddia edemez |
| CR40 | Leyla varsayılan seed | Gözlenen 9 korunur; uyuşmazlık raporlanır, sessizce sıfırlanmaz |
| CR41 | A/B ses kapsamı ve geri düşme | Açık deney seed'i korunur veya açık hata |
| CR42 | Ses revizyonu ve önbellek kimliği | Değişen model/çözücü/ses farklı revizyon girdisi üretir |
| CR43 | Eksik model/sağlayıcıyla çevrimdışı ön kontrol | Kapsamlı HOLD/`UNKNOWN_RUNTIME`; indirme, yoklama, yükleme yok |
| CR44 | Geçerli yerel fikstür, eksik isteğe bağlı bağımlılık | Yalnızca üst veri HAZIR; çalışma zamanı çıkarımı NOT_RUN |
| CR45 | Güvenli içe aktarma ve arama yan etkileri | Kayıt içe aktarma/aramadan sıfır model yükleme/ağ/DB/görev |
| CR46 | Eski API/yapılandırma adaptörü regresyonu | Eski içe aktarma/dönüş biçimi ve varsayılanlar korunur; eksik üst veri bilinmiyor |
| CR47 | M02/M04/M05/M06 arayüz noktaları | Yinelenen sahiplik yok; güvenli revizyon/yetenek devri; enjekte edilmiş sözleşme testleri |
| CR48 | İzinli fark, özellik kaydı, kanıt bütünlüğü | Yalnızca izinli değişiklik; M00 yükümlülükleri korunmuş; gizli/kişisel veri yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M03-G00 | Ön kontrol | M00/M01 kabul edilmiş, M02 uyum durumu açık, açıklanamayan sapma yok |
| M03-G01 | Tek otorite | Tek yapılandırma/model üst veri otoritesi, onaylı kapsam, pasif içe aktarma, yeni yükleyici yok |
| M03-G02 | Eski anlam | Anahtar kataloğu; gözlenen eski öncelik/varsayılan/takma adlar korunmuş |
| M03-G03 | Doğrulama | Tipli doğrulama, kısıtlar ve güvenli yapılı hatalar gösterilmiş |
| M03-G04 | Gizlilik | Tanılama/kanıtta gizli veya kişisel veri yok; gizli bilgiden türetilmiş hash yok |
| M03-G05 | Bayraklar | Mevcut bayraklar korunmuş, yeni deneyler yalıtılmış, istenen/etkin ve önkoşullar doğru |
| M03-G06 | Anlık görüntü | Derin değiştirilemezlik, belirlenimci revizyon, atomik yayın/geri dönüş, sabitleme noktası |
| M03-G07 | Model üst verisi | Revizyonlar ayrı; sahte çalışma zamanı etkinleşmesi veya hazırlık iddiası yok |
| M03-G08 | Yapıt doğrulama | Eşleşme/uyuşmazlık/eksik/yalnızca gözlendi ve güvenli yol kontrolleri test edilmiş |
| M03-G09 | Yetenek ve ses | Yetenek kanıtı revizyona bağlı; Leyla ve açık seed davranışı korunmuş |
| M03-G10 | Çevrimdışı hazırlık | Ağ/indirme/model yükleme yok; doğru kapsamlı HOLD/NOT_RUN durumları |
| M03-G11 | Test kanıtı | CR01–CR48 kanıtla geçmiş; gerçek dağıtım sınırları ayrı |
| M03-G12 | Uyum ve bütünlük | Özellik/API uyumu, izinli fark, kanıt ve geri dönüş doğrulanmış |
| M03-G13 | Devir | Aşağı akış sözleşmeleri ve sahiplik devredilmiş; yinelenen uygulama yok |

## 9. Kanıt

`evidence/M03/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `CONFIG_INVENTORY.json`, `CHANGE_SCOPE.json`, `CONFIG_DECISIONS.md`, `SETTING_CATALOG.json` (gizli değer yok), `FLAG_REGISTRY.json`, `MODEL_REGISTRY.json`, `ARTIFACT_VERIFICATION.json` (yalnızca onaylı yerel yapıtlar, mantıksal yollar), `VOICE_PROFILES.json`, `OFFLINE_READINESS.json`, `LEGACY_COMPATIBILITY_MATRIX.csv`, `TEST_MATRIX.json`, `DOWNSTREAM_HANDOFF.md`.

## 10. Geri dönüş

Kayıt pasif olduğu için geri dönüş M03 commit'lerinin `git revert`'üdür. Eski ayar nesnesi her zaman etkin kaynak olarak kalır; adaptör kaldırılınca davranış değişmez. Yayımlanmış bir anlık görüntü sorunluysa çalışma zamanında son bilinen iyi revizyona dönülür.

## 11. Devir

- **M04:** `config_revision`, `model_revision`, `voice_revision` alanları olay/izleme üst verisine; güvenli izdüşüm kuralları.
- **M05:** `lexicon_revision` yapılandırmadan bağımsız; sözlük yapıtlarının bütünlük doğrulaması aynı yapıt doğrulayıcısıyla.
- **M06:** model kaynak profili başvuruları; GPU bütçesi ayarlarının kaynağı (ölçüm ve kabul M06'da).
- **M07:** bayrak ≠ yetki; korumalı kip üst verisi.
- **M08:** sahte yükleyici ve geçici yapıt fikstürleri.
- **F5-B:** önbellek anahtarı girdileri ve ses profili revizyonu.

## 12. Başlatma komutu

```
M03 paketini uygula: docs/execution/packages/W1/M03-yapilandirma-model-kaydi.md.
Kuralları CLAUDE.md'den oku; M01 kanıtını (ve varsa M02 devrini) doğrula.
Mevcut ayarları ve model yükleyicilerini değiştirmeden tipli yapılandırma, bayrak, model,
yapıt, yetenek ve ses profili kaydını ekle; hiçbir model yükleme veya ağ erişimi yapma.
CR01–CR48'i çalıştır, M03-G00…G13'ü değerlendir, paket/M03 dalında PR aç ve dur.
```
