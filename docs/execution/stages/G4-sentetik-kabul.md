# G4 — Sentetik ürün kabulü ve kapsamlı benchmark

> G2 ve G3 kabulünden sonra, ürünün tamamı **yalnız sentetik veriyle** ölçülür: önceki tüm belirlenimci testler yeniden çalıştırılır; katman bazında baz–aday eşli karşılaştırmalar; mock ve gerçek yerel model (native) yolları **ayrı** uçtan uca yolculuklar; hata enjeksiyonu ve sınırlı yük. Gerçek insan sesi, gerçek müşteri verisi ve gerçek SIP yoktur (G5). MOS/ABX burada `NOT_RUN` kalır.

| Alan | Değer |
| --- | --- |
| Kimlik | G4 |
| Dalga | Ürün aşaması |
| Öncelik | P0 |
| Önkoşullar | G3 |
| Sonraki | G5 |
| Bayrak | Yeni bayrak yok; aday profiller yalnız laboratuvar yapılandırmasıyla (`config/acceptance/g4/`) seçilir, canlı varsayılan değişmez |
| Ortam | Çevrimdışı; yalıtılmış test DB'si; ağ çıkışı izin listesiyle; yerel GPU (M06 üzerinden, onaylı sınırlar); isteğe bağlı yalıtılmış PBX laboratuvarı yalnız ayrı izinle |
| Eski görevler | F0-T30, F0-T31, F0-T32, F1-T26, F1-T27, F1-T28, F2-T31, F2-T32, F2-T34, F2-T35, F3-T36, F3-T37, F3-T38, F3-T39, F4-T31, F4-T32, F5-T28, F5-T29, F5-T30, F5-T31, F6-T26, F6-T27, F6-T28 |
| Kaynak | Bundle `06_PRODUCT_STAGES/G4/Freya_2_0_G4_Synthetic_Product_Acceptance_Master_Prompt.md`; aşama `acceptance.md` dosyaları |
| Durum | NOT_RUN |

## 1. Amaç

Her paket kendi testlerini geçmiş olsa da ürün bir bütün olarak ölçülmemiştir. G4, master planın hedeflerini (§Hedefler) önceden kayıtlı, dondurulmuş, eşli ve paydası tam bir protokolle **gerçek yerel modellerde ama sentetik girdiyle** ölçer; G5'e yalnız dürüst bir kanıt seti devreder.

## 2. Başlamadan önce

- [ ] G2 ve G3 gerçek kabul; CG/WG gerçek PASS (yalnız "hazır" bayrağı yetmez); uyumlu soy.
- [ ] Kullanıcı G4'ü başlattı; kapsam (hangi isteğe bağlı profiller, yük basamakları, PBX laboratuvarı) yazılı.
- [ ] Onaylı model yapıtları yerelde; eksikse ilgili yerel profil HOLD (indirme yok).
- [ ] Test DB'si üretimden ayrı; çalıştırıcı üretim DB'sine bağlanmayı reddeder.

## 3. Kapsam

**Yapılacak:** giriş ve soy; ortam yalıtımı; devralınan belirlenimci regresyon; derlem ve haklar; değerlendirici ve deney dondurma; F0–F6 katman denemeleri; mock ve yerel ürün yolculukları; arayüz ve yetki yolculukları; belirlenimci hata/güvenlik; yerel yük ve dayanıklılık; toplama ve kanıt doğrulama; geri dönüş ve kapsam kararı; bağımsız inceleme ve G5 devri.

**Yapılmayacak:** gerçek insan kaydı, müşteri verisi, gerçek çağrı/SIP; model indirme veya değiştirme; eşik değerlerini sonuç gördükten sonra değiştirme; ayrılmış küme üzerinde ayar; Freya→Whisper gidiş-dönüşünü bağımsız ASR ölçümü saymak; LoRA eğitimi.

## 4. Dosyalar

Mevcut M08 çalıştırıcısı kullanılır; yinelenen üretim kodu yok.

```
config/acceptance/g4/          dondurulmuş kapsam, profil, hedef ve deneme şartnameleri
tests/acceptance/g4/
  contracts/                  devralınan vaka bağlamaları
  fixtures/                   sentetik üretim, kâhin ve bölüm kontrolleri
  layers/                     gerçek F0–F6 adaptörleri, katman denemeleri
  journeys/                   mock ve yerel tam ürün vakaları
  fault_load/                 belirlenimci hata ve sınırlı yerel yük
  codec_lab/                  yalıtılmış isteğe bağlı kodek/PBX
  ui/                         mevcut frontend çalıştırıcısı entegrasyonu
evidence/G4/<run_id>/          değiştirilemez çalıştırma bildirimi ve güvenli yapıtlar
data/<aşama>/lab-report-*.json katman ölçüm raporları
```

Kişisel kayıt, kimlik bilgisi, ham kayıt, transkript veya model ağırlığı commit edilmez.

## 5. Tasarım ve sözleşmeler

### 5.1 Test yolları ve kanıt sınıfları

