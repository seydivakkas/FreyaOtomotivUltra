# Freya 2.0 — Ana plan (paket planı)

> Bu belge projenin **tek yürütme planıdır**. Eski AIP/Faz planı ([docs/roadmap/master-plan.md](../roadmap/master-plan.md)) emekliye ayrılmıştır; eşleme [legacy-mapping.md](legacy-mapping.md) dosyasındadır. Teknik ayrıntı aşama spec'lerinde ([docs/stages/](../stages/)) ve ortak katman belgelerinde ([docs/cross-cutting/](../cross-cutting/)) kalır. Çalışma kuralları yalnız [CLAUDE.md](../../CLAUDE.md)'dedir.

## Amaç

FreyaTTS Automotive PoC'u, RTX 4070 Laptop 8 GB üzerinde çevrimdışı çalışan, Türkçe konuşan, telefon ve mikrofon üzerinden otomotiv servis işlemlerini yürüten bir sesli asistana dönüştürmek. Yeni ağır model eklemeden (Whisper, Qwen, FreyaTTS tek örnek), mevcut özellikleri kaybetmeden, her yeni davranışı bayrak arkasında ve ölçerek.

Öncelik sırası (mevcut ölçümlere göre): otomotiv terimlerinin güvenilir işlenmesi (tanıma %48 → ≥ %95), görüşme gecikmesi (LLM turu 6 sn → ilk duyulur ses 1,2 sn hedefi), söz kesme ve ses kalitesi, sonra arayüz ve gerçek koşul kabulü.

## Yapı: dalgalar, paketler, aşamalar

Bir **paket** tek oturumda bir ajanın uygulayacağı, kendi testleri ve kabul kapılarıyla kapanan iş birimidir. Paketler **dalgalara** gruplanır; dalgalar arasında **kapı** paketleri vardır. Tüm zorunlu paketler bittikten sonra **ürün aşamaları** (G2–G5) gelir.

| Dalga | Paketler | Öncelik | Amaç |
| --- | --- | --- | --- |
| W0 | [M00](packages/W0/M00-baseline-envanter.md), [H01](packages/W0/H01-guvenli-zemin.md) | P0 | Salt okunur envanter; bugün canlıyı etkileyen hataların bayraktan bağımsız düzeltilmesi |
| W1 | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) … [M08](packages/W1/M08-test-altyapisi.md), [CORE_GATE](packages/W1/CORE_GATE-cekirdek-kapisi.md) | P0 | Ortak çekirdek: sözleşmeler, oturum/iptal, yapılandırma, gözlem, sözlük, GPU, güvenlik, test altyapısı |
| W2 | [F0-A](packages/W2/F0-A-ses-girisi.md) … [F6-A](packages/W2/F6-A-render-aktarim.md), [W2_GATE](packages/W2/W2_GATE-w2-kapisi.md) | P0 | Uçtan uca dikey dilim: her aşamanın temel sürümü bayrak arkasında |
| W3 | [F1-B](packages/W3/F1-B-soz-kesme.md), [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md), [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md), [F3-B](packages/W3/F3-B-yonlendirme-onay.md), [F4-B](packages/W3/F4-B-fonoloji-g2p.md), [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) | P0 | Söz kesme, oynatma kuyruğu, otomotiv terim düzeltme, onaylı işlem, Türkçe fonoloji, ses profili/önbellek |
| W4 | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md), [F2-C](packages/W4/F2-C-akis-tanima.md), [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md), [F3-C](packages/W4/F3-C-coklu-niyet-rag.md), [F4-C](packages/W4/F4-C-prozodi.md), [F5-C](packages/W4/F5-C-ode-kimlik.md), [F6-C](packages/W4/F6-C-birlestirme-dsp.md) | P1 | Uyarlanır DSP/AEC, akış tanıma, anlamsal tur sonu, çoklu niyet ve RAG, prozodi, ODE profilleri, gelişmiş render |
| W5 | [F6-D](packages/W5/F6-D-chan-websocket.md) (isteğe bağlı), [F5-D](packages/W5/F5-D-lora.md) (araştırma) | P2 | Alternatif aktarım; LoRA araştırması (yalnız gerçek ve atfedilmiş hata varsa) |

