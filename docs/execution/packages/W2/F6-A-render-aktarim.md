# F6-A — Durumlu render, çerçeveleme ve aktarım

> F5'in ham 48 kHz mono Float32 parçalarını doğrular; mevcut çıkış DSP'sini (HPF/EQ/limiter/fade) sırası ve ayarları **değiştirmeden ve bir kez** uygular; plan duraklamasını tek seferde yerleştirir; akış boyunca durumlu yeniden örnekleyiciyle web (16 kHz) ve telefon (8 kHz) hızlarına indirir; PCM16 LE'ye niceler; 20 ms çerçeveler kurar; monoton saatle tek bir zamanlayıcıyla gönderir; M02 çitiyle bayat gönderimi engeller ve dürüst kapsamlı `PlaybackEvent` yayar. Ayrıca W2_GATE koşucusunu kaydeder.

| Alan | Değer |
| --- | --- |
| Kimlik | F6-A |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, F5-A, M02 |
| Sonraki | W2_GATE, F1-B, F6-B |
| Bayrak | `f6_pipeline_v2` (varsayılan kapalı; `off / shadow / strict`) |
| Ortam | CPU (sahte saat, kaydeden aktarım) |
| Eski görevler | F6-T02, F6-T05, F6-T10, F6-T13, F6-T15, F6-T16, F6-T20 |
| Kaynak | Bundle `W2/Freya_2_0_F6_A_Agent_Implementation_Package.md` (W2_GATE bu dosyanın H bölümünde); [F6 spec](../../../stages/F6-rendering-transport/spec.md), [F6 tasks](../../../stages/F6-rendering-transport/tasks.md) |
| Durum | NOT_RUN |

## 1. Amaç

PoC'ta çıkış DSP'si parça başına durumsuz uygulanıyor (parça sınırlarında tıklama riski), yeniden örnekleme her parçada baştan başlıyor, gönderim `sleep` birikimiyle kayıyor ve "boşaltıldı" olayı duyulan kesme gibi yorumlanabiliyordu. F6-A, CLAUDE.md kural 8'in F6 kısmını uygular: **duraklama/fade/EQ F6'da, tek yerde, bir kez**. WSOLA, birleştirme, de-esser, loudness, konfor gürültüsü ve kodek laboratuvarı F6-C'dedir.

## 2. Başlamadan önce

- [ ] CORE_GATE, F5-A, M02 kabul edilmiş; güncel soy; onay. Yetkisiz yol veya çakışan çalışma ağacı sahibi varsa HOLD.
- [ ] Tüm gerçek render, DSP, web, AudioSocket yolları ve atlamalar envantere alınmış; mevcut DSP sırası ve aktarım varsayılanları değişiklikten **önce** karakterize edilmiş (eski F6-T02 A0).
- [ ] H01'deki ağ yazma zaman aşımı düzeltmesi (eski F6-T03) birleştirilmiş.

## 3. Kapsam

**Yapılacak:** Tek render/aktarım otoritesi; sözleşme eşlemesi; giriş doğrulaması; güvenilir kanal ve M03 profili; M02 akış durumu ve tek yazıcı; mevcut çıkış DSP adaptörleri; kontrol (duraklama/hız/fade) sahipliği; iki hızda durumlu yeniden örnekleme; PCM16 niceleme; 20 ms çerçeveleme ve EOS; örnek muhasebesi; AudioSocket ve web adaptörleri; monoton zamanlayıcı; sınırlı akış ve atomik gönderim; EOS/iptal/kapanış; `PlaybackEvent` ve M04; F5 bağlantısı; W2_GATE kaydı.

**Yapılmayacak:** Oynatma kuyruğu yeniden tasarımı, söz kesme köprüsü, tarayıcı makbuzları, AMI/ARI aktarım doğrulaması (F6-B); birleştirme/WSOLA/de-esser/loudness/konfor gürültüsü/kodek laboratuvarı (F6-C); chan_websocket (F6-D); arayüz değişikliği; W2_GATE'in çalıştırılması (ayrı onayla).

## 4. Dosyalar

