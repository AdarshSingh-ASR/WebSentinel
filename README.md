# WebSentinel - AI-Powered Web Testing Platform

[![Demo Video](https://img.shields.io/badge/Demo-Watch%20Video-blue?style=for-the-badge)](https://youtu.be/sE3TGDDeI4Q)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=for-the-badge)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-blue.svg?style=for-the-badge)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg?style=for-the-badge)](https://fastapi.tiangolo.com)

> **🏆 Built for AgentHack 2025** - A powerful web-based platform for automated website testing that combines browser automation with AI analysis, featuring real-time execution monitoring and comprehensive results visualization.

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage Guide](#-usage-guide)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## 🎯 Overview

WebSentinel is a comprehensive web testing platform that leverages AI to automate website testing and analysis. It combines the power of browser automation with intelligent AI agents to provide detailed insights into web application behavior.

### Key Capabilities

- 🤖 **AI-Powered Testing**: Intelligent agents that can understand and interact with web pages
- 📸 **Smart Screenshot Capture**: Automated visual documentation of test execution
- 📊 **Real-Time Monitoring**: Live status updates and execution progress tracking
- 🧠 **Agent Reasoning**: Transparent view into AI decision-making processes
- 📱 **Modern Web Interface**: Beautiful, responsive frontend for test management
- 🔄 **Comprehensive Analysis**: Detailed reports with actionable insights

## ✨ Features

### Core Functionality
- **Automated Web Testing**: Navigate, interact, and validate web applications
- **AI Agent Intelligence**: Powered by Gemini 2.0 Flash for intelligent decision-making
- **Real-Time Execution**: Live monitoring of test progress and agent actions
- **Visual Documentation**: Automatic screenshot capture at key moments
- **Comprehensive Logging**: Detailed execution logs and agent thoughts

### User Interface
- **Modern React Frontend**: Clean, intuitive interface with real-time updates
- **Execution Dashboard**: Visual representation of test progress and results
- **Screenshot Gallery**: Interactive view of captured screenshots
- **Results Analysis**: AI-powered analysis of test results
- **Responsive Design**: Works seamlessly on desktop and mobile devices

### Advanced Capabilities
- **Extracted Content Display**: Shows data extracted during test execution
- **Execution Steps Timeline**: Detailed view of all actions performed
- **Error Handling**: Robust error detection and reporting
- **Log Management**: Organized storage and access to execution logs
- **API Integration**: RESTful API for programmatic access

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI Backend │    │   Browser Agent  │
│                 │    │                 │    │                 │
│ • Test Config   │◄──►│ • API Endpoints │◄──►│ • Web Automation│
│ • Results View  │    │ • Task Management│    │ • AI Reasoning  │
│ • Real-time UI  │    │ • File Serving   │    │ • Screenshots   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, Python 3.8+, Uvicorn
- **Browser Automation**: Browser Use + Playwright
- **AI Integration**: Google Gemini 2.0 Flash
- **Real-time Updates**: Polling-based status monitoring

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** and **Node.js 16+**
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))
- **Chrome/Chromium browser**

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd WebSentinel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. Configure Environment

```bash
# Create environment file
cp .env.example .env

# Edit .env and add your API key
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
```

### 3. Start the Platform

```bash
# Terminal 1: Start backend
python api_server.py

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 4. Access the Platform

Open your browser and navigate to `http://localhost:3000`

## 📦 Installation

### Detailed Setup Instructions

#### Backend Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or install manually
pip install fastapi uvicorn browser-use python-dotenv
pip install portia-sdk-python[google]
```

#### Frontend Dependencies

```bash
cd frontend

# Install Node.js dependencies
npm install

# Available scripts
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
```

#### Environment Configuration

Create a `.env` file in the root directory:

```env
# Required
GEMINI_API_KEY=your_google_gemini_api_key_here

# Optional
PORT=8000
HOST=0.0.0.0
DEBUG=true
```

## 📖 Usage Guide

### Creating Your First Test

1. **Configure Test Parameters**
   - **Target URL**: The website you want to test
   - **Task Description**: What the AI agent should accomplish
   - **Screenshot Instructions**: Specific moments to capture (optional)

2. **Execute the Test**
   - Click "Execute Test" to start automation
   - Monitor real-time progress in the dashboard
   - Watch agent reasoning and decision-making

3. **Review Results**
   - **Execution Steps**: Timeline of all actions performed
   - **Screenshots**: Visual documentation of key moments
   - **Extracted Content**: Data found during execution
   - **Analysis**: AI-powered insights and recommendations

### Example Test Scenarios

#### E-commerce Testing
```json
{
  "target_url": "https://shop.example.com",
  "task_description": "Search for 'wireless headphones', view the first product, and add it to cart",
  "screenshot_instructions": [
    {
      "step_description": "Search results page",
      "filename": "search_results.png"
    },
    {
      "step_description": "Product page",
      "filename": "product_page.png"
    },
    {
      "step_description": "Cart confirmation",
      "filename": "cart_confirmation.png"
    }
  ]
}
```

#### Form Testing
```json
{
  "target_url": "https://forms.example.com/contact",
  "task_description": "Fill out the contact form with test data and submit",
  "screenshot_instructions": [
    {
      "step_description": "Empty form",
      "filename": "empty_form.png"
    },
    {
      "step_description": "Completed form",
      "filename": "filled_form.png"
    }
  ]
}
```

#### Content Extraction
```json
{
  "target_url": "https://news.example.com",
  "task_description": "Extract the headlines from the main page",
  "screenshot_instructions": [
    {
      "step_description": "Main page",
      "filename": "main_page.png"
    }
  ]
}
```

### Understanding Results

#### Execution Dashboard
- **Status Overview**: Success/failure indicators
- **Step Count**: Number of actions performed
- **Screenshot Count**: Visual documentation captured
- **Extracted Content**: Data found during execution

#### Execution Steps
Each step shows:
- **Action**: What was performed
- **Result**: Outcome of the action
- **Timestamp**: When it occurred
- **Screenshot**: Visual evidence (if available)

#### Extracted Content
- **Data Type**: Category of extracted information
- **Content**: Actual data found
- **Step**: When it was extracted
- **Success Status**: Whether extraction succeeded

## 🔌 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/execute-test` | POST | Start a new test execution |
| `/task-status/{task_id}` | GET | Get execution status |
| `/task-results/{task_id}` | GET | Get execution results |
| `/analyze-results/{task_id}` | POST | Run AI analysis |
| `/screenshots/{filename}` | GET | Serve screenshot files |
| `/health` | GET | Health check |

