# Kısıtlar

## Donanım

| Kaynak | Değer | Not |
| --- | --- | --- |
| GPU | NVIDIA RTX 4070 Laptop, 8188 MiB VRAM | Tek GPU; STT, LLM ve TTS paylaşır |
| Ölçülmüş tepe VRAM | 7478 MiB (%91,3) | Ön ısıtmadan önce, masaüstü uygulamaları (~1770 MiB) dahil |
| Boş pay | ≈ 710 MiB | Yeni model için yer yok |
| CPU işleri | F0, F1 (Silero), F4, F6, RAG gömme modeli | GPU bütçesi 0 MB |

**Sonuç:** Yeni ağır model yüklenmez. Her GPU işi ortak yöneticiden geçer. Model başına bellek dağılımı F5-T01 ile ölçülür ve [gpu-resource-manager](../cross-cutting/gpu-resource-manager.md) bütçesine girer.

## Modeller (değiştirilmez)

| Rol | Model | Çalışma |
| --- | --- | --- |
| STT | Faster-Whisper large-v3-turbo | CUDA FP16, tek örnek |
| LLM | Qwen 2.5 7B | Ollama (loopback), tek örnek |
| TTS | FreyaTTS (karakter düzeyinde DiT + Euler ODE 32 adım + AudioVAE, 48 kHz, 25 latent kare/s) | Tek örnek, Leyla, seed 9 |
| VAD | Silero VAD | CPU, 16 kHz, 512 örnek blok; oturum başına durum |

FreyaTTS ağırlıkları değiştirilmez. Kontrollü LoRA denemesi yalnızca F5-S26'da, ayrı model sürümü olarak yapılır.

## Yazılım

| Konu | Değer |
| --- | --- |
| Python | `>=3.11,<3.12` (PoC `pyproject.toml`) — `audioop` 3.13'te kaldırıldığı için codec laboratuvarı kendi G.711 uygulamasını kullanır |
| Backend | FastAPI, SQLAlchemy 2, Alembic, pydantic-settings, numpy, scipy, soxr |
| Frontend | React (Vite), TypeScript |
| İşletim sistemi | Windows (CUDA). Asterisk Linux'ta: pilot ve geliştirmede aynı makinede (WSL2/VM, loopback), üretimde ayrı sunucuda ([ADR-X-01](../01-architecture/adr/ADR-X-01-asterisk-dagitim.md)) |
| Telefoni | Asterisk AudioSocket (ana yol; 8 kHz slin16, 20 ms, 320 B), chan_websocket (aday; Asterisk 20.16 / 21.11 / 22.6 / 23.0 ve sonrası), AMI/ARI |

## Çalışma ilkeleri

- **Offline-first:** Görüşme sırasında internet gerekmez. Ollama yalnızca loopback adresine bağlanır.
- **Gerçek zamanlı medya:** 20 ms çerçeve; ağ yazması hiçbir zaman süresiz bloklamaz.
- **Eşzamanlı görüşme:** `max_concurrent_calls = 50` yapılandırma değeridir, ölçülmüş kapasite değildir (F5 N10). Kapasite F5-T30 ile ölçülür ve yapılandırma ölçülen değere çekilir.

## Hukuki ve kurumsal

- **KVKK:** Ham ses kaydı varsayılan kapalı; saklama süreleri ve silme talebi mevcut `kvkk_compliance.py` üzerinden. Ayrıntı: [security-and-privacy](../cross-cutting/security-and-privacy.md).
- **Lisans:** PoC kaynak dosyaları "ÖZEL LİSANS — TÜM HAKLAR SAKLIDIR" başlığı taşır. Üçüncü taraf bileşen (RNNoise, speaker encoder, AEC kütüphanesi, RAG belgeleri) eklenmeden önce lisansı kaydedilir (F0 ADR-F0-03, F5-T22, F3-T20).
- **Güvenlik:** AudioSocket şifresiz ve kimlik doğrulamasızdır; yalnızca loopback, özel ağ veya tünel üzerinden açılır.

## Kapsam disiplini

- Yeni bileşen eklemeden önce PoC'ta (canlı, `experimental/`, `automotive_voice/`) karşılığı aranır. Bulunan karşılık genişletilir; paralel ikinci uygulama yazılmaz.
- Bir aşamanın işi başka aşamada tekrar yapılmaz (ör. duraklama yalnızca F6'da, normalizasyon yalnızca F4'te).