| Yol | Gerçek bileşenler | Değiştirilen sınırlar | İzin verilen iddia |
| --- | --- | --- | --- |
| T0/T1 belirlenimci | Kabul edilmiş sözleşmeler/çalışma zamanı/hat/geçit/DB/UI | Sahte saat; kontrollü yerel/dış sağlayıcılar | Fikstür kapsamında yapısal doğruluk (`MOCK_RUNTIME` / `SYNTHETIC_FIXTURE`); akustik/performans iddiası yok |
| T2-yerel | Gerçek kurulu DSP/model/kodek/değerlendirici | Sentetik ses/metin; dış etki yok | Belirtilen katman/profilde `LOCAL_RUNTIME_MEASURED`; insan kabulü değil |
| T3-mock | Tüm F0–F6 + gerçek UI + yalıtılmış DB | Yerel modeller, uzak sağlayıcılar ve uçlar sahte | Sahte uyaranlarla gerçek orkestrasyon; yerel WER/MOS/gecikme iddiası yok |
| T3-yerel | Gerçek kurulu F0–F6 modelleri ve orkestratör, gerçek UI, yalıtılmış DB | Sentetik girdiler; sahte iş/bildirim/uzak etki | Sentetik yük altında `LOCAL_RUNTIME_MEASURED`; gerçek müşteri başarısı değil |
| T4-hata | Gerçek sahipler; yalıtılmış hata adaptörü; belirlenimci takvim | Enjekte edilmiş hata/kontrol sınırları | Güvenlik değişmezleri, temizlik; sahte gecikme donanım performansı değil |
| T4-yük | Onaylı sınırlarla gerçek yerel çalışma zamanı | Yalnız sentetik trafik | Kesin profil/donanım/yük için ölçülmüş kapasite; üretim kapasitesi değil |
| T4-PBX-lab | Ayrıca izinliyse yerel test PBX/yazılım uç | Sentetik ses; herkese açık rota veya insan yok | Yalıtılmış topoloji için ölçüm; G5 SIP kanıtı değil |
| T5 | Gerçek insan / gerçek SIP | Burada çalıştırılmaz | `NOT_RUN`; yalnız G5 |

Kanıt sınıfları M04 sıralamasıyla: `STATIC_CODE`, `HISTORICAL_RECORD`, `SYNTHETIC_FIXTURE`, `MOCK_RUNTIME`, `LOCAL_RUNTIME_MEASURED`, `REAL_ENDPOINT_MEASURED`. Matematiksel, mock veya tarihsel sonuç yerel ölçüme terfi ettirilmez.

### 5.2 Derlem ve referanslar

| Veri kümesi | Önerilen sayı | Altın ve katmanlar | Ayrım |
| --- | ---: | --- | --- |
| ASR-1000 | 1000 ifade | Kesin metin, kanonik slotlar, belirsizlik, bağımsız biliniyorsa zamanlama; kısa/uzun, marka, model/yıl, rakam/plaka/telefon/saat, düzeltme, olumsuzluk, sessizlik/gürültü/yankı | Şablon, konuşmacı üretici ailesi, dalga biçimi varyantı; bağımsız üretici ile gidiş-dönüş etiketli |
| DLG-2000 | 2000 senaryo | Niyet kümeleri, rotalar, slot değerleri, bağımlılıklar, yetkiler, challenge yaşam döngüsü, beklenen DB değişimi/makbuz; yanıtsız ve negatif vakalar | İş akışı ve yeniden ifade ailesi; RAG-500 alt kümedir, ek sayılmaz |
| LING-3000 | 3000 metin | Kesin normalize referans, tipli korumalı atomlar, Unicode aralıkları, incelenmişse morfoloji/hece/vurgu, parça sınırı kısıtları | Metin/şablon ve sözcük ailesi |
| TTS-2000 | 2000 metin | Sabit kaynak ve hazırlanmış plan, terim/sayı hedefi, söz eylemi, süre/yapı iddiaları; izinliyse akustik referans | Şablon/marka/fonoloji ailesi; aday çıktı referans kümesinde yok |
| DSP-18 | 18 senaryo ailesi | Sessiz, yalnız konuşma, beyaz/renkli gürültü, motor, fan, yol, rüzgâr, atölye darbesi, dar bant, yalnız yankı, yalnız yakın uç, çift konuşma, gecikme değişimi, kayma, eksik referans, kırpılma, örnek süreksizliği, DTMF karışımı | Bağımsız seed'li eşli dalga biçimleri; bilinen kaynaklar ve aralıklar |
| E2E-JOURNEY | Kullanıcı dondurur | Çok turlu durum, beklenen eylem/ret ve son yanıt; aynı yolculuk mock ve yerel yolda | Ayrı yolculuk kimlikleri; çift sayım yok |
| HIST-320 | Kurtarılırsa tarihsel 320 vaka | Birleşik TTS/telefon bandı/STT tarihsel sonucu | Yalnız tarihsel; yeni ayrılmış kanıt değil |

