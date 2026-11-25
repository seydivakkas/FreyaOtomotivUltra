# F4-B — Türkçe morfoloji, fonoloji, G2P rehberi ve telaffuz varyantları

> F4-A'nın tek geçişi içine: kaynak hizalı Unicode jetonlama, mevcut morfoloji çözümleyicisiyle kök/ek ayrımı, çekimli varlık köprüsü (`Peugeot'ya`, `Qashqai'nin`, `DSG'li`), ünlü uyumu ve ünsüz değişimi kuralları (istisnalarla), M05 kapsamlı telaffuz varyantları, kısaltma/model/kod seslendirme stratejileri, sürümlü G2P **rehberi** (model girdisi değil) ve modele güvenli metin üretimi. Kritik değer ve kimlik değişikliği sıfır; ikinci normalizasyon yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F4-B |
| Dalga | W3 |
| Öncelik | P0 |
| Önkoşullar | W2_GATE, F4-A, F2-B, M05 |
| Sonraki | F4-C |
| Bayrak | `f4_pipeline_v2` + M03 profili `f4.morphophonology` (varsayılan kapalı) |
| Ortam | CPU (gerçek yerel sözcük dağarcığı yalnız üst veriden; model yüklenmez) |
| Eski görevler | F4-T16, F4-T17, F4-T18, F4-T26, F4-T30 |
| Kaynak | Bundle `W3/Freya_2_0_F4_B_Agent_Implementation_Package.md`; [F4 spec](../../../stages/F4-linguistic-frontend/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

"Peugeot'ya" doğru okunmalı (ek, markanın **söylenişine** göre: Pejo → -ya), "Qashqai'nin" kimliği korunmalı, "kitabı"nın belirsizliği uydurulmamalı, "hukuku"da zorla yumuşama olmamalı. FreyaTTS fonem girdisini doğrudan desteklemiyorsa G2P çıktısı **rehber** olarak kalır; modele yalnız onaylı, güvenli metin dönüşümü gider. F4-B, Freya'nın Türkçe telaffuzdaki ayırt edici gücünü güvenli biçimde kurar.

## 2. Başlamadan önce

- [ ] CORE_GATE ve W2_GATE PASS; F4-A, F2-B, M05 gerçek uygulama kanıtıyla kabul edilmiş; onay.
- [ ] Normalizasyon/morfoloji/sözlük/kodlayıcı çağrı grafiği ve etkin/deneysel özellikler envanterde; katı yolda gizli `normalize` çağıran kodlayıcı varsa engel (MG06).
- [ ] Mevcut `backend/morphology/` çözümleyicisi ve kuralları okunmuş; yeni kök bulma algoritması yazılmaz, mevcut olan genişletilir.
- [ ] 3 000 örneklik küme (eski F4-T30) sürümlü manifestle; kalibrasyon/test ayrı. Tersine ayrıştırma ve kalite kapısı (eski F4-T26) bu paketin parçası.

## 3. Kapsam

**Yapılacak:** Tek sahipli geçiş ve tek geçiş ekleme noktası; sözleşme eşlemesi; görüntü bağlama; Unicode jetonlama genişletmesi; morfoloji çözümlemesi; çekimli varlık köprüsü; ünlü uyumu; ünsüz değişimi ve sınır kuralları; telaffuz varyantı araması; kısaltma/model/kod stratejileri; G2P rehber alfabesi ve hizalama; modele güvenli gerçekleştirme; korumalı değer genişletmesi; sözcük dağarcığı doğrulaması; plan bütünlüğü; yaşam döngüsü; telemetri; eski kod uyumu; F4-C/F5-B devri.

**Yapılmayacak:** Heceleme, vurgu, ulama, prozodi profilleri, duraklama planı (F4-C); model ağırlığı veya sözcük dağarcığı değişikliği; IPA/SSML'in modele enjeksiyonu (yetenek doğrulanmadan); sözlük girdisi onayı (M05 süreci); akustik doğruluk iddiası (G4).

## 4. Dosyalar

```
backend/linguistic_frontend/morphophonology/
  snapshots.py  tokenize_unicode.py  morphology_bridge.py  inflected_entities.py
  vowel_harmony.py  consonant_rules.py  pronunciation_variants.py  acronym_codes.py
  g2p_guidance.py  model_text_realization.py  protected_values_ext.py
  vocabulary_check.py  plan_integrity.py  lifecycle.py  telemetry.py
config/linguistics/phonology_rules.json   # sürümlü kurallar (M03/M05 revizyonuyla)
tests/linguistic_frontend/morphophonology/
evidence/F4-B/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Tek geçiş içindeki yer

F4-A'nın tek normalizasyon geçişi içinde, sayı/tarih/birim ve otomotiv tanımlayıcılarından **sonra**, parçalamadan **önce**: jetonlama → morfoloji → çekimli varlık → telaffuz varyantı → kısaltma/kod → uyum/ünsüz kuralları → model metni gerçekleştirme → korumalı değer kontrolü → dağarcık doğrulaması. Casus testiyle tam metin çağrısı **bir** kalır (MG83). Çağıranın `already_normalized`/`trusted` bayrağı yetki değildir.

