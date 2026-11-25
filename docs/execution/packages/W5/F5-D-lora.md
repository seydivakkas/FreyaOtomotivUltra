# F5-D — LoRA ile otomotiv ses uyarlaması araştırması

> **Araştırma paketi, ana ürünün parçası değil.** FreyaTTS DiT'e dar kapsamlı düşük sıralı uyarlayıcı (LoRA) eklemenin, gerçek ve **F5'e atfedilmiş** kalıcı bir otomotiv telaffuz hatasını düzeltip düzeltmediğini, ses kimliğini (Leyla, seed 9) ve genel Türkçe kaliteyi bozmadan, RTX 4070 8 GB sınırında ölçer. Ön uç (F4/M05) düzeltmesi sorunu çözüyorsa sonuç `NO_TRAINING_NEEDED`'dır ve bu geçerli bir başarıdır. Hiçbir aşama otomatik terfi etmez; ana ürün (G5) F5-D'ye bağlı değildir.

| Alan | Değer |
| --- | --- |
| Kimlik | F5-D |
| Dalga | W5 |
| Öncelik | P2 (araştırma; isteğe bağlı) |
| Önkoşullar | W2_GATE, F5-C + gerçek ve atfedilmiş F5 hata kanıtı (R1) |
| Sonraki | — |
| Bayrak | M03 uyarlayıcı tanımlayıcısı `f5.adapter` (varsayılan yok; `LAB_ONLY`); canlı yapılandırmadan etkinleştirilemez |
| Ortam | R2: CPU, belirlenimci fikstürler, sahte motor. R3–R5: ayrı onayla yerel GPU (M06 özel kira, canlı oturum yok) |
| Eski görevler | F5-T33 |
| Kaynak | Bundle `W5/Freya_2_0_F5_D_Agent_Implementation_Package.md`; [F5 spec](../../../stages/F5-neural-synthesis/spec.md); Hu vd., LoRA (arXiv:2106.09685) |
| Durum | NOT_RUN (R0: yalnız plan) |

## 1. Amaç

Mevcut doğrulama otomotiv terim doğruluğunu birleşik TTS+STT ölçümüyle %48 bulmuştur; bu, hatanın DiT'ten kaynaklandığını **kanıtlamaz**. F5-D önce hatayı katmanlara ayırır (F3 değer, F4 gerçekleştirme, ham F5, VAE, çözücü, F6/kodek, değerlendirici). Yalnız kalıcı ve bağımsız olarak doğrulanmış bir ham F5 hatası kalırsa ve haklar uygunsa, sınırlı bir LoRA deneyi tasarlanır.

### Araştırma aşamaları (bağlayıcı)

| Aşama | İçerik | Onay |
| --- | --- | --- |
| R0 plan | Yalnız bu belge; yürütülebilir değişiklik yok | — |
| R1 kalıcı hata uygunluğu | Çekirdek/W2/F5-C kabul + gerçek hata kanıtı + incelenmiş atıf; bağımsız karar: `ELIGIBLE_FOR_REVIEW` / `NO_TRAINING_NEEDED` / `HOLD` | Bağımsız gözden geçiren |
| R2 araştırma uygulaması | Yalıtılmış kod ve testler; yalnız belirlenimci sahte/yerel sınır fikstürleri; eğitim veya yerel yoklama yok | Kullanıcı (açık) |
| R3 fizibilite | Çevrimdışı gerçek yerel kuru çalıştırma: sınırlı ileri/geri/optimizer adımı, ölçülmüş bellek; ihlalde dur | Kullanıcı (ayrı) |
| R4 eğitim | Kapsamlı sınırlı denemeler; donmuş protokol; test kümesine erişim yok | Kullanıcı (ayrı) |
| R5 bağımsız değerlendirme | Seçilmiş uyarlayıcı dondurulur; ayrılmış küme bir kez; gerçek dinleyiciler yalnız yetkili son akustik kabulde | Bağımsız değerlendirici |
| R6 aday sürüm | Ayrı kullanıcı kararı; etkilenen ürün regresyonu; aksi halde `LAB_ONLY` veya ret | Kullanıcı (ayrı) |

Bu paketin "uygulanması" en fazla R2'yi kapsar. R3–R6 her biri ayrı onaydır; onaysız aşamanın kapıları `NOT_RUN` kalır.

## 2. Başlamadan önce

- [ ] Çekirdek, W2_GATE ve F5-C gerçek kabul; F5-C kabulü uyumlu anlık görüntüden (soy eşleşir).
- [ ] Gerçek kalıcı hata kanıtı var (yalnız tarihsel birleşik WER/terim sonucu yetmez).
- [ ] Kullanıcı R1/R2 onayı açıkça verilmiş; plan varlığı onay değildir.
- [ ] Mevcut model yükleyici, kayıt, önbellek ve zamanlayıcı envanterde; ikinci yükleyici yok.

## 3. Kapsam

