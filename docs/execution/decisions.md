# Kararlar

> Bu planın, kaynak alınan "Freya 2.0 Final Unified Execution Bundle" (25.11.2026) üzerinde yaptığı değişikliklerin gerekçeleri. Bundle bu repoda saklanmaz; tüm içeriği Türkçe paket dosyalarına aktarılmıştır. Açık (kullanıcı kararı bekleyen) konular [master-plan.md §Açık kararlar](master-plan.md#açık-kararlar)'dadır.

## Kullanıcı tercihleri (25.11.2026)

1. **Paket planı tek plandır.** F0–F6 spec'leri teknik kaynak olarak kalır; eski AIP/Faz planı eşleme tablosuyla emekliye ayrılır.
2. **Sadeleştir.** Paket başına tek dosya, sabit bölümler; kurallar tek yerde ([CLAUDE.md](../../CLAUDE.md)); görev/test/kapı kimlikleri korunur, tekrarlar birleşir.
3. **Tamamen Türkçe.** Kod, dosya ve dizin adları İngilizce kalır.
4. **Dal + PR.** Plan değişiklikleri ayrı dalda ve PR ile; `main`'e doğrudan push yok.

## K-01 — Yeni paket H01 (güvenli zemin)

**Sorun:** Bundle'da ilk kod değişikliği M01'de başlar; bugün canlıyı etkileyen bazı hatalar (kimliği doğrulanmamış arayana özel kayıt okunması, ikinci araç randevusunun başarısız olması, oturumlar arası VAD durumu, çift normalizasyon, ölçülmemiş değer gösteren UI, torch olmadan toplanamayan testler) ancak çok sonraki paketlerde ele alınır.

**Karar:** M00 ile M01 arasına W0 paketi [H01](packages/W0/H01-guvenli-zemin.md) eklendi. Eski planın "Faz 0 — Bayraktan bağımsız düzeltmeler" görevleri, hermetik test minimumu ve ölçülmemiş iddiaların temizlenmesi burada. Bu düzeltmeler bayraktan bağımsızdır. M01'in önkoşulu `M00, H01` oldu. Kimlikler: görev `H01.01…`, test `HF01…`, kapı `H01-G00…`.

## K-02 — Yönetişimin sadeleştirilmesi

**Sorun:** Bundle; yetki belgeleri (grant), dosya kiralama, SHA-256 doğrulaması, çoklu ajan koordinasyonu ve ayrıntılı soy kayıtları ister. Tek kişilik projede bu, ajanın asıl işten önce yönetişim belgesi üretmesine yol açıyor.

**Karar:**
- Yetki belgesi yerine kullanıcının açık komutu: "X paketini başlat".
- Dosya kiralama yerine aynı anda tek ajan.
- Bundle hash doğrulaması kaldırıldı (bundle repoda yok); soy, git commit'i ve kabul edilmiş çalıştırma kimliğiyle izlenir.
- Bağımsız inceleme yalnız CORE_GATE, W2_GATE, G2–G5 ve PILOT için zorunlu.
- Git: dal `paket/<ID>` veya `asama/<ID>`; commit başlığı `<GÖREV-ID>: …`; paket başına PR; `main`'e push, force push ve etiket yok.

Korunan ilkeler: kabul gerçek kanıtla verilir; uygunluk ("hazır") kabul değildir; bir paketin kabulü sonrakini başlatmaz.

## K-03 — Kimlik kuralları

- Görev kimlikleri bundle'daki gibi: `M01.05`, `F4-A.12`, `UI.07`, `G4.13`, `G5.20`.
- Test kimlikleri bundle'daki gibi ve tüm planda benzersiz: `CT01`, `LN44`, `SA061`, `RH100` …
- Paket kapıları paket önekli: bundle'daki yerel `G03` → `M01-G03`. Böylece küresel aşamalarla (G0–G5) karışmaz.
- Kapı paketleri ve aşamalar kendi benzersiz öneklerini korur: CORE_GATE `CG00–CG11`, W2_GATE `WG00–WG11`, G3 `UG00–UG19`, G4 `SG00–SG19`, G5 `RG00–RG19`.
- Bu planın eklediği kimlikler: H01 (`H01.xx`, `HF01–HF17`, `H01-G00–G05`), G2 (`G2.01–G2.08`, `G2-K01–K08`), PILOT (`PILOT.01–06`, `PILOT-K01–K05`).

## K-04 — Kanıt yolları

Bundle kanıtı PoC reposunda `docs/freya2/...` ve `evidence/<küçük harf>/...` altına yazdırıyordu. PoC reposunda `docs/` kullanılmaz (CLAUDE.md yol kuralı: `docs/` plan reposundadır). Yeni kural: `evidence/<PAKET>/<run_id>/` (`manifest.json`, `test-log.txt`, `decision.json` + paketin listelediği raporlar); laboratuvar ölçümleri `data/<aşama>/lab-report-*.json`. Ayrıntı: [evidence.md](evidence.md).

## K-05 — Tek sözleşme kaynağı

Bundle'daki M01 sözleşme adları ile plan reposundaki [interfaces.md](../01-architecture/interfaces.md) adları farklıydı. Karar: `interfaces.md` tek kaynaktır; §7'ye paket planı ad eşlemesi eklendi (ör. bundle `ResponsePlan` = `DialogueResponse.segments`; yeni `ToolReceipt` sözleşmesi C15). Sözleşme değişikliği önce plan reposunda, ayrı PR ile.

## K-06 — Yapay zekâ bildirimi

**Kabul edildi (2026-11-26):** [ADR-X-03](../01-architecture/adr/ADR-X-03-yapay-zeka-bildirimi.md). Her görüşmenin başında bildirim yapılır ("Merhaba, Freya yapay zekâ destekli müşteri temsilcisine ulaştınız."). H01.14 koşulsuz uygulanır; G5 ve PILOT bildirimin uygulanmış ve test edilmiş olmasını (HF16) ister.

## K-07 — G2 ve PILOT kontrol listeleri

Bundle G2 ve PILOT_DECISION için yalnız kısa koşul cümleleri içerir (görev/test/kapı tablosu yok). Ajanın uygulayabilmesi için bu plan [G2](stages/G2-entegrasyon.md) ve [PILOT](stages/PILOT-karari.md) dosyalarında görev ve kapı kontrol listeleri tanımladı. Yeni test kimliği tanımlanmadı; G2 mevcut tüm testleri yeniden çalıştırır.

## K-08 — Bayrak varsayılanları

Eski kural "bayrak varsayılanı aşamanın regresyon sprintinden sonra değişir" idi. Yeni kural: paket kabulleri ve G2–G5 yeni yolu bayrak/profil arkasında doğrular; **canlı varsayılan yalnız PILOT_DECISION kapsamında** değişir. G4 aday profilleri yalnız laboratuvar yapılandırmasıyla seçer.

## K-09 — Sayım dürüstlüğü

Paket dosyalarındaki satırlar **plan** sayısıdır; çalıştırılmış test sayısı değildir. Aynı test farklı kapılarda yeniden çalıştırılırsa tek kimlik, ayrı çalıştırma satırı olur. İsteğe bağlı/ertelenmiş vakalar PASS sayılmaz. Güncel sayılar `python scripts/build_registry.py` çıktısındadır.

## K-10 — Bundle'dan bilinçli olarak alınmayanlar

- Bundle'ın orkestratör istemi, birleşik yürütme politikası ve kayıt JSON'ları ayrı belge olarak taşınmadı; içerikleri master plan, yürütme sırası, kararlar, sahiplik ve riskler belgelerine dağıtıldı.
- Bundle'daki tarihsel arşivler (`90_ORIGINAL_ARCHIVES`) ve SHA-256 listeleri taşınmadı.
- Bundle'daki İngilizce "ajan rolü" girişleri ("You are the senior …") yerine her paketin sonunda kısa Türkçe başlatma komutu var.

## K-11 — Kullanıcı kararları (2026-11-26)

Ana plandaki açık kararların yedisi kullanıcı tarafından karara bağlandı ve ADR olarak kaydedildi ([master-plan §Verilen kararlar](master-plan.md#verilen-kararlar)). Kullanıcının karar günlüğündeki numaralar (ADR-001…007) mevcut ADR kimlikleriyle eşlendi; her ADR dosyasının başlığında iki numara da var. Kararları uygulanabilir kılmak için eklenen kurallar ADR'lerin "Uygulama kuralları" bölümündedir ve kararı değiştirmez. Aynı gün iki karar revize edildi: telefon okuması ikişerli gruplardan `05xx xxx xx xx` gruplamasına (11 hane ikişerli eşit bölünemediği için), gömme modeli e5-large + bge-m3 alternatifinden yalnız `bge-m3`'e.

Bu kararlar CLAUDE.md kural 4'e bir istisna getirir: ADR-F3-02 gömme modeli GPU'ya yüklenmeyen, CPU'da çalışan, yerel olarak sağlanan tek onaylı ek modeldir.

