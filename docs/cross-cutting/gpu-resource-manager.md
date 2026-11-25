# GPU Resource Manager (AP08)

Üç büyük model (Whisper, Qwen, FreyaTTS) tek RTX 4070 Laptop 8 GB üzerinde çalışır. Bu bileşen GPU işlerinin önceliğini, bekleme kuyruklarını, VRAM durumunu ve iptalleri merkezi olarak yönetir.

**Kod:** `backend/runtime_resources/` — `gpu_scheduler.py`, `priority_queue.py`, `memory_budget.py`, `cancellation.py`
**Tüketiciler:** F2 Inference Scheduler (F2 §5.14), F3 LLM çağrıları (F3-T33), F5 Inference Scheduler (F5 §5.4), F1 spekülatif STT (F1 §5.7)

## 1. PoC'taki durum

| Konu | Kod | Not |
| --- | --- | --- |
| STT kilidi | `models.stt_lock` (`threading.Lock`) | STT kendi içinde sıralı |
| TTS kilitleri | `models.lock` (asyncio) + `worker_lock` (thread) | Toplu yolda kilitsiz `to_thread` (F5 N4) |
| İptal | `asyncio.shield` | İptal edilen STT ve TTS işi GPU'da sürüyor (F2 S7, F5 N5) |
| STT ↔ TTS | Ayrı kilitler | **STT ve TTS aynı anda GPU'da çalışabiliyor**; aralarında öncelik yok |
| LLM | Ollama (ayrı süreç), `keep_alive: -1`, `num_gpu: 8` (`ollama_gpu_layers`), `num_ctx: 4096` | Qwen 2.5 7B'nin 28 katmanından yalnızca 8'i GPU'da; kalanı CPU'da. LLM turu ≈ 6 s ölçümünün olası nedenlerinden biri — ölçülmeli |
| VRAM gözlemi | `gpu_health_circuit_breaker.py` (`nvidia-smi`, `torch.cuda.mem_get_info`) | Yalnızca gözlem panelinde; zamanlamaya bağlı değil |
| Ölçüm | Tepe 7478 / 8188 MiB | Ön ısıtmadan önce; model başına dağılım bilinmiyor |

## 2. Öncelikler

| Öncelik | İş | Kaynak | Önalım (preemption) |
| --- | --- | --- | --- |
| P0 | Aktif barge-in için gerekli STT | F1/F2 | Başlamamış alt öncelikli işlerin önüne geçer |
| P1 | Final STT | F2 | |
| P2 | İlk TTS cümleciği | F5 | |
| P3 | Gerekli LLM çıkarımı | F3 | Ollama isteği; Freya içinden önalım yok |
| P4 | Sonraki TTS cümlecikleri | F5 | Deadline: önceki cümleciğin oynatma bitişi |
| P5 | Kısmi / spekülatif STT | F1/F2 | GPU yükü yüksekken azaltılır |
| P6 | Önbellek ön ısıtma | F5 | Görüşme yokken |
| P7 | Benchmark, akustik analiz | Lab | Canlı görüşme varken çalışmaz |

