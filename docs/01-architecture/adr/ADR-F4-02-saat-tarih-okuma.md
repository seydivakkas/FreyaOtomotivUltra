# ADR-F4-02 — Saat ve tarih okuma standardı (karar günlüğü: ADR-003)

| Alan | Değer |
| --- | --- |
| Durum | Kabul edildi |
| Sahibi olan paket | F4-A (okuma), F4-B (ek uyumu), F2-B (geri ayrıştırma), F3-A (netleştirme) — eski görev F4-T11 |
| Tarih | 2026-11-26 |
| Karar veren | Kullanıcı (ürün sahibi) |

## Bağlam

Saatlerin sayısal biçimde okunması ("on dört otuz") doğal konuşma akışını bozabiliyor. [F4 spec](../../stages/F4-linguistic-frontend/spec.md) §12 soru 2.

## Seçenekler

| Seçenek | Örnek (14:30) |
| --- | --- |
| A | "on dört otuz" (sayısal) |
| B | "öğleden sonra iki buçuk" (doğal) |

## Ölçüm

Ölçüm gerektirmeyen kullanıcı kararı. Anlaşılırlık G5 dinleme çalışmasında doğrulanır.

## Karar

**Seçenek B.** Saatler doğal Türkçe konuşma biçiminde okunur:

| Yazı | Okunuş |
| --- | --- |
| 09:30 | sabah dokuz buçuk |
| 14:00 | öğleden sonra iki |
| 18:30 | akşam altı buçuk |

Gerekçe: daha doğal etkileşim; yanlış anlama oranını azaltır.

## Uygulama kuralları (F4-A)

Kararın örneklerinden genellenen kurallardır; sınır durumları ürün sahibi incelemesine açıktır ve F4-A fikstürlerinde sabitlenir.

**Gün dilimi** (12 saatlik okuma; gün dilimi her zaman söylenir, böylece 24 saatlik değer korunur):

| Saat aralığı | Dilim | Örnek |
| --- | --- | --- |
| 05:00–11:59 | sabah | 08:00 → sabah sekiz |
| 12:00–12:59 | öğlen | 12:30 → öğlen on iki buçuk |
| 13:00–17:59 | öğleden sonra | 17:00 → öğleden sonra beş |
| 18:00–21:59 | akşam | 20:15 → akşam sekizi çeyrek geçe |
| 22:00–04:59 | gece | 23:00 → gece on bir; 00:00 → gece yarısı |

**Dakika:**

| Dakika | Biçim | Örnek |
| --- | --- | --- |
| :00 | `<dilim> <saat>` | 14:00 → öğleden sonra iki |
| :30 | `<dilim> <saat> buçuk` | 09:30 → sabah dokuz buçuk |
| :15 | `<dilim> <saat (belirtme hâli)> çeyrek geçe` | 09:15 → sabah dokuzu çeyrek geçe |
| :45 | `<dilim> <sonraki saat (yönelme hâli)> çeyrek var` | 09:45 → sabah ona çeyrek var |
| :01–:29 | `<saat (belirtme)> <dakika> geçe` | 09:05 → sabah dokuzu beş geçe |
| :31–:59 | `<sonraki saat (yönelme)> <60−dakika> var` | 09:40 → sabah ona yirmi var |

- Gün dilimi gerçek saate göre seçilir (11:45 → "sabah on ikiye çeyrek var").
- **Zaman bildiren ek** (`'de/'da`, "saat X'te randevu"): "buçuk" → "buçukta", "<saat>" → "<saat>-DA" ("sabah dokuzda"), "var" → "kala" ("sabah ona yirmi kala"), "geçe" değişmez. Ekler F4-B ünlü uyumu, kaynaştırma ve ünsüz yumuşaması kurallarıyla üretilir (dokuzu, ikiyi, altıya, ona, dördü, dörde, dörtte).
- Saatten hemen önceki "saat" sözcüğü gün dilimiyle birleşir: "yarın saat 14:30'da" → "yarın öğleden sonra iki buçukta".
- Saat korunmuş atomdur: tek parça, bölünmez; anlamsal değer (14:30) planda tipli olarak taşınır.
- **Tarih:** mevcut F4 tarih kuralları sürer (05.06.2027 → "beş haziran iki bin yirmi yedi"); tarih ile saat birlikte geçtiğinde sıra "tarih + gün dilimi + saat"tir.

## Sonuçlar

- **F2-B** doğal biçimleri geri ayrıştırır ("öğleden sonra iki buçuk" → 14:30, "sabah ona çeyrek var" → 09:45).
- **F3-A:** arayan gün dilimi söylemeden saat verirse ("iki buçuk") ve çalışma saatleri tek anlam bırakmıyorsa netleştirme sorusu sorulur; tahmin edilmez.
- Güncellenen belgeler: F4-A §5 ve sayı/saat tablosu, [F4 spec](../../stages/F4-linguistic-frontend/spec.md) okuma tabloları ve §12, [F4 acceptance](../../stages/F4-linguistic-frontend/acceptance.md) T saat testi, H01 HF10.
- **Geri alma koşulu:** G5'te doğal saat okumasında yanlış anlama sayısal okumadan fazla çıkarsa karar yeniden açılır.
