# G3 — Ortak Freya kokpiti (arayüz)

> G2 kabulünden sonra, mevcut React panelini koruyarak dört alanlı ortak kokpit kurulur: **Ses Hattı** (F0–F6 Studio ve iz), **Atölye Operasyonu**, **Telefoni ve Santral**, **Gözetim ve Kalite**. Her görünür kontrol gerçek API/yetenek/yetki kaynağına bağlıdır; desteklenmeyen kontrol nedeniyle devre dışıdır. Sahte düğme, uydurma grafik, yalnız arayüz yetkisi, laboratuvar anahtarıyla canlı etkinleştirme veya otomatik eğitim yoktur. Mock/simülasyon verisi kalıcı etiketle ayrılır.

| Alan | Değer |
| --- | --- |
| Kimlik | G3 |
| Dalga | Ürün aşaması |
| Öncelik | P0 |
| Önkoşullar | G2 |
| Sonraki | G4 |
| Bayrak | Yeni bayrak yok; ekranlar paket bayraklarının ve M03 profillerinin **gerçek durumunu** gösterir, değiştiremez |
| Ortam | Yerel frontend araç zinciri (internetten kurulum yok); yalıtılmış fikstür arka ucu; gerçek müşteri işlemi yok |
| Eski görevler | F0-T27, F0-T28, F1-T23, F1-T24, F1-T25, F2-T28, F2-T29, F3-T34, F3-T35, F4-T29, F5-T27, F6-T25 |
| Kaynak | Bundle `06_PRODUCT_STAGES/G3/Freya_2_0_G3_UI_Master_Prompt.md`; aşama spec'lerindeki Studio bölümleri |
| Durum | NOT_RUN |

## 1. Amaç

Her pakette ayrı bir arayüz yazmak yerine tek, tutarlı ve dürüst bir kokpit: operatör ve geliştirici aynı ekranda gerçek durumu, birimi, kaynağı, tazeliği ve bilinmeyeni görür. M00 özellik envanterindeki her kimlik bir rotaya/eyleme/arka uç yeteneğine/teste eşlenir veya gerekçeli "yalnız arka uç" kararı alır.

## 2. Başlamadan önce

- [ ] G2 gerçek kabul; mevcut ağaç G2 anlık görüntüsüyle uyumlu (değilse soy uzlaştırma ve etkilenen yeniden çalıştırmalar).
- [ ] Kullanıcı G3'ü başlattı ("G3 aşamasını başlat"); G2 kabulü otomatik UI izni değildir.
- [ ] Yerel frontend bağımlılıkları kurulu; eksikse HOLD (internetten kurulum yok).
- [ ] M00 UI/API/özellik/DB/yapılandırma envanteri ve G2 özellik kapanışı okunmuş.

## 3. Kapsam

**Yapılacak:** Envanter uzlaştırma; mimari ve dosya sahipliği; tasarım sistemi ve kabuk; tipli istemci ve yetenek izdüşümü; paylaşılan gözlem durumu; 9 ses hattı, 7 atölye, 4 telefoni, 7 kalite ekranı; kapsam/güvenlik/regresyon; erişilebilirlik ve dayanıklılık; kanıt ve geri dönüş.

**Yapılmayacak:** Mevcut rotaları silme veya bozma; sayıyı doldurmak için yinelenen sayfa; dağıtım/migration/model ağırlığı değişikliği; gerçek çağrı başlatma; gerçek müşteri kaydı değiştirme; G4/G5 başlatma; eğitim; kapı durumunu arayüzden PASS yapma.

## 4. Dosyalar

Mevcut `frontend/` uyarlanır, değiştirilmez. Yollar öneridir; M00/G2 uzlaştırmasından sonra gerçek ağaca göre belirlenir.

```
frontend/src/
  app/                 mevcut kabuk/yönlendirici; tek entegrasyon yazarı
  components/cockpit/  gezinme, durum başlığı, kanıt çekmecesi, durum panelleri
  api/                 mevcut istemcinin genişletilmesi; tipli izdüşümler, doğrulama
  features/voice/      F0–F6 studiolar, genel bakış, iz
  features/workshop/   CRM, araç, randevu, atölye, satış, bilgi
  features/telephony/  çağrı, operatör, aktarım, RTP/RTCP
  features/quality/    GPU, olaylar, benchmark, kayıt, kapılar, araştırma
  state/               kapsamlı izdüşüm ve abonelik yaşam döngüsü
  styles/              tasarım belirteçleri, duyarlı düzen, erişilebilirlik
  tests/               UI01–UI100 izlenebilirliği
evidence/G3/<run_id>/
```

