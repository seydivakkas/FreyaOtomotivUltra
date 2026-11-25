# F0-B — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller

> F0-A cephesinin arkasında: F6-B oynatma referansıyla hizalanmış CPU tabanlı yankı giderme (AEC), double-talk gözlemi (karar değil), konuşmayla geçitlenmiş uyarlanır gürültü kestirici, otomotiv gürültü profilleri, mevcut spektral bastırıcının sınırlı kazançla adaptasyonu, temiz konuşma koruması, mevcut HPF/AGC/limiter/gate uyumu, isteğe bağlı RNNoise yetenek noktası ve SNR/ERLE ölçüm tanımları. Tek giriş sahibi; çift AEC veya çift bastırma yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F0-B |
| Dalga | W4 |
| Öncelik | P1 |
| Önkoşullar | W2_GATE, F0-A, F6-B |
| Sonraki | F1-C |
| Bayrak | `f0_pipeline_v2` + M03 profili `f0.adaptive_dsp` (varsayılan KAPALI; profiller: sessiz, park, seyir, atölye, rüzgâr, telefon) |
| Ortam | CPU (sentetik sinyaller; gerçek araç kaydı G5) |
| Eski görevler | F0-T09, F0-T10, F0-T11, F0-T12, F0-T13, F0-T15, F0-T16, F0-T17, F0-T18, F0-T19, F0-T20, F0-T25, F0-T26 |
| Kaynak | Bundle `W4/Freya_2_0_F0_B_Agent_Implementation_Package.md`; [F0 spec](../../../stages/F0-audio-acquisition/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Araç içinde motor uğultusu, klima/fan, rüzgâr ve Freya'nın kendi sesinin geri dönmesi tanıma doğruluğunu düşürür. Ancak aşırı filtreleme konuşmayı bozar ve "RNNoise daha iyi" gibi iddialar ölçülmeden yapılamaz. F0-B uyarlanır işlemleri **ölçülebilir, sınırlı ve geri alınabilir** biçimde ekler; iki yöntem ölçülmeden arka arkaya uygulanmaz.

## 2. Başlamadan önce

- [ ] W2_GATE, F0-A, F6-B kabul edilmiş; onay; uyumlu soy.
- [ ] Gerçek giriş DSP'si, hızlar, filtreler, tarayıcı ayarları (istenen/etkin), AEC/DTMF, referanslar ve eski rotalar M00 kimlikleriyle envanterde.
- [ ] Tarayıcı AEC'si istendi ama etkin değilse durum `UNKNOWN`; telefon hattında yerel AEC iddiası yok.
- [ ] RNNoise bağlaması (ABI/lisans/hız/çerçeve/ölçek) yalnızca envantere alınır; kurulum yapılmaz.
- [ ] Gürültü korpusu, seed, beklenen metrik tanımları ve toleranslar **önceden** dondurulur (F0-B.21).

## 3. Kapsam

**Yapılacak:** Tek giriş sahibi ve kapalı varsayılan; sözleşmeler; M03 profili ve yetenekleri; F6-B referans okuyucu; hız köprüsü ve saat eşlemesi; sınırlı gecikme kestirici; CPU AEC adaptörü/prototipi; double-talk gözlemi; uyarlanır gürültü kestirici; otomotiv profilleri ve spektral bastırma; temiz konuşma koruması; mevcut HPF/AGC/limiter/gate; RNNoise yetenek noktası; SNR/ERLE tanımları; örnek defteri ve DTMF; kaynak yönetimi; gizlilik; entegrasyon; fikstür ve benchmark protokolü.

**Yapılmayacak:** Söz kesme/yeniden başlatma kararı (F1); konuşmacı ayrıştırma; GPU işlemi; RNNoise kurulumu veya varsayılan geçişi; tarayıcı arayüz değişikliği (Studio paneli G3); gerçek araç ölçümü (G5); kalıcı kayıt.

## 4. Dosyalar

```
backend/audio_frontend/adaptive/
  profile.py  reference_reader.py  rate_clock_bridge.py  lag_estimator.py  aec.py
  double_talk.py  noise_estimator.py  automotive_profiles.py  spectral_suppressor_adapter.py
  clean_speech_guard.py  legacy_stages.py  rnnoise_capability.py  quality_metrics.py
  sample_accounting.py  resources.py  telemetry.py
tests/audio_frontend/adaptive/   tests/audio_frontend/lab/
evidence/F0-B/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Aşama sırası (katı kip)

```
F0-A doğrulama/dönüşüm ─► ham DTMF kolu (değişmez)
  └─► HPF (mevcut) ─► [AEC: F6-B referansı + hizalama + double-talk geçidi]
        ─► uyarlanır gürültü kestirimi ─► TEK bastırıcı (spektral VEYA onaylı ablasyonda RNNoise)
        ─► temiz konuşma koruması ─► AGC/gate/limiter (mevcut) ─► 16 kHz ─► F1
```

Bayrak kapalıyken F0-A eski yolu aynen; yeni referans okuması yok. Aynı anda iki tam bastırma veya iki AEC yapılandırması reddedilir. Gölge kip fazladan ses, DTMF veya kontrol kararı yayınlamaz.

### 5.2 Referans, hizalama ve AEC

- Referans yalnızca F6-B'nin **talep edilmiş** son DSP PCM'idir (kesin bayt, nesil, aralık, `SERVER` kökeni). Yalnız kuyruktaki veya talepten önce silinmiş çerçeveler için uydurma referans/sessizlik yok. Kısmi/bilinmeyen aktarım teslimi taşınır; öğrenme engellenir veya sınırlı güvenli politika. Yanlış oturum/yetkisiz eşleme okunmaz. Çıkış dönemi değişince eski eşleme geçersiz. Duraklatma/kesmede uygun sınırlı geçmiş yankı kuyruğu tutulur, giriş sürer. Tahliye/eksik aralık açık boşluk; gizli sıfır yok. Yavaş okuyucu oynatmayı geciktirmez.
- 8k/16k referans → 16k işleme hızına durumlu köprü (doğru ofset/faz ve gecikme). Ortak doğrulanmış saatte aralık hesabı; eşlenmemiş saatlerde mutlak gecikme `UNKNOWN`.
- Gecikme kestirici: bilinen pozitif gecikmeli yankıda doğru işaret ve gecikme (dondurulmuş tolerans); arama aralığı dışında uydurma sınır kestirimi yok; sabit/sıfır enerjili referansta payda hatası ve geçerli hizalama yok; tekrarlı motor harmoniği/rakip korelasyon tepeleri → marj geçidi belirsiz gecikmeyi reddeder; yetersiz geçmiş → öğrenme engellenir; gecikme sıçraması → sınırlı kayma/yeniden edinme.
- AEC: bilinen nedensel FIR yankısında sınırlı yakınsama ve sonlu artık (yalnız fikstür ERLE'si); referans kaybında dondur/sıfırla/bypass; katsayı taşması/sonlu olmayan ara değerde güvenli hata; düşük enerji ve epsilon kenarında sonlu ağırlıklar; referans rotası değişince eski filtre kullanılmaz; temiz yakın uç girişinde koşulsuz susturma veya çift AEC yok.

### 5.3 Double-talk ve gürültü kestirimi

- Double-talk yalnızca **kanıt** üretir (`DOUBLE_TALK_LIKELY` vb.) ve AEC güncellemesini geçitler; duraklatma/devam/kesme kararı vermez (F1'in işi). Bayat/yabancı F1 ipucu yok sayılır; aynı pencerenin F1 gözlemi beklenmez (döngüsel bekleme yok, yalnız nedensel önceki ipucu).
- Gürültü kestirici: sınırlı PSD durumu; yalnız uygun geçitte güncelleme; konuşma sıfırıncı örnekte başlarsa ilk aralık gürültü varsayılmaz; double-talk/olası yakın uç konuşmada dondur/yavaşlat; seviye değişiminde sınırlı zaman sabiti; farklı bölme boyutlarında kararlı zaman tabanlı güncelleme; boşluk/dolgu/bilinmeyen tabanda geçersiz öğrenme yok.

### 5.4 Profiller ve bastırma

| Gürültü (sentetik fikstür) | İşlem | Sınır |
| --- | --- | --- |
| Sabit motor harmoniği | Bant sınırlı yanıt, sınırlı kazanç | Gerçek araç iddiası yok; toptan çentik yok |
| Fan/yol renkli gürültüsü | Seçili spektral bastırma | Beklenen örnek sayısı |
| Rüzgâr benzeri düşük frekans patlaması ve kırpılma | Bozulma/kırpılma işaretlenir | Doymuş örneklerin kurtarıldığı iddia edilmez |
| Konuşma benzeri başlangıçlı atölye geçişi | — | Toptan bastırma veya otomatik profil değişimi yok |
| Gürültü tabanı / atak-salınım sınırı | Onaylı aralıkta sonlu kazançlar | Kontrollü kayma |

Profil (sessiz/park/seyir/atölye/rüzgâr/telefon) güvenilir kaynaktan **istenir**; gerçek ortamdan çıkarılmış gibi gösterilmez. Geçersiz kazanç tabanı/gecikme sınırı/eşik/negatif bütçe etkinleşmeden reddedilir. Akış sırasında profil revizyonu sabit kalır.

### 5.5 Temiz konuşma ve uyum

Temiz sentetik ünlü benzeri ve geniş bantlı konuşma vekillerinde kazanç/gecikme korunumu (dondurulmuş sınırlar); kısa yumuşak başlangıç + gürültüde başlangıç/kuyruk muhasebesi, sessiz silme yok; akış ortasında bypass geçişi hizalı veya açık süreksizlik; uzun gürültüden sonra sessiz girişte sınırsız kazanç yok. Mevcut HPF yanıtı ve durumu, AGC azami kazanç/kayma, limiter tavanı ve kırpılma sayaçları, gate anlamı korunur; ikinci gate yok.

### 5.6 RNNoise ve metrikler

- RNNoise isteğe bağlı **yetenek noktası**: bağlama/lisans/ABI bilinmiyorsa `HOLD/UNKNOWN`, kurulum veya varsayılan geçişi yok. Sahte RNNoise ile hız/çerçeve/ölçek eşlemesi test edilir (sahte durum gerçek yerelden ayrı). Parçalı giriş/EOS'ta durum ve çerçeve kalanı; iki akış yalıtılmış; spektral bastırıcıyla birlikte seçilirse ret (yalnız açık onaylı ablasyon). Yerel karşılaştırma çalıştırılmadıysa **üstünlük iddiası yok** (`NOT_RUN`).
- SNR: kehanet (oracle) fikstürde beyan edilen aralık/hız/güç kuralıyla; payda bilinmiyor/sıfırsa `null` veya onaylı sansürlü sınır; farklı musluklar/kazançlar arası "iyileşme" iddiası reddedilir. ERLE yalnız uygun uzak-uç-yalnız aralıkta; double-talk'ta `UNKNOWN`. Kestirilen SNR ile F2 güveni ayrı puan türleri; olasılığa dönüşüm yok. `AcousticEvidence` kesin yarı açık aralık ve tazelikle.

### 5.7 Defter, DTMF ve kaynaklar

8/16/48 kHz değişken girişte F0-A rasyonel örnek defteri ve 16k çıkış; gerçek EOS'ta son kuyruk bir kez, blok başı dolgu yok; F1'in 512/32 ms penceresi değişmez. Ham DTMF algılayıcısı iyileştirilmemiş veriyi alır; kontrol baytlarına DSP uygulanmaz. İki oturumda ağırlık/PSD/saat/yeniden örnekleyici paylaşılmaz; küresel sınır/işçi kuyruğu dolunca sınırlı ret, kontrol hattı açık; işçi sürerken kapanışta yayın çitlenir, sahip tamamlanmaya/karantinaya kadar tutulur; eski generation iptalinde giriş sürer.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F0-B.01 | Ön kontrol | Yetki, çekirdek/W2 kabulü, F0-A/F6-B soyu ve kapsam | `PREFLIGHT`; AD01–AD04 |
| F0-B.02 | Envanter | Giriş DSP'si, hızlar, filtreler, tarayıcı ayarları, AEC/DTMF, referanslar, eski rotalar; M00 kimlikleri | `INVENTORY`; AD05–AD08 |
| F0-B.03 | Sahiplik | Tek giriş sahibi, geçiş bayrağı/kapalı kip, aşama sırası, sahiplik matrisi | `OWNERSHIP`; AD09–AD12 |
| F0-B.04 | Sözleşmeler | M01 çerçeveler, örnek aralıkları, M02 kapsamları, F0-A defteri; iç kanıt türleri | `CONTRACT_MAPPING`; AD13–AD16 |
| F0-B.05 | Profil ve yetenekler | M03 sabit profil/yetenekler, aday yapılandırmalar, sonlu sınırlar; varsayılan ve tarayıcı istenen/etkin | `PROFILE_SPEC`; AD17–AD20 |
| F0-B.06 | Referans okuyucu | F6-B referansı; güvenilir eşleme, kiralar, biçim/dönem ve teslim belirsizliği; ham dalga geri düşmesi yok | `REFERENCE_MAPPING`; AD21–AD28 |
| F0-B.07 | Hız ve saat köprüsü | Referans hız köprüsü, doğrulanmış saat eşlemesi, kesin örnek kökenleri ve grup gecikmesi | AD29–AD32 |
| F0-B.08 | Gecikme kestirici | Sınırlı kestirici; enerji/örtüşme/marj geçitleri; geçmiş, kayma/dondurma/yeniden edinme; parametreler önceden kayıtlı | `ALIGNMENT_SPEC`; AD33–AD38 |
| F0-B.09 | AEC | Mevcut AEC veya incelenmiş CPU prototipi; sonlu sınırlı filtre; ayrı güncelleme/çıkış kontrolü; yakın uç korunur | `AEC_SPEC`; AD39–AD44 |
| F0-B.10 | Double-talk | Gözlemler ve nedensel uyarlama geçidi; anlamsal veya kesme kararı yok; bayat ipucu reddi | `DOUBLE_TALK_SPEC`; AD45–AD50 |
| F0-B.11 | Gürültü kestirici | Sınırlı PSD, konuşma geçitli güncelleme, başlangıç, bant/zaman sabitleri, profil revizyonu | `NOISE_ESTIMATOR_SPEC`; AD51–AD56 |
| F0-B.12 | Profiller ve bastırıcı | Otomotiv gürültü profilleri ve mevcut spektral bastırıcı; sınırlı kazanç tabanı, atak/salınım | `DENOISING_MATRIX`; AD57–AD62 |
| F0-B.13 | Temiz konuşma koruması | Güvenli bypass geçişleri, başlangıç/kuyruk ve kısa düşük enerjili konuşma; örnek silme yok | `CLEAN_SPEECH_SPEC`; AD63–AD66 |
| F0-B.14 | Mevcut aşamalar | HPF/AGC/limiter/gate açık musluk/hız ve kazanç sınırlarıyla; sonlu çıktı; çift aşama yok | AD67–AD70 |
| F0-B.15 | RNNoise yeteneği | Bağlama/ABI/lisans/hız/çerçeve/ölçek envanteri; yetenek noktası; bağımsız durum/hız adaptörü | `RNNOISE_CAPABILITY`; AD71–AD76 |
| F0-B.16 | Kalite metrikleri | SNR/ERLE ve kalite üst veri yöntemleri, geçerli pencereler, null nedenleri; kestirim/kehanet ayrımı | `QUALITY_METRIC_SPEC`; AD77–AD82 |
| F0-B.17 | Defter ve DTMF | F0-A örnek defteri ve ham DTMF/kontrol hattı; karışık çerçeveler; kesin EOS/iptal; F1 512/32 ms bağımsız | `SAMPLE_ACCOUNTING`, `DTMF_MAPPING`; AD83–AD86 |
| F0-B.18 | Kaynaklar | M02 sınırlı CPU işçileri, tampon sahipliği, iptal/sıfırlama, referans temizliği, iki oturum yalıtımı, aşırı yük | `RESOURCE_LEDGER`; AD87–AD92 |
| F0-B.19 | Gizlilik | M04 güvenli telemetri ve M07 gizlilik; ham PCM, özel referans, müşteri verisi, kalıcı kayıt yok | AD93–AD94 |
| F0-B.20 | Entegrasyon | Gerçek F0-A/F6-B + kabul edilmiş F1-A/B; gelecek F1-C/F2-C test tüketicisi; aşağı akış uygulanmaz | AD95–AD96 |
| F0-B.21 | Fikstür ve benchmark | Belirlenimci fikstürler/test matrisi ve benchmark protokolü; korpus, seed, metrik tanımları, toleranslar dondurulur | `FIXTURE_MANIFEST`, `BENCHMARK_PROTOCOL.md` |
| F0-B.22 | Test yürütme | Yetkili yapısal test ailesi ve etkilenen regresyonlar | `TEST_RESULTS`; AD97 |
| F0-B.23 | Bütünlük ve geri dönüş | Bütünlük, geri dönüş, kaynak geri alımı, benchmark ertelemesi; isteğe bağlı etkinleştirme engelleri | AD98–AD99 |
| F0-B.24 | Kabul ve devir | F0-B-G00…G19 bağımsız inceleme; F1-C/F2-C/F6 devri ve açık hazırlık; dur | AD100; `ACCEPTANCE_MATRIX` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| AD01 | Yürütme yetkisi yok | Kaynak değişikliği yok; NOT_RUN/HOLD, açık engel |
| AD02 | Çekirdek kapı geçerli ama W2 yalnız hazır, kabul değil | HOLD; yürütme yok |
| AD03 | F0-A veya F6-B kanıtı bayat/uyumsuz | HOLD; gerçek soy uzlaştırılır; sahte PASS yok |
| AD04 | Gerçek kabul edilmiş önkoşullar ve incelenmiş kapsam fikstürü | Yalnız ön kontrole uygun; paket kabulü değil |
| AD05 | Web ve telefon girişi ve kaynak hızlarının izlenmesi | Gerçek aşama ve kontrol sahipliği kaydedilir; çıkarılmış yol yok |
| AD06 | Eski HPF/FFT/AGC/gate ve ön ayarlar | Etkin varsayılanlar ve gerçek çağrı özellik kimliklerine eşlenir |
| AD07 | Tarayıcı AEC istenen ile etkin yok | Ayrı durum UNKNOWN; yerel veya telefon iddiası yok |
| AD08 | Eski DTMF ve deneysel yollar envanteri | Tüm belirlenen etkiler ve rotalar hesaplanır |
| AD09 | Eski girişle katı bayrak KAPALI | Mevcut davranış değişmez; yeni referans okuması yok |
| AD10 | Kabul edilmiş fikstürde isteğe bağlı katı profil | Tam olarak bir seçili DSP zinciri ve bir çıkış sahibi |
| AD11 | Yinelenen tam bastırma veya yinelenen AEC denemesi | Yapılandırma reddedilir; gizli ardışık zincir yok |
| AD12 | DTMF'li sınırlı gölge fikstürü | Fazladan yayımlanan ses, DTMF veya kontrol kararı yok |
| AD13 | Bozuk uzunluk, kanal, kodlama veya hız | F0-A doğrulamasıyla ret; güvensiz tahsis yok |
| AD14 | Float yükte NaN/Inf veya geçersiz geçerli sayı | Ret; durum zehirlenmesi yok |
| AD15 | Yinelenen/sırasız/bayat giriş çerçevesi | F0-A boşluk/ret politikası; uydurma örnek yok |
| AD16 | Terminal dolgu ve geçerli sayı | Yalnız gerçek mikrofon örnekleri gürültü/kanıtı günceller; kesin defter |
| AD17 | Güvenilir sessiz/park/seyir/atölye/rüzgâr/telefon ön ayar fikstürleri | Doğru sabit istenen/etkin eşleme; çıkarılmış gerçek değer yok |
| AD18 | Geçersiz kazanç tabanı, gecikme sınırı, eşik veya negatif bütçe | Etkinleşmeden önce yapılandırma reddedilir |
| AD19 | Aktif akış sırasında profil revizyonu güncellenir | Onaylı sınıra kadar sabit profil değişmez |
| AD20 | Doğrulanmış tarayıcı AEC'si veya desteklenmeyen yerel yetenek | Çift AEC önlenir; bilinmiyor veya erişilemez açık |
| AD21 | Geçerli kapsamlı F6-B DSP sonrası talep edilmiş PCM | Doğru kaynak biçimi, generation, aralık ve SERVER kökeni |
| AD22 | Yalnız kuyrukta veya talepten önce silinmiş referans | Uydurma referans baytı veya sessizlik yok |
| AD23 | Kısmi/bilinmeyen aktarım teslimi | Belirsizlik taşınır; uyarlama engellenir veya sınırlı güvenli politika |
| AD24 | Yanlış oturum veya yetkisiz giriş-çıkış eşlemesi | Okuma reddedilir; başka oturum referansı yok |
| AD25 | Çıkış dönemi değişimi ve eski geri çağrı | Eski eşleme geçersiz; bayat referans kullanılmaz |
| AD26 | Önceki talep edilmiş geçmişle yumuşak duraklatma / kesin kesme | Uygun sınırlı geçmiş yankı kuyruğu tutulur; giriş aktif |
| AD27 | Geçmiş tahliyesi ve eksik aralık | Açık boşluklar/kapsam; gizli sıfır ikamesi yok |
| AD28 | Yavaş okuyucu, tükenmiş referans bütçesi | Sınırlı erişilemez/süre dolumu; oynatma yazıcısı gecikmez |
| AD29 | 8k veya 16k referanstan gerçek 16k AEC işleme hızına | Durumlu hız köprüsü; doğru ofset/faz ve gecikme eşlemesi |
| AD30 | Eşit olmayan keyfi referans bölmeleri | Sürekli referansla önceden onaylı toleransta eşleşir |
| AD31 | Doğrulanmış ortak saatte yakalama ve talep | Doğru aralık hesabı; gözlem kapsamı değişmez |
| AD32 | Bağımsız eşlenmemiş saatler | Mutlak gecikme UNKNOWN; yalnız gerekçeli göreli yöntem |
| AD33 | Pozitif gecikmeli bilinen seed'li geniş bant yankı | Dondurulmuş toleransta doğru işaret ve gecikme |
| AD34 | Onaylı arama aralığı dışında gecikme | Uydurma sınır kestirimi yok; UNKNOWN/yeniden edinme |
| AD35 | Sabit veya sıfır enerjili referans | Payda hatası yok; geçerli hizalama yok |
| AD36 | Tekrarlı motor harmoniği / rakip korelasyon tepeleri | Marj geçidi belirsiz gecikmeyi reddeder |
| AD37 | Yetersiz geçmiş veya geçerli örtüşme | AEC öğrenmesi engellenir; açık kapsam nedeni |
| AD38 | Gecikme sıçraması ve saat süreksizliği | Sınırlı kayma/yeniden edinme; bayat kestirimler dolar |
| AD39 | Bilinen nedensel FIR yankısı, uygun yalnız-uzak-uç referans | Sınırlı uyarlanır yakınsama ve sonlu artık; yalnız fikstür ERLE'si |
| AD40 | Öğrenirken referans kaybı | Politikaya göre dondur/sıfırla/bypass; keyfi sıfır referans güncellemesi yok |
| AD41 | Filtre katsayı taşması, sonlu olmayan ara değer | Geçersiz çıktı yok; sınırlı güvenli hata/sıfırlama yolu |
| AD42 | Düşük enerjili referans ve epsilon kenarı | Sonlu sınırlı ağırlıklar; sıfıra bölme yok |
| AD43 | Referans rotası değişen önceden eğitilmiş AEC | Uyumsuz filtre yeniden kullanılmaz; yeniden edinme |
| AD44 | Temiz yalnız-yakın-uç girişi | Koşulsuz susturma veya çift AEC yok; onaylı temiz koruma |
| AD45 | Bilinen eşzamanlı yakın ve uzak uç fikstürü | DOUBLE_TALK_LIKELY kanıtı ve korumalı güncelleme; yakın uç korunur |
| AD46 | Güvenilir hizalamalı yalnız-uzak-uç fikstürü | Yapılandırılmış politikada uygun güncelleme; anlamsal hüküm değil |
| AD47 | Yalnız yakın uç ve eksik referans | Muhafazakâr belirsiz kanıt; konuşma yine teslim edilir |
| AD48 | Bayat/yabancı F1 ipucu | İpucu yok sayılır; kontrol etkisi yok |
| AD49 | Aynı pencerenin F1 gözlemi henüz yok | Döngüsel bekleme yok; yalnız nedensel önceki ipucu |
| AD50 | Etkin oynatmada yüksek aday akustik skor | F0 yalnız kanıt yayar; duraklatma, devam veya generation commit'i yok |
| AD51 | Seed'li durağan yalnız-gürültü aralığı | Gürültü PSD'si uygun geçitte güncellenir; sınırlı durum |
| AD52 | Konuşma sıfırıncı örnekte başlar | İlk aralığın gürültü olduğu varsayılmaz; muhafazakâr başlangıç |
| AD53 | Double-talk veya olası yakın uç konuşma | Gürültü kestirimi dondurulur/yavaşlar; konuşma gürültü modeline emilmez |
| AD54 | Gürültü seviyesi bilinen zamanda değişir | Sınırlı zaman sabiti yanıtı; sınırsız geçmiş yok |
| AD55 | Farklı bölme boyutlarında aynı gürültü | Dondurulmuş toleransta kararlı zaman tabanlı güncelleme |
| AD56 | Boşluk, dolgu veya bilinmeyen gürültü tabanı | Geçersiz öğrenme yok; açık sıfırlama/bilinmiyor |
| AD57 | Durağan motor harmoniği fikstürü | Beyan edilen bant sınırlı yanıt ve sınırlı kazanç; gerçek araç iddiası yok |
| AD58 | Fan/yol renkli gürültü fikstürü | Seçili spektral bastırma sınırlı; beklenen örnek sayısı |
| AD59 | Rüzgâr benzeri düşük frekans patlaması ve kırpılma | Bozulma/kırpılma işaretlenir; doymuş örnekleri kurtarma iddiası yok |
| AD60 | Konuşma benzeri başlangıçlı atölye geçişi | Toptan bastırma/otomatik profil değişimi yok |
| AD61 | Gürültü tabanı ve atak/salınım sınırı | Onaylı aralıkta sonlu kazançlar; kontrollü kayma |
| AD62 | Bastırıcı bypass ve örtüşmeli toplama EOS'u | Çift DSP yok; beyan edilen gecikme ve kesin kuyruk |
| AD63 | Temiz sentetik ünlü benzeri ve geniş bant konuşma vekilleri | Dondurulmuş fikstür sınırlarında eşleşen kazanç/gecikme korunumu |
| AD64 | Kısa yumuşak başlangıç/dürtü artı gürültü | Başlangıç/kuyruk muhasebesi; sessiz silme yok |
| AD65 | Akış ortasında bypass geçişi | Hizalı geçiş veya açık süreksizlik; gizli kırpma yok |
| AD66 | Uzun gürültülü aralıktan sonra sessiz giriş | Sınırsız kazanç veya bastırma kalıcılığı yok |
| AD67 | Mevcut HPF dürtü/geçirme bandı fikstürü | Onaylı hıza özgü filtre yanıtı ve durumu korunur |
| AD68 | AGC azami kazanç/kayma ve sessizlik | Sınırlı kazanç, sonlu çıktı, sınırsız gürültü yükseltme yok |
| AD69 | Limiter/kırpılma fikstürü | Gerçek onaylı tavan ve kırpılma sayaçları; uydurma limiter varsayılanı yok |
| AD70 | Eski gate açık/kapalı | Mevcut anlam; örnek sayısı korunur; yinelenen gate yok |
| AD71 | RNNoise bağlaması yok veya lisans/ABI bilinmiyor | İsteğe bağlı yerel hazırlık HOLD/UNKNOWN; kurulum veya varsayılan geçişi yok |
| AD72 | Sahte RNNoise yerel hız/çerçeve/ölçek sözleşmesi | Doğru adaptör eşlemesi; sahte durum doğrulanmış yerelden ayrı |
| AD73 | RNNoise köprüsünde parçalı giriş/EOS | Durum ve çerçeve kalanı izlenir; kesin gecikme ve geçerli örnek defteri |
| AD74 | İki RNNoise adaptör akışı / işçi sürerken kapanış | Yalıtılmış yerel durum ve kira; erken bırakma yok |
| AD75 | RNNoise ve spektral bastırıcı birlikte seçilir | Ret veya yalnız açık onaylı ablasyon |
| AD76 | Yerel karşılaştırma yürütülmedi | Yerel RNNoise performansı NOT_RUN; üstünlük iddiası yok |
| AD77 | Sonlu enerjili bilinen temiz/gürültü fikstürü | Kehanet SNR beyan edilen aralık/hız ve güç kuralını kullanır |
| AD78 | Bilinmeyen veya sıfır payda, pozitif kestirilmiş sinyal yok | Null veya onaylı sansürlü sınır; uydurma sıfır değil |
| AD79 | Karşılaştırılamaz musluk veya kazançlı ön/son SNR | İyileşme iddiası reddedilir; ayrı kapsamlar korunur |
| AD80 | Bilinen yalnız-uzak-uç ile double-talk fikstürü | ERLE yalnız uygun uzak uç aralığında geçerli; double-talk UNKNOWN |
| AD81 | Kestirilen SNR ve F2 güven izdüşümü | Ayrı puan türleri, köken; olasılık dönüşümü yok |
| AD82 | `AcousticEvidence` çıkış aralığı ve tazeliği | Kesin yarı açık aralık; bilinmeyen/bayat tüketicide reddedilir |
| AD83 | 8/16/48 kHz değişken ardışık geçerli giriş | F0-A rasyonel örnek defteri ve 16k çıkış; açıklanamayan kayıp yok |
| AD84 | Parçalı kısa giriş, tam çerçeve ve gerçek EOS | Son kuyruk bir kez; blok başı dolgu yok; F1 512 pencere değişmez |
| AD85 | Ham DTMF ton fikstürü ve uyarlanır çıkış | Mevcut ham algılayıcı iyileştirilmemiş veriyi alır; yinelenen algılama yok |
| AD86 | Gerçek aktarım DTMF kontrol olayı + ham algılama | Mevcut tekilleştirme/öncelik; kontrol baytlarına DSP yok |
| AD87 | Farklı gürültü ve yankılı eşzamanlı A/B oturumu | Paylaşılan değiştirilebilir ağırlık, PSD, saat veya yeniden örnekleyici durumu yok |
| AD88 | Küresel sınır aşıldı, işçi kuyruğu doygun | Sınırlı ret/geri basınç; kontrol hattı erişilebilir |
| AD89 | CPU/yerel işçi sürerken giriş kapanışı | Yayın çitlenir; gerçek sahip tamamlanmaya/karantinaya kadar tutulur |
| AD90 | Giriş geçerliyken eski generation iptali | Giriş sürer; yalnız sınırlı önceki yankı referansı uygun |
| AD91 | Referans geri çağrısı beklerken giriş dönemi sıfırlanır | Bayat çıktı veya durum değişikliği yok; bir kez bırakma |
| AD92 | Yinelenen kapanış, kısmi başlatma hatası | İdempotent temizlik; sızan görev veya negatif defter yok |
| AD93 | Özel yük ve bozuk değerli M04 olay izdüşümü | İzin listesine göre ret/maskeleme; sonlu/null sayısal üst veri |
| AD94 | Referans saklama süresi dolumu ve yetkisiz tüketici | Ham PCM kalıcılaştırılmaz/ifşa edilmez; sınırlı kira temizliği |
| AD95 | Gerçek F6-B talebi → F0-B referansı → F1-A giriş yolu | Gerçek kapsamlı zincir; örnek sayıları ve belirsizlik korunur |
| AD96 | F1-C/F2-C test tüketicisi yok veya isteğe bağlı ipucu eksik | Mevcut F1-A/B ve F2-A/B geri düşmesi; yeni bağımlılık veya anlam yok |
| AD97 | Etkilenen tüm M00/F0-A/F6-B/F1-A regresyon aileleri | Mevcut özellikler hesaplanır; gerçek kanıt; sessiz atlama yok |
| AD98 | Kaynak/yapılandırma farkı ve bağımlılık denetimi | Yetkisiz model, bağımlılık, arayüz, DB, aktarım değişikliği yok |
| AD99 | Geliştirilmiş bayrağın geri alınması ve aktif akış sınırı | Onaylı yol güvenle geri gelir; kanıt ve uçuştaki sahiplik korunur |
| AD100 | Kapı/kanıt kurcalaması, eksik yerel sonuç ve ertelenmiş benchmark'lar | Sahte kabul yok; gerçek yapısal durum ile isteğe bağlı ayrımı |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F0-B-G00 | Ön kontrol | Çekirdek + W2 gerçek kabul, F0-A/F6-B kabul, uyumlu soy ve yetki |
| F0-B-G01 | Sahiplik | Gerçek DSP envanteri, tek giriş otoritesi, incelenmiş geçiş/varsayılan KAPALI |
| F0-B-G02 | Sözleşmeler | M01 `AudioFrame`/M02 kapsamları ve F0-A örnek sözleşmesi; ham yol korunur |
| F0-B-G03 | Profil | M03 sabit profil/yetenek, gerçek aşama hızı/sırası ve sınırlı yapılandırma |
| F0-B-G04 | Referans | Yetkili F6-B referansı; kesin bayt/aralık, belirsizlik ve boşluklar; sahte uç yok |
| F0-B-G05 | Hizalama | Hız/saat eşlemesi, açık bilinmiyor, sınırlı hizalayıcı ve geçmiş kontrolleri; AD29–AD38 |
| F0-B-G06 | AEC | Sonlu sınırlı durumlu CPU AEC ve nedensel referans uygunluğu; AD39–AD44 |
| F0-B-G07 | Double-talk | Double-talk uyarlama koruması ve F1 karar ayrımı; AD45–AD50 |
| F0-B-G08 | Gürültü kestirici | Sınırlı uyarlanır kestirici, başlangıç ve dondur/güncelle politikası |
| F0-B-G09 | Bastırma | Otomotiv profilleri ve seçili spektral bastırma; yinelenen tam aşama yok |
| F0-B-G10 | Temiz konuşma | Temiz konuşma ve kazanç/gecikme/örnek korunumu; HPF/AGC/limiter uyumu |
| F0-B-G11 | Defter | Kesin 16k çıkış, yeniden örnekleme defteri, EOS/iptal ve sessiz kayıp yok |
| F0-B-G12 | DTMF | Ham/kontrol DTMF korunur; yinelenen olay veya F1 tampon sahipliği yok |
| F0-B-G13 | Metrikler | SNR/ERLE kestirim ile kehanet ayrımı, kapsam ve isteğe bağlı akustik kanıt |
| F0-B-G14 | Kaynaklar | M02 durum/kaynak yalıtımı, bayat çıktı yok, GPU bağımlılığı yok, temizlik; AD87–AD92 |
| F0-B-G15 | RNNoise | RNNoise alternatif yeteneği ve KAPALI/bypass anlamı; sahte ile gerçek yerel kanıt ayrımı |
| F0-B-G16 | Gizlilik ve entegrasyon | M04/M07 gizlilik, gerçek F6-B/F0/F1 bütünleşmesi ve isteğe bağlı aşağı akış noktası; AD93–AD96 |
| F0-B-G17 | Test kanıtı | AD01–AD100 gerçek yapısal sonuçlar, zorunlu paket ve fikstür kanıtı |
| F0-B-G18 | Regresyon | Etkilenen tüm regresyonlar, kaynak bütünlüğü, onaylı geri dönüş |
| F0-B-G19 | Devir | Bağımsız inceleme, kabul ve açık ertelenmiş hedeflerle aşağı akış devri |

## 9. Kanıt

`evidence/F0-B/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `PREFLIGHT.json`, `INVENTORY.json`, `OWNERSHIP.md`, `CONTRACT_MAPPING.csv`, `PROFILE_SPEC.md`, `REFERENCE_MAPPING.md`, `ALIGNMENT_SPEC.md`, `AEC_SPEC.md`, `DOUBLE_TALK_SPEC.md`, `NOISE_ESTIMATOR_SPEC.md`, `DENOISING_MATRIX.csv`, `CLEAN_SPEECH_SPEC.md`, `SAMPLE_ACCOUNTING.md`, `DTMF_MAPPING.md`, `QUALITY_METRIC_SPEC.md`, `RESOURCE_LEDGER.md`, `RNNOISE_CAPABILITY.md`, `FIXTURE_MANIFEST.json`, `BENCHMARK_PROTOCOL.md` (SI-SDR, STOI, SNR, ERLE, ASR WER etkisi — DSP açık/kapalı; G4/G5'te), `TEST_MATRIX.json`. Laboratuvar sonuçları `data/F0/lab-report-*.json`.

## 10. Geri dönüş

`f0.adaptive_dsp` kapalı: F0-A taban zinciri tek aktif. Geçiş aktif akış sınırında güvenli; uçuştaki sahiplik korunur. Kod `git revert`.

## 11. Devir

- **F1-C:** `AcousticEvidence` (SNR kestirimi, double-talk kanıtı, kırpılma) bağlamsal backchannel ve double-talk sınıflandırıcısına girdi; F0-B karar vermez.
- **F2-C:** kestirilen SNR ayrı puan türü olarak kayan pencere profiline girdi olabilir; olasılığa dönüştürülmez.
- **F6:** referans tüketim sözleşmesi; F6-B'nin talep edilmiş çerçeve anlamı değişmez.
- **G4/G5:** F0 DSP p95 ≤ 10 ms; DSP açık/kapalı ASR etkisi; gerçek araç kayıt protokolü (eski F0-T33) ve kabul değerlendirmesi (eski F0-T34).

## 12. Başlatma komutu

```
F0-B paketini uygula: docs/execution/packages/W4/F0-B-uyarlanir-dsp.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F0-A ve F6-B kabulünü doğrula; korpus, seed ve toleransları önceden dondur.
F0-A cephesi arkasında F6-B referanslı CPU AEC, double-talk kanıtı, uyarlanır gürültü kestirici, otomotiv profilleri ve
temiz konuşma korumasını f0.adaptive_dsp (varsayılan kapalı) altında kur; çift bastırma/AEC yok, RNNoise yalnız yetenek noktası.
AD01–AD100'ü çalıştır, F0-B-G00…G19'u değerlendir, paket/F0-B dalında PR aç ve dur.
```
