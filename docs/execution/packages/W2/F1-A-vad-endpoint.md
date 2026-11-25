# F1-A — VAD, ön kayıt ve akustik konuşma sonu

> F0'dan gelen değişken boyutlu 16 kHz çerçeveleri 512 örneklik (32 ms) VAD pencerelerine böler; akış başına yalıtılmış Silero durumu, tek ön kayıt (lookback) sahibi, histerezisli başlangıç/bitiş, akustik endpoint, süre sınırları ve M02 üzerinden tek seferlik atomik söz (utterance) devri sağlar. Anlamsal tur sonu ve söz kesme bu paketin işi değildir.

| Alan | Değer |
| --- | --- |
| Kimlik | F1-A |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, F0-A, M02 |
| Sonraki | F2-A, W2_GATE, F1-B |
| Bayrak | `f1_pipeline_v2` (varsayılan kapalı; `off / shadow / strict`) |
| Ortam | CPU (Silero gerçek modeli yalnızca `@pytest.mark.gpu`/yerel testlerde; birim testleri sahte VAD ile) |
| Eski görevler | F1-T02, F1-T06, F1-T07, F1-T08, F1-T09, F1-T10, F1-T14 |
| Kaynak | Bundle `W2/Freya_2_0_F1_A_Agent_Implementation_Package.md`; [F1 spec](../../../stages/F1-voice-turn-detection/spec.md), [F1 tasks](../../../stages/F1-voice-turn-detection/tasks.md) |
| Durum | NOT_RUN |

## 1. Amaç

PoC'ta ön kayıt iki ayrı yerde tutuluyor, VAD durumu oturumlar arasında paylaşılabiliyordu (H01'de geçici düzeltme yapıldı) ve konuşma sonu yalnızca sabit sessizlik süresine bakıyordu. F1-A, bu akustik katmanı tek sahipli ve ölçülebilir hale getirir. F1-B (söz kesme) ve F1-C (anlamsal tur sonu) bu temelin üzerine kurulur.

## 2. Başlamadan önce

- [ ] CORE_GATE ve F0-A kabul edilmiş; F0-A devir notu okunmuş.
- [ ] Mevcut Silero durumu, endpoint mantığı, lookback, geri çağrılar, zaman aşımları, DTMF ve STT bağlantısı M00 özellik kimlikleriyle izlenmiş.
- [ ] H01'deki VAD oturum yalıtımı (ADR-F1-01) uygulanmış haliyle okunmuş; F1-A onu akış düzeyine genişletir.
- [ ] Kurulu Silero sürümünün API'si incelenmiş; güvenli durum yalıtımı desteklenmiyorsa F1-A.07 HOLD.

## 3. Kapsam

**Yapılacak:** M01 sözleşme eşlemesi; çerçeve senkronizörü (512 pencere); akış kabulü ve EOS; Silero yetenek denetimi ve durum yalıtımı; birleşik lookback; aday başlangıç; histerezis durum makinesi; akustik endpoint; söz sınırları; örnek muhasebesi; atomik sonlandırma ve tur devri; sınırlı tamponlar ve temizlik; M03/M04; eski kodla uyum.

**Yapılmayacak:** Söz kesme orkestrasyonu ve olay sınıflandırma (F1-B); profil tabanlı/anlamsal endpoint, spekülatif STT köprüsü, double-talk, backchannel (F1-C); ASR (F2); yeni model.

## 4. Dosyalar

