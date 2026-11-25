# M02 — Oturum ve iptal çalışma zamanı

> Her görüşme için tek bir oturum bağlamı; tur ve generation numaralarının tekdüze tahsisi; hiyerarşik iptal; eski sonuçların içeri girmesini engelleyen kabul çitleri; sınırlı tampon sahipliği ve güvenli kapanış. Mevcut web/telefon davranışı değişmez.

| Alan | Değer |
| --- | --- |
| Kimlik | M02 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M01 |
| Sonraki | M04, M06, M07, M08, CORE_GATE, F0-A, F1-A, F6-A |
| Bayrak | Yok — yeni çalışma zamanı eklemeli; eski yol varsayılan kalır, canlı bağlantı yalnızca incelenmiş dar noktalarda |
| Ortam | CPU |
| Eski görevler | CC-T01, CC-T02 |
| Kaynak | Bundle `W1/Freya_2_0_M02_Agent_Implementation_Package.md`; [session-and-state](../../../cross-cutting/session-and-state.md) |
| Durum | NOT_RUN |

## 1. Amaç

Bugün PoC'ta tur ve generation tek bir sayaçta birleşik; iptal edilen işler GPU'da sürüyor; bir görüşme diğerinin durumunu etkileyebiliyor. M02, oturum başına tek ve yetkili bir yaşam döngüsü kurar: tur/generation tahsisi, iptal kapsamları, sonuç kabul çitleri, kaynak sahipliği ve kapanış. F0–F6 paketleri bu çalışma zamanını kullanır.

## 2. Başlamadan önce

- [ ] M01 kabul edilmiş (`m02_ready: true`); `M02_HANDOFF.md` okunmuş.
- [ ] M01 türleri (`SessionIdentity`, `TurnRef`, `GenerationRef`, `StreamRef`, `CancellationReference`, `EventEnvelope`, `SpeechEvent`, `AudioChunk`, `PlaybackEvent`) gerçek içe aktarma yollarıyla kullanılacak; **kopyalanmaz**.
- [ ] Mevcut tüm yaşam döngüsü giriş noktaları izlenmiş: web gelen/giden, AudioSocket, operatör devri, AMI/ARI sahte yolları, oturum kaydı, model çağrıları, oynatma/gönderme/boşaltma geri çağrıları, kapanış/`finally` yolları, görev oluşturma, kuyruk sahipliği, iş parçacığı/yürütücü sınırları. (Aday dosyalar: `session.py`, `audio.py`, `audiosocket_server.py`, `models.py`, `batched_ode.py`, `telephony.py`, `supervisor/`, `caller_memory.py`.)
- [ ] Var olan her tur/generation sayacı ve durdurma sinyali ile onu kimin tükettiği kayıtlı. Güvenle çitlenemeyen canlı yol eski halinde bırakılır ve HOLD olarak işaretlenir; sessizce kapatılmaz.

## 3. Kapsam

**Yapılacak:** Oturum bağlamı ve kaydı, yaşam döngüsü, tur ve generation yöneticileri, iptal hiyerarşisi, atomik sonuç kabulü, görev kaydı, tampon/kira sahipliği, duraklat/devam/kesinleştir ilkelleri, son tarihler ve sahte saat, kapanış ve ertelenmiş temizlik, eski koda dar adaptörler, yarış testleri.

**Yapılmayacak:** Olay yolu (M04), GPU kabulü (M06), yapılandırma kaydı (M03), politika motoru (M07), DSP/kodek/model algoritmaları, arayüz. Yeni bir hattın varsayılan olarak açılması. İş mantığı, modeller, frontend, veritabanı şeması, bağımlılıklar.

## 4. Dosyalar

```
backend/core/runtime/
  session_context.py   session_registry.py   lifecycle.py
  turn_manager.py      generation_manager.py cancellation.py
  result_admission.py  task_registry.py      buffer_registry.py
  pause_controller.py  deadlines.py          resource_ledger.py
  cleanup.py           runtime_events.py     legacy_bridge.py
tests/runtime/   tests/integration/ (dar)   tests/regression/ (dar)
evidence/M02/<run_id>/
```

