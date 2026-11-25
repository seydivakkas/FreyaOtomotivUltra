# F2-C — Sözde akış tanıma: kayan pencere, kısmi ve kararlı önek

> Mevcut Whisper'ı değiştirmeden, konuşma sürerken kayan pencerelerle M06 **P5** kısmi tanıma yapar; pencereleri örnek kökenli hizalamayla birleştirir; bağımsız iki gözlemle desteklenen, **geri alınabilir** kararlı önek üretir; değiştirilemez revizyonları M02 üzerinden yayımlar; sonlandırmada kısmi hattı mühürler ve yetkili final çözmeyi F2-B/M06 **P1** yolundan yapar; F1-C için salt okunur anlamsal ipucu verir. Kısmi veya kararlı önek hiçbir zaman iş eylemi, slot veya onay tetiklemez.

| Alan | Değer |
| --- | --- |
| Kimlik | F2-C |
| Dalga | W4 |
| Öncelik | P1 |
| Önkoşullar | W2_GATE, F2-B, M06 |
| Sonraki | F1-C |
| Bayrak | `f2_pipeline_v2` + M03 profili `f2.partial` (varsayılan KAPALI) |
| Ortam | CPU (sahte yerel yineleyici, sahte saat); gerçek gecikme ölçümü G4 |
| Eski görevler | F2-T22, F2-T23, F2-T24, F2-T25, F2-T26 |
| Kaynak | Bundle `W4/Freya_2_0_F2_C_Agent_Implementation_Package.md`; [F2 spec](../../../stages/F2-speech-recognition/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Bugün tanıma konuşma bittikten sonra başlıyor; uzun cümlelerde ilk sese kadar geçen süre uzuyor ve F1 "konuşma gerçekten bitti mi" sorusunu yalnız akustikle yanıtlıyor. F2-C, final yolunu bozmadan önden bilgi üretir: F1-C anlamsal tur sonu için ipucu alır, ekran kısmi metni gösterebilir. Final sonuç her zaman tam sözün ayrı çözümüdür.

## 2. Başlamadan önce

- [ ] W2_GATE, F2-B, M06 gerçek kabul; onay; soy. F0-B yoksa yeni DAG kenarı eklenmez.
- [ ] Ses, endpoint, ASR, sağlayıcı yineleyici, kısmi bayraklar, genel rotalar ve F3 iş girişleri izlenmiş; iki Whisper yükleyicisi erişilebilirse sahiplik çatışması raporlanır, katı yol üçüncüsünü eklemez.
- [ ] M01 `TurnRef`'in null olabilirliği kontrol edilmiş: kabul edilmiş tur yoksa özel geçici sözleşme veya HOLD; geçersiz M01 olayı yok.
- [ ] Benchmark manifestosu, altın hizalama, gecikme/doğruluk/kararlılık/aşırı yük ölçümleri tanımlanmış; tüm gerçek ölçümler G4 (`NOT_RUN`).

## 3. Kapsam

**Yapılacak:** Envanter; sözleşmeler ve final öncesi kimlik; M03 profili; F1 geçmişinin artımlı kiralanması; pencere planlayıcı; M06 P5 kuyruk; F2-A adaptörü yeniden kullanımı; pencere gözlemi ve normalize jeton eşlemesi; sınırlı örtüşme hizalaması; geri alınabilir kararlı önek; atomik revizyon yayını; F2-B hotword/aday zenginleştirmesi; sonlandırma bağlama ve mühürleme; P1 final hakemliği; kurtarma ve bayat bastırma; F1-C ipucu; F3/M07 yalnız-final sınırı; kaynak/gizlilik; entegrasyon; benchmark protokolü.

**Yapılmayacak:** Yeni ASR modeli veya gerçek akış modeli; kısmi sonuçtan iş eylemi; F1-C sınıflandırıcısı (yalnız ipucu sözleşmesi); final yolunda değişiklik (F2-A/F2-B aynen).

## 4. Dosyalar

```
backend/speech_recognition/streaming/
  scope.py  profile.py  history_lease.py  window_planner.py  p5_queue.py
  observation.py  overlap_align.py  stable_prefix.py  revisions.py  enrichment.py
  finalization.py  recovery.py  hint_projection.py  boundary_guard.py  telemetry.py
tests/speech_recognition/streaming/
evidence/F2-C/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Pencere aritmetiği (aday test profili, 16 kHz)

| Parametre | Değer | Örnek |
| --- | --- | --- |
| İlk pencere için asgari gerçek örnek | 800 ms | 12 800 (12 799'da istek yok) |
| Adım (stride) | 500 ms | 8 000 (daha azında ek istek yok) |
| Olgun sabit pencere | 2 s | 32 000 |
| Onaylı genişleme üst sınırı | 5 s | 80 000 |
| Kararlılık koruma bandı | 320 ms | 5 120 |

Değerler M03 profilindedir ve G4'te ayarlanır; geçersiz asgari/azami/adım/TTL/bütçe reddedilir (sınırsız geri düşme yok). İzin verilen örtüşme genişlemesini aşan zamanlayıcı boşluğu süreksizliktir; uydurma birleşik transkript yok. Aynı bitişin tekrar bildirimi veya örneksiz duvar saati tetiği iş/hayali kapsam üretmez. F1 sert sınır/EOS'ta kısmi canlı aralığın ötesine geçmez.

### 5.2 Kapsam ve kimlik

- F1 adayı yüksek sonra düşükse (onaysız) kısmi yok, sabitleme yok, `TurnRef` ayrılmaz. Onaylı başlangıç ama kabul edilmiş `TurnRef` yoksa **özel yetkili konuşma kapsamı**; uydurma tur/generation yok.
- İki oturumda aynı yerel söz adı ayrı kapsamdır. Yinelenen aday/pencere geri çağrısı idempotent. Aynı istek kimliği farklı bayt/metin → bütünlük çakışması. Eski biçim dönemi/oturum enkarnasyonu yayından önce reddedilir. Sonlandırılmış kapsam yeniden açılmaz.
- Sabitlenmiş sözlük/model/bağlam konuşma ortasında değişirse mevcut kapsam kararlı; sonraki onaylı kapsam yenisini kullanır. Eksik zaman damgası/SNR veya bayat F3 ipucu → null/bilinmiyor; muhafazakâr ipucusuz davranış.

### 5.3 Geçmiş ve zamanlama

- Onaylı başlangıçta tam 320 ms geçmiş bir kez ödünç alınır (örnek kökeni tutarlı); akış başında daha kısa geçmiş → yalnız gerçek ön kayıt, sıfır uydurma yok. Parçalı 16 kHz girdi bir kez birleştirilir; ek yeniden örnekleme yok. Geçersiz hız/bayt/geçerli sayı → açık ret, yerel çağrı yok. Terminal model dolgusu kapsamdan hariç. Aralık içindeki boşluk → boşluk ötesi pencere yok. Halka üzerine yazma sabitlenmiş görünümü bozamaz; sınırda isteğe bağlı iş atlanır. Ardışık kopya için yetersiz rezervasyon → tahsisten önce kısmi atlanır; final rezervi sağlam.
- P5 istekleri: doğru sınıf, kapsam, istek kimliği, son tarih ve maliyet kökeni. Meşgulken üç bekleyen pencere → **en yenisi** bekler, geçersiz kılınanların rezervasyonu bir kez bırakılır. Oturum başına bir çalışan + bir bekleyen; küresel P5 sınırı. P1/P2 hazırsa M06 belgeli öncelik/adillik; P5 yükseltilmez. Gönderimden önce süresi dolan P5 yerel çağrı yapmaz. Kaynak tahmini bilinmiyor veya M06 reddederse isteğe bağlı kısmi atlanır, final etkilenmez. Çalışan P5 sırasında yüksek öncelikli istek gelirse hayali kesme yok.

### 5.4 Gözlem, hizalama ve kararlılık

- Tembel yineleyici: kira somutlaştırma ve gerçek tamamlanma boyunca; kısmi segmentten sonra hata → uydurma OK hipotez yok; terminal kanıtsız kapatma/iptal → erken bırakma veya yeniden deneme yok; aşırı segment/jeton → sınır ve güvenli sonlandırma; yerel bitişten sonra yavaş CPU hizalaması ayrı sınırlı sahiplik.
- Ham metin bayt bayt korunur, karşılaştırma görünümü ayrı. Kelime zaman damgası pencere ofsetine göre açık köken ve yuvarlamayla örnek aralığına; negatif/NaN/ters/aralık dışı → zamanlama üst verisi reddedilir; zaman damgası yoksa null ve yalnız onaylı muhafazakâr metin eşleşmesi. Plaka/telefon/VIN/motor kodu bulanık değiştirilmez. `avg_logprob` ve kelime olasılığı doğru puan türüyle.
- Örtüşme hizalaması: yalnız desteklenen örtüşmede tekilleştirme; farklı örnek aralıklarında meşru tekrar korunur; zamanlamasız belirsiz tekrar → belirsizlik, güvensiz silme veya kararlı uzatma yok; örtüşmede değişen sayı/model → çatışma korunur; sonraki pencerede olumsuzluk → kararsız metin revize edilir; kenarı aşan kısmi kelime tamamlanana kadar kararlılık dışı; aşırı yük sonrası örtüşmeyen pencereler → açık boşluk, eski kararlı ipucu geçersiz; DP/jeton sınırı aşılırsa isteğe bağlı sonuç bastırılır.
- **Kararlı önek:** ilk geçerli hipotez `PARTIAL`; tek gözleme dayalı kararlı önek yok. Yeni kapsamlı ikinci karşılaştırılabilir gözlem → uygun iç bitişik önek kararlı olabilir. Aynı sesin iki kez çözülmesi bağımsız sayım değildir. 320 ms koruma bandındaki jeton yeni kararlılığa terfi etmez. Pencere desteklenen önekin ötesine kayarsa köken korunur ama taze destek sayılmaz. Önceki kararlı jeton çelişilirse önek daralır/sıfırlanır, revizyon artar (kalıcı commit yok). İzlenemeyen köken → kararlı durum/ipucu geçersiz. "Qashqai" kararlı, ardından "değil" → varlık onayı yok, kutupluluk korunur.

### 5.5 Yayın, final ve F3 sınırı

- Revizyonlar değiştirilemez ve M02 atomik kabulüyle; sürüm/kapsam monoton. Yeni kısmi sonrası eski geri çağrı reddedilir; yinelenen yayın tek revizyon; yavaş gözlemci sınır içinde birleştirilir (girişi bloklamaz, revizyon boşlukları açık); karşılaştırma ile ekleme arasındaki iptal çitlenir.
- Önceki spekülatif kısmiden gelen hotword sonraki çözücüye varsayılan olarak verilmez (yalnız sabit önceki kabul edilmiş bağlam). Aday eşleyici fonetik eşleşmede yalnız aday üretir.
- **Sonlandırma:** kısmi hat atomik olarak mühürlenir, bekleyenler çıkarılır; final çözüm tam sonlandırılmış aralık (ön/son kayıt dahil) üzerinde, F2-B/M06 P1; tek mantıksal final talebi; onaylı ikinci deneme en fazla bir (toplam iki); kısmi final ham metne eklenmez; çelişen korumalı değerde F2-B netleştirme; iki deneme de başarısız/`NO_SPEECH` → tipli OK dışı final, kararlı metin finale terfi etmez.
- **F3/M07:** `PARTIAL`/`STABLE_PREFIX` içindeki "evet" veya "randevu oluştur" normal yönlendirme, slot/onay, korunan okuma, araç, LLM tetiklemez. Geçici sonucu `FINAL` diye yeniden etiketleme veya kabul edilmiş finali tekrar oynatma M02/F3 köken kapısında reddedilir.

### 5.6 F1-C ipucu

Aynı kapsamda taze kararlı/kısmi devam ipucu: salt okunur, sınırlı izdüşüm; kapsam, belirsizlik ve saatle. Bayat/süresi dolmuş, farklı dönem/saat, mühürlü veya boşluklu ipucu → ipucu yok; akustik geri düşme **ek bekleme olmadan**. F1-C yoksa test tüketicisi devri doğrular; F1-A davranışı değişmez.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F2-C.01 | Ön kontrol | Onay, çekirdek/W2 matrisleri, F2-B/M06 kabulü ve soy | `F2_C_PREFLIGHT.json`; PS01–PS04 |
| F2-C.02 | Envanter | Ses, endpoint, ASR, sağlayıcı yineleyici, kısmi bayraklar, genel rotalar, F3 iş girişleri; M00 kimlikleri | PS05–PS08 |
| F2-C.03 | Sözleşmeler | M01/M02/M06/F1; final öncesi kimlik ve değiştirilemez sahiplik; özel geçici olay gerekip gerekmediği | PS09–PS16 |
| F2-C.04 | Profil | M03 onaylı görüntüler, yetenekler, etkin ayarlar ve sınırlı profil; eski varsayılanlar | PS17–PS20 |
| F2-C.05 | Geçmiş kiralama | F1 onaylı konuşma geçmişinden artımlı görünümler; kesin aralık/biçim, ön kayıt ve gerçek sayılar | PS21–PS28 |
| F2-C.06 | Pencere planlayıcı | Belirlenimci ısınma, adım, aralık sınırları, örtüşme ve boşluk geri düşmesi; pencere aritmetiği belgeli | PS29–PS36 |
| F2-C.07 | P5 kuyruk | Mevcut M06 P5; yalnız-en-yeni değişim; oturum başına bir çalışan + bir bekleyen; sonlu küresel sınırlar | PS37–PS44 |
| F2-C.08 | Adaptör | F2-A adaptörü, etkin model/beam/kelime zaman damgası yetenekleri, sınırlı yerel yineleyici ve tamamlanma | PS45–PS49 |
| F2-C.09 | Pencere gözlemi | Değiştirilemez ham gözlem ve normalize jeton eşlemesi; Türkçe harf, noktalama, korumalı kimlikler | PS50–PS56 |
| F2-C.10 | Örtüşme hizalaması | Jeton/örnek kökenli sınırlı hizalama; tekrar, belirsizlik, atlanan aralıklar ve çatışma tespiti | PS57–PS64 |
| F2-C.11 | Kararlı önek | Bağımsız kabul edilmiş pencereler, koruma bandı, karşılaştırılabilir bağlamla geri alınabilir kanıt | PS65–PS72 |
| F2-C.12 | Revizyon yayını | M02 atomik kabul; monoton sürüm/kapsam; yavaş tüketici birleştirme | PS73–PS76 |
| F2-C.13 | Zenginleştirme | F2-B sınırlı hotword ve isteğe bağlı aday; spekülatif bağlam geri beslemesi, sayısal değişiklik veya yetki yok | PS77–PS78 |
| F2-C.14 | Sonlandırma bağlama | Kısmi hattı atomik mühürle, bekleyenleri çıkar; kesin final ses uygun kalır | PS79–PS82 |
| F2-C.15 | Final hakemliği | F2-B/M06 P1 yetkili final çözmesi; tek mantıksal final talebi; en fazla onaylı ikinci deneme; kısmi ekleme yok | PS83–PS88 |
| F2-C.16 | Kurtarma | Sınırlı kurtarma, bayat sonuç bastırma, iptal kontrolleri; fiziksel tamamlanma/karantina ayrımı | PS89–PS92 |
| F2-C.17 | F1-C ipucu | Salt okunur en son anlamsal ipucu; aynı kapsam TTL/kapsamı; eksik ipucunda akustik geri düşme | PS93–PS95 |
| F2-C.18 | F3/M07 sınırı | Kısmi/kararlı atlamalara karşı yalnız-final kabulü; slot, onay, korunan okuma, öneri yok | PS96–PS97 |
| F2-C.19 | Kaynak ve gizlilik | Sınırlı temizlik, başvuru sahipliği, güvenli telemetri ve izin listesi; sayaç ve terminal uzlaştırma | PS98 |
| F2-C.20 | Entegrasyon | Gerçek F1-A/F2-A/B/M02/M06/F3 yolu sahte yerel sınırla; F1-B/F6-B, DTMF, eski bayraklar korunur | PS99 |
| F2-C.21 | Benchmark protokolü | Tekrar üretilebilir manifest, altın hizalama, gecikme/doğruluk/kararlılık/aşırı yük ölçümleri; gerçekler NOT_RUN | `BENCHMARK_PROTOCOL.md` |
| F2-C.22 | Testler | PS01–PS100 onaylı yalıtılmış anlık görüntüde; sahte saat/yerel sağlayıcı sınırları | Tüm testler çalıştırılmış |
| F2-C.23 | Regresyon ve geri dönüş | Etkilenen önceki testler, M00 özellik matrisi, bütünlük, güvenli yalnız-final geri dönüşü | PS100 |
| F2-C.24 | Kabul ve devir | F2-C-G00…G19 bağımsız inceleme; F1-C/F3/F0-B devri; hazırlık yalnız kanıttan | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| PS01 | Onay yok | HOLD; kaynak değişikliği veya sağlayıcı çağrısı yok |
| PS02 | Çekirdek kanıtı var ama W2 yalnız hazır bayrağı | HOLD; gerçek WG00–WG11 PASS gerekir |
| PS03 | F2-B veya M06 kabul bildirimi yok/bayat | Kesin soy uyuşmazlığıyla HOLD |
| PS04 | Tüm gerçek önkoşullar geçerli, sonraki isteğe bağlı F0-B yok | Bağımlılık kontrolü geçer; eklenen DAG kenarı yok |
| PS05 | Envanterde eski yalnız-final ve deneysel eşleyici | İki yol, gerçek özellik kimlikleri ve etkinleştirme eşlenir; uydurma yok |
| PS06 | Erişilebilir iki mevcut Whisper yükleyicisi | Sahiplik çatışması raporlanır; katı yol üçüncüsünü ekleyemez |
| PS07 | Mevcut sağlayıcı tembel segmentleri işler | Adaptör/kira korunur; tamamlanma noktası kaydedilir |
| PS08 | KAPALI kip taban tekrarı | Aynı eski yol/çıktı/API ve yan etkiler; sıfır yeni P5 işi |
| PS09 | Onaylı başlangıçtan önce F1 adayı yüksek sonra düşük | Kısmi yok, sabitleme tutulmaz, `TurnRef` ayrılmaz |
| PS10 | Kabul edilmiş `TurnRef` olmadan onaylı başlangıç | Özel yetkili konuşma kapsamı; uydurma tur veya generation yok |
| PS11 | Gerçek M01 null turu reddeder | Özel geçici sözleşme veya HOLD; geçersiz M01 olayı yok |
| PS12 | İki oturum aynı yerel söz adını kullanır | Ayrı kapsam; paylaşılan değiştirilebilir geçmiş yok |
| PS13 | Yinelenen aday veya pencere geri çağrısı | Tek uygun kapsam/pencere; idempotent kesin tekrar |
| PS14 | Değiştirilmiş bayt/metinle aynı istek kimliği | Bütünlük çakışması; üzerine yazma veya yinelenen çıktı yok |
| PS15 | Eski biçim dönemi veya oturum enkarnasyonu | Yayın/okumadan önce ret |
| PS16 | Sonlandırılmış kapsam ve sonra yeniden kullanılan kimlik denemesi | Terminal eski kapsam yeniden açılamaz |
| PS17 | Kısmi bayrak kapalı/varsayılan | Kısmi zamanlayıcı etkinliği yok; final değişmez |
| PS18 | Geçersiz asgari/azami pencere, adım, TTL veya bütçe | Profil reddedilir; sınırsız geri düşme yok |
| PS19 | Konuşma ortasında sabit sözlük/model/bağlam değişir | Mevcut kapsam kararlı; sonraki onaylı kapsam yeni görüntüyü kullanır |
| PS20 | Eksik zaman damgası/SNR veya bayat F3 ipuçları | Null/bilinmiyor üst veri; muhafazakâr ipucusuz davranış; eklenen bağımlılık yok |
| PS21 | Tam 320 ms geçmişle onaylı başlangıç | Tam bir kez ödünç; örnek kökeni tutarlı |
| PS22 | Akış başında daha kısa geçmiş | Yalnız gerçek ön kayıt; sıfır uydurma yok |
| PS23 | Parçalı geçerli 16 kHz giriş | Kesin örnek aralığı bir kez birleştirilir; ek yeniden örnekleme yok |
| PS24 | Geçersiz çerçeve hızı, bayt uzunluğu veya geçerli sayı | Açık ret; yerel çağrı yok |
| PS25 | Terminal yalnız-model dolgusu | Gerçek kapsam dolguyu hariç tutar |
| PS26 | Artımlı aralık içinde boşluk | Boşluk ötesi pencere veya uydurma sessizlik yok |
| PS27 | Çalışan görünüm sabitken halka üzerine yazma | Sabitleme sahipliğine uyulur; sınırda isteğe bağlı iş atlanır |
| PS28 | Ardışık kopya için yetersiz rezervasyon | Tahsisten önce kısmi ret/atlama; final rezervi sağlam |
| PS29 | Aday test profilinde 12 799 gerçek örnek | Henüz kısmi istek yok |
| PS30 | 12 800 örnek | İlk uygun pencere kesin başlangıç/bitişi kullanır |
| PS31 | 8 000'den az ek gerçek örnek | 500 ms adımda ek istek yok |
| PS32 | Sabit 2 s olgun pencere | Tam 32 000 örnek aralığı; sınırlı görünüm |
| PS33 | 5 s'ye onaylı genişleme | En fazla 80 000 örnek; gerçek örtüşme hesaplanır |
| PS34 | İzin verilen örtüşme genişlemesini aşan zamanlayıcı boşluğu | Süreksizlik; uydurma birleşik transkript yok |
| PS35 | Aynı bitiş tekrar bildirilir / örneksiz duvar zamanlayıcısı | Yinelenen iş veya hayali kapsam yok |
| PS36 | Sınırda F1 sert sınır/EOS | Kısmi canlı aralığın ötesine geçmez; kesin final aralığı bağımsız |
| PS37 | P5 isteği oluşturulur | Doğru M06 sınıfı, kapsam, istek kimliği, son tarih ve maliyet kökeni |
| PS38 | Zamanlayıcı meşgulken üç bekleyen pencere | Bir en yeni bekleyen; geçersiz kılınan rezervasyonlar bir kez bırakılır |
| PS39 | Bir yerel kısmi zaten çalışıyor | Aynı oturum için ikinci çalışan kısmi yok |
| PS40 | Birçok oturumda küresel P5 sınırı | Bekleyen/iş sınırlı; açlık geçersiz kılma veya kaçak bellek yok |
| PS41 | P5 kuyruktayken P1/P2 hazır | M06 belgeli öncelik/adillik; P5 yükseltilmez |
| PS42 | P5 gönderimden önce süresi doldu | Yerel çağrı yok; güvenli temizlik |
| PS43 | Kaynak tahmini bilinmiyor veya M06 reddeder | İsteğe bağlı kısmi atlanır/ertelenir; final yolu etkilenmez |
| PS44 | P5 çalışırken yüksek öncelikli yeni istek | Hayali kesme yok; terminal/karantinaya kadar uygun yerel kira |
| PS45 | `transcribe()` tembel yineleyici döndürür | Kira somutlaştırma ve gerçek tamamlanma boyunca tutulur |
| PS46 | Yineleyici kısmi segmentten sonra hata fırlatır | Uydurma OK hipotezi yok; terminal durum kanıtlanır veya karantina |
| PS47 | Terminal kanıtsız yineleyici kapatma / Future.cancel | Erken bırakma veya yeniden deneme yok; M06 bekleyen yerel işi izler |
| PS48 | Sağlayıcı aşırı segment/jeton/üst veri döndürür | Sınırlar uygulanır, güvenli sonlandırma; gizli sınırsız liste yok |
| PS49 | Sağlayıcı bitişinden sonra yavaş CPU hizalaması | Yerel kira M06'da bırakılır; ayrı sınırlı CPU sahipliği |
| PS50 | Baştaki/sondaki boşluklu ham metin ve Türkçe Unicode | Metin içeriği bayt bayt korunur; karşılaştırma görünümü ayrı |
| PS51 | Pencere ofsetine göre saniye cinsinden kelime zaman damgası | Açık köken ve yuvarlamayla doğru örnek aralığı |
| PS52 | Negatif, NaN, ters veya aralık dışı zaman damgası | Zamanlama üst verisi reddedilir; null/geçersiz durum; uydurma hizalama yok |
| PS53 | Sağlayıcı kelime zaman damgası döndürmez | Null zamanlama; yalnız onaylı muhafazakâr metin eşleşmesi |
| PS54 | Çok kelimeli takma ad ve birleşen karakterler | Kaynak aralıkları beyan edilen temsile işaret eder, bayt indeksine değil |
| PS55 | Kısmide plaka/telefon/VIN/motor kodu | Bulanık değiştirme yok; korumalı aralık bütünlüğü |
| PS56 | Yerel `avg_logprob` ve isteğe bağlı kelime olasılığı | Doğru puan türü; sahte kalibre güven yok |
| PS57 | Bir ifadeyi paylaşan iki örtüşen pencere | Yalnız desteklenen örtüşmede tekilleştirme; türetilmiş metin kökeni tam |
| PS58 | Farklı örnek aralıklarında meşru tekrarlanan sözcük | İkisi korunur; yalnız metne dayalı küresel tekilleştirme yok |
| PS59 | Zamanlamasız belirsiz örtüşmede tekrarlanan jeton | Belirsizlik işaretlenir; güvensiz silme veya kararlı uzatma yok |
| PS60 | Örtüşmede değişen sayı/model | Çatışma korunur; uydurma değer veya düzeltme yok |
| PS61 | Sonraki pencerede olumsuzluk gelir | Kararsız metin revize edilir; kutupluluk kaybı yok |
| PS62 | Kısmi kelime kenarı aşar | Tamamen gözlenen jetona kadar kararlılık dışı |
| PS63 | Aşırı yükten sonra örtüşmeyen pencereler | Açık boşluk, yalnız yerel görünüm; eski kararlı ipucu geçersiz |
| PS64 | Hizalama sınırlı DP/jeton sınırlarını aşar | İsteğe bağlı sonuç bastırılır; sessiz tam metin kırpma yok |
| PS65 | İlk geçerli hipotez | PARTIAL; tek gözleme dayalı kararlı önek yok |
| PS66 | Yeni kapsamlı ikinci karşılaştırılabilir gözlem | Uygun iç bitişik önek kararlı olabilir |
| PS67 | Aynı sesin iki kez çözülmesi | Bağımsız sayım değişmez; sahte kararlılık yok |
| PS68 | 320 ms sınır koruması içindeki jeton | Yeni kararlı terfiden hariç |
| PS69 | Pencere desteklenen önekin ötesine kayar | Geçerli köken korunur; taze destek sayılmaz |
| PS70 | Önceki kararlı jeton çelişilir | Önek daralır/sıfırlanır, daha yüksek revizyon; kalıcı commit yok |
| PS71 | İzlenemeyen köken veya geçmiş sınırı | Kararlı durum/ipucu geçersiz; tahmini geçmiş yok |
| PS72 | Kararlı "Qashqai" ardından "değil" | Varlık onayı yok; kutupluluk korunur |
| PS73 | Yeni kısmi yayımlandı sonra eski geri çağrı gelir | Eski kapsam/istek reddedilir; revizyon gerilemesi yok |
| PS74 | Yinelenen başarılı yayın denemesi | Tek revizyon ve ikinci gözlemci olayı yok |
| PS75 | Gözlemci kuyruğu yavaş/dolu | Sınır içinde birleştirme; girişi bloklamaz; revizyon boşlukları açık |
| PS76 | Karşılaştırma ile ekleme bariyeri arasında iptal | Atomik sahip çiti bayat yayını engeller |
| PS77 | Önceki spekülatif kısmiden hotword | Varsayılan olarak sonraki çözücüye verilmez; yalnız sabit önceki kabul edilmiş bağlam |
| PS78 | Aday eşleyici fonetik eşleşme görür | Yalnız aday; korunan okuma/katalog doğrusu veya slot değişikliği yok |
| PS79 | Bekleyen sessizlik kısmisinden kısa sonlandırılmış aralık | Final çözme kesin kesimle; kısmi ipuçları iptal |
| PS80 | Yinelenen sonlandırma olayı | Tek mantıksal final talebi/`TurnRef`; yinelenen çıkarım yok |
| PS81 | Sonlandırma çalışan kısmiyle yarışır | Final kabulünden önce mühür; sonraki kısmi yayını yok |
| PS82 | Uyuşmayan kapsam/dönem/başlangıçla sonlandırma | Bağlama reddedilir; konuşmalar arası yeniden kullanım yok |
| PS83 | Geçerli final isteği | P1; mevcut ön/son kayıt dahil kesin tam sonlandırılmış söz |
| PS84 | Kısmi finalden farklı ham | Final ham dokunulmaz; daha yüksek revizyon görüntü/ipucunu geçersiz kılar |
| PS85 | İsteğe bağlı alternatif final açık, birincil terminal doğrulanmış | Taze M06 kabulü; tek son tarih altında en fazla iki ardışık deneme |
| PS86 | Alternatif birincinin korumalı değeriyle çelişir | Mevcut F2-B netleştirme politikası; birleştirilmiş ham veya uydurma kesinlik yok |
| PS87 | İki final denemesi de başarısız / NO_SPEECH | Politikaya göre tipli OK dışı final veya teslim yok; kararlı metin asla terfi etmez |
| PS88 | Alternatif yok, bütçe tükendi veya son tarih geçti | Üçüncü deneme yok; güvenli ilk uygun sonuç veya açık hata |
| PS89 | Giriş kısmisi sırasında yalnız generation çıkış kesmesi | İlgisiz giriş kapsamı korunur; yanlış ASR iptali yok |
| PS90 | Yerel kısmi aktifken tur/söz iptali veya oturum kapanışı | Yayın çitlenir; istek iptal; kira terminale kadar |
| PS91 | Sağlayıcı sağlıksız / OOM / bilinmeyen tamamlanma | Karantina M06'da; kör yeniden deneme, model değişimi veya zorla sıfırlama yok |
| PS92 | Yeniden bağlanmadan sonra geç tamamlanma / tekrarlı temizlik | Yalnız eski kaynaklar bir kez; yeni kapsam değişikliği yok; defter uzlaşır |
| PS93 | Taze aynı kapsamlı kararlı/kısmi devam ipucu | Kapsam, belirsizlik ve saatle salt okunur sınırlı izdüşüm |
| PS94 | Bayat/süresi dolmuş, farklı dönem/saat, mühürlü veya boşluklu ipucu | İpucu yok; ek beklemesiz akustik geri düşme |
| PS95 | Gelecek F1-C yok ve isteğe bağlı F0-B üst verisi erişilemez | Test tüketicisi devri doğrular; F1-A davranışı değişmez |
| PS96 | PARTIAL/STABLE_PREFIX "evet" veya "randevu oluştur" içerir | F3 normal yönlendirme, slot/onay, korunan okuma, araç, LLM yok |
| PS97 | Geçici sonucu FINAL diye yeniden etiketleme veya kabul edilmiş finali tekrar | M02/F3 köken kapısı sahte girdiyi reddeder; geçerli final korunur |
| PS98 | Metinde sentetik gizli/kişisel veri, bozuk sağlayıcı hatası | Güvenli izin listeli telemetri; metin/PCM/özel özet yok; sayaçlar uzlaşır |
| PS99 | Gerçek yalıtılmış F1 → F2 → F3 yolu, iki oturum, DTMF, yalnız-final geri dönüşü | Gerçek orkestrasyon, yalnız yerel sahte; korunan davranış |
| PS100 | Eksik ölçümlü ve kasıtlı hatalı benchmark/kanıt bildirimi | Dürüst NOT_RUN/HOLD/FAIL; sentetik puan yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F2-C-G00 | Ön kontrol | Çekirdek/W2 ve doğrudan bağımlılıklar kabul; yürütme yetkisi ve soy; PS01–PS04 |
| F2-C-G01 | Sahiplik | Mevcut tek çözücü/model/sahip envanteri; KAPALI uyum; PS05–PS08 |
| F2-C-G02 | Final öncesi kimlik | Final öncesi konuşma korelasyonu; spekülatif `TurnRef` yok; M01/M02 eşlemesi; PS09–PS16 |
| F2-C-G03 | Profil | Sabit profil/sözlük/yetenek ve eksik üst veri geri düşmesi; PS17–PS20 |
| F2-C-G04 | Geçmiş | Artımlı sahiplik, kesin örnek aralıkları ve sınırlı bellek; PS21–PS28 |
| F2-C-G05 | Pencere | Kayan pencere, adım, örtüşme/boşluk ve sert sınırlar; PS29–PS36 |
| F2-C-G06 | P5 | Sınırlı P5 zamanlama, final rezervi, birleştirme ve atlama yok; PS37–PS44 |
| F2-C-G07 | Yerel davranış | Mevcut adaptör üzerinden gerçek yerel yineleyici/tamamlanma/kira; PS45–PS49 |
| F2-C-G08 | Ham metin | Ham transkript, Unicode, zaman damgaları ve korumalı kimlik; PS50–PS56 |
| F2-C-G09 | Hizalama | Kökenli örtüşme hizalaması ve belirsizlik geri düşmesi; PS57–PS64 |
| F2-C-G10 | Kararlılık | Geri alınabilir kararlı önek kanıtı; sahte yeniden onay yok; PS65–PS72 |
| F2-C-G11 | Yayın | Atomik değiştirilemez revizyonlar ve sınırlı gözlemciler; PS73–PS76 |
| F2-C-G12 | Zenginleştirme | Bağlam/hotword ve aday zenginleştirme güvenliği; PS77–PS78 |
| F2-C-G13 | Final | Final mühür/bağlama ve mevcut P1 final hakemliği; PS79–PS88 |
| F2-C-G14 | Kurtarma | İptal, kurtarma, kaynak temizliği ve karantina; PS89–PS92 |
| F2-C-G15 | İpucu | F1-C danışma ipucu sözleşmesi ve akustik geri düşme; PS93–PS95 |
| F2-C-G16 | F3 sınırı | Yalnız-final F3/M07 sınırı ve gizlilik; PS96–PS98 |
| F2-C-G17 | Test kanıtı | PS01–PS100 kanıtla çalıştırılmış; zorunlu iddialar geçmiş |
| F2-C-G18 | Entegrasyon ve regresyon | Gerçek katmanlar arası bütünleşme, regresyonlar, bütünlük, geri dönüş, benchmark protokolü; PS99–PS100 |
| F2-C-G19 | Devir | Bağımsız inceleme ve hazırlık/sınırlamalarla aşağı akış devri |

## 9. Kanıt

`evidence/F2-C/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F2_C_PREFLIGHT.json`, `STREAMING_INVENTORY.json`, `PRE_FINAL_IDENTITY.md`, `WINDOW_ARITHMETIC.md`, `P5_QUEUE_POLICY.md`, `OVERLAP_ALIGNMENT_SPEC.md`, `STABLE_PREFIX_SPEC.md`, `FINALIZATION_SPEC.md`, `HINT_CONTRACT.md`, `BENCHMARK_PROTOCOL.md` (kısmi gecikme, kararlılık/geri alma oranı, final WER etkisi, aşırı yük — G4'te), `TEST_MATRIX.json`.

## 10. Geri dönüş

`f2.partial` kapalı: yalnız-final F2-A/F2-B yolu aynen. Kısmi hiçbir zaman iş etkisi üretmediği için veri geri dönüşü gerekmez. Kod `git revert`.

## 11. Devir

- **F1-C:** salt okunur ipucu (`STABLE_PREFIX` devam olasılığı değil, kanıtı; kapsam, tazelik, saat). İpucu yoksa F1-C akustik geri düşmeyi beklemeden kullanır.
- **F3:** yalnız `FINAL` girdiler; kısmi yalnızca görüntü/ipucu.
- **F0-B:** isteğe bağlı SNR kanıtı profil seçimine girdi olabilir; zorunlu bağımlılık değil.
- **G4:** kısa final ASR p95 ≤ 500 ms ve uçtan uca ilk ses 1,2 s hedeflerine katkı ölçümü.

## 12. Başlatma komutu

```
F2-C paketini uygula: docs/execution/packages/W4/F2-C-akis-tanima.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F2-B ve M06 kabulünü doğrula; M01 TurnRef null olabilirliğini kontrol et.
f2.partial (varsayılan kapalı) altında kayan pencere P5 kısmi tanıma, örnek kökenli örtüşme hizalaması ve
geri alınabilir kararlı öneki kur; sonlandırmada mühürle ve finali P1 ile ayrı çöz; kısmi asla iş eylemi tetiklemesin.
PS01–PS100'ü çalıştır, F2-C-G00…G19'u değerlendir, paket/F2-C dalında PR aç ve dur.
```