**Yapılacak (R1–R2):** giriş ve soy; hata atfı; uygunluk incelemesi; envanter; varlık bazlı haklar; derlem şartnamesi; bölümleme; ön işleme eşlemesi; yerel eğitim hedefi incelemesi; hedef modül haritası; sıfır deltalı uyarlayıcı noktası; kaynak modeli; fizibilite ve eğitim protokolleri; atomik checkpoint; önceden kayıtlı değerlendirme tasarımı; ses kimliği ve unutma koruması; M03 kaydı; önbellek ve çalışma zamanı yalıtımı; geri dönüş ve gizlilik; devir.

**Yapılmayacak:** Tam ince ayar; FreyaTTS taban ağırlıklarını değiştirme; yeni sağlayıcı veya model indirme; internetten veri kazıma; müşteri çağrısı/CRM kaynaklı ses; canlı rota/UI; seed değişikliği; simüle MOS/ABX; otomatik terfi.

## 4. Dosyalar

```
backend/neural_synthesis/research/adapters/
  attribution.py  rights.py  corpus_manifest.py  partition.py  preprocess_map.py
  objective_probe.py  targets.py  lora_seam.py  resource_model.py  checkpoint.py
  evaluation_design.py  registry_descriptor.py
tests/neural_synthesis/research/
evidence/F5-D/<run_id>/
data/F5/lab-report-*.json   (yalnız R3+ gerçek ölçümler)
```

Uyarlayıcı varlıkları yalnız onaylı yerel kökte; güvenli serileştirme (safetensors benzeri), yürütülebilir içerik (pickle) yok.

## 5. Tasarım ve sözleşmeler

### 5.1 Atıf

Her hata vakası katman katman izlenir: F3 yanlış araç değeri → F3; F4 desteklenmeyen varyant/yanlış gerçekleştirme → F4/M05; ham doğru ama kodek çıktısı yanlış → F6/kanal; onaylı fikstürde VAE yeniden kurma hatası → VAE incelemesi (atıf çözülmemiş); bağımsız inceleme olmadan değerlendirici anlaşmazlığı → bilinmiyor. İncelenmemiş alternatif neden varsa akustik kusur gözlense bile HOLD.

### 5.2 Haklar ve derlem

Yalnız kullanıcının sağladığı onaylı yerel varlıklar. Temel checkpoint, kod, tokenizer, AudioVAE, değerlendirici gömme modeli ve veri kümesi lisansları tek tek doğrulanır (türev, ticari/otomotiv kullanımı, dağıtım, atıf, rıza kapsamı). Herkese açık olmak lisans değildir; seed sahiplik veya rıza ima etmez; yalnız kayıt rızası eğitim için yetmez. Haklar süresi dolarsa yeni iş çitlenir, türevler karantinaya alınır.

Derlem bildirimi: lisanslı eşli Türkçe metin/ses; incelenmiş kanonik anlamsal alanlar ve model uyumlu gerçekleştirme; nitelikli gözden geçirenlerden telaffuz notları; örnekleme hızı/kanal/kodlama ve doğrulanmış hizalama; kaynak ve ses kökeni; kalite bayrakları; hak kapsamı/süresi; bölüm grubu ve soy. Kapsam sınıfları: marka/model (Peugeot, Qashqai, Škoda — onaylı telaffuz değil, aday sözlük girdisi), çekimli otomotiv ifadeleri, motor kodları/kısaltmalar, servis terimleri, sayısal değerler, Türkçe noktalı/noktasız I, olumsuzluk, tarih/saat/fiyat. Boş sınıf için sayı uydurulmaz.

### 5.3 Bölümleme ve ön işleme

Artırma ve ayardan **önce** bölümle. Öneri 70/15/15 eğitim/doğrulama/test, klip değil **grup** bazında: özgün kayıt/oturum, ses soyu, normalize metin/şablon ailesi (yalnız model yılı/rakamı farklı şablon aynı aile), yakın kopya ses/metin, artırılmış varyantlar geçişli bileşen olarak birlikte kalır. Hedef ses bölümler arasında ortak olabilir (belgelenir) ama oturum ve metin ailesi örtüşmesi yasak. Hata keşfi ifadeleri geliştirme kümesindedir, son teste konmaz. Test etiketleri ayar sürecine erişilemez.

Ön işleme: gerçek eğitim ön ucu ve örnekleme hızı doğrulanır; değiştirilemez F4 temsili; ham varlıklar ve hizalama korunur; yalnız gerekiyorsa kenar yumuşatmalı yeniden örnekleme (süre eşlemesi kayıtlı); korumalı rakam/olumsuzluk kaybı → öğe reddi; geçersiz hız/sonlu olmayan ses → ret; tahmini hizalama yok; toplu dolguda kayıp paydası geçersiz çerçeveleri hariç tutar.

### 5.4 Uyarlayıcı

Desteklenen afin modül için `W0 [d_out, d_in]`, `A [r, d_in]`, `B [d_out, r]`, `W_eff = W0 + (alpha/r)·B·A`; eğitilebilir sayı `r·(d_in + d_out)` (bias ve diğer parametreler donuk). Fikstür örneği: 1024×1024, r=8 → 16 384 parametre — **Freya boyutu veya VRAM tahmini değildir**. Başlangıç deltası sıfır (B sıfır); taban eşdeğerliği önceden kayıtlı toleransta. Taban parametre/tampon digest'leri öncesi/sonrası; joker/bilinmeyen hedef adı reddedilir; belgelenmiş dilimleme olmadan birleşik QKV HOLD; paylaşılan parametre eğitilebilir olursa dondurma ihlali.

