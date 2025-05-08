# Data‑Collection Module

Collect traffic traces from scripted Android‑emulator browsing sessions.

---

## 1 . What this folder does

* Spins up a rooted Android emulator (Magisk)  
* Automates browsing with configurable **duration**, **traffic intensity**, and **proxy / relay** settings  
* Saves packet captures (`.pcap`) for downstream analysis

---

## 2 . Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Android SDK** | `ANDROID_HOME` must point to the SDK root |
| **RootAVD** | For Magisk‑rooted emulator images |
| **Python ≥ 3.9** | Install packages from `requirements.txt` |

---

### Environment variables

Create `.env` **in the project root** (one level up from this folder):

```bash
# .env
export ANDROID_HOME=/path/to/your/androidsdk
export EMU_PATH=/path/to/your/androidsdk/emulator
export PCAP_PATH=/path/to/your/project/data/pcaps
export SCRIPT_DIR=/path/to/your/project
export ROOTAVD_PATH=/path/to/your/rootAVD
```

Load them once per shell:

```bash
source .env
```

---

## 3 . Quick start

```bash
# run a 2‑hour low‑intensity session, direct traffic via Bright Data proxy, with GUI hidden
python emulator/browse_emu_mixed_simplified.py 120 LOW NO 2 NO NO
```

**CLI arguments**

| Pos | Name      | Values / Example | Description                              |
|-----|-----------|------------------|------------------------------------------|
| 1   | `duration`| `120`            | Minutes per session                      |
| 2   | `intensity`| `LOW | MEDIUM | HIGH` | Browsing aggressiveness                |
| 3   | `relay`   | `YES | NO`       | Include relayed traffic or not           |
| 4   | `proxy`   | `2`              | Proxy provider (currently Bright Data)   |
| 5   | `pcapdroid`| `YES | NO`      | Use PCAPDroid for capture                |
| 6   | `window`  | `YES | NO`       | Show emulator GUI window                 |

Intensity presets:

* **LOW** – passive scrolls  
* **MEDIUM** – scroll + click  
* **HIGH** – rapid scroll, clicks, form actions  

---

## 4 . Batch collection script

For continuous cycles run:

```bash
./emulator/scripts/run.sh
```

Default sequence (4 × 120 min):

1. LOW / direct  
2. LOW / relay  
3. MEDIUM / relay  
4. HIGH / relay  

Edit `scripts/run.sh` to customise durations or order.

---

## 5 . Outputs

* `.pcap` files appear in **`${PCAP_PATH}`**, named:  
  ```
  mixed_<unix‑ts>_<intensity>.pcap       # direct
  mixed_<unix‑ts>_<intensity>_relay.pcap # relayed
  ```
* Log files in `logs/` (one per session)

---

## 6 . Next steps

Once captures are ready, move to the **analysis** module (`analysis/`) for parsing and feature extraction.