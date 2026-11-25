# F6-D — İsteğe bağlı Asterisk chan_websocket aktarımı ve PBX entegrasyon sertleştirmesi

> **İsteğe bağlı paket.** AudioSocket tabanını değiştirmeden, Asterisk'in WebSocket medya kanalını (chan_websocket) sürüme ve modüle duyarlı yetenek keşfiyle, kimliği doğrulanmış tek kullanımlık bağlamayla, el sıkışmadan önce medya kabul etmeden, ayrı ikili/metin denetimiyle, yerel ve uzak akış kredisini ayırarak, F1-B duraklat/devam ve kapsamlı boşaltma eşlemesiyle ve yan etkiden önce onaylı tabana geri düşmeyle ekler. AMI/ARI etkileri yalnız M07 üzerinden; RTCP raporları doğru birim ve yönle. Gerçek PBX/SIP doğrulaması G5'tedir.

| Alan | Değer |
| --- | --- |
| Kimlik | F6-D |
| Dalga | W5 |
| Öncelik | P2 (isteğe bağlı) |
| Önkoşullar | W2_GATE, F6-B |
| Sonraki | — |
| Bayrak | `f6_pipeline_v2` + M03 profili `f6.transport` (`audiosocket` varsayılan / `websocket` isteğe bağlı; `OFF / SHADOW`) |
| Ortam | CPU, sahte WebSocket eşi, sahte AMI/ARI; gerçek Asterisk `@pytest.mark.pbx` ve G5 |
| Eski görevler | F6-T22 |
| Kaynak | Bundle `W5/Freya_2_0_F6_D_Agent_Implementation_Package.md`; [F6 spec](../../../stages/F6-rendering-transport/spec.md) |
| Durum | NOT_RUN (isteğe bağlı; uygulanmazsa `DEFERRED`) |

## 1. Amaç

AudioSocket basit ve çalışıyor; ancak uzak duraklatma/boşaltma gibi kontroller sunmuyor. Bazı Asterisk sürümlerindeki WebSocket medya kanalı bunları sunabilir. F6-D bu seçeneği **yalnız yetenek kanıtlıysa** ve yan etkiden önce seçilmek koşuluyla ekler; aksi halde AudioSocket aynen kalır. Üretim topolojisi kararı (ADR-X-01) bu paketin önkoşulu değildir ama etkinleştirmeyi etkiler.

## 2. Başlamadan önce

- [ ] W2_GATE ve F6-B gerçek kabul (yalnız `vertical_slice_ready` yetmez); onaylı değişiklik defteriyle soy; açıklanamayan kirli değişiklik yok.
- [ ] Mevcut aktarım, kontrol, DTMF, oynatma referansı, AMI/ARI ve medya yazıcısı envanterde: her birinin tek sahibi; ikinci gönderici veya originate yolu yok.
- [ ] F6-C yoksa da F6-B doğrudan bağımlılığı yeterli.
- [ ] Asterisk sürüm/modül/API yetenekleri yalnız **üst veriden** keşfedilir; sürüm numarası tek başına hazırlık değildir.

## 3. Kapsam

**Yapılacak:** Sözleşme eşlemesi; yetenek keşfi; aktarım seçimi; bağlama ve el sıkışma; medya biçimi ve AudioSocket tabanı; WebSocket lehçe adaptörü; uzak akış defteri; tempo ve gönderim; yumuşak duraklat/devam; kapsamlı boşaltma; yaşam döngüsü; geri düşme ve değiştirme; AMI/ARI; DTMF ve aktarım; güvenlik ve yapılandırma; RTP/RTCP izdüşümü; oynatma referansı; gözlem ve kaynak sınırları; entegrasyon ve benchmark protokolü.

**Yapılmayacak:** Gerçek SIP çağrısı veya PBX değişikliği; yan etkiden sonra sessiz aktarım değişimi; TLS doğrulamasını kapatma; LLM'in HANGUP/FLUSH komutu vermesi; MOS iddiası.

## 4. Dosyalar

