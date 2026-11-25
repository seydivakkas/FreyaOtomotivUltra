# F3-A — Diyalog durumu, slotlar ve korumalı iş akışı

> Mevcut Dialogue/Supervisor davranışını tek bir cephe, tek bir durum sahibi ve M07 geçidi arkasına alır: yalnızca FINAL/OK girdi kabulü, oturum yalıtımlı bağlam, tipli ve revizyonlu slotlar, düzeltmede bağımlı bilgilerin geçersiz kılınması, M06 üzerinden mevcut Qwen yolu, güvenilmeyen öneri doğrulaması, onay sunumu, makbuz/uzlaştırma ve doğrulanmış bilgilerle yanıt oluşturma. Yeni niyet motoru veya yeni araç eklenmez.

| Alan | Değer |
| --- | --- |
| Kimlik | F3-A |
| Dalga | W2 |
| Öncelik | P0 |
| Önkoşullar | CORE_GATE, F2-A, M07 |
| Sonraki | F4-A, W2_GATE, F2-B, F3-B, F1-C |
| Bayrak | `f3_pipeline_v2` (varsayılan kapalı) + M07 Supervisor kipi (`OFF / SHADOW / GUARDED`) |
| Ortam | CPU, geçici DB, sahte LLM ve sahte sağlayıcı |
| Eski görevler | F3-T04, F3-T07, F3-T08, F3-T09, F3-T10, F3-T11 |
| Kaynak | Bundle `W2/Freya_2_0_F3_A_Agent_Implementation_Package.md`; [F3 spec](../../../stages/F3-dialogue-intelligence/spec.md), [F3 tasks](../../../stages/F3-dialogue-intelligence/tasks.md) |
| Durum | NOT_RUN |

## 1. Amaç

Randevu, CRM okuma, kurumsal/çok araçlı akışlar, DTMF, arayan hafızası, operatör aktarımı ve bildirimler bugün farklı yollardan tetikleniyor. Kısmi ASR'nin, eski bir turun veya LLM'in uydurduğu bir fiyatın iş etkisi üretmemesi gerekiyor. F3-A mevcut akışları **koruyarak** M07'nin tek zorlanan yoluna bağlar ve F4'e doğrulanmış, değiştirilemez bir `DialogueResponse` verir.

## 2. Başlamadan önce

- [ ] CORE_GATE, F2-A ve M07 kabul edilmiş; onay var.
- [ ] Diyalog ve etki envanteri çıkarılmış: M00 özellik kimlikleri, gerçek rota/semboller, DB/CRM/DTMF/telefon/sağlayıcı kipleri ve atlama yolları.
- [ ] Eski taban ölçümü (A0, eski F3-T04) yeniden üretilecekse sahte LLM ve 2 000 senaryoluk küme beklenmez; mevcut karakterizasyon testleriyle yapılır.

## 3. Kapsam

**Yapılacak:** Sözleşme eşlemesi; giriş kabulü; bağlam yöneticisi; slot kataloğu ve doğrulama; slot revizyonu ve düzeltme; diyalog durum adaptörü; mevcut Dialogue/Supervisor cephesi; M06 LLM köprüsü; güvenilmeyen öneri doğrulaması; M07 kimlik ve okuma sınırları; onay sunumu ve onayı; mevcut CRM ve randevu adaptörleri; diğer eski kanallar; makbuz ve uzlaştırma; yanıt oluşturucu ve doğrulayıcı; atomik yanıt teslimi; M03/M04; F4 noktası.

**Yapılmayacak:** Katman 0–4 sınıflandırıcı ve kural kapsamı genişletme (F3-B); çoklu niyet, görev planlayıcı, RAG, hafıza düzeyleri (F3-C); yeni araç; gerçek sağlayıcı/SMS/aktarım; F4 normalizasyonu.

## 4. Dosyalar