| Aşama | Belge | Çıkış koşulu |
| --- | --- | --- |
| G0 | Bu plan | Kapsam, değişmezler, DAG ve riskler net |
| G1 | [packages/](packages/) | Her pakette giriş/çıkış, bağımlılık, test, geri dönüş, kabul tanımlı |
| G2 | [stages/G2-entegrasyon.md](stages/G2-entegrasyon.md) | Zorunlu W0–W4 kabul; tam regresyon; M00 özellik kapanışı; riskler kapalı |
| G3 | [stages/G3-arayuz.md](stages/G3-arayuz.md) | Dört alanlı kokpit gerçek API/yetkiye bağlı; özellik ↔ rota/eylem/test eşlemesi |
| G4 | [stages/G4-sentetik-kabul.md](stages/G4-sentetik-kabul.md) | Sentetik veriyle katman ve uçtan uca ölçüm (mock ve gerçek model ayrı); insan/SIP HOLD |
| G5 | [stages/G5-gercek-insan-sip.md](stages/G5-gercek-insan-sip.md) | Gerçek insan sesi, dinleyici değerlendirmesi, gerçek SIP ve uç ölçümü |
| PILOT | [stages/PILOT-karari.md](stages/PILOT-karari.md) | Kullanıcının açık kararıyla sınırlı pilot |

Sıra, bağımlılık grafiği ve paralellik: [execution-order.md](execution-order.md).

## Mimari özet

F0 ses girişi ve iyileştirme → F1 ses ve tur algılama → F2 konuşma tanıma → F3 diyalog zekâsı → F4 dilbilim ön ucu → F5 nöral sentez → F6 render ve aktarım. Ortak katman: M01 sözleşmeler, M02 oturum/generation/iptal, M03 yapılandırma ve model kaydı, M04 olay ve gözlem, M05 ortak otomotiv sözlüğü, M06 GPU zamanlayıcı, M07 güvenlik ve işlem otoritesi, M08 test altyapısı. Ayrıntı: [pipeline-v2.md](../01-architecture/pipeline-v2.md), sözleşmeler: [interfaces.md](../01-architecture/interfaces.md), paket → dizin: [ownership.md](ownership.md).

Her işlem tek yerde ve bir kez: F4 normalize eder, F5 sentezler, F6 duraklama/fade/EQ uygular; hız tek sahiplidir. Eski generation'a ait ses, transkript veya yanıt hiçbir yerde kullanılmaz.

## Hedefler

Bunlar **önerilen başlangıç hedefleridir; ölçülmüş değer değildir.** Kapsam, veri kümesi, donanım ve ölçüm sınırı ölçümden önce sabitlenir. Paket kabulleri yapısal testlerle olur; gerçek model ölçümleri G4'te, insan/SIP ölçümleri G5'tedir.

| Alan | Hedef |
| --- | --- |
| F0 | Normal koşulda örnek kaybı 0; DSP p95 ≤ 10 ms (20 ms çerçeve eşdeğeri); gürültüde ASR tabandan iyi, temiz konuşmada gerileme yok |
| F1 | VAD kesinlik/duyarlılık ≥ %95; onset p95 ≤ 100 ms; kısa yanıt endpoint p95 ≤ 500 ms; yanlış söz kesme ≤ %2 |
| F2 | WER ≤ %10, CER ≤ %4; otomotiv terim doğruluğu ≥ %95; yanlış otomatik düzeltme ≤ %1; kısa son ASR p95 ≤ 500 ms |
| F3 | Niyet makro-F1 ≥ %95; görev başarısı ≥ %95; yetkisiz/onaysız yazma, çift kayıt, uydurma fiyat = 0 |
| F4 | Kritik sayı/fiyat anlam kaybı 0; normalizasyon ≥ %99; korumalı atom ihlali 0; p95 ≤ 50 ms |
| F5 | Ilık kısa parça TTFA p95 ≤ 500 ms; RTF p95 ≤ 0,30; bozuk ses ve izinsiz seed değişimi 0; konuşmacı benzerliği/F0 referansla kalibre |
| F6 | 20 ms PCM çerçeve biçimi %100; yerel tempo sapması p95 ≤ 5 ms; iptal sonrası eski generation gönderimi 0; duyulur söz kesme p95 ≤ 200 ms (gerçek uçta) |
| Uçtan uca | İlk duyulur ses p95 ≤ 1,2 sn (kısa ve standart tur ayrı); tüm modeller açıkken tek görüşmede OOM 0; eşzamanlı kapasite ölçülür |

