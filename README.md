# Policy Compliance System

A comprehensive system for processing policy documents, generating compliance questions, and performing automated compliance checks using vector databases and AI.

## 🚀 Features

- **Document Processing**: Upload and process .docx policy documents
- **Structured Extraction**: Extract structured sections from policy documents
- **Vector Storage**: Store policy data in Milvus vector database for semantic search
- **Question Generation**: Automatically generate compliance questions from policies
- **Compliance Checking**: Compare vendor policies against bank policies for compliance
- **Web Interface**: User-friendly web interface for all operations

## 🏗️ Architecture

The system consists of several key components:

- **Frontend**: HTML/CSS/JavaScript web interface
- **Backend**: FastAPI-based REST API
- **Document Processing**: Python modules for extracting and structuring policy content
- **Vector Database**: Milvus for storing and querying policy embeddings
- **AI Integration**: Question generation and compliance analysis

## 📋 Prerequisites

- Python 3.8+
- Node.js (for frontend development, if needed)
- Milvus vector database
- Required Python packages (see requirements.txt)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd policy-compliance-system
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Milvus**
   - Install and start Milvus server
   - Configure connection settings in your environment

4. **Create data directory**
   ```bash
   mkdir -p frontend/data
   ```

5. **Install uvicorn (if not already installed)**
   ```bash
   pip install uvicorn
   ```

## 🛠️ Quick Start

Once you have completed the installation steps:

1. **Start the backend server** (in one terminal):
   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the frontend server** (in another terminal):
   ```bash
   cd frontend
   python -m http.server 5500
   ```

3. **Access the application**:
   - Frontend: http://localhost:5500
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🚀 Usage

### Starting the Backend Server

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API server will start on `http://localhost:8000` with auto-reload enabled for development.

### Starting the Frontend Server

```bash
cd frontend
python -m http.server 5500
```

The frontend will be available at `http://localhost:5500`

### Alternative: Direct File Access

You can also open `frontend/index.html` directly in your web browser, though using the HTTP server is recommended for proper CORS handling.

### API Endpoints

- `POST /upload-policy/` - Upload and process policy documents
- `GET /list-json-files/` - List all processed JSON files
- `POST /generate-questions/` - Generate compliance questions
- `GET /compliance-results/` - Get compliance check results
- `GET /get-file-content/` - Retrieve file content

## 📁 Project Structure

```
policy-compliance-system/
├── frontend/
│   ├── index.html          # Main web interface
│   ├── styles.css          # Styling (not provided)
│   ├── scripts.js          # Frontend JavaScript (not provided)
│   └── data/               # Processed JSON files
├── backend/
│   ├── main.py             # FastAPI application
│   ├── extract_sections.py # Document processing (not provided)
│   ├── check_compliance.py # Compliance checking (not provided)
│   ├── store_milvus.py     # Milvus operations (not provided)
│   └── generate_questions.py # Question generation (not provided)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
API_HOST=localhost
API_PORT=8000
```

### CORS Settings

The API is configured to allow all origins for development. Update the CORS settings in `main.py` for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://your-frontend-domain.com"],  # Update this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📝 How It Works

1. **Upload Policies**: Upload bank and vendor policy documents (.docx format)
2. **Processing**: The system extracts structured sections from documents
3. **Storage**: Policy data is stored in Milvus vector database for semantic search
4. **Question Generation**: AI generates relevant compliance questions from bank policies
5. **Compliance Check**: System compares vendor policies against bank policies
6. **Results**: View compliance results and generated questions through the web interface

## 🔍 API Documentation

### Upload Policy Document

```http
POST /upload-policy/
Content-Type: multipart/form-data

Parameters:
- file: .docx policy document
- is_bank: boolean (true for bank policy, false for vendor policy)
```

### Generate Questions

```http
POST /generate-questions/
Content-Type: application/json

{
  "json_file": "policy_name.json"
}
```

### Get Compliance Results

```http
GET /compliance-results/
```

## 🐛 Troubleshooting

### Common Issues

1. **File Upload Errors**
   - Ensure uploaded files are in .docx format
   - Check file permissions in the data directory

2. **Milvus Connection Issues**
   - Verify Milvus server is running
   - Check connection configuration

3. **Question Generation Failures**
   - Ensure the policy JSON file exists
   - Check AI service availability and configuration