### Request/Response Examples

#### Start Test Execution
```bash
curl -X POST "http://localhost:8000/execute-test" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://example.com",
    "task_description": "Search for products",
    "screenshot_instructions": []
  }'
```

#### Get Task Status
```bash
curl "http://localhost:8000/task-status/task_123"
```

#### Get Task Results
```bash
curl "http://localhost:8000/task-results/task_123"
```

## ⚙️ Configuration

### Browser Settings

Modify browser configuration in `api_server.py`:

```python
browser_config = BrowserConfig(
    headless=False,  # Set to True for headless mode
    disable_security=True,
    keep_alive=True,
    extra_browser_args=[
        "--disable-blink-features=AutomationControlled",
        "--window-size=1920,1080"
    ]
)
```

### Agent Instructions

The AI agent receives detailed instructions including:
- Navigation objectives
- Custom logging functions
- Screenshot capture capabilities
- Data extraction requirements

### Frontend Configuration

Modify frontend settings in `frontend/vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check if port 8000 is available
lsof -i :8000

# Kill any existing process
kill -9 [PID]

# Check Python environment
python --version
pip list
```

#### Frontend Connection Errors
- Ensure backend is running on `http://localhost:8000`
- Check browser console for CORS errors
- Verify API endpoints are accessible
- Check network connectivity

#### No Screenshots Captured
- Browser automation may be blocked by the website
- Try setting `headless=False` for debugging
- Check browser console for errors
- Verify Chrome/Chromium is installed

#### Agent Thoughts Not Displaying
- Check if `agent_thoughts_[task_id].txt` file is created
- Verify `/agent-thoughts/{task_id}` endpoint is accessible
- Look for errors in browser console
- Check file permissions in `operation_logs/`

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set environment variable
export DEBUG=true

# Or modify .env file
DEBUG=true
```

### Log Files

Check these files for detailed error information:

```
operation_logs/
├── detailed_agent_log_[task].txt   # Comprehensive execution log
├── agent_thoughts_[task].txt       # Agent reasoning & decisions
├── agent_stdout_[task].txt         # Agent output capture
├── browser_execution_[task].json   # Detailed execution results
└── review_report_[task].json       # AI analysis report
```

## 📁 Project Structure

```
WebSentinel/
├── api_server.py              # FastAPI backend server
├── website_testing_agent.py   # Core agent logic
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables
├── operation_logs/           # Generated logs and screenshots
│   ├── screenshots/          # Captured screenshots
│   ├── *.txt                # Log files
│   └── *.json               # Execution results
└── frontend/                 # React frontend
    ├── src/
    │   ├── App.tsx          # Main application component
    │   ├── components/      # React components
    │   ├── types/           # TypeScript type definitions
    │   └── lib/             # Utility functions
    ├── package.json         # Node.js dependencies
    └── vite.config.ts       # Vite configuration
```

## 🔒 Security Considerations

- Store API keys securely in `.env` file (never commit to version control)
- Frontend runs on localhost - configure CORS for production deployment
- Screenshots may contain sensitive data - handle appropriately
- Browser automation detection is disabled for testing purposes
- Consider rate limiting for production use

## 📈 System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Node.js**: 16.0 or higher
- **RAM**: 4GB minimum
- **Storage**: 1GB for logs and screenshots
- **Browser**: Chrome/Chromium for automation

### Recommended Requirements
- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher
- **RAM**: 8GB or higher
- **Storage**: 5GB for extensive testing
- **CPU**: Multi-core processor

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests if applicable
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/WebSentinel.git
cd WebSentinel

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Setup frontend
cd frontend
npm install
npm run dev
```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **TypeScript**: Use strict mode and proper typing
- **React**: Follow functional component patterns
- **Commits**: Use conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Portia AI** for the powerful agent framework
- **Google Gemini** for AI capabilities
- **Browser Use** for web automation
- **FastAPI** for the robust backend
- **React** for the modern frontend

## 📞 Support

### Getting Help

1. **Check the troubleshooting section** above
2. **Review log files** in `operation_logs/`
3. **Ensure all dependencies** are installed correctly
4. **Verify your `.env` file** has a valid Gemini API key

### Community

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check the docs for detailed guides

---

**🏆 Enjoy automated website testing with AI-powered insights!**

WebSentinel combines the power of modern web development with intelligent AI agents to create a comprehensive, user-friendly testing solution.

**Built for AgentHack 2025** - Demonstrating the future of AI-powered web automation and testing.
