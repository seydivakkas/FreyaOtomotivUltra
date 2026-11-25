# M04 — Olay yolu, izleme ve gözlemlenebilirlik

> Tek gözlem otoritesi kurar: sınırlı ve bloklamayan olay yolu, güvenli izdüşüm, iz/aralık (span) deposu, gecikme profili, metrik kaydı, kaynak telemetri arayüzü, yapılı günlük ve yerel saklama. Gözlem düzlemi kontrol düzlemi değildir: olay kaybı iptali, boşaltmayı veya işlem commit'ini asla engellemez.

| Alan | Değer |
| --- | --- |
| Kimlik | M04 |
| Dalga | W1 |
| Öncelik | P0 |
| Önkoşullar | M01, M02 (M03 uyumu açıkça raporlanır) |
| Sonraki | M06, M07, M08, CORE_GATE |
| Bayrak | Yok — yeni tanılama açık etkinleştirme ve mevcut yetkiyle; varsayılan genel davranış değişmez |
| Ortam | CPU |
| Eski görevler | CC-T03, CC-T04 |
| Kaynak | Bundle `W1/Freya_2_0_M04_Agent_Implementation_Package.md`; [observability](../../../cross-cutting/observability.md) |
| Durum | NOT_RUN |

## 1. Amaç

Bugün gecikme ve kaynak değerleri dağınık günlüklerde, bazıları elle girilmiş sabitler. "İlk ses 1,2 s" gibi hedefleri kanıtlamak için aşama sınırları belli, saat alanları ayrı, örnek sayısı bilinen ölçümler gerekir. M04 bu altyapıyı kurar; F0–F6 paketleri kendi olaylarını bu kataloğa kaydeder.

## 2. Başlamadan önce

- [ ] M01 ve M02 kabul edilmiş; M02 olay alıcı arayüzü (`runtime_events.py`) ve devri okunmuş. M03 varsa revizyon izdüşümü kullanılır; yoksa "M03 üst verisi yok" açıkça yazılır.
- [ ] Mevcut gözlem envanteri çıkarılmış: gerçek üreticiler, günlükler, API'ler, arayüz tüketicileri (Kokpit, Studio), zaman alanları, saklama, özellik kimlikleri. **Geçmiş/canlı ve mock/gerçek** kaynaklar ayrılmış (M00 bulgusu: Kokpit v3'teki sabit metrikler).

## 3. Kapsam

**Yapılacak:** Olay kataloğu, güvenli izdüşüm, sınırlı olay yolu, abone yaşam döngüsü, korelasyon, iz/aralık deposu, gecikme profili, metrik kaydı, enjekte edilebilir kaynak örnekleyici, mevcut günlükleyiciyle köprü, yerel saklama ve döndürme, kanıt kaydedici, eski koda dar adaptörler, salt okunur güvenli özet izdüşümü.

