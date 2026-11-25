# Buradan başlayın — Freya 2.0 yürütme planı

> Kodlama ajanı için giriş noktası. Kod [`seydivakkas/FreyaTTS_Automotive_PoC`](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC) reposunda yazılır; bu klasör **ne yapılacağını, hangi sırayla ve ne zaman bitmiş sayılacağını** tanımlar. Çalışma kuralları: [CLAUDE.md](../../CLAUDE.md).

## Ajan nasıl çalışır?

1. Kullanıcı bir paketi başlatır: **"F2-B paketini başlat"**.
2. Ajan [CLAUDE.md](../../CLAUDE.md)'yi ve paket dosyasını (`packages/<dalga>/<ID>-*.md`) baştan sona okur.
3. Paket dosyasının **§2 Başlamadan önce** kutularını doğrular. Biri sağlanmıyorsa kod yazmadan durur ve nedenini bildirir.
4. **§6 Görevler**'i sırayla yapar; her görevin "Bitti sayılır" sütunundaki testleri yazar ve çalıştırır.
5. **§7 Testler**'in tümünü çalıştırır, **§8 Kabul kapıları**'nı değerlendirir, **§9 Kanıt**'ı `evidence/<ID>/<run_id>/` altına yazar.
6. `paket/<ID>` dalında PR açar ve **durur**. Sonraki paketi kendiliğinden başlatmaz.

Her paket dosyasının sonundaki **§12 Başlatma komutu** ajana doğrudan verilebilecek kısa talimattır.

## İlk kurulum (bir kez)

1. Bu plan reposundaki PR birleştirilmiş olmalı; ajanlar `main` dalını okur.
2. PoC reposunun köküne [`templates/poc-CLAUDE.md`](templates/poc-CLAUDE.md) içeriğini **`CLAUDE.md`** ve **`AGENTS.md`** adıyla ekleyin (PoC'ta zaten `CLAUDE.md` varsa en üste ekleyin). Böylece PoC reposunda açılan her ajan önce bu planı okur.
3. Ajan oturumuna **iki repoyu birlikte** ekleyin: `seydivakkas/FreyaTTS_Automotive_PoC` (yazma) ve `seydivakkas/FreyaOtomotivUltra` (okuma).
4. GPU, Ollama veya Asterisk gerektiren adımlar yerel makinede yapılır ([execution-order.md §Ortam gereksinimi](execution-order.md#ortam-gereksinimi)); bulut ajanı yalnız CPU işlerini yapabilir.

## Ajana verilecek istem

İlk paket her zaman M00'dır (salt okunur envanter; kod değişmez). Kopyalanabilir istem:

```
FreyaTTS_Automotive_PoC reposunda çalışıyorsun; plan FreyaOtomotivUltra reposunda.
Önce FreyaOtomotivUltra/CLAUDE.md ve FreyaOtomotivUltra/docs/execution/README.md dosyalarını oku.
Sonra <PAKET> paketini başlat: paket dosyasındaki "12. Başlatma komutu" bölümünü uygula.
Başlamadan önce §2'deki kutuları doğrula; biri sağlanmıyorsa kod yazmadan dur ve nedenini yaz.
Bitince paket/<PAKET> dalında PR aç, kanıtı evidence/<PAKET>/<run_id>/ altına yaz ve dur.
```

Sıradaki paket [execution-order.md](execution-order.md)'deki seri sıradır; bir paketin PR'ı birleştirilip kanıtı `PASS` olmadan sonraki başlatılmaz.

## Paket dosyasının bölümleri (hepsinde aynı)

| Bölüm | İçerik |
| --- | --- |
| Başlık tablosu | Kimlik, dalga, öncelik, önkoşullar, sonraki, bayrak, ortam, eski görevler, kaynak, durum |
| 1. Amaç | Neden bu paket var |
| 2. Başlamadan önce | Giriş kontrolleri (kutu listesi) |
| 3. Kapsam | Yapılacak / yapılmayacak |
| 4. Dosyalar | PoC reposunda oluşturulacak/değiştirilecek dizinler |
| 5. Tasarım ve sözleşmeler | Davranış kuralları, sayısal fikstürler, sözleşmeler |
| 6. Görevler | `Kimlik · Görev · Yapılacak iş · Bitti sayılır` |
| 7. Testler | `Kimlik · Test · Beklenen` |
| 8. Kabul kapıları | `Kimlik · Kapı · Geçme koşulu` |
| 9. Kanıt | `evidence/<ID>/<run_id>/` içeriği |
| 10. Geri dönüş | Bayrak ve kod geri alma |
| 11. Devir | Sonraki paketlere bırakılanlar |
| 12. Başlatma komutu | Ajana verilecek talimat |

## Klasör

| Dosya | Ne için |
| --- | --- |
| [master-plan.md](master-plan.md) | Hedef, dalgalar, aşamalar, hedef metrikler, yönetişim, verilen ve açık kararlar |
| [execution-order.md](execution-order.md) | Seri sıra, bağımlılık grafiği, ortam gereksinimi |
| [packages/](packages/) | 34 paket dosyası (W0–W5): 32 iş paketi + 2 kapı paketi (CORE_GATE, W2_GATE) |
| [stages/](stages/) | Ürün aşamaları G2, G3, G4, G5, PILOT |
| [decisions.md](decisions.md) | Bundle'a göre yapılan değişikliklerin gerekçeleri ve kullanıcı kararları (K-01…K-11) |
| [ownership.md](ownership.md) | Paket → dizin → tek yetki; sözleşme sınırları |
| [risks.md](risks.md) | Entegrasyon (IR01–IR48), aşamalar arası (CS01–CS18) ve program riskleri |
| [evidence.md](evidence.md) | Kanıt yolları, zorunlu dosyalar, kanıt sınıfları, ölçüm dürüstlüğü |
| [templates/](templates/) | `manifest`, `decision`, `lab-report`, `contract-change`, `research-eligibility` şablonları; PoC reposu için ajan rehberi şablonu `poc-CLAUDE.md` |
| [registry.json](registry.json) | Tüm görev/test/kapı kimlikleri (üretilmiş) |
| [legacy-mapping.md](legacy-mapping.md) | Eski görev (`F2-T15`) ve AIP → yeni paket eşlemesi (üretilmiş) |

`registry.json` ve `legacy-mapping.md` elle düzenlenmez; paket dosyası değişince `python scripts/build_registry.py` çalıştırılır. `--check` seçeneği kimlik benzersizliğini, bağımlılık tutarlılığını ve bağlantıları denetler.

## Teknik kaynaklar

Paket dosyaları "ne ve ne zaman"ı verir; "nasıl çalışır" ayrıntısı şuralardadır: aşama spec'leri [docs/stages/](../stages/), ortak katman [docs/cross-cutting/](../cross-cutting/), sözleşmeler [interfaces.md](../01-architecture/interfaces.md), kod düzeni [code-layout.md](../01-architecture/code-layout.md), kısıtlar [constraints.md](../00-overview/constraints.md), ölçüm planı [docs/testing/](../testing/). Paket dosyası ile spec çelişirse paket dosyası geçerlidir; çelişki PR açıklamasına yazılır.
