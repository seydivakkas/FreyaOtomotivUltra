# Kodlama ajanı rehberi — FreyaOtomotivUltra

Bu repo **yalnızca plan** içerir. Kod [`seydivakkas/FreyaTTS_Automotive_PoC`](https://github.com/seydivakkas/FreyaTTS_Automotive_PoC) reposunda yazılır. Bu dosya, planı uygulayacak kodlama ajanının (Claude Code veya başka bir ajan) çalışma kurallarıdır.

## 1. Çalışma düzeni

İki repoyu yan yana açın:

```text
workspace/
├── FreyaOtomotivUltra/          ← bu repo (plan, salt okunur kabul edin)
└── FreyaTTS_Automotive_PoC/     ← kodun yazıldığı repo
```

**Yol kuralı:** Belgelerde `backend/`, `frontend/`, `tests/`, `scripts/`, `config/`, `data/`, `contracts/`, `experimental/`, `automotive_voice/`, `asterisk/` ile başlayan her yol **PoC reposundadır**. `docs/` ile başlayan yollar **bu plan reposundadır**. Bir görev "`docs/...` dosyasına yaz" diyorsa çıktı plan reposuna gider (ayrı commit).

## 2. Görev seçimi

1. Sırayı [`docs/roadmap/master-plan.md`](docs/roadmap/master-plan.md) belirler. Aşama içi sıralama ilgili `tasks.md` dosyasındadır.
2. Bir görevi almadan önce:
   - Görevin `tasks.md` kaydını okuyun (dosyalar, bağımlılıklar, "bitti" tanımı).
   - İlgili `spec.md` bölümünü okuyun.
   - Bağımlı görevlerin bitmiş olduğunu doğrulayın. Bitmemişse başlamayın.
   - Görev başka bir aşamanın sözleşmesine dokunuyorsa [`docs/01-architecture/interfaces.md`](docs/01-architecture/interfaces.md) dosyasını okuyun.
3. Bir oturumda **tek görev** veya master planda tanımlı tek **uygulama paketi** (AIP) yapın.

## 3. Değişmez kurallar

| # | Kural |
| --- | --- |
| 1 | **Mevcut testler her görevden sonra geçer.** `pytest tests/ experimental/tests/ -q -m "not llm and not gpu and not pbx"`. (AIP-01 tamamlanana kadar 43 test dosyası torch kurulu olmadan toplanamaz — bulgu X8; o zamana kadar torch kurulu ortamda çalıştırın.) Davranış değişikliği gerektiren test güncellemesi gerekçeyle yapılır; test silinmez. |
| 2 | **Yeni hat bayrak arkasındadır** (`f0_pipeline_v2` … `f6_pipeline_v2`). Bayrak kapalıyken PoC davranışı değişmez. |
| 3 | **İstisna:** Master planın "Faz 0 — Bayraktan bağımsız düzeltmeler" listesindeki hatalar bayraktan bağımsız düzeltilir. |
| 4 | **Yeni ağır model yüklenmez.** Whisper, Qwen ve FreyaTTS'in tek örneği kullanılır. RTX 4070 Laptop 8 GB sınırı ([`docs/00-overview/constraints.md`](docs/00-overview/constraints.md)). |
| 5 | **GPU işi ortak yöneticiden geçer** (`backend/runtime_resources/`). Doğrudan `torch.cuda` veya kilitsiz `to_thread` çağrısı eklenmez. |
| 6 | **Sözleşmeler `docs/01-architecture/interfaces.md` ile birebir uyumludur.** Sözleşme değişikliği önce plan reposunda yapılır (ayrı PR), sonra kodda. |
| 7 | **FreyaTTS ağırlıkları değiştirilmez.** Leyla kimliği: seed 9; seed hiçbir yolda sessizce değişmez. |
| 8 | **Her DSP / normalizasyon işlemi tek yerde ve tek kez uygulanır** (F4 normalize eder, F5 sentezler, F6 duraklama/fade/EQ uygular). |
| 9 | **Eski generation'a ait ses, transkript veya yanıt hiçbir yerde kullanılmaz.** |
| 10 | **Kişisel veri:** Ham ses kaydı varsayılan kapalı; LLM bağlamına yalnızca gerekli alanlar girer; kimlik doğrulamasız özel kayıt paylaşılmaz ([`docs/cross-cutting/security-and-privacy.md`](docs/cross-cutting/security-and-privacy.md)). |
| 11 | **Lisans başlığı:** PoC dosyalarındaki "ÖZEL LİSANS — TÜM HAKLAR SAKLIDIR" başlığı yeni dosyalara da eklenir. |

## 4. Ölçüm dürüstlüğü

- Ölçülmemiş bir değer belgeye, koda yorumuna veya arayüze **kanıt olarak yazılmaz**. Bilinmeyen alan `null` / "Ölçüm bekleniyor" olur.
- `acceptance.md` kutuları yalnızca test çalıştırılıp sonucu `data/<aşama>/lab-report-*.json` dosyasına yazıldıktan sonra işaretlenir.
- MOS, ABX, speaker similarity eşiği gibi insan veya kalibrasyon gerektiren ölçümler **simüle edilerek başarılı gösterilmez**.
- Kalibrasyon kümesi ile test kümesi ayrıdır; eşikler yalnızca kalibrasyon kümesinde ayarlanır.
- Tek çalıştırma sonucu p95 diye raporlanmaz. Gecikmeler p50/p95/p99 ve örnek sayısıyla verilir.
- Studio sayfalarında simülasyon veya mock veri açıkça etiketlenir.

## 5. Kod düzeni

Hedef paketler [`docs/01-architecture/code-layout.md`](docs/01-architecture/code-layout.md) dosyasındadır. Özet:

| Aşama | Paket |
| --- | --- |
| F0 | `backend/audio_frontend/` |
| F1 | `backend/voice_activity/` |
| F2 | `backend/speech_recognition/` |
| F3 | `backend/supervisor/` (mevcut paket genişletilir) |
| F4 | `backend/linguistic_frontend/` + `backend/morphology/` |
| F5 | `backend/neural_synthesis/` |
| F6 | `backend/audio_rendering/` + `backend/media_transport/` |
| Ortak | `backend/runtime_resources/`, `backend/observability/`, `backend/session_state/`, `backend/dsp_common/` |

Mevcut modüller silinmez; yeni paket onları uyumluluk sarmalayıcısıyla kullanır. Taşınmaması gereken kodlar [`docs/migration/from-poc.md`](docs/migration/from-poc.md) §4'te listelidir.

## 6. Test

- Birim testleri GPU, Ollama veya ağ gerektirmez. Modeller için sahte motorlar kullanılır (F3-T01 LLM fake, F5-T07 sahte çıkarım motoru).
- GPU gerektiren testler `@pytest.mark.gpu`, canlı Ollama gerektirenler `@pytest.mark.llm`, gerçek Asterisk gerektirenler `@pytest.mark.pbx` ile işaretlenir ve varsayılan çalıştırmada atlanır.
- Laboratuvar testleri `tests/<paket>/lab/` altında, sonuç raporları `data/<aşama>/` altında.
- Karakterizasyon testleri (her aşamanın T01'i) mevcut davranışı belgeler; düzeltme görevi bu testi yeni beklenen davranışla günceller ve commit mesajında belirtir.

## 7. Commit ve PR

- Commit başlığı: `F2-T15: aday üretimi ve puanlama` biçiminde, görev kimliğiyle başlar.
- PR açıklaması: görev kimliği, "bitti" tanımının nasıl karşılandığı, çalıştırılan testler, ölçüm sonuçları (varsa dosya yolu), açık kalan noktalar.
- Bir PR tek görev veya tek uygulama paketidir. Sözleşme değişikliği ayrı PR'dır.
- Bayrak varsayılanı yalnızca o aşamanın regresyon sprinti (F0-S10, F1-S13, F2-S18, F3-S24, F4-S22, F5-S24, F6-S26) geçtikten sonra değiştirilir.

## 8. Takıldığınızda

- `spec.md` ile mevcut kod çelişiyorsa: kodu değiştirmeden önce çelişkiyi PR açıklamasına veya plan reposuna issue olarak yazın.
- Bir karar ADR gerektiriyorsa ([`docs/01-architecture/adr/README.md`](docs/01-architecture/adr/README.md)), ölçümü yapın, ADR taslağını yazın ve kararı kullanıcıya bırakın. ADR "Kabul edildi" olmadan ilgili görev bitmiş sayılmaz.
- Kullanıcı kararı bekleyen açık sorular [`docs/roadmap/master-plan.md`](docs/roadmap/master-plan.md) §8'dedir.
