# Kanıt kuralları

> Bir paket veya aşama yalnız **gerçekten çalıştırılmış** testlerin ve ölçümlerin kanıtıyla kabul edilir. Bu sayfa kanıtın nereye, hangi biçimde yazılacağını tanımlar. Şablonlar: [templates/](templates/).

## Nereye

| Ne | Yol (PoC reposu) |
| --- | --- |
| Paket/aşama çalıştırma kanıtı | `evidence/<PAKET>/<run_id>/` — örn. `evidence/F2-B/20261201-1430-a1b2c3d/` |
| Laboratuvar ölçüm raporu | `data/<aşama>/lab-report-<YYYYMMDD>-<konu>.json` — örn. `data/F5/lab-report-20261205-ttfa.json` |
| Kısıtlı veri (G5 ham ses, kimlik eşlemesi) | Git dışında, kısıtlı yerel depo; kanıtta yalnız opak başvuru |

`run_id` biçimi: `YYYYMMDD-HHMM-<kısa commit sha>`. PoC reposunda `docs/` dizini kullanılmaz (plan belgeleri bu repodadır).

## Her çalıştırmada zorunlu üç dosya

1. **`manifest.json`** ([şablon](templates/manifest.template.json)) — paket, görevler, commit, değişen dosyalar, ortam (CPU/GPU, Python, sürücü), bayrak/profil değerleri, çalıştırılan komutlar, kanıt sınıfı.
2. **`test-log.txt`** — çalıştırılan test komutlarının ham çıktısı (pytest özeti dahil). Kısaltılmaz; çok büyükse sıkıştırılmış ek + özet.
3. **`decision.json`** ([şablon](templates/decision.template.json)) — her kapı için `PASS / FAIL / HOLD / NOT_RUN / DEFERRED`, gerekçe ve dayandığı test kimlikleri; paket kararı; gözden geçiren.

Paket dosyasının §9 bölümü ek raporları listeler (envanter, şartname, benchmark protokolü vb.).

## Kanıt sınıfları

Her ölçüm veya sonuç bir sınıf taşır; sınıf terfi ettirilemez.

| Sınıf | Anlamı |
| --- | --- |
| `STATIC_CODE` | Kod/yapılandırma incelemesi; çalıştırma yok |
| `HISTORICAL_RECORD` | Önceki bir çalıştırmanın kaydı (ör. 6 Kasım 2026 doğrulama raporu) |
| `SYNTHETIC_FIXTURE` | Belirlenimci fikstür, sahte saat/motor |
| `MOCK_RUNTIME` | Gerçek orkestrasyon, sahte model/sağlayıcı |
| `LOCAL_RUNTIME_MEASURED` | Gerçek yerel model/DSP/kodek ile ölçüm (sentetik girdi veya insan girişi; köken ayrıca yazılır) |
| `REAL_ENDPOINT_MEASURED` | Gerçek uçta bağımsız ölçüm (yalnız G5) |

## Ölçüm dürüstlüğü

- Ölçülmemiş değer `null`'dır; sıfır veya tahmin yazılmaz. Neden alanı doldurulur.
- Gecikmeler p50/p95/p99 + `n` + hata/zaman aşımı sayısıyla. Tek çalıştırma p95 diye raporlanmaz. Aşama p95'leri toplanarak uçtan uca değer üretilmez.
- Ilık/soğuk, önbellek isabet/ıska, yük koşulu ayrı.
- Başarısız, eksik ve çekimser öğeler paydada kalır.
- Kalibrasyon kümesi ile test kümesi ayrı; eşikler yalnız kalibrasyon kümesinde ve ölçümden önce dondurulur.
- MOS, ABX ve konuşmacı benzerliği eşiği gibi insan veya kalibrasyon gerektiren ölçümler simüle edilerek başarılı gösterilmez.
- Mock veya simülasyon verisi her yerde (rapor, UI, PR açıklaması) açıkça etiketlenir.
- Kişisel veri, gizli bilgi, ham müşteri sesi veya düşük entropili kişisel hash kanıta girmez.

## `acceptance.md` kutuları

Aşama klasörlerindeki ([docs/stages/](../stages/)) `acceptance.md` kutuları yalnız ilgili laboratuvar raporu `data/<aşama>/` altına yazıldıktan sonra, rapora bağlantıyla işaretlenir.

## Plan reposunda durum güncellemesi

Paket kabul edilince plan reposunda paket dosyasının `Durum` satırı `PASS` yapılır ve `decision.json` yolu eklenir. Bu ayrı ve küçük bir PR'dır.