**Yapılmayacak:** Dış telemetri hizmeti, otomatik yükleme, ağ yoklaması, model yükleme, gerçek Asterisk/SIP, müşteri verisi, DB göçü, arayüz tasarımı (G3'te). Kalıcı denetim kaydı ve yetki (M07). GPU kabulü (M06). Herkese açık günlük/iz rotası. Mevcut olay adlarını veya yanıt biçimlerini değiştirmek.

## 4. Dosyalar

```
backend/observability/
  event_catalog.py  projection.py  event_bus.py  subscriber.py  health.py
  correlation.py    trace_store.py span.py       latency.py     metric_catalog.py
  metrics.py        resource_probe.py  errors.py structured_logger.py
  local_store.py    evidence.py    legacy_adapter.py  api_projection.py
  lifecycle.py      config_adapter.py
tests/observability/
evidence/M04/<run_id>/
```

Küçük uyumlu dosyalar birleştirilebilir. Dar adaptörler yalnızca M02 olay noktasına, mevcut başlatma/kapatma kancasına, mevcut tanılama yönlendiricisine ve günlükleyiciye dokunur.

## 5. Tasarım ve sözleşmeler

### 5.1 Değişmez kurallar

1. Windows öncelikli, çevrimdışı öncelikli. Standart kütüphane ve onaylı mevcut bağımlılıklar.
2. **Gözlem düzlemi kontrol düzlemi değildir.** İptal, oynatma boşaltma, araç commit'i, kimlik doğrulama, kaynak kirası bırakma ve denetim, en iyi çabayla iletilen olaylara bağlı olamaz. Yetki M02/M06/F6'da, kalıcı denetim M07'dedir.
3. Mevcut bayraklar ve API davranışı değişmez. Ek tanılama açık etkinleştirme ve mevcut yetki ister. İkinci bir canlı günlükleyici her olayı çoğaltmaz.
4. **Üretici yolu süre ve alan olarak sınırlıdır.** Ses geri çağrılarında aboneyi bekleme, dosya I/O, DB, ağ, GPU senkronizasyonu, pahalı serileştirme, yüzdelik hesap veya çıkarım yok. Ucuz sınırlı doğrulama/izdüşüm izinli; zenginleştirme ve toplama işçide.
5. Tüm zarflar M01 alanlarını ve M02 üretici kapsamlı sıra numaralarını kullanır. Eski kodda yoksa iz/tur/generation kimliği uydurulmaz. Korelasyon tam kapsamlı başvurularla yapılır; çıplak tam sayı, müşteri adı, telefon veya transkriptle değil.
6. **Veri en aza indirme:** varsayılan olaylar yüksüzdür; yalnızca izin listeli tipli skaler üst veri. Ham ses, transkript, istem, yanıt metni, araç girdi/çıktısı, telefon, plaka, e-posta, müşteri adı, yetki başlıkları, kimlik bilgileri, özel veri içeren dosya yolları, güvenilmeyen istisna metni giremez.
7. Sayaçlar ve süreler gerçek gözlemi yansıtır. Bilinmeyen/eksik/kapalı değer `null` + durum + neden. Sıfır yalnızca tanımlı bir aralıkta ölçülmüş sıfırdır. Simülasyon donanım/üretim verisi gibi sunulmaz.
8. Depolama, kuyruk, aralık, boyut, abone sayısı, kayıt boyutu, saklama süresi ve işçi kapanışı sınırlıdır. Düşürme, kırpma, örnekleme, sıfırlama ve eksik gözlem ölçülebilir. **Eksik aralık sıfır gecikme değildir.** Gözlem hatası yalnızca gözlemi bozar; iş ve medya akışı sürer.

### 5.2 Olay kataloğu

M01 `EventEnvelope` aynen kullanılır. M04'e özgü sarmalayıcı (gerekirse): olay tanımı sürümü, gözlem kapsamı, sınırlı temizlenmiş üst veri, kaynak sınıfı (`MEASURED / SYNTHETIC_FIXTURE / HISTORICAL / MOCK`), üretici örneği/akış kapsamı, `span_ref`, `parent_span_ref`, sonuç durumu, neden kodu.

```json
{
  "envelope": {"schema_version": "2.0", "event_type": "generation.revoked",
    "session_id": "fixture-session-a", "trace_id": "fixture-trace-a",
    "turn_id": 4, "generation_id": 7, "sequence": 12,
    "monotonic_ns": 120000000, "clock_domain": "fixture-clock-a", "producer": "m02.runtime"},
  "observation_scope": "SERVER",
  "source_class": "SYNTHETIC_FIXTURE",
  "metadata": {"reason_code": "BARGE_IN"}
}
```

Henüz uygulanmamış aşağı akış yolları için yalnızca şema/niyet kaydedilir ve NOT_RUN raporlanır. Mevcut M02 adları ve eski tel adları korunur; takma adlar açık kaynak ve revizyonla eşlenir.

### 5.3 Aşama gecikme tanımları

Her gecikme metriği açık başlangıç ve bitiş sınırıyla tanımlanır; aynı saat alanında ölçülür.

| Metrik | Başlangıç → bitiş | Not |
| --- | --- | --- |
| `f0.processing_ms` | giriş kabul → iyileştirilmiş çerçeve hazır | Gerçek blok boyutu kaydedilir; 20 ms eşdeğerine yalnız tanımlıysa normalize |
| `f1.endpoint_delay_ms` | bilinen konuşma sonu → sonlandırma | Gerçek konuşma sonu etiketli başvuru ister; yoksa yalnızca karar aralığı |
| `f1.barge_control_ms` | aday/kesinleştirme tetiği → çalışma zamanı kontrol makbuzu | Aday ve kesinleştirme ayrı; duyulan kesme değildir |
| `f2.queue_wait_ms` | ASR işi kuyruğa → çalışma başlar | Kuyruk ≠ hesaplama |
| `f2.inference_ms` | çalışma başı → sonuç hazır | Kısmi/final, sıcak/soğuk, giriş süresi kapsamı |
| `f3.routing_ms` | final transkript kabul → yönlendirme kararı | İlgisiz LLM süresi katılmaz |
| `f3.llm_ms` | model isteği başlar → yanıt tamamlanır | Kuyruk ve ilk jeton ayrı (varsa) |
| `f3.tool_ms` | araç isteği → yetkili makbuz | Aktarım onayından işlem başarısı çıkarılmaz |
| `f4.plan_ms` | yanıt kabul → değiştirilemez sentez planı | |
| `f5.queue_wait_ms` | parça kuyrukta → çıkarım başlar | |
| `f5.inference_ms` | model çalışması başı → çıktı hazır | Gerçek enstrümantasyon varsa kodlayıcı/ODE/VAE alt aralıkları |
| `f5.ttfa_ms` | sentez isteği → ilk geçerli ses parçası | Sunucu gözlemi; önbellek isabet/ıska ayrı |
| `f5.rtf` | sentez süresi / geçerli ses süresi | Oran; pozitif payda; çıkarım ve kapsayıcı yol ayrı adlı |
| `f6.render_ms` | F5 parçası alındı → render tamam | Doğal çalma süresi hariç |
| `f6.submit_wait_ms` | çerçeve hazır → aktarıma gönderim | Yalnız sunucu; teslim değil |
| `f6.pacing_error_ms` | gerçek gönderim − planlanan zaman | İşaretli sapma ile mutlak hata birbirinin yerine kullanılmaz |
| `e2e.server_ttfa_ms` | gözlenen konuşma sonu/sonlandırma çapası → ilk geçerli medya gönderimi | Çapa açık; gerçek konuşma sonu ile endpoint kararı karıştırılmaz |
| `e2e.audible_ttfa_ms` | başvuru konuşma sonu → uçta ilk ses | Yalnızca doğrulanmış gerçek uç/loopback ölçümü |
| `f6.audible_barge_cut_ms` | müşteri başlangıcı/kesinleştirme çapası → eski ses uçta duyulmuyor | Yalnızca gerçek uç kanıtı |

### 5.4 Metrik kataloğu (çekirdek)

| Ad | Tür / birim | Kapsam / kaynak |
| --- | --- | --- |
| `observation.events_admitted` / `events_dropped` | sayaç / adet | üretici, hat, neden |
| `observation.queue_depth` / `queue_bytes` | gösterge / kayıt, bayt | kuyruk anlık görüntüsü |
| `observation.subscriber_failures` / `trace_evictions` / `store_errors` | sayaç / adet | güvenli kod |
| `observation.publish_ms` | histogram / ms | enstrümantasyon ek yükü |
| `runtime.active_sessions` / `stale_results_rejected` / `quarantined_resources` | gösterge, sayaç | M02 yetkili anlık görüntü |
| `runtime.cancel_observed_ms` | histogram / ms | mantıksal/fiziksel ayrımı |
| `gpu.used_bytes` / `gpu.total_bytes` | gösterge / bayt | cihaz, kaynak, zaman; M06 veya enjekte örnekleyici |
| `cpu.utilization_pct` / `ram.used_bytes` | gösterge | süreç mi makine mi açık |
| `asr.wer` / `asr.cer` | metrik örneği / oran | yalnızca başvuru benchmark'ı |

Yüzdelikler: belgeli yöntem, örnek sayısıyla birlikte; boş küme `null`; **tek örnek SLA değildir**. Yüzdeliklerin ortalaması alınmaz. Sıcak/soğuk, önbellek isabet/ıska, mock/gerçek, model/kodek popülasyonları ayrı tutulur. Etiket kardinalitesi sınırlıdır; kişisel veri etiket olamaz. Oran ile yüzde açıkça ayrılır; sıfır payda `null`.

### 5.5 Olay yolu, aboneler ve saklama

- Bloklamayan kabul; sayı ve bayt üst sınırı; açık taşma ve öncelik/hat politikası; kuyruk sağlığı. İş parçacıkları arası üretici güvenli; birleştirilmiş bildirim; yeniden girişli yayın sınırlı veya reddedilir; düşürme özeti fırtına yaratmaz.
- Her abonenin kendi sınırlı kuyruğu; yavaş veya hatalı abone diğerlerini etkilemez; abone olayları değiştiremez; başlat/durdur/boşalt süreli; "kabul edildi" ile "kalıcılaştı" ayrı.
- Yerel saklama: güvenli yollar (yol geçişi/sembolik bağ kaçışı reddedilir), bayt/sayı/yaş sınırlı döndürme, yalnızca sahip olunan süresi geçmiş dosyalar silinir, disk dolu/kilitli/okunamaz durumlar iş akışını bozmaz.
- Mevcut günlükleyici korunur: tek yayın, hız sınırı, bastırma sayaçları; küresel günlükleyici sıfırlanmaz.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| M04.01 | Önkoşul kontrolü | Kabul edilmiş M00/M01/M02, M03 uyumu, kaynak ve kirli kapsam | Kapsam onayı veya HOLD |
| M04.02 | Gözlem envanteri | Gerçek üreticiler, günlükler, API'ler, arayüz tüketicileri, zaman alanları, gizlilik, saklama, özellik kimlikleri; geçmiş/canlı, mock/gerçek ayrımı | `OBSERVABILITY_INVENTORY.json` |
| M04.03 | Sahiplik ve tasarım | Tek gözlem otoritesi, M02 noktası, işçi sahipliği, sınırlı kuyruklar, hata politikaları, uyum kipleri; karar kaydı | `OBSERVABILITY_DECISIONS.md` |
| M04.04 | Olay kataloğu | `EventEnvelope` yeniden kullanımı; iç türler, yük izin listeleri, sürüm, sıra kapsamı, üretici sahipliği | OB03–OB07 |
| M04.05 | Güvenli izdüşüm | Tipli sınırlı izin listeleri, güvenli hatalar, kimlik işleme, maskeleme; gözlem sınırından önce temizleme | OB08–OB12 |
| M04.06 | Sınırlı olay yolu | Bloklamayan kabul, açık taşma ve hat politikası, kuyruk sağlığı | OB13–OB20 |
| M04.07 | Abone yaşam döngüsü | Sınırlı dağıtım, yalıtım, kayıt/tekilleştirme, durdur/boşalt süreleri | OB21–OB26 |
| M04.08 | Korelasyon motoru | Tam kapsamlı oturum/tur/generation/iz/üretici korelasyonu; eksik eski bağlam; boşluk/sıra dışı | OB27–OB28 |
| M04.09 | İz ve aralık deposu | Sınırlı yerel izler, başlangıç/bitiş eşleme, kısmi izler, iptal/zaman aşımı sonuçları, tahliye | OB29–OB34 |
| M04.10 | Gecikme profili | Aynı saat alanında zamanlama; açık aşama sınırları; kuyruk/hesaplama ayrımı; TTFA kapsamları | OB35–OB37 |
| M04.11 | Metrik kaydı | Tipli sayaç/gösterge/histogram; sınırlı etiketler, pencere, sıfırlama, null/durum, yüzdelik yöntemi | OB38–OB44 |
| M04.12 | Kaynak telemetri arayüzü | Enjekte edilebilir CPU/RAM/GPU örnekleyici; sahte kaynak testleri; model yükleme veya kabul kontrolü yok | OB45–OB46 |
| M04.13 | Yapılı günlük | Mevcut günlükleyiciyle yinelemesiz bütünleşme; güvenli alanlar, maskeli hata taksonomisi, hız sınırı | OB50 |
| M04.14 | Yerel saklama | Güvenli yollar, sınırlı bellek/disk, döndürme, kısmi yazma, gizli bilgi yok, sınırsız yeniden deneme yok | OB47–OB49 |
| M04.15 | Kanıt kaydedici | Çalıştırma kökeni; ölçülmüş/sentetik/geçmiş kapsamı; kanıt başvuruları; eksikse NOT_RUN/HOLD | OB51 |
| M04.16 | Eski kod bütünleşmesi | M02 alıcısı ve mevcut gözlem API'leri/tüketicileri dar adaptörlerle; genel API kırılmaz | OB53–OB54 |
| M04.17 | Güvenli okuma izdüşümü | Sınırlı salt okunur metrik/iz özetleri, sayfalama, gözlem kapsamı, mevcut yetki (arayüz G3'te) | OB52 |
| M04.18 | Belirlenimci testler | OB01–OB56; yarış/taşma/hata testleri, kontrollü saat ve fikstürler | Tüm testler çalıştırılmış |
| M04.19 | Regresyon ve bütünlük | M00 özellikleri, M01/M02 değişmezleri, M03 uyumu, içe aktarma davranışı, kapsam | OB55–OB56 |
| M04.20 | Kabul ve devir | M04-G00…G15, geri dönüş, kanıt, aşağı akış sözleşmeleri, bağımsız inceleme | `decision.json`, devir notu |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| OB01 | Önkoşul eksik | HOLD; kaynak düzenleme veya işçi başlatma yok; eksik bağımlılık adlandırılır |
| OB02 | Pasif içe aktarma | İş parçacığı/görev, dosya/soket, günlükleyici veya model başlatma yan etkisi yok |
| OB03 | M01 zarfının yeniden kullanımı | Kabul edilmiş tür ve uyumlu serileştirme; ikinci kanonik sözleşme yok |
| OB04 | Geçersiz şema/sürüm | Güvenle reddedilir; aşağı akışa iletilmez, güvenilmeyen hata metni yok |
| OB05 | Katalog doğrulaması | Bilinmeyen olay/alan reddedilir veya belgeli eski dönüşüm; ham yük yok |
| OB06 | Kapsamlı kimlik ve sıra | İki oturumda aynı tur/generation tam sayısı bağımsız; üretici sırası küresel değil |
| OB07 | Eksik eski üst veri | Eksik kimlik/saat yok olarak kalır veya açık dönüşüm hatası; uydurma yok |
| OB08 | Alanlarda sentetik kişisel veri | Sentetik telefon/plaka/e-posta/ad/istem/ses işaretleri kuyruğa girmeden reddedilir |
| OB09 | İç içe ve aşırı büyük yük | Sınırlı ret; nesne başvurusu tutulmaz, ham serileştirme yok |
| OB10 | Hata ve günlük maskeleme | İstisna/iz/etiketteki gizli bilgi işareti güvenli günlükte, sağlıkta veya kanıtta görünmez |
| OB11 | Güvensiz eski kimlik | Sızıntı yok; kişisel veriyle korelasyon yok; açık yok/engellendi |
| OB12 | İzdüşüm hatası | Kayıt düşürülür, güvenli sayaç artar; maskesiz geri düşme yok |
| OB13 | Normal yayın | Kabul ve belgelenen kuyruk kapsamında sıralı teslim |
| OB14 | Giriş sayı sınırı | Dolu kuyruk hemen düşürür/döner, doğru sayım; sınırsız büyüme yok |
| OB15 | Giriş bayt sınırı | Aşırı büyük veya toplam bayt taşması reddedilir; toplam sınır korunur |
| OB16 | Öncelik hattı doygunluğu | Ayrılmış hat sınırlı politikaya uyar; kayıp gözlenebilir; işletim yetkisi etkilenmez |
| OB17 | İş parçacıkları arası üretici | Eşzamanlı sınırlı gönderim; kayıp uyandırma/kilitlenme/sınırsız geri çağrı yok |
| OB18 | Üreticide I/O/bekleme yok | Bloklanmış sahte yazıcı/abone üretici kabulünü bloklamaz; geri çağrıdan disk/model işlemi yok |
| OB19 | Yeniden girişli yayın | Sınırlı veya açıkça reddedilir; sonsuz özyineleme/kilitlenme yok |
| OB20 | Düşürme özeti | Sayaçlar doğru; doygunlukta özyinelemeli olay fırtınası yok |
| OB21 | Abone kaydı | Yinelenen/azami kayıt kontrollü; çift teslim yok |
| OB22 | Yavaş abone | Kendi kuyruğu sınırlı; diğer aboneler sürer; gecikme/düşürme gözlenir |
| OB23 | Hatalı abone | Güvenli hata yalıtılır; ham istisna yok; diğer yollar sürer |
| OB24 | Abonenin olayı değiştirmesi | Girdi değiştirilemez/yalıtılmış; başka abonenin olayını etkileyemez |
| OB25 | Başlat/durdur/boşalt | Süreli kapanış; kabul/kalıcı ayrımı; atılan sayaçları; tekrar kapatma güvenli |
| OB26 | M02 kontrolünden bağımsızlık | Yol kapalı/dolu/hatalıyken iptal, kapanış, çit veya kaynak kirası davranışı engellenmez |
| OB27 | İz korelasyonu | Tam kapsamlı başvurular ve üst bağlantı; oturumlar arası veri yok |
| OB28 | Üretici yeniden başlatma/boşluk | Sıra boşlukları/yinelemeler/sıra dışı/yeniden başlatma açık; uydurma süreklilik yok |
| OB29 | Aralık zamanlaması | Aynı alanda sahte başlangıç/bitiş tam süre verir; sonuç değiştirilemez |
| OB30 | Yinelenen/eşsiz aralık | İki kez bitiş çift sayılmaz; eşsiz bitiş/açık aralık işaretlenir, sıfır değil |
| OB31 | Saat alanları arası süre | Farklı alanlar doğrudan çıkarılamaz; nedenle "yok" |
| OB32 | Saat gerilemesi / UTC sıçraması | Geçersiz monoton süre; duvar saati sıçraması geçerli süreyi etkilemez |
| OB33 | İz sınırı/tahliye | İz/aralık/bayt sınırları uygulanır; eksik iz durumu; sınırlı dizin |
| OB34 | İptal edilmiş/bayat gözlem | Tanılama olayı yalnız izinli kapsamda tutulur; kabul edilmiş generation sayılmaz |
| OB35 | Kuyruk/hesaplama ayrımı | Bilinen sahte sınırlar ayrı metrik üretir; örtüşme yanlış toplanmaz |
| OB36 | F6 makbuz kapsamları | SERVER gönderim/boşaltma veya PBX tükenmesi duyulan oynatma/kesme iddia etmez |
| OB37 | TTFA çapa ayrımı | Konuşma sonu, endpoint kararı ve sentez isteği metrikleri karışmaz |
| OB38 | Metrik şeması ve birimler | Sonlu olmayan/geçersiz birim/aralık reddedilir; oran/yüzde açık |
| OB39 | Sayaç sıfırlama ve kapsam | Gözlenen artışlar ve sıfırlama dönemi doğru; çift sayım/negatif fark yok |
| OB40 | Gösterge bayatlığı | Süresi geçmiş/erişilemez örnek sıfır değil, durumla `null` |
| OB41 | Yüzdelik yöntemi | Bilinen fikstür belgeli p50/p95/p99 ve sayıyı verir; boş `null`; tek örnek SLA değil |
| OB42 | Popülasyon ayrımı | Sıcak/soğuk, isabet/ıska, mock/gerçek, model/kodek ayrı; yüzdelik ortalaması yok |
| OB43 | Etiket ve seri sınırları | Kişisel veri dahil yüksek kardinaliteli etiketler reddedilir/sınırlanır; bellek sınırlı |
| OB44 | Oran/kapsama | Sıfır payda `null`; düşürme/örnekleme kapsamı açık; geçersiz oranlar reddedilir |
| OB45 | Sahte kaynak örnekleyici | GPU/CPU/RAM fikstürle eşleşir, kapsamıyla; çıkarım veya GPU başlatma yok |
| OB46 | Erişilemez kaynak | Eksik sağlayıcı/bayat/hata bilinmiyor verir; otomatik kurulum, ağ veya sahte veri yok |
| OB47 | Güvenli yerel yol | Yol geçişi, junction/sembolik bağ kaçışı reddedilir; dışarı yazma yok |
| OB48 | Döndürme ve saklama | Bayt/sayı/yaş sınırı; yalnızca sahip olunan süresi geçmiş dosyalar silinir; kanıt korunur |
| OB49 | Disk hatası/kısmi kayıt | Dolu/kilitli/okunamaz disk simülasyonu: sınırlı yeniden deneme, güvenli sağlık, iş hatası yok |
| OB50 | Yapılı günlükleyici köprüsü | Mevcut günlükleyici davranışı korunur; tek yayın, hız sınırı, bastırma sayaçları |
| OB51 | Kanıt kökeni | Sentetik/geçmiş/ölçülmüş kategoriler ve gerçek kaynak/hash; sahte PASS veya gerçek iddiası yok |
| OB52 | Güvenli okuma izdüşümü | Yetkili kapsam, yetkisiz ret, sınırlı sayfalama/filtre; gizli/kişisel veri yok |
| OB53 | M03 bütünleşme noktası | Güvenli revizyon izdüşümü; eksik M03 üst verisi açık; ikinci ayar kaydı yok |
| OB54 | Eski API ve davranış | Mevcut uç nokta biçimleri/durumlar/birimler/olay adları, varsayılan bayraklar, arayüz sözleşmesi korunur |
| OB55 | Sürekli sınırlı yük | Yüksek hızlı sentetik üretici + yavaş alıcı: bellek/görev sınırı, doğru kayıp sayımı, temiz kapanış |
| OB56 | Bütünlük ve regresyon | M00 özellik kimlikleri, M01/M02 testleri geçerli; izinsiz değişiklik yok; geri dönüş ve kanıt doğrulanmış |

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| M04-G00 | Ön kontrol | M00/M01/M02 kanıtı doğrulanmış, kaynak uzlaştırılmış, M03 uyumu açık |
| M04-G01 | Tek otorite | Tek gözlem otoritesi, onaylı kapsam, pasif içe aktarma, işletim bağımlılığı yok |
| M04-G02 | Zarf ve katalog | M01 zarfı, M02 kapsamlı kimlik/sıra ve katalog doğrulaması gösterilmiş |
| M04-G03 | Güvenli izdüşüm | Kişisel veri/gizli bilgi/ham yük reddedilir; güvenli hata, çıktı ve günlük test edilmiş |
| M04-G04 | Üretici kabulü | Sınırlı bloklamayan kabul, sayı/bayt sınırı, iş parçacıkları arası ve taşma test edilmiş |
| M04-G05 | Aboneler | Abone yalıtımı, sınırlı dağıtım, güvenli yaşam döngüsü ve doygunluk sağlığı |
| M04-G06 | İzler | İz korelasyonu, kısmi izler, boşluklar, saat alanları ve bayat gözlemler doğru |
| M04-G07 | Gecikme | Aşama sınırı zamanlaması, kuyruk/hesaplama ayrımı, TTFA ve oynatma gözlem kapsamları doğru |
| M04-G08 | Metrikler | Birimler, sayımlar, bayatlık, yüzdelikler, oranlar, kapsam ve seri sınırları test edilmiş |
| M04-G09 | Kaynak telemetrisi | Enjekte edilebilir telemetri, eksik kaynak, GPU/model yan etkisi yok |
| M04-G10 | Günlük ve saklama | Güvenli sınırlı günlük/saklama/döndürme ve I/O hata davranışı |
| M04-G11 | Kanıt kökeni | Gerçek gözlem ayrımı; sahte metrik veya sonuç yok |
| M04-G12 | Uyum | Eski API/bayraklar ve M02 kontrol davranışı korunmuş; güvenli okuma ve yetki sınırı |
| M04-G13 | Test kanıtı | OB01–OB56 gerçekten çalıştırılmış ve geçmiş; gizli hata/atlama yok |
| M04-G14 | Bütünlük | M00 koruma matrisi, izinli fark, kanıt ve geri dönüş doğrulanmış |
| M04-G15 | Devir | Aşağı akış sahipliği ve devir tam; kalan ürün/entegrasyon sınırları açık |

## 9. Kanıt

`evidence/M04/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json`, `OBSERVABILITY_INVENTORY.json`, `OBSERVABILITY_DECISIONS.md`, `EVENT_CATALOG.json`, `METRIC_CATALOG.json`, `LATENCY_DEFINITIONS.md` (§5.3 tablosunun uygulanmış hali), `LEGACY_COMPATIBILITY_MATRIX.csv`, `TEST_MATRIX.json`, `DOWNSTREAM_HANDOFF.md`.

## 10. Geri dönüş

Gözlem altyapısı eklemelidir; M02 alıcı noktası no-op'a döner ve M04 commit'leri `git revert` ile geri alınır. Mevcut günlükleyici ve tanılama rotaları değişmediği için davranış korunur.

## 11. Devir

- **M06:** GPU kaynak örnekleyicisinin gerçek sağlayıcısı; GPU iş olayları.
- **M07:** kalıcı denetim kaydı M04 olay yolundan bağımsız; güvenlik olaylarının izdüşüm kuralları.
- **M08:** sahte saat, bellek içi alıcı, olay fikstürleri; laboratuvar raporlarının kanıt kaydedicisi.
- **F0–F6:** her paket kendi olaylarını ve §5.3 metriklerini bu kataloğa kaydeder; tanımı değiştirmek plan reposunda bu dosyanın güncellenmesini gerektirir.
- **G3:** Kokpit/Studio yalnızca §5.4 güvenli okuma izdüşümünden beslenir; sabit metrik kalmaz.

## 12. Başlatma komutu

```
M04 paketini uygula: docs/execution/packages/W1/M04-olay-gozlem.md.
Kuralları CLAUDE.md'den oku; M01/M02 kanıtını doğrula, M03 durumunu raporla.
backend/observability/ altında sınırlı olay yolu, güvenli izdüşüm, iz/aralık, gecikme ve metrik
kaydını ekle; iptal ve kapanış hiçbir koşulda olay teslimine bağlı olmasın.
OB01–OB56'yı çalıştır, M04-G00…G15'i değerlendir, paket/M04 dalında PR aç ve dur.
```
