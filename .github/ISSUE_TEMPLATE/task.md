---
name: Paket
about: Yürütme planındaki bir paketin veya ürün aşamasının uygulanması
title: "<PAKET> · <paket adı>"
labels: ["paket"]
---

## Paket

- **Kimlik:** (ör. F2-B)
- **Dalga / öncelik:** (ör. W3 · P0)
- **Paket dosyası:** `docs/execution/packages/<dalga>/<ID>-*.md`
- **Doğrudan önkoşullar:** (paket dosyasındaki `Önkoşullar` satırı)

## Başlamadan önce

- [ ] Doğrudan önkoşulların her biri kabul edildi (`evidence/<ÖNKOŞUL>/<run_id>/decision.json` = PASS)
- [ ] Paket dosyasının §2 kutuları sağlandı
- [ ] İlgili açık karar/ADR (varsa) verildi veya güvenli varsayılan yazıldı
- [ ] Ortam: CPU / GPU / PBX / İnsan

## Kanıt

- PoC PR (`paket/<ID>` dalı): …
- Çalıştırılan testler: `pytest …`
- Kanıt klasörü: `evidence/<ID>/<run_id>/`
- Ölçüm raporu (varsa): `data/<aşama>/lab-report-….json`
- Kapı kararları: `<ID>-G00` … (PASS / FAIL / HOLD / NOT_RUN)

## Notlar

Spec ile kod arasındaki çelişkiler, açık kalan noktalar.
