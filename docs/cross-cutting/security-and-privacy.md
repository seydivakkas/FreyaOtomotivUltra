# Güvenlik ve kişisel verilerin korunması

Bu belge hukuki görüş değildir; KVKK uyumunun son kontrolü kurumun hukuk birimine aittir. Buradaki kurallar plan ve kod için asgari teknik gerekliliklerdir.

## 1. PoC'taki durum

**Korunacak mekanizmalar:** `kvkk_compliance.py` (saklama süresi, silme talebi), `redaction_kvkk_guard.py` (maskeleme), `audio_archive_compliance.py`, `security_utils.py` (imzalı müşteri bağlantıları, sınırlı gövde okuma), web oturumu için tek kullanımlık bilet, LLM'in yalnızca loopback Ollama'ya gitmesi ve `redact_identifiers` maskelemesi (F3 §3.4).

**Açıklar (doğrulanmış):**

| # | Açık | Aşama | Düzeltme |
| --- | --- | --- | --- |
| P4 | Kimlik doğrulaması olmadan, yalnızca arayan numarasıyla garanti ve bakım geçmişi paylaşılıyor | F3 | **F3-T05 — bayraktan bağımsız**, ADR-F3-01 |
| P5 | Her arayan için müşteri profili oluşturuluyor | F3 | F3-T30 (veri minimizasyonu) |
| P6 | LLM bağlamına ad, telefon, plaka, garanti, bakım geçmişi giriyor | F3 | F3-T30, F3-T31 |
| R9 | AudioSocket şifresiz ve kimlik doğrulamasız | F6 | F6-T20 (yalnızca loopback / özel ağ / tünel, IP izin listesi) |
| — | Ham ses kaydı yalnızca işlenmiş sesi yazıyor; ham kayıt ayarı yok | F0 | F0 `f0_record_raw` (varsayılan kapalı) |

## 2. Kurallar

### 2.1 Kimlik doğrulama (F3)
- Genel bilgi (çalışma saatleri, fiyat listesi, genel teknik bilgi) kimlik gerektirmez.
- **Özel kayıt okuma** (servis geçmişi, garanti, randevu durumu): arayan numarası + ikinci etken — doğum yılı, kayıtta yoksa plaka son 3–4 hanesi; görüşme başına en çok 3 deneme ([ADR-F3-01](../01-architecture/adr/ADR-F3-01-arayan-kimlik-dogrulama.md)).
- **Yazma işlemleri** (randevu oluşturma/değiştirme/iptal): ikinci etken + sözlü onay (Confirmation Manager) + idempotency.
- Doğrulama başarısızsa özel bilgi verilmez; operatöre aktarım önerilir.

### 2.2 Veri minimizasyonu
- Profil yalnızca işlem gerektiğinde açılır (P5).
- LLM bağlamına yalnızca o görevin gerektirdiği alanlar, maskelenmiş olarak girer (P6).
- Telemetri olaylarında transkript ve yanıt metni varsayılan olarak bulunmaz; uzunluk ve hash bulunur ([observability](observability.md)).

### 2.3 Ses kayıtları
- Ham ses kaydı **varsayılan kapalı** (`f0_record_raw = False`). Laboratuvar ve kabul testlerinde açılır; kayıtlar `data/` altında, saklama süresi `kvkk_compliance` kurallarıyla.
- Gerçek müşteri sesi içeren veri kümeleri (F1-T29, F2-T36, F0-T33) yalnızca açık rıza ile toplanır; rıza kaydı veri kümesi bildirimine (datasheet) eklenir ([datasets](../testing/datasets.md)).
- Ses kimliği (Leyla) referans kümesi ve speaker encoder çıktıları kişisel veri değildir (sentetik ses); gerçek müşteri sesinden üretilen gömüler kişisel veridir ve saklanmaz.

### 2.4 Transport ve ağ
- AudioSocket: yalnızca loopback, güvenilir özel ağ veya güvenli tünel; IP izin listesi; internete açılmaz.
- chan_websocket: TLS ve kimlik bilgileri.
- Web: tek kullanımlık oturum bileti korunur; uzaktan erişimde HTTPS/WSS.
- Ollama: yalnızca loopback (`127.0.0.1:11434`).
- Yönetim paneli (Studio) uçları kimlik doğrulama arkasında; operatör eylemleri denetim izine yazılır (mevcut `m08_review_audit` şeması).

### 2.5 Doğrulanmamış başarı iddiası
Freya "randevunuz oluşturuldu", "aktarıldınız", "SMS gönderildi" gibi cümleleri **yalnızca doğrulanmış araç sonucuyla** söyler (F3 K18). AMI mock modunda gerçek aktarım iddiası yoktur (F6 T43).

## 3. Görevler

| Görev | Öncelik |
| --- | --- |
| F3-T05 Kimlik doğrulamasız özel kayıt paylaşımının kapatılması | **Faz 0 — hemen** |
| F3-T03 Çoklu araç idempotency | Faz 0 |
| F6-T20 AudioSocket güvenliği | Telefon kabulünden önce |
| F3-T29 Policy Engine merkezileştirme, F3-T30 hafıza ve saklama | Faz 4 |
| [ADR-F3-01](../01-architecture/adr/ADR-F3-01-arayan-kimlik-dogrulama.md), [ADR-X-01](../01-architecture/adr/ADR-X-01-asterisk-dagitim.md), [ADR-X-03](../01-architecture/adr/ADR-X-03-yapay-zeka-bildirimi.md) | Kullanıcı kararı — kabul edildi (2026-11-26) |