Kurallar: uçtan uca değer aşama p95'leri toplanarak hesaplanmaz, doğrudan ölçülür. Endpoint'ten ilk paket ve ilk duyulur ses ayrı metriktir. Ilık/soğuk, önbellek isabet/ıska, p50/p95/p99, örnek sayısı, hata sayısı ve yük koşulu ayrı kaydedilir. MOS/ABX gerçek dinleyici olmadan geçmiş sayılmaz. Ulaşılamayan hedef FAIL veya HOLD olarak gerekçelendirilir.

## Test seviyeleri

| Seviye | İçerik | Nerede |
| --- | --- | --- |
| T0 | Birim ve sözleşme testleri | Her paket |
| T1 | Kayıttan oynatma / fikstür | Her paket |
| T2 | Katman benchmark'ı (protokol pakette, gerçek ölçüm G4'te) | Paket + G4 |
| T3 | F0–F6 sentetik uçtan uca (mock ve gerçek model ayrı) | W2_GATE, G4 |
| T4 | Hata enjeksiyonu ve yük | Paket (belirlenimci) + G4 (yerel) |
| T5 | Gerçek kullanıcı ve SIP | Yalnız G5 |

Ayrıntı: [M08 §5.2](packages/W1/M08-test-altyapisi.md), [docs/testing/](../testing/).

## Yayılım

Eski davranış → gölge (yan etkisiz) → korumalı salt okunur → korumalı işlem → gerçek SIP/insan pilotu. Üretimde model, sözlük, çözücü veya aktarım değişikliği yalnız yetenek/bayrakla açılır. Hata durumunda güvenli baza dönülür; işlem sonucu bilinmiyorsa önce uzlaştırma yapılır.

## Yönetişim

- **Başlatma:** Her paket veya aşama kullanıcının açık komutuyla başlar ("M03 paketini başlat", "G4 aşamasını başlat"). Bir paketin kabulü sonrakini kendiliğinden başlatmaz.
- **Tek ajan:** Aynı anda tek ajan, tek paket. [execution-order.md](execution-order.md)'deki "sırası değiştirilebilir" grupları yalnız sıra esnekliğidir.
- **Bağımsız inceleme:** CORE_GATE, W2_GATE, G2, G3, G4, G5 ve PILOT kararları paketi uygulayan ajandan **ayrı** bir oturum veya kişi tarafından kanıt üzerinden verilir. Diğer paketlerde PR incelemesi yeterlidir.
- **Git:** Dal `paket/<ID>` (aşamalar için `asama/<ID>`); commit başlığı `<GÖREV-ID>: <kısa açıklama>`; paket başına bir PR; `main`'e doğrudan push, force push ve etiket yok.
- **Durum sözlüğü:** `NOT_RUN`, `PASS`, `FAIL`, `HOLD`, `DEFERRED` (yalnız isteğe bağlı kapsam). Ölçülmemiş değer `null`.
- **Kanıt:** [evidence.md](evidence.md).
- **Bayrak varsayılanları:** Canlı varsayılan yalnız PILOT_DECISION kapsamında değişir. G4'te aday profiller yalnız laboratuvar yapılandırmasıyla seçilir.
- **Sözleşme değişikliği:** Önce plan reposunda [interfaces.md](../01-architecture/interfaces.md) güncellenir (ayrı PR), sonra kod.
- Ayrıntılı gerekçeler: [decisions.md](decisions.md).

## Verilen kararlar

Kullanıcı (ürün sahibi) kararları, 2026-11-26. Karar günlüğü numarası parantez içinde. Kullanıcı tercihi bekleyen karar kalmadı; aşağıdaki açık kararlar ölçümle verilir.

