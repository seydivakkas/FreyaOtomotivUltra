# F3-B — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri

> F3-A cephesinin içine: kural öncelikli hiyerarşik yönlendirici, isteğe bağlı sınıflandırıcı ve tek bir M06 P3 LLM geri düşmesi, mevcut Supervisor kaydı üzerinden dar uzman ajan adaptörleri, katı yapılı öneri doğrulaması, M07 politikasına bağlı araç kataloğu, doğrulanmış okuma/bilgi adaptörleri, onay sunumu, operasyon özeti ve geçersiz kılma, kalıcı idempotency, randevu oluştur/ertele/iptal adaptörleri, makbuz ve uzlaştırma, yanıt kalite kapısı. Yeni otorite, yeni defter veya yeni politika motoru yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F3-B |
| Dalga | W3 |
| Öncelik | P0 |
| Önkoşullar | W2_GATE, F3-A, F2-B, M07 |
| Sonraki | F3-C |
| Bayrak | `f3_pipeline_v2` + Supervisor kipi (`OFF / SHADOW / GUARDED`) |
| Ortam | CPU, geçici DB, yalıtılmış sağlayıcı, sahte LLM/sınıflandırıcı |
| Eski görevler | F3-T12, F3-T13, F3-T14, F3-T17, F3-T25, F3-T27, F3-T31, F3-T40 |
| Kaynak | Bundle `W3/Freya_2_0_F3_B_Agent_Implementation_Package.md`; [F3 spec](../../../stages/F3-dialogue-intelligence/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

Gecikme ölçümlerinde LLM gerektiren tur ~6 s; kural yolu yeterliyken LLM çağrılmamalı. Aynı zamanda randevu yazma işlemleri yarış, yeniden başlatma, zaman aşımı ve yanlış onaya karşı güvenli olmalı. F3-B, yönlendirmeyi hızlı ve belirlenimci, yazmayı kalıcı ve doğrulanabilir hale getirir.

## 2. Başlamadan önce

- [ ] CORE_GATE ve W2_GATE PASS; F3-A, F2-B, M07 **uygulama** kanıtıyla kabul edilmiş (plan belgesi önkoşul PASS değildir); onay; ilgisiz kirli dosyalar korunur.
- [ ] Mevcut diyalog, Supervisor, DB, API, DTMF, outbox ve aktarım işleyicileri (hata yolları dahil) izlenmiş; her etki sınıflanmış. Doğrudan DB çağıran eski rota atlama engeli olarak raporlanır, "korumalı" denmez.
- [ ] Mevcut sınıflandırıcı (varsa) incelenmiş; yeni model indirilmez. 2 000 senaryoluk küme (eski F3-T40) sürümlü manifestle; kalibrasyon/test ayrı.

## 3. Kapsam

**Yapılacak:** Sahiplik ve geçiş; sözleşmeler ve giriş kabulü; bağlam ve netleştirme; hiyerarşik yönlendirici; sınırlı sınıflandırıcı/LLM; Supervisor orkestrasyonu; uzman ajan adaptörleri; yapılı öneri doğrulaması; araç kataloğu ve yetki; okuma ve bilgi adaptörleri; onay sunumu; özet ve geçersiz kılma; kalıcı talep; oluştur/ertele/iptal adaptörleri; makbuz ve uzlaştırma; iptal ve yaşam döngüsü; yanıt ve kalite kapısı; kipler ve telemetri.

**Yapılmayacak:** Çoklu niyet ayrıştırma ve görev planlayıcı, RAG/belge kaynakları, hafıza düzeyleri, değerlendiriciler (F3-C); sınıflandırıcı eğitimi (yalnız mevcut olan kullanılır; eğitim ayrı karar); gerçek sağlayıcı; otomatik telafi işlemi.

## 4. Dosyalar

```
backend/supervisor/dialogue/
  router.py  classifier_bridge.py  llm_fallback.py  orchestrator.py
  agents/  service_booking.py  technical_knowledge.py  sales_parts.py
           customer_crm.py  workshop_operations.py  human_handoff.py
  tool_catalog_binding.py  read_adapters.py  confirmation_flow.py  operation_digest_binding.py
  booking_create.py  booking_reschedule.py  booking_cancel.py  receipts_reconcile.py
  quality_gate.py
tests/dialogue/routing/  tests/dialogue/transactions/
evidence/F3-B/<run_id>/
```

Tek cephe (F3-A), tek çalışma zamanı (M02), tek politika (M07), tek kalıcı defter (M07). Mevcut kayıt ve gönderim genişletilir; ikinci kayıt yok.

## 5. Tasarım ve sözleşmeler

### 5.1 Yönlendirme

```
FINAL/OK veya doğrulanmış DTMF/arayüz ─► bağlam (F3-A CAS) + F2-B adayları
  ─► Katman 0: kurallar (karşılama, iptal/durdur ayrımı, operatör, acil güvenlik, etkin slot yanıtı)
  ─► Katman 1: mevcut sınıflandırıcı (isteğe bağlı, tek geçiş; doğrulanmamış/NaN/bilinmeyen → reddedilir)
  ─► Katman 2: tek M06 P3 LLM geri düşmesi (yalnız gerekirse; tipli çıktı doğrulanır)
  ─► belirsiz/zayıf/eşit → netleştirme veya operatör; keyfi kazanan yok
```

- Kural belirleyiciyse LLM çağrı sayısı **sıfır** (casusla doğrulanır).
- "Randevumu iptal et" ile "konuşmayı durdur" ayrı rotalardır; örtük iptal yok. Etkin akışta beklenen slot yanıtı yeni bağımsız eylem sayılmaz; açık konu değişikliği etkilenen akışı ve onayı güvenle temizler. Aynı mesajda oluştur + iptal → hangisi önce sorulur; çoklu yazma yayılımı yok.
- F2-B adayı (ör. Qashqai, doğrulanmamış) yalnız aday slotudur → nötr netleştirme. İki aday + çıplak "evet" → açık seçim istenir. "Qashqai değil Juke" düzeltmesi korunur. Belirsiz VIN/plaka → tam tekrar istenir; bulanık düzeltme yok.
- LLM: hatalı/zaman aşımı/zamanlayıcı reddi → güvenli geri düşme; doğrudan sağlayıcı atlaması veya ikinci model çağrısı yok. İptal edilen HTTP isteği sürerken M06 kirası tutulur.

### 5.2 Uzman ajanlar

| Ajan | Yetenek | Dürüst sınır |
| --- | --- | --- |
| ServiceBooking | Randevu soruları, oluştur/ertele/iptal önerisi | Eksik slotta yalnız soru önerisi, DB değişikliği yok |
| TechnicalKnowledge | Onaylı teknik bilgi | Desteklenmeyen tanı → güvenli yönlendirme; uydurma teknik bilgi yok |
| SalesParts | Parça/satış bilgisi | Stok kaynağı yoksa stok bilinmiyor; satış vaadi yok |
| CustomerCRM | Müşteri kaydı okuma | Başka müşterinin geçmişi okumadan önce M07'de reddedilir |
| WorkshopOperations | Atölye iş emri bilgisi | Sağlayıcı yoksa uydurma iş emri yok |
| HumanHandoff | Operatör aktarımı | Aktarım başarısı uydurulmaz ("gönderildi" ≠ "bağlandı") |

Tek birincil ajan; sınırlı okuma yayılımı; onay başına **yalnızca bir** ayrıca yetkilendirilmiş değişiklik. Yinelenen ajan kimliği reddedilir; erişilemeyen yetenek açıkça "desteklenmiyor".

### 5.3 Öneri, yetki ve okuma

- Öneri güvenilmez veridir; etkisi yalnız M07 ile. Bilinmeyen araç, keyfi SQL alanı, yinelenen JSON anahtarı, aşırı büyük/derin nesne, int yerine bool, NaN, geçersiz zaman damgası reddedilir. LLM'in `actor/admin/confirmed/provider` geçersiz kılmaları reddedilir; güvenilmeyen belge/araç çıktısındaki "politikayı yok say" veri olarak kalır. Öneri kaynak revizyonu bayatsa ret/yeniden değerlendirme.
- Arayan numarası veya eşleşen araç kimlik değildir. Doğrulanmış müşteri yalnız kendi asgari kaydını görür; başka kaynak kimliği varlık sızdırmadan reddedilir; kurum üyeliği devredilmiş araç yetkisi değildir; yapılandırma sabitlendikten sonra iptal edilen politika geçerlidir; doğrulayıcı yoksa canlı yol HOLD (sahte OTP yok). Katalog satırı model doğrular, sahiplik değil. Sağlayıcının fazladan özel alanları güvenilir izdüşümle küçültülür; ham hali LLM bağlamına girmez.

### 5.4 Onay, özet, idempotency ve işlemler

- Önemli olgu (ör. fiyat) güvenilir kaynaktan yoksa yürütülebilir onay sorusu yok. Ses özeti sunum sınırından önce kesilirse rastlantısal "evet" onay değildir; güvenli yeniden sunum. Sunucuda tükenme veya yalnız yerel boşaltma "duyuldu" kanıtı değildir. Soruya bağlı geçerli sonraki tur onayı kabul edilir. Modelin kendi konuşması veya kısmi transkript onay değildir. Önemli değişiklik → eski soru iptal, yeni özet/özet karması. Yanlış/başka oturum/süresi dolmuş/iptal edilmiş soru diriltilmez. Yeniden başlatmada saat geçerliliği bilinmiyorsa muhafazakâr yeni onay.
- M07 kalıcı defteri: aynı anahtar + özet eşzamanlı → tek talep; aynı anahtar farklı özet → çakışma (bilgi sızıntısı yok); tüketilmiş soruyu yeni anahtarla kullanma reddi; yeniden başlatma sonrası yetkili tekrar → aynı makbuz; kapsam dışı tekrar → varlık ifşası yok; aynı istek sonradan yeni geçerli soruyla → kısıtlar izin verirse ayrı meşru operasyon.
- İşlemler gerçek yerel işlemle: son boş saat için iki bağlantı → en fazla bir commit, kapasite değişmezi; ön kontrol ile talep arasında saat değişirse işlem reddeder veya yeni sunum; başarılı oluşturma etki/sonuç/denetim/outbox ile atomik (fikstür makbuzu MOCK); ertelemede hedef boş değilse eski randevu korunur (kısmi bırakma yok); bayat kayıt sürümü/yanlış durumla iptal → istenmeyen etki yok; zorunlu denetim niyeti yazılamazsa yeni etki yok.
- Kurtarma: commit öncesi çökme → yetkili yeniden denemeden önce etki olmadığı kanıtlanır; commit sonrası yanıt öncesi çökme → kalıcı makbuz kurtarılır, yinelenen yazma yok; zaman aşımı/belirsiz etki → `UNKNOWN`, sınırlı uzlaştırma; çelişkili/yanlış kapsamlı makbuz → reddet/uzlaştır/HOLD.

### 5.5 İptal, yanıt ve kipler

M02 operasyon kabulünden önce iptal → gönderim yok, kullanılmamış onay iptal; talep/commit sonrası iptal → kalıcı sonuç korunur, bayat konuşma bastırılır, otomatik telafi yok. `MOCK/PENDING/UNKNOWN` veya eski `true` makbuz gerçek başarı gibi söylenmez. Kalite kapısı salt okunur ve belirlenimci: modelin yanlış tarih/fiyat/makbuz söylemesi güvenli izdüşümle onarılır veya engellenir; yeni araç çağrısı yok. `SHADOW`'da ek okuma/yazma/çıkarım/onay tüketimi sıfır; `GUARDED`'da politika yoksa hata kapalı; `OFF` korumalı atlama engel olarak kaydedilir.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F3-B.01 | Ön kontrol ve soy | CG/WG kabulü, F3-A/F2-B/M07, bildirimler, onay; uyumsuz farklar | Ön kontrol raporu; MI01–MI06 |
| F3-B.02 | Diyalog/araç envanteri | Diyalog, Supervisor, DB, API, DTMF, outbox, aktarım işleyicileri ve hata yolları; etki sınıflaması | MI07–MI08 |
| F3-B.03 | Sahiplik ve geçiş | Tek cephe, tek çalışma zamanı, tek politika, tek kalıcı defter; dar düzenlemeler, eski varsayılanlar | Karar kaydı |
| F3-B.04 | Sözleşmeler ve giriş | M01/M02/M07 ve F2-B; final/diğer kanal olaylarının doğrulanması ve tekilleştirme | MI09–MI16 |
| F3-B.05 | Bağlam ve netleştirme | F3-A CAS; güncel aday ipuçları; olumsuzluk ve korumalı kimlikler; bağımlı slot geçersizliği | MI17–MI24 |
| F3-B.06 | Hiyerarşik yönlendirici | Mevcut taksonomi ve kural önceliği; etkin akış ile düzeltmeler, güvenlik ve belirsizlik | MI25–MI34 |
| F3-B.07 | Sınırlı sınıflandırıcı/LLM | Mevcut sınıflandırıcı; tek isteğe bağlı geçiş ve tek M06 P3 geri düşmesi; çıktı ve bütçe doğrulaması | MI32–MI38 |
| F3-B.08 | Supervisor orkestrasyonu | Mevcut kayıt ve gönderim; tek birincil ajan, sınırlı okuma yayılımı, sıralı onaylı yazmalar | MI39, MI46 |
| F3-B.09 | Uzman ajan adaptörleri | ServiceBooking, TechnicalKnowledge, SalesParts, CustomerCRM, WorkshopOperations, HumanHandoff | MI40–MI45 |
| F3-B.10 | Yapılı öneri doğrulaması | Katı M07 şemaları; yinelenen, bilinmeyen alan, güvensiz araç kimliği, yetki geçersiz kılma reddi | MI47–MI54 |
| F3-B.11 | Araç kataloğu ve yetki | Her okuma/yazma/etki → gerçek M07 politikası ve güvenilir kapsamlı kaynak çözücü; alternatif yollar denetimi | MI55–MI59 |
| F3-B.12 | Okuma ve bilgi adaptörleri | Kapsamlı veri alma, tazelik ve kanıt doğrulaması, asgari çıktı; çıkarılmış stok/fiyat yok | MI60–MI63 |
| F3-B.13 | Onay sunumu | Yetkili operasyon ve özet M07 sorusuna bağlı; F1/F6 kesmesi ve kanal kökeni dikkate alınır | MI64–MI67 |
| F3-B.14 | Özet ve geçersiz kılma | M07 kanonik özeti, ilgili slot revizyonu, kapsam ve sağlayıcı/politika bağları; önemli değişiklikte iptal | MI68–MI70 |
| F3-B.15 | Kalıcı talep | M07 idempotency defteri; tam tekrar, çakışan özet, yeniden başlatma, tüketilmiş soru ve yetki | MI71–MI76 |
| F3-B.16 | Randevu oluşturma | Kabul edilmiş mevcut depo; işlemsel kapasite/yetki/sürüm kontrolleri ve kapsamlı makbuz | MI77–MI79 |
| F3-B.17 | Erteleme/iptal | Onaylı mevcut işlemler atomik; reddedilen hedefte eski randevu korunur; otomatik telafi yok | MI80–MI82 |
| F3-B.18 | Makbuz ve uzlaştırma | Gerçek M01/M07 makbuzu; yerel/dış etki ayrımı; bilinmeyen için kalıcı sınırlı uzlaştırma | MI83–MI86 |
| F3-B.19 | İptal ve yaşam döngüsü | M02 atomik kabul/teslim, M06 yerel tamamlanma, konuşmadan bağımsız kalıcı sonuç; temizlik sınırları | MI87–MI88, MI94 |
| F3-B.20 | Yanıt ve kalite kapısı | Doğrulanmış anlamsal konuşma/görüntü; salt okunur belirlenimci kalite kontrolü; yazma tekrarı yok | MI89–MI90 |
| F3-B.21 | Kipler ve telemetri | OFF/SHADOW/GUARDED varsayılanları; gölgede ek etki yok; M04 gizliliği ve M07 denetim ayrımı | MI91–MI93 |
| F3-B.22 | Belirlenimci doğrulama | Yalıtılmış sağlayıcılarla gerçek F3-B/F3-A/M07/M02/M06; MI01–MI96 ve etkilenen önceki testler | Tüm testler çalıştırılmış |
| F3-B.23 | Regresyon, geri dönüş, benchmark | Tüm M00 kimlikleri; fikstürde geri dönüş; ertelenen performans/gerçek sağlayıcı protokolü | MI95–MI96 |
| F3-B.24 | Kabul ve devir | F3-B-G00…G19 bağımsız inceleme; doğru hazırlık; arayüzler ve engeller | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| MI01 | W2 yok veya NOT_RUN; başlatma istendi | Kaynak değişikliği yok; açık önkoşul engeli |
| MI02 | İlgisiz anlık görüntüde çekirdek kapı PASS | Uyuşmayan soy reddedilir; uydurma kabul yok |
| MI03 | F2-B planı var ama uygulama kanıtı yok | HOLD; plan belgesi önkoşul PASS değildir |
| MI04 | Açıklanamayan güvenlik farkı olan kabul edilmiş W2 atası | Yürütmeden önce etkilenen regresyon ve inceleme gerekir |
| MI05 | Onay yok veya ilgisiz kirli dosyalar | Kaynak değişikliğinden önce dur; kullanıcı düzenlemeleri korunur |
| MI06 | Gerçek kabul edilmiş önkoşullar ve temiz yetkili kapsam | Yalnız envantere ilerle; testlere kadar hazırlık false |
| MI07 | Eski rota doğrudan DB çağırır; kaynak ve özellik eşlenir | Atlama engeli raporlanır; korumalı kapsam iddia edilmez |
| MI08 | Mevcut yinelenen ajan/geçit adayı bulunur | Gerçek sahip yeniden kullanılır; ikinci otorite veya yinelenen yürütme yok |
| MI09 | Güncel kimliklerle FINAL OK ses sonucu | Bir F3-A talebi ve bir rota |
| MI10 | Açık oluşturma istekli PARTIAL | Korunan okuma, slot değişikliği, onay veya yazma yok |
| MI11 | Olumlu STABLE_PREFIX | Onay veya değişiklik yok |
| MI12 | NO_SPEECH veya ERROR veya UNKNOWN sonucu | Güvenli kurtarma; normal iş gönderimi yok |
| MI13 | Aynı kaynak revizyonunda tekrarlanan final | İkinci rota veya etki yok |
| MI14 | Yanlış oturum, tur veya bayat revizyon | Durum değişmeden ret |
| MI15 | Doğru kapsamlı soruyla doğrulanmış DTMF seçimi | Sahte ASR değil, gerçek DTMF kökeniyle yönlendirme |
| MI16 | Kimliği doğrulanmamış arayüz onayı veya geçersiz DTMF tekrarı | Ret; talep veya soru tüketimi yok |
| MI17 | F2-B adayı Qashqai doğrulanmamış | Yalnız aday slotu; nötr netleştirme |
| MI18 | İki aday model ve çıplak "evet" | Seçim yok; açık seçim istenir |
| MI19 | Olumsuzluk "Qashqai değil Juke" | Düzeltme korunur; olumsuzlanan model seçilmez |
| MI20 | Korumalı VIN/plakada belirsiz karakter | Tam tekrar istenir; bulanık düzeltme yok |
| MI21 | Araç değişiminden sonra bayat F2 bağlam revizyonu | Bayat ipucu yok sayılır; güncel kapsam yeniden değerlendirilir |
| MI22 | Aynı beklenen revizyonla iki eşzamanlı slot güncellemesi | Bir CAS kazanır; bayat fark reddedilir veya yeniden değerlendirilir |
| MI23 | Bekleyen onayla değişen hizmet veya araç | Bağımlı bilgiler ve önemli onay geçersiz |
| MI24 | A oturumunun ipuçlarına B'den erişim | Oturumlar arası veri veya rota eğilimi yok |
| MI25 | Basit karşılama | Belirlenimci rota; sıfır LLM/araç etkisi |
| MI26 | Açık randevu iptali ile konuşmayı durdur | Doğru ayrı rota; örtük iptal yok |
| MI27 | Sıradan akışta açık operatör isteği | Mevcut aktarım rotası; ilgisiz değişiklik yok |
| MI28 | Acil güvenlik fikstürü | Onaylı muhafazakâr yükseltme; doğrulanmamış tanı yok |
| MI29 | Kesin beklenen bağlamla etkin slot yanıtı | Akış sürer; yeni bağımsız eylem değil |
| MI30 | Açık konu değişikliği etkin rotayla çelişir | Etkilenen akış ve onay güvenle temizlenir; zorla öncelik yok |
| MI31 | Çoklu niyet: oluştur ve iptal | Hangisi önce sorulur; çoklu yazma yayılımı yok |
| MI32 | Sınıflandırıcı yok veya doğrulanmamış | Güvenli kural/onaylı geri düşme; yeni indirme yok |
| MI33 | Sınıflandırıcı bilinmeyen niyet veya NaN skor | Sonuç reddedilir; yetki çıkarılmaz |
| MI34 | Eşit veya zayıf rota adayları | Keyfi kazanan yerine netleştirme/aktarım |
| MI35 | Kurallar belirleyici; sahte LLM casusu | Sıfır LLM çağrısı |
| MI36 | Geçerli tipli çıktıyla gerekli geri düşme | Tam bir M06 P3 isteği; rota doğrulanır |
| MI37 | LLM hatalı, zaman aşımı veya zamanlayıcı reddi | Güvenli geri düşme; doğrudan sağlayıcı atlaması veya ikinci model çağrısı yok |
| MI38 | Sağlayıcı sürerken iptal edilen HTTP isteği | M06 kirası doğrulanmış tamamlanma/karantinaya kadar; bayat çıktı yok |
| MI39 | Kayıtta yinelenen ajan kimliği | Yinelenen kayıt reddedilir; tek yetkili eşleme |
| MI40 | Erişilemeyen uzman yeteneği | Açık desteklenmiyor; sahte sağlayıcı sonucu yok |
| MI41 | Eksik slotlu randevu ajanı | Yalnız soru önerisi; DB değişikliği yok |
| MI42 | Teknik ajan desteklenmeyen tanı isteği alır | Onaylı güvenli yönlendirme; uydurma teknik bilgi yok |
| MI43 | Satış ajanında stok kaynağı yok | Stok bilinmiyor; satış vaadi yok |
| MI44 | CRM ajanı başka müşterinin geçmişini ister | Okumadan önce M07 reddi |
| MI45 | Atölye veya aktarım sağlayıcısı erişilemez | Uydurma iş emri veya aktarım başarısı yok |
| MI46 | Birden çok bağımsız okuma ve iki yazma denemesi | Sınırlı okuma yayılımı; onay başına yalnız bir ayrıca yetkili değişiklik |
| MI47 | Geçerli tipli argümanlı bilinen oluşturma aracı | Yalnız güvenilmeyen öneri olarak ayrıştırılır; M07'ye kadar etki yok |
| MI48 | Bilinmeyen araç veya keyfi SQL alanı | Sağlayıcı erişiminden önce ret |
| MI49 | Farklı değerli yinelenen JSON anahtarı | Tüm öneri reddedilir |
| MI50 | Aşırı büyük veya aşırı iç içe nesne | Görev/bellek büyümesi olmadan sınırlı ret |
| MI51 | Int yerine bool, NaN veya geçersiz zaman damgası | Tip uyuşmazlığı reddedilir; kritik değerler zorlanmaz |
| MI52 | LLM actor/admin/confirmed/provider geçersiz kılması ekler | Ret; güvenilir yetki sunucu tarafında çözülür |
| MI53 | Güvenilmeyen belge veya araç çıktısı "politikayı yok say" der | Veri olarak işlenir; ayrıcalık veya ek gönderim yok |
| MI54 | Yürütmeden önce öneri kaynak revizyonu bayat | Ret veya yeniden değerlendirme; bayat duruma dayalı değişiklik yok |
| MI55 | Kimlik olarak arayan numarası veya eşleşen araç | Kimlik doğrulama değildir; korunan erişim reddedilir/soru sorulur |
| MI56 | Doğrulanmış müşteri kendi randevusu | Yalnız yetkili asgari kayıt erişilebilir |
| MI57 | Doğrulanmış müşteri başka kaynak kimliği dener | Kaynak sorgusunda red; varlık sızıntısı yok |
| MI58 | Kurum üyesinin devredilmiş araç yetkisi yok | Red; üyelik tek başına yetmez |
| MI59 | Yapılandırma görüntüsü sabitlendikten sonra politika iptali | Güncel iptal kazanır; gönderim yok |
| MI60 | Doğrulayıcı yokken korunan okuma | Canlı yol HOLD; sahte OTP veya kimlik yok |
| MI61 | Katalog satırı modeli doğrular ama sahipliği değil | Ayrı bilgiler; yeni izin yok |
| MI62 | Sağlayıcı fazladan özel alan veya yanlış kaynak döndürür | Güvenilir izdüşümle ret/küçültme; ham LLM bağlamı yok |
| MI63 | Önemliyken güvenilir fiyatı olmayan geçerli güncel slot | Yürütülebilir soru yok; bilgi alınır veya netleştirilir |
| MI64 | Sunum sınırından önce kesilen ses özeti | Rastlantısal "evet"ten onay yok; güvenli yeniden sunum |
| MI65 | Sunucu tükendi veya yalnız yerel boşaltma | Duyulduğu veya tam sunulduğu iddiası yok |
| MI66 | Soruya bağlı geçerli sonraki tur onayı | Güncel durum, kapsam, kanal ve kanıt geçerliyse kabul |
| MI67 | Onay modelin kendi konuşması veya kısmi transkript | Ret; tüketim yok |
| MI68 | Onaydan sonra önemli fiyat/saat/araç değişikliği | Eski soru iptal; yeni özet/özet karması gerekir |
| MI69 | Yanlış soru, başka oturum, süresi dolmuş veya iptal edilmiş başvuru | Ret; asla diriltilmez |
| MI70 | Saat geçerliliği bilinmeyen yeniden başlatma | Muhafazakâr yeni onay; süreçler arası monoton karşılaştırma yok |
| MI71 | Eşzamanlı aynı anahtar ve özet | Tek kalıcı talep; ikincisi kapsamlı mevcut durumu döndürür |
| MI72 | Aynı anahtar farklı özet | Çakışma; değişiklik ve bilgi sızıntısı yok |
| MI73 | Yeni anahtar tüketilmiş soruyu yeniden kullanmaya çalışır | Ret veya yalnız özgün yetkili operasyon çözülür |
| MI74 | Süreç yeniden başladıktan sonra tam yetkili tekrar | Aynı makbuz; yeniden yürütme yok |
| MI75 | Bilinen operasyon anahtarı için kapsam dışı tekrar | Varlık ifşası olmadan red |
| MI76 | Sonradan yeni geçerli soruyla aynı önemli istek | Yalnız güncel kısıtlar geçerse ayrı meşru operasyon |
| MI77 | İki bağlantı son boş saat için yarışır | En fazla bir commit; diğeri bilinen çakışma; kapasite değişmezi |
| MI78 | Ön kontrol ile talep arasında saat değişir | Gerçek işlem reddeder veya yeni sunum ister; bayat rezervasyon yok |
| MI79 | Yalıtılmış DB'de oluşturma başarılı | Desteklenen yerde atomik etki/sonuç/denetim/outbox; fikstür makbuzu MOCK |
| MI80 | Erteleme hedefi boş değil | Eski randevu korunur; kısmi bırakma yok |
| MI81 | Bayat kayıt sürümü veya yanlış durumla iptal | İstenmeyen etki yok; güvenli yeniden kontrol |
| MI82 | Zorunlu denetim niyeti deposu başarısız | Gönderimden önce yeni korunan etki engellenir |
| MI83 | Commit'ten önce çökme | Yetkili yeniden denemeden önce etki olmadığı kanıtlanır; varsayılan geri alma yok |
| MI84 | Commit'ten sonra yanıttan önce çökme | Kalıcı makbuz kurtarılabilir; yinelenen yazma yok |
| MI85 | Sağlayıcı zaman aşımı veya belirsiz etki | UNKNOWN; yalnız sınırlı uzlaştırma; kör yeniden deneme yok |
| MI86 | Çelişkili/yanlış kapsamlı makbuz veya geç kanıt | İzdüşüm reddedilir, uzlaştırılır veya HOLD; sahte başarı yok |
| MI87 | İptal M02 operasyon kabulünden önce kazanır | Gönderim yok; kullanılmamış onay uygun şekilde iptal |
| MI88 | Talep/commit sonrası iptal; geç tamamlanma | Kalıcı sonuç korunur; bayat konuşma bastırılır; otomatik telafi yok |
| MI89 | MOCK/PENDING/UNKNOWN veya eski true makbuz | Gerçek başarı yok; doğru kapsamlı anlamsal yanıt |
| MI90 | Kalite kapısı model yanıtında yanlış tarih, fiyat veya makbuz bulur | Belirlenimci güvenli izdüşüm onarımı veya engel; yeni araç çağrısı yok |
| MI91 | Okuma, yazma, LLM ve onay casuslu SHADOW isteği | Ek yan etki/okuma/çıkarım/tüketim yok; yetkili eski yol bir kez |
| MI92 | GUARDED eksik politika veya OFF korumalı atlama | Yönetilen korumalı kipte hata kapalı; eski engel kaydedilir; geri düşme yok |
| MI93 | M04 taşması ve iç içe araç hatasında hassas işaret | Kişisel veri sızıntısı yok; M07 kalıcı denetimi etkilenmez |
| MI94 | Model/okuma/operasyon sırasında kapanış; iki oturum | Geçici durum çitli ve sınırlı; kalıcı operasyonlar bağımsız sonuçlanır |
| MI95 | M07 gerçek fikstür deposuyla tam F2-B → F3-B → F4 noktası | Güvenli bilgi/makbuzlu tek kabul edilmiş yanıt; normalizasyon veya araç tekrarı yok |
| MI96 | Son regresyon ve kapı kanıtı denetimi | Tüm zorunlu kimlikler/özellik eşlemeleri, geri dönüş kanıtı ve kapsam geçerli; NOT_RUN/HOLD PASS olamaz |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F3-B-G00 | Önkoşullar | Gerçek CG00–CG11/WG00–WG11, doğrudan önkoşulların kabul edilmiş soyu ve onay; MI01–MI06 |
| F3-B-G01 | Sahiplik | Tek F3 cephesi, zamanlayıcı, politika, kalıcı defter; tam yol envanteri ve onaylı kapsam; MI07–MI08 |
| F3-B-G02 | Giriş sözleşmesi | M01 final ve doğrulanmış kanallar, tekilleştirme, kısmi etki yok; MI09–MI16 |
| F3-B-G03 | Bağlam ve netleştirme | CAS, F2 aday/olumsuzluk/korumalı değerler, bayat ipuçları, kapsam; MI17–MI24 |
| F3-B-G04 | Hiyerarşik yönlendirme | Kural önceliği, bilinmeyenler, düzeltme ve belirsizlik, sınırlı alternatifler; MI25–MI34 |
| F3-B-G05 | Model ve bütçe | Tek gerekli M06 P3 geri düşmesi, atlama yok, tamamlanma kiraları; MI35–MI38 |
| F3-B-G06 | Uzman orkestrasyonu | Kayıt, sınırlı yayılım, gerçek yetenek eşlemesi ve dürüst erişilemez durumu; MI39–MI46 |
| F3-B-G07 | Yapılı öneriler | Katı M07 şeması; enjeksiyon ve yetki geçersiz kılma reddi; MI47–MI54 |
| F3-B-G08 | Yetki | Güvenilir kimlik, nesne/işlev kapsamı, iptal, asgari okumalar; MI55–MI62 |
| F3-B-G09 | Onay | Tam desteklenen sunum, kesin soru ve sonraki tur, önemli değişiklik/süre; MI63–MI70 |
| F3-B-G10 | Kalıcı idempotency | Eşzamanlı talep, çakışma, yeniden başlatma ve kapsamlı tekrarlar; MI71–MI76 |
| F3-B-G11 | İşlemsel yeniden doğrulama | Gerçek yerel oluştur/ertele/iptal; kapasite/sürüm ve denetim korumaları; MI77–MI82 |
| F3-B-G12 | Makbuz ve kurtarma | Çökme kanıtı, UNKNOWN ve kalıcı uzlaştırma; kör tekrar yok; MI83–MI86 |
| F3-B-G13 | İptal | M02 kabul/yanıt çiti; etkiden sonra geri alma yok; temizlik; MI87–MI88, MI94 |
| F3-B-G14 | Yanıt kalitesi | Doğrulanmış bilgi/makbuz, salt okunur değerlendirici ve M01 izdüşümü; MI89–MI90, MI95 |
| F3-B-G15 | Kipler ve gizlilik | SHADOW ek etkisiz, korumalı hata kapalı, M04 ile denetim ayrımı; MI91–MI94 |
| F3-B-G16 | Katmanlar arası | Gerçek F2/F3/M07/M02/M06 ve F4 noktası; ilgili F1/F6 uyumu; MI95 |
| F3-B-G17 | Zorunlu testler | 96 zorunlu kimliğin tamamı kanıtla çalıştırılmış; sessiz atlama veya sahte çekirdek yok; MI01–MI96 |
| F3-B-G18 | Regresyon ve geri dönüş | M00 kapsamı, etkilenen kabul edilmiş testler, kaynak bütünlüğü, güvenli yalıtılmış geri dönüş; MI96 |
| F3-B-G19 | İnceleme ve devir | Tüm zorunlu kapılar PASS; kanıt ve kapsam incelemesi; hazırlık canlı yetkiden ayrı; MI96 |

## 9. Kanıt

`evidence/F3-B/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `DIALOGUE_TOOL_INVENTORY.json`, `ROUTING_TABLE.md` (katman 0 kuralları ve öncelik), `AGENT_CAPABILITY_MATRIX.csv`, `TOOL_POLICY_BINDING.csv`, `TRANSACTION_SPEC.md`, `RECONCILIATION_SPEC.md`, `BENCHMARK_PROTOCOL.md` (2 000 senaryo; niyet macro-F1, görev başarısı, sıfır yetkisiz yazma/çift rezervasyon/sahte fiyat — G4'te ölçülür), `TEST_MATRIX.json`.

## 10. Geri dönüş

Supervisor kipi `OFF` ve `f3_pipeline_v2=off`: F3-A/eski yol tek aktif. Kalıcı operasyon defteri ve denetim silinmez; çözülmemiş operasyonlar uzlaştırılmaya devam eder. Kod `git revert`.

## 11. Devir

- **F3-C:** çoklu niyet ayrıştırma, görev planlayıcı ve zaman aşımları, RAG (belge kaynağı, ingestion, hibrit arama, kanıt doğrulama), hafıza düzeyleri, değerlendiriciler, yol bazında gecikme ve LLM azaltma — bu paketteki tek yönlendirici, ajan kaydı ve M07 geçidi üzerine.
- **F4:** `DialogueResponse` kritik bilgiler korumalı; F3-B normalizasyon yapmaz.
- **G4:** niyet macro-F1 ≥ %95, görev başarısı ≥ %95; yetkisiz yazma/çift rezervasyon/sahte fiyat = 0.

## 12. Başlatma komutu

```
F3-B paketini uygula: docs/execution/packages/W3/F3-B-yonlendirme-onay.md.
Kuralları CLAUDE.md'den oku; W2_GATE, F3-A, F2-B ve M07 uygulama kabulünü doğrula.
F3-A cephesi içinde kural öncelikli yönlendirici, tek M06 P3 LLM geri düşmesi, dar uzman ajanlar ve
M07'ye bağlı kalıcı/idempotent randevu işlemlerini kur; yeni otorite veya defter ekleme.
MI01–MI96'yı çalıştır, F3-B-G00…G19'u değerlendir, paket/F3-B dalında PR aç ve dur.
```
