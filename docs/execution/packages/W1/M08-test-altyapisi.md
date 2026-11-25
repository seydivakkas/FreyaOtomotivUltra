# M08 — Ortak test altyapısı ve çekirdek entegrasyon koşucusu

> Tüm paketlerin kullanacağı güvenli test koşucusunu, sahte saat ve bariyerleri, sentetik ses fikstürlerini, sahte model/GPU/DB/aktarım adaptörlerini, altın senaryo tekrarını, hata enjeksiyonunu, uyum kontrollerini ve kanıt doğrulamasını kurar. Ayrıca [CORE_GATE](CORE_GATE-cekirdek-kapisi.md) koşucusunu hazırlar ama kendiliğinden çalıştırmaz.

| Alan | Değer |
| --- | --- |
| Kimlik | M08 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M00, M01, M02, M04 (M03/M05/M06/M07 isteğe bağlı noktalar) |
| Sonraki | CORE_GATE, F0-A |
| Bayrak | Yok — yalnızca test kodu; üretim davranışı değişmez |
| Ortam | CPU |
| Eski görevler | F5-T07, F0-T01, F1-T01, F2-T03, F3-T02, F4-T01, F5-T02, F6-T01, F0-T29 |
| Kaynak | Bundle `W1/Freya_2_0_M08_Agent_Implementation_Package.md`; [docs/testing](../../../testing/) |
| Durum | NOT_RUN |

## 1. Amaç

Her aşamanın ilk görevi (karakterizasyon testleri) ve sonraki tüm kabul ölçümleri aynı altyapıya dayanmalı: GPU'suz, ağsız, belirlenimci, kişisel verisiz. H01 hermetik test asgarisini kurdu (tembel torch içe aktarma, `gpu/llm/pbx` işaretleri, sahte LLM); M08 bunu tam bir koşucuya, fikstür kaydına ve çekirdek kapı koşucusuna genişletir.

## 2. Başlamadan önce

- [ ] M00, M01, M02, M04 kabul edilmiş; M03/M05/M06/M07 varsa gerçek noktaları kullanılır, yoksa "nokta yok" açıkça sınıflanır (sahte kullanılabilirlik üretilmez).
- [ ] Mevcut tüm test paketleri, koşucular, fikstürler, giriş noktaları, yan etkiler, seçiciler ve kapsam boşlukları envantere alınmış; eski test kimlikleri eşlenmiş.
- [ ] Mevcut pytest/unittest ve (varsa) frontend koşucusu kullanılır; kurulu olmayan araç varsayılmaz.

## 3. Kapsam

**Yapılacak:** Koşucu ve seçim; yalıtım ve temizlik; sahte saat ve bariyerler; fikstür kaydı ve RNG; sentetik ses fikstürleri; sahte VAD/ASR/LLM/TTS; sahte GPU/yoklayıcı/işçi; yalıtılmış DB ve güvenlik fikstürleri; sahte medya ve aktarım; altın senaryo kaydı ve tekrar motoru; hata enjeksiyonu; sözleşme test paketlerinin kaydı (CT/RT/CR/OB/LX/GPU/SEC); özellik regresyon kaydı; API/aktarım/arayüz/DB/yapılandırma uyum kontrolleri; kanıt doğrulama ve durum birleştirme; CORE_GATE planı ve koşucusu.

**Yapılmayacak:** Üretim kodunda davranış değişikliği; arayüz yeniden tasarımı; üretim DB'sine erişim; gerçek model, GPU, Ollama, Asterisk/SIP; ağ; mevcut testleri silme veya yeniden numaralandırma.

## 4. Dosyalar

