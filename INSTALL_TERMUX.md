# Panduan Instalasi OpenHands di Termux

Panduan lengkap untuk menginstall dan menggunakan OpenHands di Termux (Android).

## 📱 Persiapan

### 1. Install Termux

Download Termux dari:
- [F-Droid](https://f-droid.org/packages/com.termux/) (Recommended)
- [GitHub Releases](https://github.com/termux/termux-app/releases)

⚠️ **Jangan install dari Google Play Store** karena versi di sana sudah outdated.

### 2. Setup Termux

```bash
# Update packages
pkg update && pkg upgrade

# Install Git
pkg install git

# Setup storage (optional, untuk akses file Android)
termux-setup-storage
```

## 🚀 Instalasi OpenHands

### Metode 1: Instalasi Otomatis (Recommended)

```bash
# Clone repository
git clone https://github.com/mulkymalikuldhrs/OpenHands.git
cd OpenHands
git checkout termux-version

# Jalankan installer Python
python install_termux.py
```

### Metode 2: Instalasi Manual

```bash
# Clone repository
git clone https://github.com/mulkymalikuldhrs/OpenHands.git
cd OpenHands
git checkout termux-version

# Jalankan setup script
chmod +x termux_setup.sh
./termux_setup.sh
```

### Metode 3: Instalasi Step-by-Step

```bash
# 1. Update Termux
pkg update && pkg upgrade

# 2. Install dependencies
pkg install python python-pip git nodejs npm rust binutils clang make cmake pkg-config libffi openssl zlib

# 3. Install Python packages
pip install --upgrade pip setuptools wheel
pip install -r requirements-termux.txt

# 4. Setup directories
mkdir -p ~/.openhands/{config,workspace,cache,trajectories,file_store}

# 5. Copy config
cp termux_config.toml ~/.openhands/config/config.toml

# 6. Setup CLI
chmod +x termux_cli.py
ln -sf $(pwd)/termux_cli.py ~/.openhands/openhands
cp termux_agent.py ~/.openhands/

# 7. Add to PATH
echo 'export PATH="$HOME/.openhands:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## ✅ Verifikasi Instalasi

```bash
# Test instalasi
python test_termux.py

# Cek CLI
openhands --help
```

## ⚙️ Konfigurasi

### Setup API Key

```bash
openhands config
```

Masukkan informasi berikut:
- **API Key**: API key dari provider LLM
- **Base URL**: Endpoint API
- **Model**: Model yang akan digunakan
- **Temperature**: Kreativitas respons (0.0-1.0)

### Contoh Konfigurasi Provider

#### OpenAI
```
API Key: sk-your-openai-key
Base URL: https://api.openai.com/v1
Model: gpt-3.5-turbo
Temperature: 0.7
```

#### Anthropic Claude
```
API Key: sk-ant-your-claude-key
Base URL: https://api.anthropic.com
Model: claude-3-sonnet-20240229
Temperature: 0.7
```

#### Google Gemini
```
API Key: your-gemini-key
Base URL: https://generativelanguage.googleapis.com/v1beta
Model: gemini-pro
Temperature: 0.7
```

#### Local Ollama
```
API Key: (kosongkan)
Base URL: http://localhost:11434/v1
Model: llama2
Temperature: 0.7
```

#### Groq
```
API Key: your-groq-key
Base URL: https://api.groq.com/openai/v1
Model: mixtral-8x7b-32768
Temperature: 0.7
```

## 🎯 Penggunaan

### Chat Interaktif

```bash
openhands chat
```

### Perintah dalam Chat

- **Pertanyaan biasa**: Ajukan pertanyaan apapun
- **Tool commands**: Gunakan tools untuk file/command operations
- **clear**: Bersihkan history percakapan
- **exit** atau **quit**: Keluar dari chat

### Contoh Tool Usage

```
# Jalankan command
Tolong jalankan command "ls -la" untuk melihat file di direktori ini

# Baca file
Baca file ~/.bashrc dan jelaskan isinya

# Tulis file
Buatkan file hello.py yang berisi program hello world

# List direktori
Tampilkan isi direktori /sdcard/Download
```

## 🔧 Troubleshooting

### Error: Command not found

```bash
# Pastikan PATH sudah diset
echo $PATH
source ~/.bashrc

# Atau jalankan langsung
~/.openhands/openhands chat
```

### Error: litellm tidak terinstall

```bash
pip install litellm
```

### Error: Permission denied

```bash
chmod +x ~/.openhands/openhands
```

### Error: API Key tidak valid

```bash
# Reconfigure API key
openhands config
```

### Error: Connection timeout

1. Cek koneksi internet
2. Coba provider lain
3. Tingkatkan timeout di config

### Error: Dependencies gagal install

```bash
# Install satu per satu
pip install litellm
pip install aiohttp
pip install fastapi
pip install uvicorn
pip install toml
pip install python-dotenv
```

### Error: Rust compiler

```bash
# Install Rust
pkg install rust
```

### Error: Build tools

```bash
# Install build tools
pkg install clang make cmake
```

## 📁 Struktur File

```
~/.openhands/
├── openhands                    # CLI executable
├── termux_agent.py             # Agent dengan tool support
├── config/
│   └── config.toml             # Konfigurasi
├── workspace/                  # Workspace untuk file
├── cache/                      # Cache
├── trajectories/               # History percakapan
└── file_store/                # Penyimpanan file
```

## 🔄 Update

```bash
cd OpenHands
git pull origin termux-version
python install_termux.py
```

## 🗑️ Uninstall

```bash
# Hapus files
rm -rf ~/.openhands

# Hapus dari PATH (edit ~/.bashrc)
nano ~/.bashrc
# Hapus baris: export PATH="$HOME/.openhands:$PATH"
```

## 💡 Tips

1. **Gunakan WiFi**: Untuk download dependencies yang besar
2. **Monitor storage**: Termux butuh space untuk dependencies
3. **Backup config**: Simpan file config sebagai backup
4. **Test provider**: Coba berbagai provider untuk performa terbaik
5. **Update regular**: Update Termux dan dependencies secara berkala

## 🆘 Bantuan

Jika masih mengalami masalah:

1. Jalankan test: `python test_termux.py`
2. Cek log error dengan detail
3. Buka issue di GitHub repository
4. Diskusi di komunitas Termux

---

**Happy coding with OpenHands on Termux! 🚀**