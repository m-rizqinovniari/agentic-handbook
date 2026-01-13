# Setup Instructions

## Quick Start

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Azure OpenAI credentials:
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.2-chat
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   BING_SEARCH_API_KEY=your_bing_key_here
   ENCODER_API_TYPE=azure
   ```

3. **Create input file:**
   Edit `input/topic_input.json`:
   ```json
   {
     "topik": "Machine Learning",
     "bahasa": "id",
     "audience": "beginner"
   }
   ```

4. **Run the pipeline:**
   ```bash
   python main.py --input input/topic_input.json
   ```

5. **Preview Docusaurus (optional):**
   ```bash
   cd docusaurus
   npm install
   npm start
   ```

## Troubleshooting

### STORM Import Errors

If you encounter import errors with `knowledge_storm`, make sure:
- You have installed the package: `pip install knowledge-storm`
- The package version is compatible (>=1.1.0)
- Check the [STORM GitHub repository](https://github.com/stanford-oval/storm) for the latest installation instructions

### Azure OpenAI Configuration

Ensure all required environment variables are set in `.env`:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_VERSION`

### Bing Search API

For STORM to work properly, you need a Bing Search API key:
1. Get a key from [Azure Portal](https://portal.azure.com/)
2. Add it to `.env` as `BING_SEARCH_API_KEY`

### Docusaurus Setup

If Docusaurus preview doesn't work:
- Make sure Node.js 18+ is installed
- Run `npm install` in the `docusaurus` directory
- Check that all markdown files are properly generated in `docusaurus/docs/`