Mevcut oturum/aktarım modülleri yalnızca M00'da bulunan kesin noktalarda (oturum kaydı/kapanışı, başvuru taşıma, tamamlama çiti, geri çağrı uyarlama) ve önceden yazılmış değişiklik listesiyle düzenlenir. Eşdeğer modül varsa tek tanım tercih edilir; dosya sayısı şişirilmez.

## 5. Tasarım ve sözleşmeler

### 5.1 Değişmez kurallar

1. **Tek yetkili bağlam.** Mantıksal oturum başına tek canlı bağlam. Aktarım bağlantısı kimliği, mantıksal oturum ve müşteri kimliği ayrıdır. Telefon numarası veya ad yeni kimlik olarak kullanılmaz. Yeniden kullanılan dış kimlik eski görevleri, durumu, iptali veya oynatmayı devralamaz: her açılış yeni bir **oturum enkarnasyonu**dur.
2. **Oturuma yerel değiştirilebilir durum:** görev tutamaçları, kuyruklar, tur/generation sayaçları, jetonlar, akış/biçim dönemleri, tampon kiraları, oynatma durumu, son tarihler. Paylaşılan model nesneleri küresel kalabilir; modelin içindeki değiştirilebilir çıkarım durumunun (ör. VAD) yalıtımı F1'in işidir. Oturum başına model kopyası yok.
3. **Tek serileştirme otoritesi.** Değiştirilebilir oturum durumu tek sahipte (genellikle sahip olay döngüsü + kısa kilit veya aktör posta kutusu). İş parçacığı/yürütücü geri çağrıları güvenli ilkellerle sahibe aktarılır. Durum kilidi tutulurken model, aktarım, DB veya kullanıcı geri çağrısı beklenmez. Kilit sırası belgelenir; kayıt kilidi tutulurken oturum kilidi alınmaz.
4. **Tekdüze kimlikler.** Tur ve generation kimlikleri enkarnasyon içinde artarak tahsis edilir; geri dönmez, sıfırlanmaz, yeniden kullanılmaz. Sayaçlar ayrıdır; bir turda birden fazla generation olabilir; başlangıçta oturum başına en fazla bir konuşulabilir aktif generation. **Yeni tur, diyalog düzeyinde kabul edilmiş giriş sınırıdır** — her VAD çerçevesi veya kısmi transkript değil. Spekülatif söz kesme tur ilerletmez.
5. **Katı yolda çit.** Bilinmeyen kimlik, yanlış oturum, eski tur, iptal edilmiş veya aktif olmayan generation, yanlış plan revizyonu/parça veya kapalı oturum teslim sınırına giremez. Eski kod adaptörü "mevcut değil" üst verisi döndürüp eski yolda kalabilir; kimlik uydurmaz.
6. **İptal işbirlikçi ve kapsamı için kesindir;** geri dönüş yoktur. Oturum iptali alt tur/generation/işlere yayılır; tur iptali kendi altına; generation iptali ilgisiz girişi veya tüm görüşmeyi iptal etmez. Kuyruktaki yerel işler çıkarılabilir; çalışan yerel CUDA/CTranslate2/Ollama işi hemen durmayabilir: mantıksal teslim hemen çitlenir, fiziksel durdurma yalnızca desteklenirse istenir, gerçek tamamlanma ayrıca raporlanır. İş gerçekten bitmeden kaynak kirası bırakılmaz.
7. **Kabul ve iptal aynı noktada serileşir.** "Kontrol et, sonra bekleyip koy" güvensizdir. Sahip otoritesi altında bloklamayan sınırlı kuyruğa ekleme veya rezervasyon + yeniden kontrol + açık iptal. Beklemeler kilit dışında, sonra yeniden kontrol. Kuyruktan çekişte, gönderimde, her asenkron sınırdan sonra ve aktarım yazmasında tekrar kontrol. Yazma zaten gönderildiyse "uçuşta / teslim edilmiş olabilir" kaydı; geri çağırma iddiası yok.
8. **Yumuşak duraklatma iptal değildir.** Aktif generation'ın çıkışını geri alınabilir biçimde kapatır; yalnızca sınırlı gelecek sesi tutar; gönderilmiş sesi geri sarmaz. Devam yalnızca aynı duraklatma dönemi/jetonu ve aynı canlı generation için. Kesinleştirme atomik olarak eski generation'ı iptal eder, duraklatmayı geçersiz kılar, yerel kuyruğu boşaltır, iptal/boşaltma isteğini yayar. Tekrarlanan/bayat komutlar idempotent veya reddedilir. Akustik/onay sesi kararı F1'in, aktarım düzeyi eylem F6'nındır; M02 ilkelleri sağlar.
9. **Hesaplama iptali, işlem geri alma değildir.** Commit edilmiş bir iş işlemi iptalle geri alınmaz. Uçuştaki/bilinmeyen işlem M01 `ToolReceipt` anlamıyla izlenir; bilinmeyen sonuç M07/F3 uzlaştırmasına gider. Kör yeniden oynatma yok. Kısmi/kararlı ASR iş işlemini yetkilendiremez.
10. **Kapanış idempotent ve süreli.** `CLOSING` başlayınca yeni kabuller reddedilir. Görev/kira temizliği ve bağlantı kesme bir kez yapılır; bitmeyen iş için zaman aşımı/karantina durumu. Mantıksal `CLOSED` ile kaynakların tamamen geri alınması ayrıdır. Geç gelen geri çağrı oturumu yeniden açamaz. Karantina bütçesi sınırlıdır; dolunca kabul açıkça reddedilir/düşürülür.
11. **Tampon sınırları açık:** öğe, örnek/bayt ve süre olarak. Paylaşılan yazılabilir NumPy takma adı yok. Örnek sırası, biçim ve ham DTMF yolu korunur. Kuyruk taşması rastgele ses atmaz ve sınırsız büyümez: tipli kabul sonucu, sınırlı bekleme, açık boşluk/aşırı yük veya kontrollü hata.
12. **Saat:** enjekte edilebilir monoton saat ve açık son tarih bütçeleri; duvar saati yalnızca kanıt için. Makineler arası çıkarma yok. Son tarih, müşterinin duyduğu gecikme değildir.
13. İçe aktarma sırasında görev/iş parçacığı/model/DB/ağ başlatılmaz; açık başlatma ve kapatma. M04 için yalnızca pasif olay alıcı arayüzü (no-op).
14. Eski genel davranış ve bayraklar korunur. Gölge gözlemci yazma yapamaz veya sentezi çoğaltamaz. Sahte çit testlerinden canlı F0–F6 iptal garantisi iddia edilmez.