Sayılar derlem boyutu tasarım hedefidir; çalıştırılmış test sayısı değildir. Değiştirilemez bildirim: veri kümesi kimliği, sürüm, öğe ve grup kimliği, bölüm, üretici/sürüm/seed, fikstür hash'i, hak, altın kimliği, not sürümü, dönüşüm zinciri, ses biçimi/süresi. Gerçek insan kaydı veya müşteri verisi yok. Freya'nın ürettiği sesin Whisper'a verilmesi bağımsız ASR veri kümesi sayılmaz (öz gidiş-dönüş etiketi).

### 5.3 Deney protokolü

- Aynı öğe ve referansta eşli baz/aday; sürümler sabit; RNG ve yük sabit; yalnız değişen etken belgelenir. Baz = kabul edilmiş eski davranış veya önceki paket; rastgele eski çalıştırma değil. Yasal baz yoksa karşılaştırma HOLD.
- Çalıştırma sırası seed'li veya dengeli AB/BA; termal/zaman kayması önlenir; tüm denemeler saklanır. Soğuk/ılık, önbellek isabet/ıska ayrı.
- Gecikmeler p50/p95/p99 + n + hata sayısı; bileşen p95'leri toplanarak uçtan uca değer üretilmez; ilk paket ≠ ilk duyulur ses; yalnız aynı saat veya doğrulanmış eşleme.
- RTF = gerçek işlem süresi / gerçek ses süresi; kuyruk dahil ve yerel ayrı. VRAM kapsamları (cihaz/süreç/ayırıcı) ayrı.
- WER/CER/PER ayrı referans birimi ve paydayla; başarısız/eksik/çekimser öğeler paydada.
- Eşikler değerlendirmeden önce dondurulur; ayrılmış kümede yeniden ayar yok. Hedefe ulaşılamazsa FAIL/HOLD; hedef asla ölçülmüş başarıya dönüştürülmez.

### 5.4 Hedefler