```
backend/audio_rendering/
  contracts_map.py  admission.py  profile.py  stream_state.py  legacy_dsp.py
  controls.py  resampler.py  quantize.py  framer.py  sample_ledger.py
backend/media_transport/
  audiosocket_adapter.py  web_adapter.py  pacer.py  flow.py  lifecycle.py
  playback_events.py  telemetry.py  legacy_bridge.py
tests/audio_rendering/  tests/media_transport/
tests/integration/w2/          # WI01–WI24 (kayıt; çalıştırma W2_GATE'te)
evidence/F6-A/<run_id>/
```

Yeniden örnekleyici F0-A ile aynı uygulamayı yeniden kullanabilir; ancak **örnekler ayrıdır** (giriş ve çıkış yönleri durum paylaşmaz, AR21).

## 5. Tasarım ve sözleşmeler

### 5.1 Hat

```
AudioChunk (48k mono f32, ham) ─► doğrulama ─► profil (WEB 16k | AUDIOSOCKET 8k, akış başında sabit)
  ─► mevcut çıkış DSP'si (gerçek sıra, gerçek hız, bir kez) ─► duraklama (desteklenirse, bir kez)
  ─► durumlu yeniden örnekleme (48→16 veya 48→8) ─► PCM16 LE niceleme
  ─► 20 ms çerçeve (web 320 örnek/640 B, telefon 160 örnek/320 B) ─► RenderedFrame
  ─► sınırlı akış + M02 atomik gönderim ─► monoton zamanlayıcı ─► aktarım ─► PlaybackEvent (SERVER)
```

### 5.2 Kurallar

