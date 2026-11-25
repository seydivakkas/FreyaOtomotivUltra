# PILOT_DECISION — Sınırlı pilot kararı

> G5 kabulünden sonra, **kullanıcının açık kararıyla**, aynı uyumlu profil üzerinde, sınırlı kapsamlı bir pilotun açılıp açılmayacağı belirlenir. Pilot herkese açık yayın değildir. Bu bir yürütme paketi değil, karar kontrol listesidir.

| Alan | Değer |
| --- | --- |
| Kimlik | PILOT_DECISION |
| Dalga | Ürün aşaması |
| Öncelik | P0 |
| Önkoşullar | G5 |
| Sonraki | — |
| Bayrak | Canlı varsayılan değişikliği yalnız burada ve yalnız onaylı kapsamda; acil durdurma anahtarı zorunlu |
| Ortam | Onaylı pilot ortamı (rotalar, hatlar, saatler, çağrı sınırı kullanıcı tarafından belirlenir) |
| Eski görevler | — |
| Kaynak | Bundle `04_GOVERNANCE/UNIFIED_EXECUTION_POLICY.md` (PILOT_DECISION satırı); `01_MASTER_PLAN` §11 yayılım |
| Durum | NOT_RUN |

## 1. Amaç

Pilot; G5'te ölçülen profilin gerçek kullanımda sınırlı ve geri alınabilir biçimde denenmesidir. Karar yalnız kullanıcıya aittir; ajan pilotu başlatmaz, yalnız karar dosyasını hazırlar.

## 2. Başlamadan önce

- [ ] G5 gerçek kabul; pilot profili G5'te kabul edilen profille **birebir** aynı (model, sözlük, çözücü, aktarım, bayraklar).
- [ ] Kullanıcının yazılı pilot kararı: kapsam, süre, hatlar, çağrı sınırı, izleme sorumlusu.
- [ ] Yapay zekâ bildirimi ([ADR-X-03](../../01-architecture/adr/ADR-X-03-yapay-zeka-bildirimi.md)) ve kimlik doğrulama ([ADR-F3-01](../../01-architecture/adr/ADR-F3-01-arayan-kimlik-dogrulama.md)) kararları verildi (2026-11-26); G5'te uygulanmış ve doğrulanmış.
- [ ] Pilot topolojisi [ADR-X-01](../../01-architecture/adr/ADR-X-01-asterisk-dagitim.md): Asterisk ve Freya aynı makinede.

## 3. Kapsam

**Yapılacak:** pilot kapsamının yazılması; operasyonel korumaların ve acil durdurmanın doğrulanması; geri dönüş tatbikatı; izleme ve olay müdahale planı; karar kaydı.

**Yapılmayacak:** herkese açık yayın; G5'te ölçülmemiş profil; yeni model veya uyarlayıcı (F5-D adayı ayrı yeniden yeterlilik ister); otomatik genişletme.

## 4. Dosyalar

```
evidence/PILOT_DECISION/<run_id>/   PILOT_SCOPE.md, GUARDRAILS.md, ROLLBACK_DRILL.md, MONITORING.md, decision.json
```

## 5. Tasarım ve sözleşmeler

Yayılım sırası (master plan): eski davranış → gölge (yan etkisiz) → korumalı salt okunur → korumalı işlem → gerçek SIP/insan pilotu. Pilot son basamaktır. Hata durumunda güvenli baza dönülür; işlem sonucu bilinmiyorsa önce uzlaştırma yapılır.

## 6. Görevler

| Kimlik | Görev | Yapılacak iş | Bitti sayılır |
| --- | --- | --- | --- |
| PILOT.01 | Profil eşliği | Pilot profilinin G5 kabul profiliyle birebir aynı olduğunu hash'lerle doğrula | `PROFILE_MATCH.json` |
| PILOT.02 | Kapsam | Rotalar, saatler, çağrı sınırı, kullanıcı grubu, süre ve sonlandırma koşulları | `PILOT_SCOPE.md` |
| PILOT.03 | Korumalar | Acil durdurma, oran sınırları, yetkili işlem sınırları, insan operatöre devir yolu | `GUARDRAILS.md` |
| PILOT.04 | Geri dönüş tatbikatı | Baz profile dönüş ve bilinmeyen işlem uzlaştırması yalıtılmış ortamda denenir | `ROLLBACK_DRILL.md` |
| PILOT.05 | İzleme ve olay müdahalesi | İzlenecek metrikler, eşikler, sorumlu ve müdahale adımları | `MONITORING.md` |
| PILOT.06 | Karar kaydı | Kullanıcı kararı ve bağımsız gözden geçiren notu | `decision.json` |

## 7. Testler

Yeni test kimliği yok. PILOT.04 geri dönüş tatbikatı ve PILOT.03 acil durdurma denemesi gerçek kanıtla kaydedilir.

## 8. Kabul kapıları

| Kimlik | Kapı | Geçme koşulu |
| --- | --- | --- |
| PILOT-K01 | G5 eşliği | Güncel G5 kabulü ve birebir aynı uyumlu profil |
| PILOT-K02 | Kullanıcı kararı | Açık, yazılı, kapsamlı pilot kararı |
| PILOT-K03 | Korumalar | Acil durdurma ve korumalar denenmiş ve çalışıyor |
| PILOT-K04 | Geri dönüş | Geri dönüş tatbikatı başarılı; veri kaybı yok |
| PILOT-K05 | İzleme | İzleme ve olay müdahale planı sorumlusuyla hazır |

## 9. Kanıt

`evidence/PILOT_DECISION/<run_id>/`: görev tablosundaki dosyalar + `manifest.json`.

## 10. Geri dönüş

Acil durdurma anahtarı pilotu hemen kapatır; baz profile dönülür; bilinmeyen işlemler uzlaştırılır.

## 11. Devir

Pilot sonucu ayrı bir değerlendirmedir; genişletme veya genel yayın yeni bir kullanıcı kararı ister. Üretim, [ADR-X-01](../../01-architecture/adr/ADR-X-01-asterisk-dagitim.md) gereği Asterisk ve Freya'yı **ayrı sunuculara** taşır; bu topoloji için G5 uç gecikme, söz kesme ve yeniden bağlanma ölçümleri yeniden yapılır (pilot ölçümleri üretime aktarılmaz).

## 12. Başlatma komutu

```
PILOT_DECISION kontrol listesini hazırla: docs/execution/stages/PILOT-karari.md.
G5 kabulünü ve profil eşliğini doğrula; kapsam, korumalar, geri dönüş tatbikatı ve izleme belgelerini hazırla.
Pilotu başlatma; kararı kullanıcıya bırak; asama/PILOT_DECISION dalında PR aç ve dur.
```