### 5.2 Yaşam döngüsü

| Şimdiki | Olay | Sonraki | Kısıt |
| --- | --- | --- | --- |
| NEW | kaynakları hazırla | OPENING | teslim yok |
| OPENING | hazır | ACTIVE | yalnızca gerekli yerel kurulum başarılıysa |
| OPENING | hata / bağlantı koptu | CLOSING | kısmen alınmış kaynaklar temizlenir |
| ACTIVE | kapat / ölümcül hata / bağlantı koptu | CLOSING | yeni kabuller atomik olarak kapatılır |
| CLOSING | yerel kapanış bitti | CLOSED | bekleyen yerel/aktarım geri alımı ayrıca raporlanır |
| CLOSED | herhangi bir geç olay | CLOSED | reddedilir; yeniden açılma yok |

NEW, hazırlanmadan CLOSING üzerinden kapanabilir. Yeniden bağlanma yeni enkarnasyondur (`CLOSED → ACTIVE` yok). Oturum yaşam döngüsü, tur durumu (`OPEN/FINALIZING/COMPLETE/CANCELED`), generation durumu (`ACTIVE/COMPLETED/CANCELED/FAILED`) ve oynatma kapısı (`RUNNING/SOFT_PAUSED`) ayrı tutulur; tek bir enum'a sıkıştırılmaz. Generation `COMPLETE` yeni parça kabul etmez; kabul edilmiş yerel ses yalnızca generation teslim yetkisini koruduğu sürece akar.

### 5.3 Tur ve generation kuralları