```
backend/supervisor/dialogue/
  facade.py  admission.py  context.py  slots.py  slot_revision.py  state_adapter.py
  llm_bridge.py  proposal_validation.py  confirmation_presenter.py  crm_adapter.py
  appointment_adapter.py  legacy_channels.py  receipts.py  composer.py
  response_validator.py  delivery.py  telemetry.py
tests/dialogue/
evidence/F3-A/<run_id>/
```

`dialogue.py`, `backend/supervisor/` ve mevcut iş akışı modülleri silinmez; cephe onları sarar. Tek kompozisyon kökü vardır.

## 5. Tasarım ve sözleşmeler

### 5.1 Değişmez kurallar

1. **Girdi:** yalnızca güncel kapsamdaki `FINAL` + `OK` ASR sonucu normal diyaloğa girer. `PARTIAL`/`STABLE_PREFIX` korunan okuma/yazma veya normal diyalog tetiklemez. `NO_SPEECH/ERROR/UNKNOWN/REJECTED` açık OK dışı yollara gider; konuşma uydurulmaz. DTMF ve kimliği doğrulanmış arayüz kendi kanal sözleşmeleriyle gelir; sahte ASR üretilmez.
2. **Bağlam:** oturum enkarnasyonuna yalıtılmış; aynı arayan numarasıyla iki oturum bağımsız; yeniden bağlanma eski geçici durumu veya onayı taşımaz. Anlık görüntü değiştirilemez ve sınırlıdır.
3. **Slotlar:** tipli değer + kaynak + durum + kanıt. M05 eşleşmesi yalnızca adaydır. Plaka/motor kodu/yıl ham haliyle korunur. Tarih/saat enjekte saat ve saat dilimiyle; belirsizse netleştirme sorusu. Tutarlar ondalık, kayan nokta kayması yok, uydurma teklif yok.
4. **Revizyon:** slot güncellemesi karşılaştır-değiştir (CAS) ile; müşteri/kurum değişimi özel bilgileri, araç/hizmet değişimi uygunluk/teklif/onay sorusunu, tarih/saat değişimi onay özetini geçersiz kılar. Kabul edilmiş operasyondan sonra gelen düzeltme yeni bir yetkili istektir; özgün operasyonu sessizce değiştirmez.
5. **Yönlendirme:** mevcut kural/niyet yolu korunur; ikinci motor yok. Kural yanıtı yeterliyse LLM çağrılmaz. `SHADOW`: sıfır ek etki, özel kayıt okuma, onay tüketimi veya canlı LLM çağrısı yok. `GUARDED`'da politika hatası → red/HOLD; korumasız geri düşme yok.
6. **LLM:** mevcut Qwen yolu M06 **P3** işi olarak; doğrudan Ollama atlaması yok. LLM çıktısı güvenilmeyen öneridir: geçersiz JSON/aşırı büyük çıktı/bilinmeyen araç/keyfi SQL reddedilir; "yöneticiyim" gibi enjeksiyon aktörü değiştirmez.
7. **Kimlik ve okuma:** arayan numarası, plaka ve ad tek başına kimlik kanıtı değildir; doğrulama yalnız M07 doğrulama adımıyla [ADR-F3-01](../../../01-architecture/adr/ADR-F3-01-arayan-kimlik-dogrulama.md) yöntemine göre yapılır (doğum yılı, yoksa plaka son 3–4 hanesi). F3-A bu adımı diyalogda başlatır, sonucu yalnız "doğrulandı / doğrulanmadı" olarak görür. Korunan okuma M07 doğrulamasıyla, yalnızca izinli müşteri kaynaklarına; başka müşterinin kaydı varlığı sızdırılmadan reddedilir.
8. **Onay:** etkin bir soru yoksa "evet" onay değildir. Kısmi "evet" veya ilgisiz DTMF onay tüketmez. Sunum kanıtı yoksa (soru duyulmadıysa) HOLD/tekrar. Süresi dolmuş/tekrar oynatılmış onay etkiden önce reddedilir. "Hayır" veya düzeltme kullanılmamış onayı iptal eder.
9. **İşlemler:** mevcut oluştur/ertele/iptal/sorgu/uygunluk davranışı M07 politikasıyla. Son boş saat için eşzamanlı istek → işlem içinde yeniden kontrol, aşırı rezervasyon yok. Aynı anahtar/özet → tek etki; farklı özet → çakışma. Zaman aşımı/bilinmeyen → kalıcı uzlaştırma, yeni anahtarla kör yeniden deneme yok. Zorunlu denetim yoksa yeni etki yok.
10. **Makbuz ve yanıt:** `REAL COMMITTED`, `MOCK COMMITTED`, `UNKNOWN` ve eski `true` makbuzlar farklı şablonlarla yanıtlanır; mock başarı gerçek gibi söylenmez. Aktarım "gönderildi" ≠ "bağlandı"; bildirim "kuyruğa alındı" ≠ "teslim edildi". LLM yanlış fiyat/tarih/rezervasyon numarası söylerse kritik yanıt engellenir veya doğrulanmış şablonla değiştirilir.
11. **Teslim:** yanıt M02 güncel kapsamında atomik kabul edilir; tur değiştiyse geçici durum değişmez ve bayat yanıt teslim edilmez (kalıcı makbuz uzlaştırılır). Teslim hatası aracı yeniden çalıştırmaz.

