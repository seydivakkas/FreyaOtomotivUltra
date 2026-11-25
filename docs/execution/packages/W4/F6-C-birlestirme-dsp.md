# F6-C — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı

> F6-A/F6-B render hattına (kapalı profil arkasında): tek hız sahibine bağlı sınırlı WSOLA, aynı kapsamdaki komşu parçalar için uyarlanır çapraz geçiş, doğal sessizlik kredisi ve **toplam** hedefe göre anlamsal duraklama ekleme, hıza duyarlı de-esser, kararlı EQ, sınırlı yumuşatılmış loudness ve son hızda tek limiter, durumlu yeniden örnekleme ve PCM çerçeveleme, oynatma referansının korunması; yalıtılmış G.711/G.722/Opus kodek laboratuvarı. Her etki tek sahipli ve bir kez; korumalı grup veya güçlü sınır üzerinde karıştırma yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F6-C |
| Dalga | W4 |
| Öncelik | P1 |
| Önkoşullar | W2_GATE, F6-B, F4-C, F5-B |
| Sonraki | G2 |
| Bayrak | `f6_pipeline_v2` + M03 profili `f6.enhanced_render` (`OFF / SHADOW / GUARDED`; varsayılan OFF) + `f6.codec_lab` (yalnız laboratuvar) |
| Ortam | CPU (sentetik sinyaller); yerel kodek ikilileri yalnız yerelde ve lisanslıysa |
| Eski görevler | F6-T06, F6-T07, F6-T08, F6-T09, F6-T11, F6-T12, F6-T14 |
| Kaynak | Bundle `W4/Freya_2_0_F6_C_Agent_Implementation_Package.md`; [F6 spec](../../../stages/F6-rendering-transport/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Cümlecik geçişlerinde keskin kesintiler, ard arda iki duraklama, hem modelde hem render'da uygulanan hız veya iki kez uygulanan fade sesi bozar. `experimental/prosody_wsola_streamer.py` zaten var ama canlı hatta bağlı değil. F6-C bunları **ölçülebilir ve kapalı varsayılanla** bağlar; G.711/G.722/Opus gibi kodeklerin telefon kalitesine etkisini yalnız yalıtılmış laboratuvarda inceler.

## 2. Başlamadan önce

- [ ] W2_GATE, F6-B, F4-C, F5-B gerçek kabul; onay. F5-C yoksa yeni kenar eklenmez.
- [ ] Tüm render/kodek yolları, bayraklar, gerçek hızlar ve yinelenen aşamalar (ör. iki fade çağrısı) envanterde; mevcut WSOLA deneysel olarak sınıflanmış, canlı iddiası yok.
- [ ] Eski profil kapalıyken önceki altın fikstürler aynı çıktı/çerçeveleme/kontrol davranışını verir.
- [ ] Kodek ikilileri ve lisansları yalnız envanterde; kurulum yok.

## 3. Kapsam

**Yapılacak:** Sözleşme ve kabul; sabit profiller ve aşama sırası; hız sahipliği; WSOLA adaptörü; sınır birleştirme; uyarlanır çapraz geçiş; doğal sessizlik; anlamsal duraklama; de-esser; EQ; loudness ve limiter; yeniden örnekleme ve PCM çerçeveleme; rezervasyon ve yaşam döngüsü; referans korunumu; kodek yeteneği; G.711/G.722/Opus laboratuvarı; hizalama ve bozulma protokolü; telemetri ve kipler; entegrasyon ve F6-D devri.

**Yapılmayacak:** Kodek kurulumu, canlı aktarıma kodek ekleme, ağ; konfor gürültüsü varsayılan etkinleştirmesi; gerçek uç ölçümü (G4/G5); akustik kalite iddiası; F5'in uyguladığı hızın tekrarı.

## 4. Dosyalar

```
backend/audio_rendering/enhanced/
  profile.py  rate_owner.py  wsola.py  boundary_assembly.py  crossfade.py
  natural_silence.py  semantic_pause.py  deesser.py  eq.py  loudness_limiter.py
  resample_frame.py  reservation.py  reference_tap.py  telemetry.py
backend/audio_rendering/codec_lab/
  capability.py  g711.py  g722.py  opus.py  alignment.py  impairment.py
tests/audio_rendering/enhanced/  tests/audio_rendering/codec_lab/
evidence/F6-C/<run_id>/
```

`experimental/prosody_wsola_streamer.py` adaptörle yeniden kullanılır; silinmez.

## 5. Tasarım ve sözleşmeler

### 5.1 Aşama sırası (geliştirilmiş profil)

```
AudioChunk (48k mono f32, ham) ─► [hız sahibi F6 ise] WSOLA ─► sınır birleştirme + çapraz geçiş
  ─► doğal sessizlik kredisi + anlamsal duraklama ─► de-esser ─► EQ ─► loudness
  ─► durumlu yeniden örnekleme (16k/8k) ─► son hızda tek limiter ─► PCM16 ─► 20 ms çerçeve ─► F6-B
```

Her aşama tek sahipli; eski aşamayla eşdeğer olan geliştirilmiş aşama aynı anda etkin olmaz (ör. eski EQ + yeni EQ). Gölge kip aynı girdide ek oynatma veya gerçek etki üretmez.

### 5.2 Hız ve WSOLA

- F5 0,94 uyguladıysa ve F6'ya aynı faktör istendiyse → F6 bypass, gerçek model ayarı kaydedilir. F6 sahibi 0,98 ve F5 nötr doğrulanmışsa → bir kez uygula. F5 uygulanan kontrol durumu bilinmiyorsa → geliştirilmiş hız yok, zorunlu kontrol HOLD. 0,90/0,93 aday WSOLA aralığı dışında (0,94–1,06) → sessiz kırpma yok, onaylı no-op veya HOLD. 1,0 → gizli gecikmesiz tam no-op. Duraklat/devam sonrası yinelenen hız geri çağrısı → ikinci uygulama veya yeniden render yok.
- WSOLA: 0,94 ve 1,06 sinüs fikstürlerinde onaylı algoritmaya göre sınırlı çıktı sayısı ve faz muhasebesi; asgari pencereden kısa girdi → açık bypass/ret; sıfır enerjili korelasyon → sonlu belirlenimci geri düşme; eşit korelasyon adayları → belirlenimci; segment sınırı yakınında geçiş/dürtü → beklenmedik silme yok; çok blokta kesirli atlama → birikmiş yuvarlama kayması yok; en kötü arama/pencere için işlem, bayt ve ileri bakış tahsisten önce sınırlanır; EOS'ta tutulan kuyruk bir kez, iptalde yalnız eski durum atılır.

### 5.3 Birleştirme, çapraz geçiş, sessizlik ve duraklama

- Birleştirme: aynı kapsam ve yasal sınırdaki komşu parçalar → sınırlı kuyruk/baş eşleşmesi; eksik/sırasız komşu → sınırsız yeniden sıralama yok; korumalı grup veya güçlü duraklama → örtüşme yasak; kuyruk son tarihinde sonraki parça yoksa kuyruk bir kez bırakılır (sonradan örtüşme yok); terminal parça komşusuz → kuyruk bir kez, hayali sonraki yok.
- Çapraz geçiş: sıfır örtüşme → kesin birleştirme veya açık atanmış kenar fade'i; 480 örnek aday ama 120 uygun örnek → örtüşme ≤ 120; aynı sabit girdilerde tamamlayıcı yükseltilmiş kosinüs → ilişkili genlik artışı yok; L=1 özel durum belirlenimci; farklı generation/dönem çifti asla karıştırılmaz; yinelenen sınır geri çağrısı tekrar örtüşme veya örnek silme üretmez.
- Doğal sessizlik: yalnız gerçek nitelikli aralıklar doğru örnekleme hızında kredilenir; sessiz sesli konuşma veya nefes → kredi yok/UNKNOWN (konuşma kırpılmaz); eksik/bilinmeyen kenar → uydurma sıfır ölçüm yok; iki duraklama arasındaki tamamen sessiz parça → sınırlar arası ayrık krediler; hız/örtüşme değiştiyse kredi dönüşüm sonrası alanda ölçülür.
- **Anlamsal duraklama (toplam hedef):** 48 kHz'te 160 ms hedef, kuyruk 40 ms + baş 20 ms → **4 800** örnek eklenir, kredilenen + eklenen = **7 680**. Doğal sessizlik hedefi aşarsa sıfır eklenir; doğal sessizlik asla kısaltılmaz. Null / açık sıfır / eski ek duraklama ayrı anlamlar; belirsiz eski `post_pause_ms` yeniden yorumlanmaz (taban veya HOLD). Toplam duraklama sınırı aşılırsa yayından önce ret/onaylı geri düşme. Yalnız sondan kanıtlı terminal duraklamada uydurma sağ baş yok. Tekrarlanan duraklama isteği tek sınır tüketimi. Konfor gürültüsü onaylıysa aynı kasıtlı duraklama uzunluğu, gürültü durumu açık.

### 5.4 De-esser, EQ, loudness, limiter

Hedef Nyquist üzerindeki de-esser bandı → geçersiz profil veya doğrulanmış alternatif hız; ıslıklı ve korumalı konuşma fikstürlerinde sınırlı kazanç azaltma (susturma yok); sessizlik/bilinmeyen enerjide kontrolsüz azaltma veya pompalama yok; kararsız filtre katsayıları etkinleşmeden reddedilir. EQ 48k ve 8k için ayrı doğru katsayılar; eşdeğer aşamanın tek etkin sahibi. RMS/tepe dBFS ile erişilemez LUFS ayrı (LUFS null). Sessizlikten sonra etkin sinyalde sınırlı yumuşatılmış kazanç (sessizlik yükseltme yok). Geçişte limiter onaylı örnek tavanında; yeniden örneklemeden sonra **tek** son hız limiter'ı (varsayılan çift limiter yok). PCM tam ölçekte sarmasız doyum. Sonlu olmayan DSP ara değeri çerçevelemeden önce güvenli iptal. İki oturum karşıt kazanç/filtre geçmişiyle bağımsız.

### 5.5 Çerçeveleme, kaynaklar ve referans

48k→16k ve 48k→8k düzensiz bölmelerde birikimli hız eşlemesi; dürtü/Nyquist üstü fikstürde sınırlı gecikme ve kenar yumuşatma (ölçülmüş performans iddiası yok); EOS iki kez → tek kuyruk/terminal çerçeve; kalanlı iptal → eski durum defterle atılır. 20 ms web 320 örnek/640 B, AudioSocket 160 örnek/320 B; tam 8k çerçevede `10 01 40` başlık + PCM16 LE; eksik terminal çerçevede açık geçerli sayı, dolgu bir kez. En kötü germe + duraklama + çalışma alanı sınırı aşarsa tahsisten önce ret; DSP sonrası kuyruk dolu → sınırlı geri basınç (yeni gizli kuyruk yok); yumuşak duraklatmada kuyruk/yeniden örnekleyici durumu ve kesin gönderilmemiş imleç korunur (yeni DSP geçişi yok); kesin kesme seçili gönderilmemiş çerçeveyle yarışırsa çit yeni talebi engeller; talepten sonra iptal → uçuşta izlenir, geri çağırma vaadi yok. Referans: tüm dönüşümler/PCM sonrası talep edilmiş yükle bayt bayt aynı; gönderilmemiş silinmiş veya spekülatif PCM referans olmaz; bilinmeyen teslim/saat → açık bilinmiyor/boşluk.

### 5.6 Kodek laboratuvarı (yalıtılmış)

| Kodek | Fikstür sözleşmesi |
| --- | --- |
| G.711 A-law / μ-law | Ayrı kipler; işaret/sıfır eşlemesi; 8 kHz 20 ms → 160 örnek, 160 kodlanmış oktet (64 kb/s; gerçek çıktı sonra) |
| G.722 | 16 kHz PCM, 8 kHz RTP saati: 20 ms'de 320 PCM örneği, 160 RTP tik |
| Opus | 20 ms'de 48 kHz saat 960 tik; paket baytı ölçülene kadar null |

Yerel ikili veya lisans yoksa yerel yetenek HOLD (kurulum/sahte ikame yok). Laboratuvar rotası canlı aktarım yazıcısını hedeflerse engellenir. Desteklenmeyen hız/çerçeve isteği tam sağlayıcı sınırlamasıyla reddedilir; bozuk paket → kırpma veya sahte çözülmüş ses yok; denemeler arası kod çözücü durumu taşınmaz; kodek gecikmesi ve uyuşmayan bant genişliği açık hizalama ve eşleşen bant karşılaştırıcısıyla (seçici sonuç yok); seed'li kayıp/patlama/yeniden sıralama belirlenimci ve sınırlı; desteklenmeyen PLC/FEC/DTX → bilinmiyor/desteklenmiyor; eksik metrik bağımlılığı veya yetersiz sesli süre → null (sıfır skor değil).

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F6-C.01 | Ön kontrol ve soy | Sahip yetkisi; çekirdek/W2/doğrudan kapılar | DC01–DC04 |
| F6-C.02 | Envanter ve sahiplik | Tüm render/kodek yolları ve bayraklar, gerçek hızlar, yinelenen aşamalar | DC05–DC08 |
| F6-C.03 | Sözleşmeler ve kabul | Değiştirilemez girdiler, kapsamlar, sınır doğrulaması, özel yan kayıtlar | DC09–DC14 |
| F6-C.04 | Sabit profiller | İncelenmiş kapalı profil ve aşama sırası; yetenek ve etkin değerler | DC15–DC18 |
| F6-C.05 | Hız sahipliği | İstenen/etkin/uygulanan hız; çift dönüşüm yok; desteklenmeyen reddi | DC19–DC24 |
| F6-C.06 | WSOLA adaptörü | Sınırlı yeniden kullanım, belirlenimci arama, gerçek örnek muhasebesi | DC25–DC33 |
| F6-C.07 | Sınır birleştirme | Sıralı parça eşleme, güvenli kuyruk/baş uygunluğu, son tarih | DC34–DC38 |
| F6-C.08 | Uyarlanır çapraz geçiş | Sınırlı örtüşme, tamamlayıcı pencere; korumalı/duraklama/dönem ötesi yok | DC39–DC44 |
| F6-C.09 | Doğal sessizlik | Muhafazakâr nitelikli kenar gözlemi, ayrık kredi | DC45–DC49 |
| F6-C.10 | Anlamsal duraklama | Benzersiz TOPLAM/EK niyet; net ekleme kredisi; sınır ve atomiklik | DC50–DC57 |
| F6-C.11 | De-esser | Sınırlı hıza duyarlı azaltma; sessizlik ve korumalı konuşma | DC58–DC61 |
| F6-C.12 | EQ | Kararlı filtreler, Nyquist ve pay; yinelenen eski aşama yok | DC62–DC63 |
| F6-C.13 | Loudness ve limiter | Sınırlı yumuşatılmış kazanç, son hız limiter'ı, doğru RMS/tepe | DC64–DC70 |
| F6-C.14 | Yeniden örnekleme ve PCM çerçeveleme | Durumlu hız eşlemesi, sonlu niceleme, terminal geçerli/dolgu | DC71–DC78 |
| F6-C.15 | Rezervasyon ve yaşam döngüsü | En kötü çalışma alanı/çıkış rezervi; duraklat/devam/iptal | DC79–DC84 |
| F6-C.16 | Referans korunumu | PCM sonrası talep musluğu; boşluk ve bilinmeyen durum; sınırlı geçmiş | DC85–DC88 |
| F6-C.17 | Kodek yeteneği | Onaylı yerel adaptörlerin incelenmesi; laboratuvar yalıtımı; kurulum yok | DC89–DC91 |
| F6-C.18 | G.711/G.722/Opus laboratuvarı | Yalıtılmış kodlama/çözme ve paket saati/sayı fikstürleri | DC92–DC98 |
| F6-C.19 | Hizalama ve bozulma | Eşleşen bant, gecikme, belirlenimci kayıp ve metrik protokolü | DC99–DC102 |
| F6-C.20 | Telemetri ve kipler | Sınırlı güvenli gözlemler, KAPALI regresyonu, gölge yan etkisiz | DC103–DC105 |
| F6-C.21 | Entegrasyon ve F6-D devri | Gerçek F4/F5/F6-B/M02 yolu; isteğe bağlı noktalar | DC106–DC107 |
| F6-C.22 | Belirlenimci doğrulama | DC01–DC108 ve ilgili önceki testler yalıtılmış koşucuda | Tüm testler çalıştırılmış |
| F6-C.23 | Regresyon, geri dönüş, benchmark | Özellik envanteri, regresyon/geri dönüş, benchmark protokolü | DC108 |
| F6-C.24 | Kabul ve durma | F6-C-G00…G19 bağımsız gözden geçiren; gerçek kapsam/hazırlık | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| DC01 | Çekirdek kapı yok | Düzenlemeden önce HOLD; uydurma soy yok |
| DC02 | Yalnız W2 uygunluk bayrağı, kabul edilmiş WG kanıtı yok | HOLD; uygunluk kabul değildir |
| DC03 | Bir doğrudan bağımlılık kabul edilmemiş | HOLD; kaynak değişikliği yok |
| DC04 | Tüm doğrudan kanıt var ama F5-C yok | Yalnız sahip yetkisiyle ilerle; eklenen kenar yok |
| DC05 | Mevcut DSP rota envanterinde iki fade çağrısı | Gerçek sahiplik kaydedilir; geliştirilmiş yineleme engellenir |
| DC06 | Mevcut WSOLA deneysel yolu bağlı değil | Deneysel sınıflanır; canlı iddiası yok |
| DC07 | Eski profil KAPALI ve önceki altın fikstürler | Aynı onaylı çıktı/çerçeveleme/kontrol davranışı |
| DC08 | Çözülmemiş özellik kimlikleri veya kaynak revizyonu uyuşmazlığı | Geçişten önce engel kaydedilir |
| DC09 | Geçerli 48k mono f32le parça, kesin baytlar ve güncel kapsam | Yalnız rezervasyonla değiştirilemez görünüm kabul |
| DC10 | Yanlış hız/kanal/kodlama veya geçersiz şekil | Ret; örtük biçim onarımı yok |
| DC11 | NaN veya Inf yük | Ret; geçersiz örnekleri gizleyen doyum yok |
| DC12 | F5 yapısal FAIL ile akustik UNKNOWN | FAIL engellenir; bilinmeyen akustik bilinmiyor kalır |
| DC13 | Bayat generation veya uyuşmayan plan/parça | DSP'den önce ret; yeni kuyruk girdisi yok |
| DC14 | Yinelenen parça kimliği değişmiş yük | Çakışma; üzerine yazma veya yinelenen teslim yok |
| DC15 | Duraklatılmış generation sırasında profil değişir | Sabit etkin ayarlar korunur; plan ortasında değişiklik yok |
| DC16 | Desteklenmeyen profil bayrağı/yeteneği | Geliştirilmiş etkinleşme yok; politikaya göre taban veya HOLD |
| DC17 | Katsayı/hız/sınır tamsayı veya sonlu olmayan doğrulama | Tahsisten önce bozuk ayarlar reddedilir |
| DC18 | Gölge dala aynı canlı girdi verilir | Ek oynatma veya gerçek etki yok; sınırlı üst veri |
| DC19 | F5 0,94 uyguladı, F6'dan aynı faktör istendi | F6 bypass; gerçek model ayarı kaydedilir |
| DC20 | F6 sahibi 0,98 ve doğrulanmış F5 nötr | Bir kez uygula; gerçek render ayarı kaydedilir |
| DC21 | Bilinmeyen F5 uygulanan kontrol durumu | Geliştirilmiş hız yok; zorunlu kontrol HOLD |
| DC22 | Aday WSOLA aralığı dışında istenen 0,90 veya 0,93 | Sessiz kırpma yok; onaylı no-op veya HOLD |
| DC23 | İstenen faktör 1,0 | Gizli gecikmesiz kesin no-op yolu |
| DC24 | Duraklat/devam sonrası yinelenen hız geri çağrısı | İkinci uygulama veya yeniden render yok |
| DC25 | 0,94'te gerçek uzunluk sinüs fikstürü | Onaylı algoritmaya göre beklenen sınırlı çıktı sayısı; uydurma yok |
| DC26 | 1,06'da gerçek uzunluk sinüs fikstürü | Sayı ve faz hesaplanır; güvensiz kırpma yok |
| DC27 | Asgari WSOLA penceresinden kısa | Açık bypass veya güvenli ret; geçersiz örtüşme yok |
| DC28 | Sıfır enerjili korelasyon araması | Sonlu geri düşme; belirlenimci sonuç |
| DC29 | Tekrarlanan eşit korelasyon adayları | Belirlenimci eşitlik çözümü |
| DC30 | Segment sınırı yakınında geçiş/dürtü girdisi | Beklenmeyen silme yok; sınırlı güvenli yol veya geri düşme |
| DC31 | Çok blokta kesirli atlama | Sınırsız birikimli yuvarlama kayması yok; kesin sayılar kaydedilir |
| DC32 | En kötü onaylı arama/pencere ve girdi boyutu | Tahsisten önce işlem, bayt ve ileri bakış sınırlanır |
| DC33 | Tutulan WSOLA kuyruğuyla EOS ve iptal | EOS bir kez; iptal yalnız eski durumu atar; sonraki generation'a sızma yok |
| DC34 | Eşleşen kapsam ve yasal sınırlı komşu parçalar | Uygun sınırlı kuyruk/baş eşleşmesi |
| DC35 | Eksik veya sırasız komşu | Sınırsız yeniden sıralama veya sınır ötesi birleştirme yok |
| DC36 | Korumalı grup veya güçlü duraklama | Örtüşme yasak |
| DC37 | Kuyruk son tarihinde sonraki parça yok | Kuyruk bir kez bırakılır; sonraki parça geriye dönük örtüşemez |
| DC38 | Komşusuz terminal parça | Kuyruk bir kez boşaltılır; hayali sonraki parça yok |
| DC39 | Sıfır örtüşme | Kesin birleştirme veya açık atanmış kenar fade'i |
| DC40 | Yalnız 120 uygun örnekli 480 örnek aday | Örtüşme ≤ 120 ve beyan edilen sayı |
| DC41 | Aynı sabit girdilerde tamamlayıcı yükseltilmiş kosinüs | Sayısal toleransın ötesinde ilişkili genlik artışı yok |
| DC42 | L=1 özel durum | Belirlenimci sonlu kural; kesin sayılar |
| DC43 | İlgisiz generation/dönemle çapraz geçiş | Çift reddedilir; asla karıştırılmaz |
| DC44 | Yinelenen sınır geri çağrısı | Tekrar örtüşme veya örnek silme yok |
| DC45 | Bilinen sessizlik aralıklı kuyruk ve baş | Yalnız gerçek nitelikli aralıklar doğru hızda kredilenir |
| DC46 | Sessiz sesli konuşma veya nefes fikstürü | Muhafazakâr kredi yok veya UNKNOWN; konuşma kırpılmaz |
| DC47 | Eksik baş veya bilinmeyen kenar gözlemi | Uydurma sıfır ölçüm yok; yalnız incelenmiş geri düşme |
| DC48 | İki duraklama arasında tamamen sessiz parça | Krediler sınırlar arasında ayrık |
| DC49 | Hız/örtüşme kenar uzunluklarını değiştirdi | Kredi dönüşüm sonrası alanda ölçülür; ham sayı yeniden kullanılmaz |
| DC50 | 48k'da 160 ms hedef, kuyruk 40 ms / baş 20 ms | 4800 örnek eklenir; toplam kredilenen + eklenen 7680 |
| DC51 | Doğal sessizlik hedefi aşar | Sıfır eklenir; doğal sessizlik asla kısaltılmaz |
| DC52 | Null ile açık sıfır ile eski ek duraklama | Ayrı anlamlar; gizli ekleme veya çıkarma yok |
| DC53 | Belirsiz eski `post_pause_ms` | Yeniden yorumlanmaz; gerçek taban veya HOLD |
| DC54 | Toplam duraklama sınırı aşıldı | Yayından önce ret/onaylı geri düşme; sessiz aşma yok |
| DC55 | Yalnız sondan kanıtlı terminal duraklama | Uydurma sağ baş yok; tek ekleme kararı |
| DC56 | Tekrarlanan duraklama isteği veya kabul yeniden denemesi | Tek sınır tüketimi; yinelenen süre yok |
| DC57 | Konfor gürültüsü etkin onaylı duraklama | Aynı kasıtlı duraklama uzunluğu; gürültü durumu açık |
| DC58 | Hedef Nyquist üzerinde de-esser bandı | Geçersiz profil veya doğrulanmış alternatif hız; geçersiz filtre yok |
| DC59 | Islıklı ve korumalı konuşma fikstürleri | Sınırlı kazanç azaltma; susturma veya keyfi konuşma silme yok |
| DC60 | Sessizlik/bilinmeyen enerji | Kontrolsüz azaltma veya kazanç pompalama yok |
| DC61 | Kararsız filtre katsayıları | Etkinleşmeden önce ret |
| DC62 | 48k ve 8k farklı hız fikstürlerinde EQ | Doğru katsayılar ve geçerli bantlar; yanlış hız yeniden kullanımı yok |
| DC63 | Eski EQ artı geliştirilmiş EQ bayrağı | Eşdeğer aşamanın tam bir etkin sahibi |
| DC64 | RMS/tepe dBFS ile erişilemez LUFS | Ayrı ölçüler raporlanır; LUFS null |
| DC65 | Sessizlik sonra etkin sinyal | Sınırlı yumuşatılmış kazanç; sessizlik yükseltme yok |
| DC66 | Geçişli yüksek genlik fikstürü | Limiter sonlu ve onaylı örnek tavanı/toleransı içinde |
| DC67 | Yeniden örnekleme sonrası ile öncesi limiter | Tek son hız aşaması; varsayılan çift limiter yok |
| DC68 | PCM pozitif/negatif tam ölçek | Sarmasız doyum; kabul edilmiş eşleme korunur |
| DC69 | Sonlu olmayan üretilmiş DSP ara değeri | Çerçevelemeden önce güvenli iptal; sahte geçerli çıktı yok |
| DC70 | Karşıt kazanç/filtre geçmişli iki oturum | Bağımsız durum; oturumlar arası sızıntı yok |
| DC71 | 48k→16k düzensiz bölünmüş kaynak parçaları | Kabul edilmiş birikimli hız eşlemesi; parça başı yuvarlama yok |
| DC72 | 48k→8k düzensiz parça bölmeleri | Kesin sağlayıcı faz/kuyruk muhasebesi |
| DC73 | Dürtü/Nyquist üstü fikstür | Sınırlı gecikme ve kenar yumuşatma yolu; henüz ölçülmüş performans iddiası yok |
| DC74 | İki kez EOS boşaltma | Yalnız bir kabul edilmiş kuyruk/terminal çerçeve |
| DC75 | Yeniden örnekleyici kalanıyla iptal | Eski durum defterle atılır; yeni generation'a asla boşaltılmaz |
| DC76 | 20 ms web ve AudioSocket çerçeveleme | Sırasıyla 320/160 geçerli örnek ve 640/320 yük baytı |
| DC77 | AudioSocket başlığı ve yük bayt sırası | Tam 8k çerçeve için `10 01 40` başlık; PCM16 LE yük |
| DC78 | Eksik terminal çerçeve | Açık geçerli sayı; dolgu bir kez; anlamsal süreden hariç |
| DC79 | En kötü germe artı duraklama ve çalışma alanı sınırı aşar | Tahsisten önce ret; kısmi sessiz sonek kaybı yok |
| DC80 | DSP sonucundan sonra kuyruk dolu | Sınırlı geri basınç ve sahiplik; yeni gizli kuyruk yok |
| DC81 | Kuyruk/yeniden örnekleyici durumuyla yumuşak duraklatma | Durum ve kesin gönderilmemiş imleç korunur; yeni DSP geçişi yok |
| DC82 | Kesin kesme seçili gönderilmemiş çerçeveyle yarışır | Çit yeni talebi engeller ve eski sahipli durumu siler |
| DC83 | Gönderim talebinden sonra iptal | Uçuşta izlenir; geri çağrılan bayt veya duyulan sessizlik vaadi yok |
| DC84 | Kapanış/yeni generation sonrası eski DSP tamamlanması | Yalnız kendi kirasını temizler; yeni kapsamı yayımlayamaz/değiştiremez |
| DC85 | Tüm dönüşümler/PCM sonrası referans çerçevesi | Talep edilmiş yükle bayt bayt aynı; doğru geçerli sayı ve ofset |
| DC86 | Gönderilmemiş silinmiş veya spekülatif PCM | Canlı oynatma referansı yayımlanmaz |
| DC87 | Bilinmeyen teslim veya eksik saat eşlemesi | Açık bilinmiyor/boşluk; uydurma uç gözlemi yok |
| DC88 | Referans bütçesi dolu ve iptal sonrası eski gönderilmiş kuyruk | Boşlukla sınırlı düşürme/tahliye; izinli korunur |
| DC89 | Yerel kodek ikilisi yok veya onaylanmamış lisans | Yerel yetenek HOLD; kurulum veya sahte ikame yok |
| DC90 | Kodek adaptörü desteklenmeyen hız/çerçeve isteği | Ret ve kesin sağlayıcı sınırlaması raporu |
| DC91 | Laboratuvar rotası yanlışlıkla canlı aktarım yazıcısını hedefler | Engellenir; ağ/yan etki yok |
| DC92 | Sahte/yerel sınır ayrımlı G.711 A-law uygunluk vektörleri | Doğru fikstür şeması; gerçek uygunluk sonra |
| DC93 | G.711 μ-law uygunluk vektörleri ve işaret/sıfır eşlemesi | Ayrı kip; yanlış etiketli doğrusal PCM yok |
| DC94 | G.711 8k 20 ms nominal paket | 160 örnek, 64 kb/s'de 160 kodlanmış oktet (gerçek çıktı sonra gerekir) |
| DC95 | G.722 16k PCM ve 8k RTP saati | 20 ms'de 320 PCM örneği, 160 RTP tik |
| DC96 | Opus 20 ms 48k saati ve değişken paket baytı | 960 tik; gerçek bayt ölçülene kadar null olabilir |
| DC97 | Kodek çerçeve hızı uyuşmazlığı veya bozuk paket | Ret; kırpma veya sahte çözülmüş ses yok |
| DC98 | Deneme EOS dolgusu/kod çözücü sıfırlama ve başka deneme | Kesin geçerli kapsam; denemeler arası durum taşınmaz |
| DC99 | Kodek gecikmesi ve uyuşmayan bant genişliği | Açık hizalama ve eşleşen bant karşılaştırıcısı; seçici sonuç yok |
| DC100 | Seed'li kayıp/patlama/yeniden sıralama denemesi | Belirlenimci hata dizisi; sınırlı; canlı aktarım yok |
| DC101 | Desteklenmeyen PLC/FEC/DTX kipi | Yetenek UNKNOWN/UNSUPPORTED; uydurma kurtarma yok |
| DC102 | Eksik metrik bağımlılığı veya yetersiz sesli süre | Null/yetersiz metrik; sıfır skor değil |
| DC103 | Telemetri ham ses/metin/kişisel veri/hash dener | Güvenli izin listesi hassas yükü reddeder |
| DC104 | Yol/istisnalı kodek laboratuvarı veya render hatası | Maskeli kategori, sınırlı olay; gerçek defter değişmez |
| DC105 | OFF/SHADOW/korumalı kip geçişleri ve revizyon sabitlemeleri | Onaysız etki yok; taban korunur; etkinleştirme kanıta bağlı |
| DC106 | Hız, duraklama, iptalle gerçek F4/F5/F6-B/M02 bütünleşmesi | Güncel kesin çıktı ve makbuz kapsamı; çift uygulama yok |
| DC107 | F5-C var/yok; F0-B isteğe bağlı referans tüketicisi; F6-D yapılmamış | Gerçek uyumlu nokta; ters bağımlılık yok |
| DC108 | Doygunlukta önceki regresyon paketi ve geri dönüş | Özellik/API/DTMF regresyonu yok; kapsamlı kaynaklar bırakılır |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F6-C-G00 | Ön kontrol | Çekirdek/W2/doğrudan bağımlılıklar incelenmiş soyda kabul; DC01–DC04; sahip yetkisi |
| F6-C-G01 | Sahiplik ve uyum | Tek gerçek render, yazıcı ve kuyruk; taban envanteri ve eski altın fikstürler; DC05–DC08 |
| F6-C-G02 | Sözleşmeler | Değiştirilemez ham plan/parça/güncel kapsam; katı biçim ve kabul; DC09–DC14 |
| F6-C-G03 | Profiller | Sabit revizyon, sonlu sınırlar, onaysız etkinleşme yok; DC15–DC18 |
| F6-C-G04 | Hız sahipliği | Tek etkin hız kontrolü; açık desteklenmiyor; seed değişmez; DC19–DC24 |
| F6-C-G05 | WSOLA | Sınırlı belirlenimci algoritma ve kesin muhasebe/no-op/iptal fikstürleri; DC25–DC33; akustik kabul ertelenmiş |
| F6-C-G06 | Sınır birleştirme | Aynı kapsamlı uygun komşu parçalar, sınırlı kuyruk ve terminal işleme; DC34–DC38 |
| F6-C-G07 | Çapraz geçiş | Güvenli örtüşme, kesin defter; korumalı/güçlü sınır karıştırması yok; yinelenen fade yok; DC39–DC44 |
| F6-C-G08 | Doğal sessizlik | Nitelikli ayrık krediler; bilinmeyen sıfır değil; konuşma silme yok; DC45–DC49 |
| F6-C-G09 | Anlamsal duraklama | Benzersiz niyet, toplam/ek eşlemesi, kesin ekleme ve sınırlar; DC50–DC57 |
| F6-C-G10 | De-esser/EQ | Hıza duyarlı kararlı sınırlı işleme; yinelenen DSP yok; DC58–DC63 |
| F6-C-G11 | Loudness/limiter | Sınırlı kazanç, sonlu çıktı, gerçek örnek tepe/niceleme, yalıtılmış durum; DC64–DC70 |
| F6-C-G12 | Yeniden örnekleme/çerçeveleme | Sürekli hız fazı, EOS geçerli/dolgu, tel biçimi değişmez; DC71–DC78 |
| F6-C-G13 | Kaynaklar/iptal | M02/F6-B rezervasyonu, kesin devam ve sert çit; bayat yayın/erken bırakma yok; DC79–DC84 |
| F6-C-G14 | Oynatma referansı | Gerçek son PCM talep musluğu; sınırlı gizlilik/boşluk ve kapsam; DC85–DC88 |
| F6-C-G15 | Kodek laboratuvarı | Yalıtılmış yetenek ve protokol/biçim/metrik fikstürleri DC89–DC102; yerel profil HOLD kalır |
| F6-C-G16 | Kipler/entegrasyon | M04 güvenli telemetri, gerçek katmanlar arası arayüzler ve isteğe bağlı uyum; DC103–DC107 |
| F6-C-G17 | Test kanıtı | DC01–DC108 ve gerekli devralınan testlerin gerçek sonuçları; belirlenimci yalıtım |
| F6-C-G18 | Regresyon/geri dönüş | DC108 ve M00/M08 eşlemesi; önceki API/özellik/DTMF regresyonu; yeni canlı ayar yok |
| F6-C-G19 | Bağımsız inceleme/devir | Gerçek kapsam, kanıt ve profil hazırlığı incelenir; F6-D noktası; dur |

## 9. Kanıt

`evidence/F6-C/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `RENDER_INVENTORY.json`, `STAGE_ORDER.md`, `RATE_OWNERSHIP.md`, `WSOLA_SPEC.md`, `BOUNDARY_CROSSFADE_SPEC.md`, `PAUSE_ACCOUNTING.md` (toplam hedef örnekleri), `DSP_FILTERS.md`, `LOUDNESS_LIMITER.md`, `CODEC_CAPABILITY.md`, `CODEC_LAB_PROTOCOL.md` (PESQ/POLQA benzeri metrikler ancak yerel ve lisanslıysa; aksi halde null), `BENCHMARK_PROTOCOL.md`, `TEST_MATRIX.json`. Laboratuvar sonuçları `data/F6/lab-report-*.json`.

## 10. Geri dönüş

`f6.enhanced_render=OFF`: F6-A/F6-B taban render. `f6.codec_lab` yalnız laboratuvar; canlı yola etkisi yok. Kod `git revert`.

## 11. Devir

- **F6-D:** chan_websocket aktarımı bu render çıktısını ve F6-B makbuz anlamını kullanır; kodek seçimi laboratuvar sonucuna ve ayrı karara bağlıdır.
- **F0-B:** referans musluğu tüm dönüşümler sonrası PCM'dir.
- **G4/G5:** geçiş/duraklama doğallığı, loudness, kodek etkisi yalnız gerçek dinleme ve uç ölçümüyle.

## 12. Başlatma komutu

```
F6-C paketini uygula: docs/execution/packages/W4/F6-C-birlestirme-dsp.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F6-B, F4-C ve F5-B kabulünü doğrula; mevcut fade/EQ/WSOLA yollarını envantere al.
f6.enhanced_render (varsayılan OFF) altında tek hız sahipli WSOLA, güvenli çapraz geçiş, toplam hedefli anlamsal duraklama,
de-esser/EQ/loudness ve tek son hız limiter'ını kur; kodek laboratuvarını canlı yoldan yalıtılmış tut, kurulum yapma.
DC01–DC108'i çalıştır, F6-C-G00…G19'u değerlendir, paket/F6-C dalında PR aç ve dur.
```