```
backend/media_transport/websocket/
  capability.py  selection.py  binding.py  dialect.py  flow_ledger.py  pacing.py
  pause_resume.py  flush.py  lifecycle.py  fallback.py  security.py
backend/media_transport/pbx/
  ami_ari_bridge.py  dtmf_transfer.py  rtcp_projection.py
tests/media_transport/websocket/  tests/media_transport/pbx/
evidence/F6-D/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Yetenek ve seçim

| Durum | Sonuç |
| --- | --- |
| Fikstür sürümleri 20.15.0/20.16.0, 21.11, 22.6, 23.0 | Yalnız belgelenmiş dal tabanı; gerçek hazırlık değil |
| JSON kontrol için 20.18 / 22.8 / 23.2 ile daha eski sürüm | JSON yeteneği eski dalda varsayılmaz |
| Sürüm eşleşir ama modül yok | `UNSUPPORTED/UNKNOWN`; WebSocket etkinleşmez |
| Özel veya ayrıştırılamaz sürüm | `UNKNOWN`; sözlüksel tahmin yok |
| Modül var ama API'de websocket yok | Profil reddi; onaylı yan etki öncesi taban mümkün |
| Yalnız metin kontrol profili | Yalnız JSON alanları veya komutları varsayılmaz |
| Kurulu JSON profili ama sahte doğrulama | Kanıt kapsamı mock; yerel `NOT_RUN` |
| Beyan edilen PCM ama doğrulanmamış bayt sırası | Katı biçim HOLD |

Seçim **yan etkiden önce** yapılır; isteğe bağlı profil yoksa yetkili AudioSocket seçimi WebSocket'ten ayrıdır. TLS doğrulaması başarısızsa düz metne veya kimliksiz eşe otomatik düşüş yok. Olası kanal oluşturulduktan sonra kopma → uzlaştırma, kör originate veya geçiş yok.

### 5.2 Bağlama, biçim ve lehçe

- Doğrulanmış `MEDIA_START`'tan önce gelen medya kabul edilmez. Doğru bağlantı kimliğiyle yanlış eş, beklenen eşle yanlış kanal (arayan numarası eşleştirmesi yok), bağlantı kimliği tekrarı (tek kullanımlık), çelişen yinelenen `MEDIA_START`, yeniden bağlanmadan sonra eski dönem geri çağrısı reddedilir. Kötü niyetli `channel_variables` yetki, komut, günlük veya rota değiştiremez. Yön/otomatik yanıt uyuşmazlığı yan etkiden önce ret/HOLD.
- AudioSocket tabanı: tür `0x10`, 320 B → kesin 323 B başlık + PCM; bölünmüş TCP başlık/yük sınırlı birleştirici; birleşik iki mesaj sıralı ayrılır; tek PCM uzunluğu veya aşırı beyan tahsisten önce reddedilir; yanlış UUID bayt sayısı veya mesaj ortasında EOF kontrollü kapanış.
- WebSocket: ikili PCM'de AudioSocket/RTP başlığı yok; PCM rotasında beklenmeyen μ-law reddedilir; beklenmeyen ptime/çerçeve boyutu reddi; kesin çerçeve profilinde kısa ikili mesaj gönderilmez; terminal dolgu bir kez; ikili olarak gelen metin komutu asla komut olarak ayrıştırılmaz; yinelenen anahtarlı/aşırı iç içe/iki nesneli JSON reddedilir.

### 5.3 Akış, tempo, duraklatma ve boşaltma

- Yerel ve uzak bütçe ayrı: sınır 3 iken bir kuyrukta + bir seçili + bir rezerve → ek tahsisten önce geri basınç; küresel sınırda adil sınırlı bekleme; gönderimden önce uzak kredi bilinmiyorsa kapı kapalı; sürücü kuyruğu 900 fikstüründe sağlayıcı eşiğine kadar tamponlama yok; talepten önce XOFF → ikili teslim yok; talepten sonra XOFF → olası uçuşta izlenir, tekrar yok; yerel duraklatma etkinken XON → uzak kapı açılabilir, yerel kapalı kalır; eski dönem XON etkisiz; gecikmiş `GET_STATUS` sırasında yeni gönderimler sayılır (iyimser çıkarma yok); durum zaman aşımı → sınırlı HOLD/iptal (yoklama döngüsü yok).
- Tempo XON/devam sonrası yeniden çapalanır (yakalama patlaması yok). Talepten önce iptal → eski generation teslimi yok; talepten sonra fiziksel gönderimden önce iptal → doğrulanmış sonuçlanmaya kadar `IN_FLIGHT_POSSIBLE`.
- Duraklatma: uzak tarafta kuyruklu medya varken yumuşak duraklatma yerel imleci korur, uzak duraklatma kanıtı ayrı; `PAUSE_MEDIA` desteklenmiyorsa komut ve sahte uzak duraklatma yok; durumsuz duraklatma yazması → uzak durum bilinmiyor; eşleşen `PauseRef` ve doğrulanmış uzak durumla devam → aynı generation, yeniden gönderim yok; bayat jeton/süresi dolmuş son tarih → ret.
- Boşaltma: kuyruklu duraklatma komutu sırasında kesinleştirme → uzak beklemeden önce çit, eski komutlar sıralanır; özel eski bağlamada `FLUSH_MEDIA` → sıralı yazıcıdan sonra tek yetkili komut; yeni generation aynı kuyruğu paylaşıyorsa güvensiz kanal geneli boşaltma engellenir; AudioSocket uzak boşaltma → desteklenmiyor/bilinmiyor, yalnız yerel temizlik; `QUEUE_DRAINED` boşaltmadan önce gelirse boşaltma veya uç sessizliği kanıtı değildir; ilişkisiz geç tükenme yeni dönem/generation değiştirmez; yanlış ilişkili `MEDIA_MARK_PROCESSED` ilerleme güncellemez; boşaltma yazma zaman aşımı → UNKNOWN, aynı bağlantıda değiştirme engellenir.

### 5.4 Yaşam döngüsü, AMI/ARI, güvenlik ve RTCP

- Bağlantı terminal/temizlik sahibi; çağrı durumu ile medya durumu ayrı. Eski medya kanalı kapalı ve değiştirme yetkiliyse yeni kimliği doğrulanmış dönem, eski yük yok. Aynı dış kimlikle yeni oturumda onay/tampon/geri çağrı devralınmaz. Yeni bağlamadan sonra geç eski kapatma/boşaltma yalnız eski defteri etkiler. Kısmi yazma belirsizken EOF → tekrar yok. F5 yerel iş sürerken kapanış → M06 kirası terminale kadar. Paylaşılan köprüde iki çağrı → ilgisiz kapatma yok. Tekrarlı yeniden bağlanma hatası → sınırlı deneme, terminal kurtarma durumu.
- AMI kabul yanıtı ama yanıtlama olayı yok → yanıtlandı/commit değil. ARI 2xx dış medya oluşturuldu ama köprü yok → yalnız kaynak gözlendi. Yinelenen AMI olayları ve sırasız kapatma → kapsamlı idempotency, dirilme yok. Aynı `Linkedid` iki bacak → yalnız ona dayalı yetki/korelasyon yok. Yetkisiz originate veya keyfi araç URI'si → M07 engeller. Bilinmeyen aktarım etkisi ve yeniden deneme → uzlaştırma, ikinci aktarım yok. Tekrarlanan meşru aynı rakamlar korunur; yinelenen sağlayıcı olayından aynı rakam yalnız doğrulanmış kimlik/faza göre tekilleşir.
- Yanlış TLS ana makine adı/süresi dolmuş sertifika → hata kapalı (`verify=false` yok); aşırı kontrol/bağlantı seli → sınırlı ret; gizli bilgi, arayan numarası, SDP güvenli izin listesiyle; LLM'in ürettiği HANGUP/FLUSH_MEDIA güvenilir yetki olmadan engellenir.
- RTCP: doğrulanmış 8k RTP saatinde 80 jitter tiki = 10 ms (ham birimler korunur); G.722 16k örnek + 8k RTP saati → jitter dönüşümünde 8k; Opus RTP saati 48k; bilinmeyen saat/kayıp birimi → nedenle null türetilmiş değer; alınan/gönderilen ve iki SSRC dönemi ayrı; azalan/sıfırlanan işaretli birikimli kayıp → geçerli ham değer, sahte kayıp yüzdesi yok; PBX MES ve WS ping RTT "insan MOS" veya "RTP RTT" diye etiketlenmez.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F6-D.01 | Giriş ve soy | Gerçek çekirdek ve W2 kapıları, F6-B, yetkili soy | TD01–TD05 |
| F6-D.02 | Envanter ve sahiplik | Mevcut aktarım, kontrol, DTMF, oynatma referansı, AMI/ARI, medya yazıcısı | TD06–TD08 |
| F6-D.03 | Sözleşme eşlemesi | Özel izdüşümler → gerçek M01/F6-B/M02 başvuruları; null olabilir yetenekler | TD19–TD28 |
| F6-D.04 | Yetenek keşfi | Yalnız üst veriden sürüm/modül/API/komut yetenek haritası | TD09–TD17 |
| F6-D.05 | Aktarım seçimi | Yan etkiden önce taban veya uygun isteğe bağlı profil | TD18, TD69 |
| F6-D.06 | Bağlama ve el sıkışma | M02 sahibi; eş kimlik doğrulaması ve tek kullanımlık eşleme | TD19–TD28 |
| F6-D.07 | Medya biçimi ve AudioSocket | Taban çerçeveleme/ayrıştırıcı korunur; kesin biçim/ptime/geçerli sayı | TD29–TD38 |
| F6-D.08 | WebSocket lehçe adaptörü | Tek sınırlı okuma/yazma noktası; ayrı ikili ve metin | TD39–TD40 |
| F6-D.09 | Uzak akış defteri | F6-B'yi muhafazakâr krediyle genişlet; bilinmeyen işleme | TD41–TD50 |
| F6-D.10 | Tempo ve gönderim | Yazıcı, M02 atomik talep ve monoton gönderim bütçesi; patlama yok | TD51–TD54 |
| F6-D.11 | Yumuşak duraklat/devam | Eşleşen F1-B `PauseRef` → isteğe bağlı kanal geneli uzak duraklatma | TD55–TD59 |
| F6-D.12 | Kapsamlı boşaltma | Çit, eski yazıcıyı sonuçlandır, özel dönem bariyeri, boşaltmayı sırala | TD60–TD68 |
| F6-D.13 | Yaşam döngüsü ve kapanış | Bağlantı terminal/temizlik sahibi; çağrı ve medya durumu ayrı | TD73–TD78 |
| F6-D.14 | Geri düşme ve değiştirme | Yalnız yan etki öncesi onaylı taban; yan etki sonrası belirsizlik uzlaştırılır | TD69–TD72 |
| F6-D.15 | AMI/ARI | Mevcut M07 korumalı etki yolu; eylem/kanal/köprü bağlama | TD79–TD84 |
| F6-D.16 | DTMF ve aktarım | Ayrı DTMF kökeni ve mevcut insan devri; faza duyarlı | TD85–TD86 |
| F6-D.17 | Güvenlik ve yapılandırma | Eş izin listesi, TLS politikası, sınırlar, gizli başvurular, enjeksiyon | TD87–TD90 |
| F6-D.18 | RTP/RTCP izdüşümü | Doğrulanmış birim ve yönlerle kapsamlı raporlar; dönemler | TD91–TD97 |
| F6-D.19 | Oynatma referansı | F6-B gerçek talep edilmiş PCM musluğu, belirsizlik ve süreksizlikler | TD98–TD100 |
| F6-D.20 | Gözlem ve kaynak sınırları | M04 güvenli metrikler; bayt/çerçeve/bekleyen muhasebesi | TD88, TD103 |
| F6-D.21 | Entegrasyon ve benchmark | Sahte eşle gerçek kabul edilmiş kod; benchmark protokolü | TD101–TD104 |
| F6-D.22 | Belirlenimci doğrulama | TD01–TD106, önkoşul testleri ve uygulanabilir uyum | Tüm testler çalıştırılmış |
| F6-D.23 | Regresyon ve geri dönüş | Eski baytlar, davranış, kaynak farkı, yalıtım, geri dönüş | TD105–TD106 |
| F6-D.24 | Bağımsız kabul | F6-D-G00…G19 ve profil başı durum; kanıt; dur | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| TD01 | WG geçişi yok | Kaynak değişikliğinden önce HOLD; sahte kabul yok |
| TD02 | Yalnız M08 `vertical_slice_ready` | W2 kabul değil; HOLD |
| TD03 | F6-B kabulü yok veya hash uyuşmazlığı | Gerçek eksik kanıtla HOLD |
| TD04 | Yetkili W2 sonrası değişiklik defteri | Aynı HEAD gerekmeden soy doğrulanır |
| TD05 | Açıklanamayan kirli değişiklikler | HOLD; çalışma ağacı korunur |
| TD06 | F6-C yok ile var | F6-B doğrudan bağımlılığı yeterli; uyumlu isteğe bağlı devir |
| TD07 | Mevcut AMI/ARI ve medya yazıcısı envanteri | Her birinin tek sahibi; ikinci gönderici veya originate yolu yok |
| TD08 | Casus sağlayıcılarla OFF ve SHADOW | Yeni bağlantı veya dış etki yok; taban değişmez |
| TD09 | 20.15.0/20.16.0 fikstür sürümleri | Belgelenmiş taban ayrılır; gerçek hazırlık değil |
| TD10 | 21.11/22.6/23.0 örnekleri | Yalnız dala özgü taban |
| TD11 | 20.18/22.8/23.2 ile daha eski sürüm | Eski dalda JSON yeteneği varsayılmaz |
| TD12 | Sürüm eşleşir ama modül yok | UNSUPPORTED/UNKNOWN; websocket etkinleşmez |
| TD13 | Özel veya ayrıştırılamaz sürüm | UNKNOWN; sözlüksel tahmin yok |
| TD14 | Modül var ama API'de websocket/none yok | Profil reddi; onaylı yan etki öncesi taban mümkün |
| TD15 | Yalnız metin kontrol profili | Yalnız JSON alanları veya komut varsayımı yok |
| TD16 | Kurulu JSON profili ama sahte doğrulama | Kanıt kapsamı mock; yerel NOT_RUN kalır |
| TD17 | Beyan edilmiş PCM biçimi ama doğrulanmamış bayt sırası | Katı biçim HOLD |
| TD18 | İsteğe bağlı profil yan etki öncesi erişilemez | Yetkili AudioSocket seçimi WebSocket'ten ayrı |
| TD19 | Doğrulanmış MEDIA_START'tan önce medya gelir | Kabul yok; sınırlı ret |
| TD20 | Doğru bağlantı kimliğiyle yanlış eş | Ret; oturum bağlama yok |
| TD21 | Beklenen eş yanlış kanal | Ret; arayan numarası eşleştirmesi yok |
| TD22 | Bağlantı kimliği tekrarı | Tek kullanımlık bağlama ikinci bağlantıyı reddeder |
| TD23 | Aynı yinelenen MEDIA_START | Yalnız aynı doğrulanmış bağlamada idempotent |
| TD24 | Çelişen yinelenen MEDIA_START | Etkilenen bağlantı başarısız; üzerine yazma yok |
| TD25 | Yeniden bağlanmadan sonra eski akış dönemi geri çağrısı | Atılır; yeni oturum çözümü yok |
| TD26 | Eski metinde isteğe bağlı kanal kimliği yok | Güvenilir alternatif bağlama gerekir veya HOLD |
| TD27 | Kötü niyetli `channel_variables` | Yetki, komut, günlük veya rota değişikliği yok |
| TD28 | Yön/otomatik yanıt uyuşmazlığı | Yan etkiden önce ret veya HOLD |
| TD29 | AudioSocket tür 0x10 320 B fikstürü | Kesin 323 B başlık ve PCM baytları |
| TD30 | Bölünmüş TCP başlık ve yük | Sınırlı birleştirici kesin yeniden kurar |
| TD31 | Birleşik iki AudioSocket mesajı | Ayrı sıralı çerçeveler; kayıp yok |
| TD32 | Tek PCM uzunluğu veya aşırı beyan | Güvensiz tahsisten önce ret |
| TD33 | Yanlış UUID bayt sayısı ve mesaj ortasında EOF | Kontrollü kapanış; uydurma ses yok |
| TD34 | İkili WebSocket PCM fikstürü | AudioSocket/RTP başlığı yok; kesin yük |
| TD35 | PCM rotasında beklenmeyen μ-law | Ret; yeniden yorumlama yok |
| TD36 | Beklenmeyen ptime veya çerçeve boyutu | Ret veya yeni incelenmiş profil; sessiz zorlama yok |
| TD37 | Kısa katsız ikili mesaj | Kesin çerçeve profilinde gönderim yok |
| TD38 | Terminal dolgu ve geçerli sayı | Bir açık dolgu; ek anlamsal ses yok |
| TD39 | İkili olarak gelen metin komutu | Tespit edilebilirse geçersiz medya olarak ret; asla komut olarak ayrıştırılmaz |
| TD40 | Yinelenen anahtarlı, aşırı iç içe, iki nesneli JSON | Sınırlı girdi reddi |
| TD41 | Sınır 3'te bir kuyrukta + bir seçili + bir rezerve | Ek tahsisten önce geri basınç |
| TD42 | Oturumlar arası küresel sınır tükendi | Tahsis yok; adil sınırlı bekleme |
| TD43 | Gönderimden önce uzak kredi bilinmiyor | Kapı kapalı; çıkarılmış kullanılabilir kredi yok |
| TD44 | Sürücü kuyruğu 900 fikstürü | Sağlayıcı eşiğine kadar hedef tamponlama yok |
| TD45 | Talepten önce XOFF | İkili teslim yok |
| TD46 | Talepten sonra XOFF | Olası uçuşta izlenir; tekrar yok |
| TD47 | Yerel duraklatma etkinken XON | Uzak kapı açılabilir; yerel kapalı kalır |
| TD48 | Eski dönem bayat XON | Etki yok |
| TD49 | Yeni gönderimler sürerken gecikmiş GET_STATUS | Sonraki tüm talepler sayılır; iyimser çıkarma yok |
| TD50 | Durum zaman aşımı | Sınırlı HOLD/iptal; yoklama döngüsü yok |
| TD51 | Yazıcı bloklu ve kontrol niyeti kuyrukta | Son tarih ve belirsizlik; anında uzak etki iddiası yok |
| TD52 | XON veya devam sonrası tempo | Yeniden çapalama; yakalama patlaması yok |
| TD53 | Gönderim talebinden önce iptal | Eski generation teslimi yok |
| TD54 | Talepten sonra fiziksel gönderimden önce iptal | Doğrulanmış sonuçlanmaya kadar IN_FLIGHT_POSSIBLE |
| TD55 | Uzak taraf kuyruklu medya tutarken yumuşak duraklatma | Yerel imleç korunur; uzak duraklatma kanıtı ayrı |
| TD56 | PAUSE_MEDIA desteklenmeyen profil | Komut yok; sahte uzak duraklatma yok |
| TD57 | Duraklatma yazması durumsuz tamamlanır | Uzak durum bilinmiyor; duyulur iddiası yok |
| TD58 | Eşleşen PauseRef ve doğrulanmış uzak durumla devam | Aynı generation sürer; yeniden gönderim yok |
| TD59 | Bayat jeton veya süresi dolmuş son tarihle devam | Ret; yeniden açma yok |
| TD60 | Kuyruklu duraklatma komutu sırasında kesinleştirme | Uzak beklemeden önce çit; eski komutlar sıralanır |
| TD61 | Özel eski bağlamada FLUSH_MEDIA istenir | Sıralı yazıcıdan sonra yalnız bir yetkili komut |
| TD62 | Yeni generation kuyruğu paylaşırken boşaltma istenir | Güvensiz kanal geneli boşaltma engellenir |
| TD63 | AudioSocket uzak boşaltma isteği | Desteklenmiyor/bilinmiyor; yalnız yerel temizlik |
| TD64 | Geçiş profilinde boşaltma veya duraklatma | Desteklenmeyen komut yayımlanmaz |
| TD65 | QUEUE_DRAINED boşaltmadan önce gelir | Boşaltma veya uç sessizliği kanıtı değil |
| TD66 | Yinelenen/ilişkisiz geç tükenme | Yeni dönem veya generation değişikliği yok |
| TD67 | Yanlış ilişkili MEDIA_MARK_PROCESSED | Etkin niyet için ilerleme güncellemesi yok |
| TD68 | Boşaltma yazma zaman aşımı veya belirsiz durum | UNKNOWN; aynı bağlantıda değiştirme engellenir |
| TD69 | Herhangi bir dış etkiden önce yetenek eksik | Yalnız politika onaylı taban |
| TD70 | TLS kimlik doğrulaması başarısız | Otomatik düz metin veya kimliksiz düşüş yok |
| TD71 | Olası kanal oluşturulduktan sonra kopma | Uzlaştırma; kör originate veya geçiş yok |
| TD72 | Eski medya kanalı kapalı biliniyor ve değiştirme yetkili | Yeni kimliği doğrulanmış dönem; eski yük yok |
| TD73 | Aynı dış kimlikle yeni oturumda yeniden bağlanma | Devralınan onay, tampon veya geri çağrı yok |
| TD74 | Yeni bağlamadan sonra geç eski kapatma veya boşaltma | Yalnız eski defter etkilenir |
| TD75 | Kısmi yazma belirsizken EOF | Tekrar yok; uçuşta takibi korunur |
| TD76 | F5 yerel iş sürerken kapanış | M06 kirası gerçek terminal/karantinaya kadar |
| TD77 | İki çağrılı paylaşılan köprü | İlgisiz kapatma veya temizlik yok |
| TD78 | Tekrarlı yeniden bağlanma hatası | Sınırlı deneme; terminal kurtarma durumu |
| TD79 | Yanıtlama olayı olmayan AMI kabul yanıtı | Yanıtlandı veya commit edilmiş çağrı başarısı değil |
| TD80 | ARI 2xx dış medya oluşturuldu, köprü yok | Yalnız kaynak gözlendi; köprü hazır iddiası yok |
| TD81 | Yinelenen AMI olayları ve sırasız kapatma | Kapsamlı idempotency; durum dirilmesi yok |
| TD82 | İki bacak `Linkedid` paylaşır | Yalnız `Linkedid` ile bacaklar arası yetki/korelasyon yok |
| TD83 | Yetkisiz originate veya keyfi araç URI'si | M07 üzerinden engellenir |
| TD84 | Bilinmeyen aktarım etkisi ve yeniden deneme | Uzlaştırma; ikinci aktarım yok |
| TD85 | Tekrarlanan meşru aynı DTMF rakamları | İkisi de korunur; yalnız değere dayalı tekilleştirme yok |
| TD86 | Yinelenen sağlayıcı olayından aynı rakam | Yalnız doğrulanmış kimlik/faza göre tekilleştirme |
| TD87 | Yanlış TLS ana makine adı, süresi dolmuş sertifika fikstürü | Hata kapalı; `verify=false` yok |
| TD88 | Aşırı büyük kontrol veya bağlantı seli | Sınırlı limitler; güvenli ret |
| TD89 | Sağlayıcı yükünde gizli bilgi, arayan numarası ve SDP | Güvenli izin listesi; ham günlük yok |
| TD90 | LLM tarafından üretilmiş HANGUP veya FLUSH_MEDIA | Güvenilir yetki yok ⇒ engellenir |
| TD91 | Doğrulanmış 8k RTP saatinde 80 jitter tiki | 10 ms; ham birimler korunur |
| TD92 | G.722 örnekleme hızı 16k ve RTP saati 8k | Jitter dönüşümü için 8k kullanılır |
| TD93 | Opus RTP saati 48k | PCM giriş hızından bağımsız |
| TD94 | Bilinmeyen saat veya kayıp birimi | Nedenle null türetilmiş değer |
| TD95 | Alınan ile gönderilen RTCP ve iki SSRC dönemi | Ayrı yönler, gözlemciler, dönemler |
| TD96 | İşaretli birikimli kayıp azalır veya sıfırlanır | Geçerli ham değer korunur; sahte kayıp yüzdesi yok |
| TD97 | PBX MES ve WS ping RTT | İnsan MOS veya RTP RTT diye etiketlenmez |
| TD98 | F6-C sonrası son PCM ve referans musluğu | Kesin gerçek talep edilmiş baytlar ve ofset |
| TD99 | Gönderilmemiş silinmiş PCM ve PBX üretimi sessizlik | Referans uydurulmaz |
| TD100 | Bilinmeyen teslim ve yeni dönem boşluğu | Belirsizlik kaydedilir; dönemler arası birleştirme yok |
| TD101 | Sahte WebSocket eşiyle tam gerçek F6-B/M02 adaptörü | Kesin çerçeve, tek yazıcı, kapsamlı makbuz |
| TD102 | Alternatif OFF iken tam AudioSocket taban fikstürü | Özgün baytlar/olaylar/davranış korunur |
| TD103 | Biri XOFF biri etkin iki eşzamanlı oturum | Oturumlar arası geri basınç veya boşaltma yok |
| TD104 | Konuşma iptali sırasında M07 commit edilmiş makbuz | Makbuz kalıcı; bayat ses engellenir |
| TD105 | Yerel PBX/gerçek SIP çalıştırılmadı | Durum NOT_RUN/HOLD; sahte yetenek kanıtı yok |
| TD106 | Yalıtılmış durumda kanıt bildirimi ve geri dönüş tatbikatı | Gerçek hash'ler ve güvenli taban seçimi |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F6-D-G00 | Ön kontrol | Gerçek CG00–CG11, WG00–WG11, F6-B kabul, kaynak soyu ve onay |
| F6-D-G01 | Tek sahip | Tek aktarım yazıcısı, F6-B kuyruğu, mevcut AMI/ARI ve M07 otoritesi; envanter hesaplanmış |
| F6-D-G02 | Sözleşmeler | M01/M02 kapsamlı sözleşmeler, kesin kimlikler, değiştirilemez biçimler ve bilinmeyen işleme |
| F6-D-G03 | Yetenek | Dala duyarlı yetenek kanıtı; sahte/yerel ayrımı; sabit M03 profili |
| F6-D-G04 | Seçim | Güvenli seçim ve onaylı yan etki öncesi geri düşme; sessiz düşürme veya yinelenen çağrı yok |
| F6-D-G05 | Bağlama | Güvenilir eş ve tek kullanımlık bağlama; medyadan önce el sıkışma; doğru yön/dönem |
| F6-D-G06 | Biçim | AudioSocket taban bayt uyumu ve doğrulanmış fikstür WebSocket biçim doğrulaması |
| F6-D-G07 | Lehçe | Sınırlı ayrıştırıcı/lehçe; tek ikili/metin ayrımı; desteklenmeyen komut yok |
| F6-D-G08 | Akış | Yerel/uzak bütçe ayrımı; XOFF/XON tazeliği; muhafazakâr bilinmeyen işleme |
| F6-D-G09 | Gönderim | Atomik gönderim, tek yazıcı, tempo; bayat/tekrar yok; kesin imleç |
| F6-D-G10 | Duraklatma | F1-B yumuşak duraklatma, eşleşen aynı generation devamı; son tarih uzatması yok |
| F6-D-G11 | Boşaltma | Kapsamlı kanal geneli boşaltma bariyeri; sahte ACK/duyulur iddiası yok; belirsizlik kayıtlı |
| F6-D-G12 | Yaşam döngüsü | Sahipli yaşam döngüsü, sınırlı temizlik/karantina, yeni dönem ve eski medya yok |
| F6-D-G13 | PBX etkileri | M07 AMI/ARI etki otoritesi, doğrulanmış sağlayıcı bilgileri, DTMF ve aktarım uyumu |
| F6-D-G14 | Güvenlik | Eş güvenliği, TLS hata kapalı, limitler, gizli/ham veri sızıntısı yok |
| F6-D-G15 | RTCP ve referans | Doğru RTCP kaynağı/yönü/birimleri ve referans kapsamı/bilinmeyenler |
| F6-D-G16 | Entegrasyon | Sahte eşle gerçek entegre F6-B/M02/M07 yolu; OFF/SHADOW sıfır ek etki |
| F6-D-G17 | Test kanıtı | Her zorunlu TD testi beklenen sonuç ve izle gerçekten çalıştırılmış; uydurma test yok |
| F6-D-G18 | Regresyon | Mevcut önkoşul/regresyon testleri, kaynak farkı, geri dönüş ve ertelenmiş benchmark protokolü |
| F6-D-G19 | Devir | Bağımsız inceleme; dürüst profil başı hazırlık; kanıt ve devir; otomatik başlatma yok |

## 9. Kanıt

`evidence/F6-D/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `TRANSPORT_INVENTORY.json`, `CAPABILITY_MAP.json` (yalnız üst veri; yerel doğrulama NOT_RUN), `SELECTION_POLICY.md`, `BINDING_HANDSHAKE.md`, `FLOW_LEDGER_SPEC.md`, `PAUSE_FLUSH_SPEC.md`, `PBX_EFFECTS.md`, `RTCP_PROJECTION.md`, `BENCHMARK_PROTOCOL.md` (gerçek PBX/SIP testleri G5'te), `TEST_MATRIX.json`.

## 10. Geri dönüş

`f6.transport=audiosocket`: taban AudioSocket aynen. WebSocket profili yalnız yeni çağrılarda ve yan etkiden önce seçildiği için geri dönüş etkin çağrıları bozmaz. Kod `git revert`.

## 11. Devir

- **G5:** gerçek Asterisk sürümüyle yetenek doğrulaması, SIP/PBX kabul testleri, gerçek uç duyulur kesme ölçümü.
- **Topoloji ([ADR-X-01](../../../01-architecture/adr/ADR-X-01-asterisk-dagitim.md), kabul edildi):** pilot aynı makinede AudioSocket ile yapılır; üretimde Asterisk ayrı sunucuda olacağından TLS destekli WebSocket medya kanalı, şifreli tünel üzerinden AudioSocket'e alternatif olarak değerlendirilir. F6-D'nin üretimde etkinleştirilmesi ayrı yeterlilik ister.

## 12. Başlatma komutu

```
F6-D paketini (isteğe bağlı) uygula: docs/execution/packages/W5/F6-D-chan-websocket.md.
Kuralları CLAUDE.md'den oku; W2_GATE ve F6-B kabulünü doğrula; Asterisk yeteneklerini yalnız üst veriden keşfet.
AudioSocket tabanını koruyarak f6.transport altında kimliği doğrulanmış WebSocket medya aktarımını,
yan etki öncesi seçim/geri düşme, yerel-uzak akış defteri, kapsamlı duraklatma/boşaltma ve M07 korumalı AMI/ARI ile kur.
TD01–TD106'yı çalıştır, F6-D-G00…G19'u değerlendir, paket/F6-D dalında PR aç ve dur.
```