### 5.2 Morfoloji ve çekimli varlıklar

| Fikstür | Beklenen |
| --- | --- |
| `arabalarımızdan` | araba + lar + ımız + dan; özellikler kaynak hizalı |
| `evlerimizde` | ev + ler + imiz + de; doğru özellik sırası |
| `kitabı` (sözdizimsel bağlam yok) | belirtme/iyelik belirsizliği korunur; tek anlam uydurulmaz |
| Ek benzeri harflerle biten bilinmeyen sözcük | bilinmiyor/korunur; koşulsuz kesme yok |
| `Peugeot'ya` (onaylı M05 kökü, önerilen okuma) | kök/ek sınırları bulunur; onaysız okuma etkinleşmez |
| `Qashqai'nin` (onaylı varyant) | kimlik, ilgi hâli adayı ve özgün ek aralığı korunur |
| `DSG'li`, `ABS'nin` | stratejiye özgü ek temeli; keyfi kısaltma açılımı yok |
| `ID.4'ün` | model öbeği aynen; ek yalnız incelenmiş kuralla ayrılır |

F2-B'nin onaylanmamış takma ad adayı, F3'ün yetkili farklı araç bilgisinin üzerine yazılamaz; çelişen tipli değer raporlanır.

### 5.3 Ünlü uyumu ve ünsüz kuralları

- **A uyumu:** son ünlü a/ı/o/u → `a`; e/i/ö/ü → `e` (uygun eklerde). **I uyumu:** dört yollu ı/i/u/ü onaylı kural fikstürüyle. Değişmez/kısmi uyumlu `-ki`, `-yor`, `-ken` ve incelenmiş düzensizler toptan değiştirilmez.
- Yabancı varlıkta uyum, **onaylı söyleniş temeline** göre (ör. fikstürde `Pejo` → `Peugeot'ya`); kaynak değişmez. Son ünlü temeli eksik/çelişkiliyse belirsiz/desteklenmiyor; tahmini ek veya marka değişikliği yok.
- **Ünsüz:** `kitap+ı → kitabı`; `ağaç+da → ağaçta` (ek başı d/t); onaylı c/ç ek alomorfu; `renk+i → rengi` (toptan k→ğ yok); `hukuk+u → hukuku` (zorla yumuşama yok); y/n/s kaynaştırması yalnız dilbilgisel bağlamda. Korumalı özel ad, VIN, arıza kodu, k/t/p/ç ile biten model koduna sıradan kök değişimi uygulanmaz. `ğ` bağlamları ve karışık yabancı sözcükte bağlama özgü incelenmiş rehber veya bilinmiyor; küresel silme yok.

### 5.4 Varyantlar, kısaltmalar, G2P ve model metni

- Varyant durumları: `APPROVED` (tam yerel ayar/model kapsamında, revizyon ve kural kökeniyle; ürün sahibi + iş birimi onayı M05 inceleme bildiriminde kayıtlı — [ADR-X-04](../../../01-architecture/adr/ADR-X-04-sozluk-okunus-onayi.md); ajan `PROPOSED` önerir, onaylamaz), `LEGACY_PRESERVED` (yalnız özgün etkin kapsamında), `PROPOSED/REJECTED/QUARANTINED/RETIRED` (etkinleşmez; sahte gözden geçiren veya akustik durum yok). İki onaylı çelişen varyant → açık belirsizlik. Bilinmeyen otomotiv telaffuzu ve onaylı güvenli geri düşme yoksa → engel/kurtarma; uydurma üretici okuması yok. Yeni sözlük görüntüsü yalnız yeni planları etkiler.
- Kısaltma/kod: ABS, DSG, CVT, TDI için onaylı harf-harf/sözcük kipi; 3008/5008, ID.4/ID.3 kimlik ve sayı korunur; `T10X`, `P0300` harf/rakam sırası ve baştaki sıfırlar; `1.6`/`1.5` yalnız onaylı kesin değer, çözülmemiş kritik anlam engeller; kWh/kW/Nm birim ve değer korunur, dönüşüm yok; incelenmemiş kısaltma açıkça çözülmemiş.
- **G2P rehberi:** sürümlü alfabe, belirlenimci kurallar, grafem/fon hizalaması (bire-çok ve açık sıfır-fon kuralı dahil). Belirsiz yabancı sözcük → `UNKNOWN` veya sınırlı alternatifler. Desteklenmeyen fon simgesi veya sürümsüz rehber → ret; model metnine enjeksiyon yok. Yalnız karakter girdili modelde IPA/SSML rehberi **özel** kalır; kodlayıcıya etiket gitmez.
- **Model metni:** yalnız onaylı `model_text` farklılaşabilir; kaynak/görüntü metni ve kimlik değişmez.

### 5.5 Korumalı değerler ve dağarcık