- `begin_turn`: kabul edilmiş giriş veya açık diyalog sınırında (DTMF dahil) çağrılır; sayacı atomik artırır, değiştirilemez `TurnRef` döndürür. Gerçekten yeni bir tur eski turu geçersiz kılınca eski teslim edilebilir çıktı iptal edilir.
- `begin_generation(turn_ref, plan_id/revision)`: canlı tur, geçerli kimlik ve onaylı plan başvurusu ister. Sayaç turlar arası tekdüze; yeniden denemede kimlik yeniden kullanılmaz. Yeni generation öncekini atomik olarak geçersiz kılar. Duyulmuş kısmi çıktıdan sonra yeniden deneme eklenmez. M02 seed değiştirmez, ses üretmez.
- Kısmi STT geri çağrıları tur/söz/revizyon taşır; FINAL'den sonra gelen geç revizyon kabul edilmiş finali geçersiz kılamaz. F3 işlem makbuzları (commit/bilinmiyor) "yan etkisi yokmuş" gibi atılmaz, uzlaştırılır.

### 5.4 İptal hiyerarşisi

```
Oturum kapsamı (kök)
  Tur kapsamı
    Tanıma / diyalog işleri
    Generation kapsamı
      Sentez / kalite işleri
      Yerel oynatma gönderimleri
```

`CancellationReference` M01'in değiştirilemez başvurusudur; `CancellationToken`/`Scope` çalışma zamanı durumudur (`request_cancel(reason)`, `is_cancel_requested`, `wait_cancelled`, `check_active`, `child_scope`). İlk etkili neden ve zaman değişmez; sonraki tekrar nedenler yalnızca denetim kaydıdır. İptal edilmiş üst kapsamdan sonra kaydolan alt kapsam hemen iptal edilir.

### 5.5 Sonuç kabul protokolü

Tipli sonuçlar: `ACCEPTED`, `STALE_SESSION`, `STALE_TURN`, `STALE_GENERATION`, `CANCELED`, `PAUSED`, `CLOSED`, `REVISION_MISMATCH`, `DUPLICATE`, `OUT_OF_ORDER`, `BACKPRESSURE`, `INVALID`, `DEADLINE_EXCEEDED`.

```python
async def admit_local(result, scope):
    async with scope.owner_lock:
        decision = validate_identity_state_revision_deadline(result, scope)
        if decision != ACCEPTED:
            return decision
        if not bounded_queue.can_reserve(result.size):
            return BACKPRESSURE
        bounded_queue.commit_nowait(result)   # aynı serileştirme alanında
        return ACCEPTED
```

| Yarış | Zorunlu sonuç |
| --- | --- |
| Kuyruğa eklemeden önce iptal | Eklenmez |
| Eklemeden sonra iptal | Eşleşen yerel kuyruk öğesi silinir; çekişte yeniden kontrol |
| Kapasite beklerken iptal | Uyandır/reddet; rezervasyon sızıntısı yok |
| Çekişten sonra, gönderimden önce iptal | Gönderim yapılmaz |
| Gönderimden sonra iptal | "Uçuşta / teslim edilmiş olabilir"; geri çağırma iddiası yok |
| Yerel çıkarım iptalden sonra biter | Çıktı kabul edilmez; kira gerçek bitişte bırakılır |
| Aynı dış kimlikle yeni oturum | Eski geri çağrı enkarnasyon kontrolünde reddedilir |
| Yeni turdan sonra eski F3 yanıtı | Bayat yanıt yok; işlem makbuzu uzlaştırması korunur |

### 5.6 Kaynak sınırları ve temizlik

