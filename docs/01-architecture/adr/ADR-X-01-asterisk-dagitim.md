# ADR-X-01 — Asterisk dağıtım mimarisi (karar günlüğü: ADR-006)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | F6-A (AudioSocket), F6-D (isteğe bağlı aktarım), G5, PILOT_DECISION — eski görev F6-T20 |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Freya Windows + CUDA üzerinde çalışıyor; Asterisk Linux üzerinde çalışır. Pilot döneminde operasyonel karmaşıklığın azaltılması, üretim ortamında ise hata izolasyonu ve ölçeklenebilirlik hedefleniyor. AudioSocket şifresiz bir TCP protokolüdür.

## Seçenekler

| Seçenek | Açıklama |
| --- | --- |
| A | Her ortamda aynı makine |
| B | Her ortamda ayrı sunucular |
| C | Pilot ve geliştirmede aynı makine, üretimde ayrı sunucular |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı. Ağ gecikmesi ve kararlılık üretim yeterlilik testinde ölçülür.

## Karar

**Seçenek C.**

- **Pilot ve geliştirme:** Asterisk ve Freya aynı makinede çalışır.
- **Üretim:** Asterisk ve Freya ayrı sunucularda çalışır.

Gerekçe: pilotta kurulum ve yönetim maliyetini azaltır; üretimde hata izolasyonu ve bağımsız ölçekleme sağlar.

## Uygulama kuralları

**Aynı makine (pilot/geliştirme):**
- Asterisk aynı Windows makinesinde WSL2 veya Linux sanal makinesinde çalışır.
- AudioSocket yalnız yerel döngü (loopback) veya yalnız-ana-makine (host-only) ağ arabirimine bağlanır; dış ağa açılmaz. Güvenlik duvarı kuralı bu portu dışarıya kapatır.
- AMI/ARI kimlik bilgileri yerel gizli dosyada tutulur; repoya girmez.
- G5 ve pilot bu topolojide yapılır; ölçümler bu topoloji için geçerlidir.

**Ayrı sunucular (üretim):**
- AudioSocket şifresiz olduğu için trafik yalnız özel ağ, VLAN veya şifreli tünel (ör. WireGuard/IPsec) üzerinden taşınır; açık internetten geçmez.
- Alternatif olarak TLS destekleyen WebSocket medya kanalı (F6-D) değerlendirilir; F6-D isteğe bağlıdır ve ayrı yeterlilik ister.
- Üretime geçmeden önce ayrı sunucu topolojisi için **yeniden yeterlilik** gerekir: G5'in uç gecikme (T0–T8), söz kesme (B0–B5), çerçeve kaybı ve yeniden bağlanma ölçümleri bu topolojide tekrarlanır. Pilot ölçümleri üretime aktarılmaz.

## Sonuçlar

- Güncellenen belgeler: F6-D §11, G5 §2, PILOT §11, [constraints](../../00-overview/constraints.md), [F6 spec](../../stages/F6-rendering-transport/spec.md) §13 soru 5.
- **Geri alma koşulu:** pilotta aynı makinede kaynak çekişmesi (Asterisk yükünün GPU/CPU gecikmesine etkisi) kabul edilemez ölçülürse pilot da ayrı makineye taşınır.