1.250.000 TL / 2.500,50 TL tam TRY tutarı ve kuruş; negatif sıcaklık/yüzde/ondalık; `05.06.2027` ve `14:30` (geçersiz veya yerel ayara göre belirsiz fikstür reddedilir); baştaki sıfırlı/karışık harfli telefon/plaka/VIN karakter sırası; "Qashqai değil, Juke" karşıtlığı ve çelişen tipli değer → engel; iç içe öbeklerde açık üst-alt eşlemesi; parça sınırında bölme yok; yer tutucu çakışması güvenli. Gerçek yerel sözcük dağarcığı varsa son model metni CPU'da doğrulanır ve yapıt hash'i kaydedilir; yalnız sahte dağarcık varsa fikstür testleri geçebilir ama **katı gerçek dağarcık kapısı HOLD**. Sessiz silme, tahmini ikame, gizli kırpma yok.

### 5.6 Önbellek ve devir

Geliştirilmiş kural değişikliği eski önbellek anahtarında temsil edilmiyorsa güvenli önbellek bypass veya HOLD; bayat katı önbellek yeniden kullanımı yok. F4-C'ye morfoloji/fonoloji üst veri izdüşümü (yalnız üst veri; yeni vurgu/duraklama/hız etkisi yok); F5-B'ye davranış revizyonu (önbellek anahtarı girdisi).

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F4-B.01 | Ön kontrol | Kaynak soyu, gerçek çekirdek/W2 kapısı ve bağımlılık kabulü, onay kapsamı | `F4_B_PREFLIGHT.json`; MG01–MG04 |
| F4-B.02 | Envanter | Normalizasyon/morfoloji/sözlük/kodlayıcı çağrı grafiği; etkin ve deneysel özellikler | Her yol özellik kimliğine eşlenmiş; MG05–MG08 |
| F4-B.03 | Geçiş ve ekleme noktası | Tek sahipli geçiş, açık tek geçiş ekleme noktası; eski sarmalayıcı anlamı ve bayraklar değişmez | `CHANGE_SCOPE.json` |
| F4-B.04 | Sözleşme eşlemesi | M01, M02, M03, M05, F2-B, F3; özel değiştirilemez hizalı kayıtlar; genel şema çatallanması yok | `CONTRACT_MAPPING.csv`; MG09–MG12 |
| F4-B.05 | Görüntü bağlama | Güvenilir yanıt/model/sözlük/ses görüntüleri ve tek kapsamlı planlama kabulü | `SNAPSHOT_BINDING.md`; MG13–MG16 |
| F4-B.06 | Unicode jetonlama | Kaynak hizalı jetonlama; açık kod noktası aralıkları; kesme işareti davranışı | `UNICODE_MAPPING_SPEC.md`; MG17–MG24 |
| F4-B.07 | Morfoloji çözümlemesi | Mevcut çözümleyici; kök/ek özellik dizisi; sınırlı belirsizlik; keyfi gövdeleme yok | `MORPHOLOGY_ANALYSIS_SPEC.md`; MG25–MG32 |
| F4-B.08 | Çekimli varlık köprüsü | M05'e incelenmiş köprü; en uzun tam kök ve güvenli ek çözümlemesi; kimlik değişmez | `INFLECTED_LEXICON_MATRIX.csv`; MG33–MG38 |
| F4-B.09 | Ünlü uyumu | Ünlü özellik tablosu; uygun A/I eki; söyleniş temeli seçimi ve istisnalar | `VOWEL_HARMONY_MATRIX.csv`; MG39–MG44 |
| F4-B.10 | Ünsüz ve sınır kuralları | Sınırlı ünsüz değişimi ve dilbilgisel sınır kuralları; özel ad, kod ve istisnalar korunur | `CONSONANT_RULE_MATRIX.csv`; MG45–MG52 |
| F4-B.11 | Telaffuz varyantları | M05 kapsamlı inceleme ve etkin varyant araması; çakışma, eksik temel ve önerilenler açık | `PRONUNCIATION_VARIANT_MATRIX.csv`; MG53–MG58 |
| F4-B.12 | Kısaltma/model/kod | Mevcut onaylı stratejiler; tahmin yok | `ACRONYM_CODE_MATRIX.csv`; MG59–MG64 |
| F4-B.13 | G2P rehberi | İncelenmiş rehber alfabesi, belirlenimci kurallar, grafem/fon hizalaması, desteklenmiyor durumları; yalnız CPU | `G2P_ALPHABET_SPEC.md`; MG65–MG68 |
| F4-B.14 | Model metni gerçekleştirme | Onaylı politika; rehber ve kodlayıcı metni ayrı; gizli dönüşüm veya kontrol işaretlemesi yok | `MODEL_TEXT_REALIZATION.md`; MG69–MG70 |
| F4-B.15 | Korumalı değer genişletmesi | Tam tipli değerler, kimlik, olumsuzluk; çift gerçekleştirme yok | `PROTECTED_VALUE_MATRIX.csv`; MG71–MG78 |
| F4-B.16 | Dağarcık doğrulaması | Gerçek yerel dağarcık ve desteklenen kontrol/uzunluk anlamı; katı UNKNOWN hata kapalı; yapıtlar değişmez | `VOCABULARY_COMPATIBILITY.json`; MG79–MG82 |
| F4-B.17 | Plan bütünlüğü | Mevcut parçalayıcı ve değiştirilemez plan oluşturucu; tek geçiş enstrümantasyonu; hazır F5 tüketimi | `PLAN_INTEGRITY.md`; MG83–MG86 |
| F4-B.18 | Yaşam döngüsü | M02 atomik kabul ve iptal; sınırlı iş ve temizlik; duraklat/devam asla yeniden normalize etmez | `LIFECYCLE_BUDGET_SPEC.md`; MG87–MG90 |
| F4-B.19 | Telemetri ve gizlilik | M04 en iyi çaba metrikler; ham metin veya müşteriden türetilmiş kimlik yok | `TELEMETRY_PRIVACY.md`; MG91–MG92 |
| F4-B.20 | Eski kod uyumu | Eski etkin kurallar/varsayılanlar; F2 aday sınırı ve F3 kurtarma; F5 hazır girdi; katı kipte atlama yok | `LEGACY_COMPATIBILITY_MATRIX.csv`; MG93–MG94 |
| F4-B.21 | Aşağı akış devri | F4-C morfoloji/fonoloji üst veri izdüşümü ve F5-B davranış revizyonu/önbellek devri; yeni prozodi/önbellek yok | `DOWNSTREAM_HANDOFF.md` |
| F4-B.22 | Belirlenimci testler | MG01–MG96 gerçek F4-B/F4-A/M05 ve diğer kabul edilmiş sahiplerle; yalnız sınırda sahteler | `FIXTURE_MANIFEST.json` |
| F4-B.23 | Regresyon ve geri dönüş | Etkilenen zorunlu önceki testler, regresyon matrisi; yalıtılmış ağaçta geri dönüş provası; gelecek benchmark protokolü | MG95 |
| F4-B.24 | Kabul | F4-B-G00…G19 gerçek sonuçlardan; bağımsız inceleme; F5-B'den önce dur | MG96; `ACCEPTANCE_MATRIX.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| MG01 | Yalnız Markdown planlar, kabul edilmiş çalıştırma kanıtı yok | Ön kontrol HOLD; kaynak değişikliği veya uydurma kabul yok |
| MG02 | Çekirdek kabul ama W2 yok veya WG kapısı FAIL | F4-B yürütmesi engellenir; eksik kanıt ile gözlenen hata ayrılır |
| MG03 | Hepsi yetkili atada kabul; bir korumalı kural noktası değişmiş | Soy farkı ve etkilenen regresyon incelemesi gerekir; yalnız bayat kanıt yetmez |
| MG04 | Doğrudan bağımlılıklar kabul ama onay yok | Uygulama yok; önceki seri paketler sessizce yeni DAG kenarı olarak eklenmez |
| MG05 | Canlı, bayraklı, deneysel ve yalnız beyan edilmiş morfoloji yolları fikstürü | Her yol kökenle sınıflanır; canlı iddiası yok |
| MG06 | Mevcut kodlayıcı katı yolda gizli normalize çağırır | Çağrı grafiği denetimi yinelemeyi bulur; kabul edilmiş nokta düzelene kadar engel |
| MG07 | Mevcut etkin eski varyant ve etkinleşmemiş deneysel varyant | Etkin davranış ve etkinleştirme varsayılanları korunur; ayrı sınıflanır |
| MG08 | Ağ/model/GPU yasak ve yalıtılmış dosya sistemiyle içe aktarma | Pasif içe aktarma; çıkarım/indirme/kalıcı değişiklik yok |
| MG09 | Geçerli kabul edilmiş M01 yanıt ve generation fikstürü | Gerçek paylaşılan türler ve mevcut kompozisyon sahibi; paralel plan yok |
| MG10 | Çağıranın `already_normalized` veya `trusted` bayrağı geçirmesi | Güvenilmeyen yetki reddedilir/yok sayılır; gerçek F4 çağrısı ölçülür |
| MG11 | Bozuk aralık, geçersiz enum, indeks olarak bool veya eksik yanıt kimliği | Açık geçersiz giriş; plan yok |
| MG12 | Dondurulduktan sonra iç içe çözümleme/rehber koleksiyonu değiştirilir | Değişiklik engellenir veya kabul edilmiş görüntüyü etkileyemez |
| MG13 | İşleme sırasında M03/M05 görüntüsü değişir | Sabit tutarlı revizyonlar; karışık varyant yok |
| MG14 | Bilinmeyen model/yetenek veya ses revizyonu | Katı HOLD/ret; geri düşme seed'i veya tahmini yetenek yok |
| MG15 | Leyla seed 9 ve yetkili deney seed'leri 42/77/123 | Kesin profil/seed korunur; ikame yok |
| MG16 | Aynı kapsamlı, çelişen içerikli yinelenen yanıt | Mevcut M02 tekilleştirme/çakışma anlamı; ikinci plan teslimi yok |
| MG17 | Türkçe `I İ ı i` jetonları | Yerel ayar duyarlı eşleşme; kesin kaynak değişmez; i/ı keyfi birleştirilmez |
| MG18 | NFC ile ayrışık `Citroën` fikstürü | Geçerli eşleşme temsili ve açık kaynak hizalaması; kaynak değişmez |
| MG19 | Onaylı çekimde U+0027 ile U+2019 kesme işareti | Eşdeğer yetkili eşleşme; ayrı harfi harfine ham aralık korunur |
| MG20 | Varlıktan önce emoji veya BMP dışı kod noktası | Doğru Unicode kod noktası ofsetleri; UTF-16/UTF-8 karışıklığı yok |
| MG21 | İki farklı kaynak konumunda tekrarlanan marka | İki ayrı oluşum kimliği; küresel değiştirme yok |
| MG22 | Noktalama, boşluk, CRLF ve bitişik kesme işareti | Kaynak kayıpsız; eşleme ayırıcıları kapsar; yanlış ofset yok |
| MG23 | Örtüşen en uzun korumalı/sözcüksel aralık adayları | Özel/tipli öncelik veya açık çakışma; kazara alt sözcük değişikliği asla |
| MG24 | Düşmanca uzun birleşen dizi veya kalıp benzeri kullanıcı dizgisi | Sınırlı normalizasyon/eşleşme; felaket regex veya eval yok |
| MG25 | `arabalarımızdan` sentetik çözümlenmiş biçim | araba + lar + ımız + dan; beklenen özellikler, kaynak hizalı |
| MG26 | `evlerimizde` sentetik çözümlenmiş biçim | ev + ler + imiz + de; doğru özellik sırası |
| MG27 | Sözdizimsel bağlamsız `kitabı` | Belirtme/iyelik belirsizliği korunur; uydurma tek anlam yok |
| MG28 | Ek benzeri harflerle biten bilinmeyen sözcük | Bilinmiyor/korunur; koşulsuz kesme yok |
| MG29 | Model takma adıyla alt dizgi paylaşan sıradan Türkçe sözcük | Sıradan kalır; kesin jeton sınırı gerekir |
| MG30 | Onaylı parça veya aday sınırını aşan ek zinciri | Açık bütçe/belirsizlik sonucu; kısmi yanlış gerçekleştirme yok |
| MG31 | Geçersiz/bozuk ek dizisi veya dilbilgisi özelliği | Desteksiz yeniden kurma yok; güvenli koruma veya engel |
| MG32 | Aynı kaynak ve sabit kurallarla tekrarlanan çözümleme | Belirlenimci sıra ve kaynak kapsamı; küresel değiştirilebilir durum yok |
| MG33 | İncelenmiş M05 kökü ve önerilen okumalı `Peugeot'ya` | Kök/ek sınırları bulunur; onaysız okuma etkinleşmez |
| MG34 | Onaylı varyantlı `Qashqai'nin` fikstürü | Kimlik, ilgi hâli adayı ve özgün ek aralığı korunur |
| MG35 | Onaylı `DSG'li` ve `ABS'nin` varyantları | Stratejiye özgü ek temeli; keyfi kısaltma açılımı yok |
| MG36 | Onaylı kesme işaretsiz takma ad ile incelenmemiş benzeri | Yalnız incelenmiş kapsamlı eşleşme etkinleşir; bilinmeyen bilinmiyor kalır |
| MG37 | `ID.4'ün` korumalı model fikstürü | Model öbeği aynen; ek yalnız incelenmiş kuralla ayrılır |
| MG38 | F2-B onaylanmamış takma ad adayı ama F3 yetkili farklı araç | F3 kaynağı/bilgileri asla geçersiz kılınmaz; çelişen tipli değerde uyuşmazlık raporlanır |
| MG39 | a/ı/o/u son temelli A uyumu | Uygun test ekinde beklenen `a`; değişmez ekler etkilenmez |
| MG40 | e/i/ö/ü son temelli A uyumu | Uygun test ekinde beklenen `e` |
| MG41 | I uyumu tablosu sekiz ünlü durumu | Onaylı kural fikstürüne göre dört yollu ı/i/u/ü |
| MG42 | Fikstür onaylı söyleniş temeli `Pejo` ile `Peugeot'ya` | Söyleniş temeli yalnız onaylı gerçekleştirmede; kaynak değişmez |
| MG43 | Yabancı varlıkta eksik veya çelişen son ünlü temeli | Belirsiz/desteklenmiyor; tahmini ek veya marka değişikliği yok |
| MG44 | Değişmez/kısmi uyumlu `-ki`, `-yor`, `-ken` ve incelenmiş düzensiz fikstür | Toptan A/I değişimi yok; gerçek morfoloji korunur |
| MG45 | `kitap + ı` onaylı sıradan sözcük testi | Uygun değişimle `kitabı`; kök kimliği korunur |
| MG46 | `ağaç + da` onaylı sıradan sözcük testi | Ek başı d/t kuralıyla `ağaçta` |
| MG47 | Onaylı ek c/ç değişimi fikstürü | Doğru kapsamlı alomorf; küresel c/ç ikamesi yok |
| MG48 | `renk + i` onaylı istisna duyarlı test | `rengi`; toptan k→ğ kuralı yok |
| MG49 | `hukuk + u` onaylı istisna fikstürü | `hukuku`; zorla yumuşama yok |
| MG50 | Yönelme/iyelik/ilgi sınırında y/n/s fikstürleri | Yalnız dilbilgisel bağlamda uygun kaynaştırma; özellik dizisi korunur |
| MG51 | k/t/p/ç ile biten korumalı özel ad, VIN, arıza kodu veya model | Tanımlayıcıya sıradan kök değişimi uygulanmaz |
| MG52 | ğ bağlamları, karışık yabancı sözcük ve mevcut vurgu/hece tabanı | İncelenmiş bağlama özgü rehber veya bilinmiyor; küresel silme yok; mevcut taban korunur |
| MG53 | Kesin yerel ayar/model kapsamında APPROVED varyant | Uygun varyant revizyon ve kural kökeniyle seçilir |
| MG54 | Özgün kapsam içinde ve dışında LEGACY_PRESERVED varyant | Yalnız özgün etkin kapsamda korunur; genişletilmiş etkinleşme yok |
| MG55 | PROPOSED/REJECTED/QUARANTINED/RETIRED varyant | Yeni etkinleşemez; sahte gözden geçiren veya akustik durum yok |
| MG56 | Çelişen iki onaylı varyant | Açık belirsizlik; belirlenimci görüntü sırası kazanan değil |
| MG57 | Bilinmeyen otomotiv telaffuzu ve onaylı güvenli geri düşme yok | Engel/kurtarma; uydurma üretici okuması yok |
| MG58 | İki yetkili plan arasında yeni sözlük görüntüsü yayımlanır | Yeni planlar yeni onaylı varyantı sabitleyebilir; önceki plan değişmez; ayrı revizyon |
| MG59 | ABS, DSG, CVT ve TDI fikstür stratejileri | Kesin onaylı harf/sözcük kipi; sıralı kod birimleri korunur |
| MG60 | Sayısal modeller 3008 ile 5008, ID.4 ile ID.3 | Gerçek model kimliği ve sayısı korunur; bulanık ikame yok |
| MG61 | `T10X` ve baştaki sıfırlı `P0300` fikstürü | Kesin harf/rakam sırası ve sıfırlar korunur |
| MG62 | `1.6 TDI` ile `1.5 TDI` veya ondalık yerel ayar belirsizliği | Yalnız onaylı kesin değer; çözülmemiş kritik anlam engeller |
| MG63 | Tipli bilgilerde kWh, kW, Nm | Birim türü ve değer korunur; dönüşüm/hesaplama yok |
| MG64 | Yarışan harf-harf/sözcük okumalı incelenmemiş kısaltma | Açık çözülmemiş; tahmini açılım yok |
| MG65 | Bilinen fon envanterli incelenmiş sıradan sözcük fikstürü | Belirlenimci rehber, alfabe revizyonu ve kaynak hizalaması |
| MG66 | Bire-çok grafem eşlemesi ve açık sıfır-fon kuralı | Kapsanan hizalı aralıklar ve açık kural kökeni; eksik girdi yok |
| MG67 | Fon eşlemesi belirsiz yabancı sözcük | UNKNOWN veya sınırlı alternatifler; uydurma kesinlik yok |
| MG68 | Desteklenmeyen fon simgesi veya sürümsüz rehber | Rehber/kontrol reddedilir; model metnine enjeksiyon yok |
| MG69 | IPA/SSML rehberli mevcut yalnız-karakter modeli | Rehber özel kalır; kodlayıcıda desteklenmeyen etiket yok |
| MG70 | İncelenmiş model metni izdüşümü görüntü metninden farklı | Yalnız onaylı `model_text` değişir; kaynak/görüntü ve kimlik değişmez |
| MG71 | 1.250.000 TL ve 2.500,50 TL tipli fikstürleri | Kesin TRY tutarı ve kuruş eşdeğeri; float kaybı yok |
| MG72 | Negatif sıcaklık, yüzde, ondalık hassasiyet | İşaret, değer ve birim korunur |
| MG73 | `05.06.2027` tipli tarih ve `14:30` saat | Kesin tarih/saat; geçersiz veya yerel ayara göre belirsiz fikstür reddedilir |
| MG74 | Baştaki sıfırlı veya karışık harfli sentetik telefon/plaka/VIN | Karakter kimliği/sırası korunur; yaklaşık düzeltme yok |
| MG75 | "Qashqai değil, Juke" ve ayrı çelişen tipli değer | Olumsuzluk/karşıtlık korunur; çatışma varlığı değiştirmek yerine engeller |
| MG76 | İç içe tutar+para birimi veya model+ek korumalı öbek | Açık üst-alt eşlemesi; kesin gerçekleştirme sayısı; yineleme yok |
| MG77 | Parça sınırında korumalı aralık bölme adayı | Sınır kayar veya güvenli ret; öbek ortasında bölme yok |
| MG78 | Kullanıcı girdisi eski yer tutucu/işaretle çakışır | Çakışma güvenli; işaret sızıntısı, yineleme veya silme yok |
| MG79 | Gerçek yerel dağarcık mevcut ve kabul edilmiş revizyon | CPU'da kesin son model metni/kodlayıcı yolu doğrulanır; gerçek yapıt hash'i kaydedilir |
| MG80 | Gerçek dağarcık yok, yalnız sahte dağarcık var | Fikstür testleri geçebilir; zorunlu katı gerçek dağarcık kapısı HOLD |
| MG81 | Desteklenmeyen Unicode karakter, kontrol jetonu, gizli kırpma veya bilinmeyen jeton davranışı | Açık güvenli durum; sessiz silme veya tahmini ikame yok |
| MG82 | Etkin checkpoint sınırının üzerinde jeton uzunluğu | Güvenli ret veya onaylı korumalı parça işleme; sessiz kırpma yok |
| MG83 | Morfoloji, sayı ve takma ad aşamalı tek kaynak | Tam bir F4 tam metin çağrısı (casuslar); ikinci tam normalizasyon yok |
| MG84 | Sahte modelle gerçek F5-A hazır noktasına gönderilen geçerli plan | Kesin `model_text`, seed/revizyonlar değişmez; sıfır ek normalize çağrısı |
| MG85 | Son plan değiştirilemez ve F4-C izdüşümü | Yalnız üst veri; yeni vurgu/duraklama/hız etkisi yok; F5-B davranış revizyonu eşlenir |
| MG86 | Eski önbellek anahtarında temsil edilmeyen geliştirilmiş kural değişikliği | Mevcut güvenli önbellek bypass veya HOLD; bayat katı önbellek yeniden kullanımı yok |
| MG87 | Bariyerle çözümleme ile plan yayını arasında M02 iptali | Bayat gönderim yok; geçici alan bir kez bırakılır |
| MG88 | Aynı generation yumuşak duraklat/devam ile kesin kesme | Devamda ek normalizasyon yok; kesilen generation asla diriltilmez |
| MG89 | Farklı sözlük görüntülü araya girmiş iki oturum | Veri/varyant/durum sızıntısı yok; sınırlı istek yerel geçici alan |
| MG90 | Uzun jeton, sınır taşması, zaman aşımı veya kapanış | Sınırlı tamamlanma/ret; sızan kaynak veya kısmi plan yok |
| MG91 | Kaynak, telefon ve sözlük önerilerinde sentetik kişisel veri işaretleri | Günlük, metrik, kanıt veya önbellekte ham metin/telefon/fonem/türetilmiş hash yok |
| MG92 | M04 gözlemcisi dolu/kapalı/hatalı ve bilinmeyen metrikler | En iyi çaba gözlem planı değiştiremez; sahte sıfır veya sahte PASS yok |
| MG93 | Mevcut eski rotalar, deney bayrakları, F3 makbuz duyarlı yanıt | Onaylı taban özellik davranışı korunur; konuşma/iş yetkisi yok |
| MG94 | Sahte yerel sınırlarla gerçek F2-B → F3 → F4-A/B → F5-A hazır tüketici | Tek kaynak otoritesi; aday ile onaylı bilgi ayrımı; korumalı değerler |
| MG95 | Etkilenen önceki testler, kaynak bütünlüğü ve yalıtılmış geri dönüş provası | İzinsiz düzenleme yok; gerçek eski regresyon kanıtı ve geri alınabilirlik |
| MG96 | Eksik/sahte sonuç veya kanıt; tümü geçen fikstür kapı değerlendirmesi | Doğrulayıcı her zorunlu gerçek sonuç ve bağımsız inceleme olmadan hazırlığı reddeder |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F4-B-G00 | Ön kontrol | CG00–CG11, WG00–WG11 ve gerçek doğrudan bağımlılık kabulü; geçerli soy ve onay; MG01–MG04 |
| F4-B-G01 | Tek sahip | Tek F4 kompozisyon sahibi; gerçek envanter ve onaylı eski uyum; MG05–MG10 |
| F4-B-G02 | Sözleşmeler | Paylaşılan sözleşmeler sağlam; değiştirilemez yerel veri; yalnız kabul edilmiş yanıt; MG09–MG12 |
| F4-B-G03 | Görüntüler | M03/M05 görüntüsü, seed/revizyon ve yinelenen kabul güvenliği; MG13–MG16 |
| F4-B-G04 | Unicode | Kaynak koruyan Unicode, sınırlar ve yarı açık aralık doğruluğu; MG17–MG24 |
| F4-B-G05 | Morfoloji | Açık belirsizlikle sınırlı kök/ek çözümlemesi; keyfi gövdeleme yok; MG25–MG32 |
| F4-B-G06 | Çekimli varlıklar | Çekimli M05 araması; varlık ikamesi veya F2 yetki karışıklığı yok; MG33–MG38 |
| F4-B-G07 | Ünlü uyumu | İncelenmiş ünlü uyumu ve istisna işleme; MG39–MG44 |
| F4-B-G08 | Ünsüz kuralları | İncelenmiş ünsüz ve sınır kuralları; korumalı kod güvenliği; MG45–MG52 |
| F4-B-G09 | Telaffuz | Kapsamlı telaffuz incelemesi ve değiştirilemez revizyon etkinleştirmesi; MG53–MG58 |
| F4-B-G10 | Kodlar | Kısaltma, model ve teknik tanımlayıcı gerçekleştirme bütünlüğü; MG59–MG64 |
| F4-B-G11 | G2P | Sürümlü G2P rehberi; desteklenmeyen kontrol veya sahte akustik iddia yok; MG65–MG70 |
| F4-B-G12 | Korumalı değerler | Sıfır kritik değer/kimlik değişikliği; izlenmeyen korumalı öbek kaybı veya bölünmesi yok; MG71–MG78 |
| F4-B-G13 | Dağarcık | Gerçek yerel dağarcık ve kodlayıcı doğrulaması; sessiz desteklenmeyen girdi yok; MG79–MG82 |
| F4-B-G14 | Plan | Değiştirilemez M01 plan, tek tam normalizasyon çağrısı, hazır F5 noktası, güvenli önbellek sınırı; MG83–MG86 |
| F4-B-G15 | Yaşam döngüsü | M02 iptal, sınırlı iş ve oturum yalıtımı; devamda yeniden normalizasyon yok; MG87–MG90 |
| F4-B-G16 | Gizlilik ve entegrasyon | Gizlilik, güvenli gözlem, eski ve gerçek entegre noktalar; MG91–MG94 |
| F4-B-G17 | Test kanıtı | MG01–MG96 gerçek kanıtla; sahte sınırlar açıkça etiketli |
| F4-B-G18 | Regresyon | Önceki zorunlu regresyonlar, M00 kapsamı ve güvenli geri dönüş; izinsiz değişiklik yok; MG95 |
| F4-B-G19 | Devir | Bağımsız inceleme, aşağı akış devri, uydurma kabul yok; MG96 |

