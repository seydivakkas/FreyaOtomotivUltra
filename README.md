# FreyaOtomotivUltra

**FreyaTTS Automotive — Freya 2.0 geliştirme planı.**

Bu repo **yalnızca plan** içerir. Kod [`seydivakkas/FreyaTTS_Automotive_PoC`](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC) reposunda yazılmaya devam eder. Buradaki belgeler, bir geliştiricinin veya kodlama ajanının PoC reposunda neyi, hangi sırayla ve hangi kabul kriterine göre yapacağını tanımlar.

> **Kodlama ajanı mısınız?** [`CLAUDE.md`](CLAUDE.md) ile başlayın, sonra [`docs/roadmap/master-plan.md`](docs/roadmap/master-plan.md).

## Hedef

Yerel çalışan, Türkçe konuşan, telefon ve mikrofon üzerinden otomotiv işlemlerini (randevu, ekspertiz, servis durumu, bilgi, operatöre aktarım) yürüten sesli asistanı gerçek telefon görüşmelerine hazır hale getirmek.

- **Donanım:** RTX 4070 Laptop 8 GB üzerinde çevrimdışı çalışma
- **İlke:** Yeni ağır model eklemek yerine mevcut modelleri (Faster-Whisper large-v3-turbo, Qwen 2.5 7B, FreyaTTS) daha verimli ve koordineli çalıştırmak
- **Ölçüt:** Otomotiv terim doğruluğu (bugün %48,04 → hedef %95), görüşme gecikmesi (ilk ses hedefi 1,2 s) ve söz kesme davranışı

## Belgeler

| Bölüm | İçerik |
| --- | --- |
| [`CLAUDE.md`](CLAUDE.md) | Kodlama ajanının çalışma kuralları |
| [`docs/00-overview/`](docs/00-overview/vision-and-scope.md) | [Vizyon ve kapsam](docs/00-overview/vision-and-scope.md) · [Mevcut durum ve bulgular](docs/00-overview/current-state.md) · [Kısıtlar](docs/00-overview/constraints.md) · [Sözlük](docs/00-overview/glossary.md) |
| [`docs/01-architecture/`](docs/01-architecture/pipeline-v2.md) | [Hat v2](docs/01-architecture/pipeline-v2.md) · [Birleşik sözleşmeler](docs/01-architecture/interfaces.md) · [Kod düzeni](docs/01-architecture/code-layout.md) · [Gecikme bütçesi](docs/01-architecture/latency-budget.md) · [ADR dizini](docs/01-architecture/adr/README.md) |
| [`docs/stages/`](#ses-işleme-hattı-f0f6) | Yedi katmanın `spec.md`, `tasks.md`, `acceptance.md` dosyaları |
| [`docs/cross-cutting/`](docs/cross-cutting/README.md) | GPU yöneticisi, oturum ve durum, gözlemlenebilirlik, güvenlik ve KVKK, ortak sözlük, yapılandırma, hata kurtarma |
| [`docs/roadmap/`](docs/roadmap/master-plan.md) | [**Freya 2.0 Master Development Plan**](docs/roadmap/master-plan.md) · [AP01–AP13 eşlemesi](docs/roadmap/roadmap.md) |
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
| `tasks.md` | Kimlikli görevler (`F0-T01`…), sprintler, dosyalar, bağımlılıklar, "bitti" tanımı |
| `acceptance.md` | Kabul kriterleri, test senaryoları ve aşama kapıları |

## Uygulama sırası

[Master plan](docs/roadmap/master-plan.md) 242 görevi 48 uygulama paketine (AIP) ve 8 faza böler:

| Faz | İçerik |
| --- | --- |
| 0 | Güvenlik açıkları ve canlı hatalar (bayraktan bağımsız), hermetik test, taban ölçümler |
| 1 | Ortak temel: sözleşmeler, kimlikler, telemetri, GPU yöneticisi |
| 2 | **Terim doğruluğu:** ortak sözlük, F2 Entity Resolver, F4 Türkçe telaffuz, tek sentez yolu |
| 3 | Gecikme ve kesinti: F0/F1 düşük gecikme, semantic turn, pseudo-streaming STT, F5/F6 |
| 4 | Diyalog orkestrasyonu (AP13) — Faz 2–3 ile paralel |
| 5 | Studio arayüzleri |
| 6 | Sentetik laboratuvar, ablation, uçtan uca regresyon |
| 7 | Gerçek mikrofon, insan sesi, Asterisk/SIP kabulü |

## Yol kuralı

Belgelerdeki dosya yolları:

- `backend/`, `frontend/`, `tests/`, `scripts/`, `config/`, `data/`, `contracts/`, `experimental/`, `automotive_voice/`, `asterisk/` ile başlıyorsa → **PoC reposu**
- `docs/` ile başlıyorsa → **bu plan reposu**

## Ölçüm dürüstlüğü

- Kabul kriterlerindeki değerler, test çalıştırılıp sonucu rapora yazılmadan "tamam" işaretlenmez.
- İnsan değerlendirmesi gerektiren ölçümler (MOS, ABX) simüle edilerek başarılı gösterilmez.
- Arayüzlerde gerçek ölçüm yokken "Ölçüm bekleniyor" gösterilir; temsili sinyaller açıkça etiketlenir.
- Sentetik testlerin başarısı gerçek görüşmelerin başarısını tek başına kanıtlamaz; her aşama gerçek ses ve SIP kabulüyle kapanır.

## Kullanıcı kararı bekleyen sorular

[ADR dizini](docs/01-architecture/adr/README.md#kullanıcı-kararı-bekleyen-sorular): özel kayıt okumada ikinci kimlik etkeni (ADR-F3-01), saat okuma biçimi (ADR-F4-02), telefon numarası okuma biçimi, sözlük onay yetkilisi, üretim topolojisi (ADR-X-01).