Sahiplik: kabuk/tasarım/istemci → arayüz entegrasyon sorumlusu (tek yazar); her alan için tek yazar; arka uç sözleşme sahipleri F0–F6, M01–M08. Aynı paylaşılan dosyaya paralel yazım yok.

## 5. Tasarım ve sözleşmeler

### 5.1 Düzen ve görsel dil

- Masaüstü öncelikli kabuk: dört alana gruplanmış daraltılabilir sol gezinme; üst çubukta ortam (LAB / MOCK / gerçekten desteklenen işletim kipi), seçili oturum/çalıştırma, bağlantı durumu, rol ve yalnız destekleniyorsa güvenli durdurma.
- Görünüm boyutları: 1440×900 ve 1280×800 masaüstü, 1024 tablet, 390 mobil (izleme). Klavye öncelikli; görünür odak; tuzak yok; erişilebilir adlar; diyalog odak geri dönüşü.
- Belirteçler: nötr yüzeyler, etkileşim için sade mavi, gerçek PASS için yeşil, bayat/HOLD için amber, gerçek hata için kırmızı, NOT_RUN/desteklenmiyor için gri. Durum her zaman metin + simge (yalnız renk değil). Türkçe etiketler: Hazır, Çalışıyor, Beklemede, Desteklenmiyor, Bilinmiyor, Ölçülmedi.
- Her sayfa: genel bakış, kapsamlı ayrıntı, (destekleniyorsa) yapılandırma/öneri, kanıt ve hatalar. Laboratuvar ve canlı profiller görsel ve mantıksal olarak ayrı; taslak değişiklik profili etkinleştirmez. Onay incelemesi kesin işlem özeti ve gerçek M07 challenge yaşam döngüsüyle (onay kutusu veya yalnız istemci modali değil).
- Grafikler yalnız kaynaklı gözlem veya açıkça işaretli fikstür serisi. Null/bilinmeyen = "veri yok" (asla sıfır); bilinmeyen boşluklarda enterpolasyon yok; kaynak, revizyon, zaman damgası, tazelik, birim, örnek sayısı ve ölçüm kapsamı erişilebilir. Metinden dalga biçimi uydurulmaz.

### 5.2 Ekran envanteri

Rota önerisidir; mevcut rota takma adı veya sekme olabilir. Eylem yoksa veya yetki yoksa kontrol nedeniyle devre dışı.

