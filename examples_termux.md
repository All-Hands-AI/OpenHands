# Contoh Penggunaan OpenHands Termux

Kumpulan contoh penggunaan OpenHands di Termux untuk berbagai keperluan.

## 🤖 Chat Dasar

### Pertanyaan Umum

```
👤 Anda: Apa itu Python dan mengapa populer?

🤖 OpenHands: Python adalah bahasa pemrograman tingkat tinggi yang populer karena:

1. **Sintaks sederhana**: Mudah dibaca dan dipelajari
2. **Versatile**: Bisa untuk web, AI, data science, automation
3. **Library lengkap**: Ekosistem package yang sangat besar
4. **Community**: Komunitas yang aktif dan supportive
5. **Cross-platform**: Berjalan di Windows, Mac, Linux, Android (Termux)

Di Termux, Python sangat berguna untuk automation, scripting, dan development mobile.
```

### Bantuan Coding

```
👤 Anda: Buatkan function Python untuk menghitung faktorial

🤖 OpenHands: Berikut beberapa cara membuat function faktorial:

**1. Recursive (Rekursif):**
```python
def factorial_recursive(n):
    if n == 0 or n == 1:
        return 1
    return n * factorial_recursive(n - 1)

# Contoh penggunaan
print(factorial_recursive(5))  # Output: 120
```

**2. Iterative (Loop):**
```python
def factorial_iterative(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

# Contoh penggunaan
print(factorial_iterative(5))  # Output: 120
```

**3. Menggunakan math.factorial:**
```python
import math

def factorial_builtin(n):
    return math.factorial(n)

# Contoh penggunaan
print(factorial_builtin(5))  # Output: 120
```
```

## 🛠️ Tool Commands

### File Operations

```
👤 Anda: Tolong baca file ~/.bashrc dan jelaskan isinya

🤖 OpenHands: TOOL_CALL: read_file("/data/data/com.termux/files/home/.bashrc")

📋 Tool Results:
✅ read_file:
```
# Termux bashrc
export PATH="$HOME/.openhands:$PATH"
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
```

File ~/.bashrc berisi:
1. **PATH export**: Menambahkan ~/.openhands ke PATH untuk akses CLI
2. **Aliases**: Shortcut untuk command ls dengan berbagai format
   - `ll`: ls -la (list lengkap dengan hidden files)
   - `la`: ls -A (list semua kecuali . dan ..)
   - `l`: ls -CF (list dengan indicator)

File ini dijalankan setiap kali Anda membuka terminal baru.
```

### Command Execution

```
👤 Anda: Jalankan command "uname -a" untuk melihat info sistem

🤖 OpenHands: TOOL_CALL: execute_command("uname -a")

📋 Tool Results:
✅ execute_command:
```
Linux localhost 4.14.186-perf+ #1 SMP PREEMPT Mon Jul 8 12:47:23 UTC 2024 aarch64 Android
```

Informasi sistem Anda:
- **OS**: Linux (Android kernel)
- **Hostname**: localhost
- **Kernel**: 4.14.186-perf+
- **Architecture**: aarch64 (ARM 64-bit)
- **Build**: Android system

Ini menunjukkan Anda menggunakan Termux di perangkat Android dengan processor ARM 64-bit.
```

### Directory Listing

```
👤 Anda: Tampilkan isi direktori /sdcard/Download

🤖 OpenHands: TOOL_CALL: list_directory("/sdcard/Download")

📋 Tool Results:
✅ list_directory:
```
  file: document.pdf
  file: image.jpg
  file: music.mp3
  directory: Apps
  file: termux-backup.tar.gz
```

Direktori /sdcard/Download berisi:
- **document.pdf**: File PDF
- **image.jpg**: File gambar
- **music.mp3**: File audio
- **Apps/**: Subdirectory (mungkin berisi APK)
- **termux-backup.tar.gz**: Backup Termux

Anda bisa mengakses file-file ini dari Termux untuk processing lebih lanjut.
```

## 💻 Development Tasks

### Membuat Project Python

```
👤 Anda: Buatkan project Python sederhana untuk web scraping dengan requests dan BeautifulSoup

🤖 OpenHands: Saya akan membuatkan project web scraping untuk Anda.

TOOL_CALL: write_file("webscraper.py", "#!/usr/bin/env python3\n\"\"\"\nWeb Scraper Sederhana\nScraper untuk mengambil data dari website\n\"\"\"\n\nimport requests\nfrom bs4 import BeautifulSoup\nimport json\nimport time\n\nclass WebScraper:\n    def __init__(self):\n        self.session = requests.Session()\n        self.session.headers.update({\n            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36'\n        })\n    \n    def scrape_quotes(self):\n        \"\"\"Scrape quotes dari quotes.toscrape.com\"\"\"\n        url = 'http://quotes.toscrape.com/'\n        \n        try:\n            response = self.session.get(url)\n            response.raise_for_status()\n            \n            soup = BeautifulSoup(response.content, 'html.parser')\n            quotes = []\n            \n            for quote in soup.find_all('div', class_='quote'):\n                text = quote.find('span', class_='text').text\n                author = quote.find('small', class_='author').text\n                tags = [tag.text for tag in quote.find_all('a', class_='tag')]\n                \n                quotes.append({\n                    'text': text,\n                    'author': author,\n                    'tags': tags\n                })\n            \n            return quotes\n            \n        except requests.RequestException as e:\n            print(f'Error: {e}')\n            return []\n    \n    def save_to_json(self, data, filename='quotes.json'):\n        \"\"\"Simpan data ke file JSON\"\"\"\n        with open(filename, 'w', encoding='utf-8') as f:\n            json.dump(data, f, indent=2, ensure_ascii=False)\n        print(f'Data disimpan ke {filename}')\n\ndef main():\n    scraper = WebScraper()\n    \n    print('🕷️ Memulai web scraping...')\n    quotes = scraper.scrape_quotes()\n    \n    if quotes:\n        print(f'✅ Berhasil scrape {len(quotes)} quotes')\n        scraper.save_to_json(quotes)\n        \n        # Tampilkan beberapa contoh\n        print('\\n📋 Contoh quotes:')\n        for i, quote in enumerate(quotes[:3]):\n            print(f'{i+1}. \"{quote[\"text\"]}\" - {quote[\"author\"]}')\n    else:\n        print('❌ Gagal scrape data')\n\nif __name__ == '__main__':\n    main()")

TOOL_CALL: write_file("requirements.txt", "requests>=2.28.0\nbeautifulsoup4>=4.11.0\nlxml>=4.9.0")

TOOL_CALL: write_file("README.md", "# Web Scraper Project\n\nProject sederhana untuk web scraping menggunakan Python.\n\n## Dependencies\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\n```bash\npython webscraper.py\n```\n\n## Features\n\n- Scrape quotes dari quotes.toscrape.com\n- Simpan hasil ke JSON\n- Error handling\n- User-Agent header\n\n## Output\n\nFile `quotes.json` berisi array quotes dengan format:\n\n```json\n[\n  {\n    \"text\": \"Quote text\",\n    \"author\": \"Author name\",\n    \"tags\": [\"tag1\", \"tag2\"]\n  }\n]\n```")

📋 Tool Results:
✅ write_file: Success
✅ write_file: Success  
✅ write_file: Success

Project web scraping berhasil dibuat! 🎉

**Files yang dibuat:**
1. **webscraper.py**: Main scraper script
2. **requirements.txt**: Dependencies
3. **README.md**: Dokumentasi

**Untuk menjalankan:**
```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan scraper
python webscraper.py
```

**Features:**
- ✅ Scrape quotes dari quotes.toscrape.com
- ✅ Simpan hasil ke JSON
- ✅ Error handling
- ✅ Proper User-Agent header
- ✅ Class-based structure

Project siap digunakan dan bisa dikembangkan lebih lanjut!
```

### Automation Script

```
👤 Anda: Buatkan script untuk backup file penting di Termux

🤖 OpenHands: Saya akan buatkan script backup otomatis untuk Termux.

TOOL_CALL: write_file("backup_termux.py", "#!/usr/bin/env python3\n\"\"\"\nTermux Backup Script\nScript untuk backup file dan konfigurasi penting di Termux\n\"\"\"\n\nimport os\nimport shutil\nimport tarfile\nimport datetime\nfrom pathlib import Path\n\nclass TermuxBackup:\n    def __init__(self):\n        self.home = Path.home()\n        self.backup_dir = self.home / 'backups'\n        self.backup_dir.mkdir(exist_ok=True)\n        \n        # File dan direktori yang akan di-backup\n        self.backup_items = [\n            '.bashrc',\n            '.profile', \n            '.vimrc',\n            '.openhands/',\n            '.termux/',\n            'bin/',\n            'projects/',\n            '.ssh/',\n            '.gitconfig'\n        ]\n    \n    def create_backup(self):\n        \"\"\"Buat backup dengan timestamp\"\"\"\n        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')\n        backup_name = f'termux_backup_{timestamp}.tar.gz'\n        backup_path = self.backup_dir / backup_name\n        \n        print(f'🗂️ Membuat backup: {backup_name}')\n        \n        with tarfile.open(backup_path, 'w:gz') as tar:\n            for item in self.backup_items:\n                item_path = self.home / item\n                \n                if item_path.exists():\n                    print(f'  ✅ Adding: {item}')\n                    tar.add(item_path, arcname=item)\n                else:\n                    print(f'  ⚠️ Skipping: {item} (not found)')\n        \n        # Buat info file\n        info_content = f\"\"\"Termux Backup Info\n===================\nDate: {datetime.datetime.now()}\nBackup file: {backup_name}\nItems backed up: {len([i for i in self.backup_items if (self.home / i).exists()])}\n\nContents:\n\"\"\" + '\\n'.join([f'- {item}' for item in self.backup_items if (self.home / item).exists()])\n        \n        info_path = self.backup_dir / f'backup_info_{timestamp}.txt'\n        with open(info_path, 'w') as f:\n            f.write(info_content)\n        \n        print(f'✅ Backup selesai: {backup_path}')\n        print(f'📋 Info file: {info_path}')\n        \n        return backup_path\n    \n    def list_backups(self):\n        \"\"\"List semua backup yang ada\"\"\"\n        backups = list(self.backup_dir.glob('termux_backup_*.tar.gz'))\n        \n        if not backups:\n            print('📭 Tidak ada backup ditemukan')\n            return\n        \n        print(f'📦 Ditemukan {len(backups)} backup:')\n        for backup in sorted(backups):\n            size = backup.stat().st_size / (1024 * 1024)  # MB\n            mtime = datetime.datetime.fromtimestamp(backup.stat().st_mtime)\n            print(f'  - {backup.name} ({size:.1f} MB, {mtime.strftime(\"%Y-%m-%d %H:%M\")})')\n    \n    def restore_backup(self, backup_file):\n        \"\"\"Restore dari backup file\"\"\"\n        backup_path = self.backup_dir / backup_file\n        \n        if not backup_path.exists():\n            print(f'❌ Backup file tidak ditemukan: {backup_file}')\n            return False\n        \n        print(f'🔄 Restoring dari: {backup_file}')\n        \n        # Konfirmasi\n        confirm = input('⚠️ Ini akan menimpa file yang ada. Lanjutkan? (y/N): ')\n        if confirm.lower() != 'y':\n            print('❌ Restore dibatalkan')\n            return False\n        \n        try:\n            with tarfile.open(backup_path, 'r:gz') as tar:\n                tar.extractall(self.home)\n            \n            print('✅ Restore berhasil!')\n            print('🔄 Restart Termux untuk menerapkan perubahan')\n            return True\n            \n        except Exception as e:\n            print(f'❌ Error saat restore: {e}')\n            return False\n    \n    def cleanup_old_backups(self, keep_count=5):\n        \"\"\"Hapus backup lama, simpan hanya yang terbaru\"\"\"\n        backups = sorted(self.backup_dir.glob('termux_backup_*.tar.gz'))\n        \n        if len(backups) <= keep_count:\n            print(f'📦 Hanya ada {len(backups)} backup, tidak perlu cleanup')\n            return\n        \n        to_delete = backups[:-keep_count]\n        \n        print(f'🗑️ Menghapus {len(to_delete)} backup lama:')\n        for backup in to_delete:\n            print(f'  - {backup.name}')\n            backup.unlink()\n            \n            # Hapus info file juga\n            info_file = backup.with_name(backup.name.replace('termux_backup_', 'backup_info_').replace('.tar.gz', '.txt'))\n            if info_file.exists():\n                info_file.unlink()\n        \n        print(f'✅ Cleanup selesai, tersisa {keep_count} backup terbaru')\n\ndef main():\n    import argparse\n    \n    parser = argparse.ArgumentParser(description='Termux Backup Tool')\n    parser.add_argument('action', choices=['backup', 'list', 'restore', 'cleanup'], \n                       help='Action to perform')\n    parser.add_argument('--file', help='Backup file untuk restore')\n    parser.add_argument('--keep', type=int, default=5, help='Jumlah backup yang disimpan (default: 5)')\n    \n    args = parser.parse_args()\n    \n    backup_tool = TermuxBackup()\n    \n    if args.action == 'backup':\n        backup_tool.create_backup()\n        backup_tool.cleanup_old_backups(args.keep)\n        \n    elif args.action == 'list':\n        backup_tool.list_backups()\n        \n    elif args.action == 'restore':\n        if not args.file:\n            print('❌ Specify backup file dengan --file')\n            return\n        backup_tool.restore_backup(args.file)\n        \n    elif args.action == 'cleanup':\n        backup_tool.cleanup_old_backups(args.keep)\n\nif __name__ == '__main__':\n    main()")

TOOL_CALL: write_file("backup_cron.sh", "#!/data/data/com.termux/files/usr/bin/bash\n\n# Termux Backup Cron Script\n# Jalankan backup otomatis\n\necho \"$(date): Starting automatic backup\" >> ~/backups/backup.log\npython3 ~/backup_termux.py backup >> ~/backups/backup.log 2>&1\necho \"$(date): Backup completed\" >> ~/backups/backup.log")

📋 Tool Results:
✅ write_file: Success
✅ write_file: Success

Script backup Termux berhasil dibuat! 🎉

**Files yang dibuat:**
1. **backup_termux.py**: Main backup script
2. **backup_cron.sh**: Script untuk automation

**Penggunaan:**

```bash
# Buat backup
python backup_termux.py backup

# List backup yang ada
python backup_termux.py list

# Restore dari backup
python backup_termux.py restore --file termux_backup_20241212_143022.tar.gz

# Cleanup backup lama
python backup_termux.py cleanup --keep 3
```

**Features:**
- ✅ Backup file konfigurasi penting (.bashrc, .vimrc, dll)
- ✅ Backup direktori .openhands, .termux, projects
- ✅ Compressed backup dengan timestamp
- ✅ List dan restore functionality
- ✅ Auto cleanup backup lama
- ✅ Logging untuk automation

**Setup automation (optional):**
```bash
# Install cronie untuk cron jobs
pkg install cronie

# Setup cron untuk backup harian
chmod +x backup_cron.sh
crontab -e
# Tambahkan: 0 2 * * * /data/data/com.termux/files/home/backup_cron.sh
```

Script siap digunakan untuk backup rutin! 🔒
```

## 📊 Data Analysis

```
👤 Anda: Analisis file CSV dan buat visualisasi sederhana

🤖 OpenHands: Saya akan buatkan script untuk analisis CSV dengan visualisasi.

TOOL_CALL: write_file("data_analyzer.py", "#!/usr/bin/env python3\n\"\"\"\nCSV Data Analyzer\nScript untuk analisis data CSV dan visualisasi sederhana\n\"\"\"\n\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport numpy as np\nfrom pathlib import Path\n\nclass CSVAnalyzer:\n    def __init__(self, csv_file):\n        self.csv_file = Path(csv_file)\n        self.df = None\n        self.load_data()\n    \n    def load_data(self):\n        \"\"\"Load CSV data\"\"\"\n        try:\n            self.df = pd.read_csv(self.csv_file)\n            print(f'✅ Data loaded: {len(self.df)} rows, {len(self.df.columns)} columns')\n        except Exception as e:\n            print(f'❌ Error loading data: {e}')\n            return False\n        return True\n    \n    def basic_info(self):\n        \"\"\"Tampilkan informasi dasar dataset\"\"\"\n        if self.df is None:\n            return\n        \n        print('\\n📊 Dataset Info:')\n        print(f'Shape: {self.df.shape}')\n        print(f'Columns: {list(self.df.columns)}')\n        \n        print('\\n📋 Data Types:')\n        print(self.df.dtypes)\n        \n        print('\\n📈 Statistical Summary:')\n        print(self.df.describe())\n        \n        print('\\n🔍 Missing Values:')\n        missing = self.df.isnull().sum()\n        if missing.sum() > 0:\n            print(missing[missing > 0])\n        else:\n            print('No missing values found')\n    \n    def create_sample_data(self):\n        \"\"\"Buat sample data jika file tidak ada\"\"\"\n        print('📝 Creating sample data...')\n        \n        np.random.seed(42)\n        data = {\n            'name': [f'Person_{i}' for i in range(100)],\n            'age': np.random.randint(18, 65, 100),\n            'salary': np.random.normal(50000, 15000, 100),\n            'department': np.random.choice(['IT', 'HR', 'Finance', 'Marketing'], 100),\n            'experience': np.random.randint(0, 20, 100),\n            'satisfaction': np.random.randint(1, 6, 100)\n        }\n        \n        df = pd.DataFrame(data)\n        df['salary'] = df['salary'].round(2)\n        df.to_csv('sample_data.csv', index=False)\n        \n        print('✅ Sample data created: sample_data.csv')\n        return 'sample_data.csv'\n    \n    def visualize_data(self):\n        \"\"\"Buat visualisasi data\"\"\"\n        if self.df is None:\n            return\n        \n        # Setup matplotlib untuk Termux\n        plt.style.use('default')\n        fig, axes = plt.subplots(2, 2, figsize=(12, 10))\n        fig.suptitle('Data Analysis Dashboard', fontsize=16)\n        \n        # 1. Histogram untuk kolom numerik pertama\n        numeric_cols = self.df.select_dtypes(include=[np.number]).columns\n        if len(numeric_cols) > 0:\n            col = numeric_cols[0]\n            axes[0, 0].hist(self.df[col], bins=20, alpha=0.7, color='skyblue')\n            axes[0, 0].set_title(f'Distribution of {col}')\n            axes[0, 0].set_xlabel(col)\n            axes[0, 0].set_ylabel('Frequency')\n        \n        # 2. Box plot untuk kolom numerik kedua\n        if len(numeric_cols) > 1:\n            col = numeric_cols[1]\n            axes[0, 1].boxplot(self.df[col])\n            axes[0, 1].set_title(f'Box Plot of {col}')\n            axes[0, 1].set_ylabel(col)\n        \n        # 3. Bar chart untuk kolom kategorikal\n        categorical_cols = self.df.select_dtypes(include=['object']).columns\n        if len(categorical_cols) > 0:\n            col = categorical_cols[0]\n            value_counts = self.df[col].value_counts()\n            axes[1, 0].bar(value_counts.index, value_counts.values, color='lightcoral')\n            axes[1, 0].set_title(f'Count by {col}')\n            axes[1, 0].set_xlabel(col)\n            axes[1, 0].set_ylabel('Count')\n            axes[1, 0].tick_params(axis='x', rotation=45)\n        \n        # 4. Scatter plot jika ada 2+ kolom numerik\n        if len(numeric_cols) >= 2:\n            x_col, y_col = numeric_cols[0], numeric_cols[1]\n            axes[1, 1].scatter(self.df[x_col], self.df[y_col], alpha=0.6, color='green')\n            axes[1, 1].set_title(f'{x_col} vs {y_col}')\n            axes[1, 1].set_xlabel(x_col)\n            axes[1, 1].set_ylabel(y_col)\n        \n        plt.tight_layout()\n        \n        # Simpan plot\n        output_file = 'data_analysis.png'\n        plt.savefig(output_file, dpi=150, bbox_inches='tight')\n        print(f'📊 Visualization saved: {output_file}')\n        \n        # Tampilkan plot (jika display tersedia)\n        try:\n            plt.show()\n        except:\n            print('💡 Plot saved to file (display not available in Termux)')\n    \n    def correlation_analysis(self):\n        \"\"\"Analisis korelasi\"\"\"\n        numeric_df = self.df.select_dtypes(include=[np.number])\n        \n        if len(numeric_df.columns) < 2:\n            print('⚠️ Need at least 2 numeric columns for correlation')\n            return\n        \n        print('\\n🔗 Correlation Matrix:')\n        corr_matrix = numeric_df.corr()\n        print(corr_matrix)\n        \n        # Heatmap korelasi\n        plt.figure(figsize=(10, 8))\n        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)\n        plt.title('Correlation Heatmap')\n        plt.tight_layout()\n        plt.savefig('correlation_heatmap.png', dpi=150, bbox_inches='tight')\n        print('📊 Correlation heatmap saved: correlation_heatmap.png')\n        \n        try:\n            plt.show()\n        except:\n            print('💡 Heatmap saved to file')\n\ndef main():\n    import argparse\n    \n    parser = argparse.ArgumentParser(description='CSV Data Analyzer')\n    parser.add_argument('--file', default='sample_data.csv', help='CSV file to analyze')\n    parser.add_argument('--create-sample', action='store_true', help='Create sample data')\n    \n    args = parser.parse_args()\n    \n    if args.create_sample:\n        analyzer = CSVAnalyzer('')\n        csv_file = analyzer.create_sample_data()\n        args.file = csv_file\n    \n    if not Path(args.file).exists():\n        print(f'❌ File not found: {args.file}')\n        print('💡 Use --create-sample to generate sample data')\n        return\n    \n    # Analisis data\n    analyzer = CSVAnalyzer(args.file)\n    \n    if analyzer.df is not None:\n        analyzer.basic_info()\n        analyzer.visualize_data()\n        analyzer.correlation_analysis()\n        \n        print('\\n✅ Analysis completed!')\n        print('📁 Output files:')\n        print('  - data_analysis.png')\n        print('  - correlation_heatmap.png')\n\nif __name__ == '__main__':\n    main()")

TOOL_CALL: write_file("requirements_analysis.txt", "pandas>=1.5.0\nmatplotlib>=3.5.0\nseaborn>=0.11.0\nnumpy>=1.21.0")

📋 Tool Results:
✅ write_file: Success
✅ write_file: Success

Script analisis data berhasil dibuat! 📊

**Penggunaan:**

```bash
# Install dependencies
pip install -r requirements_analysis.txt

# Buat sample data dan analisis
python data_analyzer.py --create-sample

# Analisis file CSV yang ada
python data_analyzer.py --file your_data.csv
```

**Features:**
- ✅ Load dan analisis CSV data
- ✅ Informasi dasar dataset (shape, types, statistics)
- ✅ Deteksi missing values
- ✅ Visualisasi multi-panel (histogram, boxplot, bar chart, scatter)
- ✅ Analisis korelasi dengan heatmap
- ✅ Generate sample data untuk testing
- ✅ Export visualisasi ke PNG

**Output:**
- `data_analysis.png`: Dashboard visualisasi
- `correlation_heatmap.png`: Heatmap korelasi
- Console output dengan statistik detail

Script siap untuk analisis data di Termux! 📈
```

## 🌐 API Integration

```
👤 Anda: Buatkan script untuk mengecek cuaca menggunakan API

🤖 OpenHands: Saya akan buatkan weather checker menggunakan API.

TOOL_CALL: write_file("weather_checker.py", "#!/usr/bin/env python3\n\"\"\"\nWeather Checker\nScript untuk cek cuaca menggunakan OpenWeatherMap API\n\"\"\"\n\nimport requests\nimport json\nfrom datetime import datetime\nimport os\n\nclass WeatherChecker:\n    def __init__(self, api_key=None):\n        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')\n        self.base_url = 'http://api.openweathermap.org/data/2.5'\n        \n        if not self.api_key:\n            print('⚠️ API key tidak ditemukan!')\n            print('💡 Dapatkan gratis di: https://openweathermap.org/api')\n            print('💡 Set environment: export OPENWEATHER_API_KEY=your_key')\n    \n    def get_current_weather(self, city, units='metric'):\n        \"\"\"Get cuaca saat ini\"\"\"\n        if not self.api_key:\n            return None\n        \n        url = f'{self.base_url}/weather'\n        params = {\n            'q': city,\n            'appid': self.api_key,\n            'units': units\n        }\n        \n        try:\n            response = requests.get(url, params=params)\n            response.raise_for_status()\n            return response.json()\n        except requests.RequestException as e:\n            print(f'❌ Error fetching weather: {e}')\n            return None\n    \n    def get_forecast(self, city, units='metric'):\n        \"\"\"Get forecast 5 hari\"\"\"\n        if not self.api_key:\n            return None\n        \n        url = f'{self.base_url}/forecast'\n        params = {\n            'q': city,\n            'appid': self.api_key,\n            'units': units\n        }\n        \n        try:\n            response = requests.get(url, params=params)\n            response.raise_for_status()\n            return response.json()\n        except requests.RequestException as e:\n            print(f'❌ Error fetching forecast: {e}')\n            return None\n    \n    def format_current_weather(self, data):\n        \"\"\"Format data cuaca saat ini\"\"\"\n        if not data:\n            return\n        \n        city = data['name']\n        country = data['sys']['country']\n        temp = data['main']['temp']\n        feels_like = data['main']['feels_like']\n        humidity = data['main']['humidity']\n        pressure = data['main']['pressure']\n        description = data['weather'][0]['description'].title()\n        wind_speed = data['wind']['speed']\n        \n        sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')\n        sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')\n        \n        print(f'🌍 {city}, {country}')\n        print(f'🌡️ Temperature: {temp}°C (feels like {feels_like}°C)')\n        print(f'☁️ Condition: {description}')\n        print(f'💧 Humidity: {humidity}%')\n        print(f'🌬️ Wind Speed: {wind_speed} m/s')\n        print(f'📊 Pressure: {pressure} hPa')\n        print(f'🌅 Sunrise: {sunrise}')\n        print(f'🌇 Sunset: {sunset}')\n    \n    def format_forecast(self, data):\n        \"\"\"Format data forecast\"\"\"\n        if not data:\n            return\n        \n        print(f'\\n📅 5-Day Forecast for {data[\"city\"][\"name\"]}:')\n        print('=' * 50)\n        \n        # Group by date\n        daily_data = {}\n        for item in data['list']:\n            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')\n            if date not in daily_data:\n                daily_data[date] = []\n            daily_data[date].append(item)\n        \n        for date, forecasts in list(daily_data.items())[:5]:\n            day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')\n            \n            # Ambil data siang hari (sekitar jam 12)\n            midday_forecast = min(forecasts, \n                                key=lambda x: abs(datetime.fromtimestamp(x['dt']).hour - 12))\n            \n            temp = midday_forecast['main']['temp']\n            description = midday_forecast['weather'][0]['description'].title()\n            \n            # Min/max temp untuk hari itu\n            temps = [f['main']['temp'] for f in forecasts]\n            min_temp = min(temps)\n            max_temp = max(temps)\n            \n            print(f'📅 {day_name} ({date})')\n            print(f'   🌡️ {min_temp:.1f}°C - {max_temp:.1f}°C')\n            print(f'   ☁️ {description}')\n            print()\n    \n    def save_weather_data(self, city, current_data, forecast_data):\n        \"\"\"Simpan data cuaca ke file JSON\"\"\"\n        timestamp = datetime.now().isoformat()\n        \n        weather_data = {\n            'timestamp': timestamp,\n            'city': city,\n            'current': current_data,\n            'forecast': forecast_data\n        }\n        \n        filename = f'weather_{city.lower().replace(\" \", \"_\")}_{datetime.now().strftime(\"%Y%m%d\")}.json'\n        \n        with open(filename, 'w') as f:\n            json.dump(weather_data, f, indent=2)\n        \n        print(f'💾 Weather data saved: {filename}')\n\ndef main():\n    import argparse\n    \n    parser = argparse.ArgumentParser(description='Weather Checker')\n    parser.add_argument('city', nargs='?', default='Jakarta', help='City name')\n    parser.add_argument('--api-key', help='OpenWeatherMap API key')\n    parser.add_argument('--forecast', action='store_true', help='Show 5-day forecast')\n    parser.add_argument('--save', action='store_true', help='Save data to JSON file')\n    parser.add_argument('--units', choices=['metric', 'imperial'], default='metric', \n                       help='Temperature units')\n    \n    args = parser.parse_args()\n    \n    # Inisialisasi weather checker\n    weather = WeatherChecker(args.api_key)\n    \n    if not weather.api_key:\n        print('\\n💡 Untuk menggunakan script ini:')\n        print('1. Daftar gratis di https://openweathermap.org/api')\n        print('2. Dapatkan API key')\n        print('3. Set environment: export OPENWEATHER_API_KEY=your_key')\n        print('4. Atau gunakan: python weather_checker.py --api-key your_key Jakarta')\n        return\n    \n    print(f'🌤️ Weather Information for {args.city}')\n    print('=' * 40)\n    \n    # Get current weather\n    current_data = weather.get_current_weather(args.city, args.units)\n    if current_data:\n        weather.format_current_weather(current_data)\n    \n    # Get forecast jika diminta\n    forecast_data = None\n    if args.forecast:\n        forecast_data = weather.get_forecast(args.city, args.units)\n        if forecast_data:\n            weather.format_forecast(forecast_data)\n    \n    # Save data jika diminta\n    if args.save and current_data:\n        weather.save_weather_data(args.city, current_data, forecast_data)\n    \n    print(f'\\n🕐 Last updated: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')\n\nif __name__ == '__main__':\n    main()")

TOOL_CALL: write_file("weather_config.sh", "#!/data/data/com.termux/files/usr/bin/bash\n\n# Weather Checker Configuration\n# Script untuk setup API key\n\necho \"🌤️ Weather Checker Setup\"\necho \"========================\"\n\nif [ -z \"$OPENWEATHER_API_KEY\" ]; then\n    echo \"⚠️ OpenWeatherMap API key belum diset\"\n    echo \"\"\n    echo \"📋 Langkah setup:\"\n    echo \"1. Buka https://openweathermap.org/api\"\n    echo \"2. Daftar akun gratis\"\n    echo \"3. Dapatkan API key\"\n    echo \"4. Jalankan: export OPENWEATHER_API_KEY=your_api_key\"\n    echo \"5. Atau tambahkan ke ~/.bashrc untuk permanent\"\n    echo \"\"\n    read -p \"Masukkan API key sekarang (optional): \" api_key\n    \n    if [ ! -z \"$api_key\" ]; then\n        export OPENWEATHER_API_KEY=\"$api_key\"\n        echo \"export OPENWEATHER_API_KEY=\\\"$api_key\\\"\" >> ~/.bashrc\n        echo \"✅ API key diset dan disimpan ke ~/.bashrc\"\n    fi\nelse\n    echo \"✅ API key sudah diset: ${OPENWEATHER_API_KEY:0:10}...\"\nfi\n\necho \"\"\necho \"📖 Contoh penggunaan:\"\necho \"python weather_checker.py Jakarta\"\necho \"python weather_checker.py --forecast Surabaya\"\necho \"python weather_checker.py --save --forecast 'New York'\"\n\n# Test connection\nif [ ! -z \"$OPENWEATHER_API_KEY\" ]; then\n    echo \"\"\n    echo \"🧪 Testing connection...\"\n    python weather_checker.py Jakarta\nfi")

📋 Tool Results:
✅ write_file: Success
✅ write_file: Success

Weather checker berhasil dibuat! 🌤️

**Setup:**

```bash
# Setup API key
chmod +x weather_config.sh
./weather_config.sh

# Atau manual:
export OPENWEATHER_API_KEY=your_api_key_here
```

**Penggunaan:**

```bash
# Cuaca saat ini
python weather_checker.py Jakarta

# Dengan forecast 5 hari
python weather_checker.py --forecast Surabaya

# Simpan data ke JSON
python weather_checker.py --save --forecast "New York"

# Gunakan Fahrenheit
python weather_checker.py --units imperial Miami
```

**Features:**
- ✅ Cuaca real-time dari OpenWeatherMap API
- ✅ Forecast 5 hari
- ✅ Support metric/imperial units
- ✅ Informasi lengkap (temp, humidity, wind, sunrise/sunset)
- ✅ Export data ke JSON
- ✅ Error handling dan validation
- ✅ Environment variable support

**API Key gratis dari:**
https://openweathermap.org/api

Script siap untuk monitoring cuaca! ⛅
```

## 🔧 System Administration

```
👤 Anda: Buatkan script monitoring sistem Termux

🤖 OpenHands: Saya akan buatkan system monitor untuk Termux.

TOOL_CALL: execute_command("df -h")

TOOL_CALL: execute_command("free -h")

TOOL_CALL: execute_command("uptime")

📋 Tool Results:
✅ execute_command:
```
Filesystem      Size  Used Avail Use% Mounted on
/data           64G   45G   19G  71% /
tmpfs           3.9G     0  3.9G   0% /dev
tmpfs           3.9G     0  3.9G   0% /tmp
```

✅ execute_command:
```
               total        used        free      shared  buff/cache   available
Mem:           7.8Gi       2.1Gi       4.2Gi       156Mi       1.5Gi       5.4Gi
Swap:             0B          0B          0B
```

✅ execute_command:
```
 14:30:25 up 2 days,  3:42,  0 users,  load average: 0.12, 0.08, 0.05
```

Berdasarkan info sistem, saya akan buat monitor yang komprehensif:

TOOL_CALL: write_file("system_monitor.py", "#!/usr/bin/env python3\n\"\"\"\nTermux System Monitor\nScript untuk monitoring sistem Termux\n\"\"\"\n\nimport os\nimport psutil\nimport subprocess\nimport time\nimport json\nfrom datetime import datetime\nfrom pathlib import Path\n\nclass TermuxMonitor:\n    def __init__(self):\n        self.log_dir = Path.home() / '.openhands' / 'logs'\n        self.log_dir.mkdir(parents=True, exist_ok=True)\n    \n    def get_system_info(self):\n        \"\"\"Get informasi sistem dasar\"\"\"\n        try:\n            # CPU info\n            cpu_count = psutil.cpu_count()\n            cpu_percent = psutil.cpu_percent(interval=1)\n            \n            # Memory info\n            memory = psutil.virtual_memory()\n            \n            # Disk info\n            disk = psutil.disk_usage('/')\n            \n            # Network info (jika tersedia)\n            try:\n                network = psutil.net_io_counters()\n                network_info = {\n                    'bytes_sent': network.bytes_sent,\n                    'bytes_recv': network.bytes_recv,\n                    'packets_sent': network.packets_sent,\n                    'packets_recv': network.packets_recv\n                }\n            except:\n                network_info = None\n            \n            # Battery info (Android specific)\n            battery_info = self.get_battery_info()\n            \n            return {\n                'timestamp': datetime.now().isoformat(),\n                'cpu': {\n                    'count': cpu_count,\n                    'percent': cpu_percent\n                },\n                'memory': {\n                    'total': memory.total,\n                    'available': memory.available,\n                    'percent': memory.percent,\n                    'used': memory.used,\n                    'free': memory.free\n                },\n                'disk': {\n                    'total': disk.total,\n                    'used': disk.used,\n                    'free': disk.free,\n                    'percent': (disk.used / disk.total) * 100\n                },\n                'network': network_info,\n                'battery': battery_info\n            }\n        except Exception as e:\n            print(f'❌ Error getting system info: {e}')\n            return None\n    \n    def get_battery_info(self):\n        \"\"\"Get battery info (Android specific)\"\"\"\n        try:\n            # Coba gunakan termux-battery-status jika tersedia\n            result = subprocess.run(['termux-battery-status'], \n                                  capture_output=True, text=True, timeout=5)\n            if result.returncode == 0:\n                return json.loads(result.stdout)\n        except:\n            pass\n        \n        # Fallback: coba baca dari /sys/class/power_supply\n        try:\n            battery_path = Path('/sys/class/power_supply/battery')\n            if battery_path.exists():\n                capacity_file = battery_path / 'capacity'\n                status_file = battery_path / 'status'\n                \n                if capacity_file.exists() and status_file.exists():\n                    capacity = int(capacity_file.read_text().strip())\n                    status = status_file.read_text().strip()\n                    \n                    return {\n                        'percentage': capacity,\n                        'status': status\n                    }\n        except:\n            pass\n        \n        return None\n    \n    def get_process_info(self, top_n=10):\n        \"\"\"Get info proses yang berjalan\"\"\"\n        try:\n            processes = []\n            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):\n                try:\n                    processes.append(proc.info)\n                except (psutil.NoSuchProcess, psutil.AccessDenied):\n                    pass\n            \n            # Sort by CPU usage\n            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)\n            \n            return processes[:top_n]\n        except Exception as e:\n            print(f'❌ Error getting process info: {e}')\n            return []\n    \n    def get_termux_packages(self):\n        \"\"\"Get daftar package Termux yang terinstall\"\"\"\n        try:\n            result = subprocess.run(['pkg', 'list-installed'], \n                                  capture_output=True, text=True, timeout=10)\n            if result.returncode == 0:\n                packages = []\n                for line in result.stdout.strip().split('\\n'):\n                    if line.strip():\n                        packages.append(line.strip())\n                return packages\n        except Exception as e:\n            print(f'⚠️ Could not get package list: {e}')\n        \n        return []\n    \n    def format_bytes(self, bytes_value):\n        \"\"\"Format bytes ke human readable\"\"\"\n        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:\n            if bytes_value < 1024.0:\n                return f'{bytes_value:.1f} {unit}'\n            bytes_value /= 1024.0\n        return f'{bytes_value:.1f} PB'\n    \n    def display_system_info(self, info):\n        \"\"\"Display system info dengan format yang bagus\"\"\"\n        if not info:\n            return\n        \n        print('🖥️ System Information')\n        print('=' * 50)\n        print(f'📅 Timestamp: {info[\"timestamp\"]}')\n        \n        # CPU Info\n        cpu = info['cpu']\n        print(f'\\n🔧 CPU:')\n        print(f'   Cores: {cpu[\"count\"]}')\n        print(f'   Usage: {cpu[\"percent\"]:.1f}%')\n        \n        # Memory Info\n        mem = info['memory']\n        print(f'\\n💾 Memory:')\n        print(f'   Total: {self.format_bytes(mem[\"total\"])}')\n        print(f'   Used: {self.format_bytes(mem[\"used\"])} ({mem[\"percent\"]:.1f}%)')\n        print(f'   Available: {self.format_bytes(mem[\"available\"])}')\n        print(f'   Free: {self.format_bytes(mem[\"free\"])}')\n        \n        # Disk Info\n        disk = info['disk']\n        print(f'\\n💿 Storage:')\n        print(f'   Total: {self.format_bytes(disk[\"total\"])}')\n        print(f'   Used: {self.format_bytes(disk[\"used\"])} ({disk[\"percent\"]:.1f}%)')\n        print(f'   Free: {self.format_bytes(disk[\"free\"])}')\n        \n        # Network Info\n        if info['network']:\n            net = info['network']\n            print(f'\\n🌐 Network:')\n            print(f'   Sent: {self.format_bytes(net[\"bytes_sent\"])}')\n            print(f'   Received: {self.format_bytes(net[\"bytes_recv\"])}')\n            print(f'   Packets Sent: {net[\"packets_sent\"]:,}')\n            print(f'   Packets Received: {net[\"packets_recv\"]:,}')\n        \n        # Battery Info\n        if info['battery']:\n            battery = info['battery']\n            print(f'\\n🔋 Battery:')\n            if 'percentage' in battery:\n                print(f'   Level: {battery[\"percentage\"]}%')\n            if 'status' in battery:\n                print(f'   Status: {battery[\"status\"]}')\n    \n    def display_process_info(self, processes):\n        \"\"\"Display process info\"\"\"\n        if not processes:\n            return\n        \n        print(f'\\n🔄 Top Processes:')\n        print('-' * 60)\n        print(f'{'PID':<8} {'Name':<20} {'CPU%':<8} {'Memory%':<8}')\n        print('-' * 60)\n        \n        for proc in processes:\n            pid = proc['pid']\n            name = (proc['name'] or 'Unknown')[:19]\n            cpu = proc['cpu_percent'] or 0\n            mem = proc['memory_percent'] or 0\n            \n            print(f'{pid:<8} {name:<20} {cpu:<8.1f} {mem:<8.1f}')\n    \n    def save_log(self, info, processes):\n        \"\"\"Simpan log monitoring\"\"\"\n        log_data = {\n            'system': info,\n            'processes': processes\n        }\n        \n        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n        log_file = self.log_dir / f'system_monitor_{timestamp}.json'\n        \n        with open(log_file, 'w') as f:\n            json.dump(log_data, f, indent=2)\n        \n        print(f'\\n💾 Log saved: {log_file}')\n    \n    def continuous_monitor(self, interval=5, duration=60):\n        \"\"\"Monitor kontinyu\"\"\"\n        print(f'🔄 Starting continuous monitoring...')\n        print(f'   Interval: {interval} seconds')\n        print(f'   Duration: {duration} seconds')\n        print('   Press Ctrl+C to stop\\n')\n        \n        start_time = time.time()\n        \n        try:\n            while True:\n                current_time = time.time()\n                if current_time - start_time > duration:\n                    break\n                \n                # Clear screen\n                os.system('clear')\n                \n                # Get dan display info\n                info = self.get_system_info()\n                if info:\n                    self.display_system_info(info)\n                \n                processes = self.get_process_info(5)\n                self.display_process_info(processes)\n                \n                print(f'\\n⏱️ Monitoring... ({int(current_time - start_time)}/{duration}s)')\n                print('Press Ctrl+C to stop')\n                \n                time.sleep(interval)\n                \n        except KeyboardInterrupt:\n            print('\\n🛑 Monitoring stopped by user')\n    \n    def system_health_check(self):\n        \"\"\"Health check sistem\"\"\"\n        print('🏥 System Health Check')\n        print('=' * 30)\n        \n        info = self.get_system_info()\n        if not info:\n            print('❌ Could not get system info')\n            return\n        \n        issues = []\n        warnings = []\n        \n        # Check CPU usage\n        if info['cpu']['percent'] > 80:\n            issues.append(f'High CPU usage: {info[\"cpu\"][\"percent\"]:.1f}%')\n        elif info['cpu']['percent'] > 60:\n            warnings.append(f'Moderate CPU usage: {info[\"cpu\"][\"percent\"]:.1f}%')\n        \n        # Check memory usage\n        if info['memory']['percent'] > 90:\n            issues.append(f'High memory usage: {info[\"memory\"][\"percent\"]:.1f}%')\n        elif info['memory']['percent'] > 75:\n            warnings.append(f'Moderate memory usage: {info[\"memory\"][\"percent\"]:.1f}%')\n        \n        # Check disk usage\n        if info['disk']['percent'] > 95:\n            issues.append(f'Very low disk space: {info[\"disk\"][\"percent\"]:.1f}% used')\n        elif info['disk']['percent'] > 85:\n            warnings.append(f'Low disk space: {info[\"disk\"][\"percent\"]:.1f}% used')\n        \n        # Check battery (if available)\n        if info['battery'] and 'percentage' in info['battery']:\n            battery_level = info['battery']['percentage']\n            if battery_level < 10:\n                issues.append(f'Very low battery: {battery_level}%')\n            elif battery_level < 20:\n                warnings.append(f'Low battery: {battery_level}%')\n        \n        # Display results\n        if not issues and not warnings:\n            print('✅ System health: GOOD')\n            print('   No issues detected')\n        else:\n            if issues:\n                print('❌ Critical Issues:')\n                for issue in issues:\n                    print(f'   - {issue}')\n            \n            if warnings:\n                print('⚠️ Warnings:')\n                for warning in warnings:\n                    print(f'   - {warning}')\n        \n        return len(issues) == 0\n\ndef main():\n    import argparse\n    \n    parser = argparse.ArgumentParser(description='Termux System Monitor')\n    parser.add_argument('--continuous', '-c', action='store_true', \n                       help='Continuous monitoring mode')\n    parser.add_argument('--interval', '-i', type=int, default=5,\n                       help='Monitoring interval in seconds (default: 5)')\n    parser.add_argument('--duration', '-d', type=int, default=60,\n                       help='Monitoring duration in seconds (default: 60)')\n    parser.add_argument('--processes', '-p', type=int, default=10,\n                       help='Number of top processes to show (default: 10)')\n    parser.add_argument('--save', '-s', action='store_true',\n                       help='Save monitoring data to log file')\n    parser.add_argument('--health', action='store_true',\n                       help='Perform system health check')\n    parser.add_argument('--packages', action='store_true',\n                       help='Show installed packages')\n    \n    args = parser.parse_args()\n    \n    monitor = TermuxMonitor()\n    \n    if args.health:\n        monitor.system_health_check()\n        return\n    \n    if args.packages:\n        print('📦 Installed Packages:')\n        packages = monitor.get_termux_packages()\n        if packages:\n            for i, pkg in enumerate(packages[:20], 1):\n                print(f'   {i:2d}. {pkg}')\n            if len(packages) > 20:\n                print(f'   ... and {len(packages) - 20} more packages')\n        else:\n            print('   Could not retrieve package list')\n        return\n    \n    if args.continuous:\n        monitor.continuous_monitor(args.interval, args.duration)\n    else:\n        # Single snapshot\n        info = monitor.get_system_info()\n        if info:\n            monitor.display_system_info(info)\n        \n        processes = monitor.get_process_info(args.processes)\n        monitor.display_process_info(processes)\n        \n        if args.save:\n            monitor.save_log(info, processes)\n\nif __name__ == '__main__':\n    main()")

📋 Tool Results:
✅ write_file: Success

System monitor untuk Termux berhasil dibuat! 🖥️

**Penggunaan:**

```bash
# Install dependency
pip install psutil

# Monitor snapshot sekali
python system_monitor.py

# Monitor kontinyu 5 menit
python system_monitor.py --continuous --duration 300

# Health check sistem
python system_monitor.py --health

# Lihat packages terinstall
python system_monitor.py --packages

# Monitor dengan save log
python system_monitor.py --save --processes 15
```

**Features:**
- ✅ **System Info**: CPU, Memory, Disk, Network usage
- ✅ **Process Monitor**: Top processes by CPU usage
- ✅ **Battery Info**: Level dan status (jika tersedia)
- ✅ **Health Check**: Deteksi masalah sistem
- ✅ **Continuous Mode**: Monitor real-time
- ✅ **Package List**: Daftar package Termux
- ✅ **Data Logging**: Export ke JSON
- ✅ **Human Readable**: Format yang mudah dibaca

**Contoh Output:**
```
🖥️ System Information
==================================================
📅 Timestamp: 2024-12-12T14:30:25

🔧 CPU:
   Cores: 8
   Usage: 12.5%

💾 Memory:
   Total: 7.8 GB
   Used: 2.1 GB (26.9%)
   Available: 5.4 GB
   Free: 4.2 GB

💿 Storage:
   Total: 64.0 GB
   Used: 45.0 GB (70.3%)
   Free: 19.0 GB

🔋 Battery:
   Level: 85%
   Status: Charging
```

Script siap untuk monitoring sistem Termux! 📊
```

Sekarang saya akan membuat file executable dan dokumentasi final:

<function_calls>
<invoke name="execute_bash">
<parameter name="command">cd /workspace/OpenHands && chmod +x termux_setup.sh termux_cli.py install_termux.py test_termux.py