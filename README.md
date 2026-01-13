# Agentic Learning Material Generator

Sistem AI untuk generate materi pembelajaran secara otomatis menggunakan STORM dari Stanford.

## Fitur

- **Structure Agent**: Menyusun struktur materi dengan pembagian part dan chapter
- **Content Agent**: Generate konten mendalam menggunakan STORM (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking)
- **Docusaurus Integration**: Konversi otomatis ke format Docusaurus untuk dokumentasi yang mudah dibaca
- **Multi-language Support**: Support untuk berbagai bahasa (Indonesia, English, dll)
- **Audience Customization**: Generate materi sesuai level audience (beginner, intermediate, advanced)

## Prerequisites

- Python 3.9+
- Node.js 18+ (untuk preview Docusaurus)
- Azure OpenAI account dengan deployment
- Bing Search API key (untuk STORM retrieval)

## Installation

1. Clone repository:
```bash
git clone <repository-url>
cd course-agentic
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment variables:
```bash
cp .env.example .env
```

Edit `.env` file dengan konfigurasi Azure OpenAI Anda:
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.2-chat
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
BING_SEARCH_API_KEY=your_bing_key_here
ENCODER_API_TYPE=azure
```

4. Install Docusaurus dependencies (optional, untuk preview):
```bash
cd docusaurus
npm install
cd ..
```

## Usage

1. Buat file input JSON di `input/topic_input.json`:
```json
{
  "topik": "Machine Learning",
  "bahasa": "id",
  "audience": "beginner"
}
```

2. Run pipeline:
```bash
python main.py --input input/topic_input.json
```

3. Preview Docusaurus site (optional):
```bash
cd docusaurus
npm start
```

## Input Format

File JSON input harus memiliki struktur berikut:

```json
{
  "topik": "Machine Learning",
  "bahasa": "id",
  "audience": "beginner"
}
```

**Field descriptions:**
- `topik`: Topik utama materi yang akan di-generate (string)
- `bahasa`: Kode bahasa untuk output (contoh: "id" untuk Indonesia, "en" untuk English)
- `audience`: Target audience (contoh: "beginner", "intermediate", "advanced")

## Output Structure

Pipeline akan menghasilkan:

```
output/
├── outline.json              # Struktur outline yang di-generate
├── summary.json              # Summary dari hasil generation
└── content/
    ├── part-1/
    │   ├── chapter-1.md
    │   ├── chapter-2.md
    │   └── ...
    └── part-2/
        └── ...

docusaurus/
└── docs/
    ├── part-1/
    │   ├── _category_.json
    │   ├── chapter-1.md
    │   └── ...
    └── part-2/
        └── ...
```

## Command Line Options

```bash
python main.py --input <input_file> [OPTIONS]

Options:
  --input PATH          Path to input JSON file (required)
  --output PATH         Output directory (default: output)
  --docusaurus PATH     Docusaurus directory (default: docusaurus)
  --retriever METHOD    Retrieval method: bing or wiki (default: bing)
  --quiet               Suppress progress messages
```

## Architecture

Sistem terdiri dari:

1. **Input Handler**: Membaca dan validasi input JSON
2. **Structure Agent**: Generate outline dengan part/chapter structure menggunakan Azure OpenAI
3. **Content Agent**: Generate konten per chapter menggunakan STORM
4. **Orchestrator**: Mengkoordinasikan Structure Agent dan Content Agent
5. **Docusaurus Converter**: Mengorganisir file ke struktur Docusaurus

## License

MIT