| Sayfa | Önerilen rota | Ekran | Paketler | Kritik sınır |
| --- | --- | --- | --- | --- |
| VP-01 | `/voice/overview` | Ses hattı genel bakış | F0-A–F6-D, M02, M04 | M04 izdüşümü; M02 durumu; ham müşteri verisi yok |
| VP-02 | `/voice/f0` | F0 Ses İşleme Studio | F0-A, F0-B, F6-B | SNR uydurma yok; AEC referansı yoksa bypass/HOLD; DTMF gürültü bastırıcıdan geçmez |
| VP-03 | `/voice/f1` | F1 Ses Zekâsı Studio | F1-A, F1-B, F1-C | Sahiplik değişmez; bayat anlamsal ipucu yeni endpoint üretmez |
| VP-04 | `/voice/f2` | F2 Konuşma Tanıma Studio | F2-A, F2-B, F2-C, M05, M06 | Kısmi/kararlı/son ayrı; kısmi sonuç iş eylemi tetiklemez; güven yoksa null |
| VP-05 | `/voice/f3` | F3 Zekâ Komuta Merkezi | F3-A, F3-B, F3-C, M07 | Onaysız öneri mutasyon göndermez; UNKNOWN makbuz otomatik yeniden denenmez |
| VP-06 | `/voice/f4` | F4 Dilbilim Studio | F4-A, F4-B, F4-C, M05 | Önizleme gerçek tek planlayıcıyı kullanır; istemcide ikinci normalizasyon yok |
| VP-07 | `/voice/f5` | F5 Nöral Sentez Studio | F5-A, F5-B, F5-C, F5-D, M03, M06 | Leyla seed 9 gerçek etkin profilden; deneysel seed'ler (42/77/123) yalnız laboratuvar; ODE/ECAPA/MOS ölçülmediyse NOT_RUN |
| VP-08 | `/voice/f6` | F6 Ses Aktarım Studio | F6-A, F6-B, F6-C, F6-D | Hız sahibi tek; duraklama defteri istenen/doğal/eklenen ayrı; boşaltma kapsamı yerel/PBX/uç ayrı |
| VP-09 | `/voice/traces` | İz gezgini | M01, M02, M04, F0-A–F6-D | Farklı saat alanları çıkarılmaz; aşama p95'leri toplanmaz; sayfalı |
| WO-01 | `/workshop/overview` | Atölye genel bakış | F3-A/B/C, M07 | Lift durumu konuşmadan çıkarılmaz |
| WO-02 | `/workshop/appointments` | Randevu yöneticisi | F3-A/B/C, M07 | G3'te yalnız yalıtılmış sentetik kayıtlar; yenilemede yinelenen etki yok |
| WO-03 | `/workshop/customers` | CRM ve müşteriler | F3-A/B/C, M07 | Arayan numarası kimlik doğrulaması değil; tarayıcıda kişisel veri saklanmaz |
| WO-04 | `/workshop/vehicles` | Araç kaydı | F3-A/B/C, M05, M07 | ASR adayı doğrulanmış kimlik değil |
| WO-05 | `/workshop/orders` | Atölye ve lift kuyruğu | F3-B/C, M07 | Desteklenmeyen mutasyon devre dışı; uydurma durum yok |
| WO-06 | `/workshop/sales` | Satış ve parça | F3-B/C, M05, M07 | RAG fiyat/stok kaynağı değil; onaysız ödeme/sipariş yok |
| WO-07 | `/workshop/knowledge` | Otomotiv bilgisi | F3-C, M05, M07 | Erişim filtresi sıralamadan önce; kısıtlı belge üst verisi gösterilmez |
| TP-01 | `/telephony/overview` | Santral ve çağrılar | F3-B, F6-A, F6-B, F6-D, M07 | AMI kabul ≠ yanıtlandı; G3'te çağrı yok |
| TP-02 | `/telephony/console` | Operatör konsolu | F3-A, F3-B, F6-B, M07 | Kör yeniden deneme yok; mock operatör etiketli |
| TP-03 | `/telephony/media` | Medya aktarım izleme | F6-A–F6-D, F0-B | Otomatik geçiş veya güvensiz düşüş yok |
| TP-04 | `/telephony/quality` | SIP kalitesi | F6-D, M04 | Yalnız RTCP'den MOS veya duyulur sonuç yok |
| OQ-01 | `/quality/overview` | Sistem kalitesi | M00, M04, M08 | Plan sayısı ≠ çalıştırılan test sayısı |
| OQ-02 | `/quality/gpu` | GPU kaynak izleme | M03, M06, F2-C, F5-C | GPU sıfırlama/öldürme yok; sahte sıfır yok; erken kira bırakma yok |
| OQ-03 | `/quality/events` | Olay ve olay kaydı | M02, M04, M07 | M04 kalıcı M07 denetimi değildir; gizli/ham yük yok |
| OQ-04 | `/quality/experiments` | Benchmark ve A/B laboratuvarı | M08, F0-B, F2-C, F5-C, F6-C, F5-D | Görüntülemek G4/G5 başlatmaz; MOS NOT_RUN |
| OQ-05 | `/quality/registry` | Model ve sözlük kaydı | M03, M05, F4-B, F5-B, F5-D | Onaysız etkinleştirme, indirme veya LoRA eğitimi yok |
| OQ-06 | `/quality/gates` | Kabul ve kanıt | M00, M08, tüm paketler | Arayüz kapıyı PASS veya `live_ready` yapamaz |
| OQ-07 | `/quality/research` | İsteğe bağlı araştırma | F5-D, F5-C, M03, M06, M07 | Kişisel ses yükleme, eğitim, uyarlayıcı etkinleştirme yok |

### 5.3 Veri ve eylem sözleşmesi