Mevcut çıkarım ODE'si otomatik olarak eğitim algoritması değildir; yerel eğitim hedefi meta verisi yoksa HOLD (varsayılan MSE veya ODE üzerinden geri yayılım yok). Koşullandırma/latent ölçek revizyonu uyuşmazsa çalıştırma engellenir.

Önerilen deney profilleri (hepsi `NOT_RUN`, asla varsayılan değil): A0 taban; A1 sıfır delta eşdeğerliği; A2 r4/α8; A3 r8/α16; A4 r16/α32; A5 seçilmiş sıra + hedef küme ablasyonu; A6 isteğe bağlı genel Türkçe tekrar karşılaştırması. Doğrulama-yalnız arama önerisi: LR 1e-5 / 5e-5 / 1e-4, dropout 0 / 0,05; en çok 6 eğitilmiş deneme (kullanıcı bütçesine bağlı).

### 5.5 RTX 4070 8 GB fizibilitesi (R3)

LoRA eğitilebilir parametre ve optimizer maliyetini düşürür; taban ağırlık ve aktivasyon belleğini otomatik düşürmez. Bütçe: taban ve donuk bileşen yerleşimi, uyarlayıcı ağırlık/gradyan/ana kopya, optimizer durumu, aktivasyon/checkpointing, maske/latent/attention çalışma alanı, VAE, CUDA bağlamı, ayırıcı parçalanması, Windows/WDDM ve dış süreç payı. Cihaz toplamı, kullanılan/boş ve ayırıcı allocated/reserved/peak ayrı ölçülür; örtüşen sayılar toplanmaz.

