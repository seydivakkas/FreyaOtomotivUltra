# H01 kapsam sapmaları — karar önerisi

Durum: ONAY BEKLİYOR. H01-G00 HOLD; kapsam kapısı bu dosya ile otomatik geçmez.

Mevcut H01 kod PR'ında ilk §4 listesinin dışına çıkan değişiklikler, gerekçeleri ve kabul koşulları:

| Yol | Gerekçe | Kanıt / koşul |
| --- | --- | --- |
| `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml` | Eksik python-multipart, hermetik CI, test işaretleri | Kilit doğrulaması, HF01/HF02, verify |
| `backend/config.py`, `backend/gpu_health_circuit_breaker.py` | AI bildirimi konfigürasyonu ve tembel torch | H01.01/.14 regresyonları |
| `alembic.ini`, `migrations/versions/025_caller_profiles.py` | Modül yolu ve ORM/göç şeması uyumu | alembic upgrade head / check |
| `frontend/src/SidebarNav.tsx`, `frontend/src/MilestonePanel.tsx`, `frontend/tests/ui.spec.ts` | V3 erişilebilir navigasyon ve gerçek normalizasyon sonucu | Yedi Playwright testi korunur; gerçek UI çıktısı |
| Mevcut `tests/test_*.py`, `tests/fakes/__init__.py`, `tests/h01/__init__.py` | Davranış değişikliğine uygun regresyon ve sahte sağlayıcılar | Test silinmez; önce/sonra farkı gerekçeli |

Kapsam listesinin güncellenmesi ancak ürün sahibi incelemesi ve paket kayıt denetimi (`python scripts/build_registry.py --check`) ardından ayrı plan değişikliğiyle yapılır. Bu öneri plan dosyasının §4'ünü veya kabul ölçütünü değiştirmez. [H01 kod PR #3](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC/pull/3).

Ek karar: ADR-X-03 giden arama bildirimindeki "ulaştınız" ifadesi ürün sahibinin onayı olmadan değiştirilmez.
