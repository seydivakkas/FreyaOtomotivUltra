# FreyaOtomotivUltra

**FreyaTTS Automotive ses işleme hattının geliştirme planı.**

Bu repo **yalnızca plan** içerir. Kod [`seydivakkas/FreyaTTS_Automotive_PoC`](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC) reposunda yazılmaya devam eder. Buradaki belgeler, bir geliştiricinin veya kodlama ajanının PoC reposunda neyi, hangi sırayla ve hangi kabul kriterine göre yapacağını tanımlar.

## Hedef

Yerel çalışan, Türkçe konuşan, telefon ve mikrofon üzerinden otomotiv işlemlerini (randevu, ekspertiz, araç bilgisi) yürüten sesli asistanın ses işleme hattını gerçek zamanlı telefon görüşmelerine hazır hale getirmek.

- **Donanım:** RTX 4070 8 GB üzerinde çevrimdışı çalışma
- **İlke:** Yeni ağır modeller eklemek yerine mevcut modelleri (Faster-Whisper Large V3 Turbo, Qwen 2.5 7B, FreyaTTS) daha verimli ve koordineli çalıştırmak
- **Ölçüt:** Başarı, sesin daha temiz duyulmasıyla değil; otomotiv terim doğruluğu, STT doğruluğu ve görüşme gecikmesiyle ölçülür

## Ses işleme hattı (F0–F6)

| Aşama | Ad | Plan durumu |
| --- | --- | --- |
| [F0](docs/stages/F0-audio-acquisition/spec.md) | Audio Acquisition & Enhancement | ✅ Plan hazır |
| [F1](docs/stages/F1-voice-turn-detection/spec.md) | Voice Activity & Turn Detection | ✅ Plan hazır |
| [F2](docs/stages/F2-speech-recognition/spec.md) | Speech Recognition & Understanding | ✅ Plan hazır |
| [F3](docs/stages/F3-dialogue-intelligence/spec.md) | Dialogue Intelligence & Multi-Agent Orchestration | ✅ Plan hazır |
| [F4](docs/stages/F4-linguistic-frontend/spec.md) | Turkish Linguistic Frontend & Prosody Intelligence | ✅ Plan hazır |
| [F5](docs/stages/F5-neural-synthesis/spec.md) | Neural Speech Synthesis & Voice Identity Intelligence | ✅ Plan hazır |
| F6 | Audio Rendering & Transport | ⏳ Planlanıyor |

> Bu tablo **planlama** ilerlemesini gösterir; kod geliştirme veya test durumunu göstermez.

Her aşama klasöründe üç dosya bulunur:

| Dosya | İçerik |
| --- | --- |
| `spec.md` | Amaç, kapsam, PoC'taki mevcut durum, bileşenler, veri sözleşmeleri, PoC'tan taşıma |
| `tasks.md` | Kimlikli görevler (`F0-T01`…), sprintler, dosyalar, bağımlılıklar, "bitti" tanımı |
| `acceptance.md` | Kabul kriterleri, test senaryoları ve aşama kapıları |

## Yol kuralı

Belgelerdeki dosya yolları:

- `backend/`, `frontend/`, `tests/`, `scripts/`, `config/`, `data/`, `experimental/`, `automotive_voice/` ile başlıyorsa → **PoC reposu**
- `docs/` ile başlıyorsa → **bu plan reposu**

## Ölçüm dürüstlüğü

- Kabul kriterlerindeki değerler, test çalıştırılıp sonucu rapora yazılmadan "tamam" işaretlenmez.
- İnsan değerlendirmesi gerektiren ölçümler (MOS, ABX) simüle edilerek başarılı gösterilmez.
- Arayüzlerde gerçek ölçüm yokken "Ölçüm bekleniyor" gösterilir; temsili sinyaller açıkça etiketlenir.
- Sentetik testlerin başarısı gerçek görüşmelerin başarısını tek başına kanıtlamaz; her aşama gerçek ses ve SIP kabulüyle kapanır.
