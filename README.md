# FreyaOtomotivUltra

**FreyaTTS Automotive — Freya 2.0 geliştirme planı.**

Bu repo **yalnızca plan** içerir. Kod [`seydivakkas/FreyaTTS_Automotive_PoC`](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC) reposunda yazılmaya devam eder. Buradaki belgeler, bir geliştiricinin veya kodlama ajanının PoC reposunda neyi, hangi sırayla ve hangi kabul kriterine göre yapacağını tanımlar.

> **Kodlama ajanı mısınız?** [`CLAUDE.md`](CLAUDE.md) ile başlayın, sonra [`docs/execution/README.md`](docs/execution/README.md).

## Hedef

Yerel çalışan, Türkçe konuşan, telefon ve mikrofon üzerinden otomotiv işlemlerini (randevu, ekspertiz, servis durumu, bilgi, operatöre aktarım) yürüten sesli asistanı gerçek telefon görüşmelerine hazır hale getirmek.

- **Donanım:** RTX 4070 Laptop 8 GB üzerinde çevrimdışı çalışma
- **İlke:** Yeni ağır model eklemek yerine mevcut modelleri (Faster-Whisper large-v3-turbo, Qwen 2.5 7B, FreyaTTS) daha verimli ve koordineli çalıştırmak
- **Ölçüt:** Otomotiv terim doğruluğu (bugün %48,04 → hedef %95), görüşme gecikmesi (ilk ses hedefi 1,2 s) ve söz kesme davranışı

## Belgeler

