# OpenHands Termux Edition

Versi OpenHands yang dioptimalkan untuk berjalan di Termux (Android) dengan dukungan custom base URL dan API key.

## 🚀 Fitur

- ✅ **100% kompatibel dengan Termux**
- ✅ **Custom Base URL API** - Dukung berbagai provider LLM
- ✅ **Custom API Key** - Mudah dikonfigurasi
- ✅ **Ringan** - Dependencies minimal
- ✅ **CLI Interaktif** - Interface yang user-friendly
- ✅ **Konfigurasi Fleksibel** - TOML configuration
- ✅ **Chat Mode** - Percakapan interaktif dengan AI

## 📱 Instalasi di Termux

### 1. Persiapan Termux

```bash
# Update Termux
pkg update && pkg upgrade

# Install Git (jika belum ada)
pkg install git
```

### 2. Clone Repository

```bash
git clone https://github.com/mulkymalikuldhrs/OpenHands.git
cd OpenHands
git checkout termux-version
```

### 3. Jalankan Setup

```bash
chmod +x termux_setup.sh
./termux_setup.sh
```

### 4. Restart Termux atau reload bashrc

```bash
source ~/.bashrc
```

## ⚙️ Konfigurasi

### Setup Awal

```bash
openhands config
```

Anda akan diminta memasukkan:
- **API Key**: API key dari provider LLM Anda
- **Base URL**: URL endpoint API (default: https://api.openai.com/v1)
- **Model**: Model yang akan digunakan (default: gpt-3.5-turbo)
- **Temperature**: Kreativitas respons (0.0-1.0)

### Contoh Konfigurasi untuk Provider Berbeda

#### OpenAI
```
API Key: sk-your-openai-key
Base URL: https://api.openai.com/v1
Model: gpt-3.5-turbo
```

#### Anthropic Claude
```
API Key: sk-ant-your-claude-key
Base URL: https://api.anthropic.com
Model: claude-3-sonnet-20240229
```

#### Local LLM (Ollama)
```
API Key: (kosongkan)
Base URL: http://localhost:11434/v1
Model: llama2
```

#### Custom Provider
```
API Key: your-custom-key
Base URL: https://your-custom-endpoint.com/v1
Model: your-model-name
```

## 🎯 Penggunaan

### Chat Interaktif

```bash
openhands chat
```

### Lihat Konfigurasi

```bash
openhands show-config
```

### Bantuan

```bash
openhands --help
```

## 📋 Perintah CLI

| Perintah | Deskripsi |
|----------|-----------|
| `openhands chat` | Mulai sesi chat interaktif |
| `openhands config` | Setup/edit konfigurasi |
| `openhands show-config` | Tampilkan konfigurasi saat ini |
| `openhands --version` | Tampilkan versi |
| `openhands --help` | Tampilkan bantuan |

## 🔧 Konfigurasi Manual

File konfigurasi tersimpan di: `~/.openhands/config/config.toml`

```toml
[llm]
api_key = "your-api-key"
base_url = "https://api.openai.com/v1"
model = "gpt-3.5-turbo"
temperature = 0.7
max_output_tokens = 2048
timeout = 60

[core]
workspace_base = "~/.openhands/workspace"
max_iterations = 100
debug = false
```

## 🛠️ Troubleshooting

### Error: litellm tidak terinstall
```bash
pip install litellm
```

### Error: Permission denied
```bash
chmod +x termux_cli.py
```

### Error: API Key tidak valid
```bash
openhands config
# Masukkan API key yang benar
```

### Error: Connection timeout
- Pastikan koneksi internet stabil
- Coba tingkatkan timeout di konfigurasi
- Periksa base URL yang digunakan

## 🔄 Update

```bash
cd OpenHands
git pull origin termux-version
./termux_setup.sh
```

## 📁 Struktur File

```
~/.openhands/
├── config/
│   └── config.toml          # File konfigurasi
├── workspace/               # Workspace untuk file
├── cache/                   # Cache
├── trajectories/            # History percakapan
└── file_store/             # Penyimpanan file
```

## 🎨 Fitur Chat

Dalam mode chat, Anda dapat:

- **Bertanya**: Ajukan pertanyaan apapun
- **Coding**: Minta bantuan dengan kode
- **Analisis**: Analisis file atau data
- **Clear**: Ketik `clear` untuk membersihkan history
- **Exit**: Ketik `exit` atau `quit` untuk keluar

## 🌟 Tips Penggunaan

1. **Gunakan model yang sesuai**: Pilih model berdasarkan kebutuhan dan budget
2. **Atur temperature**: 0.0 untuk respons konsisten, 1.0 untuk kreatif
3. **Monitor usage**: Pantau penggunaan API untuk mengontrol biaya
4. **Backup config**: Simpan file konfigurasi sebagai backup

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan:

1. Fork repository
2. Buat branch fitur baru
3. Commit perubahan
4. Push ke branch
5. Buat Pull Request

## 📄 Lisensi

MIT License - lihat file [LICENSE](LICENSE) untuk detail.

## 🆘 Support

Jika mengalami masalah:

1. Cek [Troubleshooting](#-troubleshooting)
2. Buka issue di GitHub
3. Diskusi di komunitas Termux

---

**OpenHands Termux Edition** - Code Less, Make More di Android! 🚀