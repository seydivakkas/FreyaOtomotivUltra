## Plan değişikliği

- **Tür:** Paket / Aşama / Sözleşme / Kabul kriteri / ADR / Ortak katman / Diğer
- **Etkilenen belgeler:**
- **Etkilenen paketler:**

## Kontrol listesi

- [ ] `python scripts/build_registry.py --check` temiz (kimlikler benzersiz, `Önkoşullar`/`Sonraki` tutarlı, bölümler şablona uygun, bağlantılar çalışıyor)
- [ ] Paket dosyası değiştiyse `python scripts/build_registry.py` ile `registry.json` ve `legacy-mapping.md` yeniden üretildi
- [ ] Sözleşme değiştiyse `docs/01-architecture/interfaces.md` ve ilgili `spec.md` birlikte güncellendi; sürüm değerlendirildi
- [ ] Ölçülmemiş bir değer kanıt olarak yazılmadı
