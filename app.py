import os
import logging
import ollama
import docx
import concurrent.futures
import time
import json
import reportlab
import threading
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from flask import Flask, render_template, request, jsonify, send_file
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    try:
        # Get idea text from form
        idea_text = request.form.get('idea_text', '')
        if not idea_text:
            return jsonify({'error': 'No idea text provided'}), 400

        # Initialize evaluator
        evaluator = StartupIdeaEvaluator(verbose=False)
        
        # Run evaluation
        results = evaluator.evaluate_idea(idea_text)
        
        return jsonify({
            'success': True,
            'results': results,
            'timing_data': evaluator.timing_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save', methods=['POST'])
def save():
    temp_path = None
    try:
        data = request.json
        idea_text = data.get('idea_text', '')
        results = data.get('results', {})
        format = data.get('format', 'pdf')
        
        if not idea_text or not results:
            return jsonify({'error': 'Missing required data'}), 400
            
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as temp_file:
            temp_path = temp_file.name
            
        # Save results
        evaluator = StartupIdeaEvaluator(verbose=False)
        saved_file = evaluator.save_results(idea_text, results, temp_path, format)
        
        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f'startup_evaluation_{timestamp}.{format}'
        
        # Send file and ensure it's deleted after sending
        response = send_file(
            saved_file,
            as_attachment=True,
            download_name=filename,
            mimetype=f'application/{format}'
        )
        
        # Clean up the temporary file after sending
        @response.call_on_close
        def cleanup():
            try:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {str(e)}")
        
        return response
        
    except Exception as e:
        # Clean up temporary file in case of error
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temporary file after error: {str(cleanup_error)}")
        return jsonify({'error': str(e)}), 500

class ProgressTracker:
    """Track and display progress for long-running operations"""
    def __init__(self, label="Processing"):
        self.label = label
        self.start_time = None
        self.is_running = False
        self.thread = None
    
    def start(self):
        """Start tracking progress"""
        self.start_time = time.time()
        self.is_running = True
        self.thread = threading.Thread(target=self._progress_display)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop tracking progress"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"\r{self.label} completed in {elapsed:.2f} seconds.{' ' * 20}")
    
    def _progress_display(self):
        """Display progress updates"""
        while self.is_running:
            elapsed = time.time() - self.start_time
            sys.stdout.write(f"\r{self.label} - {elapsed:.1f} sec elapsed...{' ' * 20}")
            sys.stdout.flush()
            time.sleep(1.0)

class StartupIdeaEvaluator:
    def __init__(self, verbose=True):
        """Initialize the startup idea evaluator with optimal models"""
        # Using smaller/faster models where appropriate while keeping powerful ones for complex tasks
        self.models = {
            "swot": "phi",           # Smaller but effective model for structured analysis
            "revenue": "llama2:7b",  # Good at business reasoning
            "tech": "mistral:7b",    # Strong technical understanding
            "audience": "phi",       # Efficient for demographics analysis
            "validation": "phi"      # Fast model for practical steps
        }
        self.verbose = verbose
        self.timing_data = {}
        logger.info("Startup Idea Evaluator initialized with optimized models")
        
        # Verify Ollama is available and models are installed
        try:
            if self.verbose:
                print("Verifying Ollama availability...")
            ollama.list()
            if self.verbose:
                print("✓ Ollama is running")
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {str(e)}")
            print(f"ERROR: Could not connect to Ollama. Please ensure Ollama is running.\n{str(e)}")
            sys.exit(1)
    
    def query_model(self, model, prompt, temperature=0.7, timeout=60):
        """Query an Ollama model with timeout and tracking"""
        try:
            category = None
            for cat, mod in self.models.items():
                if mod == model:
                    category = cat
                    break
            
            progress = ProgressTracker(f"Generating {category} analysis" if category else f"Querying {model}")
            progress.start()
            
            start_time = time.time()
            response = ollama.chat(
                model=model, 
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": temperature,
                    "num_predict": 1024  # Limit token generation for faster responses
                }
            )
            elapsed = time.time() - start_time
            
            progress.stop()
            
            if category:
                self.timing_data[category] = elapsed
                logger.info(f"Response from {model} for {category} received in {elapsed:.2f} seconds")
            else:
                logger.info(f"Response from {model} received in {elapsed:.2f} seconds")
                
            return response['message']['content']
            
        except Exception as e:
            if 'progress' in locals():
                progress.stop()
            logger.error(f"Error querying {model}: {str(e)}")
            return f"Error processing with {model}: {str(e)}"
    
    def extract_text_from_docx(self, file_path):
        """Extract text from .docx file"""
        progress = ProgressTracker("Reading DOCX file")
        progress.start()
        
        try:
            logger.info(f"Extracting text from DOCX: {file_path}")
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text:
                    full_text.append(para.text)
            
            progress.stop()
            return "\n".join(full_text)
        except Exception as e:
            progress.stop()
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise ValueError(f"Could not read the DOCX file: {str(e)}")
    
    def extract_text_from_txt(self, file_path):
        """Extract text from .txt file with error handling"""
        progress = ProgressTracker("Reading TXT file")
        progress.start()
        
        try:
            logger.info(f"Extracting text from TXT: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            progress.stop()
            return content
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
                progress.stop()
                return content
            except Exception as e:
                progress.stop()
                logger.error(f"Error reading TXT with latin-1: {str(e)}")
                raise ValueError(f"Could not read the text file with supported encodings: {str(e)}")
        except Exception as e:
            progress.stop()
            logger.error(f"Error reading TXT: {str(e)}")
            raise ValueError(f"Could not read the text file: {str(e)}")
    
    def get_idea_from_file(self, file_path):
        """Get idea text from a file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if file_path.lower().endswith(".txt"):
            return self.extract_text_from_txt(file_path)
        elif file_path.lower().endswith(".docx"):
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError("Unsupported file type. Please use .txt or .docx files only.")
    
    def build_prompts(self, idea):
        """Build optimized evaluation prompts for different aspects"""
        # Truncate if idea is too long
        if len(idea) > 3000:  # Reduced for faster processing
            logger.warning("Idea text truncated to 3000 characters")
            idea = idea[:3000]
        
        # More focused prompts for faster, more targeted responses
        prompts = {
            "swot": f"""You are an expert startup analyst. Evaluate this startup idea in a concise SWOT format.
            
Idea: {idea}

IMPORTANT: Be precise and specific with your analysis. Avoid generic statements.
Focus on the most important factors for each category.

Format your answer as:
STRENGTHS:
- [Key strength 1 - be specific]
- [Key strength 2 - be specific]
- [Key strength 3 - be specific]

WEAKNESSES:
- [Key weakness 1 - be specific]
- [Key weakness 2 - be specific]
- [Key weakness 3 - be specific]

OPPORTUNITIES:
- [Key opportunity 1 - be specific]
- [Key opportunity 2 - be specific]
- [Key opportunity 3 - be specific]

THREATS:
- [Key threat 1 - be specific]
- [Key threat 2 - be specific]
- [Key threat 3 - be specific]""",

            "revenue": f"""As a business model expert, suggest 3 innovative yet practical revenue models for this startup idea.
            
Idea: {idea}

IMPORTANT: Be precise and specific. Each revenue model must be directly applicable to this idea.
Provide actionable details, not generic business advice.

For each model, provide:
1. The revenue model name (be specific)
2. How it works for THIS specific startup (2-3 sentences)
3. One key advantage (with numbers if possible)
4. One implementation consideration (be specific)""",

            "tech": f"""As a technical architect, recommend a practical tech stack for this startup idea.
            
Idea: {idea}

IMPORTANT: Be precise and specific with your recommendations.
Choose technologies that are current, cost-effective, and appropriate for this specific idea.

Format your answer as:
FRONTEND: [Specific technologies with brief justification]
BACKEND: [Specific technologies with brief justification]
DATABASE: [Specific technologies with brief justification]
INFRASTRUCTURE: [Specific deployment/hosting with brief justification]
DEVELOPMENT TOOLS: [Specific tools with brief justification]

For each category, include specific names of technologies/tools, not general categories.""",

            "audience": f"""As a market research expert, identify the ideal target audience for this startup idea.
            
Idea: {idea}

IMPORTANT: Be precise and specific. Avoid generic audience descriptions.
Base your analysis on the specific value proposition of this idea.

Format your response as:
PRIMARY AUDIENCE:
- Demographics: [Specific age ranges, locations, income levels, etc.]
- Psychographics: [Specific values, interests, lifestyle details]
- Key needs: [3 specific needs this idea addresses for them]
- Acquisition channels: [3 specific channels to reach this audience]

SECONDARY AUDIENCE:
- Demographics: [Specific description of another potential user segment]
- Why they matter: [Specific value of this segment]
- Potential reach: [Estimated market size if possible]""",

            "validation": f"""As a lean startup coach, outline 3 practical steps to validate this startup idea with minimal resources.
            
Idea: {idea}

IMPORTANT: Be precise and practical. Each step must be specific, actionable, and tailored to this idea.
Avoid generic validation advice.

For each validation step:
1. The validation method (specific name)
2. How to implement it quickly (specific actions, tools, metrics)
3. What signals would indicate success (specific numbers/thresholds)
4. Approximate time and cost required (be specific)

Include one low-cost experiment that can be completed in under a week."""
        }
        return prompts
    
    def evaluate_idea(self, idea_text):
        """Evaluate a startup idea using optimized parallel processing"""
        logger.info("Starting evaluation of startup idea")
        logger.info(f"Idea preview: {idea_text[:100]}...")
        
        if self.verbose:
            print("\nPreparing analysis...")
        
        prompts = self.build_prompts(idea_text)
        results = {}
        
        # Configure temperature based on task needs
        temperatures = {
            "swot": 0.3,      # Lower temperature for more factual analysis
            "revenue": 0.7,    # Higher for creative revenue models
            "tech": 0.4,       # Moderate for technical recommendations
            "audience": 0.5,   # Moderate for audience analysis
            "validation": 0.6  # Slightly higher for practical validation steps
        }
        
        # Print startup message
        if self.verbose:
            print("\nStarting parallel evaluation of startup idea using AI models...")
            print(f"- SWOT Analysis: Using {self.models['swot']}")
            print(f"- Revenue Models: Using {self.models['revenue']}")
            print(f"- Technical Stack: Using {self.models['tech']}")
            print(f"- Target Audience: Using {self.models['audience']}")
            print(f"- Validation Steps: Using {self.models['validation']}")
            print("\nThis may take a few minutes. Processing each section in parallel...\n")
        
        total_tracker = ProgressTracker("Overall evaluation")
        total_tracker.start()
        
        # Execute API calls in parallel with optimized parameters
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_category = {
                executor.submit(
                    self.query_model, 
                    self.models[category], 
                    prompt, 
                    temperatures[category]
                ): category
                for category, prompt in prompts.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    results[category] = future.result()
                    logger.info(f"Completed {category} evaluation")
                except Exception as e:
                    logger.error(f"Error in {category} evaluation: {str(e)}")
                    results[category] = f"Error processing {category} analysis: {str(e)}"
        
        total_tracker.stop()
        
        if self.verbose:
            print("\nAll analyses complete!")
            print("\nEvaluation timing:")
            for category, duration in self.timing_data.items():
                print(f"- {category.title()}: {duration:.2f} seconds")
        
        logger.info("Evaluation complete")
        return results
    
    def save_results(self, idea, results, filename=None, format='pdf'):
        """Save the evaluation results to a file in PDF or TXT format"""
        progress = ProgressTracker(f"Saving results to {format.upper()}")
        progress.start()
        
        if not filename:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            base_filename = f"startup_evaluation_{timestamp}"
            filename = f"{base_filename}.{format}"
        elif not filename.lower().endswith(f".{format.lower()}"):
            filename = f"{filename}.{format}"
        
        if format.lower() == 'pdf':
            self._save_results_to_pdf(idea, results, filename)
        elif format.lower() == 'txt':
            self._save_results_to_txt(idea, results, filename)
        else:
            progress.stop()
            raise ValueError("Unsupported format. Use 'pdf' or 'txt'.")
        
        progress.stop()
        logger.info(f"Results saved to {filename}")
        return filename

    def _save_results_to_pdf(self, idea, results, filename):
        """Save evaluation results to a PDF file with enhanced formatting"""
        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        styles = getSampleStyleSheet()
        story = []

        # Add title with better styling
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=1,  # Center alignment
            spaceAfter=20
        )
        story.append(Paragraph("Startup Idea Evaluation Report", title_style))
        
        # Add subtitle with timestamp
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.darkgrey,
            alignment=1,
            spaceAfter=30
        )
        story.append(Paragraph(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))

        # Add idea section
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.darkblue,
            spaceBefore=20,
            spaceAfter=10
        )
        story.append(Paragraph("Startup Idea", section_style))
        
        idea_style = ParagraphStyle(
            'IdeaText',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=5,
            spaceAfter=15
        )
        
        # Truncate idea if too long
        idea_text = idea[:1000] + '...' if len(idea) > 1000 else idea
        story.append(Paragraph(idea_text, idea_style))
        
        # Add timing data
        if self.timing_data:
            story.append(Paragraph("Analysis Timing", section_style))
            timing_data = [["Analysis Section", "Processing Time (seconds)"]]
            for category, duration in self.timing_data.items():
                timing_data.append([category.title(), f"{duration:.2f}"])
            
            timing_table = Table(timing_data, colWidths=[doc.width/2.0]*2)
            timing_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.darkblue),
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 1), (1, -1), 'CENTER')
            ]))
            story.append(timing_table)
            story.append(Spacer(1, 20))

        # Add each evaluation section with improved formatting
        for category, content in results.items():
            category_title = {
                "swot": "SWOT Analysis",
                "revenue": "Revenue Models",
                "tech": "Technical Stack",
                "audience": "Target Audience Analysis",
                "validation": "Validation Strategy"
            }.get(category, category.upper())
            
            story.append(Paragraph(category_title, section_style))
            
            content_style = ParagraphStyle(
                'Content',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                spaceBefore=5,
                spaceAfter=15
            )
            
            # Format content better
            formatted_content = content.replace('\n\n', '<br/><br/>').replace('\n', '<br/>')
            story.append(Paragraph(formatted_content, content_style))
            story.append(Spacer(1, 10))

        # Add footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        story.append(Spacer(1, 20))
        story.append(Paragraph("Generated using the Startup Idea Evaluator AI Tool", footer_style))

        doc.build(story)
    
    def _save_results_to_txt(self, idea, results, filename):
        """Save evaluation results to a TXT file with formatted output"""
        with open(filename, 'w', encoding='utf-8') as f:
            # Write header
            f.write("=" * 80 + "\n")
            f.write(" STARTUP IDEA EVALUATION RESULTS ".center(80, "=") + "\n")
            f.write("=" * 80 + "\n\n")
            
            # Write timestamp
            f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write idea section
            f.write("STARTUP IDEA\n")
            f.write("-" * 80 + "\n")
            f.write(idea + "\n\n")
            
            # Write timing data if available
            if self.timing_data:
                f.write("EVALUATION TIMING\n")
                f.write("-" * 40 + "\n")
                for category, duration in self.timing_data.items():
                    f.write(f"- {category.title()}: {duration:.2f} seconds\n")
                f.write("\n")
            
            # Write each evaluation section
            for category, content in results.items():
                category_title = {
                    "swot": "SWOT ANALYSIS",
                    "revenue": "REVENUE MODELS",
                    "tech": "TECHNICAL STACK",
                    "audience": "TARGET AUDIENCE",
                    "validation": "VALIDATION STRATEGY"
                }.get(category, category.upper())
                
                f.write(f"{category_title}\n")
                f.write("-" * len(category_title) + "\n")
                f.write(content + "\n\n")
                f.write("-" * 80 + "\n\n")
            
            # Write footer
            f.write("\n" + "=" * 80 + "\n")
            f.write("Generated using the Startup Idea Evaluator AI Tool\n")
    
    def print_results(self, results):
        """Print evaluation results to console with improved formatting"""
        print("\n" + "="*80)
        print(" STARTUP IDEA EVALUATION RESULTS ".center(80, "="))
        print("="*80)
        
        # Print timing data
        if self.timing_data:
            print("\nEVALUATION TIMING")
            print("-" * 40)
            for category, duration in self.timing_data.items():
                print(f"- {category.title()}: {duration:.2f} seconds")
        
        # Print each section
        for category, content in results.items():
            category_title = {
                "swot": "SWOT ANALYSIS",
                "revenue": "REVENUE MODELS",
                "tech": "TECHNICAL STACK",
                "audience": "TARGET AUDIENCE",
                "validation": "VALIDATION STRATEGY"
            }.get(category, category.upper())
            
            print(f"\n{category_title}\n{'-' * len(category_title)}")
            print(content)
            print("\n" + "-"*80)
        
        print("\n" + "="*80 + "\n")

def main():
    """Main function to run the evaluator"""
    # Run as web server only
    host = '0.0.0.0'  # Allow external connections
    port = 5000
    print(f"\nStarting web server at http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    app.run(host=host, port=port, debug=True)

if __name__ == "__main__":
    main()