| Karar | Özet | Etkilediği paket |
| --- | --- | --- |
| [ADR-F3-01](../01-architecture/adr/ADR-F3-01-arayan-kimlik-dogrulama.md) (ADR-001) — Arayan kimliği | Arayan numarası + doğum yılı; kayıtta yoksa plaka son 3–4 hanesi; görüşme başına en çok 3 deneme, sonra operatör | H01, M07, F3-A, F3-B |
| [ADR-X-03](../01-architecture/adr/ADR-X-03-yapay-zeka-bildirimi.md) (ADR-002) — Yapay zekâ bildirimi | Her görüşmenin başında: "Merhaba, Freya yapay zekâ destekli müşteri temsilcisine ulaştınız." | H01, F3-A, G5, PILOT |
| [ADR-F4-02](../01-architecture/adr/ADR-F4-02-saat-tarih-okuma.md) (ADR-003) — Saat okuma | Doğal Türkçe, gün dilimiyle: "sabah dokuz buçuk", "öğleden sonra iki", "akşam altı buçuk" | F4-A, F4-B, F2-B, F3-A |
| [ADR-F4-03](../01-architecture/adr/ADR-F4-03-telefon-numarasi-okuma.md) (ADR-004) — Telefon okuma | `05xx xxx xx xx` gruplaması: "sıfır beş yüz otuz iki, yüz yirmi üç, kırk beş, altmış yedi" | F4-A, F2-B |
| [ADR-X-04](../01-architecture/adr/ADR-X-04-sozluk-okunus-onayi.md) (ADR-005) — Sözlük okunuş onayı | Ürün sahibi + ilgili iş birimi; ajan onaylamaz | M05, F4-B |
| [ADR-X-01](../01-architecture/adr/ADR-X-01-asterisk-dagitim.md) (ADR-006) — Asterisk dağıtımı | Pilot/geliştirme aynı makine (WSL2/VM, loopback); üretim ayrı sunucu, özel ağ/şifreli tünel | F6-A, F6-D, G5, PILOT |
| [ADR-F3-02](../01-architecture/adr/ADR-F3-02-gomme-modeli.md) (ADR-007) — Gömme modeli | Yalnız `bge-m3`, CPU'da, yerel yapıt; model yoksa yalnız BM25 | F3-C, M03 |
| [ADR-X-05](../01-architecture/adr/ADR-X-05-belge-arsivi-onayi.md) (ADR-008) — Belge arşivi onayı | Lisans, kullanım hakkı, güncellik ve içerik doğruluğu için nihai onay iş sahibi / veri sahibinde; teknik ekip yalnız teknik doğrulama | F3-C, F5-D |

## Açık kararlar

Hepsi ölçüm (ve gerekiyorsa lisans) gerektirir: ilgili pakette ölçülür, ADR taslağı yazılır, karar kullanıcıya sunulur. Karar verilene kadar paket güvenli varsayılanla ilerler ama ilgili kapı `HOLD` kalır.

| Karar | Tür | Etkilediği paket | Öneri / güvenli varsayılan |
| --- | --- | --- | --- |
| ADR-X-02 — VRAM bütçesi ve Ollama `num_gpu` | Ölçüm | M06 | M06 ölçümüyle |
| ADR-F1-01 — Silero VAD oturum izolasyonu | Ölçüm | H01, F1-A | Oturum başına durum ayrımı; kanıt yoksa HOLD |
| ADR-F1-02 — F0 çerçeve boyu ve söz kesme bütçesi | Ölçüm + kullanıcı | F0-A, F1-B | Ölçümle seçenek A–D |
| ADR-F4-01 — Ara parça noktalaması / prozodi | Akustik ölçüm | F4-C | G4 dinleme ölçümüyle |
| ADR-F0-02 / F0-03 — AEC yöntemi, RNNoise | Ölçüm + lisans | F0-B | Lisans ve ölçüm yoksa bypass |
| ADR-F2-01 — N-best desteği | Ölçüm | F2-B | Desteklenmiyorsa tek hipotez + alternatif çözme |
| ADR-F5-01 — Konuşmacı kodlayıcı (ECAPA) yerel yapıtı ve lisansı | Ölçüm + lisans | F5-C, F5-D, G4, G5 | Lisanslı yerel yapıt yoksa benzerlik null |
| ADR-F6-01…04 — Yeniden örnekleyici, hız sahibi, sessizlik/konfor gürültüsü, web oynatma | Ölçüm | F6-A, F6-B, F6-C | Pakette ölçümle |

ADR dizini: [docs/01-architecture/adr/](../01-architecture/adr/README.md).
