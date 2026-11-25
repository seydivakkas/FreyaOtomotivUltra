# M05 — Ortak otomotiv sözlüğü

> F2 (tanıma), F3 (diyalog) ve F4 (telaffuz) için tek, değiştirilemez, revizyonlu bir otomotiv terim kaydı kurar: kanonik varlıklar, ASR takma adları, korumalı tanımlayıcılar, telaffuz varyantları ve inceleme/onay akışı. Sözlük eşleşmesi yalnızca sözcüksel kanıttır; katalog doğrulaması, fiyat veya yetki değildir.

| Alan | Değer |
| --- | --- |
| Kimlik | M05 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M01, M03 (M02/M04 isteğe bağlı uyum noktaları) |
| Sonraki | CORE_GATE, F2-A, F4-A, F2-B, F4-B |
| Bayrak | Yok — mevcut eşleme ve sözlük varsayılanları korunur; yeni/incelenmemiş girdiler otomatik etkinleşmez |
| Ortam | CPU |
| Eski görevler | F4-T02, F4-T13, F4-T14, F4-T15, F2-T08 |
| Kaynak | Bundle `W1/Freya_2_0_M05_Agent_Implementation_Package.md`; [shared-lexicon](../../../cross-cutting/shared-lexicon.md), [F4 spec](../../../stages/F4-linguistic-frontend/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Otomotiv terim doğruluğu %48 civarında ölçüldü (hedef %95). Bugün aynı marka/model bilgisi STT hotword listesinde, katalogda, `automotive_frontend.py` içinde ve morfoloji verisinde ayrı ayrı tutuluyor. M05 bunları **tek otoriteye** taşır; F2 aday üretimi ve F4 telaffuzu aynı revizyonu okur.

## 2. Başlamadan önce

- [ ] M01 ve M03 kabul edilmiş. M02/M04 varsa sabitleme ve güvenli telemetri noktaları kullanılır; yoksa yokluk açıkça yazılır.
- [ ] Mevcut takma adlar, sözlükler, katalog başvuruları, morfoloji verisi ve tüketicileri envantere alınmış (özellik kimlikleriyle).
- [ ] Kaynak sözlük dosyaları değiştirilmeden okunur; göç **yıkıcı olmayan** bir defterle yapılır.

## 3. Kapsam

**Yapılacak:** Değiştirilemez sözcük kayıtları; güvenli sınırlı yerel yükleyici; eski kayıtların göçü ve çakışma muhasebesi; kanonik dizin ve ilişkiler; Unicode/Türkçe yerel ayar kuralları ve ham aralıklar; ASR takma ad dizini; korumalı tanımlayıcılar; isteğe bağlı fonetik aday arama; çekimli arama (morfoloji adaptörü); telaffuz varyantları; anlık görüntü, revizyon, inceleme ve atomik yayın; F2/F3/F4 adaptörleri.

**Yapılmayacak:** Yeni bağımlılık, embedding modeli, ağ araması, model yükleme/eğitim, DB göçü, yeni genel uç nokta, arayüz. Çağrılardan, transkriptlerden veya model çıktısından otomatik öğrenme. F4 normalizasyon motoru (F4-A'nın işi). Katalog doğrulaması, fiyat/stok (F3).

## 4. Dosyalar

```
backend/shared_lexicon/
  contracts.py  registry.py  source_loader.py  migration.py  validation.py
  canonical_index.py  unicode_normalizer.py  alias_index.py  phonetic_index.py
  inflected_matcher.py  pronunciation.py  technical_terms.py  candidate_search.py
  ambiguity.py  revisions.py  review.py  catalog_adapter.py  asr_adapter.py
  tts_adapter.py  legacy_adapter.py  telemetry.py  config_adapter.py
config/linguistics/
  lexicon_manifest.json   entities.json   aliases.json
  pronunciations.json     technical_terms.json   review_manifest.json
tests/lexicon/
evidence/M05/<run_id>/
```

Veri tek otoritedir ama birden çok dosyaya bölünür (bildirim dosyası hepsini sürümler). Bu, [code-layout.md](../../../01-architecture/code-layout.md)'deki "tek sözlük dosyası" ifadesinin yerine geçer: kural **tek otorite**dir. `backend/linguistic_frontend/automotive_lexicon.py` varsa M05 kaydını okuyan ince bir adaptör olur.

## 5. Tasarım ve sözleşmeler

### 5.1 Değişmez kurallar

1. **Dört ayrı temsil:** kanonik yazım, ASR takma adı, TTS model-güvenli metni ve IPA/fonetik rehberi birbirinden ayrıdır. TTS yazımı iş kayıtlarına geri gönderilmez. IPA/SSML, doğrulanmış yetenek olmadan model girdisine verilmez. Ham transkript ve kaynak ofsetleri korunur.
2. **Eşleşme yalnızca sözcüksel kanıttır.** Kanonik aday; doğrulanmış katalog kaydı, onaylı müşteri bilgisi, fiyat, stok, uyumluluk veya yetki değildir. Bunları yalnızca F3 gerçek katalog sorgusu ve M07 onay/politikası kurar.
3. **Düzenleme mesafesine dayanarak başka araç seçilmez.** Olumsuzluk, miktar, yıl, motor/hacim, donanım, kuşak, kod noktalaması, model numarası, plaka/telefon/tarih sınırları ve bilinmeyen metin korunur. Korumalı tanımlayıcılar muhafazakâr tam/bağlamsal eşleşmeyle bulunur; bulanık yeniden yazma yok.
4. **Takma adlar belirsiz olabilir.** Sınırlı, belirlenimci adaylar kanıtla ve açık belirsizlikle döner; eşitlik ekleme sırasıyla çözülmez. Puanlar sıralama puanıdır, olasılık değildir.
5. **Otomatik öğrenme yok;** içe aktarılan, incelenmemiş veya deneysel girdi otomatik etkinleşmez. Eski eşlemeler kökenleriyle taşınır.
6. **Unicode ve Türkçe:** açık kurallar; kaynak dizgiler korunur. Kimlikleri veya Türkçe harfleri birleştiren gelişigüzel ASCII'ye katlama, NFKC, aksan silme veya küresel küçük harfe çevirme yok (I/İ/ı/i ayrımı korunur). İçe aktarılan kaynaklarda desteklenmeyen/kontrol karakterleri reddedilir.
7. **Revizyon:** içerik parmak izi; zaman damgası, makine yolu, girdi sırası, istek kimliği veya inceleme olayından bağımsız. Yayın atomik; hata son kabul edilmiş görüntüyü etkin bırakır. Oturumlar/sentez planları açık revizyona sabitlenir.
8. **Telemetri:** yalnızca sayılar, süreler, sınırlı kategoriler ve opak revizyon kimlikleri. Ham ASR metni, kullanıcı sorgusu, kullanıcıdan gelen takma ad, telefon, plaka, VIN, ad, ham istisna veya müşteri metninin hash'i yok.
9. Test, sözlük sayısı, akustik doğruluk, telaffuz doğruluğu veya performans uydurulmaz; aşağıdaki örnekler fikstürdür.

### 5.2 Kayıt türleri

| Kayıt | Temel alanlar |
| --- | --- |
| `LexicalEntity` | `entity_id` (kararlı, yeniden kullanılmaz), `entity_type` (`BRAND / MODEL / TRIM / ENGINE / PART / SERVICE / TECH_TERM / OTHER`), `canonical_text`, `display_text`, `parent_id`, `relations`, `catalog_ref` (opak, isteğe bağlı), `source_ref`, `review_status` |
| `AliasRecord` | `alias_id`, `entity_id`, `alias_text`, `match_key`, `scope` (ör. marka içi), `alias_kind` (`ASR_MISHEARING / SPOKEN_FORM / ABBREVIATION / LEGACY`), `source_ref`, `review_status` |
| `ProtectedTermRecord` | `term_id`, `pattern_kind` (`MODEL_CODE / ENGINE_CODE / VIN / PLATE / PHONE / DATE / PRICE / DTC`), tam/bağlamsal eşleşme kuralı, `allowed_transforms` (yok varsayılan) |
| `PronunciationVariant` | `variant_id`, `entity_id`, `model_text` (TTS'e gidecek güvenli metin), `ipa_hint` (yalnız rehber), `required_capability`, `scope`, `review_status` (`APPROVED / LEGACY / STAGED / REJECTED`) |
| `LexiconSnapshot` | `lexicon_revision`, bildirim, değiştirilemez dizinler, inceleme bildirimi başvurusu, doğrulama durumu |
| `LookupResult` | `raw_span` (yarı açık, Unicode kod noktası), `candidates` (sınırlı, sıralı), `ambiguity` (`NONE / AMBIGUOUS / TRUNCATED / ABSTAIN`), `evidence` (eşleşme türü, puan türü, puanlayıcı sürümü), `lexicon_revision` |

Örnek fikstür (gerçek kayıt iddiası değildir):

```json
{"entity_id":"veh.brand.nissan","entity_type":"BRAND","canonical_text":"Nissan",
 "aliases":[{"alias_text":"nisan","alias_kind":"ASR_MISHEARING","scope":"vehicle_context_only"}],
 "pronunciations":[{"model_text":"Nissan","review_status":"LEGACY"}]}
```

"nisan" takma adı yalnızca araç bağlamında aday üretir; "nisan ayında" gibi tarih ifadesi korunur (LX30).

### 5.3 Eşleştirme kuralları

- Eşleşme anahtarı yalnızca eşleştirme için normalize edilir (NFC, belgeli kesme işareti varyantları, Türkçe büyük/küçük harf kuralı); kaynak metin ve ofsetler değişmez.
- Sözcük sınırı muhafazakârdır: ilgisiz bir kelimenin içinde eşleşme yok. Çok kelimeli ve örtüşen takma adlarda en uzun geçerli kapsamlı aday; çakışma görünür.
- Model kodları (`ID.4`, `C4`, `T10X`), motor kodları ve hacimler (`1.6` → `1.5` değil) bulanık aramaya girmez.
- Fonetik arama isteğe bağlıdır, sınırlıdır, açıklanabilir ve belirlenimcidir; kesinlik iddiası yok; iş/aday üst sınırı aşılırsa `TRUNCATED`.
- Çekimli arama (ör. "Peugeot'yu", "TDI'lı"): kök ve ek aralıkları ayrı döner; belirsiz ek varsa kesip atmak yerine çekimser kalınır. F4 yeniden yazımı burada tekrarlanmaz; mevcut `backend/morphology/` adaptörle kullanılır.

### 5.4 Revizyon, inceleme ve yayın

İçerik → kanonik bildirim → SHA-256 `lexicon_revision`. İnceleme durumu içerik özetinden ayrı bir bildirimde tutulur (`review_manifest.json`). Yayın: aday görüntü doğrulanır → onaylı ise atomik olarak etkin olur; geçersiz aday son iyi revizyonu bozmaz. Sabitlenmiş revizyonlar saklama sınırı içinde korunur; geri dönüş yalnızca onaylı revizyona. Sözlük onay yetkilisi açık karardır ([master-plan §Açık kararlar](../../master-plan.md#açık-kararlar)); karar verilene kadar `STAGED` girdiler etkinleşmez.

### 5.5 Aşama adaptörleri

| Tüketici | Adaptör çıktısı | Sınır |
| --- | --- | --- |
| F2 | M01 `EntityCandidate` (RAW aralık, sıralama kanıtı, `catalog_status=UNVERIFIED`, `confirmation_status=CANDIDATE`); sınırlı, benzersiz, kapsamlı hotword önerileri | ASR beam/hotword politikasını değiştirmez |
| F3 | Opak katalog başvurusu | Doğrulanmış bilgi, fiyat, stok, uyumluluk veya yetki üretmez |
| F4 | Kapsamlı telaffuz varyantı + `lexicon_revision` | Görüntü ve model metni ayrı; çift normalizasyon yok |
| M03 | Revizyon yayını ve profil noktası | İkinci yapılandırma otoritesi yok |
| M02/M04 | Oturum sabitleme; güvenli telemetri | Yoksa açıkça "yok" |

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M05.01 | Ön kontrol | M00/M01/M03 kabulü ve isteğe bağlı M02/M04 noktaları | Kanıt doğrulandı veya HOLD |
| M05.02 | Kaynak envanteri | Mevcut takma adlar, sözlükler, katalog başvuruları, morfoloji, tüketiciler | `LEXICON_SOURCE_INVENTORY.json`; tüm kaynaklar ve özellik kimlikleri hesaplanmış |
| M05.03 | Kapsam ve tasarım | Tek sahipli tasarım ve göç yaklaşımı | `CHANGE_SCOPE.json`, `LEXICON_DECISIONS.md`; ikinci canlı sözlük yok |
| M05.04 | Kayıt türleri | Değiştirilemez sözcük kayıtları; M01 türlerine adaptör | Tipli doğrulama, M01 türleri kopyalanmamış |
| M05.05 | Güvenli yükleyici | Sınırlı yerel yükleyici ve kaynak kökeni | Geçersiz girdi reddedilir; kaynak baytları değişmez |
| M05.06 | Eski kayıt göçü | Yinelemeler ve çakışmaların muhasebesi | `MIGRATION_LEDGER.csv`; açıklanamayan kayıp veya öncelik kayması yok |
| M05.07 | Kanonik dizin | Kararlı kimlikler, geçerli başvurular, belirlenimci tam arama | LX16–LX17 |
| M05.08 | Unicode ve aralıklar | Türkçe ve kod kuralları açık; ham metin/ofset korunur | LX18–LX24 |
| M05.09 | ASR takma ad dizini | En uzun geçerli aralıklar, çakışma yönetimi | Belirsiz takma ad sessizce çözülmez |
| M05.10 | Korumalı tanımlayıcılar | Teknik terim kaydı | Sayı/kod bozulması yok |
| M05.11 | Fonetik aday arama | Sınırlı, isteğe bağlı | Açıklanabilir, belirlenimci; desteksiz güven iddiası yok |
| M05.12 | Çekimli arama | Morfoloji adaptörü | Kök/ek aralıkları korunur; F4 yeniden yazımı tekrarlanmaz |
| M05.13 | Telaffuz varyantları | Yetenek filtresi | IPA/model metni ayrı; eski varyantlar korunur |
| M05.14 | Revizyon ve yayın | Anlamsal hash, inceleme, atomik yayın | Son iyi korunur, sabitlenmiş revizyonlar, açık etkinleştirme |
| M05.15 | F2 adaptörü | `EntityCandidate` ve hotword arayüzü | M01 aday durumu/kanıtı, sınırlı listeler |
| M05.16 | F3 ve F4 adaptörleri | Katalog başvurusu ve telaffuz | İş yetkisi ve normalizasyon sınırları korunur |
| M05.17 | M03/M02/M04 noktaları | Yapılandırma, sabitleme, güvenli telemetri | Yeni zorunlu bağımlılık veya çalışma zamanı otoritesi yok |
| M05.18 | Testler | LX01–LX56 yalıtılmış | Gerçek sonuç ve kanıt; çıkarım veya gerçek müşteri verisi yok |
| M05.19 | Regresyon ve bütünlük | Özellik regresyonu, kaynak bütünlüğü, geri dönüş | Etkilenen tüm M00 özellikleri izlenmiş; izinsiz fark yok |
| M05.20 | Kabul ve devir | M05-G00…G15, rapor, devir | Tüm zorunlu kapılar PASS veya açık HOLD/FAIL; dur |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| LX01 | Zorunlu önkoşul eksik veya tutarsız | Kaynak değişikliğinden önce HOLD |
| LX02 | Ağ/model/DB kancaları yasaklıyken pasif içe aktarma | İndirme, yükleme, servis çağrısı veya yazma yok |
| LX03 | Mevcut kaynak envanterinin tamlığı | Her ilgili kaynak ve özellik kimliği eşlenmiş |
| LX04 | Değiştirilemez kayıt oluşturma | İç içe kayıtlar etkin dizini değiştiremez |
| LX05 | Yinelenen veya yeniden kullanılan kanonik kimlik | Doğrulama çakışmayı reddeder |
| LX06 | Sarkan üst kayıt, geçersiz ilişki/döngü | Güvenli hatayla reddedilir |
| LX07 | Eksik kaynak kökeni | Yeni etkinleştirmeye uygun değil |
| LX08 | Eski içe aktarma gidiş-dönüşü | Mevcut etkin eşlemeler korunur |
| LX09 | Tam eşdeğer yineleme | Tek etkin eşleme, tüm kökenler saklanır |
| LX10 | Çakışan içe aktarılmış takma ad veya telaffuz | Açık çakışma; sessiz üzerine yazma yok |
| LX11 | Bozuk JSON/CSV veya yinelenen JSON anahtarı | Güvenli ret; özgün kaynak değişmez |
| LX12 | Aşırı büyük kaynak / çok fazla satır | Sınırlı ret; kısmi etkinleştirme yok |
| LX13 | Yol geçişi, dış URL veya sembolik bağ kaçışı | Yetkisiz kaynak açılmadan ret |
| LX14 | UTF-8/BOM ve Windows yolu fikstürü | Belgeli doğru işleme |
| LX15 | Göç defteri muhasebesi | Girdi = hesaplanan kayıtlar; açıklanamayan düşme yok |
| LX16 | Kanonik tam arama | Kararlı kimlik, görüntü metni ve köken |
| LX17 | Kapsamlı marka/model ilişkisi | Markalar arası kazara eşleşme yok |
| LX18 | Türkçe I/İ/ı/i büyük/küçük harf politikası | Belgeli ayrım; kazara katlama yok |
| LX19 | NFC birleşik/ayrışık karakterler | Amaçlanan yerde eşdeğer eşleşme; ham aralık doğru |
| LX20 | Yabancı aksanlar ve açık takma ad | Görüntü korunur; küresel aksan silme yok |
| LX21 | Kesme işareti varyantları | Yalnızca eşleşme anahtarı normalize; kaynak değişmez |
| LX22 | Ham Unicode kod noktası ofsetleri | Çok baytlı karakterlerde doğru yarı açık aralık |
| LX23 | Sözcük sınırı / alt dizgi olumsuz testi | İlgisiz kelime içinde eşleşme yok |
| LX24 | Çok kelimeli ve örtüşen takma adlar | En uzun geçerli kapsamlı aday; çakışma görünür |
| LX25 | Tam takma ad çakışması | Sınırlı alternatifler ve `AMBIGUOUS` |
| LX26 | Bilinmeyen veya katalog dışı terim | Uydurma varlık veya zorla değiştirme yok |
| LX27 | Model kodu rakamları ve noktalama | `ID.4`, `C4`, `T10X` ayrı korunur |
| LX28 | Motor/hacim çakışması | Bulanık arama `1.6`'yı `1.5` yapmaz |
| LX29 | VIN, plaka, telefon, tarih, fiyat, arıza kodu koruması | Genel bulanık yeniden yazma yok |
| LX30 | Olumsuzluk ve komşu sözcükler | Eşleşmeyen içerik değişmez |
| LX31 | İsteğe bağlı fonetik eşleşme | Aday kanıtı ve puanlayıcı sürümü; kesinlik iddiası yok |
| LX32 | Fonetik çakışma / eşitlik | Kararlı sıra, açık belirsizlik |
| LX33 | Aday veya iş üst sınırı | Sınırlı sonuç, açık kırpma, tekil iddiası yok |
| LX34 | Giriş uzunluğu/boş/geçersiz kontrol karakterleri | Açık sonuç, sınırlı iş |
| LX35 | Kaynak sırası değişince belirlenimcilik | Aynı anlamsal arama ve revizyon |
| LX36 | Kesme işaretli çekimli yabancı marka | Ham kök/ek aralıkları ayrı; yalnız incelenmiş ipucu |
| LX37 | Ekli teknik kısaltma | Kod kimliği ve ek kanıtı korunur |
| LX38 | Belirsiz veya tanınmayan ek | Çekimser; rastgele kesme yok |
| LX39 | Telaffuz varyantı kapsamı ve incelemesi | Onaylı/eski varyant yalnız kapsamında seçilir |
| LX40 | IPA rehberi ile model metni | Ayrı alanlar; desteksiz enjeksiyon yok |
| LX41 | Bilinmeyen/desteklenmeyen model yeteneği | Açık desteklenmiyor/bilinmiyor; sahte doğrulama yok |
| LX42 | İncelenmemiş telaffuz | Etkinleşmez; taban geri düşmesi değişmez |
| LX43 | Anlamsal revizyon belirlenimciliği | Anlamca aynı içerik için kararlı hash |
| LX44 | Anlamlı takma ad/varyant/kural değişikliği | Farklı anlamsal revizyon |
| LX45 | Geçersiz aday görüntü etkinleştirme | Son iyi revizyon korunur |
| LX46 | Eşzamanlı yayın/okuma ve sabitleme | Karışık revizyon veya yerinde değişim yok |
| LX47 | Saklama sınırı ve geri dönüş | Sabitlenmiş revizyon korunur; yalnızca onaylı geri dönüş |
| LX48 | F2 `EntityCandidate` eşlemesi | RAW aralık, sıralama kanıtı, CANDIDATE/UNVERIFIED |
| LX49 | Hotword adayları | Benzersiz, sınırlı, kapsamlı; ASR politikası değişmez |
| LX50 | F3 katalog başvurusu eksik/bayat | Doğrulanmış bilgi, fiyat, stok, uyumluluk veya yetki yok |
| LX51 | F4 telaffuz ve revizyon devri | Görüntü/model metni ayrı; revizyon verilir; çift normalizasyon yok |
| LX52 | M03 yapılandırma ve isteğe bağlı M02/M04 adaptörleri | Kabul edilmiş arayüzler; yokluk açık; ikinci otorite yok |
| LX53 | Telemetriye kişisel/gizli girdi saldırısı | Ham arama dizgisi, müşteri içeriğinden kimlik veya istisna yükü yok |
| LX54 | Eski API, arayüz biçimi ve özellik regresyonu | Varsayılan bayraklarla mevcut davranış korunur |
| LX55 | Sentetik fikstürle sınırlı iş yükü | Gerçek CPU süreleri/sayıları; sınırlı kayıt ve aday; GPU işi yok |
| LX56 | Son bütünlük, kanıt ve geri dönüş | Yalnızca izinli değişiklik; tüm kapılar izlenebilir; sahte PASS yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M05-G00 | Ön kontrol | M00/M01/M03 kabul zinciri; M02/M04 uyum durumu belgeli |
| M05-G01 | Tek otorite | Tek yetkili sözlük kaydı, pasif içe aktarma, kapsamlı değişiklik; envanter ve kapsam |
| M05-G02 | Kayıtlar | Kanonik kayıtlar, kararlı kimlikler ve köken doğrulanmış; LX04–LX07 |
| M05-G03 | Göç | Eski kaynaklar tamamen hesaplanmış; sessiz kayıp/üzerine yazma yok; göç defteri |
| M05-G04 | Unicode | Unicode ve ham aralıklar doğru, muhafazakâr sözcük sınırları; LX18–LX24 |
| M05-G05 | Belirsizlik | Takma ad belirsizliği, sınırlı arama ve belirlenimci sıralama; LX25–LX35 |
| M05-G06 | Korumalı tanımlayıcılar | Yapılı tanımlayıcılar ve eşleşmeyen anlam korunur; LX27–LX30 |
| M05-G07 | Çekim ve telaffuz | Çekimli arama ve telaffuz yetenekleri güvenli; LX36–LX42 |
| M05-G08 | Revizyon | Değiştirilemez revizyon, onaylı etkinleştirme, sabitlenmiş okuma, saklama ve geri dönüş; LX43–LX47 |
| M05-G09 | F2 sözleşmesi | Aday anlamı ve hotword sözleşmesi; LX48–LX49 |
| M05-G10 | F3/F4 sınırları | F3 katalog yetkisi ve F4 normalizasyon sahipliği; LX50–LX51 |
| M05-G11 | Noktalar ve gizlilik | M03 noktası, M02/M04 uyumu ve gizlilik; LX52–LX53 |
| M05-G12 | Uyum | Etkilenen eski özellikler ve API biçimleri korunmuş; LX54 ve özellik matrisi |
| M05-G13 | Test kanıtı | LX01–LX56 gerçekten çalıştırılmış ve geçmiş; sınırlı iş kanıtı |
| M05-G14 | Bütünlük | Bütünlük karşılaştırması ve güvenli geri dönüş; izinsiz düzenleme yok; LX56 |
| M05-G15 | Devir | Teslimatlar, izlenebilir kanıt ve aşağı akış devri tam; sahte hazırlık yok |

## 9. Kanıt

`evidence/M05/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `LEXICON_SOURCE_INVENTORY.json`, `CHANGE_SCOPE.json`, `LEXICON_DECISIONS.md`, `MIGRATION_LEDGER.csv`, `LEXICON_MANIFEST.json` (revizyon ve kayıt sayıları — gerçek sayım), `TEST_MATRIX.json`, `DOWNSTREAM_HANDOFF.md`. Terim doğruluğu ölçümü bu paketin işi değildir (F2-B/G4).

## 10. Geri dönüş

Göç yıkıcı değildir; eski sözlük dosyaları yerinde kalır. Geri dönüş: adaptörlerin eski kaynağa dönmesi ve M05 commit'lerinin `git revert`'ü. Çalışma zamanında son onaylı `lexicon_revision`'a dönülebilir.

## 11. Devir

- **F2-A / F2-B:** `asr_adapter` ile aday ve hotword; aday puanı ↔ kalibre güven ayrımı.
- **F3-A / F3-B:** `catalog_adapter` opak başvuru; doğrulama F3'te.
- **F4-A / F4-B:** `tts_adapter` ile telaffuz varyantı + revizyon; normalizasyon F4'te tek geçiş.
- **M06:** sözlük CPU işidir; GPU kuyruğuna girmez.
- **Açık karar:** sözlük onay yetkilisi kim? (Karar verilene kadar `STAGED` girdiler etkinleşmez.)

## 12. Başlatma komutu

```
M05 paketini uygula: docs/execution/packages/W1/M05-ortak-sozluk.md.
Kuralları CLAUDE.md'den oku; M01 ve M03 kanıtını doğrula.
Mevcut sözlük kaynaklarını değiştirmeden backend/shared_lexicon/ altında tek, değiştirilemez,
revizyonlu kayda göç et; eşleşmeyi yalnızca sözcüksel aday olarak döndür.
LX01–LX56'yı çalıştır, M05-G00…G15'i değerlendir, paket/M05 dalında PR aç ve dur.
```