- Tipli istemci gerçek şemalara bağlanır; çalışma zamanı doğrulaması; istek kimliği; kapsam değişince iptal; şema uyuşmazlığında güvenli hata (zorlanmış başarı yok).
- Olay akışı: mevcut M04 güvenli izdüşümü; sıra/dönem boşluğu tespiti; açık yeniden bağlanma ve sınırlı anlık görüntüyle eşitleme; bağlantı kopunca "bayat" etiketi; iş eylemi tekrarı yok.
- Mutasyon sırası: öneri → M07 challenge (kesin işlem özeti) → tek yetkili etki → işleme özgü makbuz. Çift tıklama tek etki ve aynı makbuz; değişen slot/fiyat eski onayı geçersiz kılar; commit sonrası zaman aşımı → doğrulanmış makbuza kadar "bilinmiyor"; kör yeniden gönderim yok.
- Yetkilendirme arka uçtadır; arayüzdeki onay yetkinin yerine geçmez. Rol değişince maskelenmiş/temizlenmiş veri; doğrudan API yetkisizi reddeder.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| UI.01 | Ön kontrol ve G3 izni | G2 kabulü, uyumlu soy, CG/WG ve kullanıcı izni doğrulanır; kapsam çözülür; eksikse HOLD | UI01–UI04 |
| UI.02 | Envanter uzlaştırma | M00 envanterleri ve G2 özellik kapanışı; mevcut React rotaları, işleyiciler, bayraklar, API istemcileri listelenir | UI05–UI08 |
| UI.03 | Mimari ve sahiplik | Kurulu frontend yığını/yönlendirici/durum/test araçları doğrulanır; dosya sahipliği ve entegrasyon planı; mevcut rota/API arayüzleri korunur | UI09–UI12 |
| UI.04 | Tasarım sistemi ve kokpit kabuğu | Ortak kabuk, dört alan, gezinme, duyarlı düzen, klavye odağı, Türkçe etiketler, tema belirteçleri, tutarlı durum gösterimi | UI13–UI16 |
| UI.05 | Tipli istemci ve yetenek izdüşümü | Gerçek şemalara ve kayıtlı API'lere bağlama; çalışma zamanı doğrulaması; istek kimliği; kapsam değişiminde iptal; açık desteklenmiyor/bilinmiyor | UI17–UI20 |
| UI.06 | Paylaşılan gözlem durumu | M04 güvenli izdüşümü; sınırlı güncelleme; sıra/dönem boşluğu; yeniden bağlanma/eşitleme; kapsamlı önbellek ve temizlik | UI21–UI24 |
| UI.07 | Ses genel bakış ve izler | VP-01 ve VP-09: kapsamlı gerçek aşama durumları, birimler, olaylar ve doğrudan gözlenen gecikme | UI25–UI28 |
| UI.08 | F0 Studio | VP-02: profiller, DSP kontrolleri ve kanıt, ham DTMF durumu, AEC referans geçerliliği; uydurma SNR yok | UI29–UI32 |
| UI.09 | F1 Studio | VP-03: VAD, geri bakış, endpoint, duraklat/commit ve anlamsal kanıt; sahiplik değişmez | UI33–UI36 |
| UI.10 | F2 Studio | VP-04: kısmi/kararlı/son, ham/kanonik, korumalı varlıklar, güven kökeni ve M06 zamanlama ayrımı | UI37–UI40 |
| UI.11 | F3 Studio | VP-05: iş akışı DAG, slot kökeni, RAG kaynakları, M07 challenge ve kapsamlı makbuzlar | UI41–UI44 |
| UI.12 | F4 Studio | VP-06: kesin metin görünümleri, korumalı gruplar, morfoloji, G2P, vurgu, değiştirilemez plan kontrolleri | UI45–UI48 |
| UI.13 | F5 Studio | VP-07: profil/seed/ODE/latent/önbellek/kalite ve ölçülmüş laboratuvar metrikleri; otomatik eğitim yok | UI49–UI52 |
| UI.14 | F6 Studio | VP-08: render, hız/duraklama defteri, çerçeve/kuyruk/boşaltma/kodek durumu; kesin teslim kapsamı | UI53–UI56 |
| UI.15 | Atölye gezinme ve CRM | WO-01, WO-03, WO-04: yetkili izdüşümler ve maskelenmiş veri | UI57–UI60 |
| UI.16 | Randevu ve iş emirleri | WO-02, WO-05: mevcut onaylı işlem akışları ve işleme özgü makbuzlar | UI61–UI64 |
| UI.17 | Satış ve bilgi | WO-06, WO-07: yetkili fiyat/stok ve erişim filtreli kaynak bağlantıları; uydurma ürün verisi yok | UI65–UI68 |
| UI.18 | Santral ve operatör | TP-01…TP-04: aktarım/çağrı durumu, doğrulanmış yetenekler, güvenli devre dışı canlı işlemler, fikstürler | UI69–UI76 |
| UI.19 | Kalite ve kaynak görünümleri | OQ-01…OQ-03: doğru metrikler, kapsam ve güvenli olay izdüşümleri | UI77–UI80 |
| UI.20 | Deney, kayıt ve araştırma görünümleri | OQ-04…OQ-07: kanıt karşılaştırma ve uygunluk incelemesi; G4/G5 veya eğitim başlatma yok | UI81–UI84 |
| UI.21 | Kapsam, güvenlik, katmanlar arası regresyon | Tüm G3 vakaları gerçek arayüz ve kabul edilmiş arka uçla yalıtılmış fikstürlerde; eski UI/API davranışı korunur | UI85–UI92 |
| UI.22 | Erişilebilirlik, performans, kurtarma | Klavye ve odak, yakınlaştırma, ekran okuyucu, düzen, uzun izler, çevrimdışı yükleme, temizlik, başarısız komutlar | UI93–UI96 |
| UI.23 | Kanıt, checkpoint, geri dönüş | Kesin kaynak ağacı, build ve test çıktıları, özellik karar matrisi, bağımsız inceleme, geri dönüş talimatı | UI97–UI99 |
| UI.24 | Bağımsız kabul ve durma | Tüm kapılar G2 soyuyla incelenir; HOLD/FAIL veya gerçek G3 PASS; G4'ten önce dur | UI100 |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| UI01 | G2 kabulü yok | Kaynak değişikliği yok; G3 HOLD |
| UI02 | G2 anlık görüntüsü mevcut ağaçtan farklı | Soy uzlaştırma ve etkilenen yeniden çalıştırmalar gerekir |
| UI03 | Plan kaynağı uyuşmazlığı (değiştirilmiş paket) | Değiştirilmiş kaynak reddedilir; kesin uyuşmazlık kaydedilir |
| UI04 | UI izni yok | Uygulama veya servis başlatma yok |
| UI05 | Eski doğrudan rota | Aynı erişilebilir hedef/davranış veya incelenmiş uyumlu takma ad |
| UI06 | Herkese açık arayüzü olmayan özellik | Test ve sahipli açık "yalnız arka uç" kararı |
| UI07 | Mock veya yalnız beyan edilmiş özellik | Asla canlı çalıştırılmış işlev diye sınıflanmaz |
| UI08 | Bağlanmamış eski kontrol | Boşluk kaydedilir; zorunlu arka uç boşluğu sahip pakette çözülür |
| UI09 | Onaysız paylaşılan dosya düzenlemesi | Yazar engellenir; sahip incelemesi istenir |
| UI10 | Yerel frontend bağımlılığı eksik | HOLD; internetten kurulum yok |
| UI11 | Herkese açık API şeması değişmiş | UI kabulünden önce uyumluluk kırılması tespit edilir |
| UI12 | Kabuğa paralel düzenleme | Tek yazar; entegrasyonu sahip yapar |
| UI13 | Dört kokpit alanı | Eşlenen tüm alanlar uygun yetkiyle gezilebilir |
| UI14 | Derin bağlantı ve tarayıcı geri | Doğru kapsamlı rota geri yüklenir; bayat özel durum yok |
| UI15 | Duyarlı gezinme | Belirlenen genişlik ve yakınlaştırmada kullanılabilir; sıkışan kontrol yok |
| UI16 | Dil ve tema | Görünür metin Türkçe; tutarlı anlamsal belirteçler; okunur kontrast |
| UI17 | Bilinmeyen yetenek | Etkilenen kontrol devre dışı ve güvenli neden gösterilir |
| UI18 | Yetkisiz yetenek üst verisi | Hassas kaynak kimliği ve kontroller gösterilmez |
| UI19 | Şema uyuşmazlığı | Güvenli hata; zorlanmış başarı veya uydurma geri düşme yok |
| UI20 | Kapsam değiştikten sonra tamamlanan istek | Bayat sonuç yok sayılır; oturumlar arası veri yok |
| UI21 | Olay sırası boşluğu | Eksik işaretlenir ve sınırlı anlık görüntüyle eşitlenir |
| UI22 | Yinelenen/sırasız olay | Tekilleştir veya yok say; doğru boşluk işareti korunur |
| UI23 | WebSocket kopması | Bayat etiketi; sınırlı yeniden bağlanma; iş tekrarı yok |
| UI24 | Bileşen kaldırma/kapanış | Abonelik bırakılır, tamponlar serbest; arka planda sızıntı yok |
| UI25 | Aşama bilinmiyor | "Bilinmiyor" gösterilir; sıfır veya geçti değil |
| UI26 | Farklı saat alanlı iz | Karşılaştırılamaz zaman damgaları çıkarılmaz |
| UI27 | İzde duyulur uç ölçümü yok | Nedenle null |
| UI28 | İz kapsamı yetkisiz | Okuma reddi; özel ayrıntı temizlenir |
| UI29 | F0 ham/işlenmiş ayrımı | Gerçek aşama ve birim etiketli; çıkarılmış dalga biçimi yok |
| UI30 | AEC referansı yok/geçersiz | Etkin iptal yerine bypass/HOLD gösterilir |
| UI31 | DTMF ham musluğu | Kontroller DTMF'yi gürültü bastırıcıdan geçirmez |
| UI32 | RNNoise desteklenmiyor | Nedenle kullanılamaz; mevcut profil korunur |
| UI33 | F1 başlangıç ve sessizlik | Gerçek örnek/saat kökeni görünür |
| UI34 | Anlamsal ipucu bayat | Süresi doldu gösterilir; yeni endpoint veya duraklatma eylemi yok |
| UI35 | Onaylanmış kesme | Gerçek F1-B commit gösterilir; kısmi sonuç beklenmez |
| UI36 | Aynı generation devamı | Generation/imleç korunur; yinelenen oynatma isteği yok |
| UI37 | Kısmi/kararlı sonuç | Geçici gösterim ve iş eylemi yok |
| UI38 | Son ASR revizyonu | Eski geçici durumun yerini alır; ham metin yetkiyle kesin |
| UI39 | Güven değeri yok | Null; sıfır veya doğruluk yüzdesi değil |
| UI40 | Belirsiz araç adayı | Netleştirme gösterilir; doğrulanmış araç iddiası yok |
| UI41 | F3 onaylanmamış öneri | Mutasyon gönderilmez |
| UI42 | F3 makbuzu UNKNOWN | Bilinmiyor ve uzlaştırma yolu gösterilir; otomatik yeniden deneme yok |
| UI43 | RAG kaynağı yok veya yetkisiz | Çekimser kal veya yetkiye göre gizle; uydurma dayanak yok |
| UI44 | Çoklu niyet kısmi başarı | Düğüm başı sonuçlar; toplu sahte başarı yok |
| UI45 | Korumalı sayısal değer | Kaynak ve model eşlemesi kesin anlamsal değeri korur |
| UI46 | Desteklenmeyen vurgu veya perde kontrolü | İstenen ile uygulanan ayrı gösterilir |
| UI47 | F4 önizlemesi | Gerçek tek planlayıcı; istemcide yinelenen normalizasyon yok |
| UI48 | Korumalı parça sınırı | Doğrulanmış atom bütün veya açık HOLD |
| UI49 | Leyla varsayılanı | Seed 9 gerçek etkin profilden gösterilir |
| UI50 | Deneysel seed'ler | Yalnız laboratuvarda isteğe bağlı; canlı varsayılan değişmez |
| UI51 | Önbellek isabeti | Kapsam ve taze generation üst verisi; özel anahtar/yük gösterilmez |
| UI52 | ODE/ECAPA/MOS ölçülmemiş | Profil isteği NFE ve ölçümden ayrı; NOT_RUN |
| UI53 | Hız sahibi F5 | Arayüz F6 WSOLA işlemini yinelemez |
| UI54 | Doğal duraklama defteri | İstenen/doğal/eklenen ayrı gösterilir |
| UI55 | AudioSocket çerçeveleme | 8k PCM16 çerçeve baytları kodek laboratuvarı baytlarından ayrı |
| UI56 | Boşaltma kapsamı | Yerel/PBX/uç durumları ayrı; duyulur durma iddiası yok |
| UI57 | Müşteri listesinde rol değişimi | Maskelenmiş/temizlenmiş kapsamlı veri; doğrudan API yetkisizi reddeder |
| UI58 | Araç ASR adayı | Kimlik kanıtı olarak kullanılmaz |
| UI59 | Atölye sağlayıcısı yok | Desteklenmiyor durumu; uydurma lift durumu yok |
| UI60 | Eşleşen kayıt yok | Doğru boş durum; hata veya demo kaydı değil |
| UI61 | Onayda çift tıklama | En çok bir yetkili etki ve aynı makbuz |
| UI62 | Değişen slot/fiyat | Eski onay geçersiz; yeni sunum istenir |
| UI63 | Commit sonrası zaman aşımı | Doğrulanmış makbuza kadar bilinmiyor; kör yeniden gönderim yok |
| UI64 | Kabulden önce iptal ile commit sonrası iptal | Farklı sonuçlar; sahte geri alma yok |
| UI65 | Fiyat kaynağı eski | Bayat işaretlenir; onaylı işlemden önce yeniden doğrulanır |
| UI66 | Yalnız stok sorgusu | Rezervasyon veya sipariş oluşturmaz |
| UI67 | Yetkisiz RAG belgesi | Başlık, sayı, skor veya parça sızmaz |
| UI68 | Kaynak belgeler arasında çelişki | Belirsizlik gösterilir; zorlanmış yanıt yok |
| UI69 | AMI originate kabul edildi | Yanıtlandı veya köprülendi diye gösterilmez |
| UI70 | ARI köprüsü oluşturuldu | Ses duyuldu diye gösterilmez |
| UI71 | Desteklenmeyen alternatif aktarım | AudioSocket tabanı; otomatik geçiş yok |
| UI72 | Uzak ön süre bilinmiyor | Bilinmiyor/HOLD; düşük gecikme iddiası yok |
| UI73 | PBX kaybı/yeniden bağlanma | Yeni akış dönemi; bayat ses tekrarı yok |
| UI74 | DTMF ve aktarım | Gerçek sağlayıcı olayları ve makbuz; kapsamlı ve tekilleştirilmiş |
| UI75 | TLS/yetenek hatası | Güvensiz geri düşme veya sahte bağlı durum yok |
| UI76 | RTCP yön ve birimi | Doğru bacak/gözlemci/saat etiketi; yoksa null |
| UI77 | GPU bellek telemetrisi yok | Bilinmiyor; 0 MB değil |
| UI78 | Yerel iş iptali | Gerçek tamamlanmaya kadar karantina/kira |
| UI79 | Düşen olaylar | Sıra boşluğu gösterilir; tam iz gibi davranılmaz |
| UI80 | Denetim görünürlüğü | M07 kalıcı denetimi en iyi çaba M04 olaylarından ayrı |
| UI81 | Tarihsel benchmark ile güncel | Kaynak/anlık görüntü/tarih, n ve koşullar etiketli |
| UI82 | Kayıt etkinleştirme isteği | Onaysız canlı değişiklik yok; değiştirilemez revizyonlar korunur |
| UI83 | G3 ekran durumu | Doğruluk kaynağı gerçek incelenmiş kanıt; değiştirilebilir anahtar değil |
| UI84 | F5-D gerçek hata kanıtı yok | Araştırma HOLD/NOT_RUN; eğitim eylemi yok |
| UI85 | Gerçek UI eylem/API eşlemesi | Her görünür eylem kontrolünün işleyicisi ve sözleşme testi var |
| UI86 | Yalnız arka uç veya ertelenmiş isteğe bağlı öğe | Belgelenmiş karar; sahipsiz zorunlu özellik yok |
| UI87 | Eski rotalar ve özellikler | Mevcut onaylı regresyon iddiaları geçer |
| UI88 | İki oturum/rol | Veri, oynatma, iz veya yapılandırma sızıntısı yok |
| UI89 | Uygulanabilirse CSRF/tekrar | Arka uç reddeder; arayüz atlatmaz veya yazmayı yeniden denemez |
| UI90 | Günlük/dışa aktarım incelemesi | Ham gizli bilgi, kişisel veri, kişisel ses veya düşük entropili hash yok |
| UI91 | Mock ile gerçek ortam | Kalıcı açık kaynak işareti; kipler arası etki yok |
| UI92 | Zorunlu arka uç kusuru | Sahip pakete dönülür; etkilenen G2/G3 kanıtı geçersiz |
| UI93 | Klavye ve odak | Tüm kontroller erişilebilir; diyaloglar odağı geri verir |
| UI94 | Yakınlaştırma/kontrast/okuyucu | %200 yakınlaştırmada ve belgelenmiş kontrast hedeflerinde erişilebilir |
| UI95 | Büyük iz veya olay patlaması | Sınırlı render, sayfalama ve bellek; ölçmeden donmama iddiası yok |
| UI96 | Çevrimdışı yükleme ve komut hatası | Yerel varlıklar; dürüst kullanılamaz durumu ve kurtarma |
| UI97 | Kanıt bildirimi | Kesin kaynak, test komutları, hash'ler, günlükler ve eksik vakalar |
| UI98 | Checkpoint/geri dönüş | Onaylı UI değişiklikleri kullanıcı düzenlemeleri veya DB verisi silinmeden geri alınır |
| UI99 | Bağımsız inceleme | Gözden geçiren yazar özetini değil gerçek kanıtı denetler |
| UI100 | Kapı durması | G3 yalnız gerçek onaylı kanıtla doğru; G4 başlatılmaz |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| UG00 | Giriş | Gerçek G2 kabulü + kullanıcı izni + soy |
| UG01 | Kapsam | Tüm M00 kimlikleri karara bağlanmış; sahipsiz zorunlu özellik yok |
| UG02 | Uyumluluk | Eski rotalar ve herkese açık sözleşmeler korunmuş |
| UG03 | Kabuk | Dört alan; duyarlı ve klavyeyle gezinme |
| UG04 | API bağlama | Her eylem gerçek kayıtlı API'ye veya belgelenmiş yerel davranışa bağlı |
| UG05 | Kapsam | Sunucu yetkilendirmesi; rol/özne/oturum yalıtımı |
| UG06 | Telemetri | Köken, birim, null, bayat, boşluk, saat doğru |
| UG07 | Ses F0/F1 | Doğrulanmış giriş ve kesme görünümleri |
| UG08 | Ses F2/F3 | Geçici ASR; gerçek iş makbuzları |
| UG09 | Ses F4/F5 | Tek plan; seed, önbellek ve yetenek sahipliği |
| UG10 | Ses F6 | Medya/kontrol/boşaltma kapsamı ve kodek yalıtımı |
| UG11 | Atölye | Gerçek CRM/randevu/atölye/satış bağlamaları |
| UG12 | Telefoni | Güvenli çağrı/medya, yetenek ve operatör kontrolleri |
| UG13 | Kalite | GPU, olaylar, benchmark, kayıt ve araştırma doğruluğu |
| UG14 | Güvenlik | Canlı yan etki, laboratuvar karışması veya sahte veri yok |
| UG15 | Erişilebilirlik | Klavye, odak, yakınlaştırma, kontrast, yardımcı etiketler |
| UG16 | Dayanıklılık | Çevrimdışı, bayat, yeniden bağlanma, sınırlı akışlar ve temizlik |
| UG17 | Testler | Uygulanabilir tüm UI01–UI100 ve mevcut regresyonlar kanıtlı |
| UG18 | Checkpoint | Geri alınabilir değişiklikler ve kanıt bütünlüğü |
| UG19 | İnceleme | Bağımsız doğrulanmış G3 kararı; G4'ten önce dur |