### 5.2 `DialogueResponse` (F3 → F4)

M01 sözleşmesi aynen: `response_id`, `speech_text` (anlamsal; F4 normalize eder — F3 normalize etmez), `display_text`, `speech_act`, anlamsal etiketli `segments`, `focus_entity_refs`, `verified_fact_refs` (kaynak + revizyon), `state_revision`, `source_asr_revision`, `tool_receipt_refs`, sonuç, hata. Kritik bilgiler (fiyat, tarih/saat, randevu numarası, plaka) doğrulanmış kaynaktan şablonla yazılır ve F4'e korumalı öbek olarak işaretlenir.

### 5.3 Eski kanallar

DTMF yinelemesi en fazla bir mevcut etki; kurumsal/çok araçlı senaryo kapsamlı seçimle; arayan hafızası yalnızca yetkili izdüşüm, yeni kalıcı geçmiş yok; operatör aktarımı ve outbox mevcut davranışıyla, gerçek gönderim yok. Her gözlenen yol sınıflandırılır ve korunur (F3-A-G12).

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F3-A.01 | Çekirdek/F2/M07 ön kontrolü | CG00–CG11 ve doğrudan bağımlılıklar; onaydan önce kaynak değişikliği yok | Ön kontrol kaydı veya HOLD |
| F3-A.02 | Diyalog ve etki envanteri | M00 kimlikleri, rota/semboller, DB/CRM/DTMF/telefon/sağlayıcı kipleri, atlama envanteri | `F3_INVENTORY.json` |
| F3-A.03 | Sahiplik ve geçiş | Tek kompozisyon kökü, durum sahibi, onaylı kapsam; kilit sırası ve geri dönüş | `F3_DECISIONS.md` |
| F3-A.04 | Sözleşme eşlemesi | M01 `ASRResult`/`DialogueResponse`/`VerifiedFactRef`/`ToolReceipt` ve yerel tipli noktalar | DF04 |
| F3-A.05 | Giriş kabulü | Yalnız güncel kapsamda FINAL/OK; tekilleştirme; kanal ayrımı | DF05–DF14 |
| F3-A.06 | Bağlam yöneticisi | Mevcut durum adaptörü, değiştirilemez sınırlı görüntü, özne/oturum yalıtımı | DF15–DF22 |
| F3-A.07 | Slot kataloğu ve doğrulama | Mevcut zorunlu slotlar; tipli değer/kaynak/durum, kanıt, korumalı değerler | DF23–DF28 |
| F3-A.08 | Slot revizyonu ve düzeltme | CAS, önemli değişiklikte geçersizlik, M07 soru/özeti, bağımlı bilgiler | DF29–DF32 |
| F3-A.09 | Diyalog durum adaptörü | Netleştirme, düzeltme, iptal, iş akışı seçimi dahil mevcut geçişler | DF33–DF35 |
| F3-A.10 | Mevcut Dialogue/Supervisor cephesi | Tek yönlendirme, kural yolu, OFF/SHADOW/GUARDED ek etki olmadan | DF36–DF38 |
| F3-A.11 | M06 LLM köprüsü | Mevcut Qwen, P3, kapsamlı iş, sınırlı istek, tamamlanma ve iptal | DF39–DF41 |
| F3-A.12 | Güvenilmeyen öneri doğrulaması | Tipli izin listesi, geçersiz çıktı işleme, model yetkisi yok | DF42–DF44 |
| F3-A.13 | M07 kimlik ve okuma sınırları | Gerçek güvenilir bağlam, kapsamlı arama, güvenli izdüşüm | DF45–DF50 |
| F3-A.14 | Onay sunumu ve onayı | Etkin soru eşleşmesi, yetkili sunum ve final yanıt, belirsiz onay reddi | DF51–DF56 |
| F3-A.15 | Mevcut CRM ve randevu adaptörleri | Oluştur/ertele/iptal/sorgu/uygunluk onaylı politikayla | DF57–DF65 |
| F3-A.16 | Diğer eski kanallar | DTMF, kurumsal/araç, arayan hafızası, operatör aktarımı, outbox | DF66–DF70 |
| F3-A.17 | Makbuz ve uzlaştırma | Sağlayıcı gerçeği, UNKNOWN/PENDING, kalıcı etki ile canlı tur ayrımı | DF71 |
| F3-A.18 | Yanıt oluşturucu ve doğrulayıcı | Anlamsal `speech_text` ve doğrulanmış bilgiler; kritik yanıtlar için belirlenimci şablonlar | DF72–DF73 |
| F3-A.19 | Atomik yanıt teslimi ve temizlik | M02 güncel kapsam, geri basınç, teslim hatasında yeniden yürütme yok | DF74–DF76 |
| F3-A.20 | Yapılandırma ve gözlem | M03 görüntüleri, M04 güvenli metrikler, ayrı M07 denetimi | DF77–DF78 |
| F3-A.21 | F4 ve aşağı akış noktaları | M01 yanıtı, ham anlam; F2-B/F1-C/F3-B/F3-C nokta notları (uygulama yok) | Devir notu |
| F3-A.22 | Belirlenimci testler | DF01–DF80; gerçek temel ve çekirdek, sahte yalnız dış sınırlarda | Tüm testler çalıştırılmış |
| F3-A.23 | Özellik regresyonu ve geri dönüş | M00 korunumu, önceki testler, API/arayüz/DB/yapılandırma uyumu, geri dönüş provası | DF79–DF80 |
| F3-A.24 | Kabul ve devir | F3-A-G00…G19, bağımsız kanıt, açık hazırlık; dur | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| DF01 | Çekirdek kapı veya F2-A/M07 kabul bildirimi yok | Kaynak değişikliğinden önce HOLD |
| DF02 | Bayat/kurcalanmış kabul kanıtı | Ön kontrol reddi; uyuşmayan revizyon/hash belirtilir |
| DF03 | Ağ/model/DB korumalarıyla içe aktarma | İçe aktarmada sağlayıcı yükleme, bağlantı veya işçi yok |
| DF04 | Gerçek kabul edilmiş M01/M02/M07 şemaları | Yinelenen paylaşılan sözleşme veya uyumsuz genel tür yok |
| DF05 | Geçerli kabul edilmiş FINAL/OK söz | Özgün ASR başvurusuyla tam olarak bir rota |
| DF06 | PARTIAL olumlu söz | Korunan okuma/yazma veya normal diyalog gönderimi yok |
| DF07 | STABLE_PREFIX | Aynı yalnız-final sınırı |
| DF08 | FINAL NO_SPEECH, boş ham metin | Normal etki yok; yetkiliyse güvenli yaşam döngüsü/yeniden sorma |
| DF09 | FINAL ERROR/UNKNOWN/REJECTED | Uydurma konuşma yok; açık OK dışı yol |
| DF10 | Güvenilmeyen JSON kabul iddiası | Gerçek üretici/çit kökeni olmadan ret |
| DF11 | Yanlış oturum veya bayat tur | Rota/sağlayıcı çağrısından önce ret |
| DF12 | Yinelenen final, eşzamanlı teslim | Tek talep ve tek rota |
| DF13 | Aynı söz kimliği, farklı içerik | Çakışma; ikinci etki yok |
| DF14 | DTMF/kimliği doğrulanmış arayüz girdisi | Kabul edilmiş ayrı kanal sözleşmesi; uydurma ASR yok |
| DF15 | Aynı arayan numaralı iki oturum | Bağımsız geçici bağlam |
| DF16 | Yeni oturum enkarnasyonuyla yeniden bağlanma | Önceki geçici durum veya onay sızmaz |
| DF17 | Yetkili durum görüntüsü | Değiştirilemez iç içe durum; özgün değişmez |
| DF18 | Aşırı büyük geçmiş / slot verisi | Sınırlı kapasite; açık kırpma veya HOLD; korumalı başvurular korunur |
| DF19 | Aynı beklenen revizyonla eşzamanlı slot güncellemeleri | En fazla bir CAS başarılı; kayıp güncelleme yok |
| DF20 | Bağlam verisi beklenirken iptal | Bayat değişiklik yok; güvenli temizlik |
| DF21 | Aynen tekrarlanan slot güncellemesi | İstenmeyen revizyon/onay çalkantısı yok |
| DF22 | Kapanış ve tekrarlı temizlik | Geçici bağlam bir kez bırakılır; kalıcı kayıtlar korunur |
| DF23 | Bilinmeyen slot anahtarı veya yanlış tür | Ret veya netleştirme; geçerli eyleme zorlama yok |
| DF24 | M05 tam takma ad adayı | Yalnız aday; kimlik/katalog/onay yükseltmesi yok |
| DF25 | Birden çok model adayı | Keyfi seçim yerine netleştirme |
| DF26 | Korumalı plaka/motor kodu/yıl | Kritik ham değerler korunur; fonetik yeniden yazma yok |
| DF27 | Bozuk tarih/saat veya belirsiz göreli tarih | Enjekte saat/saat dilimiyle ret/netleştirme |
| DF28 | Kesin ondalıklı ve para birimli tutar | Kayan nokta kayması yok; uydurma teklif yok |
| DF29 | Müşteri/kurum değişimi | Önceki kapsamlı özel bilgi/slotlar geçersiz |
| DF30 | Seçimden sonra araç/hizmet değişimi | Bağımlı uygunluk/teklif/onay sorusu geçersiz |
| DF31 | Onaydan sonra tarih/saat değişimi | Eski özet geçersiz; yeni onay gerekir |
| DF32 | Kabul edilmiş operasyondan sonra geç düzeltme | Özgün niyete dokunulmaz; ayrı yeni yetkili istek |
| DF33 | Mevcut kural karşılaması veya genel bilgi | Mevcut yetkili yanıt; gereksiz model veya etki yok |
| DF34 | Eski akışta eksik zorunlu randevu slotu | Uygun soru sorulur; etki yok |
| DF35 | Eski düzeltme/geri/iptal akışı | Desteklenen mevcut geçiş; commit edilmiş randevu otomatik iptal edilmez |
| DF36 | Mevcut rota seçimi OFF | Tek yetkili eski yol; dış biçim korunur |
| DF37 | SHADOW karşılaştırması | Sıfır ek etki, özel kayıt okuma, onay tüketimi veya canlı LLM çağrısı |
| DF38 | GUARDED politika hatası | Red/HOLD; korumasız geri düşme yok |
| DF39 | Mevcut zorunlu Qwen dalı | Gerçek M06 P3 işi; doğru tur/model görüntüsü |
| DF40 | M06 kabulü reddedildi/süresi doldu | Güvenli sınırlı yanıt; doğrudan Ollama atlaması yok |
| DF41 | Ollama HTTP iptali, yerel durum bilinmiyor | M06 kirası korunur/karantina; bayat çıktı reddedilir |
| DF42 | LLM geçersiz JSON / aşırı büyük çıktı | Öneri reddedilir; araç etkisi yok |
| DF43 | LLM bilinmeyen araç veya keyfi SQL önerir | Red; dinamik yürütme yok |
| DF44 | İstem enjeksiyonu yönetici/atlama beyan eder | Güvenilir aktör değişmez; yetki yok |
| DF45 | Arayan numarası, plaka ve ad verilir | Kimlik kanıtı değil; korunan okuma reddedilir/soru sorulur |
| DF46 | Geçerli kapsamlı müşteri doğrulaması | Yalnız izinli müşteri kaynakları erişilebilir |
| DF47 | Başka müşterinin randevu/geçmiş isteği | Korunan sağlayıcı okumasından önce red; varlık sızıntısı yok |
| DF48 | Görüntü sabitlendikten sonra yetki iptali | Güncel politika yeni etkiyi engeller |
| DF49 | Doğrulanmış genel uygunluk yanıtı | Gerçek kaynak/revizyon; rezervasyon değildir |
| DF50 | Uygunluk yok / fiyat kaynağı yok | Uydurma saat veya tutar yok |
| DF51 | Etkin soru yokken belirsiz "evet" | Onay veya etki yok |
| DF52 | Kısmi "evet" veya ilgisiz DTMF | Onay tüketilmez |
| DF53 | Eşleşen sunulmuş etkin soru ve geçerli final "evet" | M07 doğrular; yalnız yetkili operasyon ilerleyebilir |
| DF54 | Sunum kanıtı yok/yetersiz | HOLD/tekrar; duyulduğu varsayılmaz |
| DF55 | Süresi dolmuş veya tekrar oynatılmış onay | Etkiden önce red |
| DF56 | Kullanıcı "hayır" der veya bekleyen niyeti düzeltir | Kullanılmamış onay iptal; yazma yok |
| DF57 | Yalıtılmış DB'de mevcut yetkili oluşturma | Tek commit edilmiş satır/makbuz ve doğru yanıt; yalnız fikstür |
| DF58 | Yalıtılmış DB'de mevcut yetkili erteleme | Doğru kapsamlı kayıt, işlem anlamı ve makbuz |
| DF59 | Yalıtılmış DB'de mevcut yetkili iptal | Doğru kapsamlı iptal ve doğrulanmış makbuz |
| DF60 | Son boş saat için eşzamanlı istekler | Kapasite işlem içinde yeniden kontrol; aşırı rezervasyon yok |
| DF61 | Aynı anahtar/özet tekrarı | Tek etki; önceki yetkili makbuz yeniden kullanılır |
| DF62 | Aynı anahtar/farklı operasyon özeti | Çakışma; ek etki yok |
| DF63 | Sağlayıcı zaman aşımı/bilinmiyor veya yeniden başlatma | Kalıcı uzlaştırma; yeni anahtarla kör yeniden deneme yok |
| DF64 | Önce-iptal ile önce-commit-kabulü bariyeri | Doğru sıralama; bayat yanıt yok; kalıcı etki korunur |
| DF65 | Zorunlu denetim erişilemez | Yeni korunan etki yok; M04 gözlemi yerine geçmez |
| DF66 | Mevcut kurumsal/çok araçlı senaryo | Gerçek özellik ve kapsamlı seçim korunur; müşteriler arası veri yok |
| DF67 | Mevcut yinelenen DTMF olayı | En fazla bir kabul edilmiş mevcut etki |
| DF68 | Mevcut arayan hafızası erişimi | Yalnız yetkili izdüşüm; yeni kalıcı geçmiş yok |
| DF69 | Aktarım gönderildi ama bağlanmadı | Başarılı köprü veya duyulan arama iddiası yok |
| DF70 | Bildirim kuyruğa alındı ama teslim edilmedi | Kuyruğa alma ile teslim ayrı; canlı dış gönderim yok |
| DF71 | REAL COMMITTED, MOCK COMMITTED, UNKNOWN ve eski true makbuzlar | Doğru ayrışmış şablonlar; mock başarı gerçek gibi değil |
| DF72 | LLM yanlış fiyat/tarih/rezervasyon numarası söyler | Kritik anlamsal yanıt engellenir/doğrulanmış şablonla değişir |
| DF73 | Sahte F4 tüketicisine geçerli anlamsal yanıt | M01 alanları, kaynak revizyonu, bilgiler/makbuzlar korunur; normalizasyon çağrılmaz |
| DF74 | Tur değiştikten sonra gecikmiş LLM/araç tamamlanması | Geçici değişiklik veya bayat teslim yok; kalıcı makbuz uzlaştırılır |
| DF75 | Yanıt doğrulamasından sonra, kuyruğa eklemeden önce iptal | Atomik M02 kabulü bayat yanıtı engeller |
| DF76 | Dolu/kapalı F4 tüketicisi ve yinelenen geri çağrı | Açık teslim durumu; yinelenen araç yürütmesi veya yanıt teslimi yok |
| DF77 | Girdi, hata ve makbuzda iç içe kişisel veri/gizli bilgi işareti | M04, günlük, kanıt, metrik veya yetkisiz yanıtta sızıntı yok |
| DF78 | Yetkili iş akışında telemetri abonesi hatası | Kontrol/denetim yolları etkilenmez; gözlem kaybı açık |
| DF79 | M00 korunumu, API/arayüz/DB/yapılandırma kontrolleri ve önceki testler | Açıklanamayan regresyon, güvensiz atlama veya izinsiz kaynak farkı yok |
| DF80 | Entegre F2-A fikstürü → gerçek F3-A/M02/M06/M07 → sahte F4; geri dönüş provası | Tek geçerli iş akışı; bayat/yinelenen etki yok; eski kip ve kaynak bütünlüğü korunur |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F3-A-G00 | Ön kontrol | CG00–CG11, F2-A/M07 kabul edilmiş ve uygulanabilir; onay |
| F3-A-G01 | Tek otorite | Tek cephe/durum/geçit otoritesi, güvenli içe aktarma, onaylı kapsam |
| F3-A-G02 | Sözleşme | Gerçek M01 eşlemesi ve değişmemiş genel arayüz |
| F3-A-G03 | Girdi | FINAL/OK kabulü ve ayrı güvenilir ASR dışı kanal yolları; yineleme yok |
| F3-A-G04 | Bağlam | Bağlam kapsamı, sınırlı geçmiş ve temizlik; sıfır oturumlar arası sızıntı |
| F3-A-G05 | Slotlar | Tipli slotlar, köken, CAS ve bağımlı geçersiz kılma |
| F3-A-G06 | Yönlendirme | Mevcut durum/niyet yönlendirmesi korunmuş; ikinci motor yok |
| F3-A-G07 | LLM | M06 üzerinden mevcut Qwen yolu; katı atlama yok; doğru tamamlanma |
| F3-A-G08 | Öneri doğrulama | Katı güvenilmeyen öneri/sonuç doğrulaması |
| F3-A-G09 | Kimlik ve okuma | M07 kimlik ve korunan okuma zorlaması; güncel izin yeniden kontrolü |
| F3-A-G10 | Onay | Soru, sunum, onay ve özet güvenliği |
| F3-A-G11 | İş akışları | Mevcut randevu ve CRM akışları korunmuş ve korumalı; onaysız yeni araç yok |
| F3-A-G12 | Eski kanallar | DTMF/aktarım/outbox/arayan hafızası ve diğer gözlenen yollar sınıflanmış ve korunmuş |
| F3-A-G13 | Makbuz | Doğrulanmış makbuz/uzlaştırma/denetim anlamı; sıfır sahte başarı ve kör bilinmeyen yeniden deneme |
| F3-A-G14 | Yanıt | Değiştirilemez, doğrulanmış bilgiye dayalı `DialogueResponse`; tutarlı kritik bilgiler; F4 normalizasyonu yok |
| F3-A-G15 | Teslim | Atomik yanıt kabulü, bayat sonuç reddi, sınırlı geri basınç ve temizlik |
| F3-A-G16 | Yapılandırma/gözlem | M03/M04 bütünleşmesi; sıfır hassas işaret sızıntısı; denetim ayrı |
| F3-A-G17 | Test kanıtı | DF01–DF80 ve ilgili önceki testler kanıtla geçmiş; zorunlu atlama HOLD |
| F3-A-G18 | Regresyon | M00 özellik regresyonu, uyum ve kapsamlı bütünlük; geri dönüş provası |
| F3-A-G19 | Devir | F4-A ve diğer aşağı akış devirleri incelenmiş; gerçek kabul bağımsız doğrulanmış |

