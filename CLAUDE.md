# Kodlama ajanı rehberi — FreyaOtomotivUltra

Bu repo **yalnızca plan** içerir. Kod [`seydivakkas/FreyaTTS_Automotive_PoC`](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC) reposunda yazılır. Bu dosya planı uygulayan kodlama ajanının **tek kural kaynağıdır**; paket dosyaları kural tekrarlamaz, buraya başvurur.

## 1. Çalışma düzeni

İki repoyu yan yana açın:

```text
workspace/
├── FreyaOtomotivUltra/          ← bu repo (plan; uygulama sırasında salt okunur)
└── FreyaTTS_Automotive_PoC/     ← kodun yazıldığı repo
```

**Yol kuralı:** `backend/`, `frontend/`, `tests/`, `scripts/`, `config/`, `data/`, `evidence/`, `contracts/`, `experimental/`, `automotive_voice/`, `asterisk/` ile başlayan yollar **PoC reposundadır**. `docs/` ile başlayan yollar **bu plan reposundadır**. Tek istisna: bu repodaki `scripts/build_registry.py` (plan denetleyicisi).

## 2. Görev seçimi

1. Plan: [`docs/execution/`](docs/execution/README.md). Giriş noktası `docs/execution/README.md`; sıra `docs/execution/execution-order.md`.
2. Yürütme birimi **pakettir** (`docs/execution/packages/<dalga>/<ID>-*.md`) veya **ürün aşamasıdır** (`docs/execution/stages/*.md`). Eski `F2-T15` biçimli görevler ve AIP'ler yürütme birimi değildir; eşlemesi [`legacy-mapping.md`](docs/execution/legacy-mapping.md)'dedir.
3. Kullanıcı açıkça başlatmadıkça hiçbir paket başlatılmaz ("F2-B paketini başlat"). Bir paketin kabulü sonrakini başlatmaz.
4. Başlamadan önce:
   - Paket dosyasını baştan sona okuyun.
   - **§2 Başlamadan önce** kutularını doğrulayın: doğrudan önkoşulların her biri `evidence/<ÖNKOŞUL>/<run_id>/decision.json` içinde `PASS`. Değilse kod yazmadan durun ve nedenini bildirin.
   - Paket bir sözleşmeye dokunuyorsa [`interfaces.md`](docs/01-architecture/interfaces.md) ilgili bölümünü okuyun.
   - Teknik ayrıntı için paketin `Kaynak` satırındaki spec bölümünü okuyun. Paket dosyası ile spec çelişirse paket dosyası geçerlidir; çelişkiyi PR açıklamasına yazın.
5. Bir oturumda **tek paket**. Aynı anda tek ajan.

## 3. Değişmez kurallar

| # | Kural |
| --- | --- |
| 1 | **Mevcut testler her görevden sonra geçer:** `pytest tests/ experimental/tests/ -q -m "not llm and not gpu and not pbx"`. (H01 hermetik test minimumunu kurana kadar bazı test dosyaları torch olmadan toplanamaz — bulgu X8; o zamana kadar torch kurulu ortamda çalıştırın.) Davranış değişikliği gerektiren test güncellemesi gerekçeyle yapılır; test silinmez. |
| 2 | **Yeni hat bayrak arkasındadır** (`f0_pipeline_v2` … `f6_pipeline_v2` ve paketlerin M03 profilleri). Bayrak kapalıyken PoC davranışı değişmez. |
| 3 | **İstisna:** H01 paketindeki düzeltmeler bayraktan bağımsızdır. |
| 4 | **Yeni ağır model yüklenmez.** Whisper, Qwen ve FreyaTTS'in tek örneği kullanılır. RTX 4070 Laptop 8 GB sınırı ([`constraints.md`](docs/00-overview/constraints.md)). Model indirme yok. |
| 5 | **GPU işi ortak yöneticiden geçer** (`backend/runtime_resources/`, M06). Doğrudan `torch.cuda` veya kilitsiz `to_thread` çağrısı eklenmez. |
| 6 | **Sözleşmeler [`interfaces.md`](docs/01-architecture/interfaces.md) ile birebir uyumludur.** Sözleşme değişikliği önce plan reposunda (ayrı PR), sonra kodda. |
| 7 | **FreyaTTS ağırlıkları değiştirilmez.** Leyla kimliği: seed 9; seed hiçbir yolda sessizce değişmez. |
| 8 | **Her DSP / normalizasyon işlemi tek yerde ve tek kez uygulanır** (F4 normalize eder, F5 sentezler, F6 duraklama/fade/EQ uygular; hızın tek sahibi vardır). |
| 9 | **Eski generation'a ait ses, transkript veya yanıt hiçbir yerde kullanılmaz.** |
| 10 | **Kişisel veri:** Ham ses kaydı varsayılan kapalı; LLM bağlamına yalnızca gerekli alanlar girer; kimlik doğrulamasız özel kayıt paylaşılmaz ([`security-and-privacy.md`](docs/cross-cutting/security-and-privacy.md)). |
| 11 | **Lisans başlığı:** PoC dosyalarındaki "ÖZEL LİSANS — TÜM HAKLAR SAKLIDIR" başlığı yeni dosyalara da eklenir. |
| 12 | **İş etkisi yalnız M07 üzerinden:** randevu, kayıt değişikliği, aktarım gibi etkiler onay + idempotency + makbuzla; kısmi ASR sonucu onay değildir; bilinmeyen sonuç kör yeniden denenmez, uzlaştırılır. |
| 13 | **Ağ ve kurulum:** İnternetten paket/model indirme, dış servise veri gönderme, gerçek çağrı başlatma yok; paket açıkça izin vermedikçe. |

