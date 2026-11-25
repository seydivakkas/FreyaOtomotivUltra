# F0-A — Ses girişi ve temel iyileştirme hattı

> Web ve telefon girişlerini tek bir F0 cephesinde toplar: biçim doğrulama, PCM/float dönüşümü, oturum/akış durumu, ham DTMF kolu, mevcut HPF/FFT/AGC/gate'in **ayarları değiştirilmeden** adaptörle sarılması, durumlu yeniden örnekleme ve örnek muhasebesi. Çıktı: F1'e giden 16 kHz mono `AudioFrame`. Yeni DSP algoritması eklenmez (o F0-B'nin işi).

| Alan | Değer |
| --- | --- |
| Kimlik | F0-A |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, M01, M02, M08 |
| Sonraki | F1-A, W2_GATE, F0-B |
| Bayrak | `f0_pipeline_v2` (varsayılan kapalı) |
| Ortam | CPU |
| Eski görevler | F0-T02, F0-T03, F0-T05, F0-T06, F0-T07, F0-T08, F0-T21, F0-T22, F0-T23, F0-T24 |
| Kaynak | Bundle `W2/Freya_2_0_F0_A_Agent_Implementation_Package.md`; [F0 spec](../../../stages/F0-audio-acquisition/spec.md), [F0 tasks](../../../stages/F0-audio-acquisition/tasks.md) |
| Durum | NOT_RUN |

## 1. Amaç

Bugün ses `session.py` içinde 100 ms'lik bloklarla toplanıyor, `car_denoiser.py` sabit ayarlarla çalışıyor, yeniden örnekleme blok blok ve durumsuz yapılıyor; DTMF algılama DSP'den sonra gelirse bozulabiliyor. F0-A bu yolu **davranışı koruyarak** tek bir cepheye taşır ve sonraki iyileştirmeler (F0-B) için ölçülebilir, test edilebilir bir zemin kurar.

## 2. Başlamadan önce

- [ ] CORE_GATE PASS (`f_packages_ready: true`) ve F0-A başlatma onayı.
- [ ] Gerçek web/telefon/eski giriş rotaları, kaynak biçimleri, bayraklar, tampon boyutları, filtre sırası, DTMF ve kapanış yolları izlenmiş; M00 özellik kimlikleri eşlenmiş.
- [ ] `car_denoiser.py`'nin mevcut ayarları (HPF 120 Hz Butterworth, FFT pencere/örtüşme, AGC/gate) kaydedilmiş; bu pakette **yeniden ayarlanmaz**.

## 3. Kapsam

**Yapılacak:** Tek F0 cephesi (eski yol varsayılan, katı yol bayrakla); M01 sözleşme eşlemesi; biçim doğrulayıcı; PCM/float dönüşümü; oturum/akış durumu; ham DTMF köprüsü; eski HPF/FFT/AGC-gate adaptörleri; durumlu yeniden örnekleyici (8/16/48 kHz); örnek muhasebesi; sınırlı çıkış dağıtıcısı; yaşam döngüsü; M03/M04 bağlantısı; F1 noktası.

**Yapılmayacak:** Uyarlanır HPF, gürültü kestirici, profiller, Wiener, AEC, RNNoise, limiter (F0-B); VAD mantığı (F1-A); genel protokol değişikliği; aynı sese ikinci kez DSP uygulamak.

## 4. Dosyalar

```
backend/audio_frontend/
  facade.py  validation.py  conversion.py  stream_state.py  dtmf_tap.py
  legacy_hpf.py  legacy_fft.py  legacy_agc_gate.py  resampler.py
  sample_ledger.py  dispatcher.py  lifecycle.py  telemetry.py
tests/audio_frontend/
evidence/F0-A/<run_id>/
```

`session.py`, `audio.py`, `audiosocket_server.py` yalnızca cephe bağlantısı için dar noktalarda değişir. `car_denoiser.py` silinmez; adaptörler onu çağırır.

## 5. Tasarım ve sözleşmeler

### 5.1 Hat sırası

```
giriş (web PCM16 16k | AudioSocket PCM16 8k | eski) ─► doğrulama ─► dönüşüm (float32)
   ├─► ham DTMF kolu (özgün örnekler, özgün hız) ─► mevcut DTMF algılayıcı
   └─► HPF ─► FFT gürültü bastırma ─► AGC/gate ─► durumlu yeniden örnekleme (→16 kHz)
         ─► örnek defteri ─► sınırlı dağıtıcı ─► F1 (M01 AudioFrame, 16 kHz mono)
```

- Her DSP işlemi **tek yerde ve bir kez** uygulanır (CLAUDE.md kural 8). Giriş zaten işlenmişse aşama atlanır; çift DSP/çift yeniden örnekleme yok (AI37).
- DTMF ham kolu DSP'den **önce** ayrılır; DSP kapalı veya gate sesi sıfırlasa bile DTMF yolu aynen çalışır; tek olay yolu (AI26–AI29).
- Bayrak kapalıyken eski yol bayt bayt aynı çıktıyı üretir.

### 5.2 Biçim ve dönüşüm

| Profil | Örnek/20 ms | Bayt/20 ms |
| --- | --- | --- |
| 8 kHz mono PCM16 | 160 | 320 |
| 16 kHz mono PCM16 | 320 | 640 |
| 48 kHz mono PCM16 | 960 | 1920 |
| 16/48 kHz Float32 | 320 / 960 | 1280 / 3840 |

- Doğrulama bellek ayırmadan önce yapılır: hız/kodlama/kanal, yük uzunluğu, sayı sınırları, sonlu değerler; EOS ve kontrol olayları veriden ayrı.
- PCM16 → float: −32768 → −1.0; 32767 → 32767/32768; 0 → 0. Sonlu ama aralık dışı float: profile göre ret veya doyum; işaret taşması yok; yuvarlama belgeli.
- Desteklenmeyen hız/kanal tahmin edilmez: ret veya açıkça onaylı dönüşüm (ör. belgeli stereo→mono).
- Sahiplik: gönderimden sonra çağıranın tamponu değişse bile F0'ın kopyası etkilenmez.

### 5.3 Durumlu yeniden örnekleme

- Akış başına faz ve geçmiş tutulur; blok boyutundan bağımsız sonuç (1 örneklik parçalar dahil) sürekli referansla onaylı tolerans içinde eşleşir.
- Oranlar: 8→16 (×2), 48→16 (×1/3), 16→16 (gereksiz filtre yok).
- Gecikme ve EOS boşaltma politikası belgelidir; ikinci EOS çift boşaltma yapmaz; kuyruk kaybı yok.
- Uzun rasyonel girişte blok başı yuvarlama kayması birikmez.
- Geçirme bandı (1 kHz) ve durdurma bandı (48 kHz girişte 12 kHz) ölçütleri **önceden** yazılır; sonuç çalıştırılmadan "ölçüldü" denmez.

### 5.4 Durum, defter ve dağıtım

- Durum oturum + akış + yön + biçim dönemi kapsamlıdır (M02). İki oturum veya aynı oturumda iki akış filtre/gate/yeniden örnekleyici durumu paylaşmaz.
- Yeni biçim dönemi: eski durum belgeli biçimde boşaltılır/atılır; yeniden bağlanmadan sonra gelen eski dönem çerçevesi reddedilir.
- Örnek defteri: yerel giriş imleci ile 16 kHz çıkış imleci ayrı; boşluk/yineleme/dönem politikası; rasyonel süre; EOS/atılan kanıtı. Normal kapsamda sessiz kayıp yok.
- Dağıtıcı M02 kabul çitini kullanır; kuyruk dolunca tipli aşırı yük; DTMF/kontrol olayları medya kuyruğu doluyken aç kalmaz.
- Yapılandırma revizyonu (M03) akış başında sabitlenir; akış ortasında değişmez.

### 5.5 Gözlem

M04 güvenli alanları: RMS, tepe, kırpılma sayısı, aşama süreleri (`f0.processing_ms`, gerçek blok boyutuyla), düşürme/atma sayaçları. Ham ses, DTMF rakamları veya müşteri verisi günlüğe, kanıta veya `repr`'e girmez. Sessizlikte dBFS "yok" (−∞ sayı olarak yazılmaz).

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F0-A.01 | Çekirdek kapı ön kontrolü | CORE_GATE CG00–CG11, güncel soy, başlatma onayı | Ön kontrol kaydı veya düzenlemesiz HOLD |
| F0-A.02 | Giriş ve DSP envanteri | Web/telefon/eski rotalar, kaynak biçimleri, bayraklar, tampon boyutları, filtre sırası, DTMF ve kapanış yolları; M00 kimlikleri | `F0_INVENTORY.json` |
| F0-A.03 | Sahiplik ve değişiklik tasarımı | Tek cephe, eski varsayılan ve katı yol; dosya/sembol izin listesi; özellik koruma matrisi; DSP sırası ve çift işlem yasağı | `F0_DECISIONS.md` |
| F0-A.04 | Sözleşme eşlemesi | M01 `AudioFrame`/`StreamRef`; tek 16 kHz mono kodlama; kaynak/saat eşlemesi; açık desteklenmiyor sonuçları | AI05–AI08 |
| F0-A.05 | Biçim doğrulayıcı | Hız/kodlama/kanal, yük uzunluğu, sınırlar, sonlu veri, EOS/kontrol ayrımı; doğrulamadan önce ayırma yok | AI09–AI14 |
| F0-A.06 | PCM ve float dönüşümü | Doğru işaretli ölçekleme, güvenli niceleme, kırpılma sayımı, yalnız onaylı downmix/bypass; sahiplik | AI15–AI18 |
| F0-A.07 | Oturum ve akış durumu | M02 kapsamlı durum, sıra/ofset, dönem ve profil sabitleme; paylaşılan değiştirilebilir durum yok | AI19–AI25 |
| F0-A.08 | Ham DTMF köprüsü | DSP öncesi ham kol, doğru yerel hız, mevcut algılayıcı/olay anlamı, yinelenen yan etki yok, gizlilik | AI26–AI29 |
| F0-A.09 | Eski HPF adaptörü | Gerçek filtre ve hız/durum; süreklilik, yapılandırma eşdeğerliği; yeniden ayar yok | AI31–AI32 |
| F0-A.10 | Eski FFT adaptörü | Pencere/örtüşme/kalibrasyon ve sınırlı durum korunur; yeni algoritma yok | AI33–AI34 |
| F0-A.11 | Eski AGC/gate adaptörü | Mevcut kazanç/gate ve bypass anlamı; zaman sıkıştırma veya sessiz düşürme yok | AI35–AI38 |
| F0-A.12 | Durumlu yeniden örnekleyici | Akışlı faz/geçmiş, kenar yumuşatma, 8/16/48k, kesin gecikme/boşaltma; onaylı ek biçimler korunur | AI39–AI48 |
| F0-A.13 | Örnek muhasebesi | Ayrı yerel/çıkış imleçleri, boşluk/yineleme/dönem politikası, rasyonel süre, EOS/atma kanıtı | AI49–AI50 |
| F0-A.14 | Sınırlı çıkış dağıtıcısı | M02 kabulü, kapasite/sahiplik ve bayat çitleri; sahte F1 tüketicisi; VAD mantığı yok | AI51–AI52 |
| F0-A.15 | Yaşam döngüsü ve temizlik | İdempotent sıfırlama/kapanış, işçi tamamlanması/karantina, bağlantı kopması ve bayat geri çağrı | AI53–AI55 |
| F0-A.16 | Yapılandırma ve gözlem | M03 sabitlenmiş profil; M04 güvenli RMS/tepe/kırpılma/zamanlama; ham ses/rakam saklanmaz | AI56–AI59 |
| F0-A.17 | Eski kod bütünleşmesi ve F1 noktası | Onaylı minimum web/telefon cephe bağlantısı; genel protokol ve varsayılanlar korunur; tek aktif rota | AI60–AI61 |
| F0-A.18 | Belirlenimci doğrulama | AI01–AI64 (M08 ile); gerçek F0 kodu, yalnızca dış/tüketici sınırı sahte | Tüm testler çalıştırılmış |
| F0-A.19 | Regresyon ve bütünlük | Etkilenen mevcut ve temel regresyon paketleri; özellik matrisi; kaynak kapsamı | AI62–AI63 |
| F0-A.20 | Kabul ve devir | F0-A-G00…G15; geri dönüş; F1-A ve F0-B arayüz notları; dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| AI01 | Çekirdek kapı yok/NOT_RUN | Kaynak uygulaması yok, HOLD; eksik kanıt açık |
| AI02 | Çekirdek kapı başarısız veya soy/hash uyuşmazlığı | Yürütme engellenir; başarısız/bayat önkoşul raporlanır |
| AI03 | Kabul edilmiş kanıt ve yetkili fikstür ön kontrolü | Seçili çalıştırma kimlikleri ve kapsam kaydedilir; servis başlatılmaz |
| AI04 | Güvenli modül içe aktarma | CUDA/model/sağlayıcı başlatma, DB yazma veya ağ yok |
| AI05 | Geçerli 8 kHz mono PCM16, 160 örnek | Tam 320 bayt; doğru kaynak biçimi/akış |
| AI06 | Geçerli 16 kHz mono PCM16, 320 örnek | Tam 640 bayt; doğru sayı; hız tahmini yok |
| AI07 | Geçerli 48 kHz mono PCM16, 960 örnek | Tam 1920 bayt; doğru sayı |
| AI08 | Geçerli Float32 16/48 kHz, sonlu değerler | Örnek başına 4 bayt; kabul edilen biçim/profil |
| AI09 | Tek uzunluklu PCM16 bayt dizisi | Dönüşümden önce tipli ret; çıktı yok |
| AI10 | Beyan edilen sayı ile kısa/uzun yük | Ret; yalnız güvenli üst veri |
| AI11 | Sıfır/negatif/bool/aşırı büyük sayı veya taşma | Güvensiz ayırmadan önce ret; EOS ayrı |
| AI12 | Desteklenmeyen hız/kodlama/bayt sırası | Ret veya açık onaylı dönüşüm; tahmin yok |
| AI13 | Desteklenmeyen kanal / onaylı stereo fikstürü | Ret veya kesin downmix politikası; kanal başı sayı korunur |
| AI14 | Float32 NaN/+Inf/−Inf | DSP/nicelemeden önce ret; geçersiz çıktı yok |
| AI15 | PCM en küçük/en büyük/sıfır dönüşümü | −32768 → −1; 32767 → 32767/32768; 0 → 0 |
| AI16 | Aralık dışı sonlu float ve gidiş-dönüş | Profile göre ret/doyum; taşma veya işaret sarması yok; yuvarlama belgeli |
| AI17 | Gönderimden sonra değişen giriş tamponu | Sahipli yük değişmez; asenkron değiştirilebilir takma ad yok |
| AI18 | Açık son dolgu / `valid_sample_count` | Dolgu işaretli, gerçek konuşma sayılmaz; geçersiz sayılar reddedilir |
| AI19 | Aynı yerel akış indeksli iki oturum | Filtre/gate/yeniden örnekleyici durumu veya yük paylaşılmaz |
| AI20 | Bir oturumda iki yön veya akış | Bağımsız durum ve imleçler; küresel sıfırlama yok |
| AI21 | Yinelenen sıra veya örtüşen örnek aralığı | Açık ret; yinelenen örnek çıktısı yok |
| AI22 | Sırasız çerçeve ve boşluk | Sahip politikası, açık süreksizlik; sessiz uydurma süreklilik yok |
| AI23 | Yeni biçim dönemiyle hız değişimi | Eski durum belgeli biçimde boşaltılır/atılır; yeni durum ve hız geçerli |
| AI24 | Yeniden bağlanmadan sonra geç eski dönem çerçevesi | Bayat reddedilir; yeni akış kirlenmez |
| AI25 | Aktif akış sırasında yeni yapılandırma revizyonu | Sabitlenmiş durum değişmez; yalnızca onaylı yeni sınır revizyonu kullanır |
| AI26 | HPF/FFT/gate öncesi geçerli DTMF fikstürü | Mevcut ham algılayıcı özgün örnekleri/hızı alır |
| AI27 | Birincil DSP kapalı veya gate sesi sıfırlar | Ham DTMF kolu korunur; tek olay yolu |
| AI28 | Aktarım sinyali ve bant içi DTMF örtüşmesi (varsa) | Mevcut tekilleştirme politikası; ikinci iş gönderimi yok |
| AI29 | Ham kol tüketicisi değiştirmeye çalışır veya hata verir | Ana yük sağlam; tipli hata; sınırlı kaynak politikası |
| AI30 | Bypass ve eski profille sessizlik | Doğru örnek zaman çizgisi, sonlu değerler, gizli ek kazanç yok |
| AI31 | HPF dürtüsü parçalı ile tam referans | Filtre geçmişi korunur; onaylı sayısal tolerans |
| AI32 | HPF alçak/yüksek frekans fikstürü | Gerçek hızda mevcut yanıt/katsayılar doğrulanır; yeniden ayar yok |
| AI33 | Çerçevelere bölünmüş FFT penceresi | Eski örtüşme/durum korunur; ek başlangıç sıfırlaması yok |
| AI34 | Mevcut gürültü bastırıcıdan seed'li gürültü fikstürü | Sonlu çıktı ve tabanla tanımlı yanıt; gerçek ASR iddiası yok |
| AI35 | AGC düşük/yüksek genlik fikstürü | Mevcut kazanç ayarı ve durumu korunur; taşma yok |
| AI36 | Gürültü gate sınırı ve bypass | Mevcut anlam; sıfırlama örnek silme değildir |
| AI37 | Kapalı aşama / önceden işlenmiş giriş | Tam olarak bir rota; çift DSP/yeniden örnekleme yok; bayraklara uyulur |
| AI38 | Mevcut aşama kontrollü istisna fırlatır | Açık güvenli sonuç; uydurma ses veya onaysız geri düşme yok |
| AI39 | 8→16 kHz ardışık giriş | Oran 2, beyan edilen gecikme/boşaltma politikası, geçerli çıkış hızı/sayısı |
| AI40 | 48→16 kHz ardışık giriş | Oran 1/3; boşaltmadan sonra kesin süre muhasebesi |
| AI41 | 16→16 kHz özdeş hız yolu | Gereksiz filtre yok; yalnız gerekli biçim dönüşümü |
| AI42 | Düzensiz küçük ve büyük parçalar (1 örnek dahil) | Durumlu çıktı sürekli referansla onaylı toleransta eşleşir |
| AI43 | Uzun rasyonel yeniden örnekleme fikstürü | Blok başı yuvarlama kayması birikmez; açık son sayı/tolerans |
| AI44 | 1 kHz geçirme bandı, DSP bypass | Kazanç beyan edilen toleransta; gecikme hariç |
| AI45 | 48 kHz girişte 12 kHz durdurma bandı | Kenar yumuşatma önceden beyan edilen ölçütü karşılar; çalıştırılmadan ölçüm iddiası yok |
| AI46 | Ek eski desteklenen hız/kanal profili | Onaylı adaptörle korunur; yoksa açıkça desteklenmiyor |
| AI47 | EOS kuyruğu ve ikinci EOS | Geçerli kuyruk bir kez; çift boşaltma/dolgu/düşürme yok; defter uzlaşır |
| AI48 | Sıfır çıktılı ara yeniden örnekleyici çağrısı | Geçerli tamponlanmış sonuç; sahte boş veri çerçevesi yok |
| AI49 | Giriş/çıkış akış eşlemesi ve örnek ofseti | Çıkış ofsetleri 16 kHz alanında; bağımsız sıra; doğru süre |
| AI50 | Geçerli zaman damgası ile eksik yakalama zamanı | Doğru saat alanı; uydurma zaman damgası veya saatler arası çıkarma yok |
| AI51 | Uçuşta çerçeveyle dolu sınırlı kuyruk | Aşırı taahhüt veya sessiz düşürme yok; tipli aşırı yük ve doğru defter |
| AI52 | Medya kuyruğu doluyken DTMF/kontrol | Mevcut kontrol yolu çoğaltılmaz veya süresiz aç kalmaz |
| AI53 | İşçi çalışırken kapanış | Mantıksal çit bayat çıktıyı reddeder; kira gerçek bitişe/karantinaya kadar |
| AI54 | Yeni konuşma gelirken çıkış generation'ı iptali | Giriş akışı yetkili olarak sürer; yeni müşteri konuşması atılmaz |
| AI55 | Yinelenen geri çağrı, kısmi başlatma hatası, tekrar kapanış | Tam bir kez bırakma; negatif defter, sızıntı veya izlenmeyen durum yok |
| AI56 | Gözlemci istisnası / telemetri taşması | Kritik ses yolu durmaz; güvenli gözlenen kayıp durumu |
| AI57 | Bilinen analitik örneklerle RMS, tepe, kırpılma | Doğru sonlu metrikler; sessizlikte doğrusal sıfır/dBFS yok; geçerli payda |
| AI58 | Sahte saatle M04 zamanlama fikstürü | Beyan edilen sınırlar ve birimler, gerçek blok süresi; gerçek p95 çıkarımı yok |
| AI59 | İzdüşümde yük ve DTMF gizli işareti | Günlük/kanıt/`repr`'de ham ses/rakam/müşteri/gizli bilgi yok |
| AI60 | Sahte F1 tüketicisi değişken çıkış blokları alır | M01 16 kHz mono sözleşmesi, sıralı ofsetler; VAD/pencere mantığı yok |
| AI61 | Eski web/telefon yolu altın tekrarı | Genel yük, işleyiciler, varsayılanlar, kontrol anlamı değişmez; yalnız seçili yol |
| AI62 | Çoklu akış, karışık 8/16/48 kHz ve kopmalar | Belirlenimci yalıtım, sınırlı durum, uzlaşan örnek defteri |
| AI63 | Etkilenen mevcut test ve API/arayüz/yapılandırma regresyonu | Gerçek M00 özellik eşlemesi; yeni regresyon yok; izinsiz yol değişikliği yok |
| AI64 | Kanıt bütünlüğü, kapsam ve geri dönüş provası | Gerçek test durumları/hash başvuruları; F1-A devri yalnızca kabulde; canlı etkinleştirme yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F0-A-G00 | Ön kontrol | M00–M08 ve CORE_GATE CG00–CG11 PASS; kaynak soyu; açık F0-A onayı |
| F0-A-G01 | Tek cephe | Tek F0 cephesi, onaylı dosya/sembol kapsamı, güvenli içe aktarma, ikinci çalışma zamanı/DSP yok |
| F0-A-G02 | Taban eşlemesi | Gerçek taban giriş/DTMF/DSP eşlemesi ve M01 sözleşme bütünleşmesi |
| F0-A-G03 | Giriş profilleri | Geçerli 8/16/48 kHz profilleri; güvenli kodlama/boyut/kanal/sonluluk doğrulaması |
| F0-A-G04 | Dönüşüm | PCM/float dönüşümü, tampon sahipliği, açık geçerli örnek anlamı |
| F0-A-G05 | Durum yalıtımı | M02 akış/oturum durumu, sıra/dönem ve M03 görüntü yalıtımı |
| F0-A-G06 | DTMF | Ham DTMF yolu korunmuş, yinelenen olay gönderimi yok; kontrollü fikstür kanıtı |
| F0-A-G07 | Eski DSP | Eski HPF/FFT/AGC/gate ayarları ve sırası korunmuş; bypass/hata davranışı belgeli |
| F0-A-G08 | Yeniden örnekleme | Belgeli gecikme, kenar yumuşatma, parça/boşaltma testleriyle durumlu 16 kHz mono |
| F0-A-G09 | Muhasebe | Örnek muhasebesi ve boşluk/EOS politikası; beyan edilen normal kapsamda sessiz kayıp yok |
| F0-A-G10 | Kabul ve temizlik | Sınırlı kabul, temizlik ve bayat çitleme; tam bir kez kaynak bırakma |
| F0-A-G11 | Gözlem | M04 güvenli telemetri, zamanlama sınırı, gizlilik ve gözlemci yalıtımı |
| F0-A-G12 | F1 noktası ve uyum | Gerçek M01 çerçeveleriyle F1 noktası; onaylı eski tel/API/arayüz/yapılandırma uyumu |
| F0-A-G13 | Test kanıtı | AI01–AI64 gerçek eşlenmiş yürütme kanıtı; atlanan zorunlu veya uydurma sonuç yok |
| F0-A-G14 | Regresyon | Etkilenen M00 ve temel regresyon, izinli kaynak bütünlüğü, incelenebilir geri dönüş |
| F0-A-G15 | Devir | İncelenmiş F1-A/F0-B/F6-A devri; hazırlık açık; canlı etkinleştirme ayrı kalır |

## 9. Kanıt

`evidence/F0-A/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F0_INVENTORY.json`, `F0_DECISIONS.md`, `RESAMPLER_REPORT.json` (oranlar, gecikme, tolerans, geçirme/durdurma bandı sonuçları — yalnız çalıştırılmış değerler), `SAMPLE_LEDGER_REPORT.json`, `FEATURE_REGRESSION_MATRIX.csv`, `TEST_MATRIX.json`. Taban ölçüm betiği (eski F0-T02) sonuçları `data/F0/lab-report-baseline-*.json`.

## 10. Geri dönüş

`f0_pipeline_v2` kapatılır: eski yol aynen çalışır. Cephe bağlantısı ayrı commit'tir ve `git revert` ile geri alınır; `car_denoiser.py` değişmediği için ek işlem gerekmez.

## 11. Devir

- **F1-A:** 16 kHz mono M01 `AudioFrame`, sıralı ofsetler, açık süreksizlik işaretleri; değişken blok boyutu (her çerçeve 20 ms değil). VAD penceresi (512 örnek) F1'in işidir.
- **F0-B:** adaptörlerin arkasına uyarlanır HPF, gürültü kestirici, profiller, AEC, limiter eklenir; sıra ve "tek kez" kuralı korunur.
- **F6-A:** F0'ın 48 kHz giriş yolu ve yeniden örnekleyici bileşeni F6'da yeniden kullanılabilir (kopyalanmaz).

## 12. Başlatma komutu

```
F0-A paketini uygula: docs/execution/packages/W2/F0-A-ses-girisi.md.
Kuralları CLAUDE.md'den oku; CORE_GATE PASS ve başlatma onayını doğrula.
backend/audio_frontend/ altında tek F0 cephesini f0_pipeline_v2 bayrağı arkasında kur;
car_denoiser.py ayarlarını değiştirme, DTMF ham kolunu DSP'den önce ayır.
AI01–AI64'ü çalıştır, F0-A-G00…G15'i değerlendir, paket/F0-A dalında PR aç ve dur.
```