- Oturum başına ve küresel öğe/bayt/süre bütçeleri, görev üst sınırı, kapanış bekleme süresi ve karantina üst sınırı politika girdileridir. Gerçek varsayılanlar M00'daki mevcut sınırlardan veya açıkça yalıtılmış test profillerinden gelir (test örneği: 8 kHz PCM16 20 ms için 3 çerçeve / 960 bayt, 2 açık görev — üretim önerisi değildir). "50 eşzamanlı çağrı" ayarı kapasite iddiası değildir.
- Kapanış: atomik `CLOSING`, kabulleri kapat, görevlerin/kaynakların anlık görüntüsü; dış geri çağrılar kilit dışında; iptal niyeti; yeni girişi ayır; yerel kuyruğu boşalt; yalnızca güvenli kiraları bırak; işbirlikçi görevleri süreli bekle.
- `ResourceLedger`: sahipli, ödünç, uçuşta, bırakma istendi, bırakıldı, karantinada. Bir kapanış geri çağrısının hatası diğerlerini engellemez.
- Bitmeyen yerel iş: güçlü başvuruyla ertelenmiş temizlik defterinde tutulur, kira korunur, durum `PENDING_RECLAIM`; gerçek bitişte istisna gözlenir ve kira bırakılır.
- Paylaşılan model tutamaçları ödünçtür: bir görüşmenin kapanması Whisper/Ollama/FreyaTTS'i boşaltamaz veya başka görüşmeyi durduramaz.

### 5.7 Eski kodla bütünleşme

