# Eski plan → paket planı eşlemesi

> **Üretilmiş dosya — elle düzenlemeyin.** Kaynak: paket dosyalarındaki `Eski görevler` satırları ve `scripts/data/legacy_aip.json`. Yeniden üretmek için: `python scripts/build_registry.py`.

Eski AIP/Faz planı ve aşama `tasks.md` dosyalarındaki görev kimlikleri (`F2-T15`) artık yürütme birimi değildir; teknik ayrıntı için okunmaya devam eder. Yürütme birimi pakettir.

## AIP → paket

| AIP | Ad | Eski görevler | Yeni paket(ler) |
| --- | --- | --- | --- |
| AIP-01 | Hermetik test altyapısı (LLM ve Freya sahteleri, pytest işaretleri, ağır içe aktarmaların tembelleştirilmesi — bulgu X8) | F3-T01, F5-T07 | [H01](packages/W0/H01-guvenli-zemin.md), [M08](packages/W1/M08-test-altyapisi.md) |
| AIP-02 | Karakterizasyon testleri | F0-T01, F1-T01, F2-T03, F3-T02, F4-T01, F5-T02, F6-T01 | [M08](packages/W1/M08-test-altyapisi.md) |
| AIP-03 | Güvenlik düzeltmeleri | F3-T05, F3-T03 | [H01](packages/W0/H01-guvenli-zemin.md) |
| AIP-04 | Giriş ve tur hata düzeltmeleri | F1-T03, F1-T05, F0-T14 | [H01](packages/W0/H01-guvenli-zemin.md) |
| AIP-05 | Çıkış hata düzeltmeleri | F4-T04, F4-T05, F5-T11, F5-T17*, F6-T03 | [H01](packages/W0/H01-guvenli-zemin.md), [F5-C](packages/W4/F5-C-ode-kimlik.md) |
| AIP-06 | GPU taban ölçümleri ve Leyla referans kümesi | F5-T01, F5-T03, F5-T05, F2-T01, F2-T02 | [M06](packages/W1/M06-gpu-zamanlayici.md), [F5-A](packages/W2/F5-A-sentez-cekirdegi.md), [F2-A](packages/W2/F2-A-final-asr.md) |
| AIP-07 | CPU taban ölçümleri ve ölçülmemiş iddiaların temizlenmesi | F0-T02, F3-T04, F4-T03, F5-T04, F6-T02 | [F0-A](packages/W2/F0-A-ses-girisi.md), [F3-A](packages/W2/F3-A-diyalog-durumu.md), [F4-A](packages/W2/F4-A-normalizasyon-plan.md), [H01](packages/W0/H01-guvenli-zemin.md), [F6-A](packages/W2/F6-A-render-aktarim.md) |
| AIP-08 | Oturum ve kimlik çekirdeği | CC-T01, CC-T02 | [M02](packages/W1/M02-oturum-iptal.md) |
| AIP-09 | Sözleşmeler ve JSON şemaları | F0-T04, F1-T04, F2-T04, F3-T06, F4-T06, F5-T06, F6-T04 | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) |
| AIP-10 | Gözlemlenebilirlik | CC-T03, CC-T04 | [M04](packages/W1/M04-olay-gozlem.md) |
| AIP-11 | Ortak GPU yöneticisi | F5-T16, F2-T07 | [M06](packages/W1/M06-gpu-zamanlayici.md) |
| AIP-12 | Ortak otomotiv sözlüğü | F4-T02, F4-T13, F4-T14, F2-T08, F4-T15 | [M05](packages/W1/M05-ortak-sozluk.md) |
| AIP-13 | Whisper adaptörü, bağlamsal hotword, kalibrasyon/test ayrımı | F2-T05, F2-T06, F2-T09, F2-T30, F2-T33 | [F2-A](packages/W2/F2-A-final-asr.md), [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) |
| AIP-14 | Türkçe ASR normalizer ve mapper | F2-T10, F2-T11, F2-T12, F2-T13 | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) |
| AIP-15 | Phonetic Entity Resolver ve varlık çıkarımı | F2-T14, F2-T15, F2-T16, F2-T17 | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) |
| AIP-16 | Güven, belirsizlik kapısı, sahte metin koruması | F2-T18, F2-T19, F2-T20, F2-T21, F2-T22 | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md), [F2-C](packages/W4/F2-C-akis-tanima.md) |
| AIP-17 | F4 tek normalizasyon otoritesi | F4-T07, F4-T08, F4-T09, F4-T10, F4-T11, F4-T12 | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) |
| AIP-18 | Morfoloji, fonoloji, G2P, vurgu, ulama | F4-T16, F4-T17, F4-T18, F4-T19, F4-T20, F4-T21 | [F4-B](packages/W3/F4-B-fonoloji-g2p.md), [F4-C](packages/W4/F4-C-prozodi.md) |
| AIP-19 | Prozodi, bölümleme, Freya uyumluluğu, kalite kapısı | F4-T22, F4-T23, F4-T24, F4-T25, F4-T26, F4-T28 | [F4-C](packages/W4/F4-C-prozodi.md), [F4-A](packages/W2/F4-A-normalizasyon-plan.md), [F4-B](packages/W3/F4-B-fonoloji-g2p.md) |
| AIP-20 | Tek sentez yolu (sorumluluk göçü) | F5-T08, F4-T27, F5-T09, F6-T05, F6-T06, F6-T08 | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md), [F6-A](packages/W2/F6-A-render-aktarim.md), [F6-C](packages/W4/F6-C-birlestirme-dsp.md) |
| AIP-21 | Terim doğruluğu ölçümü (ara) | F0-T03, F2-T31, F2-T32, F4-T33* | [F0-A](packages/W2/F0-A-ses-girisi.md), [G4](stages/G4-sentetik-kabul.md), [G5](stages/G5-gercek-insan-sip.md) |
| AIP-22 | F0/F1/F5 test derlemleri | F0-T29, F1-T02, F5-T28 | [M08](packages/W1/M08-test-altyapisi.md), [F1-A](packages/W2/F1-A-vad-endpoint.md), [G4](stages/G4-sentetik-kabul.md) |
| AIP-23 | F0 giriş yolu ve düşük gecikmeli çerçeve | F0-T05, F0-T06, F0-T07, F0-T08, F0-T19, F0-T21, F0-T22, F0-T23, F0-T24 | [F0-A](packages/W2/F0-A-ses-girisi.md), [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) |
| AIP-24 | F0 DSP zinciri | F0-T09, F0-T10, F0-T11, F0-T12, F0-T13, F0-T15, F0-T16, F0-T25, F0-T26 | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) |
| AIP-25 | F1 VAD çekirdeği ve gecikme kararı | F1-T06, F1-T07, F1-T08, F1-T09, F1-T10, F1-T11 | [F1-A](packages/W2/F1-A-vad-endpoint.md), [F1-B](packages/W3/F1-B-soz-kesme.md) |
| AIP-26 | Endpointing, semantic turn, pseudo-streaming STT | F1-T12, F1-T13, F1-T14, F1-T15, F1-T16, F1-T17, F2-T23, F2-T24, F2-T25, F2-T26, F2-T27 | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md), [F1-A](packages/W2/F1-A-vad-endpoint.md), [F2-C](packages/W4/F2-C-akis-tanima.md), [F2-A](packages/W2/F2-A-final-asr.md) |
| AIP-27 | F5 sentez çekirdeği | F5-T10, F5-T12, F5-T13, F5-T14, F5-T15, F5-T17, F5-T18, F5-T19, F5-T20, F5-T21 | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md), [F5-B](packages/W3/F5-B-ses-profili-onbellek.md), [H01](packages/W0/H01-guvenli-zemin.md), [F5-C](packages/W4/F5-C-ode-kimlik.md) |
| AIP-28 | F6 rendering zinciri | F6-T07, F6-T09, F6-T10, F6-T11, F6-T12, F6-T13, F6-T14, F6-T15, F6-T16 | [F6-C](packages/W4/F6-C-birlestirme-dsp.md), [F6-A](packages/W2/F6-A-render-aktarim.md) |
| AIP-29 | Oynatma kuyruğu ve F5→F6 akışı | F6-T17, F6-T19, F6-T21, F5-T25, F5-T26 | [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md), [F5-B](packages/W3/F5-B-ses-profili-onbellek.md), [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) |
| AIP-30 | Barge-in 2.0 | F1-T18, F1-T19, F1-T20, F1-T21, F1-T22, F6-T18 | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md), [F1-B](packages/W3/F1-B-soz-kesme.md), [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) |
| AIP-31 | AEC ve RNNoise | F0-T17, F0-T18, F0-T20 | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) |
| AIP-32 | Transport: AudioSocket, chan_websocket, telemetri, AMI/ARI | F6-T20, F6-T22, F6-T23, F6-T24 | [F6-A](packages/W2/F6-A-render-aktarim.md), [F6-D](packages/W5/F6-D-chan-websocket.md), [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) |
| AIP-33 | Ses kimliği doğrulama | F5-T22, F5-T23, F5-T24 | [F5-C](packages/W4/F5-C-ode-kimlik.md) |
| AIP-34 | Bağlam, slot ve durum makinesi | F3-T07, F3-T08, F3-T09, F3-T10, F3-T11 | [F3-A](packages/W2/F3-A-diyalog-durumu.md) |
| AIP-35 | Senaryo kümesi, hibrit router, görev planlayıcı | F3-T40, F3-T12, F3-T13, F3-T14, F3-T15, F3-T16 | [F3-B](packages/W3/F3-B-yonlendirme-onay.md), [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) |
| AIP-36 | Tool Gateway, onay, policy, hafıza | F3-T26, F3-T27, F3-T28, F3-T29, F3-T30 | [M07](packages/W1/M07-guvenlik-politika.md), [F3-B](packages/W3/F3-B-yonlendirme-onay.md), [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) |
| AIP-37 | Yanıt doğrulama ve yol bazında gecikme | F3-T31, F3-T32, F3-T33 | [F3-B](packages/W3/F3-B-yonlendirme-onay.md), [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) |
| AIP-38 | Uzman ajanlar | F3-T17, F3-T18, F3-T19, F3-T24, F3-T25 | [F3-B](packages/W3/F3-B-yonlendirme-onay.md), [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) |
| AIP-39 | RAG ve teknik bilgi ajanı | F3-T20, F3-T21, F3-T22, F3-T23 | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) |
| AIP-40 | Studio API'leri | F0-T27, F1-T23, F2-T28, F3-T34 | [G3](stages/G3-arayuz.md) |
| AIP-41 | Studio arayüzleri | F0-T28, F1-T24, F1-T25, F2-T29, F3-T35, F4-T29, F5-T27, F6-T25 | [G3](stages/G3-arayuz.md) |
| AIP-42 | Laboratuvar testleri | F4-T30, F0-T30, F0-T31, F1-T26, F1-T27, F3-T36, F4-T31, F5-T29, F6-T26 | [F4-B](packages/W3/F4-B-fonoloji-g2p.md), [G4](stages/G4-sentetik-kabul.md) |
| AIP-43 | Ablation deneyleri | F2-T34, F3-T37, F4-T32, F5-T30, F6-T27 | [G4](stages/G4-sentetik-kabul.md) |
| AIP-44 | Uçtan uca regresyon ve bayrak açılışı | F0-T32, F1-T28, F2-T35, F3-T38, F3-T39, F5-T31, F6-T28 | [G4](stages/G4-sentetik-kabul.md) |
| AIP-45 | Gerçek mikrofon ve insan sesi kabulü | F0-T33, F0-T34, F1-T29, F1-T30, F2-T36, F2-T37 | [G5](stages/G5-gercek-insan-sip.md) |
| AIP-46 | Asterisk ve SIP kabulü | F6-T29, F6-T30, F3-T41 | [G5](stages/G5-gercek-insan-sip.md) |
| AIP-47 | İnsan dinleme değerlendirmesi | F4-T33, F5-T32 | [G5](stages/G5-gercek-insan-sip.md) |
| AIP-48 | (İsteğe bağlı) Kontrollü LoRA deneyi | F5-T33 | [F5-D](packages/W5/F5-D-lora.md) |

