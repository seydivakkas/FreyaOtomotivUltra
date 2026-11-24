# Ortak katman

F0–F6'nın tamamını yöneten bileşenler. Her biri tek yerde uygulanır ve aşamalar tarafından kullanılır; hiçbir aşama kendi kopyasını yazmaz.

| Belge | Bileşen | Kod (PoC) | Yol haritası |
| --- | --- | --- | --- |
| [gpu-resource-manager.md](gpu-resource-manager.md) | GPU Resource Manager: öncelik, VRAM bütçesi, iptal | `backend/runtime_resources/` | AP08 |
| [session-and-state.md](session-and-state.md) | Oturum, kimlikler, generation, iptal, kalıcılık | `backend/session_state/` (`automotive_voice/core` temelli) | — |
| [observability.md](observability.md) | Olaylar, gecikme profili, ses kalitesi izleme, Studio veri kaynağı | `backend/observability/` | AP10 |
| [security-and-privacy.md](security-and-privacy.md) | KVKK, kimlik doğrulama, kayıt, transport güvenliği | Mevcut KVKK modülleri + `supervisor/policy.py` | — |
| [shared-lexicon.md](shared-lexicon.md) | F2 tanıma ↔ F4 seslendirme ortak sözlüğü | `config/linguistics/automotive_lexicon.json` | AP05, AP06 |
| [configuration.md](configuration.md) | Bayraklar, profiller, yapılandırma kaydı | `backend/config.py`, `config/` | — |
| [fault-recovery.md](fault-recovery.md) | Hata sınıfları ve kurtarma | Mevcut `CircuitBreaker` + aşama kurtarma tabloları | AP09 |

Ölçüm ve test altyapısı (sentetik test motoru, akustik laboratuvar) [`docs/testing/`](../testing/measurement-plan.md) altındadır.
