# F6-B — Sınırlı oynatma kuyruğu, gönderim çiti ve makbuzlar

> F6-A'nın tek kuyruğunu, kesin kapasite bütçeleri, atomik rezervasyon, iptal edilebilir geri basınç, "hiç talep edilmemiş sonraki çerçeve" imleci, M02 son gönderim çiti, F1-B duraklat/devam/kesme bağlantısı, uçuştaki çerçeve muhasebesi, kapsamlı boşaltma makbuzları ve F0-B için sınırlı oynatma referansı (AEC girdisi) ile genişletir. İkinci yazıcı, ikinci kuyruk veya uydurma protokol yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F6-B |
| Dalga | W3 |
| Öncelik | P0 |
| Önkoşullar | W2_GATE, F6-A, F1-B |
| Sonraki | F0-B, F6-C, F6-D |
| Bayrak | `f6_pipeline_v2` (katı kipte etkin) |
| Ortam | CPU (sahte saat, kaydeden aktarım, sahte istemci onayı) |
| Eski görevler | F6-T17, F6-T18, F6-T19, F6-T21, F6-T23, F6-T24 |
| Kaynak | Bundle `W3/Freya_2_0_F6_B_Agent_Implementation_Package.md`; [F6 spec](../../../stages/F6-rendering-transport/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Söz kesmenin duyulur biçimde hızlı olması için sunucuda bekleyen ses **az ve sınırlı** olmalı; devam ederken tek çerçeve bile tekrar edilmemeli; "boşaltıldı" iddiası yalnızca gerçekten gözlenen kapsamda yapılmalı. Ayrıca F0-B'deki yankı giderme (AEC) gönderilmiş sesin güvenilir bir referansına ihtiyaç duyar. F6-B bunları tek kuyruk/tek yazıcı üzerinde kurar.

## 2. Başlamadan önce

- [ ] W2_GATE, F6-A ve F1-B kabul edilmiş; onay; onaysız kaynak sapması yok.
- [ ] Tüm oynatma/kuyruk/aktarım/boşaltma/referans yolları M00 kimlikleriyle envanterde; gerçek rotalar sınıflanmış.
- [ ] Mevcut AMI/ARI aktarım davranışı (eski F6-T24) yalnızca **korunur** ve envantere girer; gerçek aktarım doğrulaması G5'tedir.

## 3. Kapsam

**Yapılacak:** Tek otorite ve kilit sırası; sözleşme bağlama; akış başı ve küresel bütçeler; atomik rezervasyon; sıralı kuyruk; sınırlı geri basınç; imleç; M02 son gönderim çiti; F1-B duraklat/tut/devam/kesme; uçuştaki çerçeve takibi; kapsamlı boşaltma makbuzları; web/AudioSocket adaptör uzantıları; F0-B oynatma referansı; yaşam döngüsü ve karantina; M04/M07; entegrasyon; benchmark protokolü (ertelenmiş gerçek durum).

**Yapılmayacak:** AEC algoritması (F0-B); birleştirme/WSOLA/loudness (F6-C); chan_websocket (F6-D); uzak boşaltma protokolü uydurma; gerçek PBX/uç ölçümü.

## 4. Dosyalar

```
backend/media_transport/
  capacity.py  reservations.py  playback_queue.py  backpressure.py  cursor.py
  submission_fence.py  pause_resume.py  purge.py  in_flight.py  flush_receipts.py
  playback_reference.py  cleanup.py
tests/media_transport/playback/
evidence/F6-B/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Kapasite

| Profil | Yuva | Örnek / yuva | Bayt / yuva | Örnek sınır (fikstür) |
| --- | --- | --- | --- | --- |
| Telefon (8 kHz PCM16) | 20 ms | 160 | 320 | 3 yuva = 480 örnek / 960 B / 60 ms |
| Web (16 kHz PCM16) | 20 ms | 320 | 640 | eşdeğer süre sınırı |

Fikstür sınırları test içindir; üretim değeri M03 profilinden gelir ve G4'te ölçülür. Akış başı ve **küresel** bayt/öğe sınırı birlikte uygulanır. Render çalışma alanı ve referans saklama da bütçeye dahildir. Kopyalamadan önce sınır kontrolü; rezervasyon atomik; gerçek boyut tahminden küçükse rezervasyon gerçek sahiplikle değiştirilir, büyükse güvenle yeniden rezerve veya iptal. Paylaşılan değiştirilemez görünüm sahip başına bir kez sayılır.

### 5.2 İmleç ve gönderim çiti

- **İmleç = hiç talep edilmemiş sonraki sıra.** Seçilmiş-ama-talep-edilmemiş, talep edilmiş, tamamlanmış ve bilinmeyen ayrıdır. Geç onay (ACK) imleci geri sarmaz; bilinmeyen kısmi yazma geri sarma veya kör yeniden gönderim üretmez; yinelenen tamamlanma tam bir kez bırakır.
- M02 son gönderim sıralaması iki yarış sırasında da doğrudur: çekişten önce/seçimden sonra/tempo uyanmasından sonra iptal → sıfır eski talep; talep önce kazanırsa uçuşta olabilir, çitten sonra yeni talep yok, geri çağırma yok. Asenkron aktarım talepten sonra başlatırsa yalnızca "uçuşta olabilir". Otorite altında `await` yok; kontrol ve yazıcı kilitlerinde kilitlenme yok.

### 5.3 Duraklat, devam, kesme

- F1-B yumuşak duraklatması yerel kapıyı hemen kapatır (iptal değil); bekleyen seçili çerçeve ve imleç tutulur; uçuştaki tamamlanma yalnızca eski kaydı kapatır. Duraklatmada yeni F5 çıktısı ve dolu kapasite → sınırlı geri basınç/iptal; sessiz atıp devam yok.
- Devam: aynı generation/plan/jeton, sonraki gönderilmemiş çerçeveden; talep edilmiş sıralar yeniden gönderilmez; yeniden render/normalizasyon yok; bayat dönem/deneme reddi; son tarihte veya sonra yeniden açma yok; gecikmiş hedeflerde yeniden çapalama, yakalama patlaması yok; tükenmiş/imleci belirsiz hedefte hayali devam yok.
- Kesin kesme: iki gönderilmemiş + bir uçuştaki çerçevede tam iki silinir, hedef çitlenir, uçuştaki sahip tutulur; yinelenen kesme/boşaltma tek mantıksal etki; kesme ile devam yarışında M02 kazananı geçerli; yeni giriş/DTMF ve yeni tur geçerli kalır.

### 5.4 Boşaltma makbuzları ve aktarım

| Durum | Olay |
| --- | --- |
| Yerel temizlik doğrulandı, uzak desteklenmiyor | `SERVER FLUSHED` kesin sayılarla; uzak desteklenmiyor, uç bilinmiyor |
| Desteklenen sahte istemci onayı komutla eşleşir | Yalnızca `CLIENT` gözlenen makbuz; uç iddiası yok |
| Yanlış generation, komut kimliği veya bayat uzak onay | Yeni kontrolde değişiklik veya sahte makbuz yok |
| Son tarihe kadar uzak onay yok | `UNKNOWN`/zaman aşımı; sahte `FLUSHED` yok |
| İdempotent olmayan veya kapsamsız uzak temizleme | Güvensiz yeniden deneme/boşaltma bastırılır; yeni generation güvende |
| Olası etkiden sonra sağlayıcı hatası | `UNKNOWN`/uzlaştırma; iptal asla geri alınmaz |

AudioSocket: `10 01 40` + 320 B PCM aynen; doğrulanmış uzak boşaltma yoksa uydurma komut/bayt yok; DTMF/sonlandırma yolu korunur. Web: iç 640 B PCM; dış sözleşme ve tempo sahibi korunur.

### 5.5 Oynatma referansı (F0-B için)

Yalnızca **talep edilmiş** son DSP/PCM çerçeveler referans olur (kesin bayt, üst veri, `SERVER` kapsam, geçerli sayı); yalnız kuyrukta kalmış veya talepten önce silinmiş çerçeveler referans değildir. Duraklatma/kesmeden sonra sınırlı geçmiş referans politikaya göre tutulur; sahte sessizlik yok. Yavaş okuyucu ve tahliye: açık boşluk/bilinmiyor, ayrı bütçe, oynatma etkilenmez. Oturumlar arası veya bayat dönem sorgusu, eksik saat eşlemesi → ret veya erişilemez; uydurma hizalama yok. AEC algoritması burada yoktur.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F6-B.01 | Ön kontrol | Çekirdek/W2/F6-A/F1-B kabulü ve açık onay | `F6_B_PREFLIGHT`; PB01–PB04 |
| F6-B.02 | Envanter | Tüm oynatma/kuyruk/aktarım/boşaltma/referans yolları ve M00 kimlikleri | `PLAYBACK_INVENTORY`; PB05–PB06 |
| F6-B.03 | Tek otorite | Kilit sırası, geçiş ve eski uyum; ikinci yazıcı yok | `CHANGE_SCOPE`, `PLAYBACK_DECISIONS`; PB07–PB08 |
| F6-B.04 | Sözleşme bağlama | M01/M02/M03/M04/F1-B/F6-A sözleşmeleri ve güvenli özel kayıtlar; şema değişikliği yok | `CONTRACT_MAPPING`; PB09–PB12 |
| F6-B.05 | Kapasite | Doğrulanmış sabit akış başı ve küresel bütçe boyutları, sahip defteri; çalışma alanı/referans dahil | `CAPACITY_SPEC`; PB13–PB16 |
| F6-B.06 | Rezervasyon | Atomik rezervasyon, gerçek sahiplik devri, kopyadan önce sınır | `RESERVATION_SPEC`; PB17–PB22 |
| F6-B.07 | Sıralı kuyruk | Tek kuyruk; sıra/örnek bütünlüğü; boşluk/yeniden sıralama yok | `QUEUE_CURSOR_SPEC`; PB23–PB27 |
| F6-B.08 | Geri basınç | Sınırlı iptal edilebilir geri basınç, yüksek/alçak su seviyesi, zaman aşımı; kilit altında `await` yok | `BACKPRESSURE_SPEC`; PB28–PB34 |
| F6-B.09 | İmleç | Seçilmiş-gönderilmemiş / talep edilmiş / tamamlanmış-bilinmeyen; ACK'e dayalı geri sarma yok | PB35–PB39 |
| F6-B.10 | Gönderim çiti | M02 son gönderim sıralaması ve tek yazıcı; iki yarış sırası | `SUBMISSION_FENCE_SPEC`; PB40–PB45 |
| F6-B.11 | Duraklatma | F1-B yumuşak duraklatma ve sınırlı tutma; giriş korunur, yıkıcı boşaltma yok | `PAUSE_RESUME_SPEC`; PB46–PB49 |
| F6-B.12 | Devam | Aynı generation, kesin gönderilmemiş imleç, tempo yeniden çapalama; yakalama veya yeniden render yok | PB50–PB55 |
| F6-B.13 | Kesin kesme | Kesme, yerel temizlik, bekleyenleri uyandırma; geri alınamaz hedef çiti | `PURGE_ACCOUNTING_SPEC`; PB56–PB59 |
| F6-B.14 | Uçuştaki takip | Tam bir kez yerel tamamlanma muhasebesi; belirsiz teslimde tekrar yok | `IN_FLIGHT_SPEC`; PB60–PB64 |
| F6-B.15 | Boşaltma makbuzları | Hedef boşaltma niyetleri gerçek yeteneklere ve kapsamlı makbuza bağlı | `FLUSH_RECEIPT_SPEC`; PB65–PB71 |
| F6-B.16 | Aktarım adaptörleri | Mevcut web/AudioSocket uzantıları; uydurma protokol yok | `TRANSPORT_CAPABILITY_MATRIX`; PB72–PB74 |
| F6-B.17 | Oynatma referansı | F0-B için sınırlı render/talep sonrası referans sağlayıcı; AEC algoritması yok | `PLAYBACK_REFERENCE_SPEC`; PB75–PB79 |
| F6-B.18 | Yaşam döngüsü | M02/M06 ile güvenli hata, karantina ve temizlik; erken kira bırakma yok | `CLEANUP_SPEC`; PB80–PB82 |
| F6-B.19 | M04/M07 | Güvenli metrikler; gizlilik/işlem sınırları; ham medya günlüğü yok | `TELEMETRY_MAPPING`; PB83–PB84 |
| F6-B.20 | Entegrasyon | Gerçek F1-B/F5-A/F6-A/M02/M06 ve F0-B test tüketicisi; ikinci otorite yok | `LEGACY_COMPATIBILITY_MATRIX`; PB85–PB86 |
| F6-B.21 | Testler | PB01–PB88 ve gerekli mevcut regresyonlar (M08) | `TEST_MATRIX`, `TEST_RESULTS` |
| F6-B.22 | Bütünlük ve geri dönüş | Özellik/atlama ve bütünlük incelemesi, geri dönüş provası | PB87–PB88 |
| F6-B.23 | Benchmark protokolü | Performans/uç benchmark protokolü; gerçek durum ertelenmiş | `PLAYBACK_BENCHMARK_PLAN` |
| F6-B.24 | Kabul ve devir | Bağımsız F6-B-G00…G19 incelemesi; devir; dur | `ACCEPTANCE_MATRIX`, `DOWNSTREAM_HANDOFF` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| PB01 | Gerçek W2 kanıtı yok | HOLD; kaynak düzenleme yok |
| PB02 | W2 PASS ama F1-B kabul edilmemiş | HOLD; kaynak düzenleme yok |
| PB03 | Kabul edilmiş W2 + yetkili F1-B değişiklikleri | Soy doğrulanır; yanlış bayat reddi yok |
| PB04 | Onaysız kaynak sapması veya eksik onay | Düzenlemeden önce HOLD |
| PB05 | Tüm güncel oynatma tüketicilerinin sayımı | Özellik kimlikleri, sahip, kapsam ve atlama sınıflaması tam |
| PB06 | Mevcut web/telefon/deney kontrolleri | Gerçek özellikler korunur; uydurma yol yok |
| PB07 | Yalıtılmış ortamda yeni modüllerin içe aktarılması | Model, soket, işçi, DB veya ağ yan etkisi yok |
| PB08 | Aynı akış için ikinci yazıcı/kuyruk denemesi | Yinelenen sahiplik reddedilir |
| PB09 | Gerçek M01 çerçeve/oynatma sözleşmesi | Mevcut tür ve doğrulama; alternatif şema yok |
| PB10 | Gerçek M02 `PauseRef` ve F1-B kararı | Geçerli kapsam eşlenir; uydurma jeton yok |
| PB11 | Aynı yerel sayaçlı iki oturum | Ayrı kimlikler; çapraz kontrol yok |
| PB12 | Bayat plan revizyonu veya akış dönemi | Kapasite veya yan etki olmadan ret |
| PB13 | Telefon 3 yuva fikstürü | Kesin 480 örnek/960 B/60 ms sınırı |
| PB14 | Web profili eşdeğer sınır | Yuva başına doğru 320 örnek/640 B; telefon birimi yok |
| PB15 | Geçersiz negatif/sıfır/sınırsız bütçe, geçersiz su seviyeleri | Katı yapılandırma reddedilir; son kabul edilen korunur |
| PB16 | İki oturumda toplam sınır | Akış başı yer kalsa da küresel bayt/öğe sınırı tutar |
| PB17 | Render çalışma alanı sınırını aşan büyük ham parça | Kontrolsüz tahsisten önce açık nedenle ret |
| PB18 | Kapasite rezervi sonra kopyadan önce iptal | Rezervasyon bir kez bırakılır; yük kabul edilmez |
| PB19 | Son yuva için yarışan iki üretici | Bir rezervasyon kazanır; aşırı taahhüt yok |
| PB20 | Gerçek boyut tahminden küçük | Rezervasyon atomik olarak gerçek sahiplikle değişir |
| PB21 | Gerçek çıktı tahmini aşar | Güvenle yeniden rezerve veya iptal; gizli kısmi taşma yok |
| PB22 | Paylaşılan değiştirilemez görünüm ve referans saklama | Fiziksel baytlar sahip başına bir kez; referans saklama hesaplanır |
| PB23 | Sıralı ardışık çerçeveler | Kesin sıra/örnek düzeni; tek yazıcı |
| PB24 | Yinelenen çerçeve kimliği | İkinci kuyruk girdisi veya yazma yok |
| PB25 | Eksik ortadaki sıra veya ofset örtüşmesi | Açık ret/iptal; sessiz delik yok |
| PB26 | F6-A terminal dolgusu | Geçerli sayı ayrı; parça sınırında ek dolgu yok |
| PB27 | Tempo bekleyen seçili çerçeve | Sahipli gönderilmemiş kalır; sınıra sayılır |
| PB28 | Kuyruk yüksek su seviyesine ulaşır | Üretici sınırlı bekleyenle bloklanır/ertelenir |
| PB29 | Alçak su seviyesinin altında tamamlanma | Uygun bekleyen bilgilendirilir; sert sınır yeniden kontrol |
| PB30 | Kuyruk dolu ve iptal | Kontrol kazanır; bekleyenler uyanır; kilitlenme yok |
| PB31 | Kapasite beklerken zaman aşımı | Açık zaman aşımı/iptal; sızan rezervasyon yok |
| PB32 | Yinelenen uyandırma veya sahte bildirim | Yeniden kontrol; yinelenen ekleme yok |
| PB33 | Sınırdan fazla bekleyen | Sınırlı ret; görev patlaması yok |
| PB34 | Yarışan uygun oturumlar, sürekli ön plan yükü | Belgeli adillik; fikstürde sınırsız açlık yok |
| PB35 | 3, 4 kuyruktayken 2 talep edilir | İmleç sonraki hiç talep edilmemiş = 3; tamamlanma bağımsız |
| PB36 | 1 için geç ACK | İmleç değişmez; tekrar yok |
| PB37 | Seçilmiş ama talep edilmemiş 3 | İmleç 3 kalır; sağlamsa devam edilebilir |
| PB38 | 2'nin bilinmeyen kısmi yazması | Bilinmeyen teslim; geri sarma veya kör yeniden gönderim yok |
| PB39 | Yinelenen geri çağrılı kanıtlanmış tamamlanma | Tam bir kez bırakma; kararlı imleç |
| PB40 | Çekişten önce iptal | Bayat talep veya alıcı gönderimi yok |
| PB41 | Seçimden sonra tempo uyanmasından önce iptal | Yeniden kontrol; bayat gönderim engellenir |
| PB42 | Tempo uyanmasından sonra atomik talepten önce iptal | İptal kazanırsa alıcı sıfır eski talep alır |
| PB43 | Talep iptalden önce kazanır | Uçuşta olabilir; çitten sonra yeni talep yok; geri çağırma yok |
| PB44 | Asenkron aktarım talepten sonra başlatmayı erteler | Uçuşta olabilir; daha güçlü garanti yok |
| PB45 | Eşzamanlı kontrol ve yazıcı kilit edinimi | Otorite altında `await` yok; kilitlenme yok; tek sahip |
| PB46 | Canlı generation'da F1-B yumuşak duraklatması | Yerel kapı hemen kapanır; iptal yok |
| PB47 | Seçili çerçeve beklerken duraklatma | Çerçeve ve imleç tutulur; yeni talep yok |
| PB48 | Uçuştaki tamamlanmayla duraklatma | Yalnız eski kayıt tamamlanır; ek gönderim yok |
| PB49 | Duraklatılmışken yeni F5 çıktısı ve dolu sınır | Sınırlı geri basınç/iptal; sessiz at-devam et yok |
| PB50 | Son tarihten önce açık yanlış kesme | Aynı generation/plan/jeton; sonraki gönderilmemişten başla |
| PB51 | Gönderilmiş çerçevelerden sonra devam | Talep edilmiş sıralar yeniden gönderilmez; yeniden render/normalizasyon yok |
| PB52 | Bayat duraklatma dönemi veya uyuşmayan deneme | Etkin kapı değişmeden ret |
| PB53 | Kabul edilen son tarihte/sonra devam | Yeniden açma yok; F1-B zaman aşımı anlamı korunur |
| PB54 | Sahte saat gecikmiş hedeflerle devam eder | Yeniden çapalama; yakalama patlaması yok; boşluk politikası korunur |
| PB55 | Duraklatmada hedef tamamen tükendi veya imleç belirsiz | Hayali devam veya tekrar olmadan çözülür; gerekirse iptal |
| PB56 | İki gönderilmemiş ve bir uçuştaki ile kesin kesme | Tam ikisi silinir; hedef çitlenir; uçuştaki sahip tutulur |
| PB57 | Yinelenen kesme/boşaltma niyeti | Tek mantıksal silme/niyet; idempotent sonuç |
| PB58 | Kesme ile devam yarışı (iki sıra) | Gerçek M02 kazananı; dirilme veya yeni eski talep yok |
| PB59 | Eski çıkış kesmesinden sonra yeni giriş | Giriş/DTMF ve yeni tur geçerli kalır |
| PB60 | İptalden sonra yazıcı tamamlanması | Eski yerel sahip bir kez bırakılır; generation yeniden açılmaz |
| PB61 | Bilinmeyen kısmi gönderimli yazıcı istisnası | UNKNOWN; kör yeniden deneme yok; güvenli bağlantı politikası |
| PB62 | Yerel TTS işi iptali görmezden gelir | M06 kirası doğrulanmış tamamlanma/karantinaya kadar |
| PB63 | Yerel iş biter ama aşağı akış kuyruğu dolu | GPU tamamlanması bağımsız; sınırlı CPU sahipliği veya açık iptal |
| PB64 | Yeniden bağlanmadan sonra yinelenen/yabancı tamamlanma | Yalnız eski sahip temizliği; yeni akışa dokunulmaz |
| PB65 | Kesme hedef boşaltma niyeti üretir | Kimlik/yetenek bağlı; gönderim kilit dışında |
| PB66 | Yerel temizlik doğrulanmış, uzak desteklenmiyor | Kesin sayılarla SERVER FLUSHED; uzak desteklenmiyor, uç bilinmiyor |
| PB67 | Komutla eşleşen desteklenen sahte istemci ACK'i | Yalnız CLIENT gözlenen makbuz; uç iddiası yok |
| PB68 | Yanlış generation, komut kimliği veya bayat uzak ACK | Yeni kontrolde değişiklik veya sahte makbuz yok |
| PB69 | Son tarihe kadar uzak ACK yok | UNKNOWN/zaman aşımı; sahte FLUSHED yok |
| PB70 | İdempotent olmayan veya kapsamsız uzak temizleme | Güvensiz yeniden deneme/boşaltma bastırılır; yeni generation güvende |
| PB71 | Olası etkiden sonra boşaltma sağlayıcı hatası | UNKNOWN/uzlaştırma; iptal asla geri alınmaz |
| PB72 | Telefon 20 ms fikstürü | Mevcut AudioSocket `10 01 40` + 320 B PCM değişmez |
| PB73 | Web 20 ms iç fikstür ve mevcut tel/istemci tempo | İç 640 B PCM; dış sözleşme ve tempo sahibi korunur |
| PB74 | AudioSocket'te uzak boşaltma yeteneği yok; DTMF/sonlandırma | Uydurma komut/bayt yok; kontrol yolu korunur |
| PB75 | Talep edilmiş DSP/PCM sonrası çerçeve | Kesin bayt/üst veri referansı, SERVER kapsamı, geçerli sayı |
| PB76 | Yalnız kuyrukta ve talepten önce silinmiş çerçeveler | Onlar için sahte referans üretilmez |
| PB77 | Gönderilmiş çerçeveden sonra duraklatma/kesme | Politikaya göre sınırlı geçmiş referans; sahte sessizlik yok |
| PB78 | Yavaş referans okuyucu ve tahliye | Açık boşluk/bilinmiyor; ayrı sınırlı bütçe; oynatma etkilenmez |
| PB79 | Oturumlar arası veya bayat dönem referans sorgusu, eksik saat eşlemesi | Ret veya erişilemez; uydurma hizalama yok |
| PB80 | Framer kalanıyla normal EOS ile iptal | Yalnız EOS'ta yetkili kuyruk akar; iptalde kesin atma |
| PB81 | Yazıcı bloklanmışken kopma | Sınırlı kapanış; sahip doğrulanmış tamamlanmaya kadar tutulur/karantina |
| PB82 | Yinelenen kapanış ve geç geri çağrı | Tam bir kez temizlik; yetim veya yeniden açılan oturum yok |
| PB83 | Telemetri alıcısı taşması/hatası ve dolu medya kuyruğu | Kontrol canlı kalır; güvenli sayaçlar; uydurma makbuz yok |
| PB84 | Kişisel veri/ses/istisna işareti ve commit edilmiş CRM işlemi | Sızıntı yok; iş makbuzu uzlaştırması bağımsız |
| PB85 | Gerçek F1-B → M02 → F6-B → sahte alıcı kesme/devam | Doğru imleç ve kesin çit; sahte denetleyici yok |
| PB86 | Gerçek F5-A/M06 tamamlanması → F6-A render → F6-B → referans test tüketicisi | Gerçek zincir; kapsamlı referans ve kaynak sahipliği |
| PB87 | Gerekli önceki testler + M00 özellik eşlemesi ve atlama incelemesi | Açıklanamayan regresyon yok; katı atlama sıfır |
| PB88 | Bütünlük farkı, olumsuz kontrol, geri dönüş ve kanıt kontrolleri | Yalnız sahipli değişiklikler; gerçek sonuçlar; sentetik PASS yok |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F6-B-G00 | Ön kontrol | Gerçek çekirdek/W2/F6-A/F1-B kabulü, uyumlu soy ve onay |
| F6-B-G01 | Tek otorite | Tek kuyruk/yazıcı/aktarım otoritesi; pasif içe aktarma; yetkili sahiplik |
| F6-B-G02 | Sözleşmeler | Gerçek M01/M02/F1-B/F6-A sözleşmeleri, kimlik ve değiştirilemez veri |
| F6-B-G03 | Kapasite | Geçerli sabit kapasite boyutları; tahsisten önce rezervasyon; küresel sınırlar |
| F6-B-G04 | Kuyruk | Sıralı sınırlı kuyruk, muhasebe; sessiz boşluk veya yineleme yok |
| F6-B-G05 | Geri basınç | Sınırlı iptal edilebilir geri basınç, adillik ve kontrol erişilebilirliği |
| F6-B-G06 | İmleç | ACK/tamamlanmadan bağımsız kesin sonraki hiç talep edilmemiş imleç |
| F6-B-G07 | Gönderim çiti | M02 atomik son gönderim çiti; iki yarış sırası; güvensiz `await` yok |
| F6-B-G08 | Duraklatma | Geri alınabilir yumuşak duraklatma, sınırlı tutma ve giriş sürekliliği |
| F6-B-G09 | Devam | Aynı generation devamı, kesin gönderilmemiş süreklilik ve monoton tempo |
| F6-B-G10 | Kesme | Geri alınamaz hedef kesmesi, doğru yerel silme ve idempotency |
| F6-B-G11 | Uçuştaki | Uçuştaki sahiplik, yerel M06 tamamlanması ve kör yeniden gönderim yok |
| F6-B-G12 | Boşaltma | Kapsamlı boşaltma makbuzu, yetenek kontrolü ve yeni generation güvenliği |
| F6-B-G13 | Aktarım uyumu | Mevcut web/AudioSocket tel ve DTMF/kontrol uyumu |
| F6-B-G14 | Referans | Sınırlı kapsamlı oynatma referansı, açık boşluklar ve gizlilik |
| F6-B-G15 | Yaşam döngüsü | EOS/iptal/kopma temizliği ve karantina; güvenli M04 gözlemleri |
| F6-B-G16 | Entegrasyon | Yalnız sınırda sahtelerle gerçek F1-B/F5-A/F6-A/M02/M06 bütünleşmesi |
| F6-B-G17 | Test kanıtı | PB01–PB88 gerçek geçen kanıt, gerekli regresyonlar ve olumsuz kontroller |
| F6-B-G18 | Bütünlük | Özellik korunumu; katı atlama yok; bütünlük ve geri dönüş provası |
| F6-B-G19 | Devir | Bağımsız inceleme, doğru kabul, F0-B/F6-C/F6-D/F1-C devri ve W3 hazırlık sınırları |

## 9. Kanıt

`evidence/F6-B/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F6_B_PREFLIGHT.json`, `PLAYBACK_INVENTORY.json`, `CHANGE_SCOPE.json`, `PLAYBACK_DECISIONS.md`, `CONTRACT_MAPPING.csv`, `CAPACITY_SPEC.md`, `RESERVATION_SPEC.md`, `QUEUE_CURSOR_SPEC.md`, `BACKPRESSURE_SPEC.md`, `SUBMISSION_FENCE_SPEC.md`, `PAUSE_RESUME_SPEC.md`, `PURGE_ACCOUNTING_SPEC.md`, `IN_FLIGHT_SPEC.md`, `FLUSH_RECEIPT_SPEC.md`, `TRANSPORT_CAPABILITY_MATRIX.csv`, `PLAYBACK_REFERENCE_SPEC.md`, `CLEANUP_SPEC.md`, `TELEMETRY_MAPPING.csv`, `PLAYBACK_BENCHMARK_PLAN.md`, `TEST_MATRIX.json`.

## 10. Geri dönüş

F6-B katı yolun parçasıdır; `f6_pipeline_v2=off` ile tamamen devre dışı kalır. Kod değişiklikleri `git revert`; kuyruk durumu kalıcı değildir.

## 11. Devir

- **F0-B:** `playback_reference` (talep edilmiş çerçeveler, kapsam, boşluklar) AEC değerlendirmesinin girdisi.
- **F6-C:** birleştirme/WSOLA/loudness/konfor gürültüsü bu kuyruğun önünde, render aşamasında; imleç ve çit değişmez.
- **F6-D:** chan_websocket aktarımı aynı kuyruk ve makbuz anlamını kullanır.
- **F1-C:** kapsamlı oynatma makbuzları backchannel/double-talk kararlarına girdi.
- **G4/G5:** gerçek uç benchmark'ı `PLAYBACK_BENCHMARK_PLAN.md`'ye göre; AMI/ARI aktarım doğrulaması G5.

## 12. Başlatma komutu

```
F6-B paketini uygula: docs/execution/packages/W3/F6-B-oynatma-kuyrugu.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F6-A ve F1-B kabulünü doğrula.
Tek kuyruk/tek yazıcı üzerinde kapasite rezervasyonu, imleç, M02 gönderim çiti, duraklat/devam/kesme,
kapsamlı boşaltma makbuzları ve F0-B oynatma referansını kur; uzak protokol uydurma.
PB01–PB88'i çalıştır, F6-B-G00…G19'u değerlendir, paket/F6-B dalında PR aç ve dur.
```