```
tests/harness/
  runner.py  selection.py  isolation.py  fake_clock.py  barriers.py  fixture_registry.py
  audio_fixtures.py  fake_models.py  fake_resources.py  fake_db.py  fake_security.py
  fake_transport.py  golden_scenarios.py  replay.py  fault_injection.py
  feature_registry.py  compatibility.py  evidence_validator.py  gate_aggregation.py
tests/fixtures/            # sürümlü manifest + seed + SHA-256; ham müşteri verisi yok
tests/golden/              # altın senaryolar
tests/integration/core/    # CORE_GATE vakaları (CI01–CI24)
scripts/run_gate.py        # açık çağrıyla çalışan kapı koşucusu
evidence/M08/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Sahiplik ve sınırlar

M08 test yürütmesinin ve uyum orkestrasyonunun sahibidir. Özellik kimliği M00'ın, sözleşmeler M01'in, çalışma zamanı M02'nin, yapılandırma M03'ün, gözlem M04'ün, sözlük M05'in, GPU M06'nın, güvenlik M07'nin. M08 bunları kopyalamaz; test kompozisyonunda gerçek modülleri sahte sağlayıcılarla birleştirir.

### 5.2 Test seviyeleri

| Seviye | Kapsam | Şu anki yetki |
| --- | --- | --- |
| T0 | Birim ve sözleşme testleri | Her pakette zorunlu |
| T1 | Tekrar ve fikstür testleri (altın senaryolar) | Her pakette zorunlu |
| T2 | Katman benchmark'ı (tek aşama, sentetik veri) | A/B/C paketlerinde; gerçek model gerekiyorsa `@pytest.mark.gpu` |
| T3 | F0–F6 sentetik uçtan uca (sahte model ve gerçek model ayrı raporlanır) | W2_GATE (sahte), G4 (gerçek) |
| T4 | Hata enjeksiyonu ve yük | Sahte: paketlerde; gerçek donanım: G4 |
| T5 | Gerçek kullanıcı ve SIP | Yalnızca G5 |

Sentetik veri kümeleri sabit manifest, seed, SHA-256, beklenen sonuç ve kalibrasyon/değerlendirme ayrımıyla tutulur. Kalibrasyon kümesiyle test kümesi örtüşemez (TH25).

### 5.3 Koşucu ve yalıtım

- Aşamalar: ön kontrol → izin listeli paket seçimi → çalıştırma başına benzersiz sandbox → yalnız testte bağımlılık enjeksiyonu → dış etkilerin engellenmesi → toplama → sınırlı yürütme → çıktının temizlenmesi ve doğrulanması → sahip olunan kaynakların temizliği.
- Profiller: `quick` (değişen sözleşmeler/birim), `package` (seçili paketin zorunlu testleri), `core_integration` (tüm temel zorunlu testler + modüller arası noktalar), `compatibility` (M00 özellik/API/arayüz eşlemeleri).
- Kayıt: gerçek argv, çalışma dizini, koşucu sürümü, seçim, ortam değişkeni **adları** ve güvenli değerler, zaman aşımı, çıkış kodu, bulunan/çalışan/başarısız/atlanan sayıları.
- Boş seçim veya sayı uyuşmazlığı + çıkış 0 → PASS değil (TH09). Atlanan/xfail zorunlu test PASS sayılmaz (TH77).
- Kullanıcının çalışma ağacı değişiklikleri korunur; yıkıcı temizlik yok (TH11). Geçici DB açık yolla; üretim DB'si asla açılmaz (TH12).

### 5.4 Fikstürler

- **Ses:** Analitik sinyallerden küçük belirlenimci PCM16 LE ve Float32 mono fikstürler: sessizlik, dürtü, sinüs, chirp, seed'li beyaz/pembe gürültü, konuşmaya benzer genlik zarfı, motor/fan benzeri gürültü, kırpılmış ve düşük seviyeli sinyaller. "Konuşmaya benzer" fikstür insan konuşması veya bağımsız akustik benchmark olarak sınıflanmaz (TH34).
- **Sahte modeller:** ASR kısmi/kararlı/final revizyonları, ham/normalize/kanonik varyantlar, eksik güven, çakışan adaylar, bozuk ve geç sonuçlar; LLM belirlenimci yapılı öneriler, bozuk yanıt, yetki iddiası/araç enjeksiyonu; TTS geçerli/geçersiz/sırasız parçalar, iptalden sonra geç tamamlanma; VAD betikli başlangıç/bitiş.
- **Sahte kaynaklar:** GPU yoklayıcı (bayat/eksik), asenkron tamamlanma, OOM ve belirsiz tamamlanma; M06 kabul edilmişse gerçek noktası.
- **DB ve güvenlik:** Güvenli kanıtlanmışsa gerçek şema başlatmasıyla, değilse açıkça sınırlı sentetik şemayla geçici SQLite; sahte aktör, sahte sağlayıcı, işlem ve denetim fikstürleri; M07 isteğe bağlı nokta.
- **Aktarım:** AudioSocket çerçeveleme; parçalanmış/birleşmiş TCP okumaları; bağlantı kopması/kısmi yazma/geri basınç; DTMF yinelemesi; oynatma boşaltma ve onay (kuyruk temizlendi ≠ gönderildi ≠ uçta duyuldu); RTP yeniden sıralama/kayıp ayrı simülasyon kipi.
- **Altın senaryolar:** karşılama, randevu ve saat değişikliği, belirsiz araç / boş saat yok, iki oturum. Henüz uygulanmamış F3 davranışı "gelecek — NOT_RUN" olarak işaretlenir.

### 5.5 Durum birleştirme

Zorunlu testlerin doğruluk tablosu: herhangi biri `FAIL` → paket `FAIL`; `FAIL` yok ama `HOLD/NOT_RUN` var → `HOLD`; hepsi `PASS` → `PASS`. İsteğe bağlı vakalar zorunlu sonucu değiştirmez. Sentetik/mock kanıt gerçek uç noktası veya GPU olarak etiketlenemez (TH78); ölçülmemiş değer `null`.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M08.01 | Ön kontrol | Zorunlu kabul edilmiş çalıştırmalar, kapsam, soy, araçlar; belirsizlikte HOLD | Ön kontrol kaydı |
| M08.02 | Mevcut test envanteri | Paketler, koşucular, fikstürler, giriş noktaları, yan etkiler, seçiciler, kapsam boşlukları; eski kimlik eşlemesi | `TEST_INVENTORY.json` |
| M08.03 | Sahiplik ve güvenli yürütme tasarımı | Değişiklik izin listesi, yalıtım modeli, izinler, canlı etki yolu yok, seviye politikası | `HARNESS_DECISIONS.md` |
| M08.04 | Altyapı üst veri sözleşmeleri | `TestCaseSpec`, `FixtureManifest`, `RunManifest`, `CaseResult` (M01/M04 kurallarıyla) | TH74 |
| M08.05 | Koşucu ve seçim | Belirlenimci keşif, açık seçim, sınırlı alt süreç, çıkış/sayı uzlaştırması | TH07–TH10 |
| M08.06 | Yalıtım ve temizlik | Geçici dosya sistemi/DB, dış etki engeli, sahip olunan süreç/görev temizliği | TH11–TH16 |
| M08.07 | Sahte saat ve bariyerler | Enjekte saat, belirlenimci yarışlar, bekçi; üretimde küresel değişiklik yok | TH17–TH20 |
| M08.08 | Fikstür kaydı ve RNG | Sürümlü köken, seed'ler, güvenli hash, sınırlı üretim, veri kümesi bölünmesi | TH21–TH25 |
| M08.09 | Sentetik ses fikstürleri | Geçerli/geçersiz biçimler, tam sayımlar, etiket sınırları, gizlilik | TH26–TH34 |
| M08.10 | Sahte model adaptörleri | Sahte VAD/ASR/LLM/TTS; gerçek sözleşme noktaları; gecikmeli ve geçersiz sonuçlar | TH35–TH43 |
| M08.11 | Sahte kaynak adaptörleri | Sahte GPU/yoklayıcı/işçi ve tamamlanma; kabul edildiyse M06 yeniden kullanımı | TH44–TH47 |
| M08.12 | Yalıtılmış DB ve güvenlik fikstürleri | Geçici DB, sahte aktör/sağlayıcı, işlem ve denetim fikstürleri; M07 noktası | TH48–TH54 |
| M08.13 | Sahte medya ve aktarım | AudioSocket çerçeveleme, sahte oynatma, zaman aşımı/geri basınç, DTMF | TH55–TH60 |
| M08.14 | Altın senaryo kaydı | Sürümlü önkoşullar, anlamsal iddialar, yasak etkiler, gelecek vaka durumu | TH61–TH64 |
| M08.15 | Belirlenimci tekrar motoru | Sıralı senaryo yürütme, iz korelasyonu, tekrar idempotency'si, temizlik | TH65 |
| M08.16 | Hata enjeksiyon motoru | Yalnız testte sınırlı hata planı, bariyerler, erişilemeyen yetenek yolları | TH66–TH67 |
| M08.17 | Sözleşme paketlerinin bütünleşmesi | CT/RT/OB yeniden kullanımı; CR/LX/GPU/SEC kaydı; yineleme yok | TH74 |
| M08.18 | Özellik regresyon kaydı | M00 özellikleri, test kimlikleri, etkilenen değişiklikler, beklenen davranış, kapsam kararları | TH68–TH70 |
| M08.19 | API ve aktarım uyumu | Mevcut rota, şema, tel protokolü ve eski istemci kontrolleri | TH71 |
| M08.20 | Arayüz, DB ve yapılandırma uyumu | Statik ve çalıştırılabilir kontroller ayrı kapsamda; arayüz tasarımı veya üretim DB'si yok | TH72–TH73 |
| M08.21 | Kanıt doğrulama ve kabul | Güvenli raporlar, şema/durum doğrulaması, hash'ler, zorunlu kapı birleştirme | TH75–TH79 |
| M08.22 | Çekirdek entegrasyon kapısı | Ayrı M00–M08 entegrasyon planı, gerçek modül noktaları, kapı koşucusu; otomatik çağrı yok | TH80; [CORE_GATE](CORE_GATE-cekirdek-kapisi.md) vakaları yazılmış |
| M08.23 | Altyapı doğrulaması | TH01–TH80 güvenli testler; izinli özgün zorunlu paketler; erişilemeyen isteğe bağlı noktalar sınıflanmış | Tüm testler çalıştırılmış |
| M08.24 | Regresyon, geri dönüş, devir | M08-G00…G19, kapsam bütünlüğü, bağımsız inceleme, CORE_GATE talimatı, F0-A devri; dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| TH01 | Kabul edilmiş M00 yok | Koşucu üretim içe aktarmalarından önce engeller; HOLD ve eksik kanıt raporu |
| TH02 | M01/M02/M04 raporu PASS diyor ama kapı eksik | Eksik önkoşul reddedilir |
| TH03 | Çakışan kabul edilmiş çalıştırma adayları | Zaman damgasına göre seçim yok; HOLD ve açık soy istenir |
| TH04 | Onaylı artımlı kaynak değişikliği ile açıklanamayan sapma | Yalnız uzlaştırılmış soy kabul; sapma engeller |
| TH05 | M03/M05/M06/M07 isteğe bağlı noktası yok | Altyapı çalışabilir; gerçek entegrasyon HOLD; uydurma kullanılabilirlik yok |
| TH06 | Altyapı modüllerinin içe aktarılması | Model yükleme, CUDA, sağlayıcı çağrısı, arka plan servisi veya üretim dosyası yazma yok |
| TH07 | Mevcut koşucu keşfi | Eski testler toplanmaya devam eder; kararlı düğüm kimlikleri silinmeden eşlenir |
| TH08 | Bilinmeyen paket veya koşucu seçicisi | İzin listesi dışı seçim ve kabuk enjeksiyonu reddedilir |
| TH09 | Sayı uyuşmazlığı veya çıkış 0 ile boş seçim | Kapı PASS değil; gerçek bulunan/çalışan sayılar saklanır |
| TH10 | Koşucu takılır | Sınırlı bekçi; yalnızca sahip olunan iş sonlandırılır; kanıtla FAIL/HOLD |
| TH11 | Kullanıcının mevcut çalışma ağacı değişiklikleri | Baytlar ve durum korunur; yıkıcı temizlik yok |
| TH12 | Yalıtılmış DB yapılandırması | Açık geçici DB yolu; üretim DB'si asla açılmaz |
| TH13 | Dışarıya sağlayıcı denemesi | Testte dış etki engellenir, güvenli neden kaydedilir |
| TH14 | İzin listesi dışında loopback hedefi | Gerçek yerel servise erişim yok; yalıtım kurulamıyorsa HOLD |
| TH15 | Fikstür yolu geçişi veya reparse-point kaçışı | İzinli kök dışındaki yollar reddedilir |
| TH16 | Sahip olunan kaynakların temizliği | Kalan görev/iş parçacığı/işlem/kira yok; ilgisiz kaynaklara dokunulmaz |
| TH17 | Sahte saat ilerlemesi ve zaman aşımı | Belirlenimci monoton ilerleme ve uyanma; duvar saatinden bağımsız |
| TH18 | Geri giden/geçersiz sahte saat | Reddedilir; negatif süre yok |
| TH19 | Saatler arası karşılaştırma | Eksik senkronizasyon raporlanır; sahte geçen süre yok |
| TH20 | Bariyerle kontrol edilen iptal sırası | Uykuya dayalı iddia olmadan tekrarlanabilir kabul öncesi/sonrası sıralaması |
| TH21 | Yerel fikstür RNG'si ve sabit seed | Aynı manifest/seed tanımlı kapsamda aynı fikstürü üretir; küresel RNG değişmez |
| TH22 | İki bağımsız fikstür veya oturum | Paylaşılan değiştirilebilir durum yok; temizlik ve rastgele durum yalıtılmış |
| TH23 | Fikstür manifest hash uyuşmazlığı | Bozuk fikstür reddedilir; aynı revizyonda sessiz yeniden üretim yok |
| TH24 | Fikstür üretim sınırı aşıldı | Sınırsız ayırmadan önce ret, açık tanı |
| TH25 | Kalibrasyon/değerlendirme örtüşmesi | Yasak ortak kimlikler/yinelenen gruplar tespit edilir; ayrılmış küme sızıntısı yok |
| TH26 | 8 kHz PCM16 20 ms | Tam 160 örnek, 320 bayt, açık little-endian |
| TH27 | 16 kHz PCM16 20 ms | Tam 320 örnek, 640 bayt |
| TH28 | 48 kHz Float32 20 ms eşdeğeri | 960 örnek, 3840 bayt; değişken parçalar da sözleşmeye göre geçerli |
| TH29 | 16 kHz VAD penceresi ile 20 ms çerçeve | 512 örnek = 32 ms; medya çerçevesiyle karıştırılmaz |
| TH30 | Sessizlik/dürtü/sinüs/chirp/gürültü üretimi | Belirlenimci üst veri, örnek sayıları, sonlu değerler, belgeli sayısal tolerans |
| TH31 | Kırpılmış ve düşük seviyeli analitik sinyaller | Beklenen genlik koşulları; gerçek ses kalitesi iddiası yok |
| TH32 | Tek bayt uzunluğu, NaN/Inf, geçersiz hız | Sözleşme doğrulayıcı geçersiz fikstürü güvenli hatayla reddeder |
| TH33 | Boşluk, örtüşme ve son dolgu | Açık örnek ofseti ve dolgu üst verisi; uydurma süreklilik yok |
| TH34 | Konuşmaya benzer sentetik fikstür etiketi | İnsan konuşması veya bağımsız akustik benchmark olarak sınıflanmaz |
| TH35 | Sahte VAD başlangıç/bitiş olayı | Betikli örnek sınırlarına uyulur; mock etiketli |
| TH36 | Sahte ASR kısmi sonra final | Revizyon sırası korunur; ham/normalize/kanonik alanlar ayrı |
| TH37 | Sahte ASR geç sonucu | Gerçek kabul edilmiş çalışma zamanı noktasında M02 çiti bayat sonucu reddeder |
| TH38 | Sahte ASR bilinmeyen güven | Null null kalır; çıkarılmış olasılık yok |
| TH39 | Sahte LLM bozuk yanıt | Güvenli sonuç doğrulaması; otomatik araç çağrısı yok |
| TH40 | Sahte LLM yönetici iddiası veya araç enjeksiyonu | Güvenilmeyen öneri veri olarak kalır; testin etki yetkisi yok |
| TH41 | Sahte TTS parçası | Üst veri ve yük doğrulanır; fikstür üretim geri düşmesi değildir |
| TH42 | Sahte TTS geçersiz veya sırasız parçalar | Geçersiz başvuru reddedilir; sıra beklentisi korunur |
| TH43 | İptalden sonra gecikmeli sahte TTS tamamlanması | Eski generation çıktısı kabul edilmez; mantıksal ve gerçek tamamlanma izlenir |
| TH44 | Sahte GPU bayat/eksik yoklama | Dürüst "erişilemez" kabul girdisi; uydurma boş VRAM yok |
| TH45 | Sahte GPU asenkron tamamlanma | Mock'ta kira terminal tamamlanmaya kadar tutulur; kabul edildiyse gerçek M06 noktası |
| TH46 | Sahte GPU OOM ve belirsiz tamamlanma | Gerçek GPU işlemi yok; karantina test davranışı veya açık eksik nokta |
| TH47 | Sahte sağlayıcı çağrı kaydı | Kapsam ve sayılar güvenli; müşteri verisi veya ham yük günlüğü yok |
| TH48 | Geçici DB fikstür şeması ve kısıtlar | Yalıtılmış bilinen şema; gerçek kaynak kökeni ile basitleştirilmiş fikstür ayrımı açık |
| TH49 | İki DB bağlantısıyla eşzamanlı talep | Belirlenimci çekişme testi; uygun noktada en fazla bir yetkili talep |
| TH50 | Commit edilmiş fikstür etkisinden sonra geçici DB'yi yeniden açma | Kalıcılık fikstür içinde doğrulanır; canlı rezervasyon değil |
| TH51 | Kaynak kapsamı dışında sahte aktör | Başka sentetik müşteri kaydını yetkilendiremez |
| TH52 | Süresi dolmuş veya değiştirilmiş onay fikstürü | Gerçek M07 noktası varsa reddedilir; yoksa eksik nokta dürüstçe raporlanır |
| TH53 | Bilinmeyen sağlayıcı sonucu fikstürü | Kör yeniden oynatma yok; uzlaştırma gereksinimi korunur |
| TH54 | Denetim hatası enjeksiyonu fikstürü | Gerçek noktada gerekli denetim olmadan korunan etki başlamaz |
| TH55 | Parçalanmış TCP başlık/gövde | Sahte akış parçaları iletir; ayrıştırıcı doğru baytları alır veya açık ret |
| TH56 | Birleşmiş TCP çerçeveleri | Okuma düzeyinde çerçeve sınırı varsayımı yok; beklenen çerçeveleme doğrulanır |
| TH57 | Bağlantı kopması/kısmi yazma/geri basınç | Sınırlı sahte aktarım davranışı ve açık bilinmiyor/uçuşta durumu |
| TH58 | Yinelenen DTMF fikstürü | Sahibi destekliyorsa aynı mantıksal olay bir kez; değilse bekleyen yükümlülük |
| TH59 | Oynatma boşaltma ve onay | Kuyruk temizliği, gönderim ve sahte uç ayrı; duyuldu iddiası yok |
| TH60 | RTP yeniden sıralama/kayıp fikstürü | Ayrı simülasyon kipi; gözlenmiş TCP paket kaybı denmez |
| TH61 | Altın karşılama tekrarı | Belirlenimci beklenen geçiş, yan etki yok |
| TH62 | Altın randevu ve saat değişikliği tekrarı | Gerekli onay/etki iddiaları; eksik F3 davranışı gelecek NOT_RUN |
| TH63 | Altın belirsiz araç / boş saat yok | Uydurma kanonik bilgi yok, beklenmeyen etki yok |
| TH64 | Altın iki oturum tekrarı | Oturumlar arası bağlam, tampon, sonuç veya olay sızıntısı yok |
| TH65 | Aynı fikstür revizyonunu iki kez tekrar | Beklenen kapsamlı sonuçlar yeniden üretilir; önceki çalıştırmadan yinelenen etki yok |
| TH66 | Hata planı seçili oluşum/aşamayı hedefler | Yalnızca hedef test sınırı hataları; üretimden erişilemez |
| TH67 | Gözlemci veya günlük alıcısında hata | Çekirdek kontrol yolu bağımsız; M04 hatası ham veri olmadan gözlenir |
| TH68 | M00 özellik birleşiminde eksik/yinelenen kimlik | Payda uyuşmazlığı tespit edilir; sessiz özellik kaldırma yok |
| TH69 | Eşlenmiş ama çalıştırılabilir testi olmayan özellik | Kapsam boşluğu görünür; davranışsal PASS değil |
| TH70 | Geçmiş hata ile yeni regresyon | Başarısız durum, karşılaştırma ve incelenmiş taban riski korunur; yeni regresyon engeller |
| TH71 | Eski istemci API şeması ve durum kayması | Uyumsuz değişiklik tespit edilir; iç sözleşme sürümü dışarı zorlanmaz |
| TH72 | Arayüz eylemi/işleyici/API eşleme kayması | Yetim/uyuşmazlık tespit edilir; statik ve çalıştırılabilir sonuç kapsamı ayrı |
| TH73 | DB şeması/yapılandırma/seed taban kayması | İzinsiz göç, varsayılan, takma ad veya Leyla seed değişikliği tespit edilir |
| TH74 | Mevcut paket test kimliklerinin kaydı | Yeniden numaralandırma, yineleme, gizli atlama veya zorunlu vaka kaybı yok |
| TH75 | Kanıt yolu/hash/anlık görüntü uyuşmazlığı | Güvenilmeyen, bayat, eksik veya kurcalanmış yapıtlar reddedilir |
| TH76 | Zorunlu PASS/FAIL/HOLD/NOT_RUN birleştirme | Doğruluk tablosu ve isteğe bağlı vaka bağımsızlığı doğru |
| TH77 | Skip/xfail/boş test ve tutarsız sayılar | Sahte PASS yok; gerçek çalışan/başarısız/atlanan eşlemesi uzlaştırılır |
| TH78 | Gerçek uç/GPU olarak yanlış etiketlenmiş sentetik/mock kanıt | Köken/kapsam uyuşmazlığı reddedilir; ölçülmemiş değerler null |
| TH79 | İstisna, manifest ve günlükte gizli/kişisel veri işareti | Hassas kalıcılık yok; güvenli tanı ve kontrollü hata |
| TH80 | Eksik paket veya noktayla çekirdek kapı manifesti | Altyapı PASS olsa bile çekirdek hazırlık false; F0-A otomatik yetkilendirilmez |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M08-G00 | Ön kontrol | M00/M01/M02/M04 doğrulanmış; isteğe bağlı noktalar sınıflanmış |
| M08-G01 | Kapsam | İzinli kaynak kapsamı, pasif içe aktarma, tek altyapı, mevcut koşucu korunmuş |
| M08-G02 | Üst veri | M01/M04 uyumlu altyapı üst verisi ve test kimliği eşlemesi |
| M08-G03 | Koşucu | Güvenli belirlenimci keşif, seçim, sayı ve çıkış işleme |
| M08-G04 | Yalıtım | Yalıtım, yan etki reddi, yol sınırlaması ve sahipli temizlik gösterilmiş |
| M08-G05 | Belirlenimcilik | Enjekte sahte saat, RNG ve belirlenimci eşzamanlılık bariyerleri |
| M08-G06 | Fikstürler | Fikstür kökeni, revizyon, hash, sınırlar ve bölünme politikası |
| M08-G07 | Ses | Sentetik ses sözleşmeleri ve biçim sınırları test edilmiş |
| M08-G08 | Sahte modeller | Sahte VAD/ASR/LLM/TTS gerçek model yüklemeden test edilmiş |
| M08-G09 | Sahte sınırlar | Sahte GPU, DB, kimlik ve sağlayıcı sınırları; isteğe bağlı gerçek noktalar abartılmamış |
| M08-G10 | Aktarım | Sahte aktarım, DTMF fikstürü ve gözlem kapsamı doğrulanmış |
| M08-G11 | Altın senaryolar | Altın senaryolar/tekrar ve yasak etki iddiaları gösterilmiş |
| M08-G12 | Hata enjeksiyonu | Yalnız testte hata enjeksiyonu ve güvenli temizlik kanıtlanmış |
| M08-G13 | Test paketleri | Mevcut CT/RT/OB kapsamı ve CR/LX/GPU/SEC kaydı korunmuş |
| M08-G14 | Özellik paydası | M00 özellik paydası ve açık kapsam/regresyon kararları uzlaştırılmış |
| M08-G15 | Uyum | API/arayüz/DB/yapılandırma uyum kontrolleri ve sınırlamaları doğru sınıflanmış |
| M08-G16 | Kanıt | Kanıt bütünlüğü, gizlilik ve durum birleştirme doğrulanmış |
| M08-G17 | Test kanıtı | TH01–TH80 gerçekten çalıştırılmış, gerekli beklentiler geçmiş; gerçek isteğe bağlı noktalar ayrı izleniyor |
| M08-G18 | Çekirdek kapı | Çekirdek entegrasyon planı/koşucusu, kapı vakaları ve engelleyici hazırlık modeli doğrulanmış |
| M08-G19 | Devir | İncelenmiş bütünlük, geri dönüş, devir ve kesin kapsam sınırları teslim edilmiş |

## 9. Kanıt

`evidence/M08/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `TEST_INVENTORY.json`, `HARNESS_DECISIONS.md`, `FIXTURE_REGISTRY.json`, `FEATURE_TEST_MATRIX.csv` (M00 özellik → test kimlikleri → kapsam kararı), `COMPATIBILITY_REPORT.json`, `TEST_MATRIX.json`, `CORE_GATE_PLAN.md`, `DOWNSTREAM_HANDOFF.md`.

