# Kodlama ajanı rehberi — FreyaTTS_Automotive_PoC

> Bu dosya `seydivakkas/FreyaOtomotivUltra` plan reposundaki `docs/execution/templates/poc-CLAUDE.md` şablonundan kopyalanmıştır. PoC reposunun köküne hem `CLAUDE.md` hem `AGENTS.md` adıyla konur. PoC'ta zaten bir `CLAUDE.md` varsa bu metin en üste eklenir, mevcut içerik altında korunur.

Bu repo Freya'nın **kodudur**. Ne yapılacağı, hangi sırayla yapılacağı ve ne zaman bitmiş sayılacağı **plan reposunda** tanımlıdır:

**https://github.com/seydivakkas/FreyaOtomotivUltra**

## Başlamadan önce

1. Plan reposunu bu reponun yanına klonlayın (veya oturuma ekleyin):

   ```text
   workspace/
   ├── FreyaOtomotivUltra/          ← plan (salt okunur)
   └── FreyaTTS_Automotive_PoC/     ← bu repo
   ```

2. Plan reposundaki `CLAUDE.md` dosyasını baştan sona okuyun. **Tek kural kaynağı odur.**
3. Size verilen paketin dosyasını okuyun: `FreyaOtomotivUltra/docs/execution/packages/<dalga>/<ID>-*.md` (veya aşamalar için `docs/execution/stages/`). Giriş noktası: `docs/execution/README.md`.
4. Plan reposuna erişemiyorsanız **kod yazmayın**; durun ve bunu bildirin.

## Plan okunamazsa bile geçerli olan asgari kurallar

- Kullanıcı açıkça başlatmadıkça paket başlatılmaz ("M00 paketini başlat"). Bir oturumda tek paket; paket bitince PR açılır ve durulur.
- Mevcut testler her görevden sonra geçer: `pytest tests/ experimental/tests/ -q -m "not llm and not gpu and not pbx"`. Test silinmez.
- Yeni davranış bayrak arkasındadır (`f0_pipeline_v2` … `f6_pipeline_v2`); bayrak kapalıyken mevcut davranış değişmez. İstisna: H01 paketindeki düzeltmeler.
- Yeni ağır model yüklenmez, model indirilmez. FreyaTTS ağırlıkları değişmez; Leyla sesi seed 9.
- GPU işi yalnız ortak yöneticiden (`backend/runtime_resources/`) geçer.
- Ölçülmemiş değer kanıt diye yazılmaz (`null` / "Ölçüm bekleniyor"); mock veri etiketlenir.
- Kanıt `evidence/<PAKET>/<run_id>/` altına yazılır (`manifest.json`, `test-log.txt`, `decision.json`).
- Dal `paket/<ID>`; commit başlığı görev kimliğiyle başlar (`F2-B.07: …`); `main`'e doğrudan push yok.
- Yeni dosyalara "ÖZEL LİSANS — TÜM HAKLAR SAKLIDIR" başlığı eklenir.
- Kişisel veri: kimlik doğrulamasız özel kayıt paylaşılmaz; LLM bağlamına yalnız gerekli alanlar girer.