## 9. Kanıt

`evidence/F4-B/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json` ve §6'daki tüm şartname/matris dosyaları (`UNICODE_MAPPING_SPEC.md`, `MORPHOLOGY_ANALYSIS_SPEC.md`, `INFLECTED_LEXICON_MATRIX.csv`, `VOWEL_HARMONY_MATRIX.csv`, `CONSONANT_RULE_MATRIX.csv`, `PRONUNCIATION_VARIANT_MATRIX.csv`, `ACRONYM_CODE_MATRIX.csv`, `G2P_ALPHABET_SPEC.md`, `MODEL_TEXT_REALIZATION.md`, `PROTECTED_VALUE_MATRIX.csv`, `VOCABULARY_COMPATIBILITY.json`, `PLAN_INTEGRITY.md`, `LIFECYCLE_BUDGET_SPEC.md`, `TELEMETRY_PRIVACY.md`, `LEGACY_COMPATIBILITY_MATRIX.csv`, `DOWNSTREAM_HANDOFF.md`, `FIXTURE_MANIFEST.json`), `BENCHMARK_PROTOCOL.md` (3 000 örnek; yaklaşık PER, marka/model telaffuz doğruluğu — G4'te), `TEST_MATRIX.json`.

## 10. Geri dönüş

M03 profili `f4.morphophonology` kapatılır: F4-A taban kuralları tek aktif. Kural dosyası sürümlüdür; yeni planlar eski revizyona sabitlenebilir. Kod `git revert`.

## 11. Devir

- **F4-C:** morfoloji/fonoloji üst verisi (kök/ek, hece adayı, ünlü temeli) heceleme, vurgu, ulama ve prozodi için; bu paket hiçbir prozodi etkisi üretmez.
- **F5-B:** davranış revizyonu önbellek anahtarına girer; eski anahtarla uyumsuz önbellek bypass.
- **G4:** normalizasyon doğruluğu ≥ %99, korumalı öbek ihlali = 0, F4 p95 ≤ 50 ms; yaklaşık PER ve marka/model telaffuzu insan/akustik doğrulamayla.

## 12. Başlatma komutu

```
F4-B paketini uygula: docs/execution/packages/W3/F4-B-fonoloji-g2p.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F4-A, F2-B ve M05 kabulünü doğrula; kodlayıcıda gizli normalize var mı denetle.
F4-A'nın tek geçişi içinde morfoloji, ünlü uyumu, ünsüz kuralları, M05 varyantları ve sürümlü G2P rehberini kur;
rehberi modele enjekte etme, kritik değer ve kimliği asla değiştirme, gerçek dağarcık yoksa HOLD.
MG01–MG96'yı çalıştır, F4-B-G00…G19'u değerlendir, paket/F4-B dalında PR aç ve dur.
```