Master plan §Hedefler aynen geçerlidir (F0 DSP p95 ≤ 10 ms; F1 VAD P/R ≥ %95, onset p95 ≤ 100 ms, kısa endpoint p95 ≤ 500 ms, yanlış kesme ≤ %2; F2 WER ≤ %10, CER ≤ %4, terim ≥ %95, yanlış otomatik düzeltme ≤ %1; F3 niyet makro-F1 ≥ %95, görev başarısı ≥ %95, yetkisiz yazma/çift kayıt/uydurma fiyat 0; F4 normalizasyon ≥ %99, korumalı atom ihlali 0, p95 ≤ 50 ms; F5 ılık kısa parça TTFA p95 ≤ 500 ms, RTF p95 ≤ 0,30; F6 tempo sapması p95 ≤ 5 ms; tek görüşmede OOM 0). Bunlar önerilen başlangıç hedefleridir, ölçülmüş değer değildir. E2E 1,2 sn ilk duyulur ses ve 200 ms duyulur kesme yalnız G5'te gerçek uçta ölçülür; G4'te en çok laboratuvar gözlemidir.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| G4.01 | Giriş ve soy | Uyumlu incelenmiş çalıştırma kimlikleri, kullanıcı izni ve kabul edilmiş anlık görüntü doğrulanır; kapsam dondurulur | SA001–SA005 |
| G4.02 | Ortam ve yalıtım | Gerçek araçlar ve donanım; sanal alan yolları; yalıtılmış DB; çıkış kısıtları; mevcut servislerle çakışma yok | SA006–SA010 |
| G4.03 | Devralınan belirlenimci regresyon | Her özgün vaka ve G3 vakası gerçek çalıştırılabilir test ve kanıta bağlanır; M00 regresyonları eklenir | SA011–SA015 |
| G4.04 | Derlem ve haklar | ASR-1000/DLG-2000/LING-3000/TTS-2000/DSP-18/E2E için değiştirilemez bildirimler; sızıntı denetimi | SA016–SA020 |
| G4.05 | Değerlendirici ve deney dondurma | Bilinen yanıtlı vakalarla puanlama; metrik kapsamları, eşleme, örneklem, saat ve hata politikası önceden kayıtlı | SA021–SA025 |
| G4.06 | F0 uyarlanır giriş DSP'si | Bilinen kaynaklı eşli gürültü/yankı fikstürlerinde baz ile uyarlanır profil; örnek defteri ve DTMF güvenliği | SA026–SA030 |
| G4.07 | F1 endpoint ve kesme | Notlu sentetik seslerle başlangıç, uyarlanır sessizlik, onay sesi ve çift konuşma | SA031–SA035 |
| G4.08 | F2 son ASR ve hotword | Baz son ASR, hotword, fonetik/bağlamsal düzeltme; bağımsız sentetik ASR kaynağı ve gerçek çözücü | SA036–SA040 |
| G4.09 | F2 akış ve F1-C devri | Aynı ses ve sabit profille kısmi uygunluk/başlangıç, kararlılık, hizalama, tekrar | SA041–SA045 |
| G4.10 | F3 diyalog ve araç geçidi | Gerçek yalıtılmış DB ve onaylı aktörlerle niyet ve görev senaryoları; yalnız-son eylem | SA046–SA050 |
| G4.11 | F3 RAG ve çoklu niyet | Yetenek varsa BM25/yoğun/hibrit; erişim/uygulanabilirlik ve kaynak; donmuş kurgusal derlem | SA051–SA055 |
| G4.12 | F4 normalizasyon ve prozodi | Tek geçişli kesin normalizasyon, korumalı değerler, morfoloji; gözden geçirilmiş etiketler | SA056–SA060 |
| G4.13 | F5 çözücü/RNG/önbellek | Sabit Euler32 baz ile onaylı 8/16/24/48 profilleri; etkin kimlik, önbellek, geçerlilik | SA061–SA065 |
| G4.14 | F5 konuşmacı/perde ve akustik laboratuvar | Yalnız yalıtılmış laboratuvarda yapısal geçerlilik, F0 ve ECAPA; MOS NOT_RUN | SA066–SA070 |
| G4.15 | F6 gelişmiş render | Baz ile onaylı WSOLA/çapraz geçiş/duraklama/EQ/limiter; kesin dalga biçimi doğrulaması | SA071–SA075 |
| G4.16 | Kodek ve medya aktarım laboratuvarı | Mevcut kütüphanelerle çevrimdışı kodek denemeleri; yerelse açık kodek/PBX izni | SA076–SA080 |
| G4.17 | T3 mock ürün yolculukları | Tam görüşme, CRM, atölye, telefoni, UI yolculukları kabul edilmiş gerçek bileşimle | SA081–SA085 |
| G4.18 | T3 yerel sentetik ürün yolculukları | Aynı yolculuklar gerçek yerel hatla | SA086–SA090 |
| G4.19 | Arayüz ve yetki yolculukları | Tam etkileşim, çevrimdışı kaynaklar, rol uygulaması, bayat/bilinmeyen gösterimi | SA091–SA095 |
| G4.20 | T4 belirlenimci hata ve güvenlik | İptal/commit yarışları, kaynak hataları, kuyruk taşması, oturumlar arası sahtecilik, telemetri hatası | SA096–SA100 |
| G4.21 | T4 yerel yük ve dayanıklılık | Önce tek oturum, sonra onaylı sınırlı basamaklar; gerçek tepe ve hatalar; durma eşikleri | SA101–SA105 |
| G4.22 | Toplama ve kanıt doğrulama | Dondurulmuş metrikler eşli karşılaştırmalarla; tam payda; bütünlük | SA106–SA110 |
| G4.23 | Geri dönüş, regresyon, kapsam kararı | Yalnız sahiplenilen geçici yapılandırma/DB/süreç durumu geri yüklenir; kusurlar sahibe | SA111–SA115 |
| G4.24 | Bağımsız inceleme ve G5 devri | Kabul, kaynak/kanıt, ertelemeler uzlaştırılır; G5'ten önce dur | SA116–SA120 |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| SA001 | G2 veya G3 kabulü yok | Giriş HOLD; çalıştırıcı/model/DB başlatılmaz |
| SA002 | CG/WG başvurusu yalnız hazırlık | Kabul olarak reddedilir; gerçek incelenmiş PASS gerekir |
| SA003 | Süresi dolmuş veya uyuşmayan izin | Yan etkiden önce dur; neden kaydedilir |
| SA004 | Kaynak bildirimi değiştirilmiş | Hash uyuşmazlığı engeller; üst dosyalar değişmez |
| SA005 | F5-D ertelenmiş ve F6-D kapalı | Ana zorunlu kapsam uygun kalır; ertelenen PASS sayılmaz |
| SA006 | Çalıştırıcı üretim DB'sini gösterir | Bağlanmadan/yazmadan önce ret; veri okunmaz |
| SA007 | Fikstür izin listesi dışı ağa çıkmaya çalışır | Reddedilir; güvenli sayı kaydedilir |
| SA008 | Onaylı model yapıtı yok | İndirme yok; zorunlu yerel profil HOLD |
| SA009 | Windows yol geçişi veya yeniden ayrıştırma kaçışı | İzinli kök dışı reddedilir |
| SA010 | Laboratuvar süreci mevcut servisle çakışır | Devralma veya öldürme yok; etkilenen yol HOLD |
| SA011 | Aynı CI testi WG ve G4'te yeniden çalıştırılır | Tek benzersiz kimlik; ayrı çalıştırma satırları |
| SA012 | Numarasız M00 bulunmuş regresyon | Ek test olarak kaydedilir; asla atılmaz |
| SA013 | Zorunlu devralınan test eksik | Kapı HOLD; payda vakayı tutar |
| SA014 | Baz bilinen kusurun önemi değişir | Yeniden değerlendirme; yeni kritik regresyon FAIL |
| SA015 | Test tüm F katmanını sahteyle değiştirir | Entegre yapısal kanıt olarak reddedilir |
| SA016 | Aynı şablon varyantları geliştirme ve testte | Sızıntı denetimi bölümü reddeder |
| SA017 | Test çıktısı altına kopyalanmış | Değerlendirici/referans soyu reddedilir |
| SA018 | Sentetik üretici test edilen modelin kendisi | Öz gidiş-dönüş etiketi; asla bağımsız ASR değil |
| SA019 | Lisanssız ses veya gerçek arayan kaydı | Analiz edilmeden karantina; HOLD |
| SA020 | RAG-500 diyalog derleminde iki kez sayılmış | Alt küme kimlikleri uzlaştırılır; çift sayım yok |
| SA021 | 10 kelimelik referans, S2 D1 I1 | Açık paydayla WER 0,4 |
| SA022 | Boş referans ve uydurulmuş konuşma | Halüsinasyon negatif vakası; WER tanımsız |
| SA023 | Saat alanları kalibre edilmemiş | Alanlar arası süre nedenle null |
| SA024 | Ayrılmış küme marj ayarında kullanılmış | Değerlendirme geçersiz; yeni dondurulmuş test gerekir |
| SA025 | Hata gecikme özetinden çıkarılmış | Uygun hata sayısı korunur; yalnız-başarı kapsamı raporlanır |
| SA026 | Yalnız konuşma + uyarlanır gürültü bastırma | Kritik kayıp yok; temiz eşit-olmama karşılaştırması |
| SA027 | Motor/fan/yol eşli gürültü fikstürleri | Gerçek SNR/bozulma ve aşağı akış etkisi raporlanır |
| SA028 | Oynatma referansı yok veya kısa | AEC dondurulur/bypass; sahte teslim iddiası yok |
| SA029 | Çift konuşma ve gecikme kayması | Yakın uç korunur; geçersiz hizalama uyarlamayı kapatır |
| SA030 | DSP aşırı yükünde ham DTMF | Tam beklenen ham olaylar; yinelenen dedektör yok |
| SA031 | Kısa yanıt ardından sessizlik | Endpoint gecikmesi gerçek notlu sondan ölçülür |
| SA032 | Eksik telefon slotu ve devam eden konuşma | Aynı ifade; sonlu sessizlik bütçesi; örnek kaybı yok |
| SA033 | Kısmi sonuç duraklatma son tarihinden sonra gelir | Commit edilmiş generation beklenmez/sıfırlanmaz |
| SA034 | Belirsiz yankı ile gerçek yakın uç | Muhafazakâr geri düşme; gerçek kesme yalnız yankı diye atılmaz |
| SA035 | Son tarihten önce reddedilen onay sesi adayı | Aynı generation/imleç devam; yeniden seed veya tekrar yok |
| SA036 | Nissan/Qashqai ile benzer alternatifler | Kesin referans oluşumu ölçülür; zorlanmış eşleşme yok |
| SA037 | Baştaki sıfırlı telefon/plaka | Katı tipli değer karşılaştırması |
| SA038 | Konuşmasız/yalnız gürültü klibi | Negatif halüsinasyon paydası |
| SA039 | Belirsiz model ve yıl düzeltmesi | Netleştirme; ham metnin üzerine yazılmaz |
| SA040 | Son yeniden deneme bütçesi veya son tarih tükendi | Başarılı kısmi terfisi yok; gerçek son hata |
| SA041 | İlk uygun kısmi sonuç 800 ms sonra | Biriktirme ve pencere işleme gecikmesi ayrı |
| SA042 | Aynı kelime iki farklı zaman aralığında | Gerçek tekrar korunur; örtüşme çoğaltması yok |
| SA043 | Kelime zaman damgası desteklenmiyor | Null; eşit dağıtılmış uydurma hizalama yok |
| SA044 | Bayat revizyon veya geri alınmış önek | Bayat ipucu reddedilir; kararlılık doğru düşürülür |
| SA045 | P5 tembel iş etkinken P1 gelir | Bekleyen kısmi birleştirilir; kira korunur; zorla CUDA önleme yok |
| SA046 | Kısmi sonuç "evet" der | Slot commit, onay tüketimi, araç veya TTS yok |
| SA047 | Aynı onaylı işlem eşzamanlı tekrarlanır | Tam bir yalıtılmış DB commit'i; makbuz idempotent |
| SA048 | Onaydan sonra müşteri/araç değişir | Eski özet geçersiz; yeni onay |
| SA049 | Commit sonrası zaman aşımı | Kalıcı makbuz uzlaştırılır; kör yeniden deneme yok |
| SA050 | Mock makbuz veya bekleyen bildirim | Gerçek başarı/teslim iddiası yok |
| SA051 | Kısıtlı belge üst sıralarda | Sıralamadan önce hariç; üst veri sızıntısı yok |
| SA052 | Yanlış pazar/yıl veya çelişen bülten | Desteklenen çelişki nedeniyle hariç tut veya çekimser kal |
| SA053 | Teknik belge araç çağrısı talimatı içerir | Güvenilmeyen içerik; yetki yok |
| SA054 | Bağımsız okuma dalgası ve bağımlı mutasyon | İki sınırlı okuma; yazmadan önce bağımlılık/onay |
| SA055 | Stok bilinmiyor veya sağlayıcı yok | Uydurma fiyat/stok yok; bağımlı commit yok |
| SA056 | Fiyat 2.500,50 TL ve saat 14:30 | Kesin altın anlam; kritik bölünme/kayıp yok |
| SA057 | Türkçe kesme işareti ve ayrıştırılmış Unicode | Kaynak aralık eşlemesi ve ek korunur |
| SA058 | Belirsiz alıntı sözcükte Sezer kuralı | İncelenmiş istisna veya çekimser; genel kural yok |
| SA059 | Desteklenmeyen IPA/SSML veya kodlayıcı sınırı | Uydurma yetenek yok; doğrulanmış güvenli geri düşme veya engel |
| SA060 | F5 hazırlanmış metin yolu | Tek normalizasyon geçişi; aşağı akışta yeniden yazma yok |
| SA061 | Seed 9 öğe tek başına ve dolgulu toplu işte | Gerçek uzunluk başlangıç gürültüsü değişmez; kalibre çıktı karşılaştırması |
| SA062 | Farklı çözücü/uyarlayıcı revizyonu | Bayat önbellek yeniden kullanımı yok; kesin etkin kimlik |
| SA063 | Özel ifade önbelleğine oturumlar arası erişim | Ret; günlükte ham veya özel hash yok |
| SA064 | Geçersiz süre veya sonlu olmayan ses | Oynatmadan önce ret; izinliyse sınırlı aynı seed yeniden deneme |
| SA065 | Hiçbir güvenli düşük adım adayı kaliteyi karşılamaz | Euler32 baz kalır; onaysız etkinleştirme yok |
| SA066 | Sessiz çerçeve | F0 null; sesli kapsam raporlanır |
| SA067 | Sıfır norm veya sonlu olmayan ECAPA vektörü | Benzerlik skoru yok |
| SA068 | Aynı modelden sentetik referans | Öz tutarlılık etiketi; insan kimliği kanıtı değil |
| SA069 | Otomatik vekil çıktı MOS diye adlandırılmış | Etiket reddedilir; insan MOS/ABX NOT_RUN |
| SA070 | Birleşik telefon gidiş-dönüş terim hatası | Birleşik yol kaydedilir; DiT atfı veya eğitim izni yok |
| SA071 | F5 hızı zaten uyguladı | F6 WSOLA tekrarlanmaz |
| SA072 | 0,94–1,06 dışında istenen hız 0,90 | Açık desteklenmiyor/geri düşme; sessiz kırpma değil |
| SA073 | Doğal sınır sessizliği toplam hedefi aşar | Negatif ekleme veya keyfi kırpma yok |
| SA074 | Korumalı/iptal edilmiş sınırda çapraz geçiş | Bypass; örnek sızıntısı yok |
| SA075 | Eksik terminal çerçeveli 48→16/8k | Doğru rasyonel eşleme ve geçerli örnek sayısı; dolgu işaretli |
| SA076 | G.722 16k PCM ile 8k RTP saati | Ayrı hızlar; doğru zaman damgası artışları |
| SA077 | Opus değişken yük | Sabit boyut varsayımı veya PCM enjeksiyonu yok |
| SA078 | AudioSocket kısmi başlık/okuma veya yazma | Kesin ayrıştırıcı; belirsiz gönderim yeniden denenmez |
| SA079 | Kanal FLUSH_MEDIA yeni generation ile yarışır | Özel bariyer yeni medyanın silinmesini önler |
| SA080 | Yalıtılmış PBX veya WebSocket yok | Dondurulmuş kapsama göre ertelendi/HOLD; SIP iddiası yok |
| SA081 | Düzeltme sonra onaylı iki turlu randevu | Beklenen yalıtılmış durum ve bir doğrulanmış fikstür makbuzu |
| SA082 | Alternatifli müsait olmayan slot | Sahte onay veya sessiz randevu yok |
| SA083 | Teknik soru artı müsaitlik çoklu niyeti | Doğru desteklenen sonuçlar ve kaynak başvuruları |
| SA084 | DTMF ile operatöre devir | Tam bir tekilleştirilmiş olay ve fikstür aktarım makbuzu |
| SA085 | Kuyruklu oynatma sırasında söz kesme | Bayat talep yok; UI durumu yerel kapsamla uyumlu |
| SA086 | Yerel kısa ve standart tur | Doğrudan son→ham/render/gönderim süreleri; p95 toplamı değil |
| SA087 | Gerçek Whisper + Qwen + Freya etkin | Aynı M06 zamanlayıcı; gerçek VRAM ve kuyruk kapsamları |
| SA088 | Tur ortasında yerel ASR hatası | İş eylemi yok; doğru kurtarma |
| SA089 | Aynı anlamsal çıktı için önbellek isabet ve ıska | Ayrı metrikler ve etkin kimlik |
| SA090 | Sentetik uç ses loopback'i | Laboratuvar gözlemi etiketi; gerçek duyulur G5 metriği null kalır |
| SA091 | Özel istek beklerken rol değişimi | Eski yanıt gösterilmez; sunucu yetkisi yeniden denetlenir |
| SA092 | Devre dışı kontrolün doğrudan API ile atlatılması | Gerçek arka uç reddeder |
| SA093 | Telemetri boşluğu/yeniden bağlanma | Bayat ve eşitleme gösterilir; uydurma sıfır yok |
| SA094 | Panoda raporlanan mock işlem | Sağlayıcı kapsamı görünür; gerçek başarı değil |
| SA095 | Büyük iz ve hatalarla çevrimdışı kabuk | Sınırlı render/durum; klavye/odak ve temizlik çalışır |
| SA096 | Kalıcı commit'ten önce ve sonra iptal | Önce: etki önlenir; sonra: makbuz uzlaştırılır, bayat konuşma çitlenir |
| SA097 | Simüle GPU OOM veya bilinmeyen yerel tamamlanma | Güvensiz bırakma yok; karantina ve sınırlı kurtarma |
| SA098 | Kuyruk taşması ve yavaş istemci | Sınırlı bellek; yakalama patlaması veya sessiz kayıp yok |
| SA099 | Oturumlar arası sahte akış veya yetki kapsamı | Ret; ses veya veri ifşası yok |
| SA100 | Telemetri/denetim alıcısı hatası | M04 kayıplı gözlem M07 kalıcı güvenliği atlatamaz |
| SA101 | Tek tam yığın yerel görüşme | OOM=0 hedefi, gerçek tepeler ve hatalar ölçülür |
| SA102 | Onaylı ikinci veya dördüncü eşzamanlı oturum | Yalnız önceki basamaktan sonra; test edilen kapasite raporlanır, garanti değil |
| SA103 | Kısmi/ön ısıtma son/TTS ile yarışır | Gerçek öncelik ve adalet; güvensiz önleme yok |
| SA104 | Yük altında tekrarlı iptal/yeniden bağlanma | Sınırlı durgunluk; geçerli yerleşik önbellek sızıntıdan ayrılır |
| SA105 | Bütçe veya termal durma eşiği aşıldı | Alım durur; sahiplenilen işler sonuçlandırılır; kalan NOT_RUN |
| SA106 | Yalnız aşama dağılımlarının p95'i mevcut | Toplam yok; gözlenmediyse doğrudan E2E null |
| SA107 | n=0 veya geçersiz saat/sıfır payda | Metrik nedenle null; sıfır değil |
| SA108 | 100 vaka planlandı, 80 geçti, 20 eksik | Tam payda raporlanır; sahte tam PASS yok |
| SA109 | Aynı deneme beş kez tekrarlandı | Tekrar sayısı bağımsız öğe sayısından ayrı |
| SA110 | Hash'lemeden sonra bildirim yapıtı değişti | Bütünlük incelemesi başarısız; önceki kayıtlar korunur |
| SA111 | İsteğe bağlı iyileştirme düşük performans | Aday kapatılır; zorunlu baz doğrulanır; kapsam kaydedilir |
| SA112 | Zorunlu WER veya değişmez başarısız | Kanıta göre FAIL veya HOLD; eşik yeniden yazılmaz |
| SA113 | Çalıştırma sırasında açıklanamayan ağaç kayması | Dur; uyumsuz kanıt geçersiz |
| SA114 | Test DB'si geri alma isteği | Kanıt korunur ve yalıtılır; üretime asla dokunulmaz |
| SA115 | G4 regresyonundan sonra önerilen düzeltme | Sahibe yönlendirilir; yeni izin ve etkilenen G2/G3/G4 yeniden çalıştırma |
| SA116 | Mock PASS ile zorunlu yerel kanıt eksik | G4 HOLD; yerel kabul değil |
| SA117 | Seçilen tüm zorunlu kontroller gerçek PASS | Bağımsız inceleme yalnız G4 kabulünü onaylayabilir |
| SA118 | G4 sentetik kalıntı LoRA'yı işaret eder | Eğitim yok; hipotez kaydedilir; gerçek kanıt gerekir |
| SA119 | MOS veya gerçek SIP sonucu yok | T5 NOT_RUN; G5 geçti iddiası yok |
| SA120 | G4 kabul edildi ama G5 izni yok | Dur; çağrı, gerçek kayıt veya pilot yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| SG00 | Giriş | Gerçek CG/WG/G2/G3 soyu, kullanıcı izni ve seçilmiş kapsam (SA001–SA005) |
| SG01 | Ortam | Çevrimdışı, yalıtılmış veri, izinli araçlar ve donanım sınırları (SA006–SA010) |
| SG02 | Regresyon | Tüm zorunlu devralınan vakalar + bulunmuş regresyonlar; yeni engelleyici regresyon yok (SA011–SA015) |
| SG03 | Derlem | Haklar, bağımsız altın, gruplu bölümler ve donmuş katmanlar (SA016–SA020) |
| SG04 | Değerlendirici | Bilinen yanıtlı puanlama, ön kayıt, saat ve hata politikası (SA021–SA025) |
| SG05 | F0 | Gerçek zorunlu DSP profili; örnek/DTMF/yankı güvenliği; ölçülmüş kapsamlı hedefler (SA026–SA030) |
| SG06 | F1 | Endpoint, gerçek yakın uç, onay sesi ve sınırlı beklemeler; bayat generation yok (SA031–SA035) |
| SG07 | F2 | Son ve kısmi kalite/güvenlik, zaman damgaları, zamanlama; kısmi etki yok (SA036–SA045) |
| SG08 | F3 | Niyet, RAG kökeni, yetki, DB makbuzları ve bağımlılık doğruluğu (SA046–SA055) |
| SG09 | F4 | Tek normalizasyon, kritik atom bütünlüğü, sözlük ve yetenek (SA056–SA060) |
| SG10 | F5 | Gerçek seçili model profili, RNG/önbellek/kalite/gecikme; kalibre akustik kapsam (SA061–SA070) |
| SG11 | F6 | Render, örnek/hız/duraklama sahipliği, kodek/aktarım kapsamı ve geri düşme (SA071–SA080) |
| SG12 | Mock ürün | Gerçek orkestrasyon ve UI bağlantılı fikstür yolculukları; sahte yerel sonuç yok (SA081–SA085) |
| SG13 | Yerel ürün | Gerçek zorunlu yerel sentetik E2E; doğrudan ölçülmüş dağılımlar ve hatalar (SA086–SA090) |
| SG14 | UI ürün | Gerçek bağlı UI yolculukları, roller, çevrimdışı/bayat/hata ve erişim (SA091–SA095) |
| SG15 | Hata/güvenlik | Sıfır zorunlu güvensiz etki/sızıntı/bayat iddia; sınırlı kurtarma (SA096–SA100) |
| SG16 | Yük | Gerçek tek oturum zorunlu yerel iş yükü; onaylı kapasite basamakları ve temizlik (SA101–SA105) |
| SG17 | Kanıt | Seçilen tüm 120 vaka yükümlülükleri, devralınan kapsam, metrikler ve bütünlük (SA106–SA110 + uygulanabilir tüm SA) |
| SG18 | Geri dönüş | Kusurlar yönlendirilmiş, baz korunmuş, kaynak/yapılandırma geri yükleme ve yeniden yeterlilik (SA111–SA115) |
| SG19 | Bağımsız kabul | SG00–SG18 ve gerçek zorunlu hedefler incelenmiş; G5 ertelemeleri açık; dur (SA116–SA120) |

