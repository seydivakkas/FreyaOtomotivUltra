# F1-B — İki aşamalı söz kesme (barge-in)

> Freya konuşurken müşteri konuşmaya başlarsa: aday başlangıçta çıkışı **geri alınabilir** biçimde duraklatır (M02 yumuşak duraklatma), F1-A gözlemiyle adayı onaylar veya reddeder; yanlış alarmda aynı generation'ı kaldığı yerden sürdürür, onaylanan kesmede eski generation'ı atomik olarak iptal eder, gönderilmemiş sesi siler, M06 işlerini çitler ve hedefli boşaltma niyeti iletir. Tek karar sahibi; yeni VAD, kuyruk veya sınıflandırıcı yok.

| Alan | Değer |
| --- | --- |
| Kimlik | F1-B |
| Dalga | W3 |
| Öncelik | P0 |
| Önkoşullar | W2_GATE, F1-A, F5-A, F6-A |
| Sonraki | F6-B, F1-C |
| Bayrak | `f1_pipeline_v2` + M03 profili `f1.barge_in` (katı kip açıkça seçilir; varsayılan eski davranış) |
| Ortam | CPU (sahte saat, sahte yerel iş, kaydeden aktarım) |
| Eski görevler | F1-T11, F1-T20, F1-T21, F1-T22 |
| Kaynak | Bundle `W3/Freya_2_0_F1_B_Agent_Implementation_Package.md`; [F1 spec](../../../stages/F1-voice-turn-detection/spec.md) |
| Durum | NOT_RUN |

## 1. Amaç

PoC'ta söz kesme iki aşamalı ama durum ve sahiplik dağınık; yanlış alarm sonrası devam ederken ses tekrarlanabilir veya ani hızlanma (catch-up) olabilir; onaylanan kesmede eski generation'ın sesi sızabilir. F1-B, kararı tek sahibe toplar ve M02/F6/M06 ilkelleriyle **doğrulanabilir** hale getirir. Bağlamsal backchannel ve double-talk sınıflandırması F1-C'dedir.

## 2. Başlamadan önce

- [ ] W2_GATE PASS; F1-A, F5-A, F6-A kabul edilmiş; onay.
- [ ] Tüm aday, VAD, duraklatma, iptal, generation, DTMF, oynatma ve yerel görev yolları (eski ve deneysel bayraklar dahil) kaynak bağlantılı envanterde.
- [ ] F6-A'nın desteklediği boşaltma yeteneği (yerel temizlik / uzak protokol) belgelenmiş; AudioSocket'te doğrulanmış boşaltma yoksa uydurulmaz.

## 3. Kapsam

**Yapılacak:** Karar sahibi ve sahiplik haritası; M01/M02 sözleşme eşlemesi; aday kimliğinin F1-A akışına bağlanması; çıkış uygunluğu; M03 profili; tek deneme yaşam döngüsü; M02 yumuşak duraklatma köprüsü; sınırlı tutma; onay/ret; aynı generation'da devam; F6-A tempo yeniden çapalama; atomik kesin kesme; M06 kuyruk/çalışan iş koordinasyonu; hedefli boşaltma niyeti; zaman aşımı/temizlik; giriş sürekliliği; M07 sınırı; M04; entegrasyon.

**Yapılmayacak:** Olay sınıflandırıcı/backchannel/double-talk (F1-C); yeni oynatma kuyruğu (F6-B); yeni VAD modeli veya eşiği; anlamsal karar; P0 çıkarım özelliği.

## 4. Dosyalar

```
backend/voice_activity/barge_in/
  owner.py  contracts_map.py  candidate_binding.py  eligibility.py  profile.py
  attempt.py  pause_bridge.py  hold.py  decision.py  resume.py  pacing_rebase.py
  commit.py  scheduler_bridge.py  flush.py  timeouts.py  telemetry.py  legacy_bridge.py
tests/voice_activity/barge_in/
evidence/F1-B/<run_id>/
```

## 5. Tasarım ve sözleşmeler

