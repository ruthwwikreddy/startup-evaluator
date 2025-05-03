# Startup Idea Evaluator

A powerful AI-driven tool that evaluates startup ideas using multiple specialized AI models to provide comprehensive analysis and insights.

## 📋 Overview

The Startup Idea Evaluator is a toolkit that helps entrepreneurs assess the viability of their business ideas by analyzing multiple dimensions:

- 🔍 **SWOT Analysis**: Strengths, Weaknesses, Opportunities, and Threats of your idea
- 💰 **Revenue Models**: Potential monetization strategies 
- 🖥️ **Technical Stack**: Recommended technologies for implementation
- 👥 **Target Audience**: Detailed audience analysis and segmentation
- ✅ **Validation Strategy**: Practical steps to validate your concept

The application uses Ollama's local AI models (optimized for different aspects of analysis) to provide comprehensive evaluations without requiring network connectivity or sending your data to external services.

## 🚀 Features

- **Multi-model Analysis**: Uses specialized models for different aspects of evaluation
- **Parallel Processing**: Processes multiple analyses concurrently for faster results
- **Input Flexibility**: Accept startup ideas via direct text input or document upload (.txt, .docx)
- **Progress Tracking**: Real-time progress indicators for each step
- **Multiple Export Options**: Save results as JSON or formatted PDF
- **Modern UI**: User-friendly interface with responsive design
- **Detailed Timing**: Performance tracking for each analysis component

## 📦 Prerequisites

- Python 3.8+ 
- [Ollama](https://ollama.ai/) installed and running with the following models:
  - `phi` (for SWOT, Target Audience, and Validation Strategy analyses)
  - `llama2:7b` (for Revenue Models analysis)
  - `mistral:7b` (for Technical Stack analysis)
- Required Python packages:
  - `ollama` - For AI model interactions
  - `python-docx` - For DOCX file processing
  - `reportlab` - For PDF generation
  - Additional dependencies in `requirements.txt`

## ⚙️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/startup-idea-evaluator.git
   cd startup-idea-evaluator
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Ollama is installed and running:
   ```bash
   # Check if Ollama is installed
   ollama --version

   # Pull required models if not already available
   ollama pull phi
   ollama pull llama2:7b
   ollama pull mistral:7b
   ```

4. Place the HTML frontend file in a `static` folder:
   ```bash
   mkdir -p static
   # Copy the startup_evaluator.html file to the static folder
   ```

## 🖥️ Usage

### Command Line Interface

Run the evaluator from the command line:

```bash
python startup_evaluator.py
```

Follow the interactive prompts to:
1. Input your startup idea (directly or via file)
2. Review and confirm to start the evaluation
3. View real-time progress as each analysis runs
4. Review comprehensive results
5. Optionally save results as JSON or PDF

### Web Interface

1. Place the HTML file in your web server's static directory
2. Set up appropriate routes in your web framework to connect the HTML frontend with the Python backend
3. Access via browser and use the intuitive UI to evaluate your startup ideas


## 🔄 Customization

You can customize the evaluator by modifying these parameters:

- **Models**: Change which AI models are used for specific analyses in the `__init__` method
- **Prompts**: Adjust evaluation criteria by modifying the prompts in `build_prompts` method
- **Temperature**: Control creativity vs. determinism by adjusting temperature settings


## 🧠 AI Models

The evaluator uses these Ollama models with specific roles:

| Analysis Type | Model | Reasoning |
|---------------|-------|-----------|
| SWOT | phi | Efficient for structured analysis |
| Revenue Models | llama2:7b | Strong business reasoning capabilities |
| Technical Stack | mistral:7b | Excellent technical knowledge |
| Target Audience | phi | Good for demographic analysis |
| Validation | phi | Efficient for practical recommendations |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for providing the local AI models
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [python-docx](https://python-docx.readthedocs.io/) for DOCX processing