## 4. Ölçüm ve kanıt dürüstlüğü

Ayrıntı: [`docs/execution/evidence.md`](docs/execution/evidence.md).

- Ölçülmemiş değer belgeye, kod yorumuna, arayüze veya PR'a **kanıt olarak yazılmaz**. Bilinmeyen alan `null` / "Ölçüm bekleniyor".
- Durumlar: `NOT_RUN`, `PASS`, `FAIL`, `HOLD`, `DEFERRED` (yalnız isteğe bağlı kapsam). "Hazır" bayrağı kabul değildir.
- Gecikmeler p50/p95/p99 + örnek sayısı + hata sayısıyla. Tek çalıştırma p95 diye raporlanmaz; aşama p95'leri toplanarak uçtan uca değer üretilmez.
- Kalibrasyon kümesi ile test kümesi ayrıdır; eşikler yalnız kalibrasyon kümesinde, ölçümden önce dondurulur.
- MOS, ABX, konuşmacı benzerliği eşiği gibi insan veya kalibrasyon gerektiren ölçümler simüle edilerek başarılı gösterilmez.
- Mock/simülasyon verisi her yerde açıkça etiketlenir.
- `acceptance.md` kutuları yalnız laboratuvar raporu `data/<aşama>/lab-report-*.json` yazıldıktan sonra işaretlenir.

## 5. Kanıt nereye

Her paket çalıştırması: `evidence/<PAKET>/<run_id>/` (PoC reposu), `run_id = YYYYMMDD-HHMM-<kısa sha>`. Zorunlu: `manifest.json`, `test-log.txt`, `decision.json` (şablonlar: [`docs/execution/templates/`](docs/execution/templates/)) + paket dosyasının §9'unda listelenen raporlar. PoC reposunda `docs/` altına kanıt yazılmaz.

## 6. Kod düzeni

Paket → dizin → tek yetki: [`ownership.md`](docs/execution/ownership.md). Ayrıntı: [`code-layout.md`](docs/01-architecture/code-layout.md). Mevcut modüller silinmez; yeni paket onları uyumluluk sarmalayıcısıyla kullanır. Taşınmaması gereken kodlar [`from-poc.md`](docs/migration/from-poc.md) §4'te. Paylaşılan bileşim dosyalarına (`session.py`, `models.py`, `audio.py`, `supervisor/`, `db.py`, `dsp.py`) yalnız en küçük değişiklik; PR açıklamasında hangi sahibin alanına dokunulduğu yazılır.

## 7. Test

- Birim testleri GPU, Ollama veya ağ gerektirmez. Modeller için sahte motorlar kullanılır (H01 hermetik test minimumu, M08 test altyapısı).
- GPU gerektiren testler `@pytest.mark.gpu`, canlı Ollama gerektirenler `@pytest.mark.llm`, gerçek Asterisk gerektirenler `@pytest.mark.pbx` ile işaretlenir ve varsayılan çalıştırmada atlanır.
- Test kimlikleri paket dosyasındakiyle aynıdır (`CT01`, `LN44` …); test adında veya docstring'inde kimlik geçer.
- Laboratuvar testleri `tests/<paket dizini>/lab/` altında; sonuç raporları `data/<aşama>/` altında.
- Gerçek model ölçümleri G4'te, insan ve SIP ölçümleri G5'te yapılır; paket kabulü yapısal testlerle olur.

## 8. Git, commit ve PR

- Dal: `paket/<ID>` (ör. `paket/F2-B`); ürün aşamaları için `asama/<ID>`.
- Commit başlığı görev kimliğiyle başlar: `F2-B.07: kanonik varlık eşleme`.
- Bir PR = bir paket. Sözleşme değişikliği plan reposunda ayrı PR'dır.
- PR açıklaması: paket kimliği; tamamlanan görevler; çalıştırılan test komutları ve özet; kapı kararları; kanıt klasörü yolu; açık kalan noktalar; spec çelişkileri.
- `main`'e doğrudan push, force push ve etiket yok.
- Paket kabul edildiğinde plan reposunda paket dosyasının `Durum` satırı güncellenir (ayrı küçük PR).

## 9. Takıldığınızda

- Önkoşul eksik veya bir giriş kutusu sağlanmıyorsa: kod yazmadan durun, nedeni ve eksik kanıtı bildirin.
- Spec ile mevcut kod çelişiyorsa: kodu değiştirmeden önce çelişkiyi PR açıklamasına veya plan reposuna issue olarak yazın.
- Karar ADR gerektiriyorsa ([`adr/README.md`](docs/01-architecture/adr/README.md)): ölçümü yapın, ADR taslağını yazın, kararı kullanıcıya bırakın. ADR "Kabul edildi" olmadan ilgili kapı `HOLD` kalır.
- Kullanıcı kararı bekleyen konular: [master plan §Açık kararlar](docs/execution/master-plan.md#açık-kararlar).

## 10. Plan reposunu değiştirirken

Paket veya aşama dosyası değişirse `python scripts/build_registry.py` çalıştırın (`registry.json` ve `legacy-mapping.md` yeniden üretilir; kimlik, bağımlılık, bölüm ve bağlantı denetimi yapılır). PR'dan önce `python scripts/build_registry.py --check` temiz olmalıdır.
