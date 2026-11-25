# F4-A — Tek geçişli normalizasyon ve sentez planı

> F3'ün anlamsal yanıtını alır; korumalı öbekleri (fiyat, tarih/saat, model kodu, motor tanımı, plaka) güvenle tarar; mevcut Türkçe normalizasyon, otomotiv kısaltma ve morfoloji kurallarını **tek bir giriş noktasından, tam bir kez** uygular; M05 onaylı telaffuz varyantlarını bağlar; gerçek FreyaTTS sözcük dağarcığıyla uyumu kontrol eder; korumalı öbekleri bölmeden parçalara ayırır ve değiştirilemez bir M01 `SynthesisPlan` üretir. Yeni G2P, vurgu veya prozodi algoritması eklenmez (F4-B/F4-C).

| Alan | Değer |
| --- | --- |
| Kimlik | F4-A |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, F3-A, M05 |
| Sonraki | F5-A, W2_GATE, F4-B |
| Bayrak | `f4_pipeline_v2` (varsayılan kapalı) |
| Ortam | CPU (model yüklenmez; sözcük dağarcığı yalnızca dosya üst verisinden) |
| Eski görevler | F4-T03, F4-T07, F4-T08, F4-T09, F4-T10, F4-T11, F4-T12, F4-T25, F4-T28 |
| Kaynak | Bundle `W2/Freya_2_0_F4_A_Agent_Implementation_Package.md`; [F4 spec](../../../stages/F4-linguistic-frontend/spec.md), [F4 tasks](../../../stages/F4-linguistic-frontend/tasks.md) |
| Durum | NOT_RUN |

## 1. Amaç

PoC'ta metin `text.py`, `automotive_frontend.py` ve sentez yolunda farklı yerlerde, bazen iki kez normalize ediliyor; tek bir karakter (ör. `°`) yanıtı düşürebiliyordu (H01'de geçici düzeltme). Kritik değerlerin (1.250.000 TL, 14:30, 1.6 TDI, P0300) yanlış okunması doğrudan iş hatasıdır. F4-A, **CLAUDE.md kural 8**'in ("normalizasyon F4'te, tek yerde, tek kez") uygulamasıdır.

## 2. Başlamadan önce

- [ ] CORE_GATE, F3-A, M05 kabul edilmiş; onay var.
- [ ] Tüm normalizasyon, parçalama, sözcük dağarcığı ve çağıran yolları envantere alınmış (doğrudan TTS, karşılama, önbellek, toplu yol dahil); her çağrı noktası ve özellik hesaplanmış.
- [ ] Gerçek FreyaTTS checkpoint sözcük dağarcığı üst verisinin konumu biliniyor; yoksa uyumluluk `UNKNOWN/HOLD` (sahte geçiş yok).

## 3. Kapsam

**Yapılacak:** Yanıt kabulü ve tekilleştirme; M03 model/ses/yetenek ve M05 görüntü bağlama; korumalı öbek tarayıcısı; kritik değer koruması ve belirsizlik politikası; tek katı normalizasyon girişi; mevcut sayı/para/tarih/saat/birim kurallarının adaptasyonu; otomotiv tanımlayıcı/kısaltma adaptasyonu; M05 telaffuz bağlama; mevcut morfoloji adaptasyonu; kaynak/normalize/model metin eşlemeleri; güvenli sınırlarla parçalama; sözcük dağarcığı ve kontrol doğrulaması; değiştirilemez `SynthesisPlan`; anlamsal kalite kapısı; atomik teslim; M04; eski kod ve F5 noktası.

**Yapılmayacak:** Fonolojik kurallar, G2P/PER, kalite kapısı ve tersine ayrıştırma genişletmesi (F4-B); heceleme, vurgu, ulama, prozodi profilleri, duraklama planı (F4-C); model yükleme; SSML/pitch/IPA enjeksiyonu (yetenek doğrulanmadan); duraklamanın sese uygulanması (F6).

## 4. Dosyalar

```
backend/linguistic_frontend/
  admission.py  binding.py  atoms.py  critical_values.py  entry.py
  rules_numbers.py  rules_datetime.py  rules_units.py  rules_automotive.py
  lexicon_binding.py  morphology_adapter.py  text_mapping.py  chunker.py
  vocabulary.py  plan_builder.py  quality_gate.py  delivery.py  telemetry.py  legacy_bridge.py
tests/linguistic_frontend/
evidence/F4-A/<run_id>/
```