1. **Giriş:** yalnız ham 48 kHz mono Float32; yanlış hız/kodlama/kanal yeniden etiketlenmeden reddedilir; NaN/Inf, geçersiz uzunluk, bool sayı DSP'den önce reddedilir; boş veri EOS değildir. F5 yapısal hatası engeller; akustik `UNKNOWN` PASS'e yükseltilmez. Aynı kimlikli çakışan parça veya sıra boşluğu açık politikayla.
2. **Profil:** güvenilir kanal seçimi (WEB/AUDIOSOCKET) kesin hız/biçim/profili sabitler; sahte kanal üst verisi profil seçemez. Akış başladıktan sonra yapılandırma değişirse eski etkin profil sürer; yeni dönem açıktır.
3. **Durum:** akış/dönem/generation başına; iki akış birbirini etkilemez; aynı generation'da parça sınırlarında filtre geçmişi aşamanın politikasına göre korunur; iptal sonrası yeni generation'a eski kuyruk/filtre örnekleri sızmaz.
4. **Mevcut DSP:** HPF, EQ, limiter, fade etkinse gerçek taban yanıtı ve sırasıyla; yeni EQ yok, gizli kazanç değişikliği yok; fade yalnız kanıtlanmış sınırda, çerçeve başına değil. Kapalı DSP/konfor gürültüsü/deney bayrakları onaylı kapalı davranışını korur.
5. **Kontroller:** desteklenen ve daha önce uygulanmamış `post_pause` kabul edilen sınırda **tam bir kez** örnek muhasebesiyle; null duraklama veya yukarıda uygulanmış hız için ikinci dönüşüm yok; desteklenmeyen kontrol açıkça "desteklenmiyor/HOLD", uygulanmış gibi gösterilmez; negatif/sonlu olmayan/devasa süre tahsisten önce ret.
6. **Yeniden örnekleme:** iki hız; asal ve düzensiz parça bölmelerinde EOS sonrası sürekli referansla eşleşme; uzun akışta rasyonel faz ve sayaçlar, birikmiş yuvarlama hatası yok; başlangıç tamponlama ve kuyruk boşaltma açık ve bir kez; EOS öncesi iptalde eski kuyruk yayılmaz. Toleranslar ve kenar yumuşatma ölçütleri **önceden** sabitlenir (web için 12 kHz, telefon için 6 kHz girdi).
7. **Niceleme:** sıfır, işaretli sınırlar, bilinen kesirler için onaylı eşleme; aralık dışı değerler doyuma gider (tamsayı sarması yok) ve sayılır; LE bayt sırası; yarım adım eşitliği belgeli kurala göre; ham tepe, limiter ve niceleme doyumu ayrı sayılır.
8. **Çerçeveleme ve EOS:** tam çerçeveler sıralı, sınırlı kalan; kısa kalanla EOS'ta onaylı kısa/dolgu politikası ve kesin `valid_sample_count`; tam çerçeve sınırında EOS'ta ek boş/tamamen dolgu çerçeve yok; kasıtlı sessizlik geçerli içeriktir, dolgu ayrıdır; yinelenen/bayat EOS ikinci kuyruk üretmez.
9. **AudioSocket:** destekleniyorsa gerçek başlık `10 01 40` + 320 baytlık LE gövde; TCP paket sınırı değildir (parçalı/birleşik okuma); desteklenmeyen tür/uzunluk taşması gönderimden önce ret; UUID/sonlandırma/hata/DTMF kontrolü ayrı yol, ses zamanlamasına girmez; kısmi yazma/belirsiz gönderimde kör yeniden gönderim yok.
10. **Web:** mevcut zarf (640 B PCM), AudioSocket başlığı yok; mevcut el sıkışma/kontrol ve istemci tarafı tempo korunur; çift zamanlama yok; istemci yetenek uyuşmazlığında katı etkinleştirme HOLD.
11. **Zamanlama:** mutlak hedefler (sahte saatte birikimli uyku kayması yok); gönderim gecikmesinden sonra ek 20 ms eklenmez; geç uyanmada sınırlı yeniden çapalama veya açık hata, **yakalama patlaması yok**; boşluk sonrası açık yeniden çapalama, gizli konfor sessizliği yok; saat alanı uyuşmazlığında geçersiz çıkarma yok.
12. **Akış ve iptal:** sayı/bayt/süre/uçuşta sınırları; çekişten sonra gönderimden önce iptal → sıfır bayat gönderim; önce gönderim sonra iptal → "uçuşta olabilir", geri çağırma iddiası yok; sentezi bitmiş ama boşaltma yetkisi süren generation'ın geçerli son çerçeveleri akar, iptal kalanları engeller. Mevcut duraklat/devam yalnızca yetkili gönderilmemiş veriyi sürdürür (geliştirme F6-B'de). Kopma/yinelenen kapanış/yeniden bağlanma: sınırlı temizlik, yeni enkarnasyon. Tamamlanma bilinmiyorsa kira tutulur/karantina.
13. **Olaylar:** `QUEUED/STARTED/DRAINED/COMPLETED` sunucu fikstüründe `SERVER` kapsamlı; uydurma `CLIENT/PBX/ENDPOINT` makbuzu yok. `FLUSH_REQUESTED` ile kapsamlı `FLUSHED` ayrı; duyulan kesme iddiası yok.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F6-A.01 | Ön kontrol | Çekirdek kapı, F5-A/M02 kabulü, onay ve kaynak soyu | Ön kontrol raporu; HOLD'da yazma yok; AR01–AR04 |
| F6-A.02 | Envanter ve karakterizasyon | Render, DSP, web, AudioSocket ve tüm atlamalar; özellik kimlikleri | `AUDIO_OUTPUT_INVENTORY.json`, davranış karakterizasyonu; AR05–AR06 |
| F6-A.03 | Tek otorite ve kapsam | Yayılım profili sabitleme, değişiklik kapsamı | Kararlar, sahiplik ve geri dönüş haritası; AR07–AR08 |
| F6-A.04 | Sözleşme eşlemesi | M01/M02/F5/F4 sözleşmeleri, EOS, kapsam ve kimlik | `CONTRACT_MAPPING`; AR09–AR10 |
| F6-A.05 | Giriş doğrulama | Sınırlı değiştirilemez yük kabulü; bozuk/aşırı büyük/koruma hatalı giriş reddi | AR11–AR16 |
| F6-A.06 | Kanal ve profil | Güvenilir kanal ve onaylı M03 profili/revizyonları | Profil eşlemesi ve varsayılan korunumu; AR17–AR19 |
| F6-A.07 | Akış durumu ve tek yazıcı | M02 akış durumu; durum yalıtımı, yaşam döngüsü, tampon sahipliği | AR20–AR23 |
| F6-A.08 | Mevcut DSP adaptörleri | Çift uygulama olmadan; yerel hız/sıra ve karakterizasyon matrisi | AR24–AR28 |
| F6-A.09 | Kontrol sahipliği | Duraklama/hız/fade; açık desteklenmiyor durumu; bir kez muhasebesi | Kontrol uygulama matrisi; AR29–AR32 |
| F6-A.10 | Durumlu yeniden örnekleyici | Her iki hız; bölme ve kenar yumuşatma sonuçları sabit toleransla | AR33–AR40 |
| F6-A.11 | Niceleme | Sonlu normalize örneklerden PCM16 LE; kesin vektör fikstürleri; doyum sayımı | AR41–AR45 |
| F6-A.12 | 20 ms çerçeve ve EOS | Açık normal EOS terminal politikası; sınırlı kalan | Çerçeveleme şartnamesi; AR46–AR52 |
| F6-A.13 | Örnek muhasebesi ve çerçeve oluşturucu | M01 `RenderedFrame` doğrulayıcı, ofset/dolgu | AR53–AR55 |
| F6-A.14 | AudioSocket adaptörü | Mevcut serileştirme ve kontrol ayrımı; kesin 8k ikili tel fikstürleri | Protokol haritası; AR56–AR60 |
| F6-A.15 | Web adaptörü | Mevcut zarf ve gerçek tempo sahipliği; arayüz değişikliği yok | Bayt/şema uyumu; AR61–AR63 |
| F6-A.16 | Monoton zamanlayıcı | Geç kalma politikası, belirlenimci tempo | Tempo şartnamesi ve sahte saat koşuları; AR64–AR68 |
| F6-A.17 | Sınırlı akış ve atomik gönderim | M02 çiti; bayat kabul yok | Kuyruk/kira politikası; AR69–AR73 |
| F6-A.18 | EOS, iptal, kapanış ve duraklat/devam | Açık süreksizlikler ve temizlik | AR74–AR76 |
| F6-A.19 | `PlaybackEvent` ve M04 | Doğru kapsamlı olaylar, güvenli metrikler | Kapsam matrisi ve gizlilik testleri; AR77–AR79 |
| F6-A.20 | F5 bağlantısı ve eski rotalar | Gerçek katı F5 çıktısı → F6; tüm eski genel rotalar korunur | Sahte model/aktarımla gerçek katman orkestrasyonu; AR80–AR82 |
| F6-A.21 | Tam test yürütmesi | AR01–AR84 ve etkilenen M00/M01/M02/M04/F0/F5 testleri (M08 ile) | Gerçek komut/günlük/sonuç; atlama aklama yok |
| F6-A.22 | Regresyon ve geri dönüş | Atlama incelemesi, regresyon, kaynak bütünlüğü, kapsamlı geri dönüş provası | Regresyon matrisi, bütünlük hash'leri; AR83–AR84 |
| F6-A.23 | W2_GATE kaydı | Ayrı onaylı W2 koşucusu, WI01–WI24 ve WG00–WG11; yalnız fikstürlerle doğrulama | W2 planı ve test kaydı; gerçek W2 sonuçları NOT_RUN |
| F6-A.24 | Kabul ve devir | F6-A-G00…G19 bağımsız incelemeyle; F1-B/F6-B/F6-C ve W2 devri | Kabul raporu; W2 koşusu veya F1-B'den önce dur |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| AR01 | Gerçek önkoşul kabul soyu | Çekirdek, F5/M02 kanıtı ve kapsam doğrulanır; uydurma hazırlık yok |
| AR02 | Eksik/bayat çekirdek veya F5 kanıtı fikstürü | Kaynak değişikliği/gönderimden önce HOLD |
| AR03 | Ağ/GPU/üretim kaynakları yasakken içe aktarma | İçe aktarmada model, PBX, DB, iş parçacığı veya servis başlatma yok |
| AR04 | Yetkisiz yol veya çakışan çalışma ağacı sahibi | Üzerine yazma yok; HOLD ve güvenli rapor |
| AR05 | Tüm gerçek çıkış giriş noktalarının envanteri | Bulunan her rota özellik kimliği, sahip, bayrak ve biçime eşlenir |
| AR06 | Mevcut eski render karakterizasyonu | Düzenlemeden önce gerçek beklenen DSP sırası ve aktarım/varsayılan davranışı yakalanır |
| AR07 | Kabul edilmiş oturum başına katı/eski seçimi | Tek otorite, tek gönderim, sabitlenmiş rota; varsayılanlar korunur |
| AR08 | Aynı sentetik sesin gölge karşılaştırması | Sınırlı yan etkisiz karşılaştırma; ikinci gönderim yok |
| AR09 | Kabul edilmiş M01 `AudioChunk`/`RenderedFrame`/`PlaybackEvent` | Gerçek sözleşme eşlemesi; yinelenen genel tür yok |
| AR10 | Bilinmeyen zorunlu kapsam veya uyumsuz şema | Tipli ret/HOLD; sentetik kimlik yok |
| AR11 | Bilinen sayılı geçerli ham 48k mono Float32 yük | Bir kez kabul; değiştirilemez kaynak değişmez |
| AR12 | Yanlış hız, kodlama veya kanal/düzen | Yeniden etiketleme veya düzleştirme olmadan ret |
| AR13 | NaN/Inf, geçersiz yük uzunluğu, bool örnek sayısı | DSP/PCM dönüşümünden önce ret |
| AR14 | Aşırı sayı/bayt çarpımı veya sıfır veri çerçevesi | Tahsisten önce ret; boş veri EOS değildir |
| AR15 | Açık F5 yapısal hatası ile akustik UNKNOWN | Hata engeller; yalnız akustik UNKNOWN PASS'e yükseltilmez |
| AR16 | Aynı kimlikli çakışan parça veya sıra boşluğu | Yinelenen render yok; açık sıra/ret politikası |
| AR17 | Güvenilir WEB/AUDIOSOCKET seçimi | Kesin onaylı hız/biçim/profil sabitlenir |
| AR18 | Bilinmeyen veya sahte kanal üst verisi | Yetkisiz profil veya aktarım seçimi yok |
| AR19 | Akış başladıktan sonra yapılandırma değişir | Eski etkin profil korunur; yeni dönem açık |
| AR20 | A/B araya girmiş bağımsız akışlar | Her DSP çıktısı yalıtılmış referansına sabit toleransta eşit |
| AR21 | F0 giriş ve F6 çıkış yeniden örnekleyici örnekleri | Paylaşılan değiştirilebilir durum yok; ayrı yön ve sahipler |
| AR22 | Aynı sürekli generation içinde parça sınırları | Filtre geçmişi gerçek aşama politikasına göre korunur |
| AR23 | İptal edilmiş kalıntıdan sonra yeni generation/dönem | Eski filtre/kuyruk/çerçeve örnekleri yeni generation'a ulaşmaz |
| AR24 | Mevcut HPF'den (etkinse) analitik alçak frekans sinyali | Doğrulanmış taban yanıtı ve sıra; onaylı tolerans |
| AR25 | Mevcut EQ'dan (etkinse) analitik geçirme bandı sinyali | Doğrulanmış taban yanıtı; yeni EQ yok |
| AR26 | Mevcut limiter'dan (etkinse) yüksek genlik | Gerçek eski limiter sonucu korunur; gizli kazanç değişikliği yok |
| AR27 | Gerçek sınırda mevcut fade | Kanıtlanmış sınırda bir kez; çerçeve başına fade yok |
| AR28 | Kapalı DSP/konfor gürültüsü veya deney bayrağı | Onaylı kapalı davranış değişmez; sessiz etkinleşme yok |
| AR29 | Daha önce uygulanmamış açık desteklenen `post_pause` | Kabul edilen sınırda örnek muhasebesiyle tam bir kez |
| AR30 | Null duraklama veya yukarıda uygulanmış hız | Yinelenen duraklama veya hız dönüşümü yok |
| AR31 | Desteklenmeyen/bilinmeyen hız, duraklama, kontrol üst verisi | Sözleşmeye göre açık desteklenmiyor/HOLD; sahte uygulama yok |
| AR32 | Negatif/sonlu olmayan/devasa süre | Tahsisten önce ret; sınırlı sessizlik üretimi |
| AR33 | 48k→16k bilinen ardışık örnek sayısı | Sabit politikaya göre doğru oran ve tam akış sayısı |
| AR34 | 48k→8k bilinen ardışık örnek sayısı | Sabit politikaya göre doğru oran ve tam akış sayısı |
| AR35 | Asal ve düzensiz parça bölmeleri, iki hız | EOS sonrası aynı sürekli referansla karşılaştırma; parça başına kayma yok |
| AR36 | Uzun sınırlı sentetik akış, tekrarlı minik parçalar | Rasyonel faz/sayaçlar, sınırlı durum, birikmiş yuvarlama hatası yok |
| AR37 | Başlangıç tamponlama ve kuyruk boşaltma | Açık gecikme ve bir kez kuyruk; sahte örnek yok |
| AR38 | 1 kHz geçirme bandı, iki profil, DSP kapalı | Önceden beyan edilen taban/arka uç toleransını karşılar |
| AR39 | Web için 12 kHz, telefon için 6 kHz giriş | Onaylı toleransa göre kenar yumuşatma; ölçülen sentetik oran raporlanır |
| AR40 | Bekleyen yeniden örnekleyici durumuyla EOS öncesi iptal | Eski kuyruk yayılmaz; kesin hesaplanmış atma |
| AR41 | Sıfır, işaretli sınırlar, bilinen sonlu kesirler | Beklenen onaylı PCM16 sayısal eşlemesi |
| AR42 | Aralık dışı pozitif/negatif örnekler | Doyum, tamsayı sarması değil; etkilenen örnekler sayılır |
| AR43 | Negatif tamsayı ve bilinen PCM vektörü | Kesin little-endian baytlar |
| AR44 | Yarım adım yuvarlama eşitlikleri | Belgeli kural aynen uygulanır |
| AR45 | Ham tepe, limiter ve niceleme doyumu | Ayrı sayımlar; sonlu olmayan reddedilir; uydurma dBFS yok |
| AR46 | Web 320 örnek | Bir 20 ms 640 B tam çerçeve |
| AR47 | Telefon 160 örnek | Bir 20 ms 320 B tam çerçeve |
| AR48 | Çoklu düzensiz yeniden örneklenmiş bloklar | Tam çerçeveler sıralı; sınırlı kalan korunur |
| AR49 | Kısa kalanla EOS | Onaylı kısa/dolgu politikası ve kesin `valid_sample_count` |
| AR50 | Tam çerçeve sınırında EOS | Ek boş/tamamen dolgu veri çerçevesi yok |
| AR51 | Kasıtlı sessizlik ve terminal dolgu | Sessizlik geçerli içerik; dolgu ayrı ve iki kez sayılmaz |
| AR52 | Yinelenen/bayat terminal veya EOS | İkinci kuyruk veya terminal olay yok; yeni generation etkilenmez |
| AR53 | Parçalar arası sıra/ofset ilerlemesi | Belgeli kapsamda çıkış alanında monoton imleç |
| AR54 | 48k/16k/8k alanlarında iptal/atma muhasebesi | Açık aşama/hız defteri dengelenir; uyuşmayan sayılar karşılaştırılmaz |
| AR55 | Değiştirilebilirlik, çerçeve biçimi uyuşmazlığı veya geçersiz terminal sayısı | Ret; commit sonrası sahipli yük değiştirilemez |
| AR56 | Tam 8k PCM telefon çerçevesi | Destekleniyorsa gerçek tel başlığı `10 01 40`; kesin 320 baytlık LE gövde |
| AR57 | Kısmi/birleşik bayt sınırlı çoklu mesaj | Mevcut ayrıştırıcı/serileştirici sözleşmesi korunur; TCP paket sınırı değildir |
| AR58 | Desteklenmeyen tür/uzunluk taşması | Gönderimden önce ret; bozuk başlık yok |
| AR59 | Mevcut UUID/sonlandırma/hata/DTMF kontrolü | Ayrı yol korunur; kontrol ses temposuna girmez |
| AR60 | Aktarım kısmi yazma/belirsiz gönderim bildirir | Kör yeniden gönderim yok; doğru belirsizlik; güvenli kapanış yolu |
| AR61 | Web tam çerçeve | Destekleniyorsa 640 B PCM hedefli gerçek zarf; AudioSocket başlığı yok |
| AR62 | Mevcut web el sıkışma/kontrol ve istemci tarafı tempo | Korunur; yinelenen tempo yok; arayüz şeması değişmez |
| AR63 | İstemci yetenek uyuşmazlığı | Katı etkinleştirme HOLD; sessiz hız değişimi yok |
| AR64 | Sahte saatte sürekli 20 ms zamanlama | Kesin mutlak hedefler; birikimli uyku kayması yok |
| AR65 | Periyot içinde gönderim işleme gecikmesi | Sonraki hedef mutlak; tamamlanmadan sonra ek 20 ms yok |
| AR66 | Son tarihten sonra geç uyanma / yavaş boşalma | Sınırlı yeniden çapalama veya açık hata; yakalama patlaması yok |
| AR67 | Boşluk sonra veri devam | Açık boşluk/yeniden çapalama; gizli konfor sessizliği yok |
| AR68 | Saat alanı uyuşmazlığı veya duvar saati sıçraması | Geçersiz çıkarma yok; monoton zamanlama etkilenmez |
| AR69 | Yavaş alıcı ve sınırlı kapasite | Sayı/bayt/süre/uçuşta sınırı; açık geri basınç veya iptal |
| AR70 | Render öncesi ve sırasında iptal | Bayat sonuç kabul edilmez; gerçek kaynak ömrü korunur |
| AR71 | Çekişten sonra gönderimden önce bariyer | İptal kazanırsa sıfır bayat gönderim |
| AR72 | Önce gönderim sonra iptal | Uçuşta olabilir; geri çağırma iddiası yok; yinelenen gönderim/bırakma yok |
| AR73 | Sentezi bitmiş ama boşaltma yetkili generation | Geçerli son çerçeveler akar; iptal kalanları engeller |
| AR74 | Mevcut duraklat, bayat devam, yeni generation | Yalnız yetkili gönderilmemiş veri sürer; tekrar oynatma yok; F6-B geliştirmesi ertelenir |
| AR75 | Kopma, yinelenen kapanış/geri çağrı ve yeniden bağlanma | Sınırlı temizlik, yeni enkarnasyon, oturumlar arası medya yok |
| AR76 | İşçi/aktarım tamamlanması bilinmiyor | Kira tutulur/karantina; açık HOLD/FAIL; sahte temizlik yok |
| AR77 | Sunucu fikstüründe QUEUED/STARTED/DRAINED/COMPLETED | Doğru SERVER kapsamı; uydurma CLIENT/PBX/ENDPOINT makbuzu yok |
| AR78 | Mevcut boşaltma komutu ile gerçek yerel temizlik | FLUSH_REQUESTED ile kapsamlı FLUSHED ayrı; duyulan kesme iddiası yok |
| AR79 | Telemetri taşması ve özel dalga/kişisel veri işareti | Güvenli maskeleme/düşürme sayımı; iptal/gönderim etkilenmez |
| AR80 | Sahte modelle gerçek F5 orkestrasyonu geçerli `AudioChunk` yayar | Gerçek F6 yakalanan alıcıya render eder; yeniden normalizasyon veya çift DSP yok |
| AR81 | Kanıtlandığı haliyle eski metin önizleme, karşılama, aktarım ve DTMF yolları | Mevcut API davranışı ve yan etki sayısı korunur; yeni iş yürütmesi yok |
| AR82 | Gerçek M02 iptali + gerçek F6 + kaydeden aktarım | Belirlenimci çit ve tamamlanma kapsamları; sahte uzak oynatma yok |
| AR83 | M00/M01/M02/M04/F0/F5 etkilenen regresyonlar, mevcut arayüz/API/DB/yapılandırma envanteri | Açıklanamayan özellik/API/tel regresyonu yok; gerçek koşucu sonuçları |
| AR84 | İncelenmiş fark, kaynak hash'leri, geri dönüş provası ve temizlik | Yalnız yetkili değişiklikler; geri alınabilir etkinleştirme; önceki kanıt üzerine yazılmaz |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F6-A-G00 | Ön kontrol | Gerçek CG00–CG11, F5-A/M02 kabulü, güncel soy ve onay |
| F6-A-G01 | Tek otorite | Tek render/aktarım otoritesi, pasif içe aktarma, gerçek rota envanteri ve izin listesi |
| F6-A-G02 | Sözleşme ve profil | Kabul edilmiş M01/M02/F5 sözleşmeleri ve güvenilir akış/profil seçimi |
| F6-A-G03 | Giriş | Ham biçim, yük sayısı/sahipliği, yapısal koruma ve sınırlı doğrulama |
| F6-A-G04 | Durum | Sabitlenmiş yapılandırma ve akış/dönem/generation durum yalıtımı |
| F6-A-G05 | Eski DSP | Gerçek eski DSP davranışı/sırası/varsayılanları; çift uygulama yok |
| F6-A-G06 | Kontroller | İstenen/etkin kontrol sahipliği ve bir kez duraklama anlamı |
| F6-A-G07 | Yeniden örnekleme | İki hızda durumlu; bölme/sayı/EOS/kenar yumuşatma testleri sabit toleransla |
| F6-A-G08 | Niceleme | PCM16 ölçek/yuvarlama/doyum/bayt sırası ve kesin çerçeve baytları |
| F6-A-G09 | Çerçeveleme | 20 ms çerçeveleme, geçerli sayı, terminal ve örnek muhasebesi |
| F6-A-G10 | AudioSocket | Yalıtılmış fikstürde gerçek AudioSocket tel uyumu; kontrol ayrımı |
| F6-A-G11 | Web | Mevcut web aktarım uyumu ve tempo sahipliği |
| F6-A-G12 | Zamanlama | Monoton tempo, geç kalma/boşluk, yakalama patlaması yok |
| F6-A-G13 | Akış ve çit | Sınırlı akış, M02 bayat gönderim çiti ve uçuşta ayrımı |
| F6-A-G14 | Yaşam döngüsü | EOS/iptal/kapanış/kira temizliği; mevcut kontrol anlamı |
| F6-A-G15 | Olaylar | `PlaybackEvent` kapsam doğruluğu, M04 güvenli telemetri ve M07 gizlilik |
| F6-A-G16 | Entegrasyon | Onaylı test ikizleriyle gerçek F5/F6 bütünleşmesi; eski yol korunumu |
| F6-A-G17 | Test kanıtı | AR01–AR84 gerçek kapsamlı sonuçlar; zorunlu atlama yok |
| F6-A-G18 | Regresyon | Etkilenen regresyonlar, kaynak bütünlüğü ve incelenmiş geri dönüş |
| F6-A-G19 | Devir | Bağımsız inceleme, tüketici devri ve W2_GATE plan kaydı; uydurma W2 sonucu yok |

