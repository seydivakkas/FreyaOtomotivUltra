# Eski Master Development Plan (AIP-01…48) — emekliye ayrıldı

> **Bu belge artık yürütme planı değildir.** 25.11.2026'dan itibaren tek yürütme planı [docs/execution/](../execution/README.md) altındaki paket planıdır (karar: [decisions.md](../execution/decisions.md)). Kodlama ajanı bu belgeden iş almaz.

## Nereye taşındı

| Eski bölüm | Yeni yeri |
| --- | --- |
| §1 Öncelik mantığı, §2 Fazlar ve kilometre taşları | [Ana plan](../execution/master-plan.md) (dalgalar W0–W5 ve aşamalar G2–G5) |
| §3 Faz 0 — Bayraktan bağımsız düzeltmeler | [H01 paketi](../execution/packages/W0/H01-guvenli-zemin.md) |
| §4 Uygulama paketleri AIP-01…AIP-48 | [legacy-mapping.md](../execution/legacy-mapping.md) (AIP → paket ve eski görev → paket eşlemesi); veri: `scripts/data/legacy_aip.json` |
| §5 Kritik yol ve paralellik | [execution-order.md](../execution/execution-order.md) |
| §6 Tekilleştirilmiş bileşenler | [ownership.md §Tekilleştirilmiş bileşenler](../execution/ownership.md#tekilleştirilmiş-bileşenler) |
| §7 Aşamalar arası bağımlılıklar | Paket dosyalarının `Önkoşullar` satırları ve [ownership.md §Sözleşme sınırları](../execution/ownership.md#sözleşme-sınırları-üretici-ve-tüketici-gerçek-kaynakla-test-edilir) |
| §8 Kullanıcı kararı bekleyen sorular | [Ana plan §Açık kararlar](../execution/master-plan.md#açık-kararlar) |
| §9 Program riskleri | [risks.md §Program riskleri](../execution/risks.md#program-riskleri) |
| §10 İlerleme takibi | [evidence.md](../execution/evidence.md) ve [CLAUDE.md](../../CLAUDE.md) §8 |

Belgenin önceki içeriği git geçmişinde durur.