`text.py`, `automotive_frontend.py` ve `backend/morphology/` silinmez; kurallar adaptörle tek girişten çağrılır.

## 5. Tasarım ve sözleşmeler

### 5.1 Hat

```
DialogueResponse ─► kabul (güvenilir kapsam, tekilleştirme) ─► revizyon sabitleme (M03 ses/model, M05 sözlük)
  ─► korumalı öbek taraması (yarı açık aralıklar, kararlı öncelik)
  ─► TEK normalizasyon geçişi: sayı/para → tarih/saat → birim → otomotiv tanımlayıcı → M05 telaffuz → morfoloji
  ─► kaynak/normalize/model eşlemesi ─► parçalama (korumalı öbek bölünmez)
  ─► sözcük dağarcığı + kontrol doğrulaması ─► SynthesisPlan (değiştirilemez) ─► kalite kapısı ─► M02 atomik teslim ─► F5
```

- Geçiş içindeki kural aşamalarının sırası kaydedilir; **tam normalizasyon çağrı sayısı = 1** (casus/sayaç testi, LN35–LN36). `normalization_passes = 1` plana yazılır.
- Önceden hazırlanmış güvenilir plan F5 noktasına ikinci normalizasyon olmadan gider; "hazırlandı" iddia eden ham genel çağrı doğrulamayı atlayamaz. Kökeni bilinmeyen eski dizgi yolu için normalizasyon sayısı uydurulmaz (`null`).

### 5.2 Korumalı öbekler ve kritik değerler

| Tür | Örnek | Kural |
| --- | --- | --- |
| Para | `1.250.000 TL`, `2.500,50 TL` | Kesin tutar ve birim; kesir korunur; kayan nokta yuvarlaması yok |
| Saat / tarih | `14:30`, geçerli tipli tarih | Kesin anlamsal değer; belirsiz tarih tahmin edilmez; yetkili çözüm yoksa göreli tarihten takvim günü uydurulmaz |
| Motor / model kodu | `1.6 TDI`, `ID.4`, `C4`, `T10X` | Tipli ayrı değerler; `1.6` ≠ `1.5`; harf-rakam kodu genel sayıya zorlanmaz |
| Arıza kodu | `P0300` | Baştaki sıfırlar dahil aynen |
| Telefon / plaka benzeri | sentetik | Rakam kaybı yok; kimlik çıkarımı yok |
| İşaretli ondalık, sıcaklık, yüzde, aralık, birim | `−5 °C`, `%20`, `10–12 km` | İşaret, hassasiyet, uç noktalar, birim korunur |

Örtüşmelerde (tutar+para birimi, model+sayı) açık öncelik ve üst-alt eşlemesi. Desteklenmeyen kritik sayı/aralık → ret veya F3'e güvenli yeniden sorma; keyfi sözcük yok. F3'ün tipli bilgisiyle kaynak metin çelişirse çelişkili iddia normalize edilmez. Tarayıcı sınırlı çalışır (düşmanca regex girdisine karşı).