```
backend/voice_activity/
  contracts_map.py  frame_sync.py  stream_admission.py  silero_adapter.py
  vad_state.py  lookback.py  onset.py  hysteresis.py  endpoint.py
  limits.py  sample_ledger.py  finalizer.py  buffers.py  telemetry.py  legacy_bridge.py
tests/voice_activity/
evidence/F1-A/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Başlangıç profili

Bu değerler **başlangıç** profilidir (M03'te kayıtlı, `f1.profile.default`); kalibrasyon kümesinde G4'te ayarlanabilir. Bu pakette ölçülmüş performans iddiası yoktur.

| Parametre | Değer | Örnek (16 kHz) |
| --- | --- | --- |
| VAD penceresi | 32 ms | 512 |
| Başlangıç eşiği (IDLE → aday) | skor ≥ 0,60 | — |
| Bitiş eşiği (ACTIVE → sessizlik) | skor ≤ 0,35 | — |
| Başlangıç onayı | 2 ardışık yüksek pencere (64 ms) | 1024 |
| Ön kayıt | 320 ms | 5120 |
| Akustik endpoint | 10 ardışık düşük pencere (320 ms) | 5120 |
| Son kayıt (post-roll) | 160 ms | 2560 |
| Azami söz süresi | 20 s (ön kayıt dahil) | 320000 |

Kurallar: eşitlik başlangıçta aday sayılır (0,60), bitişte sessizlik başlatır (0,35). Başlangıç ≤ bitiş eşiği, NaN süre veya post-roll > endpoint sessizliği olan profil reddedilir (VA46–VA47).

### 5.2 Durum makinesi

```
IDLE ──skor≥0,60──► CANDIDATE ──2. yüksek pencere──► ACTIVE (SPEECH_START bir kez)
  ▲                    │ düşük/orta                     │ skor≤0,35
  │                    ▼                                ▼
  └──── aday reddedilir (tur/final yok)         SILENCE_PENDING ──konuşma döner──► ACTIVE (aynı söz)
                                                        │ 10 düşük pencere
                                                        ▼
                                                 FINALIZING (post-roll kesimi, M02 devri) ──► IDLE