| Mevcut sınır (M00'da doğrula) | M02 uyarlaması | Korunacak |
| --- | --- | --- |
| Web oturumu açma/kapama | Çalışma zamanı bağlam adaptörü | WS şemaları, arayüz kontrolleri, bilet akışı |
| AudioSocket UUID / kapanış | Kapsamlı eşleme ve kapanış | İkili başlık, PCM16, DTMF, kapatma |
| `VoiceSession` | Yeniden kullan veya dar cephe; ikinci canlı kayıt yok | Mevcut tüm tur/diyalog/sentez yolları |
| STT ve LLM yürütücü tamamlanması | Başvuru yakalama ve korumalı geri çağrı | Model tekilliği, çıktılar, varsayılan kip |
| Toplu ODE/TTS tamamlanması | Generation çiti ve izlenen iş kirası | Seed, önbellek, yığın algoritması |
| Oynatma kuyruğu/gönderim | Kabul noktası ve yerel çit | Zamanlama/kodek/aktarım; açık uçuş sınırı |
| Supervisor ve CRM | Makbuz üst verisi / iptal ayrımı | Onay, idempotency, commit edilmiş yazmalar |
| Operatör devri / DTMF | Yaşam döngüsü geri çağrısı veya kontrol hattı | Mevcut davranış; gerçek çağrı/aktarım yok |

Yalnızca incelenmiş güvenli sınırlar taşınır. Gerçekten bağlanmamış ve test edilmemiş üretim yolları için "korumalı" iddiası yapılmaz.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M02.01 | Ön kontrol ve kanıt doğrulama | Kabul edilmiş M00/M01 başvuruları, bütünlük, kapsam, engeller | Ön kontrol kaydı veya HOLD |
| M02.02 | Çalışma zamanı sahiplik envanteri | Gerçek oturum, sayaçlar, görevler, tamponlar, geri çağrılar, iptal yolları, özellik kimlikleri | `RUNTIME_INVENTORY.json` |
| M02.03 | Eşzamanlılık ve uyum tasarımı | Karar kaydı; sahip döngü/kilit politikası, kilit sırası; aktif/eski yol tablosu; değişiklik listesi | `RUNTIME_DECISIONS.md` |
| M02.04 | Oturum bağlamı ve kaydı | Yalıtılmış bağlamlar, benzersiz enkarnasyon, yineleme/yeniden bağlanma koruması, güvenli anlık görüntü | RT02–RT05 |
| M02.05 | Oturum yaşam döngüsü | Açık geçiş tablosu; geçersiz geçiş veya örtük yeniden bağlanma yok | RT06–RT08 |
| M02.06 | Tur tahsisi ve çiti | Oturum başına tekdüze kimlik; kısmi/spekülatif olay tur tahsis etmez | RT09–RT11 |
| M02.07 | Generation tahsisi ve çiti | Tekdüze kimlik, tura bağlı, aktif generation ve revizyon doğrulaması | RT12–RT14 |
| M02.08 | Hiyerarşik iptal | Kapsamlı jetonlar, nedenler, istek ile gerçek bitiş ayrımı, idempotent yayılım | RT15–RT19 |
| M02.09 | Atomik sonuç kabulü | İptal/commit sıralaması, sınırlı ekleme, çekiş/gönderimde yeniden kontrol | RT20–RT24 |
| M02.10 | Görev kaydı ve iş köprüsü | İzlenen görevler, sahibe aktarma, istisna gözlemi, geç geri çağrılar | RT25–RT27 |
| M02.11 | Tampon ve kira sahipliği | Sınırlı kuyruk, oturumlar arası takma ad yok, seçici boşaltma, taşma sonucu | RT28–RT30 |
| M02.12 | Duraklat/devam/kes ilkelleri | Duraklatma dönemi, sınırlı tutma, geri alma ve kesin commit çiti | RT31–RT35 |
| M02.13 | Son tarihler ve olay noktaları | Sahte saat, güvenli üst veri, monoton zaman, M04 devri | RT36–RT37 |
| M02.14 | İdempotent kapanış ve ertelenmiş temizlik | Bir kez kapanış, süre, uçuşta/karantinadaki kiralar, yeniden açılma yok | RT38–RT44 |
| M02.15 | Eski kod adaptörleri | Dar güvenli web/telefon/görev noktaları; varsayılan davranış değişmez | RT45–RT46 |
| M02.16 | Belirlenimci yarış ve hata testleri | RT01–RT48; bariyerler, sahte adaptörler, canlı servis yok | Tüm testler çalıştırılmış |
| M02.17 | Özellik regresyonu ve bütünlük | M00 yükümlülükleri, genel davranış, kaynak kapsamı, gerçek günlük | RT47 |
| M02.18 | Kabul ve aşağı akış devri | M02-G00…G13, rapor, geri dönüş, M03/M04/M06/M07/M08 notları | `decision.json`, devir notu |

## 7. Testler

Asenkron testler uyku tabanlı değil, gerçek senkronizasyon bariyerleri (`asyncio.Event`, iş kapıları, kontrollü sahte saat) kullanır. Sahte aktarımın ekleme, gönderim ve tamamlanması ayrı kontrol edilir; iptali görmezden gelen sahte yerel iş bilerek kullanılır; sentetik PCM.

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| RT01 | Güvenli içe aktarma | Model/DB/ağ/görev başlatılmaz |
| RT02 | Oturum oluşturma | Tek sahip, benzersiz iç kimlik |
| RT03 | Yinelenen oluşturma | Açık ret veya belgeli idempotency; üzerine yazma yok |
| RT04 | İki oturum | Aynı yerel sayaçlar; tamponlar/görevler/jetonlar bağımsız |
| RT05 | Yeniden kullanılan dış kimlik | Yeni enkarnasyon; eski geri çağrı reddedilir |
| RT06 | Normal yaşam döngüsü | NEW→OPENING→ACTIVE→CLOSING→CLOSED geçerli geçişleri |
| RT07 | Geçersiz geçiş | Yeniden açılamaz; açılış/kapanışta kabul yok |
| RT08 | Kısmi hazırlık hatası | Alınan kaynaklar bir kez kapatılır |
| RT09 | Tur tekdüzeliği | Eşzamanlılıkta sayaç sıfırlanmaz/yeniden kullanılmaz |
| RT10 | Kısmi/aday giriş | İstenmeyen tur tahsisi yok |
| RT11 | Yeni tur eskiyi geçersiz kılar | Eski yanıt çitlenir, güncel tur kabul edilir |
| RT12 | Generation tahsisi | Aynı turda çok generation; oturum sayacı tekdüze |
| RT13 | Yanlış kapsam | Oturum/tur dışı generation başvurusu reddedilir |
| RT14 | Plan revizyonu | Uyuşmayan parça/revizyon reddedilir |
| RT15 | Kök iptal | Alt kapsamlar bilgilendirilir; ilgisiz oturum etkilenmez |
| RT16 | Tur iptali | Yalnızca o turun altı iptal edilir |
| RT17 | Generation iptali | İlgisiz giriş/tur iptal edilmez |
| RT18 | Yinelenen iptal | İlk etkili neden/zaman korunur |
| RT19 | Alt kayıt ile üst iptal yarışı | Alt kapsam iptalden kaçamaz |
| RT20 | Eklemeden önce iptal | Bayat öğe kabul edilmez |
| RT21 | Eklemeden sonra iptal | Eşleşen öğe silinir, diğer oturum etkilenmez |
| RT22 | Kapasite beklerken iptal | Rezervasyon bırakılır, geç uyanma reddedilir |
| RT23 | Çekişten sonra gönderimden önce iptal | Sahte aktarım sıfır bayat gönderim alır |
| RT24 | Gönderimden sonra iptal | Uçuşta raporlanır; sahte "duyulur boşaltma" yok |
| RT25 | İşbirliği yapmayan yerel sonuç | Reddedilir; kira iş bitene kadar korunur |
| RT26 | Yürütücü iş parçacığı geri çağrısı | Sahibe aktarılır; iş parçacıkları arası güvensiz değişim yok |
| RT27 | Yinelenen/sırasız öğe | Açık ret/politika; çift oynatma yok |
| RT28 | Sınırlı kuyruk | Öğe ve bayt/süre sınırları uygulanır |
| RT29 | Tampon sahipliği | Yazılabilir takma ad veya erken bırakma yok |
| RT30 | Dolu medya kuyruğunda kontrol | İptal/kapanış aç kalmaz |
| RT31 | Yumuşak duraklatma | Yeni gönderim yok; generation iptal edilmez |
| RT32 | Aynı duraklatmaya devam | Yalnızca gönderilmemiş veri sürer, geri sarma yok |
| RT33 | Bayat devam/zaman aşımı | Yeni duraklatmayı veya generation'ı etkilemez |
| RT34 | Kesmeyi kesinleştirme | Bir kez iptal, boşaltma, boşaltma niyeti; geri dönüş yok |
| RT35 | Duraklatma taşması | Açık sınırlı davranış, sınırsız büyüme yok |
| RT36 | Son tarih ve sahte saat | Süresi geçen iş reddedilir; duvar saatine bağımlılık yok |
| RT37 | Olay alıcısı hatası | Çalışma zamanı durumu sağlam; yalnız güvenli kanıt |
| RT38 | Eşzamanlı kapanış | Aynı kapanış sonucu, tek temizlik |
| RT39 | Temizlik sırasında çağıranın iptali | Koordinatör izlenmeye devam eder, sızıntı yok |
| RT40 | Kapanış geri çağrısı hatası | Kalan kaynaklar işlenir, güvenli hata raporlanır |
| RT41 | İşbirliği yapmayan kapanış zaman aşımı | Mantıksal kapalı ile bekleyen geri alım ayrı |
| RT42 | Karantina doygunluğu | Açık ret/düşürme; canlı sahiplik silinmez |
| RT43 | Ertelenmiş gerçek tamamlanma | Tam bir kez geri alım, istisna gözlenir |
| RT44 | Paylaşılan model kirası | A'nın kapanması modeli boşaltmaz, B'yi etkilemez |
| RT45 | İşlem sonucu bilinmiyor/commit | Otomatik yeniden oynatma/geri alma/başarı iddiası yok |
| RT46 | Eski web/telefon sözleşmeleri | Özgün imzalar, bayraklar, PCM/DTMF şeması değişmez |
| RT47 | Özellik regresyonu/bütünlük | İlgili M00 yükümlülükleri ve kapsam karşılaştırması |
| RT48 | Sentetik yaşam döngüsü tekrarı | İki oturumla tekrar eden oluştur/tur/sentez/iptal/kapat (öneri 100 döngü); mantıksal sızıntı yok, bekleyen yerel iş izleniyor |

RT46 yalnızca sahte/fikstürle; RT47 taban hatalarını aynı bağlamla korur (ilgisiz eski hata sessizce düzeltilmez); RT48 bir verim veya RAM benchmark'ı değildir.

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M02-G00 | Ön kontrol | Kabul edilmiş M00/M01 ve uzlaştırılmış kaynak anlık görüntüsü doğrulandı |
| M02-G01 | Kapsam | Açık sahiplik/kapsam; izinsiz değişiklik veya ikinci canlı otorite yok |
| M02-G02 | Yalıtım | Oturum enkarnasyonu ve iki oturum yalıtımı doğrulandı |
| M02-G03 | Yaşam döngüsü | Geçişler ve bir kez kapanış doğrulandı |
| M02-G04 | Kimlikler | Tur/generation tekdüzeliği ve kapsamlı başvuru bütünlüğü doğrulandı |
| M02-G05 | İptal | Hiyerarşik iptal, geç kayıt, istek/tamamlanma ayrımı doğrulandı |
| M02-G06 | Kabul çiti | Atomik sonuç kabulü ve iptal/kuyruk/gönderim yarış testleri geçti; uçuş sınırlamaları açık |
| M02-G07 | Duraklatma | Duraklat/devam/kesinleştir idempotency ve sınırlı tutma doğrulandı |
| M02-G08 | Kaynaklar | Görev/tampon sınırları, son tarih, sahiplik, bırakma ve karantina test edildi |
| M02-G09 | Saat/olay | Güvenli saat/olay noktası, üst veri maskeleme ve içe aktarma davranışı doğrulandı |
| M02-G10 | Uyum | Eski web/telefon/API/DTMF ve iş davranışı korunmuş; izinsiz varsayılan etkinleştirme yok |
| M02-G11 | Test kanıtı | RT01–RT48 incelenebilir kanıtla çalıştırıldı; hata/atlamalar açık |
| M02-G12 | Bütünlük | Bütünlük, M00 özellik kimlikleri, geri dönüş ve kanıt doğrulandı |
| M02-G13 | Devir | Aşağı akış devri tam; çözülmemiş engelleyici M02 arayüzü yok |

## 9. Kanıt

`evidence/M02/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `RUNTIME_INVENTORY.json`, `RUNTIME_DECISIONS.md`, `SESSION_RUNTIME.md` (iç arayüz, durum şemaları, sınırlamalar), `CANCELLATION_MATRIX.csv` (kapsam, yayılım, kuyruktaki/çalışan/uçuştaki sonuç davranışı, test kimlikleri), `RESOURCE_OWNERSHIP.json`, `LEGACY_INTEGRATION_MATRIX.csv`, `TEST_MATRIX.json`, `FEATURE_REGRESSION_MATRIX.csv`, `DOWNSTREAM_HANDOFF.md`.

## 10. Geri dönüş

Yeni çalışma zamanı eklemelidir; eski noktalardaki dar değişiklikler ayrı commit'tir ve `git revert` ile geri alınır. Canlı bağlantı noktası sorun çıkarırsa önce o commit geri alınır, çalışma zamanı modülleri kalabilir.

## 11. Devir

- **M03:** yapılandırma ve bayrak kaydı (sınır politikalarının kaynağı).
- **M04:** olay yolu ve izleme; `sequence` kapsamı ve saat alanı sözleşmesi.
- **M06:** GPU kabulü, iş kimlikleri, kiraların M02 `ResourceLedger`'ı ile bağlanması.
- **M07:** işlem makbuzu uzlaştırması; iptal ≠ geri alma.
- **M08:** sahte saat, sahte aktarım ve iptali görmezden gelen sahte iş fikstürlerinin ortak altyapıya taşınması.
- **F1/F5/F6:** generation çitinin VAD, sentez gönderimi ve aktarım yazmasında yeniden kontrolü; gönderilmiş ses geri alınamaz.

## 12. Başlatma komutu

```
M02 paketini uygula: docs/execution/packages/W1/M02-oturum-iptal.md.
Kuralları CLAUDE.md'den oku; M01 kanıtını ve M02_HANDOFF.md'yi doğrula.
backend/core/runtime/ altında oturum, tur/generation, iptal, kabul çiti, tampon ve kapanış
çalışma zamanını ekle; eski yolu varsayılan bırak, yalnızca incelenmiş dar noktalara bağla.
RT01–RT48'i bariyerli belirlenimci testlerle çalıştır, M02-G00…G13'ü değerlendir,
paket/M02 dalında PR aç ve dur.
```