### 5.1 Deneme yaşam döngüsü

```
çıkış etkin + uygun aday (F1-A) ─► ATTEMPT (tek, kimlikli)
   ─► M02 yumuşak duraklatma (generation hedefli, PauseRef yakalanır) ─► PAUSED_HOLDING (sınırlı tutma)
        ├─ F1-A adayı reddeder (son tarihten önce) ─► RESUME: aynı generation + aynı jeton, gönderilmemiş imleçten
        ├─ F1-A başlangıcı onaylar ─► COMMIT: eski generation atomik iptal, duraklatma geçersiz, gönderilmemiş sil,
        │                               M06 işleri çitle, hedefli boşaltma niyeti, yeni giriş korunur
        └─ son tarih / kopma / dönem değişimi ─► ABORT (kontrollü, zaman aşımı nedeni)
```

### 5.2 Kurallar

1. **Uygunluk** yetkili çıkış durumundan: canlı çıkış yoksa duraklatma yok; sentez bekliyor ama oynatma gözlenmemişse onaylı profil uygulanır ama "oynatma başladı" denmez; tamamen tükenmiş çıkış için duraklatma ve tekrar yok; terminal sentez + kalan çalınabilir çerçeveler M02 çıkış kapısına göre. Eski generation'a ait gecikmeli olay yeni generation'ı hedefleyemez. Bilinmeyen hedef veya yanlış giriş dönemi geniş iptal üretmez.
2. **Aday:** F1-A'nın kabul edilmiş akış/dönem/başlangıç ofsetine bağlıdır; ikinci geçmiş veya tur ayrımı yok. Onay F1-A'nın gerçek gözlem sınırıyla (iki yüksek pencere = 64 ms), aynı aday üzerinde; F1-B kendi eşiğini tanımlamaz. Reddedilen aday ASR işi üretmez, sabitlenmiş geçmişi bırakır. Uzak duraklatma onayı beklenmeden yerel kesme yapılabilir.
3. **Duraklatma:** generation/plan/seed değişmez; tur ilerlemez. Yerel gönderim sıralanmadan önce gelen duraklatma yeni gönderimi engeller; önce sıralanmış gönderim "uçuşta olabilir"dir. Bekleyen F5 işi yalnız duraklatma yüzünden iptal edilmez; kira tutulur. Duraklatma sırasında biten F5 sonucu kapasite varsa tam bir kez tutulur, yoksa sınırlı geri basınç veya açık iptal (sessiz kayıp sonra devam yok).
4. **Tutma:** öğe/bayt/süre sınırları tüm tutulan ve uçuştaki sahipleri kapsar; tam medya tamponunda kontrol ve yeni giriş ilerler (kilitlenme yok); tek etkin zamanlayıcı.
5. **Devam:** kesin duraklatma jetonu, canlı durum, son tarih ve sağlam imleçle; geri sarma yok (gönderilmiş 0–1, tutulan 2–4 → 2'den devam, özetler ve sıra eşleşir). F6 yeniden örnekleyici kalanı/DSP durumu değişmez; yeni fade/normalizasyon yok. Uzun duraklatma sonrası tempo kabul edilen sınırdan yeniden çapalanır; yakalama patlaması yok. Duraklatma sırasında başarılı uçuştaki gönderim imleci uzlaştırır; bilinmeyen kısmi yazmada kör yeniden gönderim yok. İptalden sonra devam, yanlış generation/plan/jeton, ikinci duraklatmadan sonra eski jeton (ABA), yinelenen devam reddedilir/idempotenttir.
6. **Kesin kesme:** tek atomik iptal; yalnızca **eski** hedef; çitten sonra eski generation gönderimi sıfır; geç ret kesmeyi geri almaz; çok kaynaktan tekrarlanan kesme tek etki.
7. **M06:** kuyruktaki F5 işi M06 üzerinden iptal (çitten sonra gönderim yok); çalışan DiT/VAE işinin sonucu çitlenir, kira gerçek tamamlanmaya kadar tutulur; F1-B sağlayıcı kirasını kendisi bırakmaz; geç biten eski iş reddedilir, kira bir kez bırakılır; karantina sınırında sahiplik izlenir.
8. **Boşaltma:** hedef kapsamlı tek niyet; yerel temizlik, dış makbuz ve desteklenmeyen/bilinmeyen ayrıdır; AudioSocket'te doğrulanmış boşaltma yoksa uydurma protokol mesajı yok, uzak durum bilinmiyor; geri çağrı hatasında çit kapalı kalır; yeniden kullanılan akışta yeni sesi silmez.
9. **Zaman aşımı:** son tarihte çözülmezse kontrollü iptal (ayrı neden), sentetik başlangıç yok; devam ile zaman aşımı sınırda tek sıralı sonuç; eski zamanlayıcı etkisiz; kopma/dönem değişimi/kapanış denemeyi geçersiz kılar.
10. **Giriş ve iş:** yeni giriş kesme boyunca sürer, F1-A finali bir kez teslim edilir; eski çıkış iptali yeni girişi iptal etmez; DTMF ayrı yol. Commit edilmiş randevu yanıtı kesilirse kalıcı makbuz korunur/uzlaştırılır; geri alma veya ikinci yazma yok; akustik olay onay sayılmaz.
11. **Gözlem:** telemetri kararı kontrol etmez; saatler arası çıkarma yok; duyulan metrik `null` (gerçek uç ölçümü G4/G5).

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F1-B.01 | Ön kontrol | Çekirdek/W2 soyu, F1-A/F5-A/F6-A kabulü, kapsam ve onay | Ön kontrol raporu; eksikse kaynak düzenleme yok |
| F1-B.02 | Envanter | Aday, VAD, duraklatma, iptal, generation, DTMF, oynatma, yerel görev yolları; eski/deneysel bayraklar | Kaynak bağlantılı envanter |
| F1-B.03 | Sahiplik | Tek karar sahibi; M02/F6/M06 sahipliği, kilit sırası, sıralama, kapsam; eski korunur | Karar ve sahiplik haritası |
| F1-B.04 | Sözleşme eşlemesi | M01 `SpeechEvent`/`PlaybackEvent`, M02 `PauseRef`, F1/F5/F6 noktaları; yalnız özel deneme/sonuç kayıtları | BI05–BI06 |
| F1-B.05 | Aday bağlama | F1-A akış/dönem/başlangıç ofseti ve yaşam döngüsü; yinelenen geçmiş veya tur ayrımı yok | BI16–BI24 |
| F1-B.06 | Uygunluk | Yetkili güncel çıkış/generation durumu (kuyrukta/uçuşta/tükenmiş) | BI07–BI14 |
| F1-B.07 | Profil | M03 sabitlenmiş profil, sonlu son tarih/sınırlar, mevcut varsayılanlar, açık katı seçim | BI25–BI27 |
| F1-B.08 | Deneme yaşam döngüsü | Yinelenen/bayat ret, devamdan sonra yeni jeton, sınırlı terminal saklama | BI15 |
| F1-B.09 | Duraklatma köprüsü | Eşleşen generation'la M02 yumuşak duraklatma bir kez; gerçek `PauseRef`; komut ile gözlenen ayrımı | BI28–BI31, BI36 |
| F1-B.10 | Sınırlı tutma | M02/F6-A sahipliği ve kapasitesi; tam tamponda giriş hattı korunur | BI32–BI35 |
| F1-B.11 | Onay/ret | Gerçek F1-A gözlem sınırı ve aynı aday; anlamsal veya P0 çıkarım yok | BI16–BI19, BI23–BI24 |
| F1-B.12 | Devam | Aynı generation; kesin jeton, canlı durum, son tarih, sağlam imleç; geri sarma yok | BI37–BI48 |
| F1-B.13 | Tempo yeniden çapalama | F6-A tempo, DSP/yeniden örnekleyici kalanı ve imleç korunur; yakalama patlaması yok | BI39–BI40 |
| F1-B.14 | Kesin kesme | Yalnız eski çıkışı hedefleyen atomik M02 kesmesi; jeton geçersiz, kabul durur, gönderilmemiş silinir | BI49–BI55 |
| F1-B.15 | M06 koordinasyonu | Kuyruktaki iptal/çalışan tamamlanma ve karantina; F1 sağlayıcı kirası bırakmaz | BI56–BI61 |
| F1-B.16 | Hedefli boşaltma | F6-A'nın desteklenen geri çağrısı; yerel temizlik, dış makbuz, desteklenmeyen/bilinmeyen ayrımı | BI62–BI65 |
| F1-B.17 | Zaman aşımı ve temizlik | M02 son tarih ve sahipliğiyle sınırlı zaman aşımı/aşırı yük/dönem geçersizliği | BI66–BI69 |
| F1-B.18 | Giriş sürekliliği | F1-A giriş, lookback, DTMF ve final `Utterance` devri korunur; reddedilen adayda ASR yok | BI70–BI71 |
| F1-B.19 | M07 sınırı | İşlem/onay/makbuz anlamı; bayat konuşma bastırılır, commit edilmiş etki geri alınmaz | BI72–BI74 |
| F1-B.20 | M04 | Güvenli gözlem ve kapsam/saat politikası; telemetri hatası kararı etkilemez | BI75–BI77 |
| F1-B.21 | Entegrasyon | Gerçek F1-A/F5-A/F6-A ve eski yollar; tek aktif kontrol yolu; yeni kuyruk veya sınıflandırıcı yok | BI78–BI79 |
| F1-B.22 | Testler | BI01–BI80 gerçek kabul edilmiş kodla, onaylı sahtelerle; ilgili önceki regresyon | Tüm testler çalıştırılmış |
| F1-B.23 | Geri dönüş | Yalıtılmış anlık görüntüde kapsamlı geri dönüş provası, bütünlük karşılaştırması | BI80 |
| F1-B.24 | Kabul ve devir | Bağımsız inceleme F1-B-G00…G19; F6-B/F1-C devri; yalnız gerçek PASS'te hazırlık; dur | `decision.json` |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| BI01 | W2 kabul bildirimi yok veya NOT_RUN | HOLD; sıfır kaynak düzenleme/etkinleştirme |
| BI02 | Bayat W2 soyu, bir zorunlu WG kapısı başarısız | Kanıta göre HOLD/FAIL; uygulamaya başlanmaz |
| BI03 | F1-A/F5-A/F6-A kabulü veya sahip yetkisi yok | Yürütme engellenir; çıkarılmış hazırlık yok |
| BI04 | Ağ/model/GPU işaretleriyle incelenmiş modüllerin içe aktarılması | Pasif içe aktarma; servis veya model erişimi yok |
| BI05 | Geçerli M01 `SpeechEvent` ve gerçek M02 `PauseRef` adaptörü | Aynı kimlikler, bilinen kapsam, gerçek köken |
| BI06 | Bilinmeyen enum, bozuk dönem, negatif örnek ofseti veya bool kimlik | Güvenli ret; yan etki yok |
| BI07 | Güncel giriş adayı, canlı bekleyen çıkış yok | Duraklatma yok; normal F1-A yaşam döngüsü |
| BI08 | Canlı kuyruktaki çıkış ve uygun aday | Tek deneme ve tek hedefli duraklatma |
| BI09 | Sentez bekliyor ama oynatma gözlenmedi | Onaylı profil uygulanır; "oynatma başladı" denmez |
| BI10 | Tamamen tükenmiş terminal çıkış | Duraklatma yok; tekrar veya generation dirilmesi yok |
| BI11 | Kalan çalınabilir kuyruk çerçeveli terminal sentez | Gerçek M02 çıkış kapısı uygunluğu; yanlış "tükendi" iddiası yok |
| BI12 | Eski generation için gecikmeli oynatma olayı | Yeni generation hedeflenmez |
| BI13 | Bilinmeyen hedef kimliği veya yanlış giriş dönemi | Geniş iptal yok; güvenli ret |
| BI14 | Aynı dış arayan etiketli eşzamanlı A/B oturumları | Ayrı enkarnasyon/hedef; B etkilenmez |
| BI15 | Duraklatma onayından önce aynı aday tekrarlanır | Tam bir komut; son tarih değişmez |
| BI16 | F1-A 512 örneklik yüksek pencere, sonra düşük skor | Yalnız aday, sonra açık ret; final ASR işi yok |
| BI17 | Önerilen 64 ms fikstüründe iki uygun gerçek pencere | Aynı aday onaylanır; ayrı VAD çıkarımı yok |
| BI18 | Skor eşitliği ve histerezis sınırları | Kabul edilmiş F1-A anlamı aynen; çelişen F1-B eşiği yok |
| BI19 | Geçersiz/sonlu olmayan model gözlemi veya eksik aralık | Sessizlik veya onay değil; açık hata/bilinmiyor |
| BI20 | Kısmi giriş çerçevelerine yayılan aday | Kesin giriş ofseti ve geçmiş; yinelenen pencere yok |
| BI21 | Başlangıçtan önce F1-A lookback işareti | İşaret gerçek mevcut geçmiş içinde bir kez korunur |
| BI22 | Sabitlenmiş geçmişli reddedilen aday | Uygun sabitlemeler bırakılır; ek giriş turu veya ASR isteği yok |
| BI23 | Onaylanan başlangıç uzak duraklatma onayından önce gelir | Hedefin doğru yerel kesmesi; uzak onay gerekmez |
| BI24 | Farklı aday için onay olayı | Güncel denemenin kesme/devamı yok |
| BI25 | Sonlu sınırlar ve saatli geçerli profil | Sabitlenmiş kabul edilmiş politika uygulanır |
| BI26 | Geçersiz son tarih, NaN, pozitif olmayan sınır veya uyumsuz süre | Profil reddedilir; canlı varsayılan değişmez |
| BI27 | Duraklatılmışken profil revizyonu değişir | Deneme eski sabit revizyonu kullanır; zamanlayıcı sıfırlanmaz |
| BI28 | Yerel gönderilmemiş çıkışla yumuşak duraklatma | M02 kapısı kapanır; aynı tur/generation/plan/seed |
| BI29 | Yerel gönderim sıralanmadan önce gönderim ile duraklatma yarışı | Duraklatılan generation için yeni gönderim yok |
| BI30 | Duraklatmadan önce sıralanmış gönderim | Uçuşta/olası işaretlenir; geri çağırma iddiası yok |
| BI31 | Yumuşak duraklatma sırasında bekleyen F5 işi | Yalnız duraklatma yüzünden kesin iptal edilmez; kira tutulur |
| BI32 | Ayrılmış kapasiteyle duraklatma sırasında F5 tamamlanır | Geçerli tutulan gönderilmemiş yük tam bir kez |
| BI33 | Kapasite yokken F5 tamamlanır | Sınırlı geri basınç veya açık iptal; sessiz kayıp sonra devam yok |
| BI34 | Medya tutma öğe/bayt/süre sınırına ulaşır | Gerçek politika tüm tutulan ve uçuştaki sahipleri sınırlar |
| BI35 | Tam medya tamponu, acil kontrol ve taze giriş | Kontrol/giriş kilitlenmeden ilerler |
| BI36 | Yinelenen duraklatma zamanlayıcısı | Tek etkin zamanlayıcı; sınırlı görev sayısı |
| BI37 | Son tarihten önce açık yanlış aday | Aynı etkin generation ve jetonun yerel devamı |
| BI38 | Gönderilen 0–1; tutulan 2–4 | Yalnız 2'den devam; yük özetleri ve sıra eşleşir |
| BI39 | Duraklatılmışken F6 yeniden örnekleyici kalanı/DSP durumu | Tutulan durum değişmez; yeni fade/normalizasyon yok |
| BI40 | Uzun duraklatma sonra devam, gecikmiş eski tempo | Kabul edilen sınırdan yeniden çapalama; yakalama patlaması yok |
| BI41 | Duraklatma sırasında başarılı uçuştaki gönderim tamamlanması | Uzlaştırılmış imleç; tamamlanmış sıranın tekrarı yok |
| BI42 | Duraklatma sırasında bilinmeyen kısmi yazma | Kör yeniden gönderim yok; aktarım politikasına göre açık bilinmiyor/iptal |
| BI43 | İptalden sonra devam denemesi | Ret; iptal edilmiş generation terminal |
| BI44 | Yanlış generation, plan revizyonu veya jeton | Ret; güncel çıkışa dokunulmaz |
| BI45 | Aynı generation'ın ikinci duraklatmasından sonra eski jeton geri çağrısı | ABA devamı yok; yeni jeton güncel kalır |
| BI46 | Yinelenen devam | Tek yetkili kapı geçişi; yinelenen gönderim yok |
| BI47 | Duraklatılmışken hedef tamamen tükenir | Sahte duyulan devam veya tekrar olmadan deneme çözülür |
| BI48 | Yerel komuttan sonra devam geri çağrısı hatası | Açık hata/bilinmiyor ve kontrollü kurtarma/iptal; sahte duyulan durum yok |
| BI49 | Canlı duraklatılmış çıkışla onaylanan güncel aday | Tek atomik iptal, duraklatma geçersiz, sahipli gönderilmemiş silinir |
| BI50 | Yerel duraklatma tamamlanmadan onaylanan başlangıç | Doğrulanmış kesin kesme hedefi yine çitler; çift geçiş yok |
| BI51 | Kesin kesmeden sonra geç aday reddi | İptal edilmiş generation geri alınmaz |
| BI52 | Birden çok geri çağrıdan tekrarlanan kesme | Tek etki ve idempotent sonuç |
| BI53 | Eski kesme geri çağrısından önce yeni generation oluşturulur | Yalnız eski hedef; yeni generation asla iptal/boşaltılmaz |
| BI54 | Atomik gönderimden önce bariyer, kesme kazanır | Çitten sonra sıfır eski generation gönderimi |
| BI55 | Gönderimden sonra bariyer kazanır, sonra kesme | Önceki uçuştaki açıkça olası; sonraki gönderimler engellenir |
| BI56 | Kesin kesmede kuyruktaki F5 işi | Gerçek M06 üzerinden iptal; çitten sonra gönderim yok |
| BI57 | Kesmede çalışan yerel DiT/VAE işi | Sonuç çitlenir; kira gerçek tamamlanmaya kadar tutulur |
| BI58 | Yerel future iptal edildi ama işçi hâlâ aktif | Erken kira bırakma veya model boşaltma yok |
| BI59 | Yeni generation'dan sonra geç biten yerel iş | Eski çıktı reddedilir; gerçek kira bir kez bırakılır |
| BI60 | Yinelenen yerel tamamlanma / istisna | Defter negatif değil; çift bırakma yok |
| BI61 | Yerel tamamlanma bilinmiyor ve karantina sınırı dolu | Sahiplik izlenir; sınırlı ret; sahte geri alım yok |
| BI62 | Boşaltma niyeti geri çağrısı yerelde başarılı | Tek hedefli niyet; uydurma uç onayı yok |
| BI63 | AudioSocket'te doğrulanmış boşaltma yeteneği yok | Uydurma protokol mesajı yok; uzak durum bilinmiyor |
| BI64 | Boşaltma geri çağrısı hata fırlatır veya gecikmiş onay gelir | Çit kapalı kalır; güvenli kapsam/neden; dirilme yok |
| BI65 | Bayat boşaltma, yeni generation için yeniden kullanılan akışı hedefler | Güvensiz etki bastırılır; yeni ses silinmez |
| BI66 | Sahte saat çözülmeden son tarihe ulaşır | Hedefin kontrollü iptali, ayrı zaman aşımı nedeni; sentetik başlangıç yok |
| BI67 | Sınırda devam ve zaman aşımı, iki olay sırası | Tek sıralı sonuç; süresi dolmuş jeton yeniden açamaz |
| BI68 | Son tarihten önce açık ret ve sonra eski zamanlayıcı | Devam bir kez başarılı; bayat zamanlayıcı etkisiz |
| BI69 | Duraklatılmışken kopma, biçim dönemi değişimi veya oturum kapanışı | Deneme geçersiz; sahte akustik sessizlik yok, geç devam yok |
| BI70 | Giriş kesin kesme ve endpoint boyunca sürer | F1-A final `Utterance` bir kez teslim; eski çıkış iptali yeni girişi iptal etmez |
| BI71 | Duraklatma/tam tampon sırasında DTMF | Mevcut ayrı yol ve yetkili davranış korunur; yinelenen rakam veya uydurma VAD yok |
| BI72 | M07 commit edilmiş randevu, konuşma yanıtı kesilir | Kalıcı makbuz korunur/uzlaştırılır; geri alma veya ikinci yazma yok |
| BI73 | M07 commit kabulünden önce iptal / bilinmeyen sağlayıcı | Yetkili M07 sonucuna uyulur; tahmini ret/başarı veya kör yeniden deneme yok |
| BI74 | Onay sorusu sırasında aday, final rıza yok | Akustik olaya dayalı işlem yok; sorunun duyulduğu varsayılmaz |
| BI75 | M04 kuyruğu dolu / abone hata fırlatır | Kontrol tam bir kez ilerler; güvenli düşürme sayımı |
| BI76 | Ses/metin/sağlayıcı istisnasında gizlilik işaretleri | Olay/rapor/günlükte ham yük veya kişisel veri yok |
| BI77 | Saatler arası istemci onayı ve sunucu iptali | Geçersiz zaman çıkarması yok; duyulan metrik null |
| BI78 | Gerçek entegre F1-A → F1-B → M02/M06/F5-A/F6-A, sahte yerel sınırlar | Yanlış duraklatma/devam ve onaylı kesme yolları gerçek kodu kanıtlar; ikinci otorite yok |
| BI79 | Eski/katı/gölge yol tekrarı, özellik kimlikleri, mevcut genel protokol | Meşru eski davranışlar korunur; gölge ek etkisiz; istenmeyen varsayılan değişimi yok |
| BI80 | Yalıtılmış geri dönüş, kanıt bildirimi ve eksik testle kapı değerlendirmesi | Önceki durum yeniden üretilebilir; eksik/sahte kanıtla PASS yok; kaynak bütünlüğü |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F1-B-G00 | Ön kontrol | Gerçek çekirdek ve W2 kabulü, F1-A/F5-A/F6-A bağımlılıkları, onay ve uyumlu soy; BI01–BI04 |
| F1-B-G01 | Tek sahip | Tek kesme karar sahibi; genel protokoller değişmez; ikinci VAD/çalışma zamanı/kuyruk/zamanlayıcı yok; BI04, BI78–BI79 |
| F1-B-G02 | Sözleşme | M01/M02 kimlik ve özel sözleşme eşlemesi; uydurma kimlik/kapsam yok; BI05–BI06, BI13–BI15 |
| F1-B-G03 | Uygunluk | Yetkili çıkış uygunluğu; terminal sentez ile tükenme ayrımı; bayat hedef yok; BI07–BI14 |
| F1-B-G04 | Aday | Gerçek F1-A iki aşamalı aday/başlangıç/ret noktası, lookback, spekülatif tur yok; BI16–BI24 |
| F1-B-G05 | Profil | Kabul edilmiş profil sabitleme, sonlu sınır/son tarih; sessiz varsayılan yok; BI25–BI27 |
| F1-B-G06 | Duraklatma | M02 geri alınabilir kapı, duraklatma jetonu ve atomik gönderim sınırı; generation/seed değişmez; BI28–BI31, BI36 |
| F1-B-G07 | Tutma | Sınırlı tutma/geri basınç ve giriş/kontrol ilerlemesi; sessiz süreklilik kaybı yok; BI32–BI35 |
| F1-B-G08 | Devam | Aynı generation devamı, kesin gönderilmemiş imleç, tekrar yok, durum ve tempo korunur; BI37–BI48 |
| F1-B-G09 | Kesin kesme | Atomik ve geri alınamaz; çitten sonra eski gönderim yok; BI49–BI55 |
| F1-B-G10 | M06 | Kuyrukta/çalışan ayrımı, yerel tamamlanma ve kira sahipliği; BI56–BI61 |
| F1-B-G11 | Boşaltma | Hedefli niyet, gerçek yetenek; uzak/duyulan iddia veya generation'lar arası silme yok; BI62–BI65 |
| F1-B-G12 | Zaman aşımı | Belirlenimci yarışlarla sınırlı zaman aşımı/temizlik/dönem işleme; BI66–BI69 |
| F1-B-G13 | Giriş | Yeni giriş, F1-A final devri ve ham DTMF bağımsız; BI20–BI22, BI70–BI71 |
| F1-B-G14 | M07 | M07 etkileri ve onay sınırı korunmuş; BI72–BI74 |
| F1-B-G15 | Gözlem | Güvenli M04 gözlemi; kontrol bağımlılığı, saatler arası veya duyulan uydurma yok; BI75–BI77 |
| F1-B-G16 | Entegrasyon | Gerçek entegre F1/F5/F6 ve M02/M06 kodu; eski/katı/gölge uyumu; BI78–BI79 |
| F1-B-G17 | Test kanıtı | 80 BI vakası gerçek gözlenmiş PASS ve ilgili önceki testler kabul; sahte otorite yok |
| F1-B-G18 | Bütünlük | M00 özellik kapsamı, kaynak bütünlüğü, güvenli geri dönüş provası, bağımsız inceleme; BI80 |
| F1-B-G19 | Devir | Tam F6-B ve F1-C devri; ertelenen uzak ve donanım metrikleri açık; gerçek kanıt ve engeller |

## 9. Kanıt

`evidence/F1-B/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `BARGE_IN_INVENTORY.json`, `OWNERSHIP_MAP.md`, `ATTEMPT_TRANSITION_MATRIX.csv`, `RESUME_CURSOR_EVIDENCE.json`, `FLUSH_CAPABILITY.md`, `TEST_MATRIX.json`. Yanlış söz kesme oranı ve duyulan kesme süresi bu pakette ölçülmez (G4/G5).

## 10. Geri dönüş

M03 profili `f1.barge_in` eski kipe alınır: mevcut iki aşamalı kesme davranışı tek aktif. Kod değişiklikleri `git revert`; kalıcı iş kayıtlarına dokunulmaz.

## 11. Devir

- **F6-B:** oynatma kuyruğu, söz kesme köprüsü ve tarayıcı makbuzları; F1-B'nin hedefli boşaltma niyeti ve uçuşta ayrımı girdi.
- **F1-C:** olay sınıflandırıcı, backchannel, double-talk; F1-B kararı F1-C'nin sınıflandırmasıyla zenginleşir ama sahip değişmez.
- **G4/G5:** yanlış kesme ≤ %2 ve duyulan kesme p95 ≤ 200 ms yalnızca gerçek uç ölçümüyle.

## 12. Başlatma komutu

```
F1-B paketini uygula: docs/execution/packages/W3/F1-B-soz-kesme.md.
Kuralları CLAUDE.md'den oku; W2_GATE ve F1-A/F5-A/F6-A kabulünü doğrula.
İki aşamalı söz kesmeyi tek karar sahibiyle kur: M02 yumuşak duraklatma, aynı generation'da devam,
atomik kesin kesme, M06 çiti, hedefli boşaltma niyeti. Yeni VAD veya kuyruk ekleme.
BI01–BI80'i çalıştır, F1-B-G00…G19'u değerlendir, paket/F1-B dalında PR aç ve dur.
```