```

- Başlangıç noktası ilk aday penceresinde sabitlenir; onay 64 ms'yi kırpmaz (VA29).
- Aday reddedilirse tur ayrılmaz ve F2 işi açılmaz; ardından gelen gerçek başlangıç aynı geçmişi yinelemeden kullanır.
- 0,36–0,59 arası salınım aktif konuşmada başlat/bitir çırpınması üretmez.
- 450/800 ms gerçek sessizlik 320 ms profilde akustik olarak bölünür; bu, **anlamsal tamamlanma iddiası değildir** (F1-C).

### 5.3 Durum yalıtımı ve sıralama

- Silero durumu akış başınadır (oturum + akış + dönem). Aynı akıştaki iki pencere seri işlenir; farklı akışlar birbirinin skorlarını değiştirmez (VA17–VA19).
- Aynı akışta yeni tur Silero bağlam durumunu sıfırlamaz; çıkış generation'ı iptali giriş VAD'ını sıfırlamaz (VA20–VA21).
- Sağlayıcı NaN/>1 skor veya istisna verirse açık hata; uydurma sessizlik/başlangıç yok.
- Uçuştaki yerel iş sırasında akış iptal edilirse bayat geri çağrı reddedilir, kira gerçek bitişe kadar tutulur (M02/M06).

### 5.4 Lookback, muhasebe ve devir

- **Tek** geçmiş sahibi; örnek sınırlı kapasite; halka sarması doğru sıralı dilim verir; eski dizi takma adı yok. Eski ikinci ön kayıt yolu adaptörle kapatılır (eski F1-T07).
- Örnek aralık defteri: ön kayıt iki kez eklenmez; sentetik dolgu söze girmez; EOS'taki 73 örneklik kuyruk gerçek sayısıyla raporlanır.
- Azami süre pencere içine düşerse gerçek örnekte kesilir; kalan muhasebeye girer. Azami süre ile sessizlik kesimi çakışırsa belgeli öncelik, tek final.
- Sonlandırma M02 kabul sınırında atomiktir: tek sonlandırma talebi, değiştirilemez `Utterance`, en fazla bir devir. EOS ile akustik geri çağrı yarışırsa tek sonuç. F2 kuyruğu doluysa açık geri basınç; spekülatif tur ayrımı yok.
- Yakalama saati yoksa gecikme `null`; saat alanları arası çıkarma yok.

### 5.5 Eski kod ve kipler

| Kip | Davranış |
| --- | --- |
| `off` | Eski `audio.py`/`session.py` endpoint yolu |
| `shadow` | Yeni yol paralel hesaplar, yalnızca gözlem yayar; çıkış/yan etki yok |
| `strict` | Yeni yol tek aktif çıkış; eski yol devre dışı |

Her kipte tam olarak bir aktif çıkış vardır. F0 ham DTMF yolu ve mevcut söz kesme geri çağrıları değişmez. Eski STT sınırı sonlandırılmış veriyi alır; ikinci kırpma/yeniden örnekleme yapılmaz.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F1-A.01 | Çekirdek/F0 ön kontrolü | Kabul edilmiş kapılar, M02, F0-A devri ve onay | Yoksa yazmasız HOLD |
| F1-A.02 | Mevcut VAD envanteri | Silero durumu, endpoint, lookback, geri çağrı, zaman aşımı, DTMF, STT, özellik kimlikleri | `F1_INVENTORY.json` |
| F1-A.03 | Sahiplik ve geçiş tasarımı | Tek katı rota, eşzamanlılık sahibi, eski/gölge politikası, yol izin listesi | `F1_DECISIONS.md` |
| F1-A.04 | M01 sözleşme eşlemesi | `AudioFrame`, `SpeechEvent`, `Utterance` ve M02 başvuruları; açık "mevcut değil" üst verisi | VA04 |
| F1-A.05 | Çerçeve senkronizörü | Değişken girişler, 512 pencere, sınırlı kalan, ofset muhasebesi | VA05–VA10 |
| F1-A.06 | Akış kabulü ve EOS | Yineleme/boşluk/dönem/kuyruk/biçim politikası; iptal ile düzgün kapanış ayrımı | VA11–VA16 |
| F1-A.07 | Silero yetenek denetimi | Kurulu model API'si/sürümü, durum bağımlılıkları, seçilen yalıtım stratejisi | Karar kaydı veya HOLD (VA23) |
| F1-A.08 | VAD durum yalıtımı | Akış başına bağlam, güvenli sıfırlama, seri çıkarım, hata işleme | VA17–VA25 |
| F1-A.09 | Birleşik lookback | Tek geçmiş sahibi, örnek sınırlı kapasite, yinelenen ön kayıt rotası adaptörle kaldırılır | VA26–VA28, VA32–VA34 |
| F1-A.10 | Aday başlangıç | Başlangıç/ön kayıt sabitlenir; 64 ms onay; yanlış aday atılır | VA29–VA31 |
| F1-A.11 | Histerezis durum makinesi | Açık eşikler, eşitlik, geçişler, olay bir kez | VA35–VA39 |
| F1-A.12 | Akustik endpoint | Gerçek düşük dizi, duraklama kurtarma, sessizlik bütçesi, post-roll kesimi | VA40–VA45 |
| F1-A.13 | Söz sınırları | Tüm yükü içeren azami sınır; ayrı boşta/takılma zamanlayıcıları; EOS politikası | VA49–VA55 |
| F1-A.14 | Örnek muhasebesi ve süreklilik | Kesin aralık defteri; yinelenen ön kayıt yok; dolgulu çıktı yok | VA33, VA50, VA52 |
| F1-A.15 | Atomik sonlandırma ve tur devri | M02 kabul sınırı; değiştirilemez `Utterance` tek kez gönderilir | VA56–VA60 |
| F1-A.16 | Sınırlı tamponlar ve temizlik | M02 kaynak defteri, kapasite, geç geri çağrılar, idempotent kapanış | VA61–VA64 |
| F1-A.17 | Yapılandırma ve telemetri | M03 görüntüsü ve M04 kapsam güvenli metrikler; kişisel veri yok | VA46–VA48, VA66–VA68 |
| F1-A.18 | Eski kod bütünleşmesi | Mevcut konuşma/DTMF/STT ve kesme geri çağrıları korunur; katı rota yalıtılmış | VA65, VA69–VA70 |
| F1-A.19 | Belirlenimci testler | VA01–VA72 onaylı T0/T1 kapsamında; gerçek algoritma + sahte sınır | Tüm testler çalıştırılmış |
| F1-A.20 | Regresyon ve kanıt | Etkilenen M00 özellikleri, önceki kapılar, ilgili F0/M02 testleri, bütünlük | VA71 |
| F1-A.21 | Geri dönüş provası | Yalıtılmış rota değişimi; yinelenen gönderim yok; durum sahibi/kullanıcı işi korunur | VA72 |
| F1-A.22 | Kabul ve devir | F1-A-G00…G17; F2-A/F1-B/F1-C noktaları; dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| VA01 | Eksik veya bayat çekirdek kapı | HOLD; kaynak yazma yok |
| VA02 | F0-A kapısı veya devri yok | HOLD; kesin önkoşul belirtilir |
| VA03 | Ağ/model yükleme yasakken F1 içe aktarma | Örtük indirme, işçi veya çıkarım yok |
| VA04 | M01 eşlemesi ve yanlış şema sürümü | Kabul edilen sürüm çalışır; uyumsuz sürüm reddedilir |
| VA05 | 16 kHz'te 512 geçerli f32 örnek | Bir pencere, eşleşen ofsetler, dolgu yok |
| VA06 | 5 × 320 geçerli örnek | Üç pencere, 64 kalan, kayıp yok |
| VA07 | 1/160/800/1023 örneklik değişken bloklar | Ardışık referansla aynı tam pencereler |
| VA08 | PCM16 sınırları −32768, 0, 32767 | Doğru f32 ölçeği; taşma veya çift normalizasyon yok |
| VA09 | Yanlış hız/kanal/kodlama | Ret; VAD çağrısı yok |
| VA10 | NaN/Inf, geçersiz bayt uzunluğu/sayı | Güvensiz ayırmadan önce ret |
| VA11 | Yinelenen sıra ve örtüşen ofset | Tekrar işleme veya durum ilerlemesi yok |
| VA12 | Kabul edilen örnek ofsetlerinde boşluk | Açık süreksizlik/sıfırlama; çıkarılmış sessizlik yok |
| VA13 | Yeni dönemden sonra eski dönem çerçevesi | Yeni durum bozulmadan ret |
| VA14 | Boş veri, sonra açık EOS | Boş geçersiz; EOS tam bir kez işlenir |
| VA15 | 73 örneklik kuyrukla EOS | Yalnız model için onaylı dolgu veya açık sınıflanmamış kuyruk; gerçek sayı korunur |
| VA16 | Sonlandırmadan sonra tekrarlanan EOS | İkinci boşaltma/sonlandırma yok |
| VA17 | Durumlu sahte VAD, yalıtılmış A sonra B referansları | Akış başına belirlenimci yörüngeler |
| VA18 | Araya girmiş A/B pencere dizileri | Akış başı skor/durum yalıtılmış referanslarla eşit |
| VA19 | B aktifken A sıfırlanır/kapanır | B durumu ve çıktısı değişmez |
| VA20 | Aynı akışta yeni tur | Yinelemeli/bağlam durumu korunur |
| VA21 | Giriş sırasında çıkış generation iptali | Giriş sürer; VAD sıfırlanmaz |
| VA22 | Aynı akışta eşzamanlı gönderilen iki pencere | Seri sıra; yarış/durum yeniden sıralaması yok |
| VA23 | VAD arka ucunda güvenli durum yalıtım API'si yok | Açık HOLD; paylaşılan durum kestirmesi yok |
| VA24 | Sağlayıcı skoru NaN, >1 veya istisna | Açık hata; uydurma sessizlik/başlangıç yok |
| VA25 | Uçuştaki yerel iş, sonra akış iptali | Bayat geri çağrı reddedilir; kira gerçek bitişe kadar |
| VA26 | 320 ms geçerli önceki geçmiş, sonra uygun başlangıç | Gerçek ön kayıt 5120 örnek, kesin kaynak aralığı |
| VA27 | İlk yüksek VAD penceresi içinde ilk işaret | İşaret onaydan önce korunur, bir kez |
| VA28 | Akış başında başlangıç | Ön kayıt sıfır veya mevcut gerçek sayı; yapay sıfır yok |
| VA29 | 2 pencere sonra onaylanan aday | Başlangıç ilk aday penceresinde kalır; 64 ms kırpılmaz |
| VA30 | Bir yüksek pencere sonra düşük | Aday reddedilir; tur/final gönderilmez |
| VA31 | Reddedilen adaydan sonra gerçek başlangıç | Doğru geçmiş yeniden kullanılır; yinelenen örnek yok |
| VA32 | Geçmiş kapasitesinde halka sarması | Doğru sıralı dilim; bayat dizi takma adı yok |
| VA33 | Önceki sonlandırılmış aralık ve yeni başlangıç | Katı rotada istenmeyen örtüşme/yineleme yok |
| VA34 | Aday sabitleme + tam geçmiş kapasitesi | Sınırlı geçmiş veya açık hata; sessiz üzerine yazma yok |
| VA35 | IDLE'da skor 0,59 sonra 0,60 | İlki aday değil; başlangıçta eşitlik geçerli |
| VA36 | ACTIVE'de skor 0,36 sonra 0,35 | İlki sürer; bitişte eşitlik sessizliği başlatır |
| VA37 | Aktif konuşmada 0,36–0,59 salınımı | Tekrarlı başlat/bitir çırpınması yok |
| VA38 | Aday yüksek, sonra orta, sonra yüksek | Ardışık onay sıfırlanır; erken başlangıç yok |
| VA39 | İki ardışık yüksek pencere | Tek `SPEECH_START`; spekülatif tur ayrımı yok |
| VA40 | Konuşmadan sonra 9 düşük pencere | 288 ms'de sonlanmaz |
| VA41 | Konuşmadan sonra 10 düşük pencere | 320 ms'de akustik sonlandırma; tek final |
| VA42 | 9 düşük pencereden sonra konuşma döner | Bekleyen sessizlik iptal; aynı söz |
| VA43 | 320 ms profilde 450/800 ms gerçek sessizlik | Belgelendiği gibi akustik bölme; anlamsal tamamlanma iddiası yok |
| VA44 | 10 düşük pencere, post-roll 160 ms | Kesim düşük_başlangıç + 2560'ta; ek bekleme yok; kuyruk hesaplanır |
| VA45 | Önceki kesimden sonra yeni başlangıç | Uygun artık geçmiş; sonlandırılmış örtüşme yok |
| VA46 | Post-roll > sessizlik endpoint'i olan profil | Katı profil reddedilir |
| VA47 | Eşit eşikli veya NaN süreli profil | Etkinleşmeden önce ret |
| VA48 | Akış aktifken yayımlanan yapılandırma revizyonu | Mevcut görüntü korunur; yeni akış onaylı revizyonu kullanır |
| VA49 | Sürekli konuşma 320000 örnek sınırını aşar | Ön kayıt dahil kesin sert kesim; `MAX_DURATION` |
| VA50 | Sert sınır VAD penceresi içine düşer | Kesin gerçek örnek kesimi; kalan hesaplanır |
| VA51 | Sert sınır ile sessizlik kesimi çakışır | Belirlenimci belgeli öncelik; tek final |
| VA52 | Azami süre kesiminden sonra sürekli konuşma | Yeni aday/segment mümkün; yinelenen ses veya sahte sessizlik yok |
| VA53 | Geçerli düşük skorlu ses gelirken konuşma yok | Boşta politikası; boş söz veya STT işi yok |
| VA54 | Takılma bekçisi süresince çerçeve yok | Açık giriş takılması; örnek imleci değişmez |
| VA55 | Aktif konuşmada düzgün EOS | Gerçek kuyruk ve EOS nedeniyle en fazla bir onaylı final |
| VA56 | Aktif konuşmada kopma veya iptal | İstenmeyen tur/gönderim yok; kaynaklar bırakılır veya karantina |
| VA57 | EOS ile akustik geri çağrı yarışı | Tek sonlandırma talebi, en fazla bir devir |
| VA58 | Yinelenen final geri çağrısı | Aynı sonlandırma kimliği; ek tur yok |
| VA59 | Atomik devirden önce M02 iptali | Kabul edilmiş final yok; güvenli kira bırakma |
| VA60 | Kapanıştan önce kabul edilen final | Kabul makbuzu korunur; yinelenen devir yok; aşağı akış iptali M02'ye göre |
| VA61 | F2 kuyruğu dolu | Açık geri basınç; sınırlı bellek; spekülatif tur ayrımı yok |
| VA62 | Devir denemesinden sonra tüketici hata fırlatır | Sonuç/sahiplik belgelenir; kör yinelenen gönderim yok |
| VA63 | Kabulden sonra üretici ndarray'i değiştirilir | Sahipli değiştirilemez örnekler değişmez |
| VA64 | Tekrarlı aç/kapa ve başarısız çıkarım | İdempotent temizlik; sızan durum/kira yok |
| VA65 | Karışık DTMF ve konuşma fikstürü | Ham F0 DTMF yolu değişmez; ek rakam gönderimi yok |
| VA66 | Telemetri abonesi hatası/taşması | Akustik karar ve final devri etkilenmez |
| VA67 | Olay eklerine kişisel veri ve ham ses enjeksiyonu | Güvenli izdüşüm reddeder/maskeler; ham içerik günlüğü yok |
| VA68 | Eksik yakalama saati, yabancı saat alanı | Gecikme `null`; saatler arası çıkarma yok |
| VA69 | Eski STT sınırı sonlandırılmış veriyi kabul eder | Yinelenen kırpma/yeniden örnekleme yok; API/davranış korunur |
| VA70 | `off`/`strict`/`shadow` kip seçimi | Tam olarak bir aktif çıkış; gölge yan etkisiz; varsayılanlar korunur |
| VA71 | M00 özellik regresyonu ve ilgili F0/M02/M01 testleri | Onaysız regresyon yok; DTMF/kesme geri çağrı yolları korunur |
| VA72 | Geri dönüş, kanıt ve hazırlık doğrulaması | İncelenmiş ters değişiklik; kullanıcı işi kaybı yok; hazırlığı yalnız geçerli kanıt belirler |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F1-A-G00 | Ön kontrol | CG00–CG11 ve F0-A-G00…G15 kabul, M02 uyumu ve onay |
| F1-A-G01 | Tek sahip | Akış başına tek aktif bölümleme sahibi, güvenli içe aktarma, izin listesi |
| F1-A-G02 | Sözleşme | Gerçek M01/F0-A sözleşme eşlemesi ve katı giriş doğrulaması |
| F1-A-G03 | Senkronizör | 512 pencere senkronizörü, değişken parçalar, gerçek örnek korunumu |
| F1-A-G04 | Silero yalıtımı | Kurulu arayüzle desteklenen, belirlenimci adaptör testleriyle doğrulanmış yalıtım stratejisi; güvensiz özel durum kestirmesi yok |
| F1-A-G05 | Durum yaşam döngüsü | Akış başı durum yaşam döngüsü, sıra ve bayat geri çağrı güvenliği |
| F1-A-G06 | Lookback | Tek lookback sahibi, aday ön kaydı ve ilk işaretin korunması |
| F1-A-G07 | Histerezis | Histerezis ve başlangıç onayının belirlenimci davranışı |
| F1-A-G08 | Endpoint | Akustik endpoint, dönen konuşma ve gerçek post-roll anlamı |
| F1-A-G09 | Sınırlar | Sert süre sınırı, EOS, boşta/takılma ve açık süreksizlik |
| F1-A-G10 | Devir | M02 atomik devri; tek söz/tur teslimi; iptal ayrımı |
| F1-A-G11 | Kaynaklar | Sınırlı tampon/görev sahipliği, temizlik ve geri basınç |
| F1-A-G12 | Yapılandırma ve gözlem | M03 görüntüsü ve M04 güvenli kapsam duyarlı gözlem |
| F1-A-G13 | Uyum | Eski uyum ve ham DTMF yolu korunmuş; yeni kesme etkisi yok |
| F1-A-G14 | Test kanıtı | VA01–VA72 gerçek yapısal test kanıtı; tüm zorunlular çalıştırılmış, atlanan PASS sayılmamış |
| F1-A-G15 | Regresyon | Etkilenen M00 özellik regresyonları ve ilgili çekirdek/F0 testleri incelenmiş |
| F1-A-G16 | Bütünlük | Kaynak bütünlüğü, incelenmiş geri dönüş provası, bağımsız kanıt doğrulaması |
| F1-A-G17 | Devir | F2-A/F1-B/F1-C devri tam; hazırlık ve ertelenen akustik/donanım kapsamı açık |

## 9. Kanıt

`evidence/F1-A/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F1_INVENTORY.json`, `F1_DECISIONS.md`, `SILERO_CAPABILITY.md` (kurulu sürüm, durum API'si, seçilen yalıtım), `PROFILE.json` (§5.1 değerleri, M03 revizyonu), `TEST_MATRIX.json`. Gerçek VAD hassasiyet/duyarlılık ölçümleri bu pakette yoktur; G4'te `data/F1/lab-report-*.json`.

## 10. Geri dönüş

`f1_pipeline_v2=off`: eski endpoint yolu tek aktif çıkış olur. Kip değişimi akış sınırında etkilidir; yinelenen gönderim olmadığı geri dönüş provasıyla (F1-A.21) gösterilir. Kod değişiklikleri `git revert` ile geri alınır.

## 11. Devir

- **F2-A:** M02 kabul edilmiş, değiştirilemez `Utterance` (gerçek örnek aralığı, ön/son kayıt üst verisi, sonlandırma nedeni). Ön kayıttaki ilk örnek işaretleri korunur.
- **F1-B:** `SpeechEvent` akışı (aday/başlangıç/bitiş) söz kesme orkestratörüne girdi olur; F1-A kesme kararı vermez.
- **F1-C:** akustik endpoint "aday tur sonu"dur; anlamsal karar F1-C'de.
- **G4:** profil değerlerinin kalibrasyonu, onset p95 ≤ 100 ms ve kısa endpoint p95 ≤ 500 ms hedeflerinin gerçek ölçümü.

## 12. Başlatma komutu

```
F1-A paketini uygula: docs/execution/packages/W2/F1-A-vad-endpoint.md.
Kuralları CLAUDE.md'den oku; CORE_GATE ve F0-A kabulünü doğrula, kurulu Silero API'sini denetle.
backend/voice_activity/ altında 512 pencere senkronizörü, akış başı VAD durumu, tek lookback,
histerezis ve akustik endpoint'i f1_pipeline_v2 bayrağı arkasında kur.
VA01–VA72'yi çalıştır, F1-A-G00…G17'yi değerlendir, paket/F1-A dalında PR aç ve dur.
```