## Eski görev → paket

| Eski görev | Başlık | Paket | Not |
| --- | --- | --- | --- |
| CC-T01 | `SessionState` + milestone çekirdeğinin canlı `Session`'a bağlanması (bayrak arkasında değil — davranış aynı, yalnızca kimlikler ayrılır); web mesajlarında `generation_id` alanı | [M02](packages/W1/M02-oturum-iptal.md) — Oturum ve iptal çalışma zamanı |  |
| CC-T02 | `Session`'a `THINKING → LISTENING` generation artışı; testler | [M02](packages/W1/M02-oturum-iptal.md) — Oturum ve iptal çalışma zamanı |  |
| CC-T03 | `backend/observability/` + `pipeline_telemetry`'nin `EventEnvelope`'a taşınması (eski fonksiyon sarmalayıcı) | [M04](packages/W1/M04-olay-gozlem.md) — Olay yolu, izleme ve gözlemlenebilirlik |  |
| CC-T04 | Gecikme profili ve p50/p95/p99 raporu | [M04](packages/W1/M04-olay-gozlem.md) — Olay yolu, izleme ve gözlemlenebilirlik |  |
| F0-T01 | PoC DSP davranışını sabitleyen karakterizasyon testleri | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F0-T02 | Taban ölçüm betiği | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T03 | F0 test derlemi | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T04 | Veri sözleşmeleri | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) — Çekirdek veri sözleşmeleri |  |
| F0-T05 | Giriş adaptörü | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T06 | F0Pipeline iskeleti | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T07 | Session entegrasyonu (bayrak arkasında) | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T08 | `car_denoiser.py` uyumluluk katmanı | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T09 | Adaptif HPF | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T10 | Gürültü kestirici | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T11 | Profiller ve profil seçici | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T12 | Spektral gürültü bastırıcı düzeltmeleri | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T13 | Wiener modu | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T14 | Bloklamayan kalibrasyon | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F0-T15 | AGC ve gate | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T16 | Peak limiter ve giriş kırpılma algılayıcı | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T17 | Yankı ölçüm düzeneği | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T18 | AEC adaptörü ve aday değerlendirmesi | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T19 | Web getUserMedia ayarları | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T20 | RNNoise adaptörü | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T21 | Durumlu resampler | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T22 | Çerçeve süresinin küçültülmesi ve olay döngüsü yükü | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T23 | Dispatcher | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T24 | DTMF ham yol | [F0-A](packages/W2/F0-A-ses-girisi.md) — Ses girişi ve temel iyileştirme hattı |  |
| F0-T25 | Kalite analizörü | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T26 | Telemetri | [F0-B](packages/W4/F0-B-uyarlanir-dsp.md) — Uyarlanır araç içi DSP: yankı giderme, gürültü kestirimi ve profiller |  |
| F0-T27 | REST ve WS API | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F0-T28 | Studio paneli | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F0-T29 | Sentetik sinyal üreteci | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F0-T30 | T01–T18 testlerinin uygulanması | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F0-T31 | Laboratuvar raporu | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F0-T32 | Uçtan uca regresyon | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F0-T33 | Gerçek koşul kayıt protokolü | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F0-T34 | DSP açık/kapalı kabul değerlendirmesi | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F1-T01 | Karakterizasyon testleri | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F1-T02 | F1 test derlemi ve etiketleri | [F1-A](packages/W2/F1-A-vad-endpoint.md) — VAD, ön kayıt ve akustik konuşma sonu |  |
| F1-T03 | VAD oturum izolasyonu (hata düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F1-T04 | Sözleşmeler ve çerçeve senkronizörü | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) — Çekirdek veri sözleşmeleri |  |
| F1-T05 | Bölüm iptalinin kaldırılması (hata düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F1-T06 | Birleşik tampon | [F1-A](packages/W2/F1-A-vad-endpoint.md) — VAD, ön kayıt ve akustik konuşma sonu |  |
| F1-T07 | Eski tamponların kaldırılması | [F1-A](packages/W2/F1-A-vad-endpoint.md) — VAD, ön kayıt ve akustik konuşma sonu |  |
| F1-T08 | Histerezisli VAD | [F1-A](packages/W2/F1-A-vad-endpoint.md) — VAD, ön kayıt ve akustik konuşma sonu |  |
| F1-T09 | Adaptif eşik | [F1-A](packages/W2/F1-A-vad-endpoint.md) — VAD, ön kayıt ve akustik konuşma sonu |  |
| F1-T10 | Gecikme bütçesi ölçümü ve karar | [F1-A](packages/W2/F1-A-vad-endpoint.md) — VAD, ön kayıt ve akustik konuşma sonu |  |
| F1-T11 | Olay sınıflandırıcı | [F1-B](packages/W3/F1-B-soz-kesme.md) — İki aşamalı söz kesme (barge-in) |  |
| F1-T12 | Profil tabanlı endpointing | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md) — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel |  |
| F1-T13 | Konuşma hızına uyum | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md) — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel |  |
| F1-T14 | Kontrollü bölümleme | [F1-A](packages/W2/F1-A-vad-endpoint.md) — VAD, ön kayıt ve akustik konuşma sonu |  |
| F1-T15 | Kural tabanının düzeltilmesi ve taşınması | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md) — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel |  |
| F1-T16 | Diyalog bağlamı ve slot doluluğu | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md) — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel |  |
| F1-T17 | Spekülatif STT köprüsü | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md) — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel |  |
| F1-T18 | Double-talk algılayıcı | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md) — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel |  |
| F1-T19 | Bağlamsal backchannel sınıflandırıcı | [F1-C](packages/W4/F1-C-anlamsal-tur-sonu.md) — Anlamsal tur sonu, yankı farkındalığı ve bağlamsal backchannel |  |
| F1-T20 | Barge-in orkestratörü | [F1-B](packages/W3/F1-B-soz-kesme.md) — İki aşamalı söz kesme (barge-in) |  |
| F1-T21 | Utterance Manager | [F1-B](packages/W3/F1-B-soz-kesme.md) — İki aşamalı söz kesme (barge-in) |  |
| F1-T22 | F1 telemetrisi ve gecikme ölçümünün düzeltilmesi | [F1-B](packages/W3/F1-B-soz-kesme.md) — İki aşamalı söz kesme (barge-in) |  |
| F1-T23 | API | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F1-T24 | Ana sayfa | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F1-T25 | Alt sayfalar | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F1-T26 | T01–T22 testleri | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F1-T27 | Laboratuvar raporu | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F1-T28 | Uçtan uca regresyon | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F1-T29 | Gerçek konuşma kayıt protokolü | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F1-T30 | Kabul değerlendirmesi | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F2-T01 | Taban ölçümünün yeniden üretilmesi | [F2-A](packages/W2/F2-A-final-asr.md) — Final ASR ve ham transkript |  |
| F2-T02 | Sıcaklık geri dönüşü ve segment filtresi analizi | [F2-A](packages/W2/F2-A-final-asr.md) — Final ASR ve ham transkript |  |
| F2-T03 | PoC karakterizasyon testleri | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F2-T04 | Sözleşmeler | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) — Çekirdek veri sözleşmeleri |  |
| F2-T05 | Whisper adaptörü ve hotword token ölçümü | [F2-A](packages/W2/F2-A-final-asr.md) — Final ASR ve ham transkript |  |
| F2-T06 | Decode politikası | [F2-A](packages/W2/F2-A-final-asr.md) — Final ASR ve ham transkript |  |
| F2-T07 | Inference Scheduler | [M06](packages/W1/M06-gpu-zamanlayici.md) — GPU kaynak zamanlayıcısı |  |
| F2-T08 | Katalog dizini | [M05](packages/W1/M05-ortak-sozluk.md) — Ortak otomotiv sözlüğü |  |
| F2-T09 | Bağlamsal hotword motoru | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T10 | Normalizer ve N-best doğrulaması | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T11 | Ortak Türkçe sayı ayrıştırıcı | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T12 | Mapper'ın taşınması | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T13 | Gündelik sözcük çakışması ve bağlam kapısı | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T14 | Türkçe fonetik kodlayıcı | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T15 | Aday üretimi ve puanlama | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T16 | Ağırlık kalibrasyonu | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T17 | Varlık çıkarıcı | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T18 | Güven özellikleri | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T19 | Belirsizlik kapısı (kural tabanlı) | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T20 | Güven kalibrasyonu | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T21 | Çok aşamalı koruma | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T22 | Profil seçimi ve RECOVERY | [F2-C](packages/W4/F2-C-akis-tanima.md) — Sözde akış tanıma: kayan pencere, kısmi ve kararlı önek |  |
| F2-T23 | Kayan pencere | [F2-C](packages/W4/F2-C-akis-tanima.md) — Sözde akış tanıma: kayan pencere, kısmi ve kararlı önek |  |
| F2-T24 | Kısmi çözümleme maliyet ölçümü | [F2-C](packages/W4/F2-C-akis-tanima.md) — Sözde akış tanıma: kayan pencere, kısmi ve kararlı önek |  |
| F2-T25 | Partial Transcript Manager | [F2-C](packages/W4/F2-C-akis-tanima.md) — Sözde akış tanıma: kayan pencere, kısmi ve kararlı önek |  |
| F2-T26 | F1.07 bağlantısı | [F2-C](packages/W4/F2-C-akis-tanima.md) — Sözde akış tanıma: kayan pencere, kısmi ve kararlı önek |  |
| F2-T27 | Ortak GPU yöneticisiyle entegrasyon | [F2-A](packages/W2/F2-A-final-asr.md) — Final ASR ve ham transkript |  |
| F2-T28 | API | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F2-T29 | Ana sayfa ve alt sayfalar | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F2-T30 | Metin hattı veri kümesi | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T31 | Akustik sentetik veri kümesi | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F2-T32 | Benchmark aracı | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F2-T33 | Kalibrasyon / test ayrımı | [F2-B](packages/W3/F2-B-baglamsal-duzeltme.md) — Bağlamsal hotword, otomotiv varlık çözümü ve güvenli düzeltme |  |
| F2-T34 | A0–A7 | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F2-T35 | Uçtan uca regresyon | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F2-T36 | İnsan sesi kayıt protokolü | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F2-T37 | Kabul değerlendirmesi | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F3-T01 | Hermetik test altyapısı (LLM fake) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F3-T02 | Karakterizasyon testleri | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F3-T03 | Çoklu araç idempotency doğrulaması ve düzeltmesi (hata düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F3-T04 | Legacy taban ölçümü (A0) | [F3-A](packages/W2/F3-A-diyalog-durumu.md) — Diyalog durumu, slotlar ve korumalı iş akışı |  |
| F3-T05 | Kimlik doğrulamasız özel kayıt paylaşımının kapatılması (güvenlik düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F3-T06 | Sözleşmeler | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) — Çekirdek veri sözleşmeleri |  |
| F3-T07 | Context Manager | [F3-A](packages/W2/F3-A-diyalog-durumu.md) — Diyalog durumu, slotlar ve korumalı iş akışı |  |
| F3-T08 | Slot Manager | [F3-A](packages/W2/F3-A-diyalog-durumu.md) — Diyalog durumu, slotlar ve korumalı iş akışı |  |
| F3-T09 | BookingStateMachine genişletmesi | [F3-A](packages/W2/F3-A-diyalog-durumu.md) — Diyalog durumu, slotlar ve korumalı iş akışı |  |
| F3-T10 | İş akışı modülleri | [F3-A](packages/W2/F3-A-diyalog-durumu.md) — Diyalog durumu, slotlar ve korumalı iş akışı |  |
| F3-T11 | LegacyDialogueAdapter | [F3-A](packages/W2/F3-A-diyalog-durumu.md) — Diyalog durumu, slotlar ve korumalı iş akışı |  |
| F3-T12 | Katman 0 ve kural kapsamı | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T13 | Katman 2–4 entegrasyonu | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T14 | Sınıflandırıcı eğitimi | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T15 | Çoklu niyet ve görev ayrıştırma | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T16 | Görev planlayıcı ve zaman aşımları | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T17 | A01 | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T18 | A04 | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T19 | A05 | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T20 | Belge kaynağı ve lisans kaydı | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T21 | Ingestion ve indeksler | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T22 | Hibrit arama ve kanıt doğrulama | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T23 | A02 | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T24 | A03 | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T25 | A06 | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T26 | Araç kayıt defteri ve izinler | [M07](packages/W1/M07-guvenlik-politika.md) — Güvenlik, yetki ve işlem politikası |  |
| F3-T27 | Yazma araçları ve reconcile | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T28 | Confirmation Manager | [M07](packages/W1/M07-guvenlik-politika.md) — Güvenlik, yetki ve işlem politikası |  |
| F3-T29 | Policy Engine'in merkezileştirilmesi | [M07](packages/W1/M07-guvenlik-politika.md) — Güvenlik, yetki ve işlem politikası |  |
| F3-T30 | Hafıza düzeyleri ve saklama | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T31 | Composer ve Validator | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T32 | Değerlendiriciler | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T33 | Yol bazında gecikme ve LLM azaltma | [F3-C](packages/W4/F3-C-coklu-niyet-rag.md) — Kanıta dayalı teknik bilgi (yerel RAG), çoklu niyet ve sıralı iş akışı |  |
| F3-T34 | API | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F3-T35 | Arayüz | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F3-T36 | T01–T32 testleri | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F3-T37 | Ablation A0–A8 | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F3-T38 | Shadow'un tüm kanallara açılması ve karşılaştırma | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F3-T39 | Uçtan uca regresyon | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F3-T40 | 2 000 senaryoluk küme | [F3-B](packages/W3/F3-B-yonlendirme-onay.md) — Hiyerarşik yönlendirme, uzman ajanlar ve korumalı yazma işlemleri |  |
| F3-T41 | Gerçek görüşme kabulü | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F4-T01 | Karakterizasyon testleri | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F4-T02 | Sözlük uyum raporu | [M05](packages/W1/M05-ortak-sozluk.md) — Ortak otomotiv sözlüğü |  |
| F4-T03 | Taban ölçümü (A0) | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T04 | Tek karakterin yanıtı düşürmesinin önlenmesi (hata düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F4-T05 | Sıra sayısı düzeltmesi (hata düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F4-T06 | Sözleşmeler | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) — Çekirdek veri sözleşmeleri |  |
| F4-T07 | F4 pipeline iskeleti ve tek giriş noktası | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T08 | Çifte normalizasyon koruması | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T09 | Tokenizer | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T10 | Sayı ve para | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T11 | Tarih ve saat | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T12 | Tanımlayıcılar ve birimler | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T13 | Tek sözlük dosyası ve şema | [M05](packages/W1/M05-ortak-sozluk.md) — Ortak otomotiv sözlüğü |  |
| F4-T14 | Kısaltma politikası ve telaffuz eşleyici | [M05](packages/W1/M05-ortak-sozluk.md) — Ortak otomotiv sözlüğü |  |
| F4-T15 | F2 ile paylaşım | [M05](packages/W1/M05-ortak-sozluk.md) — Ortak otomotiv sözlüğü |  |
| F4-T16 | Morfolojinin canlı hatta bağlanması | [F4-B](packages/W3/F4-B-fonoloji-g2p.md) — Türkçe morfoloji, fonoloji, G2P rehberi ve telaffuz varyantları |  |
| F4-T17 | Fonolojik kurallar | [F4-B](packages/W3/F4-B-fonoloji-g2p.md) — Türkçe morfoloji, fonoloji, G2P rehberi ve telaffuz varyantları |  |
| F4-T18 | G2P ve yaklaşık PER | [F4-B](packages/W3/F4-B-fonoloji-g2p.md) — Türkçe morfoloji, fonoloji, G2P rehberi ve telaffuz varyantları |  |
| F4-T19 | Heceleme genişletmesi | [F4-C](packages/W4/F4-C-prozodi.md) — Heceleme, vurgu, klitik/ulama, konuşma eylemi prozodisi ve anlamsal parçalama |  |
| F4-T20 | Vurgu ve cümle odağı | [F4-C](packages/W4/F4-C-prozodi.md) — Heceleme, vurgu, klitik/ulama, konuşma eylemi prozodisi ve anlamsal parçalama |  |
| F4-T21 | Clitic ve ulama | [F4-C](packages/W4/F4-C-prozodi.md) — Heceleme, vurgu, klitik/ulama, konuşma eylemi prozodisi ve anlamsal parçalama |  |
| F4-T22 | Prozodi profilleri | [F4-C](packages/W4/F4-C-prozodi.md) — Heceleme, vurgu, klitik/ulama, konuşma eylemi prozodisi ve anlamsal parçalama |  |
| F4-T23 | Bölümleme ve duraklama planı | [F4-C](packages/W4/F4-C-prozodi.md) — Heceleme, vurgu, klitik/ulama, konuşma eylemi prozodisi ve anlamsal parçalama |  |
| F4-T24 | Ara parça noktalaması akustik testi | [F4-C](packages/W4/F4-C-prozodi.md) — Heceleme, vurgu, klitik/ulama, konuşma eylemi prozodisi ve anlamsal parçalama |  |
| F4-T25 | Adaptör | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T26 | Kalite kapısı ve tersine ayrıştırma | [F4-B](packages/W3/F4-B-fonoloji-g2p.md) — Türkçe morfoloji, fonoloji, G2P rehberi ve telaffuz varyantları |  |
| F4-T27 | Plan tüketimi | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) — Sentez çekirdeği ve ham ses parçası |  |
| F4-T28 | Eğitim/çıkarım normalizer birliği | [F4-A](packages/W2/F4-A-normalizasyon-plan.md) — Tek geçişli normalizasyon ve sentez planı |  |
| F4-T29 | API ve arayüz | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F4-T30 | 3 000 örneklik küme | [F4-B](packages/W3/F4-B-fonoloji-g2p.md) — Türkçe morfoloji, fonoloji, G2P rehberi ve telaffuz varyantları |  |
| F4-T31 | T01–T36 testleri | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F4-T32 | A0–A9 ve regresyon | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F4-T33 | Akustik kabul | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F5-T01 | VRAM ve çıkarım envanteri | [M06](packages/W1/M06-gpu-zamanlayici.md) — GPU kaynak zamanlayıcısı |  |
| F5-T02 | Karakterizasyon testleri | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F5-T03 | Belirleyicilik ve kabul cümlesi kararlılığı analizi | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) — Sentez çekirdeği ve ham ses parçası |  |
| F5-T04 | Ölçülmemiş iddiaların temizlenmesi | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F5-T05 | Leyla referans kümesi | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) — Sentez çekirdeği ve ham ses parçası |  |
| F5-T06 | Sözleşmeler | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) — Çekirdek veri sözleşmeleri |  |
| F5-T07 | Sahte çıkarım motoru | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F5-T08 | Model adaptörü ve model kaydı | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) — Sentez çekirdeği ve ham ses parçası |  |
| F5-T09 | F5'ten metin dönüşümünün ve sessizliğin kaldırılması | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) — Sentez çekirdeği ve ham ses parçası |  |
| F5-T10 | Duration Guard | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) — Sentez çekirdeği ve ham ses parçası |  |
| F5-T11 | Seed yöneticisi ve seed düşürmelerinin kaldırılması (hata düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F5-T12 | Gerçek uzunlukta gürültü ve öğe başına VAE | [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma |  |
| F5-T13 | Ses profilleri | [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma |  |
| F5-T14 | Önbellek düzeyleri | [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma |  |
| F5-T15 | Ön ısıtma | [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma |  |
| F5-T16 | Ortak GPU yöneticisi | [M06](packages/W1/M06-gpu-zamanlayici.md) — GPU kaynak zamanlayıcısı |  |
| F5-T17 | Yığınlama ve iptal filtresi | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri, [F5-C](packages/W4/F5-C-ode-kimlik.md) — ODE profil seçimi, son tarih duyarlı toplu iş, ses kimliği ve perde ölçümü | yalnızca iptal filtresi; kalan kısım |
| F5-T18 | ODE profil karşılaştırması | [F5-C](packages/W4/F5-C-ode-kimlik.md) — ODE profil seçimi, son tarih duyarlı toplu iş, ses kimliği ve perde ölçümü |  |
| F5-T19 | Kod çözücü ölçümü ve optimizasyonu | [F5-C](packages/W4/F5-C-ode-kimlik.md) — ODE profil seçimi, son tarih duyarlı toplu iş, ses kimliği ve perde ölçümü |  |
| F5-T20 | Q1 hızlı denetim | [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma |  |
| F5-T21 | Kontrollü yeniden sentez | [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma |  |
| F5-T22 | Speaker encoder seçimi ve lisansı | [F5-C](packages/W4/F5-C-ode-kimlik.md) — ODE profil seçimi, son tarih duyarlı toplu iş, ses kimliği ve perde ölçümü |  |
| F5-T23 | Kimlik doğrulama ve eşik kalibrasyonu | [F5-C](packages/W4/F5-C-ode-kimlik.md) — ODE profil seçimi, son tarih duyarlı toplu iş, ses kimliği ve perde ölçümü |  |
| F5-T24 | Drift analizörü | [F5-C](packages/W4/F5-C-ode-kimlik.md) — ODE profil seçimi, son tarih duyarlı toplu iş, ses kimliği ve perde ölçümü |  |
| F5-T25 | Chunk dispatcher | [F5-B](packages/W3/F5-B-ses-profili-onbellek.md) — Gerçek uzunlukta latent, toplu iş yalıtımı, güvenli önbellek ve aynı seed'le kurtarma |  |
| F5-T26 | F6'ya ham ses teslimi | [F5-A](packages/W2/F5-A-sentez-cekirdegi.md) — Sentez çekirdeği ve ham ses parçası |  |
| F5-T27 | API ve arayüz | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F5-T28 | 2 000 girdilik küme | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F5-T29 | T01–T40 testleri | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F5-T30 | A0–A10 ve kapasite ölçümü | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F5-T31 | Uçtan uca regresyon | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F5-T32 | İnsan değerlendirmesi | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F5-T33 | Kontrollü LoRA deneyi | [F5-D](packages/W5/F5-D-lora.md) — LoRA ile otomotiv ses uyarlaması araştırması |  |
| F6-T01 | Karakterizasyon testleri | [M08](packages/W1/M08-test-altyapisi.md) — Ortak test altyapısı ve çekirdek entegrasyon koşucusu |  |
| F6-T02 | Taban ölçüm (A0) | [F6-A](packages/W2/F6-A-render-aktarim.md) — Durumlu render, çerçeveleme ve aktarım |  |
| F6-T03 | Ağ yazma zaman aşımı (hata düzeltmesi) | [H01](packages/W0/H01-guvenli-zemin.md) — Güvenli zemin: canlı hata ve güvenlik düzeltmeleri |  |
| F6-T04 | Sözleşmeler | [M01](packages/W1/M01-cekirdek-sozlesmeler.md) — Çekirdek veri sözleşmeleri |  |
| F6-T05 | Durumlu rendering iskeleti | [F6-A](packages/W2/F6-A-render-aktarim.md) — Durumlu render, çerçeveleme ve aktarım |  |
| F6-T06 | Birleştirme ve sınır yumuşatma | [F6-C](packages/W4/F6-C-birlestirme-dsp.md) — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı |  |
| F6-T07 | WSOLA | [F6-C](packages/W4/F6-C-birlestirme-dsp.md) — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı |  |
| F6-T08 | Duraklama uygulama | [F6-C](packages/W4/F6-C-birlestirme-dsp.md) — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı |  |
| F6-T09 | De-esser | [F6-C](packages/W4/F6-C-birlestirme-dsp.md) — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı |  |
| F6-T10 | Durumlu EQ | [F6-A](packages/W2/F6-A-render-aktarim.md) — Durumlu render, çerçeveleme ve aktarım |  |
| F6-T11 | Loudness ve zarf tabanlı limiter | [F6-C](packages/W4/F6-C-birlestirme-dsp.md) — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı |  |
| F6-T12 | Comfort noise | [F6-C](packages/W4/F6-C-birlestirme-dsp.md) — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı |  |
| F6-T13 | Akış boyunca durumlu yeniden örnekleme | [F6-A](packages/W2/F6-A-render-aktarim.md) — Durumlu render, çerçeveleme ve aktarım |  |
| F6-T14 | Codec laboratuvarı | [F6-C](packages/W4/F6-C-birlestirme-dsp.md) — Parça birleştirme, WSOLA, anlamsal duraklama, çıkış DSP'si ve kodek laboratuvarı |  |
| F6-T15 | Çerçeve yöneticisi | [F6-A](packages/W2/F6-A-render-aktarim.md) — Durumlu render, çerçeveleme ve aktarım |  |
| F6-T16 | Tek pacer | [F6-A](packages/W2/F6-A-render-aktarim.md) — Durumlu render, çerçeveleme ve aktarım |  |
| F6-T17 | Oynatma kuyruğu | [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) — Sınırlı oynatma kuyruğu, gönderim çiti ve makbuzlar |  |
| F6-T18 | Barge-in köprüsü | [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) — Sınırlı oynatma kuyruğu, gönderim çiti ve makbuzlar |  |
| F6-T19 | Hata yönetimi | [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) — Sınırlı oynatma kuyruğu, gönderim çiti ve makbuzlar |  |
| F6-T20 | AudioSocket adaptörü ve güvenlik | [F6-A](packages/W2/F6-A-render-aktarim.md) — Durumlu render, çerçeveleme ve aktarım |  |
| F6-T21 | Tarayıcı oynatma makbuzları | [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) — Sınırlı oynatma kuyruğu, gönderim çiti ve makbuzlar |  |
| F6-T22 | chan_websocket | [F6-D](packages/W5/F6-D-chan-websocket.md) — İsteğe bağlı Asterisk chan_websocket aktarımı ve PBX entegrasyon sertleştirmesi |  |
| F6-T23 | Telemetri ve gecikme ayrıştırması | [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) — Sınırlı oynatma kuyruğu, gönderim çiti ve makbuzlar |  |
| F6-T24 | AMI/ARI ve doğrulanmış aktarım | [F6-B](packages/W3/F6-B-oynatma-kuyrugu.md) — Sınırlı oynatma kuyruğu, gönderim çiti ve makbuzlar |  |
| F6-T25 | API ve arayüz | [G3](stages/G3-arayuz.md) — Ortak Freya kokpiti (arayüz) |  |
| F6-T26 | T01–T48 testleri | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F6-T27 | A0–A11 | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F6-T28 | Sentetik görüşme regresyonu | [G4](stages/G4-sentetik-kabul.md) — Sentetik ürün kabulü ve kapsamlı benchmark |  |
| F6-T29 | L0–L5 kabul laboratuvarı | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
| F6-T30 | L6 | [G5](stages/G5-gercek-insan-sip.md) — Gerçek insan sesi ve SIP kabulü |  |