## 9. Kanıt

`evidence/G3/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `FEATURE_UI_MAP.json` (M00 kimliği → rota/eylem/API/yetki/test kimliği veya "yalnız arka uç" kararı), `ROUTE_COMPATIBILITY.md`, `ACCESSIBILITY_REPORT.md`, `SECURITY_REVIEW.md`, ekran görüntüleri (yalnız fikstür verisiyle), `ROLLBACK.md`.

## 10. Geri dönüş

Arayüz değişiklikleri ayrı commit'lerdedir; `git revert` mevcut paneli geri getirir. Arka uç, DB veya yapılandırma değişmediği için veri geri dönüşü gerekmez.

## 11. Devir

- **G4:** kokpitin benchmark/A-B ve kapı ekranları G4 kanıtını **okur**; G4'ü başlatmaz.
- **Arka uç boşluğu:** zorunlu bir özellik için arka uç yoksa ilgili pakete dönülür; etkilenen G2/G3 kanıtı geçersiz olur.

## 12. Başlatma komutu

```
G3 aşamasını uygula: docs/execution/stages/G3-arayuz.md.
Kuralları CLAUDE.md'den oku; G2 kabulünü ve soyu doğrula; M00 özellik envanterini ve mevcut frontend rotalarını çıkar.
Mevcut paneli koruyarak dört alanlı kokpiti gerçek API/yetenek/yetki bağlamalarıyla kur; desteklenmeyen kontrolü nedeniyle devre dışı bırak.
UI01–UI100'ü çalıştır, UG00…UG19'u değerlendir, asama/G3 dalında PR aç ve dur (G4'ü başlatma).
```