R3 sırası: statik parametre ve şekil envanteri → bellek tahmini → sınırlı CPU kontrolleri → gerçek eğitim hedefiyle en kısa temsilî mikro toplu ileri/geri/güncelleme → sonlu kayıp, yalnız uyarlayıcıda gradyan, taban hash'leri değişmemiş, senkronize tepe ölçümü → önceden bildirilmiş azami uzunluk ve gradyan biriktirmeyle (ilk optimizer durumu tahsisi ve checkpoint kaydet/geri yükle dahil) tekrar. Gerçek GPU'da kasıtlı OOM testi yok (sahte OOM R2'de). Üretim ASR oturumu etkinken özel eğitim kirası verilmez. Yalnız ileri geçiş ölçümü fizibilite için yetmez.

### 5.6 Değerlendirme ve unutma (R5)

Taban ve aday ayrılmış kümeden önce dondurulur; aynı hazırlanmış metin, koşullandırma, **seed 9**, çözücü/ızgara, dtype/cihaz, önbellek bypass, uzunluk profili ve değerlendirme hattı. Önce ham çıktı, sonra aynı F6 render/kodek ayrı katman, gerçek uç yalnız sonda ve yetkiliyse. Bağımsız değerlendirici uyarlayıcı/sıraya kör; başarısız ve çıktısız öğeler paydada kalır.

| Metrik | Önerilen kabul (inceleme için öneri; doğrulanmış sınır değil) |
| --- | --- |
| Otomotiv terim doğruluğu | Bağımsız incelenmiş doğru oluşum / beklenen tüm oluşumlar; ≥ %95 hedef + kalıcı hata sınıfında önceden kayıtlı asgari eşli iyileşme |
| WER / CER / PER | Ham ve gidiş-dönüş ayrı; F2 bağlam hedefleri (WER ≤ %10, CER ≤ %4) F5 ham kalitesinin kanıtı değil; F5 ham vekil eşiği ayrı kalibre edilir |
| Genel Türkçe eşit-olmama | Aday − taban WER/CER/PER bozulması önceden kayıtlı küçük mutlak marjda (öneri: her biri 1 puan); eşli GA üst sınırı marj içinde |
| Konuşmacı benzerliği | F5-C ECAPA protokolü; bağımsız kalibrasyonda sabitlenmiş referans başı marj; GA alt sınırı marjı karşılar |
| Perde/seslilik/süre | F5-C katman başı dağılım ve sınırlar; eksik kapsam açık |
| MOS | Gerçek dinleme ortalaması ≥ 4,0 **ve** eşli eşit-olmama (öneri marj 0,2); yetersiz N terfiyi engeller |
| Kritik anlam | Kontrollü sette yeni kritik atlama/ikame/uydurma değer sıfır |
| Ham TTFA/RTF | Ilık kısa ıska p95 ≤ 500 ms, önbellek isabeti ≤ 50 ms, RTF p95 ≤ 0,30 (F5-C profilleri) |
| Kaynak | Onaylı profilde gözlenmiş OOM yok; gerçek tepe/pay ve hata sayıları |

Ayrılmış kümeye baktıktan sonra aday seçimi karşılaştırmayı geçersiz kılar. Önceden bildirilmiş marjın ötesinde iyileşme yoksa sonuç ret veya `NO_TRAINING_NEEDED`'dır.

### 5.7 Kayıt, önbellek ve geri dönüş

M03 tanımlayıcısı: uyarlayıcı kimliği, taban hash'i, sıra/α, hedef modüller, haklar ve son kullanma, aşama onayı. Taban hash'i yanlışsa yükleme reddi; `LAB_ONLY` uyarlayıcı canlı yapılandırmadan reddedilir; UI yerel boole ile etkinleştiremez (M07/M03). Etkin generation sırasında kayıt yeniden yüklemesi sabitlenmiş revizyonu değiştirmez. Önbellek kimliği uyarlayıcıyı içerir (aynı metin/seed taban ≠ uyarlayıcı); bir toplu işte karışık uyarlayıcı yok. Geri dönüş yeni planları tabana döndürür; etkin yerel iş varsa çitlenir ve kira yerel terminale kadar tutulur; generation ortasında uyarlayıcıdan tabana geçiş yok.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| F5-D.01 | Giriş | Çekirdek/W2/F5-C kabulü ve gerçek hata aşaması; soy uzlaştırma; kanıt yoksa R1'de dur | `preflight.md`; LR01–LR04 |
| F5-D.02 | Atıf | Anlamsal değer, F4, ham F5, VAE, çözücü ve F6/değerlendiriciyi ayrı izle | `attribution.md`; LR05–LR10 |
| F5-D.03 | Uygunluk incelemesi | Kalıcı hata, anlamlı etki, alternatifler ve hak fizibilitesinin bağımsız incelemesi; R2 onayı iste | `eligibility.json`; LR11–LR12 |
| F5-D.04 | Envanter ve sahiplik | Gerçek kayıt, yükleyici, eğitim kodu, önbellek, zamanlayıcı ve bayraklar | `inventory.json`; LR13–LR16 |
| F5-D.05 | Haklar | Varlık bazlı lisans/rıza/türev hakkı, geri alma ve kısıtlı amaç | `rights.json`; LR17–LR22 |
| F5-D.06 | Derlem | Eşli ses/metin ve notlar, çeşitlilik/kalite, sentetik kanaryalar, kabul | `corpus_spec.md`; LR23–LR26 |
| F5-D.07 | Bölümleme | Geçişli kaynak/şablon/kopya soyu gruplanır; referans/kalibrasyon ayrı; gözetim | `partition.json`; LR27–LR32 |
| F5-D.08 | Ön işleme | Yerel latent/metin hattı, hizalama, kalite dışlamaları; kaynak korunur | `preprocess.md`; LR33–LR36 |
| F5-D.09 | Yerel eğitim hedefi | Gerçek eğitim hedefi, koşullandırma ve maskeler; kesin yerel yetenek | `objective.md`; LR37–LR40 |
| F5-D.10 | Hedef haritası | Denetlenmiş afin hedefler; şekil, bağlı/birleşik ve eğitilebilirlik haritası | `targets.md`; LR41–LR44 |
| F5-D.11 | Uyarlayıcı noktası | Yalıtılmış sıfır delta yapımı; katı yüklemeli güvenli serileştirme | `adapter_seam.md`; LR45–LR48 |
| F5-D.12 | Kaynak modeli | Gerçek bileşen bütçeleri, M06 özel kira ve durma politikası | `resource_model.md`; LR49–LR52 |
| F5-D.13 | Fizibilite protokolü | Ayrı onaylı sınırlı R3 kuru çalıştırma; R2'de yalnız fikstür | `feasibility_protocol.md`; LR53–LR56 |
| F5-D.14 | Eğitim protokolü | Optimizer, kayıp, seed'ler, limitler, doğrulama seçimi ve bütçe dondurulur | `training_protocol.md`; LR57–LR60 |
| F5-D.15 | Checkpoint | Atomik yalnız-uyarlayıcı kaydet/devam soyu; yürütülebilir serileştirme yok | `checkpoint.md`; LR61–LR64 |
| F5-D.16 | Değerlendirme tasarımı | Önceden kayıtlı eşli ham/render/uç kapsamları, metrikler, ayrılmış küme gözetimi | `evaluation_plan.md`; LR65–LR68 |
| F5-D.17 | Ses kimliği ve unutma | ECAPA/F0/MOS/ABX kalibrasyonu ve genel Türkçe eşit-olmama; kritik koruma | `voice_forgetting.md`; LR69–LR76 |
| F5-D.18 | Kayıt | Yalnız incelenmiş M03 uyarlayıcı tanımlayıcısı doğrulaması; aşama onayı ayrı | `registry.md`; LR77–LR80 |
| F5-D.19 | Önbellek ve çalışma zamanı | F5-B kesin kimlik, M06 yerleşim yalıtımı, M02 generation kabulü | `cache_runtime.md`; LR81–LR84 |
| F5-D.20 | Geri dönüş ve gizlilik | Yeni planları tabana döndür/geri al; kira sonuçlandırma; kısıtlı saklama | `rollback_privacy.md`; LR85–LR90 |
| F5-D.21 | Devir | Gerçek araştırma sonucu incelemesi ve etkilenen ürün regresyonu; ana ürün bağımlılığı yok | `handoff.md`; LR91–LR95 |
| F5-D.22 | Doğrulama | LR01–LR104 yalnız yetkili yapısal aşamada; gerçek metrikler ayrı | `test_matrix.json`; LR96–LR100 |
| F5-D.23 | Regresyon ve aşama incelemesi | Önceki uygulanabilir testler, taban değişmezliği ve geri dönüş | `regression.md`; LR101–LR103 |
| F5-D.24 | Bağımsız kabul | Yapısal, R3–R6 ve ana ürün durumları ayrı; dur | `decision.json`; LR104 |

## 7. Testler

| Kimlik | Test | Beklenen |
| --- | --- | --- |
| LR01 | Çekirdek kabul kanıtı yok | Giriş HOLD; uygulama veya model erişimi yok |
| LR02 | W2 planı var ama gerçek WG PASS yok | Giriş HOLD; çıkarılmış kabul yok |
| LR03 | Uyumsuz farklı anlık görüntüden F5-C kabulü | Soy uyuşmazlığı girişi engeller |
| LR04 | Tüm planlar var, kullanıcı aşama onayı yok | NOT_RUN; kod/eğitim eylemi yok |
| LR05 | Yalnız tarihsel birleşik WER/terim sonucu | DiT hata kanıtı değil; HOLD |
| LR06 | Yanlış F3 araç değeri | Atıf F3; eğitim uygunluğu yok |
| LR07 | F4 varyantı desteklenmiyor veya yanlış gerçekleştirme | Atıf F4/M05; eğitim yok |
| LR08 | Ham doğru ama kodek çıktısı yanlış | F6/kanal kusuru; DiT iddiası yok |
| LR09 | Onaylı fikstürde VAE yeniden kurma hatası | VAE incelemesi; atıf çözülmemiş |
| LR10 | Bağımsız inceleme olmadan değerlendirici anlaşmazlığı | Bilinmiyor; zorlanmış DiT atfı yok |
| LR11 | Onaylı ön uç düzeltmesi hatayı çözer | NO_TRAINING_NEEDED; ana sürüm etkilenmez |
| LR12 | İncelenmemiş alternatif nedenli gerçek hata kanıtı | Akustik kusur gözlense bile HOLD |
| LR13 | Mevcut model yükleyici ve kayıt envanterde | Eşlenmiş otorite yeniden kullanılır; ikinci yükleyici yok |
| LR14 | Yerel eğitim yolu yok | Yetenek UNKNOWN; uydurma uygulama yok |
| LR15 | İsteğe bağlı F6-D yok | Yeni zorunlu DAG kenarı yok; kapsam not edilir |
| LR16 | F5-D'yi G5 için zorunlu yapma girişimi | Değişen grafik reddedilir; ana ürün bağımsız |
| LR17 | Lisansı doğrulanmamış herkese açık derlem | Karantina; veri kümesine alınmaz |
| LR18 | Kayıt rızası türev eğitim kapsamı içermiyor | Varlık için eğitim uygunluğu reddedilir |
| LR19 | Lisans araştırmaya izin verir, ticari dağıtıma vermez | Yalnız laboratuvar kısıtı yayılır |
| LR20 | Aşamalı çalıştırma sırasında hakların süresi doldu | Yeni iş çitlenir; türevler karantinaya |
| LR21 | Müşteri çağrısı veya CRM kaynaklı ifade | Görünür anonimleştirmeden bağımsız ret |
| LR22 | Onaylı kök dışına yol geçişi/yeniden ayrıştırma noktası | Hedef açılmadan ret |
| LR23 | Eşli doğru sesi olmayan sentetik metin fikstürü | Yalnız değerlendirme/tasarım; denetimli hedef yok |
| LR24 | Yanlış hedef konuşmacı/bilinmeyen koşullandırma | HOLD; Leyla uyarlaması iddiası yok |
| LR25 | Teknik kod etiketleri sesle çelişir | Ret veya bağımsız hakemlik; sessiz yeniden yazma yok |
| LR26 | Derlem sınıfında örnek yok | Eksik kapsam raporlanır; uydurma sayı yok |
| LR27 | Eğitim/test arasında birebir kopya ses | Bölüm denetimi başarısız |
| LR28 | Bölümler arasında yakın kopya/artırılmış kopya | Grup birleşimi; örtüşme reddi |
| LR29 | Yalnız model yılı/rakamla farklı şablon | Aynı aile bölümü; sızıntı yok |
| LR30 | Aynı hedef ses ama bağımsız oturum/metin aileleri | Yalnız beyan edilmiş sese özgü protokolle izinli |
| LR31 | Hata keşfi ifadesi son teste konmuş | Ret; keşif geliştirmeye aittir |
| LR32 | Test etiketleri ayar sürecine erişilebilir | Gözetim başarısız; etkilenen değerlendirme geçersiz |
| LR33 | Geçersiz örnekleme hızı veya sonlu olmayan ses | Ret; tahmini dönüşüm yok |
| LR34 | Hizalama kökenli gerekli yeniden örnekleme | Ham ve eşlenmiş süre korunur; yalnız doğrulanmış dönüşüm |
| LR35 | Ön işlemede korumalı rakam veya olumsuzluk kaybı | İşlenmiş öğe reddi |
| LR36 | Latent toplu işte dolgu | Kayıp paydası geçersiz çerçeveleri hariç tutar |
| LR37 | Yerel eğitim hedefi meta verisi yok | HOLD; varsayılan MSE veya ODE üzerinden geri yayılım yok |
| LR38 | Kasıtlı uyumsuz sahte hedef | Doğrulama optimizer oluşturmadan önce reddeder |
| LR39 | Koşullandırma/latent ölçek revizyonu uyuşmazlığı | Çalıştırma engellenir; zorlama yok |
| LR40 | Gerçek uzunluk için yanlış maske şekli | Kayıptan önce ret; dolgu kirlenmesi yok |
| LR41 | Bilinmeyen/joker hedef adı | Hedef şartnamesi reddedilir |
| LR42 | Belgelenmiş dilimleme olmadan birleşik QKV şekli | Hedef HOLD; tahmini izdüşüm yok |
| LR43 | Paylaşılan parametre yanlışlıkla eğitilebilir | Dondurma değişmezi FAIL; optimizer adımı yok |
| LR44 | 1024×1024 fikstürde r=8 | 16384 eğitilebilir parametre; fikstür gerçek Freya değil |
| LR45 | Fikstür afin yolunda sıfır delta uyarlayıcı | Önceden kayıtlı toleransta eşdeğer |
| LR46 | Yanlış şekil/beklenmeyen anahtarlı uyarlayıcı | Katı yükleme reddi |
| LR47 | Sonlu olmayan uyarlayıcı tensörü veya güvensiz dosya biçimi | İçerik yürütülmeden ret |
| LR48 | Sahte adımda taban parametresi veya tamponu değişti | Başarısız ve karantina; terfi yok |
| LR49 | Bayat cihaz/boş bellek gözlemi | Kaynak kabulü yok |
| LR50 | Üretim ASR oturumu hâlâ etkin | Özel eğitim kirası yok |
| LR51 | Parametre baytları sığar ama aktivasyon maliyeti bilinmiyor | Tahmin yetersiz; fizibilite PASS yok |
| LR52 | Belirsiz yerel terminal durumu | Kira tutulur/karantina; yeniden tahsis yok |
| LR53 | Yalnız ileri geçiş bellek ölçümü | Fizibilite eksik; geri/güncelleme gerekir |
| LR54 | İlk sahte güncellemede tahsis edilen optimizer durumu sınırı aşar | Dur; hata kaydedilir; kör yeniden deneme yok |
| LR55 | R3 simülasyonunda sahte OOM | Dur/uzlaştır; taban korunur; gerçek GPU kanıtı değil diye işaretlenir |
| LR56 | Yerel adım sırasında iptal | Sonraki yazmalar çitlenir; kira tamamlanana kadar |
| LR57 | Gerçek R3 kanıtı olmadan R4 isteği | Eğitim başlatma reddi |
| LR58 | Eğitim RNG seed'i çıkarım seed'inden farklı | Leyla çıkarımı 9 kalır; ayrı soy |
| LR59 | Azami optimizer adımına ulaşıldı | Bütçede tam durma; biriktirme doğru sayılır |
| LR60 | Doğrulama hatası veya NaN | Uygun checkpoint yok; politikaya göre sonlandırma |
| LR61 | Kesintiye uğramış checkpoint yayını | Önceki geçerli checkpoint kalır; geçici dosya etkin değil |
| LR62 | Devamda checkpoint taban/veri revizyonu uyuşmazlığı | Devam reddi |
| LR63 | Checkpoint kaydından sonra haklar geri alındı | Karantina; devam/etkinleştirme engellenir |
| LR64 | Bozuk checkpoint digest'i | Yüklemeden önce ret; pickle geri düşmesi yok |
| LR65 | Ayrılmış küme incelendikten sonra aday seçimi | Karşılaştırma geçersiz; yeni onaylı test gerekir |
| LR66 | Ham testte aday ve taban farklı F6 profilleri kullanır | Eşli karşılaştırma reddi veya ayrı katmanlar |
| LR67 | Başarısız çıktı metrik paydasından çıkarılmış | Doğrulama FAIL; eksik/başarısız açıkça kaydedilir |
| LR68 | Geçerli referans kelime/fonem yok | Nedenle null metrik; sıfıra bölme yok |
| LR69 | ECAPA sıfır norm veya desteklenmeyen boyut | Geçersiz skor null; sahte 0 yok |
| LR70 | Aynı üretilmiş taban referansı | Öz tutarlılık olarak etiketlenir, insan kimliği değil |
| LR71 | Sessiz veya yalnız sessizlik perde fikstürü | Sessiz yerde F0 null; kapsam raporlanır |
| LR72 | Gerçek dinleyici olmadan MOS isteği | NOT_RUN; vekil eşleme yok |
| LR73 | Otomotiv kazancı var ama genel Türkçe marjı aşar | Aday eşit-olmama reddi |
| LR74 | Ortalama iyileşmeye rağmen kritik sayısal atlama | Güvenlik FAIL; terfi yok |
| LR75 | Güçsüz eşli GA eşit-olmama sınırını keser | HOLD; üstünlük iddiası yok |
| LR76 | Akustik kanıt olmadan düşük eğitim kaybı | Yalnız eğitim metriği; araştırma NOT_RUN/HOLD |
| LR77 | Uyarlayıcı bildirim hash'i geçerli ama taban hash'i yanlış | Uyumsuz yükleme reddi |
| LR78 | Canlı yapılandırma yalnız laboratuvar uyarlayıcısı ister | Etkinleştirme reddi; aşama onayı gerekir |
| LR79 | Hakları süresi dolmuş tanımlayıcı | Uygunluk geri alınır; karantina |
| LR80 | Etkin generation sırasında kayıt yeniden yüklemesi | Sabit revizyon değişmez; yeni seçim ayrı |
| LR81 | Aynı metin/seed taban ile uyarlayıcı | Ayrı önbellek kimliği veya bypass |
| LR82 | Herkese açık önbellek önerisinde kişisel transkript hash'i | Ret; içerikten türetilmiş telemetri yok |
| LR83 | Toplu işte karışık uyarlayıcı kimlikleri | Uyumsuz; uyarlayıcılar arası gönderim yok |
| LR84 | Geri dönüşten sonra tamamlanan eski generation | Sonuç kabulü bayat çıktıyı engeller |
| LR85 | Yerel yürütme etkinken geri dönüş isteği | Hemen çit; kira yerel terminale kadar |
| LR86 | Geçersiz kılma sırasında eski önbellek ödünç alanı etkin | Mantıksal tahliye; bellek ödünç bırakılana kadar sayılır |
| LR87 | Kurtarma generation ortasında uyarlayıcıdan tabana geçerdi | Ret; yeni yetkili plan gerekir |
| LR88 | M03 CAS çelişen revizyon | Sessiz üzerine yazma yok; önceki/yeni durum yeniden doğrulanır |
| LR89 | Genel telemetride ham metin/ses/gömme | Mevcut politikayla ret/maskeleme; yük sızıntısı yok |
| LR90 | Geri alma özgün artı türev ağırlıkların silinmesini ister | Türevler karantinaya; yükümlülükler incelenir |
| LR91 | Araştırma PASS ama gerçek SIP regresyonu yok | Canlı hazırlık yanlış; taban G5 bağımsız |
| LR92 | Sentetik regresyon PASS ama gerçek kalıcı hata yok | Eğitim uygunluğu yok |
| LR93 | Gelecekteki UI yerel booleanla etkinleştirmeye çalışır | M07/M03 reddeder; UI yetkisi yok |
| LR94 | F5-D reddedildi ve taban kabul edildi | Ana ürün uyarlayıcısız kabul kalabilir |
| LR95 | Geri dönüşten sonra eski taban kesin profil | Aynı kabul edilmiş anlam; önbellek yalıtılmış; ek normalizasyon yok |
| LR96 | F5-B yeniden deneme sınırına ulaşıldı | Üçüncü deneme veya otomatik seed ikamesi yok |
| LR97 | Onaylı kimlik olmadan F5-C çözücü değişikliği | Yeni tanımlayıcı veya bypass; önbellek çakışması yok |
| LR98 | M06 zamanlayıcı ve M02 iptal entegrasyonu | Yerel tamamlanma ve CPU kabulü bağımsız; erken bırakma yok |
| LR99 | Önceki paket/kaynak hash uyuşmazlığı | Dur ve uzlaştır; yıkıcı onarım yok |
| LR100 | Belirlenimci fikstür gerçek ölçüm diye işaretlenmiş | Kanıt doğrulayıcı kabul iddiasını reddeder |
| LR101 | Yapısal testler PASS, eğitim hiç çalışmadı | Yalnız yapısal durum; eğitilmiş uyarlayıcı veya kalite iddiası yok |
| LR102 | Bağımsız gözden geçiren araştırma sonucunu reddeder | Aday devre dışı kalır; karar kaydedilir |
| LR103 | Tüm onaylı aşamalar PASS ama sürüm izni yok | Yalnız araştırma kabulü; üretim etkinleştirmesi yok |
| LR104 | Son rapor üretildi | Tam kanıt/bilinmeyenler/geri dönüş; dur; sonraki aşama gönderimi yok |

## 8. Kabul kapıları

Kapıların her biri ilgili yetkili aşamaya göre değerlendirilir; onaylanmamış aşamanın kapısı `NOT_RUN` kalır.

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| F5-D-G00 | Giriş | Kabul edilmiş çekirdek, W2, F5-C kesin soy, gerçek kalıcı hata aşaması ve kullanıcı onayı |
| F5-D-G01 | Atıf | Bağımsız yeniden üretimli incelenmiş atıf ve eğitim dışı alternatifler değerlendirilmiş |
| F5-D-G02 | Envanter | Mevcut sahip haritası ve gerçek yerel eğitim yeteneği envanteri; yinelenen otorite yok |
| F5-D-G03 | Haklar | Varlık bazlı lisans, rıza, izinli amaç ve türev kapsamı; bilinmeyen/süresi dolmuş hak yok |
| F5-D-G04 | Derlem | Doğrulanmış eşlemeli derlem, etiket ve ön işleme bildirimi; korumalı içerik kaybı yok |
| F5-D-G05 | Bölümleme | Donmuş bölüm ve bağımsız gözetim; kopya denetimi; sızıntı yok |
| F5-D-G06 | Eğitim hedefi | Yerel eğitim hedefi ve latent/koşullandırma sözleşmesi uyumlu ve bilinir |
| F5-D-G07 | Hedefler | Denetlenmiş hedef modüller, dondurma ve sıfır delta değişmezleri; joker enjeksiyon/taban değişikliği yok |
| F5-D-G08 | Kaynak | M06 özel kaynak sözleşmesi ve fizibilite protokolü; sınırsız tahsis veya canlı çekişme yok |
| F5-D-G09 | R3 fizibilite | Gerçek kuru çalıştırma ileri/geri/güncelleme ve ölçülmüş pay; ayrı onay (R2'de NOT_RUN) |
| F5-D-G10 | R4 eğitim | Donmuş eğitim planı ve gerçek sınırlı deneme kanıtı (R2'de NOT_RUN) |
| F5-D-G11 | Checkpoint | Atomik checkpoint ve kesin devam/hak soyu; güvensiz yapıt yok |
| F5-D-G12 | R5 değerlendirme | Önceden kayıtlı eşli ayrılmış küme protokolü ve gerçek değerlendirme (R2'de NOT_RUN) |
| F5-D-G13 | İyileşme ve güvenlik | Bağımsız otomotiv iyileşmesi + kritik güvenlik + genel Türkçe eşit-olmama |
| F5-D-G14 | Ses kalitesi | Kalibre konuşmacı/prozodi ve gerçek insan MOS kanıtı |
| F5-D-G15 | Kayıt/çalışma zamanı | Sürümlü uyarlayıcı kaydı, önbellek ve çalışma zamanı yalıtımı; otomatik etkinleştirme yok |
| F5-D-G16 | Geri dönüş/gizlilik | Geri dönüş, gizlilik, denetim ve geri alma işleme; taban bütünlüğü korunur |
| F5-D-G17 | Test kanıtı | LR01–LR104 gerçek belirlenimci sonuçlar ve uygulanabilir önceki regresyonlar |
| F5-D-G18 | Aday regresyonu | Gerçek aday çalışma zamanı regresyonu/geri dönüşü; uygulanabilirse ayrı sürüm yeniden yeterliliği |
| F5-D-G19 | Bağımsız inceleme | Bağımsız aşama incelemesi, açık aşama kararı ve kullanıcı onayı; asla otomatik değil |

## 9. Kanıt

`evidence/F5-D/<run_id>/`: `manifest.json`, `test-log.txt`, `decision.json` (aşama başı durum: yapısal / R3 / R4 / R5 / R6 / ana ürün ayrı), görev tablosundaki belgeler (`preflight.md`, `attribution.md`, `eligibility.json`, …, `handoff.md`), `TEST_MATRIX.json`. R3+ gerçek ölçümler `data/F5/lab-report-*.json`. Fikstür sonuçları asla "ölçülmüş" diye etiketlenmez.

## 10. Geri dönüş

Uyarlayıcı tanımlayıcısı geri alınır → yeni planlar tabana döner; taban ağırlıklar hiç değişmediği için ek işlem yok. Haklar geri alınırsa türev ağırlıklar karantinaya alınır. Kod `git revert`.

## 11. Devir

- **Ana ürün:** G2–G5 ve PILOT_DECISION F5-D'den bağımsızdır; F5-D reddedilse de taban kabul kalır.
- **R6:** aday sürüm ayrı kullanıcı kararı ve etkilenen ürün regresyonu (G4/G5 ilgili testleri) ister.
- **Açık kararlar:** ECAPA değerlendirici yerel yapıt/lisansı; derlem lisans ve inceleme yetkilisi ([master plan §Açık kararlar](../../master-plan.md#açık-kararlar)).

## 12. Başlatma komutu

```
F5-D araştırma paketini yalnız R1/R2 kapsamında uygula: docs/execution/packages/W5/F5-D-lora.md.
Kuralları CLAUDE.md'den oku; W2_GATE ve F5-C kabulünü, gerçek ve atfedilmiş F5 hata kanıtını ve kullanıcı R1/R2 onayını doğrula; eksikse dur.
Atıf, haklar, derlem/bölüm şartnamesi, eğitim hedefi incelemesi, sıfır delta uyarlayıcı noktası ve M03 tanımlayıcı doğrulamasını
yalnız CPU fikstürleriyle kur; eğitim, yerel GPU yoklaması veya model indirme yapma. LR01–LR104'ü çalıştır,
F5-D-G00…G19'u aşama başı değerlendir (R3–R6 NOT_RUN), paket/F5-D dalında PR aç ve dur.
```