**Kurallar:**
1. **Başlamamış iş iptal edilebilir; başlamış CUDA işi durdurulmuş sayılmaz.** Sonucu atılır (veya F2'de birleştirme için saklanır), bellek güvenle serbest bırakılır.
2. **Önalım yalnızca kuyruk düzeyindedir.** Çalışan bir çekirdek kesilmez. Bu yüzden uzun işler (TTS yığını, uzun STT) parçalanır ki yüksek öncelikli iş en fazla bir parça süresi bekler.
3. **Aynı anda en fazla bir TTS GPU yığını** (F5 N4). STT ve TTS'in aynı anda çalışmasına izin verilip verilmeyeceği ölçümle kararlaştırılır (ADR-X-02): eşzamanlılık toplam işi hızlandırabilir ama P0/P1 gecikmesini artırabilir.
4. **Deadline farkındalığı:** Öncelik eşitse deadline'ı yakın olan önce. F5 P4 işinin deadline'ı önceki cümleciğin oynatma bitişidir (F6 `PlaybackState`).
5. **Kabul denetimi (admission):** Bütçe doluysa iş reddedilmez, bekletilir; bekleme süresi telemetriye yazılır.
6. **LLM:** Ollama ayrı süreçtir. Yönetici LLM için yalnızca "ne zaman istek gönderilir" kararını verir (eşzamanlı LLM isteği en fazla 1) ve Ollama'nın yerleşik belleğini bütçeye sabit kalem olarak yazar.

## 3. VRAM bütçesi

Bütçe ölçümle doldurulur (F5-T01). Ölçülmeden değer yazılmaz.

| Kalem | Değer | Kaynak |
| --- | --- | --- |
| Whisper large-v3-turbo FP16 (yüklü + çalışma tepe) | Ölçüm bekleniyor | F5-T01 |
| FreyaTTS DiT + AudioVAE (yüklü + yığın tepe) | Ölçüm bekleniyor | F5-T01 |
| Ollama Qwen 2.5 7B (`num_gpu` = 8 ve alternatifler) | Ölçüm bekleniyor | F5-T01 + ADR-X-02 |
| CUDA bağlamları ve parçalanma | Ölçüm bekleniyor | |
| Masaüstü uygulamaları | ≈ 1770 MiB (ölçülmüş, 6 Kasım) | `measured-latency.json` |
| Güvenlik payı | Öneri ≥ 300 MiB | |

`config/resources/gpu_budget.json` bu tabloyu tutar. `memory_budget.py`:
- Başlangıçta `torch.cuda.mem_get_info` ve `nvidia-smi` ile gerçek boş belleği okur (mevcut `gpu_health_circuit_breaker` sorgularını yeniden kullanır).
- Her GPU işinden önce tahmini tepe belleği kontrol eder; yetmiyorsa bekletir.
- CUDA OOM: önbelleği boşaltır, işi bir kez daha küçük profille dener (F2: `FAST`, F5: daha küçük yığın), yine olmazsa aşamanın kurtarma yoluna verir. **Oturum düşmez.**

## 4. `num_gpu` (Ollama katman sayısı) kararı — ADR-X-02

LLM gecikmesi ile STT/TTS için kalan VRAM arasında doğrudan bir değiş tokuş vardır. Ölçülecek matris:

| `num_gpu` | Ollama VRAM | LLM ilk token / toplam süre (p50/p95) | STT + TTS tepe ile toplam VRAM | OOM |
| --- | --- | --- | --- | --- |
| 8 (bugün) | | | | |
| 16 | | | | |
| 28 (tamamı) | | | | |

Masaüstü uygulamaları kapalı ve açık olarak ayrı ölçülür. Karar ADR-X-02'ye yazılır.

## 5. Arayüz

```python
class GpuJob(Protocol):
    session_id: str
    generation_id: int
    priority: Priority           # P0..P7
    deadline_ns: int | None
    est_peak_mib: int | None     # ölçülmemişse None → muhafazakâr varsayılan
    stage: Literal["stt", "tts", "llm", "lab"]

async def submit(job: GpuJob, fn: Callable[[], T]) -> T: ...   # kuyruk + bütçe + yürütme
def cancel(session_id: str, generation_id: int | None = None) -> int: ...  # başlamamış işleri iptal eder, sayısını döndürür
```

- İptal `automotive_voice/core/cancellation.CancellationController` ile tutarlıdır: bir generation ilerlediğinde eski generation'ın başlamamış GPU işleri kuyruktan çıkarılır.
- Her iş için telemetri: kuyrukta bekleme, çalışma süresi, tepe bellek, iptal/atılma durumu.

## 6. Görevler

Ortak yönetici tek bir yerde yazılır. Aşama görevleri onu kullanır:

| Görev | İçerik |
| --- | --- |
| F5-T01 | VRAM ve çıkarım envanteri (model başına) |
| F5-T16 | Ortak GPU yöneticisi (`runtime_resources/`) — **sahibi** |
| F2-T07, F2-T27 | STT önceliklendirme ve entegrasyon |
| F3-T33 | LLM çağrı politikası |
| F1-T17 | Spekülatif STT (P5, barge-in'de P0) |
| M06 paketi | Ortak GPU zamanlayıcının uygulanması ([M06](../execution/packages/W1/M06-gpu-zamanlayici.md)); gerçek yük ölçümü G4'te |

## 7. Kabul

| # | Kriter | Hedef |
| --- | --- | --- |
| G1 | OOM kaynaklı oturum düşmesi | 0 |
| G2 | P0 STT'nin kuyrukta bekleme süresi p95 | ≤ bir TTS parçası süresi (ölçülüp yazılır) |
| G3 | İptal edilmiş başlamamış işin GPU'da çalışması | 0 |
| G4 | 1, 2, 4 eşzamanlı görüşmede tepe VRAM | Bütçe içinde; ölçülen değer raporlanır |
| G5 | `max_concurrent_calls` | Ölçülen kapasiteye çekilir (F5 N10) |