## 9. Kanıt

`evidence/G4/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `DATASET_MANIFESTS/` (yalnız bildirim ve hash; ses/metin içeriği yalnız izinli fikstürse), `PREREGISTRATION.md` (dondurulmuş metrik, eşik, bölüm, deneme takvimi), `INHERITED_COVERAGE.json`, `LAYER_RESULTS.json`, `JOURNEYS_MOCK.json`, `JOURNEYS_NATIVE.json`, `FAULT_LOAD.json`, `METRICS_SUMMARY.json` (p50/p95/p99, n, hata sayısı, kapsam), `SCOPE_DISPOSITION.md`, `G5_HANDOFF.md`. Katman raporları `data/<aşama>/lab-report-*.json`.

## 10. Geri dönüş

G4 yalnız laboratuvar yapılandırması ve yalıtılmış test DB'si kullanır; çalıştırma sonunda yalnız sahiplenilen geçici durum geri yüklenir. Bir düzeltme gerekiyorsa ilgili pakete gider; ardından etkilenen G2/G3/G4 kanıtı yeniden üretilir. Eşikler sonuçtan sonra değiştirilmez.

## 11. Devir

- **G5:** donmuş profil, sentetik sonuçlar, açık ertelemeler (MOS/ABX, gerçek uç gecikmesi, gerçek SIP) ve bilinen riskler.
- **F5-D:** sentetik kalıntı yalnız hipotezdir; eğitim uygunluğu ancak G5'teki gerçek ve atfedilmiş hatayla açılır.

## 12. Başlatma komutu

```
G4 aşamasını uygula: docs/execution/stages/G4-sentetik-kabul.md.
Kuralları CLAUDE.md'den oku; G2 ve G3 kabulünü, CG/WG gerçek PASS'ini ve kullanıcının dondurduğu kapsamı doğrula.
Sentetik derlem bildirimlerini ve ön kaydı dondur; devralınan regresyonu, F0–F6 katman denemelerini, mock ve yerel yolculukları,
hata ve sınırlı yük testlerini yalıtılmış ortamda çalıştır; gerçek insan/SIP kullanma.
SA001–SA120'yi çalıştır, SG00…SG19'u değerlendir, asama/G4 dalında PR aç ve dur (G5'i başlatma).
```