## 9. Kanıt

`evidence/F3-A/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `F3_INVENTORY.json`, `F3_DECISIONS.md`, `SLOT_CATALOG.json`, `CHANNEL_CLASSIFICATION.csv` (her eski kanal: korunuyor / korumalı / engelli), `RESPONSE_TEMPLATES.md` (kritik bilgi şablonları), `TEST_MATRIX.json`. A0 taban ölçümü yapılırsa `data/F3/lab-report-a0-*.json`.

## 10. Geri dönüş

`f3_pipeline_v2=off` ve Supervisor kipi `OFF`: eski diyalog yolu tek aktif. Kalıcı operasyon defteri ve denetim kayıtları silinmez (çözülmemiş operasyonların uzlaştırılması sürer). Kod değişiklikleri `git revert` ile geri alınır.

## 11. Devir

- **F4-A:** `DialogueResponse` anlamsal metin + korumalı kritik bilgi işaretleri; normalizasyon F4'te tek geçiş.
- **F2-B:** diyalog durumu ve beklenen slot türü bağlamsal hotword ve düzeltme için girdi; F3-A bunu yalnızca okunabilir bir arayüz olarak sunar.
- **F3-B:** katman 0–4 yönlendirme, onay soruları ve yazma araçlarının genişletilmesi bu cephenin içine eklenir.
- **F1-C:** slot doluluğu ve diyalog bağlamı anlamsal tur sonu için okunabilir.
- **F3-C:** çoklu niyet, planlayıcı, RAG ve hafıza; bu paketteki tek cephe ve M07 geçidi değişmez.

## 12. Başlatma komutu

```
F3-A paketini uygula: docs/execution/packages/W2/F3-A-diyalog-durumu.md.
Kuralları CLAUDE.md'den oku; CORE_GATE, F2-A ve M07 kabulünü doğrula, tüm etki yollarını envantere al.
Mevcut Dialogue/Supervisor davranışını tek cephe ve M07 geçidi arkasına al (f3_pipeline_v2);
yalnız FINAL/OK girdi, M06 üzerinden Qwen, doğrulanmış bilgilerle yanıt. Yeni araç ekleme.
DF01–DF80'i çalıştır, F3-A-G00…G19'u değerlendir, paket/F3-A dalında PR aç ve dur.
```