| Bölüm | İçerik |
| --- | --- |
| [`CLAUDE.md`](CLAUDE.md) | Kodlama ajanının çalışma kuralları (tek kural kaynağı) |
| [`docs/execution/`](docs/execution/README.md) | **Freya 2.0 yürütme planı:** [ana plan](docs/execution/master-plan.md) · [yürütme sırası](docs/execution/execution-order.md) · [paketler](docs/execution/packages/) · [ürün aşamaları G2–G5](docs/execution/stages/) · [kararlar](docs/execution/decisions.md) · [riskler](docs/execution/risks.md) · [kanıt kuralları](docs/execution/evidence.md) |
| [`docs/00-overview/`](docs/00-overview/vision-and-scope.md) | [Vizyon ve kapsam](docs/00-overview/vision-and-scope.md) · [Mevcut durum ve bulgular](docs/00-overview/current-state.md) · [Kısıtlar](docs/00-overview/constraints.md) · [Sözlük](docs/00-overview/glossary.md) |
| [`docs/01-architecture/`](docs/01-architecture/pipeline-v2.md) | [Hat v2](docs/01-architecture/pipeline-v2.md) · [Birleşik sözleşmeler](docs/01-architecture/interfaces.md) · [Kod düzeni](docs/01-architecture/code-layout.md) · [Gecikme bütçesi](docs/01-architecture/latency-budget.md) · [ADR dizini](docs/01-architecture/adr/README.md) |
| [`docs/stages/`](#ses-işleme-hattı-f0f6) | Yedi katmanın `spec.md`, `tasks.md`, `acceptance.md` dosyaları |
| [`docs/cross-cutting/`](docs/cross-cutting/README.md) | GPU yöneticisi, oturum ve durum, gözlemlenebilirlik, güvenlik ve KVKK, ortak sözlük, yapılandırma, hata kurtarma |
| [`docs/roadmap/`](docs/roadmap/roadmap.md) | [AP01–AP13 eşlemesi](docs/roadmap/roadmap.md) · [eski AIP planı (emekli)](docs/roadmap/master-plan.md) |
| [`docs/testing/`](docs/testing/measurement-plan.md) | [Ölçüm planı](docs/testing/measurement-plan.md) · [Veri kümeleri](docs/testing/datasets.md) · [Kabul kapıları](docs/testing/acceptance-gates.md) |
| [`docs/migration/`](docs/migration/from-poc.md) | PoC'tan geçiş |

## Ses işleme hattı (F0–F6)

| Aşama | Ad | Görev | Sprint | Plan |
| --- | --- | --- | --- | --- |
| [F0](docs/stages/F0-audio-acquisition/spec.md) | Audio Acquisition & Enhancement | 34 | 11 | ✅ |
| [F1](docs/stages/F1-voice-turn-detection/spec.md) | Voice Activity & Turn Detection | 30 | 14 | ✅ |
| [F2](docs/stages/F2-speech-recognition/spec.md) | Speech Recognition & Understanding | 37 | 19 | ✅ |
| [F3](docs/stages/F3-dialogue-intelligence/spec.md) | Dialogue Intelligence & Multi-Agent Orchestration | 41 | 25 | ✅ |
| [F4](docs/stages/F4-linguistic-frontend/spec.md) | Turkish Linguistic Frontend & Prosody Intelligence | 33 | 23 | ✅ |
| [F5](docs/stages/F5-neural-synthesis/spec.md) | Neural Speech Synthesis & Voice Identity Intelligence | 33 | 26 | ✅ |
| [F6](docs/stages/F6-rendering-transport/spec.md) | Audio Rendering, DSP & Telephony Transport Intelligence | 30 | 28 | ✅ |
| [Ortak](docs/cross-cutting/README.md) | GPU, oturum, gözlem, güvenlik, sözlük, hata kurtarma | 4 | — | ✅ |

> Bu tablo **planlama** durumunu gösterir; kod geliştirme veya test durumunu göstermez.

Her aşama klasöründe üç dosya bulunur:

| Dosya | İçerik |
| --- | --- |
| `spec.md` | Amaç, kapsam, PoC'taki doğrulanmış durum ve bulgular, bileşenler, veri sözleşmeleri, PoC'tan taşıma |
| `tasks.md` | Teknik görev ayrıntısı (`F0-T01`…). Yürütme birimi değildir; hangi pakette yapıldığı [`legacy-mapping.md`](docs/execution/legacy-mapping.md)'de |
| `acceptance.md` | Kabul kriterleri, test senaryoları ve aşama kapıları |

## Uygulama sırası

[Yürütme planı](docs/execution/master-plan.md) işi dalgalara ayrılmış **paketlere** böler; her paket tek oturumda bir ajanın uygulayacağı, kendi testleri ve kabul kapılarıyla kapanan birimdir. Sıra ve bağımlılıklar: [execution-order.md](docs/execution/execution-order.md).

| Dalga | İçerik |
| --- | --- |
| W0 | M00 salt okunur envanter · H01 güvenli zemin (bayraktan bağımsız canlı hata ve güvenlik düzeltmeleri, hermetik test) |
| W1 | Ortak çekirdek M01–M08 (sözleşmeler, oturum/iptal, yapılandırma, gözlem, otomotiv sözlüğü, GPU zamanlayıcı, güvenlik, test altyapısı) → CORE_GATE |
| W2 | F0-A … F6-A uçtan uca dikey dilim → W2_GATE |
| W3 | Söz kesme, oynatma kuyruğu, **otomotiv terim düzeltme**, onaylı işlem, **Türkçe fonoloji/G2P**, ses profili ve önbellek |
| W4 | Uyarlanır DSP/AEC, akış tanıma, anlamsal tur sonu, çoklu niyet ve RAG, prozodi, ODE profilleri, gelişmiş render |
| W5 | İsteğe bağlı chan_websocket aktarımı · LoRA araştırması (yalnız gerçek atfedilmiş hata varsa) |
| G2 → G5 | Entegrasyon incelemesi → ortak kokpit arayüzü → sentetik ürün kabulü → gerçek insan sesi ve SIP kabulü → pilot kararı |

Sayılar (görev/test/kapı) [`registry.json`](docs/execution/registry.json) içindedir ve **plan** sayısıdır; çalıştırılmış test sayısı değildir.

## Yol kuralı

Belgelerdeki dosya yolları:

- `backend/`, `frontend/`, `tests/`, `scripts/`, `config/`, `data/`, `contracts/`, `experimental/`, `automotive_voice/`, `asterisk/` ile başlıyorsa → **PoC reposu**
- `docs/` ile başlıyorsa → **bu plan reposu**

## Ölçüm dürüstlüğü

- Kabul kriterlerindeki değerler, test çalıştırılıp sonucu rapora yazılmadan "tamam" işaretlenmez.
- İnsan değerlendirmesi gerektiren ölçümler (MOS, ABX) simüle edilerek başarılı gösterilmez.
- Arayüzlerde gerçek ölçüm yokken "Ölçüm bekleniyor" gösterilir; temsili sinyaller açıkça etiketlenir.
- Sentetik testlerin başarısı gerçek görüşmelerin başarısını tek başına kanıtlamaz; ürün G5 gerçek ses ve SIP kabulüyle kapanır.

## Kullanıcı kararı bekleyen sorular

[Ana plan §Açık kararlar](docs/execution/master-plan.md#açık-kararlar): özel kayıt okumada ikinci kimlik etkeni (ADR-F3-01), karşılamada yapay zekâ bildirimi (K-06), saat ve telefon numarası okuma biçimi, sözlük onay yetkilisi, üretim topolojisi (ADR-X-01), RAG gömme modeli.