Hedef seslendirme örnekleri (vizyon belgesinden; **kabul ölçütü değil**, mevcut kuralların ne ürettiği karakterizasyonla saptanır ve fark F4-B/G4'e gider):

| Ham metin | Hedef |
| --- | --- |
| Peugeot 3008 | Pejo üç bin sekiz |
| Nissan Qashqai | Nissan Kaşkay |
| Citroën C4 | Sitroen Ce dört |
| 1.250.000 TL | Bir milyon iki yüz elli bin Türk lirası |
| 14:30 | Saat on dört otuz |
| 1.6 TDI | Bir nokta altı Te De İ |

### 5.3 Metin temsilleri ve eşleme

`source_text` (F3'ten, değişmez), `normalized_text`, parça başına `model_text`. Uzunluk değiştiren dönüşümler (sayı açılımı, Unicode) için kaynak ↔ normalize ↔ model aralık eşlemesi tutulur. Türkçe I/İ/ı/i yalnızca onaylı yerel ayar mantığıyla. Yer tutucuya benzeyen kaynak dizgi iç işaretlerle çakışmaz.

### 5.4 Sözcük dağarcığı ve kontroller

- Gerçek checkpoint sözcük dağarcığı üst verisi varsa CPU'da kodlanabilirlik kontrolü (kökenle). Yoksa sahte geçiş "uyumlu" sayılmaz → `UNKNOWN/HOLD`.
- Desteklenmeyen glif/kontrol karakteri: açık ret veya onaylı anlam güvenli eşleme. Bilinmeyen jeton filtresi kritik kodu silecekse ret; sessiz kayıp yok.
- Model yetenek revizyonu uyuşmazsa bayat dağarcıkla gönderim yok. Onaysız SSML/pitch/işaretleme enjekte edilmez; IPA desteği bilinmiyorsa rehber `model_text`'e girmez.

### 5.5 Parçalama ve plan

- Sıradan noktalama bölmesinde kaynak sırası ve ayırıcı anlamı korunur. Sınır korumalı öbeğin içine düşerse sınır kaydırılır veya ret; korumalı öbek model sınırından uzunsa açık hata, kırpma yok. Yalnız boşluk içeren konuşma parçası üretilmez. Toplam açılım/parça sayısı sınırlı; kısmi yayın yok.
- `SynthesisPlan` M01 sözleşmesi: gerçek başvurular/revizyonlar/seed; iç içe değiştirilemezlik; sıralı benzersiz parçalar; negatif duraklama/sonlu olmayan hız reddi. Mevcut desteklenen duraklama/hız ipucu yalnızca **istenen** değerdir; sese uygulanmış sayılmaz.
- Leyla varsayılanı seed 9 (M03 kaydından); açık onaylı 42/77/123 aynen; eksik/uyumsuz profil revizyonu → katı gönderim yok.

### 5.6 Teslim

M02 generation kabulü atomik: kabulden önce iptal → gönderim yok; doğrulama ile kuyruğa ekleme arasında iptal → ret; yeni generation eskisini geçersiz kılar; bekleyen hazırlıkla oturum kapanışı → sınırlı temizlik, geç plan yok. İki oturum farklı görüntülerle araya girerse metin, seed veya sözlük sızmaz.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F4-A.01 | Çekirdek/F3/M05 ön kontrolü | Bildirimler, kapı, onay kapsamı | `F4_A_PREFLIGHT.json`; gerçek PASS'e kadar değişiklik yok |
| F4-A.02 | Envanter | Normalizasyon, parçalama, dağarcık ve tüm çağıran yollar | `LINGUISTIC_INVENTORY.json`; her çağrı noktası hesaplanmış |
| F4-A.03 | Sahiplik ve geçiş | Rota geçişi, kapsam, geri dönüş | `CHANGE_SCOPE.json`, `LINGUISTIC_DECISIONS.md`; tek katı yol |
| F4-A.04 | Sözleşme eşlemesi | M01 yanıt/plan ve M02 generation | `RESPONSE_PLAN_MAPPING.csv` |
| F4-A.05 | Güvenilir yanıt kabulü | Tekilleştirme; geçersiz/yanıt yok/bayat yollarda konuşma yok | LN05–LN12 |
| F4-A.06 | Revizyon bağlama | M03 model/ses/yetenek ve M05 görüntü; seed ve kapsam korunur | LN13–LN17 |
| F4-A.07 | Öbek türleri ve tarayıcı | Yerel öbek/eşleme türleri; sınırlı tarayıcı; yarı açık aralıklar, kararlı öncelik | `PROTECTED_ATOM_SPEC.md` |
| F4-A.08 | Kritik değer koruması | Belirsizlik politikası; kritik alanlar sessizce değişmez | `SEMANTIC_VALUE_MATRIX.csv`; LN20–LN34 |
| F4-A.09 | Tek katı normalizasyon girişi | Çağrı grafiği; casus tam bir çağrıyı kanıtlar | `NORMALIZATION_CALL_GRAPH.md`; LN35–LN39 |
| F4-A.10 | Sayı/para/tarih/saat/birim kuralları | Mevcut kuralların adaptasyonu; gözlenen taban çıktıları korunur | `NORMALIZATION_RULE_MATRIX.csv`; LN40–LN45 |
| F4-A.11 | Otomotiv tanımlayıcı/kısaltma | Korumalı model/motor/kod; incelenmemiş yeniden yazma yok | LN20–LN23 |
| F4-A.12 | M05 telaffuz bağlama | Yalnız onaylı/eski kapsam | `LEXICON_MAPPING.csv`; LN46–LN50 |
| F4-A.13 | Mevcut morfoloji adaptasyonu | Mevcut ek davranışı; yeni G2P/vurgu algoritması yok | LN51–LN53 |
| F4-A.14 | Metin eşlemeleri | Kaynak/normalize/model; uzunluk değiştiren dönüşümler izlenir | `TEXT_MAPPING_SPEC.md`; LN65 |
| F4-A.15 | Güvenli sınırlarla parçalama | Mevcut parçalayıcı; korumalı bölme/kırpma yok | `CHUNK_BOUNDARY_SPEC.md`; LN60–LN64 |
| F4-A.16 | Dağarcık ve kontrol doğrulaması | Gerçek Freya dağarcığı ve desteklenen kontroller; model yükleme yok; açık bilinmiyor | `VOCABULARY_COMPATIBILITY.json`; LN54–LN59 |
| F4-A.17 | Değiştirilemez `SynthesisPlan` | Gerçek başvurular/revizyonlar/seed; iç içe değiştirilemezlik | `PLAN_SCHEMA_MAPPING.json`; LN66–LN69 |
| F4-A.18 | Anlamsal/sözleşme kalite kapısı | Bozuk plan, kritik değişiklik veya desteklenmeyen kontroller engellenir | LN43–LN45, LN57 |
| F4-A.19 | Atomik teslim ve temizlik | M02 çiti ve sınırlı kiralar | `DELIVERY_CANCELLATION_SPEC.md`; LN70–LN74 |
| F4-A.20 | M04 telemetri ve güvenli izdüşüm | Konuşma metni/kişisel veri günlüğü yok | `TELEMETRY_MAPPING.csv`; LN75–LN76 |
| F4-A.21 | Eski kod ve F5 katı noktası | Genel kırıcı değişiklik yok; yalnız sahte tüketici | `LEGACY_COMPATIBILITY_MATRIX.csv`; LN77 |
| F4-A.22 | Belirlenimci test paketi | LN01–LN80 yalıtılmış gerçek sonuçlar ve etkilenen önceki testler | Tüm testler çalıştırılmış |
| F4-A.23 | Regresyon, bütünlük, geri dönüş provası | Özellik matrisi, gerçek fark, güvenli geri dönüş kanıtı | LN78–LN79 |
| F4-A.24 | Bağımsız kabul ve devir | F4-A-G00…G19 kanıtı, rapor; F5-A'dan önce dur | LN80; `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| LN01 | Çekirdek kapı kanıtı yok | HOLD; kaynak değişikliği yok |
| LN02 | F3-A veya M05 kabul/hash'i yok | Kesin önkoşulla HOLD |
| LN03 | GPU/ağ/model yükleme casuslarıyla içe aktarma | Ağır başlatma veya I/O yan etkisi yok |
| LN04 | Gerçek M01 sözleşmesi ve alan kimliği | Kabul edilmiş paylaşılan türler; yineleme yok |
| LN05 | Geçerli kabul edilmiş yanıt | Güvenilir kapsamda bir kez kabul |
| LN06 | Bayat tur veya yanlış oturum | Plan gönderimi yok |
| LN07 | "Kabul edildi" iddialı güvenilmeyen ham sözlük | Güvenilir rota olmadan ret |
| LN08 | Yinelenen yanıt, aynı içerik | İkinci generation/konuşma yok |
| LN09 | Yinelenen kimlik, farklı metin | Çakışma; üzerine yazma yok |
| LN10 | Açık "yanıt yok" | Sentez yok; boş konuşma parçası yok |
| LN11 | Boş veya geçersiz Unicode yanıt | Kontrollü hata; sessiz kırpma yok |
| LN12 | Aşırı büyük giriş | Açılımdan önce sınırlı ret |
| LN13 | Planlama sırasında M03 yapılandırması değişir | Sabitlenmiş görüntü tutarlı kalır |
| LN14 | Plan ortasında M05 revizyonu değişir | Eski yetkili görüntü bozulmaz |
| LN15 | Kayıttan Leyla varsayılan profili | Kabul edilmiş tabanda seed 9; ikinci varsayılan yok |
| LN16 | Açık onaylı alternatif seed 42/77/123 | Kesin seed korunur; sessiz geri düşme yok |
| LN17 | Eksik veya uyumsuz profil revizyonu | Katı gönderim yok; açık hata |
| LN18 | Boşluk ve birleşen karakterli kaynak metin | Kesin kaynak korunur |
| LN19 | Türkçe I/İ/ı/i ve Unicode varyantları | Yalnız onaylı yerel ayar mantığı ve eşlemeyle eşleşme |
| LN20 | Kanonik model adı ve noktalama | Öbek aralığı doğru varlığı korur |
| LN21 | Motor tanımı 1.6 TDI ile 1.5 | Ayrı tipli değerler; ikame yok |
| LN22 | ID.4, C4, T10X harf-rakam karışık | Tanımlayıcılar genel sayılara zorlanmaz |
| LN23 | P0300 ve baştaki sıfırlar | Kod anlamsal eşlemede aynen korunur |
| LN24 | Telefon ve plaka benzeri sentetik giriş | Rakam kaybı yok; kimlik çıkarımı yok |
| LN25 | Para 1.250.000 TL | Kesin tutar ve birim |
| LN26 | Para 2.500,50 TL | Kesir korunur; float yuvarlaması yok |
| LN27 | İşaretli ondalık ve negatif sıcaklık | İşaret, hassasiyet politikası ve birim korunur |
| LN28 | 14:30 saati | Kesin anlamsal saat korunur |
| LN29 | Geçerli tipli tarih ile belirsiz tarih | Geçerli eşlenir; belirsiz asla tahmin edilmez |
| LN30 | Yüzde, aralık ve birimler | Büyüklük, uç noktalar ve birim korunur |
| LN31 | Tutar/para birimi ve model/sayı örtüşmesi | Açık öncelik/üst-alt eşlemesi |
| LN32 | İlgisiz bir kelimeye gömülü takma ad alt dizgisi | Kazara değiştirme yok |
| LN33 | Yer tutucuya benzeyen kaynak dizgi | İşaret çakışması veya sızıntı yok |
| LN34 | Aşırı öbek/rakam veya düşmanca regex girdisi | Sınırlı işlem, kontrollü ret |
| LN35 | Standart tek geçişli ham giriş | Tam olarak bir tam normalizasyon çağrısı |
| LN36 | Geçiş içinde birden çok mevcut kural aşaması | Aşama sırası kaydedilir; tam geçiş sayısı bir kalır |
| LN37 | Hazırlanmış güvenilir planın sahte F5 noktasına gitmesi | İkinci normalizasyon çağrısı yok |
| LN38 | Ham genel çağıran "hazırlandı" iddia eder | Doğrulamayı atlayamaz |
| LN39 | Kökeni bilinmeyen eski dizgi yolu | Uydurma katı normalizasyon sayısı yok |
| LN40 | Eski `.strip`/noktalama davranışı | Kabul edilen yerlerde mevcut genel çıktı korunur |
| LN41 | Sayısal kural açılımı ve bitişik noktalama | Kesin kaynak aralık eşlemesi; kayıp sınır yok |
| LN42 | Mevcut normalizasyon altın fikstürleri | Onaylı eski çıktılar değişmez veya belgeli sahip istisnası |
| LN43 | Desteklenmeyen kritik sayı/aralık | Ret veya güvenli F3 yeniden sorma; keyfi sözcük yok |
| LN44 | F3 tipli bilgisi kaynak metinle çelişir | Tutarsız iddia normalize edilmez |
| LN45 | Yetkili çözümü olmayan göreli tarih | Uydurma takvim tarihi yok |
| LN46 | Onaylı M05 telaffuz varyantı | Yalnız doğru kapsamda; kaynak değişmez |
| LN47 | `LEGACY_PRESERVED` varyant | Yalnız mevcut etkin davranış korunur |
| LN48 | `PROPOSED/REJECTED/QUARANTINED` varyant | Etkinleşmez |
| LN49 | Belirsiz M05 takma adı | Kanonik iş bilgisine yükseltme yok |
| LN50 | Sözlükte olmayan terim | Sadık güvenli taban veya açık ret |
| LN51 | Mevcut ek/kesme işareti morfolojisi | Taban kök/ek eşlemesi korunur |
| LN52 | Mevcut morfoloji adaptörü çağrılır | İkinci normalizasyon veya yinelenen ikame yok |
| LN53 | IPA desteği bilinmeyen fonetik rehber | Rehber `model_text`'e enjekte edilmez |
| LN54 | Gerçek checkpoint dağarcık üst verisi mevcut | Kökenle yalnız CPU kodlanabilirlik kontrolü |
| LN55 | Gerçek dağarcık yok, sahte geçer | Gerçek uyumluluk UNKNOWN/HOLD |
| LN56 | Desteklenmeyen glif veya kontrol karakteri | Açık ret veya onaylı anlam güvenli eşleme |
| LN57 | Bilinmeyen jeton filtresi kritik kodu silecek | Ret; sessiz kayıp yok |
| LN58 | Model yetenek revizyonu uyuşmazlığı | Bayat dağarcıkla gönderim yok |
| LN59 | Onaysız SSML, pitch veya işaretleme kontrolü | Desteklenmeyen kontrol enjeksiyonu yok |
| LN60 | Sıradan noktalama bölmesi | Kaynak sırası ve ayırıcı anlamı korunur |
| LN61 | Korumalı öbek içinde parça sınırı | Sınır kayar veya ret; bölme yok |
| LN62 | Gerçek model sınırından uzun korumalı öbek | Açık hata; kırpma yok |
| LN63 | Bölmeden sonra yalnız boşluk parçası | Boş konuşma parçası yok; meşru boşluk izlenir |
| LN64 | Aşırı toplam açılım/parça sayısı | Sınırlı hata; kısmi yayın yok |
| LN65 | Uzunluk değiştiren Unicode ve sayı açılımları | Doğru özgün ve model eşlemeleri |
| LN66 | Tam geçerli plan | Gerçek M01 sözleşmesi; sıralı benzersiz parçalar |
| LN67 | İç içe plan/parça üst verisini değiştirme denemesi | Değiştirilemez; paylaşılan değiştirilebilir takma ad yok |
| LN68 | Negatif duraklama/sonlu olmayan hız | Doğrulama reddeder |
| LN69 | Mevcut desteklenen duraklama/hız ipucu | Yalnız istenen; ses olarak uygulanmış sayılmaz |
| LN70 | Generation kabulünden önce iptal | Generation gönderimi yok |
| LN71 | Doğrulama ile kuyruğa ekleme arasında iptal | Atomik çit bayat sonucu reddeder |
| LN72 | Yeni generation eski planı geçersiz kılar | Eski plan teslim edilmez; dirilme yok |
| LN73 | Bekleyen hazırlıkla oturum kapanışı | Sınırlı temizlik; geç plan yok |
| LN74 | Farklı görüntülü iki oturum araya girer | Oturumlar arası metin, seed veya sözlük sızıntısı yok |
| LN75 | Özel sentetik işaretli güvenli hata | Günlük/metrikte hassas yük yok |
| LN76 | M04 olay kuyruğu taşması/hatası | Atlama veya sahte sonuç yok; sınırlı gözlem |
| LN77 | Eski doğrudan TTS/karşılama/önbellek/toplu yollar | Taban genel davranışı; katı kapsam doğru sınıflanmış |
| LN78 | Gerçek F3 yanıtı → gerçek F4 → sahte F5 | Tek geçiş; değiştirilemez `model_text` ve başvurular değişmez |
| LN79 | Etkilenen temel/özellik regresyonu ve geri dönüş | Açıklanamayan regresyon yok; onaylı geri alınabilir fark |
| LN80 | Kabul kanıtı ve eksik test enjeksiyonu | Eksik/HOLD/NOT_RUN zorunlu kanıt için PASS yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F4-A-G00 | Ön kontrol | Çekirdek kapı + F3-A/M05 kabul kanıtı, onay; LN01–LN02 |
| F4-A-G01 | Tek sahip | Tek katı normalizasyon sahibi, onaylı kapsam, güvenli içe aktarma; envanter/LN03 |
| F4-A-G02 | Sözleşme | Gerçek M01 yanıt/plan ve M02 sözleşmeleri; LN04–LN12 |
| F4-A-G03 | Revizyonlar | Sabitlenmiş M03/M05 ve ses/seed revizyonları; LN13–LN17 |
| F4-A-G04 | Kaynak | Değiştirilemez kaynak ve doğru Unicode aralıkları; LN18–LN19, LN65 |
| F4-A-G05 | Korumalı değerler | Korumalı tanımlayıcılar ve değerler; LN20–LN34 |
| F4-A-G06 | Tek geçiş | Gerçek çağrı grafiği kanıtıyla tam bir normalizasyon geçişi; LN35–LN39 |
| F4-A-G07 | Mevcut kurallar | Mevcut Türkçe kurallar ve anlamsal bilgiler korunmuş; LN40–LN45 |
| F4-A-G08 | Sözlük kapsamı | M05 onaylı varyant kapsamı; LN46–LN50 |
| F4-A-G09 | Morfoloji | Taban morfoloji ve G2P/kontrol ayrımı; LN51–LN53 |
| F4-A-G10 | Dağarcık | Gerçek dağarcık/yetenek uyumu; LN54–LN59; gerçek dağarcık zorunlu |
| F4-A-G11 | Parçalama | Parça sınırları, kaynak eşlemeleri, korumalı bölme yok; LN60–LN65 |
| F4-A-G12 | Plan | Değiştirilemez plan, geçerli ipuçları ve seed; LN66–LN69 |
| F4-A-G13 | Teslim | M02 atomik kabul, temizlik ve bayat ret; LN70–LN74 |
| F4-A-G14 | Gözlem | M04 güvenli gözlem, M07 veri sınırı; LN75–LN76 |
| F4-A-G15 | Uyum | Eski API/rota/özellik davranışı ve katı kapsam; LN77, özellik matrisi |
| F4-A-G16 | Uçtan uca | Gerçek F3 üreticisi → gerçek F4 → kaydeden sahte F5; LN78 |
| F4-A-G17 | Test kanıtı | LN01–LN80 zorunluların tamamı gerçek kanıtla; LN80 |
| F4-A-G18 | Regresyon | Etkilenen regresyon, bütünlük ve geri dönüş provası; LN79 |
| F4-A-G19 | Devir | Bağımsız inceleme, aşağı akış devri ve açık sınırlamalar |

## 9. Kanıt

`evidence/F4-A/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F4_A_PREFLIGHT.json`, `LINGUISTIC_INVENTORY.json`, `CHANGE_SCOPE.json`, `LINGUISTIC_DECISIONS.md`, `RESPONSE_PLAN_MAPPING.csv`, `PROTECTED_ATOM_SPEC.md`, `SEMANTIC_VALUE_MATRIX.csv`, `NORMALIZATION_CALL_GRAPH.md`, `NORMALIZATION_RULE_MATRIX.csv`, `LEXICON_MAPPING.csv`, `TEXT_MAPPING_SPEC.md`, `CHUNK_BOUNDARY_SPEC.md`, `VOCABULARY_COMPATIBILITY.json`, `PLAN_SCHEMA_MAPPING.json`, `DELIVERY_CANCELLATION_SPEC.md`, `TELEMETRY_MAPPING.csv`, `LEGACY_COMPATIBILITY_MATRIX.csv`, `TEST_MATRIX.json`. A0 taban ölçümü (eski F4-T03) yapılırsa `data/F4/lab-report-a0-*.json`.

## 10. Geri dönüş

`f4_pipeline_v2=off`: eski metin hazırlama yolu tek aktif. Kural adaptörleri eski modülleri çağırdığı için eski davranış korunur; kod değişiklikleri `git revert` ile geri alınır.

## 11. Devir

- **F5-A:** değiştirilemez `SynthesisPlan` (tek geçiş, `normalization_passes=1`, seed, revizyonlar, parça sırası). F5 metni yeniden normalize etmez.
- **F4-B:** fonolojik kurallar, G2P ve yaklaşık PER, kalite kapısı genişletmesi, 3 000 örneklik küme; aynı tek giriş içinde.
- **F4-C:** heceleme, vurgu, ulama, prozodi profilleri, duraklama planı; F6 duraklamayı uygular.
- **G4:** "hedef seslendirme" tablosunun gerçek akustik doğrulaması (yaklaşık PER, marka/model doğruluğu).

## 12. Başlatma komutu

```
F4-A paketini uygula: docs/execution/packages/W2/F4-A-normalizasyon-plan.md.
Kuralları CLAUDE.md'den oku; CORE_GATE, F3-A ve M05 kabulünü doğrula; tüm normalizasyon çağrı yollarını envantere al.
backend/linguistic_frontend/ altında tek girişli, tek geçişli normalizasyonu ve değiştirilemez
SynthesisPlan üretimini f4_pipeline_v2 arkasında kur; kritik değerleri asla değiştirme.
LN01–LN80'i çalıştır, F4-A-G00…G19'u değerlendir, paket/F4-A dalında PR aç ve dur.
```