## 9. Kanıt

`evidence/F6-A/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `AUDIO_OUTPUT_INVENTORY.json`, `LEGACY_DSP_CHARACTERIZATION.json`, `CONTRACT_MAPPING.csv`, `CONTROL_APPLICATION_MATRIX.csv`, `RESAMPLER_REPORT.json`, `FRAMING_SPEC.md`, `WIRE_FIXTURES/` (sentetik), `PACING_SPEC.md`, `PLAYBACK_SCOPE_MATRIX.csv`, `W2_GATE_PLAN.md`, `TEST_MATRIX.json`. A0 taban ölçümü `data/F6/lab-report-a0-*.json`.

## 10. Geri dönüş

`f6_pipeline_v2=off`: eski render/gönderim yolu tek aktif. Katı yolun etkinleştirmesi oturum başında sabitlenir; geri dönüş yeni oturumlarda etkilidir. Kod değişiklikleri `git revert` ile geri alınır.

## 11. Devir

- **W2_GATE:** WI01–WI24 kaydedildi; çalıştırma ayrı onayla ([W2_GATE](W2_GATE-w2-kapisi.md)).
- **F1-B:** `PlaybackEvent` (kapsamlı), duraklat/devam/boşaltma ilkelleri ve uçuşta ayrımı söz kesme köprüsüne girdi.
- **F6-B:** oynatma kuyruğu, söz kesme köprüsü, hata yönetimi, tarayıcı makbuzları, AMI/ARI.
- **F6-C:** birleştirme, WSOLA, de-esser, loudness/limiter, konfor gürültüsü, kodek laboratuvarı — "tek kez" kuralı ve buradaki sıra korunarak.
- **G4:** pacing p95 ≤ 5 ms ve duyulan söz kesme p95 ≤ 200 ms hedefleri yalnız gerçek uç ölçümüyle.

## 12. Başlatma komutu

```
F6-A paketini uygula: docs/execution/packages/W2/F6-A-render-aktarim.md.
Kuralları CLAUDE.md'den oku; CORE_GATE, F5-A ve M02 kabulünü doğrula; mevcut çıkış DSP'sini düzenlemeden önce karakterize et.
backend/audio_rendering/ ve backend/media_transport/ altında durumlu render, 20 ms çerçeveleme,
monoton zamanlayıcı ve M02 gönderim çitini f6_pipeline_v2 arkasında kur. WI01–WI24'ü yalnız kaydet.
AR01–AR84'ü çalıştır, F6-A-G00…G19'u değerlendir, paket/F6-A dalında PR aç ve dur.
```