## 10. Geri dönüş

Yalnızca test kodu eklenir; geri dönüş M08 commit'lerinin `git revert`'üdür. Üretim kodu değişmediği için uygulama davranışı etkilenmez. Mevcut testler silinmediği için geri dönüş sonrası eski paket aynen çalışır.

## 11. Devir

- **CORE_GATE:** `scripts/run_gate.py --gate CORE_GATE` açık komutla, bağımsız gözden geçirenle çalıştırılır.
- **F0-A … F6-A:** her paketin T01 karakterizasyon testi bu altyapıyla yazılır; sahte model adaptörleri ve sentetik sinyal üreteci (eski F0-T29) buradan kullanılır.
- **G4:** T3/T4 gerçek donanım koşuları için `gpu`/`llm` işaretli profiller; sonuçlar `data/<aşama>/lab-report-*.json`.

## 12. Başlatma komutu

```
M08 paketini uygula: docs/execution/packages/W1/M08-test-altyapisi.md.
Kuralları CLAUDE.md'den oku; M00, M01, M02, M04 kanıtını doğrula, diğer noktaları sınıfla.
tests/harness/ altında güvenli koşucu, sahte saat, fikstürler, sahte adaptörler, tekrar ve
hata enjeksiyonunu kur; CORE_GATE vakalarını yaz ama çalıştırma.
TH01–TH80'i çalıştır, M08-G00…G19'u değerlendir, paket/M08 dalında PR aç ve dur.
```
