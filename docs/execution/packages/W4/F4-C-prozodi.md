# F4-C — Heceleme, vurgu, klitik/ulama, konuşma eylemi prozodisi ve anlamsal parçalama

> F4-B'nin tek geçişli planına prozodi **niyeti** ekler: söyleniş temeline göre heceleme, incelenmiş kök/ek vurgu önceliği, Sezer kuralı (yalnız uygun sınıfta, istisnalarla), klitik grupları ("mı", "de"), ulama **rehberi**, güvenilir konuşma eylemi ve odak eşlemesi, korumalı grupları bölmeyen anlamsal parçalama, mantıksal sınır başına tek duraklama niyeti ve hız/perde kontrolünün **tek sahibi**. Plan değiştirilemez; F5 yalnız doğrulanmış kontrolü uygular, F6 duraklamayı uygular.

| Alan | Değer |
| --- | --- |
| Kimlik | F4-C |
| Dalga | W4 |
| Öncelik | P1 |
| Önkoşullar | W2_GATE, F4-B |
| Sonraki | F5-C, F6-C |
| Bayrak | `f4_pipeline_v2` + M03 profili `f4.prosody` (`OFF / SHADOW / ENHANCED`; varsayılan OFF) |
| Ortam | CPU (gerçek tokenizer yalnız üst veriden) |
| Eski görevler | F4-T19, F4-T20, F4-T21, F4-T22, F4-T23, F4-T24 |
| Kaynak | Bundle `W4/Freya_2_0_F4_C_Agent_Implementation_Package.md`; [F4 spec](../../../stages/F4-linguistic-frontend/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

"Aracınız hazır mı?" sorusu düz okunursa soru olduğu anlaşılmaz; "Qashqai değil, Juke" yanlış yerden bölünürse anlam değişir; "1.250.000 TL" iki parçaya bölünürse yanlış duyulur. F4-C, Türkçe prozodiyi **güvenli, kanıtlanabilir ve sahiplikleri net** biçimde plana ekler. Gerçek akustik etki ancak G4'te ölçülür; burada yalnız istenen niyet ve doğrulanmış yetenek eşlemesi vardır.

## 2. Başlamadan önce

- [ ] W2_GATE PASS; F4-B kabul edilmiş ve uyumlu soy; onay. F5-C/F6-C yoksa yeni DAG kenarı eklenmez.
- [ ] Mevcut metin, morfoloji, vurgu, parçalayıcı, önbellek ve kodlayıcı/render yolları izlenmiş; mevcut hece/vurgu motoru (varsa) yeniden kullanılır, tek sahip.
- [ ] Kodlayıcıda gizli normalizasyon veya bağımsız duraklama uygulaması varsa çatışma izlenir ve katı yol engellenir.
- [ ] M03 yetenek kanıtı (hız/perde: `DECLARED` mi `VERIFIED` mi) okunmuş.

## 3. Kapsam

**Yapılacak:** Sözleşme ve kabul; temsil ve kaynak eşlemesi; heceleme adaptörü; morfolojik vurgu; Sezer istisnaları; klitik çözümlemesi; ulama rehberi; konuşma eylemi ve odak; korumalı grup kurulumu; anlamsal sınır seçimi; kapsam ve geri düşme; uyarlanır duraklama politikası; yetenek ve kontrol sahipliği; gerçek dağarcık doğrulaması; değiştirilemez plan bütünleşmesi; önbellek ve gizlilik uyumu; M02 yaşam döngüsü; entegrasyon; F5-C/F6-C devri.

**Yapılmayacak:** Duraklamanın veya fade'in sese uygulanması (F6); doğrulanmamış perde/hız kontrolünün modele gönderilmesi; SSML/IPA enjeksiyonu; yeni telaffuz onayı (M05); prozodi kalitesinin akustik iddiası (G4).

## 4. Dosyalar

```
backend/linguistic_frontend/prosody/
  source_map.py  syllabifier.py  stress.py  sezer.py  clitics.py  liaison.py
  speech_act.py  protected_groups.py  chunk_selector.py  coverage.py  pause_policy.py
  control_ownership.py  vocabulary_check.py  plan_integration.py  cache_compat.py  lifecycle.py
config/linguistics/prosody_profiles.json  config/linguistics/stress_exceptions.json
tests/linguistic_frontend/prosody/
evidence/F4-C/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Heceleme ve vurgu

| Fikstür | Beklenen |
| --- | --- |
| araba, kitap, arkadaş, evler, Türkçe | a-ra-ba; ki-tap; ar-ka-daş; ev-ler; Türk-çe |
| Türk | tek birim, doğru çekirdek |
| İncelenmiş uzun/kısa ünlü çifti | ağırlık incelenmiş niceliğe göre; süre çıkarımı yok |
| İncelenmemiş yabancı ünsüz kümesi | çözülmemiş; ünlü ekleme/silme yok |
| Onaylı açılımlı kısaltma | hece sayısı söyleniş temeline göre; kanonik kod korunur |

- Vurgu önceliği: düzenli sınıfta varsayılan son hece (yalnız sınıf içinde, kural kökeniyle); sözcüksel vurgulu kök + nötr ek → kök vurgusu korunur; incelenmiş ön vurgulayıcı ek → önceki hece; fiil olumsuzluk `-mA` ile ad `-mA` ayrı, belirsizse UNKNOWN.
- **Sezer** (yalnız uygun yer adı sınıfında): An-ka-ra (A-H/L deseni) → indeks 0; A-da-na (tümü hafif) → sondan bir önceki (1); İs-tan-bul (ağır sondan bir önceki) → 1. Tek/iki heceli adlarda negatif indeks yok; incelenmiş sözcüksel istisna Sezer adayını geçersiz kılar (köken kaydıyla); incelenmemiş otomotiv markasına zorla Sezer veya yeni telaffuz onayı yok.

### 5.2 Klitik ve ulama

"Aracınız hazır **mı**?" → ana–ilgeç bağı, soru anlamı ve boşluk korunur; "Siz **de** gelir **misiniz**?" → ek-ilgeç ve soru grubu ayrı; "Serviste" → bağlı bulunma eki bağımsız ilgeç değil; "Evdeki" ile ayrı "ki" bağlacı ayrımı. Ana + ilgeç model jeton sınırını aşarsa güvenli yeniden planlama/engel. Ulama yalnız **rehber**: aynı öbekte "bir araç" uygun; cümle duraklamasını aşan ulama yok; tanımlayıcı sınırı veya bilinmeyen yabancı temel → engel/UNKNOWN; seçilen parça sınırına düşen ulama ipucu kaldırılır.

### 5.3 Konuşma eylemi ve odak

Güvenilir F3 `speech_act` → sürümlü niyet kategorisi (bilgi, karşılama, evet/hayır sorusu, ne-sorusu, onay, uyarı). Evet/hayır ile ne-sorusu ayrı kontur; evrensel yükselme kuralı yok. Doğrulanmamış araç adaylı onayda yalnız yetkili soru korunur, onaylı iddia yok. Olumsuz/koşullu uyarıda olumsuzluk ve koşul korunur. Desteklenmeyen/eksik eylem → açık nötr/bilinmiyor politikası. F3'ün fiyat/stok `UNKNOWN` durumu kesin bilgi veya onaya dönüşemez. Tekrarlanan terimde belirsiz odak → güvenli varsayılan. F3-C çoklu niyet ayrı makbuz/kaynakları ayrı kalır. Prozodi profili **istenen** değerdir, uygulanmış değil.

### 5.4 Korumalı gruplar ve parçalama

- Korumalı grup tek parçada: `Peugeot 3008`, `1.6 TDI`, `P0300`, `ID.4`, `1.250.000 TL`, `2.500,50 TL`, `14:30`, `05.06.2027` (saat/tarih içindeki noktalama yasal sınır değil), baştaki sıfırlı telefon/VIN/plaka, işaretli tutar/yüzde/sıcaklık, "Qashqai değil, Juke" olumsuzluk ilişkisi. Örtüşen tipli öbek + ek → yasal birleşme veya tutarsız başvuru reddi.
- Seçim: yasal cümle sınırı zayıf boşluğa tercih edilir; eşit maliyetli seçeneklerde belgeli kararlı eşitlik bozma (tekrar aynı plan); gerçek jeton sayısı + ek karakter sınırı (kod noktası sınırı değil); kodlayıcı sınırını aşan tek grup → güvenli yeniden planlama/engel, kırpma yok; aday sınır bütçesi aşılırsa sınırlı ret (sınırsız karesel döngü yok).
- Kapsam: bitişik parçalardaki ayırıcılar dahil her kaynak/model karakteri **tam bir kez** defterde; boş/yalnız noktalama parçası konuşma parçası olmaz; geliştirilmiş yol yoksa ama taban geçerliyse aynı sert kontrollerden sonra onaylı geri düşme.

### 5.5 Duraklama ve kontrol sahipliği

- Onaylı her mantıksal sınırda **tek** duraklama niyeti; `null` (istek yok) ile açık `0` ayrı; negatif/sonlu olmayan/aşırı duraklama plan yayınından önce reddedilir; toplam duraklama sınırı aşılırsa belirlenimci incelenmiş indirme veya güvenli ret; korumalı öbek/ana–klitik içinde duraklama yok; terminal dolgu ve doğal kuyruk "eklenmiş duraklama" sayılmaz (örnekler F6'nın); mevcut noktalama duraklaması ile aynı sınırdaki açık duraklama → tek sahip, çift etki engellenir.
- Kontrol: `DECLARED` ama `VERIFIED` olmayan perde kontrolü yalnız üst veri (IPA/SSML veya sahte F0 komutu yok). Model hız yeteneği kapsamda doğrulanmışsa hız **F5'e** bir kez atanır, F6'ya aynı hız atanmaz. Yalnız render tarafında doğrulanmış hız → modele hız değişikliği yok, sahip F6. İstenen 0,90 veya 0,93 ve render aralığı 0,94–1,06 → açık desteklenmiyor veya onaylı indirme. Bilinmeyen hız anlamı veya ters çarpan → doğrulanana kadar uygulama yok.
- Gerçek yerel tokenizer yapıtı yoksa zorunlu dağarcık kapısı HOLD (sahte geçiş eşdeğer değil); desteklenmeyen karakter veya gizli tokenizer düşürmesi → açık ret/inceleme.

### 5.6 Plan, önbellek ve yaşam döngüsü

Değiştirilemez plan gönderimden önce bir kez dondurulur: kesin kaynak ve onaylı `model_text`, normalizasyon sayısı 1, sıralı parçalar, seed 9 (veya onaylı deney seed'i), revizyonlar. F5 hazır metni ek normalizasyon olmadan alır. Yalnız F6 duraklaması değiştiyse önbellek isabeti taze zarf ve duraklama üst verisiyle (ham yeniden kullanım yalnız model etkisi yoksa); model uygulamalı hız veya bağlama duyarlı parçalama değiştiyse yeni ham anahtar veya güvenli bypass. Kişisel metinde geliştirilmiş prozodi → paylaşılan önbellek bypass, telemetride kişisel hash yok. Parça araması sırasında/yayından hemen önce iptal → kabul edilmiş bayat plan yok; aynı generation yumuşak duraklat/devam → yeniden planlama/seed/normalizasyon yok; kesin kesme + geç planlayıcı → dirilme yok.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F4-C.01 | Ön kontrol ve soy | Kabul edilmiş çekirdek/W2 ve F4-B kanıtı, onay, kaynak soyu | PC01–PC05 |
| F4-C.02 | Envanter ve sahiplik | Metin, morfoloji, vurgu, parçalayıcı, önbellek ve kodlayıcı/render yolları | PC06–PC08 |
| F4-C.03 | Sözleşmeler ve kabul | M01/M02 kesin türler; kabul edilmiş yanıt ve değiştirilemez sabit kimlik | PC09–PC14 |
| F4-C.04 | Temsil ve kaynak eşlemesi | F4-B eşlemesi; kesin kaynak/model/fonolojik sınırlar, açılımlar | PC15–PC20 |
| F4-C.05 | Heceleme adaptörü | İncelenmiş hecelemeyi söyleniş temelinde; ağırlık, çekirdek, belirsizlik | PC21–PC28 |
| F4-C.06 | Morfolojik vurgu | İncelenmiş düzenli, kök ve ek vurgu önceliği; sözcüksel ile öbek vurgusu | PC29–PC32 |
| F4-C.07 | Sezer istisnaları | Sınıfa özgü nicelik kuralı ve istisna önceliği yalnız yetkili kapsamda | PC33–PC38 |
| F4-C.08 | Klitik çözümlemesi | Ana–ilgeç gruplarını eklerden ayır; anlam ve korumalı grup sınırları | PC39–PC44 |
| F4-C.09 | Ulama rehberi | Uygun bağlı konuşma sınırları; parça seçiminden sonra uzlaştır; yazımı asla değiştirme | PC45–PC48 |
| F4-C.10 | Konuşma eylemi ve odak | Kabul edilmiş F3 enum ve odak → sürümlü niyet kategorileri ve güvenli hız/odak | PC49–PC56 |
| F4-C.11 | Korumalı grup kurulumu | Örtüşen tipli korumalı grupları birleştir; tanımlayıcılar ve kritik anlam korunur | PC57–PC64 |
| F4-C.12 | Anlamsal sınır seçimi | Gerçek jeton ve grup sınırları altında belirlenimci sınırlı seçim | PC65–PC69 |
| F4-C.13 | Kapsam ve geri düşme | Tam bir kez metin kapsamı, ayırıcılar, noktalama ve güvenli taban geri düşmesi | PC70–PC72 |
| F4-C.14 | Uyarlanır duraklama | Mantıksal sınır başına tek sınırlı niyet; null/sıfır ayrımı, terminal | PC73–PC79 |
| F4-C.15 | Yetenek ve kontrol sahipliği | M03 gerçek yetenek kanıtı; istenen/etkin/uygulanan ayrımı | PC80–PC84 |
| F4-C.16 | Gerçek dağarcık doğrulaması | Yerel tokenizer/`char_to_id`, sınırlar, gizli dönüşümler; sahte HOLD | PC85–PC86 |
| F4-C.17 | Değiştirilemez plan bütünleşmesi | Gerçek M01 planı gönderimden önce bir kez dondur; tek normalizasyon, ses ve seed | PC87–PC88 |
| F4-C.18 | Önbellek ve gizlilik uyumu | F5-B gerçek ham kimlik veya güvenli bypass; isabette güncel üst veri | PC89–PC91 |
| F4-C.19 | M02 yaşam döngüsü ve bütçeler | Karşılaştır-ve-yayınla; sınırlı iptal/temizlik; aynı generation devamı ve bayat çit | PC92–PC95 |
| F4-C.20 | Entegrasyon ve kipler | Gerçek kabul edilmiş hat, önceki tüketiciler, fikstür yerel sınırları | PC96–PC97 |
| F4-C.21 | F5-C/F6-C devri | Değiştirilemez davranış revizyonları; uygulanan sahip makbuz beklentisi | PC99 |
| F4-C.22 | PC01–PC100 doğrulama | Tüm belirlenimci vakalar ve kabul edilmiş yukarı akış regresyonu | Tüm testler çalıştırılmış |
| F4-C.23 | Regresyon, geri dönüş, benchmark | Taban korunur; geri dönüş; katmanlı ayrılmış korpus tanımı | PC98, PC100 |
| F4-C.24 | Kabul ve durma | F4-C-G00…G19 bağımsız inceleme; yalnız kanıtla hazırlık; dur | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| PC01 | Çekirdek bildiriminde bir CG kapısı eksik | Kaynak değişikliğinden önce HOLD; eksik kapı kaydedilir |
| PC02 | Tüm A planları var ama W2 WG11 NOT_RUN | HOLD; plan tamlığı asla W2 kabulü değildir |
| PC03 | F4-B uyumsuz kaynak revizyonunda kabul | Soy uzlaştırmasına kadar HOLD; kaynak düzenleme yok |
| PC04 | F5-C ve F6-C yok | Eklenen DAG bağımlılığı yok; kabul edilmiş önceki tüketici noktaları seçilir |
| PC05 | İzlenen ilgisiz kirli dosya | Baytlar korunur ve raporlanır; sıfırlama veya üzerine yazma yok |
| PC06 | Mevcut `TurkishSyllabifier` ve vurgu motoru | Gerçek semboller eşlenir ve yeniden kullanılır; her birinin tek sahibi |
| PC07 | Beyan edilmiş ama hiç çağrılmayan deneysel prozodi bayrağı | Doğru sınıflanır; canlı yetenek iddiası yok |
| PC08 | Kodlayıcıda gizli normalizasyon ve bağımsız duraklama uygulaması | Çatışma izlenir ve katı yol engellenir |
| PC09 | Kabul edilmemiş veya kısmi kökenli `DialogueResponse` | Sentez planı, yeni generation veya araç yan etkisi yok |
| PC10 | Uyuşmayan oturum/tur/generation kapsamı | Planlama veya önbellekten önce ret |
| PC11 | Planlama sırasında sabit sözlük ve yapılandırma değişir | Özgün değiştirilemez görüntü korunur; karışık revizyon yok |
| PC12 | Geçersiz model veya yetenek revizyonu | Katı yetenek HOLD; tahmini revizyon yok |
| PC13 | Bool istenen hız veya NaN süre | Tahsisten önce geçersiz türler reddedilir |
| PC14 | Açık "konuşma yok" yanıtı | Sentetik metin parçası ve GPU gönderimi yok |
| PC15 | NFC ve ayrışık Türkçe harf fikstürleri | Kesin kaynak ofsetleri korunur; kod noktası kaybı yok |
| PC16 | İki kaynak aralığında tekrarlanan "bakım" | Ayrı eşlenmiş jeton kimlikleri; alt dizgi belirsizliği yok |
| PC17 | İncelenmiş özel adda kıvrık ve düz kesme işareti | Kaynak korunur; eşleme ayırıcıları hesaplar |
| PC18 | Çoktan-bire kaynak eşlemeli F4-B kısaltma açılımı | Rehber indeksleri söyleniş temeline; kaynak korunur |
| PC19 | Belirsiz korumalı öbek eşlemesi | Güvenli engel/yeniden planlama; tahmini kaynak veya anlamsal değer yok |
| PC20 | Desteklenmeyen yabancı söyleniş temeli | Açık UNKNOWN; uydurma hece veya model metni yok |
| PC21 | araba, kitap, arkadaş, evler, Türkçe fikstürleri | a-ra-ba; ki-tap; ar-ka-daş; ev-ler; Türk-çe söyleniş temelinde |
| PC22 | Tek ünlülü tek heceli "Türk" | Doğru çekirdekli tam bir çözülmüş birim |
| PC23 | İncelenmiş uzun ünlü ve kısa açık ünlü çifti | Ağırlık incelenmiş niceliğe uyar; süre çıkarımı yok |
| PC24 | İncelenmiş temeli olmayan yabancı ünsüz kümesi | Ünlü ekleme/silme yerine çözülmemiş |
| PC25 | İncelenmiş fonolojik bağlamda ğ | F4-B rehberine uyulur; toptan silme/değiştirme yok |
| PC26 | Onaylı açılımlı söyleniş temelli kısaltma | Hece sayısı temele uyar; kanonik kod korunur |
| PC27 | Morfolojik sınır hece içine düşer | Ayrı indeksler korunur; zorla biçimbirim bölmesi yok |
| PC28 | Aşırı jeton/fonem uzunluğu | Sınırlı ret veya kabul edilmiş güvenli geri düşme; kontrolsüz döngü yok |
| PC29 | İncelenmiş düzenli vurgu sınıfı | Varsayılan son hece yalnız sınıf içinde; kural kökeni kaydedilir |
| PC30 | Nötr ekli sözcüksel vurgulu kök | İncelenmiş kök belirginliği korunur |
| PC31 | İncelenmiş ön vurgulayıcı ek | Kural kabul edilen öncelikle önceki heceyi seçer |
| PC32 | Fiil olumsuzluk `-mA` ile ad `-mA` | Farklı morfolojiye uyulur; belirsiz durum UNKNOWN |
| PC33 | An-ka-ra uygun Sezer H-L deseni | Sınıf kökenli aday birincil indeks 0 |
| PC34 | A-da-na uygun Sezer tümü-hafif deseni | Aday sondan bir önceki indeks 1 |
| PC35 | İs-tan-bul uygun Sezer ağır sondan bir önceki | Aday sondan bir önceki indeks 1 |
| PC36 | Tek/iki heceli adlar ve belirsiz ağırlık | Negatif indeks yok; incelenmiş istisna veya UNKNOWN |
| PC37 | İncelenmiş sözcüksel istisna Sezer adayını geçersiz kılar | İstisna kökenle kullanılır; toptan ad kuralı değil |
| PC38 | İncelenmemiş otomotiv markası ve çelişen çözümlemeler | Zorla Sezer veya yeni telaffuz onayı yok |
| PC39 | "Aracınız hazır mı?" | Ana–ilgeç bağı; soru anlamı ve boşluk korunur |
| PC40 | "Siz de gelir misiniz?" | Ek-ilgeç ve soru grubu ayrı eşlenir |
| PC41 | "Serviste bekliyor." | Bağlı bulunma eki bağımsız ilgeç olarak yanlış sınıflanmaz |
| PC42 | "Evdeki araç" ile ayrı "ki" bağlacı | Ek ve bağlaç ayrılır; kaynak değişmez |
| PC43 | Soru ilgeci artı kişi eki | Kapsam/grup korunur; keyfi vurgu iddiası yok |
| PC44 | Ana ve ilgeç sert model jeton sınırını aşar | Güvenli yeniden planlama/engel; korumalı grubu bozan bölme yok |
| PC45 | İncelenmiş temellerle aynı öbekte "bir araç" | Yalnız uygun rehber; yazım veya ses değişikliği yok |
| PC46 | Cümle duraklaması boyunca ünsüzle biten + ünlüyle başlayan | Engellenir; duraklama ötesi ulama yok |
| PC47 | Tanımlayıcı sınırı veya bilinmeyen yabancı temel | Engel/UNKNOWN; uydurma telaffuz yok |
| PC48 | Aday ulama sonradan seçilen parça sınırına düşer | Geçerli değilse parçalar arası ipucu kaldırılır/düşürülür |
| PC49 | Güvenilir `speech_act` ile nötr bilgi ve karşılama | Belirlenimci istenen profil; uygulanmış değil |
| PC50 | Evet/hayır ile ne-sorusu fikstürleri | Ayrı kontur kategorileri; evrensel yükselme kuralı yok |
| PC51 | Doğrulanmamış araç adaylı onay | Yalnız yetkili soru korunur; onaylı iddia yok |
| PC52 | Olumsuz veya koşullu önermeli uyarı | Olumsuzluk ve koşul korunur; odak eşlenir |
| PC53 | Desteklenmeyen veya eksik `speech_act` enum | Açık eşlenmiş nötr/bilinmiyor politikası; tahmini iş anlamı yok |
| PC54 | F3'ten fiyat/stok durumu UNKNOWN | Kesin bilgi veya onaya dönüşemez |
| PC55 | Tekrarlanan terimde belirsiz odak aralığı | Tahmini vurgu aralığı yok; güvenli varsayılan |
| PC56 | F3-C çoklu niyet ayrı makbuzlar ve kaynak başvuruları | Ayrı sonuçlar ve koşullar korunur; genişleme yok |
| PC57 | Nominal parça hedefi yakınında `Peugeot 3008` | Tüm korumalı grup tek parçada |
| PC58 | `1.6 TDI`, `P0300`, `ID.4` noktalaması | Kod veya ondalık içinde bölme yok; kimlikler kesin |
| PC59 | `1.250.000 TL` ve `2.500,50 TL` | Ondalık, binlik, birim ve söyleniş eşlemesi korunur |
| PC60 | `14:30` ve `05.06.2027` | Saat/tarih içindeki noktalama yasal sınır değil |
| PC61 | Baştaki sıfırlı telefon, VIN ve plaka | Kesin korumalı dizi; yaklaşık/bölme yok |
| PC62 | Negatif tutar, yüzde ve sıcaklık | İşaret ve birim sağlam; ayrılmış işaret yok |
| PC63 | "Qashqai değil, Juke" içeren yan cümle | Olumsuzluk ilişkisi korunur; yanıltıcı bölme yok |
| PC64 | Örtüşen tipli öbek ve bitişik ek | Yasal grup birleştirilir veya tutarsız başvurular reddedilir |
| PC65 | Yasal cümle sınırı ile daha zayıf boşluk | Politika tercihli yasal bölme belirlenimci seçilir |
| PC66 | Birden çok uygulanabilir bölmede aynı maliyet | Belgeli kararlı eşitlik bozma; tekrar aynı plan |
| PC67 | Gerçek tokenizer sınırı kod noktası sınırından farklı | Gerçek jeton sayısı ve ek karakter sınırı kullanılır |
| PC68 | Tek korumalı grup kodlayıcı sınırını aşar | Açık güvenli yeniden planlama/engel; kırpma yok |
| PC69 | Bütçenin ötesinde çok sayıda aday sınır | Sınırlı ret; sınırsız karesel döngü yok |
| PC70 | Bitişik parçalarda boşluk/noktalama ayırıcıları | Defter tüm kaynak/model karakterlerini bir kez kapsar |
| PC71 | Boş veya yalnız noktalama parçası | Yetkisiz konuşma parçası yok; ayırıcılar hesaplanır |
| PC72 | Uygulanabilir geliştirilmiş yol yok ama taban geçerli | Aynı sert kontrollerden sonra yalnız onaylı geri düşme |
| PC73 | Yan cümle/liste/cümle sınırı fikstürü | Onaylı sınır başına tek benzersiz duraklama niyeti |
| PC74 | Null ile açık sıfır | Gerçek sözleşmeye göre istek yok ile sıfır ayrılır |
| PC75 | Negatif, sonlu olmayan veya aşırı duraklama | Plan yayınından önce ret; ses tahsisi yok |
| PC76 | Toplam duraklama sınırı aşıldı | Belirlenimci incelenmiş indirme veya güvenli ret; gizli aşma yok |
| PC77 | Korumalı öbek/ana–klitik iç sınırı | Grup içinde duraklama niyeti oluşturulmaz |
| PC78 | Terminal dolgu ve doğal kuyruk üst verisi | Eklenmiş duraklama diye etiketlenmez; örnekler F6'nın |
| PC79 | Mevcut noktalama duraklaması ve aynı sınırda açık duraklama | Tek sahip; geliştirilmiş yinelenen etki engellenir |
| PC80 | DECLARED ama VERIFIED olmayan perde kontrolü | Yalnız üst veri; IPA/SSML veya sahte F0 komutu yok |
| PC81 | Kapsamda doğrulanmış gerçek model hız yeteneği | F5'e bir kez atanır; F6'ya aynı hız atanmaz |
| PC82 | Yalnız render'da doğrulanmış hız yeteneği | Modele hız değişikliği yok; F6 sahibi kaydedilir |
| PC83 | İstenen 0,90 veya 0,93; render aralığı 0,94–1,06 | Açık desteklenmiyor veya onaylı indirme; sessiz kırpma yok |
| PC84 | Bilinmeyen sağlayıcı hız anlamı veya ters çarpan | Doğrulanana kadar uygulama yok; tahmini dönüşüm yok |
| PC85 | Yerel gerçek tokenizer yapıtı yok | Zorunlu dağarcık kapısı HOLD; sahte geçiş eşdeğer değil |
| PC86 | Desteklenmeyen karakter veya gizli tokenizer düşürmesi | Açık ret/inceleme; sessiz anlam kaybı yok |
| PC87 | Kesin kaynak ve onaylı `model_text`'li değiştirilemez plan | Normalizasyon sayısı 1, sıralı parçalar, seed 9, revizyonlar |
| PC88 | F5 tüketicisi hazır metni alır | Gerçek çağrı casusu ek normalizasyon olmadığını doğrular |
| PC89 | Yalnız F6 duraklaması değiştikten sonra güncel plan önbellek isabeti | Taze zarf ve duraklama üst verisi; ham yeniden kullanım yalnız model etkisi yoksa |
| PC90 | Değişen model uygulamalı hız veya bağlama duyarlı parçalama | Yeni ham anahtar veya güvenli bypass; bayat isabet yok |
| PC91 | Geliştirilmiş prozodili kişisel metin | Paylaşılan önbellek bypass; telemetride kişisel hash yok |
| PC92 | Parça araması sırasında ve yayından hemen önce iptal | Kabul edilmiş bayat plan yok; kendi kaynakları bırakılır |
| PC93 | Aynı generation yumuşak duraklat ve devam | Kesin plan korunur; yeniden planlama, seed, normalizasyon yok |
| PC94 | Kesin kesme ve geç planlayıcı tamamlanması | Dirilme veya bayat gönderim yok; M02 otoritesi korunur |
| PC95 | Kaynak sınırı, yavaş F6 ve iki oturum | Sınırlı sahiplik; oturumlar arası üst veri veya büyüyen kuyruk yok |
| PC96 | Gerçek F4-A/B hattı + mevcut F5 hazır noktası, sahte yerel sınır | Tek normalizasyon; kesin model metni |
| PC97 | OFF/SHADOW/geliştirilmiş, eski altın fikstürler ve enjekte telemetri hatası | Ek konuşma/etki yok; eski çıktılar korunur |
| PC98 | Enjekte hatadan sonra geri dönüş ve önceki kabul edilmiş test doğrulaması | Önceki güvenli bayraklar/revizyonlar ve değişmemiş davranış |
| PC99 | F5-C/F6-C yok ama gerçek önceki devir doğrulanmış | Yalnız sözleşme düzeyi aşağı akış hazırlığı; açık etiket |
| PC100 | Benchmark fikstüründe yinelenen aile veya eksik altın başvuru | Payda kirlenmesi reddedilir |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F4-C-G00 | Aşama ön kontrolü | CG00–CG11 ve WG00–WG11 gerçekten kabul; F4-B soyu ve açık yetki; PC01–PC05 |
| F4-C-G01 | Tek F4 otoritesi | Mevcut sahipler yeniden kullanılmış; yinelenen planlayıcı/normalizasyon/önbellek yok; gerçek çağrı grafiği; PC06–PC08 |
| F4-C-G02 | Sözleşme ve görüntü | Güvenilir kabul edilmiş yanıt, gerçek M01/M02 başvuruları, sabit revizyonlar ve sınırlar; PC09–PC14 |
| F4-C-G03 | Kaynak eşlemesi | Kesin Unicode/açılım/ayırıcı muhasebesi; belirsiz korumalı eşleme yok; PC15–PC20 |
| F4-C-G04 | Heceleme | İncelenmiş temel, çekirdek/ağırlık, açık belirsizlik, sınırlı davranış; PC21–PC28 |
| F4-C-G05 | Morfolojik vurgu | İncelenmiş kök/ek önceliği; koşulsuz son hece vurgusu yok; PC29–PC32 |
| F4-C-G06 | Sezer ve istisnalar | Kısıtlı uygun sınıf; geçersiz kılma/bilinmeyen işlenmiş; keyfi marka kuralı yok; PC33–PC38 |
| F4-C-G07 | Klitik ve ulama | Ana gruplar, ek/ilgeç ayrımı, sınır ötesi desteklenmeyen ulama yok; PC39–PC48 |
| F4-C-G08 | Konuşma eylemi ve odak | Güvenilir anlam sağlam; kontur rehberi akustik iddia edilmez; PC49–PC56 |
| F4-C-G09 | Korumalı gruplar | Tipli değerler ve olumsuzluk/koşul bütünlüğü; kritik bölme yok; PC57–PC64 |
| F4-C-G10 | Anlamsal parçalama | Gerçek jeton sınırları, belirlenimci seçim ve kapsam; kırpma yok; PC65–PC72 |
| F4-C-G11 | Duraklama politikası | Sınırlı, benzersiz mantıksal sınır; yinelenen doğal/açık duraklama yok; PC73–PC79 |
| F4-C-G12 | Yetenek ve sahiplik | M03 doğrulanmış veya yalnız ipucu; tek hız sahibi ve açık desteklenmeyen aralık; PC80–PC84 |
| F4-C-G13 | Gerçek dağarcık | Gerçek yerel yapıt ve tokenizer davranışı okunur; yalnız sahte HOLD; PC85–PC86 |
| F4-C-G14 | Plan ve önbellek | Tek normalizasyon; kesin model metni ve seed; taze zarf; önbellek kimliği veya bypass; PC87–PC91 |
| F4-C-G15 | Çalışma zamanı ve kaynak güvenliği | M02 bayat çiti, aynı generation devamı, sınırlı kaynaklar ve gizlilik; PC92–PC95 |
| F4-C-G16 | Gerçek katmanlar arası bütünleşme | Kabul edilmiş F4/F5 noktası ve güvenli OFF/SHADOW; dış yan etki yok; PC96–PC97 |
| F4-C-G17 | Test kanıtı | PC01–PC100 zorunlular kanıt ve durumla; isteğe bağlı varyantlar açıkça kapsamlı |
| F4-C-G18 | Regresyon ve geri dönüş | Gerçek taban doğrulaması, geri dönüş ve önceden beyan edilmiş benchmark protokolü; PC98–PC100 |
| F4-C-G19 | Bağımsız inceleme ve devir | F5-C/F6-C uyum sözleşmesi, gerçek hazırlık bayrakları, ters bağımlılık yok |

## 9. Kanıt

`evidence/F4-C/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `PROSODY_INVENTORY.json`, `SOURCE_MAP_SPEC.md`, `SYLLABLE_STRESS_MATRIX.csv`, `SEZER_EXCEPTIONS.csv`, `CLITIC_LIAISON_MATRIX.csv`, `SPEECH_ACT_PROFILES.json`, `CHUNK_SELECTION_SPEC.md`, `PAUSE_POLICY.md`, `CONTROL_OWNERSHIP_MATRIX.csv`, `VOCABULARY_COMPATIBILITY.json`, `BENCHMARK_PROTOCOL.md` (ayrılmış katmanlı korpus; vurgu doğruluğu, insan dinleme — G4), `TEST_MATRIX.json`.

## 10. Geri dönüş

`f4.prosody=OFF`: F4-B planı prozodi niyeti olmadan. Profil dosyaları sürümlü; kod `git revert`.

## 11. Devir

- **F5-C:** doğrulanmış model hızı (sahip F5 ise) ve davranış revizyonları; ODE profili karşılaştırması prozodi niyetini değiştirmez.
- **F6-C:** duraklama niyetleri (sınır başına bir), render tarafı hız sahipliği (doğrulanmışsa), birleştirme/WSOLA için sınır bilgisi; F6 her etkiyi **bir kez** uygular ve "uygulandı" makbuzu verir.
- **G4:** prozodi doğallığı ve vurgu doğruluğu yalnız insan dinlemesiyle (MOS/ABX simüle edilmez).

## 12. Başlatma komutu

```
F4-C paketini uygula: docs/execution/packages/W4/F4-C-prozodi.md.
Kuralları CLAUDE.md'den oku; W2_GATE ve F4-B kabulünü doğrula; M03 hız/perde yetenek kanıtını oku.
f4.prosody (varsayılan OFF) altında heceleme, vurgu/Sezer, klitik/ulama rehberi, konuşma eylemi profili, korumalı
anlamsal parçalama ve sınır başına tek duraklama niyetini değiştirilemez plana ekle; doğrulanmamış kontrolü uygulama.
PC01–PC100'ü çalıştır, F4-C-G00…G19'u değerlendir, paket/F4-C dalında PR aç ve dur.
```
