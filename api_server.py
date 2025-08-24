import os
import os
import json
import asyncio
import sys
import io
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Portia imports
from portia import Portia, Config, LLMProvider, tool, ToolRegistry

# Browser-use imports
from langchain_google_genai import ChatGoogleGenerativeAI
import browser_use
from browser_use import Browser, BrowserConfig, Controller, ActionResult

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI(
    title="Website Testing Agent API",
    description="AI-powered website testing and automation API",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch the Gemini API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file or environment variables.")

# Create operation_logs directory and serve static files
logs_dir = Path("./operation_logs")
screenshots_dir = logs_dir / "screenshots"
logs_dir.mkdir(exist_ok=True)
screenshots_dir.mkdir(exist_ok=True)

# Mount static files for serving screenshots
app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")

# Pydantic models for API requests and responses
class ScreenshotInstruction(BaseModel):
    step_description: str
    filename: str

class TestInstructions(BaseModel):
    target_url: str
    task_description: str
    screenshot_instructions: List[ScreenshotInstruction]

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class ExecutionResult(BaseModel):
    task_id: str
    success: bool
    timestamp: str
    task_details: Dict
    execution_steps: List[Dict]
    screenshots: List[str]
    error: Optional[str] = None
    log_file: Optional[str] = None

class AnalysisResult(BaseModel):
    task_id: str
    analysis_report: Dict
    recommendations: List[str]
    compliance_check: Dict

# In-memory storage for task status (use Redis/DB in production)
task_storage = {}

class BrowserExecutor:
    """Direct browser automation executor using browser-use library."""
    
    def __init__(self):
        self.logs_dir = Path("./operation_logs")
        self.screenshots_dir = Path("./operation_logs/screenshots")
        self.logs_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        
    def setup_detailed_logging(self, task_id: str):
        """Setup comprehensive logging for the agent execution."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = self.logs_dir / f"detailed_agent_log_{task_id}_{timestamp}.txt"
        
        # Create a custom logger
        logger = logging.getLogger(f"agent_{task_id}")
        logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger, log_file_path
    
    def capture_stdout_stderr(self, task_id: str):
        """Capture stdout and stderr to log everything the agent outputs."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stdout_log_path = self.logs_dir / f"agent_stdout_{task_id}_{timestamp}.txt"
        stderr_log_path = self.logs_dir / f"agent_stderr_{task_id}_{timestamp}.txt"
        
        # Backup original stdout/stderr
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # Create file objects for capturing output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Custom stdout/stderr that writes to both original and capture
        class TeeOutput:
            def __init__(self, original, capture, log_file):
                self.original = original
                self.capture = capture
                self.log_file = log_file
                
            def write(self, text):
                self.original.write(text)
                self.capture.write(text)
                # Also write to file immediately
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(text)
                    f.flush()
                    
            def flush(self):
                self.original.flush()
                self.capture.flush()
        
        # Redirect stdout and stderr
        sys.stdout = TeeOutput(original_stdout, stdout_capture, stdout_log_path)
        sys.stderr = TeeOutput(original_stderr, stderr_capture, stderr_log_path)
        
        return original_stdout, original_stderr, stdout_capture, stderr_capture, stdout_log_path, stderr_log_path
    
    async def create_browser_agent(self, task: str, task_id: str = None):
        """Create and configure a browser-use agent with Gemini 2.0 Flash."""
        try:
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
                
            # Initialize Gemini LLM for browser-use with improved configuration
            gemini_llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=GEMINI_API_KEY,
                temperature=0.1,
                max_tokens=4096,
                timeout=60
            )
            
            # Configure browser settings for better screenshot capture
            browser_config = BrowserConfig(
                headless=False,  # Run with head for better compatibility
                disable_security=True,  # Disable security features for testing
                keep_alive=True,
                extra_browser_args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "--window-size=1920,1080",
                    "--disable-extensions",
                    "--disable-plugins",
                ]
            )
            
            # Create browser with config (without context_config)
            browser = Browser(config=browser_config)
            
            # Create custom controller for enhanced logging functions
            controller = Controller()
            agent_logger = AgentLogger(self.logs_dir, task_id or "unknown")
            
            @controller.action('Log what you are doing right now with detailed context')
            def log_action(message: str) -> ActionResult:
                """Log what the agent is doing right now with enhanced tracking."""
                agent_logger.log_thought(f"ACTION: {message}", "ACTION")
                return ActionResult(extracted_content=f"Action logged: {message}")
            
            @controller.action('Log what you observe on the current page')
            def log_observation(message: str) -> ActionResult:
                """Log what the agent observes on the page with enhanced tracking."""
                agent_logger.log_thought(f"OBSERVATION: {message}", "OBSERVE")
                return ActionResult(extracted_content=f"Observation logged: {message}")
            
            @controller.action('Log your decision-making process and reasoning')
            def log_decision(message: str) -> ActionResult:
                """Log agent's decision-making process with enhanced tracking."""
                agent_logger.log_thought(f"DECISION: {message}", "DECISION")
                return ActionResult(extracted_content=f"Decision logged: {message}")
            
            @controller.action('Navigate to a specific URL and log the result')
            def navigate_and_log(url: str) -> ActionResult:
                """Navigate to URL with enhanced logging."""
                try:
                    agent_logger.log_navigation(url, True)
                    return ActionResult(extracted_content=f"Navigation logged for: {url}")
                except Exception as e:
                    agent_logger.log_navigation(url, False)
                    agent_logger.log_error("Navigation", str(e))
                    return ActionResult(extracted_content=f"Navigation failed for: {url}")
            
            @controller.action('Log interaction with page elements')
            def log_element_interaction(element: str, action: str) -> ActionResult:
                """Log interactions with page elements."""
                agent_logger.log_interaction(element, action, True)
                return ActionResult(extracted_content=f"Interaction logged: {action} on {element}")
            
            @controller.action('Extract and log data from the current page')
            def extract_and_log(data_type: str, content: str) -> ActionResult:
                """Extract and log data from the page."""
                agent_logger.log_extraction(data_type, content, True)
                return ActionResult(extracted_content=f"Data extraction logged: {data_type}")
            
            @controller.action('Take a screenshot of current page state with description')
            def take_screenshot_now(description: str) -> ActionResult:
                """Take a screenshot of current browser state with enhanced logging."""
                try:
                    agent_logger.screenshot_count += 1
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_filename = f"{task_id}_agent_action_{agent_logger.screenshot_count}_{timestamp}.png"
                    screenshot_path = agent_logger.screenshots_dir / screenshot_filename
                    screenshot_url = f"/screenshots/{screenshot_filename}"
                    
                    # Enhanced logging for screenshot
                    agent_logger.log_thought(f"📸 SCREENSHOT {agent_logger.screenshot_count}: {description}", "SCREENSHOT")
                    
                    return ActionResult(
                        extracted_content=f"Screenshot {agent_logger.screenshot_count} requested: {screenshot_filename} - {description}",
                        include_in_memory=True
                    )
                    
                except Exception as e:
                    agent_logger.log_error("Screenshot", str(e))
                    return ActionResult(extracted_content=f"Screenshot failed: {str(e)}")
            
            # Create browser-use agent with custom controller and optimized settings
            agent = browser_use.Agent(
                task=task,
                llm=gemini_llm,
                browser=browser,
                use_vision=True,  # Enable vision for screenshots
                save_conversation_path=str(self.logs_dir / "browser_conversation"),
                controller=controller,  # Use our custom controller
                enable_memory=False,  # Disable memory to avoid package warnings
                max_actions_per_step=5,  # Limit actions per step for better performance
                include_attributes=["title", "aria-label", "placeholder"]  # Optimize element detection
            )
            
            # Store agent_logger reference for manual screenshot capture
            agent._custom_logger = agent_logger
            
            return agent
            
        except Exception as e:
            raise Exception(f"Error creating browser agent: {e}")
    
    def enhance_step_with_thoughts(self, step_info: dict, enhanced_step: dict, step_number: int, agent_thoughts: list, actions: list = None) -> tuple:
        """Enhance step information with agent thoughts for natural language descriptions."""
        # Look for relevant thoughts for this step
        step_thoughts = {
            "actions": [],
            "observations": [],
            "decisions": []
        }
        
        # Collect thoughts for this step (rough correlation by order)
        thoughts_per_step = max(1, len(agent_thoughts) // max(1, step_number)) if agent_thoughts else 0
        start_idx = (step_number - 1) * thoughts_per_step
        end_idx = min(len(agent_thoughts), start_idx + thoughts_per_step + 2)  # Allow some overlap
        
        for thought in agent_thoughts[start_idx:end_idx]:
            if thought["type"] == "action":
                step_thoughts["actions"].append(thought["message"])
            elif thought["type"] == "observation":
                step_thoughts["observations"].append(thought["message"])
            elif thought["type"] == "decision":
                step_thoughts["decisions"].append(thought["message"])
        
        # If we have specific actions with log_action details, match them
        if actions:
            for action in actions:
                if action["type"] in ["log_action", "log_observation", "log_decision"]:
                    message = action["details"].get("message", "")
                    if message:
                        if action["type"] == "log_action":
                            step_thoughts["actions"].append(message)
                        elif action["type"] == "log_observation":
                            step_thoughts["observations"].append(message)
                        elif action["type"] == "log_decision":
                            step_thoughts["decisions"].append(message)
        
        # Create human-readable action summary
        if step_thoughts["actions"]:
            action_summary = step_thoughts["actions"][0]  # Use first action as main summary
        elif step_thoughts["decisions"]:
            action_summary = f"Decision: {step_thoughts['decisions'][0]}"
        elif step_thoughts["observations"]:
            action_summary = f"Observation: {step_thoughts['observations'][0]}"
        else:
            # Fall back to technical summary
            if actions:
                technical_actions = [a["type"] for a in actions if a["type"] not in ["log_action", "log_observation", "log_decision"]]
                if technical_actions:
                    action_summary = f"Step {step_number}: {', '.join(technical_actions)}"
                else:
                    action_summary = f"Step {step_number}: {', '.join([a['type'] for a in actions])}"
            else:
                action_summary = step_info.get("action", "Unknown action")
        
        # Update step_info with natural language content
        step_info["action"] = action_summary
        step_info["thoughts"] = step_thoughts
        
        # Update enhanced_step with natural language content
        enhanced_step["action_summary"] = action_summary
        enhanced_step["thoughts"] = step_thoughts
        
        # Add detailed thought breakdown
        enhanced_step["action_details"]["thoughts"] = step_thoughts
        
        return step_info, enhanced_step
    
    def load_agent_thoughts(self, task_id: str) -> list:
        """Load agent thoughts from the log file for natural language descriptions."""
        thoughts_file = self.logs_dir / f"agent_thoughts_{task_id}.txt"
        thoughts = []
        
        try:
            if thoughts_file.exists():
                with open(thoughts_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ('] ACTION:' in line or '] OBSERVATION:' in line or '] DECISION:' in line):
                            # Parse timestamp and content
                            parts = line.split('] ', 1)
                            if len(parts) == 2:
                                timestamp_part = parts[0][1:]  # Remove leading [
                                content_part = parts[1]
                                
                                # Extract action type and message
                                if ': ' in content_part:
                                    action_type, message = content_part.split(': ', 1)
                                    thoughts.append({
                                        "timestamp": timestamp_part,
                                        "type": action_type.lower(),
                                        "message": message
                                    })
                print(f"✅ Loaded {len(thoughts)} agent thoughts from {thoughts_file}")
            else:
                print(f"[WARNING] Agent thoughts file not found: {thoughts_file}")
        except Exception as e:
            print(f"❌ Error loading agent thoughts: {e}")
        
        return thoughts
    
    def save_execution_results(self, history, task_details: dict, task_id: str):
        """Save browser execution results and screenshots with enhanced processing and agent thoughts integration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save execution log
        log_file = self.logs_dir / f"browser_execution_{task_id}_{timestamp}.json"
        
        # Load agent thoughts for natural language descriptions
        agent_thoughts = self.load_agent_thoughts(task_id)
        
        results = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "task_details": task_details,
            "execution_steps": [],
            "screenshots": [],
            "screenshot_urls": [],  # URLs for frontend access
            "success": False,
            "error": None,
            "full_conversation": [],
            "debug_info": {},
            "enhanced_steps": [],  # New enhanced step format
            "agent_thoughts": agent_thoughts  # Include agent thoughts
        }
        
        try:
            # Debug the history object structure
            print(f"[DEBUG] History type: {type(history)}")
            print(f"[DEBUG] History dir: {dir(history)}")
            
            # Handle new AgentHistoryList format that has a .history attribute
            if hasattr(history, 'history'):
                print(f"[DEBUG] AgentHistoryList detected, accessing .history attribute")
                actual_history = history.history
                print(f"[DEBUG] Actual history type: {type(actual_history)}")
                print(f"[DEBUG] Actual history length: {len(actual_history)}")
                
                # Convert actual history to list if it's not already
                if hasattr(actual_history, '__iter__'):
                    history_list = list(actual_history)
                else:
                    history_list = [actual_history] if actual_history else []
            else:
                # Fallback to old format handling
                if hasattr(history, '__iter__'):
                    history_list = list(history)
                else:
                    history_list = [history] if history else []
            
            print(f"[DEBUG] Final history list length: {len(history_list)}")
            
            # Store debug info
            results["debug_info"] = {
                "history_type": str(type(history)),
                "history_length": len(history_list),
                "history_attributes": dir(history) if history else []
            }
            
            if history_list:
                for i, step in enumerate(history_list):
                    print(f"[DEBUG] Step {i+1} type: {type(step)}")
                    print(f"[DEBUG] Step {i+1} attributes: {dir(step)}")
                    
                    # Extract step information with enhanced processing
                    step_info = {
                        "step_number": i + 1,
                        "action": "N/A",
                        "result": "N/A", 
                        "timestamp": datetime.now().isoformat(),
                        "screenshot_url": None,
                        "raw_step_type": str(type(step)),
                        "step_attributes": dir(step),
                        "action_type": "unknown",
                        "success": False,
                        "duration": None
                    }
                    
                    # Enhanced step processing with better action classification
                    enhanced_step = {
                        "step_number": i + 1,
                        "timestamp": datetime.now().isoformat(),
                        "action_summary": "Unknown action",
                        "action_details": {},
                        "result_summary": "No result available",
                        "result_details": {},
                        "action_type": "unknown",
                        "success_status": "unknown",
                        "screenshot_url": None,
                        "errors": [],
                        "metadata": {}
                    }
                    
                    # Handle AgentHistory objects from browser-use
                    if hasattr(step, 'model_output') and hasattr(step, 'result'):
                        print(f"[DEBUG] AgentHistory object detected")
                        model_output = step.model_output
                        result = step.result
                        
                        # Extract actions from model_output
                        actions = []
                        if hasattr(model_output, 'action') and model_output.action:
                            for action in model_output.action:
                                action_type = "unknown"
                                action_details = {}
                                
                                # Check for different action types
                                if hasattr(action, 'go_to_url') and action.go_to_url:
                                    action_type = "navigate"
                                    action_details = {"url": action.go_to_url.url}
                                elif hasattr(action, 'input_text') and action.input_text:
                                    action_type = "input"
                                    action_details = {"text": action.input_text.text, "index": action.input_text.index}
                                elif hasattr(action, 'click_element_by_index') and action.click_element_by_index:
                                    action_type = "click"
                                    action_details = {"index": action.click_element_by_index.index}
                                elif hasattr(action, 'log_action') and action.log_action:
                                    action_type = "log_action"
                                    action_details = {"message": action.log_action.message}
                                elif hasattr(action, 'log_observation') and action.log_observation:
                                    action_type = "log_observation"
                                    action_details = {"message": action.log_observation.message}
                                elif hasattr(action, 'log_decision') and action.log_decision:
                                    action_type = "log_decision"
                                    action_details = {"message": action.log_decision.message}
                                elif hasattr(action, 'done') and action.done:
                                    action_type = "done"
                                    action_details = {"text": action.done.text, "success": action.done.success}
                                elif hasattr(action, 'extract_content') and action.extract_content:
                                    action_type = "extract_content"
                                    action_details = {"goal": action.extract_content.goal}
                                elif hasattr(action, 'take_screenshot_now') and action.take_screenshot_now:
                                    action_type = "screenshot"
                                    action_details = {"description": action.take_screenshot_now.description}
                                
                                actions.append({
                                    "type": action_type,
                                    "details": action_details
                                })
                        
                        # Extract results
                        results_data = []
                        if result and hasattr(result, '__iter__'):
                            for action_result in result:
                                if hasattr(action_result, 'extracted_content'):
                                    results_data.append({
                                        "content": action_result.extracted_content,
                                        "is_done": getattr(action_result, 'is_done', False),
                                        "success": getattr(action_result, 'success', None),
                                        "error": getattr(action_result, 'error', None)
                                    })
                        
                        # Extract brain state information
                        brain_state = {}
                        if hasattr(model_output, 'current_state'):
                            state = model_output.current_state
                            brain_state = {
                                "evaluation": getattr(state, 'evaluation_previous_goal', ''),
                                "memory": getattr(state, 'memory', ''),
                                "next_goal": getattr(state, 'next_goal', '')
                            }
                        
                        # Extract screenshot if available
                        screenshot_data = None
                        if hasattr(step, 'state') and hasattr(step.state, 'screenshot'):
                            screenshot_data = step.state.screenshot
                        
                        # Build comprehensive step info
                        step_info.update({
                            "action": f"Step {i+1}: {', '.join([a['type'] for a in actions])}",
                            "result": f"Results: {len(results_data)} actions completed",
                            "actions": actions,
                            "results": results_data,
                            "brain_state": brain_state,
                            "action_type": actions[0]['type'] if actions else "unknown",
                            "success": all(r.get('success', True) for r in results_data) if results_data else True
                        })
                        
                        enhanced_step.update({
                            "action_summary": f"Step {i+1}: {', '.join([a['type'] for a in actions])}",
                            "action_details": {"actions": actions, "brain_state": brain_state},
                            "result_summary": f"Completed {len(results_data)} actions",
                            "result_details": {"results": results_data},
                            "action_type": actions[0]['type'] if actions else "unknown",
                            "success_status": "success" if step_info["success"] else "failed"
                        })
                        
                        # Handle screenshots
                        if screenshot_data:
                            screenshot_filename = f"{task_id}_step_{i+1}_{timestamp}.png"
                            screenshot_path = self.screenshots_dir / screenshot_filename
                            screenshot_url = f"/screenshots/{screenshot_filename}"
                            
                            try:
                                # Decode base64 screenshot
                                import base64
                                screenshot_bytes = base64.b64decode(screenshot_data)
                                with open(screenshot_path, 'wb') as f:
                                    f.write(screenshot_bytes)
                                
                                step_info["screenshot"] = str(screenshot_path)
                                step_info["screenshot_url"] = screenshot_url
                                enhanced_step["screenshot_url"] = screenshot_url
                                results["screenshots"].append(str(screenshot_path))
                                results["screenshot_urls"].append(screenshot_url)
                                
                                print(f"✅ Saved screenshot for step {i+1}: {screenshot_filename}")
                            except Exception as e:
                                enhanced_step["errors"].append(f"Screenshot save error: {str(e)}")
                                print(f"❌ Error saving screenshot for step {i+1}: {e}")
                        
                        print(f"✅ Processed AgentHistory step {i+1} with {len(actions)} actions and {len(results_data)} results")
                        
                        # Enhance step with agent thoughts for natural language descriptions
                        step_info, enhanced_step = self.enhance_step_with_thoughts(step_info, enhanced_step, i+1, agent_thoughts, actions)
                    
                    # Handle tuple format (appears to be the actual format)
                    elif isinstance(step, tuple):
                        print(f"[DEBUG] Tuple length: {len(step)}")
                        if len(step) >= 2:
                            # Typically (model_output, result) or similar
                            action_data = str(step[0]) if step[0] else "N/A"
                            result_data = str(step[1]) if step[1] else "N/A"
                            
                            step_info["action"] = action_data
                            step_info["result"] = result_data
                            
                            # Enhanced processing for better display
                            enhanced_step["action_summary"] = self.extract_action_summary(action_data)
                            enhanced_step["action_details"] = self.parse_action_details(action_data)
                            enhanced_step["result_summary"] = self.extract_result_summary(result_data)
                            enhanced_step["result_details"] = self.parse_result_details(result_data)
                            enhanced_step["action_type"] = self.classify_action_type(action_data)
                            enhanced_step["success_status"] = self.determine_success_status(result_data)
                            
                            print(f"✅ Extracted from tuple - Action: {action_data[:100]}...")
                            print(f"✅ Extracted from tuple - Result: {result_data[:100]}...")
                            
                            # Enhance step with agent thoughts for natural language descriptions
                            step_info, enhanced_step = self.enhance_step_with_thoughts(step_info, enhanced_step, i+1, agent_thoughts)
                            
                        # Look for additional data in the tuple
                        for j, item in enumerate(step):
                            print(f"[DEBUG] Tuple item {j}: {type(item)} = {str(item)[:100]}...")
                            
                            # Check if any item has screenshot data
                            if hasattr(item, 'screenshot') and item.screenshot:
                                screenshot_filename = f"{task_id}_step_{i+1}_{timestamp}.png"
                                screenshot_path = self.screenshots_dir / screenshot_filename
                                screenshot_url = f"/screenshots/{screenshot_filename}"
                                
                                try:
                                    # Handle screenshot data
                                    if isinstance(item.screenshot, bytes):
                                        with open(screenshot_path, 'wb') as f:
                                            f.write(item.screenshot)
                                    elif hasattr(item.screenshot, 'save'):
                                        item.screenshot.save(str(screenshot_path))
                                    
                                    step_info["screenshot"] = str(screenshot_path)
                                    step_info["screenshot_url"] = screenshot_url
                                    enhanced_step["screenshot_url"] = screenshot_url
                                    results["screenshots"].append(str(screenshot_path))
                                    results["screenshot_urls"].append(screenshot_url)
                                    
                                    print(f"✅ Saved screenshot from tuple item {j}: {screenshot_filename}")
                                    break
                                except Exception as e:
                                    enhanced_step["errors"].append(f"Screenshot save error: {str(e)}")
                                    print(f"❌ Error saving screenshot from tuple item {j}: {e}")
                    
                    else:
                        # Try different attribute names for browser-use objects
                        action_attrs = ['model_output', 'action', 'input', 'query', 'tool_calls']
                        result_attrs = ['result', 'output', 'response', 'content']
                        timestamp_attrs = ['timestamp', 'time', 'created_at']
                        screenshot_attrs = ['screenshot', 'image', 'screen_capture', 'page_screenshot']
                        
                        # Extract action
                        for attr in action_attrs:
                            if hasattr(step, attr):
                                value = getattr(step, attr)
                                if value:
                                    action_data = str(value)
                                    step_info["action"] = action_data
                                    enhanced_step["action_summary"] = self.extract_action_summary(action_data)
                                    enhanced_step["action_details"] = self.parse_action_details(action_data)
                                    enhanced_step["action_type"] = self.classify_action_type(action_data)
                                    print(f"✅ Found action in {attr}: {str(value)[:100]}...")
                                    break
                        
                        # Extract result
                        for attr in result_attrs:
                            if hasattr(step, attr):
                                value = getattr(step, attr)
                                if value:
                                    result_data = str(value)
                                    step_info["result"] = result_data
                                    enhanced_step["result_summary"] = self.extract_result_summary(result_data)
                                    enhanced_step["result_details"] = self.parse_result_details(result_data)
                                    enhanced_step["success_status"] = self.determine_success_status(result_data)
                                    print(f"✅ Found result in {attr}: {str(value)[:100]}...")
                                    break
                        
                        # Extract timestamp
                        for attr in timestamp_attrs:
                            if hasattr(step, attr):
                                value = getattr(step, attr)
                                if value:
                                    if hasattr(value, 'isoformat'):
                                        step_info["timestamp"] = value.isoformat()
                                        enhanced_step["timestamp"] = value.isoformat()
                                    else:
                                        step_info["timestamp"] = str(value)
                                        enhanced_step["timestamp"] = str(value)
                                    print(f"✅ Found timestamp in {attr}: {step_info['timestamp']}")
                                    break
                        
                        # Look for screenshots in various possible locations
                        for attr in screenshot_attrs:
                            if hasattr(step, attr):
                                screenshot = getattr(step, attr)
                                if screenshot:
                                    screenshot_filename = f"{task_id}_step_{i+1}_{timestamp}.png"
                                    screenshot_path = self.screenshots_dir / screenshot_filename
                                    screenshot_url = f"/screenshots/{screenshot_filename}"
                                    
                                    try:
                                        # Handle different screenshot formats
                                        if isinstance(screenshot, bytes):
                                            with open(screenshot_path, 'wb') as f:
                                                f.write(screenshot)
                                        elif hasattr(screenshot, 'save'):
                                            # PIL Image or similar
                                            screenshot.save(str(screenshot_path))
                                        elif isinstance(screenshot, str) and screenshot.startswith(('http', '/', 'data:')):
                                            # URL or data URI - try to download/decode
                                            if screenshot.startswith('data:image'):
                                                import base64
                                                header, data = screenshot.split(',', 1)
                                                with open(screenshot_path, 'wb') as f:
                                                    f.write(base64.b64decode(data))
                                            elif screenshot.startswith('/') and os.path.exists(screenshot):
                                                # File path
                                                import shutil
                                                shutil.copy2(screenshot, screenshot_path)
                                        
                                        step_info["screenshot"] = str(screenshot_path)
                                        step_info["screenshot_url"] = screenshot_url
                                        enhanced_step["screenshot_url"] = screenshot_url
                                        results["screenshots"].append(str(screenshot_path))
                                        results["screenshot_urls"].append(screenshot_url)
                                        
                                        print(f"✅ Saved screenshot from {attr}: {screenshot_filename}")
                                        break
                                        
                                    except Exception as e:
                                        enhanced_step["errors"].append(f"Screenshot processing error: {str(e)}")
                                        print(f"❌ Error saving screenshot from {attr}: {e}")
                    
                    # Enhance step with agent thoughts for natural language descriptions (fallback case)
                    step_info, enhanced_step = self.enhance_step_with_thoughts(step_info, enhanced_step, i+1, agent_thoughts)
                    
                    # Add conversation details if available
                    if step_info["action"] != "N/A":
                        # Create enhanced conversation entry with rich data
                        conversation_entry = {
                            "step": i + 1,
                            "model_output": step_info["action"],
                            "timestamp": step_info["timestamp"],
                            "conversation_data": {}
                        }
                        
                        # Try to extract rich conversation data from the step
                        if hasattr(step, 'model_output') and step.model_output:
                            # Look for enhanced logging patterns in the model output
                            model_output = str(step.model_output)
                            
                            # Extract observations
                            if '👁️ [OBSERVE]' in model_output:
                                obs_match = re.search(r'👁️ \[OBSERVE\] Agent Log: OBSERVATION:\s*(.+?)(?:\n|$)', model_output)
                                if obs_match:
                                    conversation_entry["conversation_data"]["observation"] = obs_match.group(1).strip()
                            
                            # Extract extractions
                            if '⚡ [EXTRACT]' in model_output:
                                extract_match = re.search(r'⚡ \[EXTRACT\] Agent Log: EXTRACTION: ✅ Extracted (.+?): (.+?)(?:\n|$)', model_output)
                                if extract_match:
                                    conversation_entry["conversation_data"]["extraction"] = {
                                        "type": extract_match.group(1).strip(),
                                        "content": extract_match.group(2).strip()
                                    }
                            
                            # Extract decisions
                            if '🧭 [DECISION]' in model_output:
                                decision_match = re.search(r'🧭 \[DECISION\] Agent Log: DECISION:\s*(.+?)(?:\n|$)', model_output)
                                if decision_match:
                                    conversation_entry["conversation_data"]["decision"] = decision_match.group(1).strip()
                            
                            # Extract actions (including interactions)
                            if '⚡ [ACTION]' in model_output:
                                action_match = re.search(r'⚡ \[ACTION\] Agent Log: ACTION:\s*(.+?)(?:\n|$)', model_output)
                                if action_match:
                                    conversation_entry["conversation_data"]["action"] = action_match.group(1).strip()
                            
                            # Extract interactions (which are also actions)
                            if '⚡ [INTERACT]' in model_output:
                                interact_match = re.search(r'⚡ \[INTERACT\] Agent Log: INTERACTION:\s*(.+?)(?:\n|$)', model_output)
                                if interact_match:
                                    # Add to actions if not already present
                                    if "action" not in conversation_entry["conversation_data"]:
                                        conversation_entry["conversation_data"]["action"] = interact_match.group(1).strip()
                                    else:
                                        # Append to existing action
                                        conversation_entry["conversation_data"]["action"] += f"\n{interact_match.group(1).strip()}"
                            
                            # Look for extracted content from page
                            if '📄  Extracted from page' in model_output:
                                # Try to find JSON content after the extraction marker
                                json_match = re.search(r'📄  Extracted from page\s*:\s*```json\s*(\{.*?\})\s*```', model_output, re.DOTALL)
                                if json_match:
                                    try:
                                        extracted_json = json.loads(json_match.group(1))
                                        conversation_entry["conversation_data"]["extracted_page_content"] = extracted_json
                                    except json.JSONDecodeError:
                                        # If JSON parsing fails, capture as raw text
                                        conversation_entry["conversation_data"]["extracted_page_content"] = json_match.group(1)
                        
                        # Also try to get data from other attributes
                        if hasattr(step, 'extracted_content') and step.extracted_content:
                            conversation_entry["conversation_data"]["extracted_content"] = step.extracted_content
                        
                        if hasattr(step, 'metadata') and step.metadata:
                            conversation_entry["conversation_data"]["metadata"] = step.metadata
                        
                        results["full_conversation"].append(conversation_entry)
                    
                    results["execution_steps"].append(step_info)
                    results["enhanced_steps"].append(enhanced_step)
                
                results["success"] = True
                print(f"✅ Processed {len(history_list)} execution steps with {len(results['screenshots'])} screenshots")
            else:
                print("[WARNING] No history items found")
            
        except Exception as e:
            results["error"] = str(e)
            print(f"❌ Error processing browser history: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
        
        # Save results to file
        try:
            with open(log_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            results["log_file"] = str(log_file)
            print(f"✅ Execution results saved to: {log_file}")
        except Exception as e:
            results["error"] = f"Error saving results: {e}"
            print(f"❌ Error saving results file: {e}")
        
        return results
    
    def extract_action_summary(self, action_data: str) -> str:
        """Extract a concise summary from action data."""
        if not action_data or action_data == "N/A":
            return "No action specified"
        
        # Remove verbose technical details
        lines = action_data.split('\n')
        first_line = lines[0].strip()
        
        # Look for specific action patterns
        if 'navigate' in first_line.lower() or 'goto' in first_line.lower():
            return "Navigating to webpage"
        elif 'click' in first_line.lower():
            return "Clicking element"
        elif 'type' in first_line.lower() or 'input' in first_line.lower():
            return "Entering text"
        elif 'scroll' in first_line.lower():
            return "Scrolling page"
        elif 'wait' in first_line.lower():
            return "Waiting for element"
        elif 'screenshot' in first_line.lower():
            return "Taking screenshot"
        elif 'search' in first_line.lower():
            return "Searching"
        else:
            # Truncate long actions
            return first_line[:60] + "..." if len(first_line) > 60 else first_line
    
    def parse_action_details(self, action_data: str) -> dict:
        """Parse action data into structured details."""
        if not action_data or action_data == "N/A":
            return {}
        
        details = {
            "raw_action": action_data,
            "action_lines": action_data.split('\n')[:5],  # First 5 lines
            "contains_elements": [],
            "contains_urls": [],
            "contains_errors": False
        }
        
        # Extract URLs
        import re
        urls = re.findall(r'https?://[^\s]+', action_data)
        details["contains_urls"] = urls[:3]  # Limit to 3 URLs
        
        # Check for errors
        if any(word in action_data.lower() for word in ['error', 'failed', 'exception', 'timeout']):
            details["contains_errors"] = True
        
        # Extract element references
        element_patterns = [r"element\s*[\"\']([^\"\']*)[\"\']", r"button\s*[\"\']([^\"\']*)[\"\']", r"input\s*[\"\']([^\"\']*)[\"\']"]
        for pattern in element_patterns:
            matches = re.findall(pattern, action_data, re.IGNORECASE)
            details["contains_elements"].extend(matches[:2])  # Limit elements
        
        return details
    
    def extract_result_summary(self, result_data: str) -> str:
        """Extract a concise summary from result data."""
        if not result_data or result_data == "N/A":
            return "No result available"
        
        lines = result_data.split('\n')
        first_line = lines[0].strip()
        
        # Look for specific result patterns
        if 'success' in first_line.lower():
            return "Action completed successfully"
        elif 'failed' in first_line.lower() or 'error' in first_line.lower():
            return "Action failed"
        elif 'found' in first_line.lower():
            return "Element found"
        elif 'loaded' in first_line.lower():
            return "Page loaded"
        elif 'clicked' in first_line.lower():
            return "Click performed"
        elif 'typed' in first_line.lower():
            return "Text entered"
        elif '[]' in first_line or 'empty' in first_line.lower():
            return "No results returned"
        else:
            # Truncate long results
            return first_line[:60] + "..." if len(first_line) > 60 else first_line
    
    def parse_result_details(self, result_data: str) -> dict:
        """Parse result data into structured details."""
        if not result_data or result_data == "N/A":
            return {}
        
        details = {
            "raw_result": result_data,
            "result_lines": result_data.split('\n')[:5],  # First 5 lines
            "contains_data": len(result_data) > 10,
            "is_empty_result": '[]' in result_data or 'empty' in result_data.lower(),
            "contains_errors": False,
            "element_count": 0
        }
        
        # Check for errors
        if any(word in result_data.lower() for word in ['error', 'failed', 'exception', 'timeout']):
            details["contains_errors"] = True
        
        # Count elements or results
        if '[' in result_data and ']' in result_data:
            # Try to count items in list-like results
            try:
                import json
                if result_data.strip().startswith('['):
                    parsed = json.loads(result_data)
                    if isinstance(parsed, list):
                        details["element_count"] = len(parsed)
            except:
                # Count commas as rough estimate
                details["element_count"] = result_data.count(',')
        
        return details
    
    def classify_action_type(self, action_data: str) -> str:
        """Classify the type of action being performed."""
        if not action_data or action_data == "N/A":
            return "unknown"
        
        action_lower = action_data.lower()
        
        if any(word in action_lower for word in ['navigate', 'goto', 'visit']):
            return "navigation"
        elif any(word in action_lower for word in ['click', 'tap', 'press']):
            return "interaction"
        elif any(word in action_lower for word in ['type', 'input', 'enter', 'fill']):
            return "input"
        elif any(word in action_lower for word in ['scroll', 'swipe']):
            return "scroll"
        elif any(word in action_lower for word in ['wait', 'pause', 'sleep']):
            return "wait"
        elif any(word in action_lower for word in ['screenshot', 'capture', 'image']):
            return "capture"
        elif any(word in action_lower for word in ['search', 'find', 'locate']):
            return "search"
        elif any(word in action_lower for word in ['extract', 'get', 'read']):
            return "extraction"
        else:
            return "other"
    
    def determine_success_status(self, result_data: str) -> str:
        """Determine if the action was successful based on result data."""
        if not result_data or result_data == "N/A":
            return "unknown"
        
        result_lower = result_data.lower()
        
        if any(word in result_lower for word in ['success', 'completed', 'done', 'found']):
            return "success"
        elif any(word in result_lower for word in ['failed', 'error', 'exception', 'timeout', 'not found']):
            return "failed"
        elif '[]' in result_data or 'empty' in result_lower or 'none' in result_lower:
            return "empty"
        elif len(result_data.strip()) > 0:
            return "completed"
        else:
            return "unknown"
    
    async def execute_task(self, target_url: str, task_description: str, screenshot_instructions: list, task_id: str):
        """Execute browser automation task directly."""
        task_details = {
            "target_url": target_url,
            "task_description": task_description,
            "screenshot_instructions": screenshot_instructions
        }
        
        # Update task status
        task_storage[task_id]["status"] = "running"
        task_storage[task_id]["progress"] = "Setting up logging..."
        
        # Setup comprehensive logging
        logger, detailed_log_path = self.setup_detailed_logging(task_id)
        
        # Setup stdout/stderr capture
        original_stdout, original_stderr, stdout_capture, stderr_capture, stdout_log_path, stderr_log_path = self.capture_stdout_stderr(task_id)
        
        logger.info(f"=== STARTING AGENT EXECUTION FOR TASK {task_id} ===")
        logger.info(f"Target URL: {target_url}")
        logger.info(f"Task Description: {task_description}")
        logger.info(f"Screenshot Instructions: {len(screenshot_instructions)} items")
        
        # Construct detailed task for browser agent with enhanced logging instructions
        full_task = f"""
        Navigate to: {target_url}
        
        Task: {task_description}
        
        ENHANCED LOGGING INSTRUCTIONS:
        1. Use log_action(message) to log what you are doing at each step with detailed context
           Example: "I am now navigating to the YouTube homepage to begin the search task"
        
        2. Use log_observation(message) to log what you see and understand about the page
           Example: "I can see the YouTube homepage with a search box in the center and trending videos below"
        
        3. Use log_decision(message) to log your reasoning and decision-making process
           Example: "I need to search for '{task_description.split()[4] if len(task_description.split()) > 4 else 'target term'}' so I will click on the search box and type the query"
        
        4. Use take_screenshot_now(description) whenever something important happens
           Example: take_screenshot_now("Homepage loaded before search")
        
        5. Use navigate_and_log(url) when navigating to track URL access
        
        6. Use log_element_interaction(element, action) when interacting with page elements
           Example: log_element_interaction("search box", "clicking to focus")
        
        7. Use extract_and_log(data_type, content) when extracting information
           Example: extract_and_log("search results", "Found relevant videos and channels")
        
        IMPORTANT: Be very detailed and descriptive in your logging so we can track every step of your reasoning and actions!
        """
        
        if screenshot_instructions:
            full_task += "\nAdditional Screenshot Requirements:"
            for i, instr in enumerate(screenshot_instructions):
                full_task += f"\n{i+1}. {instr.get('step_description', 'N/A')} (save as {instr.get('filename', f'screenshot_{i+1}.png')})"
        
        full_task += "\n\nRemember: Use the enhanced logging functions throughout your execution to provide comprehensive insights into your AI decision-making process!"
        
        logger.info(f"Enhanced Task Prompt Created: {len(full_task)} characters")
        logger.info(f"Target URL: {target_url}")
        logger.info(f"Task Description: {task_description[:100]}...")
        
        try:
            # Create browser agent
            task_storage[task_id]["progress"] = "Initializing browser agent..."
            logger.info("Creating browser agent...")
            browser_agent = await self.create_browser_agent(full_task, task_id)
            logger.info("Browser agent created successfully")
            
            # Execute the task
            task_storage[task_id]["progress"] = "Executing automation task..."
            logger.info("Starting agent.run() execution...")
            
            # Capture initial screenshot
            logger.info("Capturing initial screenshot...")
            initial_screenshot_path, initial_screenshot_url = await self.capture_manual_screenshot(browser_agent, task_id, "initial")
            
            # The agent execution will output to our captured stdout/stderr
            history = await browser_agent.run()
            
            # Capture final screenshot
            logger.info("Capturing final screenshot...")
            final_screenshot_path, final_screenshot_url = await self.capture_manual_screenshot(browser_agent, task_id, "final")
            
            logger.info("Agent execution completed")
            logger.info(f"History type: {type(history)}")
            logger.info(f"History length: {len(list(history)) if history else 0}")
            
            # Save results and screenshots
            task_storage[task_id]["progress"] = "Saving results and screenshots..."
            logger.info("Processing execution results...")
            results = self.save_execution_results(history, task_details, task_id)
            
            # Add manual screenshots to results
            if initial_screenshot_path:
                results["screenshots"].append(initial_screenshot_path)
                results["screenshot_urls"].append(initial_screenshot_url)
                logger.info(f"Added initial screenshot: {initial_screenshot_path}")
                
            if final_screenshot_path:
                results["screenshots"].append(final_screenshot_path)
                results["screenshot_urls"].append(final_screenshot_url)
                logger.info(f"Added final screenshot: {final_screenshot_path}")
            
            logger.info("Results processed successfully")
            
            # Close browser
            logger.info("Closing browser...")
            await browser_agent.browser.close()
            logger.info("Browser closed")
            
            # Update task status
            task_storage[task_id]["status"] = "completed"
            task_storage[task_id]["end_time"] = datetime.now().isoformat()
            task_storage[task_id]["results"] = results
            
            # Add log file paths to results
            results["detailed_log_file"] = str(detailed_log_path)
            results["stdout_log_file"] = str(stdout_log_path)
            results["stderr_log_file"] = str(stderr_log_path)
            
            # Add agent thoughts log file and session summary
            if hasattr(browser_agent, '_custom_logger'):
                results["agent_thoughts_file"] = str(browser_agent._custom_logger.log_file)
                # Log session summary for comprehensive insights
                browser_agent._custom_logger.log_session_summary()
            
            logger.info(f"=== TASK {task_id} COMPLETED SUCCESSFULLY ===")
            
            return results
            
        except Exception as e:
            logger.error(f"ERROR during task execution: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            error_result = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "task_details": task_details,
                "success": False,
                "error": str(e),
                "execution_steps": [],
                "screenshots": [],
                "screenshot_urls": [],
                "detailed_log_file": str(detailed_log_path),
                "stdout_log_file": str(stdout_log_path),
                "stderr_log_file": str(stderr_log_path)
            }
            
            # Add agent thoughts log file if available and log session summary
            if 'browser_agent' in locals() and hasattr(browser_agent, '_custom_logger'):
                error_result["agent_thoughts_file"] = str(browser_agent._custom_logger.log_file)
                # Log session summary even for failed tasks for debugging
                browser_agent._custom_logger.log_session_summary()
            
            # Update task status
            task_storage[task_id]["status"] = "failed"
            task_storage[task_id]["end_time"] = datetime.now().isoformat()
            task_storage[task_id]["error"] = str(e)
            task_storage[task_id]["results"] = error_result
            
            logger.info(f"=== TASK {task_id} FAILED ===")
            
            return error_result
            
        finally:
            # Restore original stdout/stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            
            # Log final captured output
            logger.info("=== CAPTURED STDOUT ===")
            logger.info(stdout_capture.getvalue())
            logger.info("=== CAPTURED STDERR ===")
            logger.info(stderr_capture.getvalue())
            logger.info("=== END OF EXECUTION LOG ===")
            
            # Close logger handlers
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    async def capture_manual_screenshot(self, browser_agent, task_id: str, step_name: str):
        """Manually capture a screenshot from the browser agent."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_filename = f"{task_id}_{step_name}_{timestamp}.png"
            screenshot_path = self.screenshots_dir / screenshot_filename
            screenshot_url = f"/screenshots/{screenshot_filename}"
            
            # Try to get screenshot from browser using Browser API
            if hasattr(browser_agent, 'browser') and browser_agent.browser:
                try:
                    # Method 1: Try browser.get_current_page()
                    if hasattr(browser_agent.browser, 'get_current_page'):
                        current_page = await browser_agent.browser.get_current_page()
                        if current_page:
                            screenshot_data = await current_page.screenshot()
                            with open(screenshot_path, 'wb') as f:
                                f.write(screenshot_data)
                            print(f"✅ Manual screenshot captured via get_current_page: {screenshot_filename}")
                            return str(screenshot_path), screenshot_url
                except Exception as e:
                    print(f"❌ Method 1 failed: {e}")
                
                # Method 2: Try browser.browser_context.pages
                try:
                    if hasattr(browser_agent.browser, 'browser_context'):
                        pages = browser_agent.browser.browser_context.pages
                        if pages:
                            page = pages[0]  # Get first page
                            screenshot_data = await page.screenshot()
                            with open(screenshot_path, 'wb') as f:
                                f.write(screenshot_data)
                            print(f"✅ Manual screenshot captured via browser_context: {screenshot_filename}")
                            return str(screenshot_path), screenshot_url
                except Exception as e:
                    print(f"❌ Method 2 failed: {e}")
            
            print(f"❌ Could not capture manual screenshot: no accessible browser page found")
            return None, None
            
        except Exception as e:
            print(f"❌ Error capturing manual screenshot: {e}")
            return None, None

# Results analysis function (non-decorated for direct use)
def analyze_results_direct(execution_results: dict, original_instructions: dict) -> dict:
    """Analyze browser automation results and generate comprehensive report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_id = execution_results.get("task_id", "unknown")
    
    logs_dir = Path("./operation_logs")
    logs_dir.mkdir(exist_ok=True)
    
    review_report = {
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
        "original_instructions": original_instructions,
        "execution_summary": {
            "success": execution_results.get("success", False),
            "steps_completed": len(execution_results.get("execution_steps", [])),
            "screenshots_captured": len(execution_results.get("screenshots", [])),
            "error": execution_results.get("error")
        },
        "detailed_analysis": {
            "conversation_length": len(execution_results.get("full_conversation", [])),
            "screenshot_analysis": "Screenshots captured at key moments" if execution_results.get("screenshots") else "No screenshots captured"
        },
        "recommendations": [],
        "compliance_check": {}
    }
    
    # Analyze task completion
    task_desc = original_instructions.get("task_description", "")
    execution_steps = execution_results.get("execution_steps", [])
    
    # Improved URL access detection using multiple methods
    target_url = original_instructions.get("target_url", "")
    url_accessed = False
    
    # Method 1: Check enhanced steps for navigation actions
    enhanced_steps = execution_results.get("enhanced_steps", [])
    for step in enhanced_steps:
        if isinstance(step, dict) and "actions" in step:
            for action in step.get("actions", []):
                if (action.get("type") == "navigate" and 
                    action.get("details", {}).get("url", "").startswith(target_url.rstrip("/"))):
                    url_accessed = True
                    break
        if url_accessed:
            break
    
    # Method 2: Check execution steps for embedded action data (more reliable)
    if not url_accessed:
        for step in execution_steps:
            # Check if step has actions embedded (common in newer format)
            if "actions" in step:
                for action in step.get("actions", []):
                    if (action.get("type") == "navigate" and 
                        action.get("details", {}).get("url", "").startswith(target_url.rstrip("/"))):
                        url_accessed = True
                        break
            if url_accessed:
                break
    
    # Method 3: Check results content for navigation indicators
    if not url_accessed:
        for step in execution_steps:
            results_data = step.get("results", [])
            if isinstance(results_data, list):
                for result in results_data:
                    content = result.get("content", "") if isinstance(result, dict) else str(result)
                    if ("navigated to" in content.lower() and target_url.lower() in content.lower()):
                        url_accessed = True
                        break
            if url_accessed:
                break
    
    # Method 4: Fallback to checking regular execution steps for navigation indicators
    if not url_accessed:
        for step in execution_steps:
            action_text = step.get("action", "").lower()
            result_text = step.get("result", "").lower()
            
            # Check for navigation patterns in action or result
            if ("navigate" in action_text or "goto" in action_text or 
                target_url.lower() in action_text or
                "navigated to" in result_text or 
                target_url.lower() in result_text):
                url_accessed = True
                break
    
    # Method 5: Check if any step contains the target domain
    if not url_accessed and target_url:
        try:
            from urllib.parse import urlparse
            target_domain = urlparse(target_url).netloc.lower()
            
            for step in execution_steps:
                step_text = f"{step.get('action', '')} {step.get('result', '')}".lower()
                if target_domain in step_text:
                    url_accessed = True
                    break
        except Exception:
            pass  # If URL parsing fails, skip this method
    
    review_report["compliance_check"]["target_url_accessed"] = url_accessed
    
    # Check screenshot requirements
    required_screenshots = original_instructions.get("screenshot_instructions", [])
    captured_screenshots = execution_results.get("screenshots", [])
    
    review_report["compliance_check"]["screenshots_captured"] = {
        "required": len(required_screenshots),
        "captured": len(captured_screenshots),
        "meets_requirements": len(captured_screenshots) >= len(required_screenshots) if required_screenshots else True
    }
    
    # Generate recommendations based on analysis
    if not execution_results.get("success", False):
        review_report["recommendations"].append("Task execution failed - check error logs")
    
    if not url_accessed:
        review_report["recommendations"].append(f"Target URL {target_url} may not have been properly accessed")
    
    if required_screenshots and len(captured_screenshots) < len(required_screenshots):
        review_report["recommendations"].append("Not all required screenshots were captured")
    
    # Positive recommendations for successful tasks
    if execution_results.get("success", False):
        if url_accessed:
            review_report["recommendations"].append("Task appears to have completed successfully")
            review_report["recommendations"].append(f"Target URL {target_url} was successfully accessed")
        
        if captured_screenshots:
            review_report["recommendations"].append(f"Successfully captured {len(captured_screenshots)} screenshots")
        
        steps_count = len(execution_steps)
        if steps_count > 0:
            review_report["recommendations"].append(f"Completed {steps_count} execution steps")
    
    # Save review report
    review_file = logs_dir / f"review_report_{task_id}_{timestamp}.json"
    try:
        with open(review_file, 'w') as f:
            json.dump(review_report, f, indent=2, default=str)
        review_report["review_file"] = str(review_file)
    except Exception as e:
        review_report["error"] = f"Error saving review report: {e}"
    
    return review_report

# Results analysis tool (decorated version for potential tool registry use)
@tool
def analyze_results(execution_results: dict, original_instructions: dict) -> dict:
    """Analyze browser automation results and generate comprehensive report."""
    return analyze_results_direct(execution_results, original_instructions)

# Custom tool for agent logging
class AgentLogger:
    """Custom tool for the browser agent to log information and take screenshots with enhanced tracking."""
    
    def __init__(self, logs_dir: Path, task_id: str):
        self.logs_dir = logs_dir
        self.task_id = task_id
        self.log_file = logs_dir / f"agent_thoughts_{task_id}.txt"
        self.screenshots_dir = logs_dir / "screenshots"
        self.screenshot_count = 0
        self.action_count = 0
        self.observation_count = 0
        self.decision_count = 0
        self.error_count = 0
        self.success_count = 0
        
        # Initialize log file with header
        self._initialize_log_file()
        
    def _initialize_log_file(self):
        """Initialize the log file with session header."""
        header = f"""=== AI AGENT EXECUTION LOG ===
Task ID: {self.task_id}
Session Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(header)
            f.flush()
        print(f"📝 Initialized agent log: {self.log_file}")
        
    def log_thought(self, message: str, category: str = "INFO") -> str:
        """Enhanced logging with categorization and counters."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update counters based on message type
        if "ACTION:" in message:
            self.action_count += 1
            icon = "⚡"
        elif "OBSERVATION:" in message:
            self.observation_count += 1
            icon = "👁️"
        elif "DECISION:" in message:
            self.decision_count += 1
            icon = "🧭"
        elif "ERROR:" in message or "❌" in message:
            self.error_count += 1
            icon = "❌"
        elif "SUCCESS:" in message or "✅" in message:
            self.success_count += 1
            icon = "✅"
        else:
            icon = "💭"
        
        # Format log entry with enhanced structure
        log_entry = f"[{timestamp}] {icon} {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            f.flush()
        
        # Enhanced console output with category
        print(f"{icon} [{category}] Agent Log: {message}")
        return f"Logged: {message}"
    
    def log_step_start(self, step_number: int, description: str) -> str:
        """Log the start of a new execution step."""
        message = f"STEP {step_number} START: {description}"
        separator = "-" * 50
        full_message = f"\n{separator}\n{message}\n{separator}"
        return self.log_thought(full_message, "STEP")
    
    def log_step_end(self, step_number: int, success: bool, duration: float = None) -> str:
        """Log the completion of an execution step."""
        status = "SUCCESS" if success else "FAILED"
        duration_str = f" (Duration: {duration:.2f}s)" if duration else ""
        message = f"STEP {step_number} {status}{duration_str}"
        return self.log_thought(message, "STEP")
    
    def log_navigation(self, url: str, success: bool = True) -> str:
        """Log navigation actions with URL tracking."""
        status = "✅ Successfully navigated to" if success else "❌ Failed to navigate to"
        message = f"NAVIGATION: {status} {url}"
        return self.log_thought(message, "NAV")
    
    def log_interaction(self, element: str, action: str, success: bool = True) -> str:
        """Log element interactions."""
        status = "✅" if success else "❌"
        message = f"INTERACTION: {status} {action} on '{element}'"
        return self.log_thought(message, "INTERACT")
    
    def log_extraction(self, data_type: str, content: str, success: bool = True) -> str:
        """Log data extraction actions."""
        status = "✅" if success else "❌"
        content_preview = content[:100] + "..." if len(content) > 100 else content
        message = f"EXTRACTION: {status} Extracted {data_type}: {content_preview}"
        return self.log_thought(message, "EXTRACT")
    
    def log_error(self, error_type: str, error_message: str) -> str:
        """Log errors with enhanced formatting."""
        message = f"ERROR: {error_type} - {error_message}"
        return self.log_thought(message, "ERROR")
    
    def log_session_summary(self) -> str:
        """Log a summary of the entire session."""
        summary = f"""\n{'='*50}
SESSION SUMMARY:
- Actions: {self.action_count}
- Observations: {self.observation_count}
- Decisions: {self.decision_count}
- Successes: {self.success_count}
- Errors: {self.error_count}
- Screenshots: {self.screenshot_count}
Session End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}\n"""
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(summary)
            f.flush()
        
        print(f"📊 Session Summary: {self.action_count} actions, {self.screenshot_count} screenshots, {self.error_count} errors")
        return "Session summary logged"
    
    def save_screenshot(self, description: str = "screenshot") -> str:
        """Save a screenshot with description."""
        self.screenshot_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.task_id}_manual_{self.screenshot_count}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        
        self.log_thought(f"Taking screenshot: {description}")
        
        # Return the filename for the agent to know
        return f"Screenshot request saved: {filename} - {description}"
    
    def get_screenshot_path(self, description: str = "screenshot"):
        """Get the path where a screenshot should be saved."""
        self.screenshot_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.task_id}_agent_{self.screenshot_count}_{timestamp}.png"
        return self.screenshots_dir / filename, f"/screenshots/{filename}"

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Website Testing Agent API",
        "version": "1.0.0",
        "endpoints": {
            "POST /execute-test": "Execute browser automation test",
            "GET /task-status/{task_id}": "Get task execution status",
            "GET /task-results/{task_id}": "Get task execution results",
            "POST /analyze-results/{task_id}": "Analyze task results",
            "GET /screenshots/{filename}": "Serve screenshot files",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/execute-test", response_model=Dict)
async def execute_test(instructions: TestInstructions, background_tasks: BackgroundTasks):
    """Execute browser automation test."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    # Generate unique task ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Initialize task status
    task_storage[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "start_time": datetime.now().isoformat(),
        "progress": "Task queued for execution",
        "instructions": instructions.model_dump()
    }
    
    # Execute task in background
    executor = BrowserExecutor()
    background_tasks.add_task(
        executor.execute_task,
        instructions.target_url,
        instructions.task_description,
        [instr.model_dump() for instr in instructions.screenshot_instructions],
        task_id
    )
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Task queued for execution",
        "check_status_url": f"/task-status/{task_id}"
    }

@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get task execution status."""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = task_storage[task_id]
    return {
        "task_id": task_id,
        "status": task_info["status"],
        "progress": task_info.get("progress"),
        "start_time": task_info.get("start_time"),
        "end_time": task_info.get("end_time"),
        "error": task_info.get("error")
    }

@app.get("/task-results/{task_id}")
async def get_task_results(task_id: str):
    """Get task execution results."""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = task_storage[task_id]
    
    if task_info["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail=f"Task is still {task_info['status']}")
    
    return task_info.get("results", {})

# Store reference to the direct function to avoid tool issues
analyze_results_tool = analyze_results_direct

@app.post("/analyze-results/{task_id}")
async def analyze_results_endpoint(task_id: str):
    """Analyze task execution results."""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = task_storage[task_id]
    
    if task_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task must be completed before analysis")
    
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    
    try:
        # Get execution results and original instructions
        execution_results = task_info.get("results", {})
        original_instructions = task_info.get("instructions", {})
        
        # First generate our own detailed analysis
        analysis_result_data = analyze_results_tool(execution_results, original_instructions)
        
        # Create simplified prompt that avoids JSON serialization issues
        task_success = execution_results.get("success", False)
        steps_count = len(execution_results.get("execution_steps", []))
        screenshots_count = len(execution_results.get("screenshots", []))
        task_error = execution_results.get("error", "None")
        target_url = original_instructions.get("target_url", "Unknown")
        task_description = original_instructions.get("task_description", "No description")
        
        # Key analysis insights
        url_accessed = analysis_result_data.get("compliance_check", {}).get("target_url_accessed", False)
        recommendations = analysis_result_data.get("recommendations", [])
        
        prompt = f"""You are a website testing analysis expert. Analyze this browser automation test:

TEST OVERVIEW:
- Target URL: {target_url}
- Task: {task_description[:200]}...
- Success: {task_success}
- Steps Completed: {steps_count}
- Screenshots Captured: {screenshots_count}
- Error: {task_error}
- Target URL Accessed: {url_accessed}

KEY FINDINGS:
{chr(10).join(f'- {rec}' for rec in recommendations[:5])}

Provide a comprehensive analysis with:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (bullet points)
3. **Recommendations** (actionable items)
4. **Compliance Status** (Pass/Fail assessment)

Keep response clear and actionable."""
        
        try:
            # Create Portia config with minimal settings to avoid telemetry issues
            # Try multiple approaches to disable telemetry
            import os
            original_telemetry = os.environ.get('PORTIA_TELEMETRY_ENABLED')
            os.environ['PORTIA_TELEMETRY_ENABLED'] = 'false'
            
            try:
                google_config = Config.from_default(
                    llm_provider=LLMProvider.GOOGLE,
                    default_model="google/gemini-2.0-flash",
                    google_api_key=GEMINI_API_KEY
                )
                
                # Try to disable telemetry through multiple methods
                for attr in ['telemetry_enabled', 'enable_telemetry', 'telemetry']:
                    try:
                        setattr(google_config, attr, False)
                    except:
                        pass
                
                # Create Portia agent for analysis
                portia_agent = Portia(config=google_config)
            finally:
                # Restore original telemetry setting
                if original_telemetry is not None:
                    os.environ['PORTIA_TELEMETRY_ENABLED'] = original_telemetry
                else:
                    os.environ.pop('PORTIA_TELEMETRY_ENABLED', None)
            
            # Run analysis with error handling and telemetry error suppression
            import warnings
            import logging
            
            # Temporarily suppress telemetry-related warnings/errors
            telemetry_logger = logging.getLogger('portia.telemetry.telemetry_service')
            original_level = telemetry_logger.level
            telemetry_logger.setLevel(logging.CRITICAL)
            
            try:
                plan_run = portia_agent.run(prompt)
            finally:
                # Restore original logging level
                telemetry_logger.setLevel(original_level)
            
            # Extract analysis from plan run with enhanced error handling
            ai_analysis = None
            extraction_method = "unknown"
            
            # First, let's check what Portia actually returned by examining all attributes
            print(f"[DEBUG] Portia plan_run type: {type(plan_run)}")
            print(f"[DEBUG] Portia plan_run attributes: {[attr for attr in dir(plan_run) if not attr.startswith('_')]}")
            
            # Method 1: Try outputs (most likely location for step results)
            if hasattr(plan_run, 'outputs') and plan_run.outputs:
                print(f"[DEBUG] Found outputs: {type(plan_run.outputs)}")
                
                # Check if outputs has final_output
                if hasattr(plan_run.outputs, 'final_output') and plan_run.outputs.final_output:
                    final_output = plan_run.outputs.final_output
                    print(f"[DEBUG] final_output type: {type(final_output)}")
                    
                    # Check if it's a LocalDataValue object with value attribute
                    if hasattr(final_output, 'value') and final_output.value:
                        content = str(final_output.value).strip()
                        print(f"[DEBUG] Found final_output.value: {len(content)} chars")
                        print(f"[DEBUG] Content preview: {content[:200]}...")
                        if len(content) > 20:
                            ai_analysis = content
                            extraction_method = "outputs_final_output_value"
                            print(f"[SUCCESS] Successfully extracted from outputs.final_output.value: {len(content)} characters")
                    
                    # Fallback: try string conversion of final_output
                    if not ai_analysis:
                        content = str(final_output).strip()
                        if len(content) > 20 and not content.startswith('LocalDataValue'):
                            ai_analysis = content
                            extraction_method = "outputs_final_output_string"
                            print(f"[SUCCESS] Successfully extracted from outputs.final_output string: {len(content)} characters")
                
                # Check if outputs has step_outputs
                if not ai_analysis and hasattr(plan_run.outputs, 'step_outputs') and plan_run.outputs.step_outputs:
                    step_outputs = plan_run.outputs.step_outputs
                    print(f"[DEBUG] Found step_outputs: {type(step_outputs)}")
                    
                    if isinstance(step_outputs, dict):
                        # Look for analysis or other relevant keys
                        for key in ['$analysis', 'analysis', 'result', 'output']:
                            if key in step_outputs:
                                step_output = step_outputs[key]
                                print(f"[DEBUG] Found step_outputs[{key}]: {type(step_output)}")
                                
                                # Check if it's a LocalDataValue object
                                if hasattr(step_output, 'value') and step_output.value:
                                    content = str(step_output.value).strip()
                                    print(f"[DEBUG] Found step_outputs[{key}].value: {len(content)} chars")
                                    if len(content) > 20:
                                        ai_analysis = content
                                        extraction_method = f"outputs_step_outputs_{key}_value"
                                        print(f"[SUCCESS] Successfully extracted from outputs.step_outputs[{key}].value: {len(content)} characters")
                                        break
                                elif isinstance(step_output, str) and len(step_output.strip()) > 20:
                                    ai_analysis = step_output.strip()
                                    extraction_method = f"outputs_step_outputs_{key}"
                                    print(f"[SUCCESS] Successfully extracted from outputs.step_outputs[{key}]: {len(ai_analysis)} characters")
                                    break
                
                # Last resort for outputs: try string conversion
                if not ai_analysis:
                    content = str(plan_run.outputs).strip()
                    # Look for the analysis content within the string representation
                    if "**Executive Summary:**" in content or "**Key Findings:**" in content:
                        # Extract just the analysis part
                        start_markers = ["Here's an analysis", "**Executive Summary:**"]
                        end_markers = ["', summary=", "final_output=", "LocalDataValue"]
                        
                        analysis_start = -1
                        for marker in start_markers:
                            pos = content.find(marker)
                            if pos >= 0:
                                analysis_start = pos
                                break
                        
                        if analysis_start >= 0:
                            # Find the end of the analysis
                            analysis_end = len(content)
                            for marker in end_markers:
                                pos = content.find(marker, analysis_start + 50)  # Look after the start
                                if pos >= 0:
                                    analysis_end = pos
                                    break
                            
                            extracted = content[analysis_start:analysis_end].strip()
                            # Clean up any trailing artifacts
                            extracted = extracted.replace("\\n", "\n").replace("\\'", "'")
                            if len(extracted) > 50:
                                ai_analysis = extracted
                                extraction_method = "outputs_string_parsed"
                                print(f"[SUCCESS] Successfully parsed analysis from outputs string: {len(extracted)} characters")
            
            # Method 2: Try final_output with relaxed validation
            if not ai_analysis and hasattr(plan_run, 'final_output') and plan_run.final_output:
                content = str(plan_run.final_output).strip()
                print(f"[DEBUG] final_output content: {content[:200]}...")
                # Much more relaxed validation - just check it's not empty and not a clear object repr
                if (len(content) > 5 and 
                    not content.startswith('Run(id=') and 
                    not content.startswith('PlanRun(id=') and
                    not content.startswith('<') and
                    content != 'set' and
                    'object at 0x' not in content):
                    ai_analysis = content
                    extraction_method = "final_output"
                    print(f"[SUCCESS] Successfully extracted from final_output: {len(content)} characters")
            
            # Method 3: Try output attribute
            if not ai_analysis and hasattr(plan_run, 'output') and plan_run.output:
                content = str(plan_run.output).strip()
                print(f"[DEBUG] output content: {content[:200]}...")
                if (len(content) > 5 and 
                    not content.startswith('Run(id=') and 
                    not content.startswith('PlanRun(id=') and
                    not content.startswith('<') and
                    'object at 0x' not in content):
                    ai_analysis = content
                    extraction_method = "output"
                    print(f"[SUCCESS] Successfully extracted from output: {len(content)} characters")
            
            # Method 4: Try steps extraction
            if not ai_analysis and hasattr(plan_run, 'steps') and plan_run.steps:
                print(f"[DEBUG] Found {len(plan_run.steps)} steps")
                for i, step in enumerate(plan_run.steps):
                    step_attrs = [attr for attr in dir(step) if not attr.startswith('_')]
                    print(f"[DEBUG] Step {i} attributes: {step_attrs}")
                    
                    # Check multiple possible attributes
                    for attr in ['output', 'result', 'content', 'response', 'text']:
                        if hasattr(step, attr):
                            attr_value = getattr(step, attr)
                            if attr_value:
                                content = str(attr_value).strip()
                                if (len(content) > 5 and 
                                    not content.startswith('Run(id=') and 
                                    not content.startswith('PlanRun(id=')):
                                    ai_analysis = content
                                    extraction_method = f"step_{i}_{attr}"
                                    print(f"[SUCCESS] Successfully extracted from step {i}.{attr}: {len(content)} characters")
                                    break
                    if ai_analysis:
                        break
            
            # Method 5: Try additional object attributes
            if not ai_analysis:
                for attr in ['result', 'content', 'response', 'text', 'analysis', 'summary']:
                    if hasattr(plan_run, attr):
                        attr_value = getattr(plan_run, attr)
                        if attr_value:
                            content = str(attr_value).strip()
                            print(f"[DEBUG] {attr} content: {content[:100]}...")
                            if (len(content) > 5 and 
                                not content.startswith('Run(id=') and 
                                not content.startswith('PlanRun(id=') and
                                'object at 0x' not in content):
                                ai_analysis = content
                                extraction_method = f"attribute_{attr}"
                                print(f"[SUCCESS] Successfully extracted from {attr}: {len(content)} characters")
                                break
            
            # Validate final result
            if ai_analysis and len(ai_analysis.strip()) >= 5:
                print(f"[SUCCESS] Final analysis extracted successfully!")
                print(f"[SUCCESS] Extraction method: {extraction_method}")
                print(f"[SUCCESS] Content length: {len(ai_analysis)} characters")
                print(f"[SUCCESS] Content preview: {ai_analysis[:300]}...")
            else:
                raise Exception(f"Portia returned insufficient analysis content. Method: {extraction_method}")
                
        except Exception as portia_error:
            print(f"[WARNING] Portia analysis failed, using fallback: {portia_error}")
            print(f"[DEBUG] Error type: {type(portia_error).__name__}")
            
            # Enhanced fallback analysis with better context
            ai_analysis = f"""**AI Analysis Report**

**Executive Summary:**
The browser automation task {'completed successfully' if task_success else 'encountered issues'} with {steps_count} execution steps and {screenshots_count} screenshots captured. {'The target URL was accessed properly' if url_accessed else 'There may have been issues accessing the target URL'}.

**Key Findings:**
• Task Status: {'Success' if task_success else 'Failed'}
• Execution Steps: {steps_count} completed
• Visual Documentation: {screenshots_count} screenshots captured
• Target URL Access: {'Successful' if url_accessed else 'Failed or incomplete'}
• Error Status: {'No errors detected' if task_success else 'Errors occurred during execution'}

**Recommendations:**
{chr(10).join(f'• {rec}' for rec in recommendations) if recommendations else '• Review execution logs for detailed information' + chr(10) + '• Check screenshots for visual confirmation' + chr(10) + '• Verify task completion manually if needed'}

**Compliance Status:**
• Overall Assessment: {'PASS' if task_success and url_accessed else 'NEEDS REVIEW'}
• Target URL Compliance: {'PASS' if url_accessed else 'FAIL'}
• Task Execution: {'PASS' if task_success else 'FAIL'}

---
*Note: This analysis was generated using fallback mode due to AI analysis system limitations. The task execution results above are still accurate.*"""
        
        # Store analysis results
        analysis_result = {
            "task_id": task_id,
            "analysis_content": ai_analysis,
            "detailed_analysis": analysis_result_data,
            "timestamp": datetime.now().isoformat(),
            "analysis_method": "portia" if 'portia_error' not in locals() else "fallback"
        }
        
        task_storage[task_id]["analysis"] = analysis_result
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        
        # Create a basic analysis as final fallback
        try:
            execution_results = task_info.get("results", {})
            original_instructions = task_info.get("instructions", {})
            
            fallback_analysis = {
                "task_id": task_id,
                "analysis_content": f"""**Analysis Report (Fallback Mode)**

**Executive Summary:**
Basic analysis completed for task {task_id}. The system encountered technical difficulties with the advanced AI analysis but was able to extract basic information.

**Key Findings:**
- Task Status: {execution_results.get('success', 'Unknown')}
- Steps Executed: {len(execution_results.get('execution_steps', []))}
- Screenshots: {len(execution_results.get('screenshots', []))}
- Target URL: {original_instructions.get('target_url', 'Not specified')}

**Recommendations:**
- Review the detailed execution logs for more information
- Check system configuration if analysis continues to fail
- Contact support if issues persist

**Compliance Status:**
Unable to perform full compliance check due to technical issues.""",
                "detailed_analysis": {"error": "Analysis system unavailable", "fallback_used": True},
                "timestamp": datetime.now().isoformat(),
                "analysis_method": "emergency_fallback"
            }
            
            task_storage[task_id]["analysis"] = fallback_analysis
            return fallback_analysis
            
        except Exception as final_error:
            print(f"❌ Even fallback analysis failed: {final_error}")
            raise HTTPException(status_code=500, detail=f"Analysis system unavailable: {str(e)}")

@app.get("/tasks")
async def list_tasks():
    """List all tasks and their statuses."""
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": info["status"],
                "start_time": info.get("start_time"),
                "end_time": info.get("end_time")
            }
            for task_id, info in task_storage.items()
        ]
    }

@app.get("/logs/{task_id}/stdout")
async def get_stdout_log(task_id: str):
    """Get stdout log file content for a task."""
    try:
        # Look for stdout log file
        stdout_file_pattern = f"agent_stdout_{task_id}_*.txt"
        stdout_file = None
        
        # Search in logs directory
        logs_dir = Path("./operation_logs")
        for file_path in logs_dir.glob(stdout_file_pattern):
            stdout_file = file_path
            break
        
        if not stdout_file or not stdout_file.exists():
            return "No stdout log file found for this task."
        
        # Read and return file content
        with open(stdout_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading stdout log: {str(e)}")

@app.get("/logs/{task_id}/detailed")
async def get_detailed_log(task_id: str):
    """Get detailed agent log file content for a task."""
    try:
        # Look for detailed log file
        detailed_file_pattern = f"detailed_agent_log_{task_id}_*.txt"
        detailed_file = None
        
        # Search in logs directory
        logs_dir = Path("./operation_logs")
        for file_path in logs_dir.glob(detailed_file_pattern):
            detailed_file = file_path
            break
        
        if not detailed_file or not detailed_file.exists():
            return "No detailed log file found for this task."
        
        # Read and return file content
        with open(detailed_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading detailed log: {str(e)}")

@app.get("/agent-thoughts/{task_id}")
async def get_agent_thoughts(task_id: str):
    """Get agent thoughts file content for a task."""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Look for agent thoughts file
        thoughts_file_pattern = f"agent_thoughts_{task_id}.txt"
        thoughts_file = None
        
        # Search in logs directory
        logs_dir = Path("./operation_logs")
        for file_path in logs_dir.glob(f"*{thoughts_file_pattern}*"):
            thoughts_file = file_path
            break
        
        if not thoughts_file or not thoughts_file.exists():
            return "No agent thoughts file found for this task."
        
        # Read and return file content
        with open(thoughts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading agent thoughts: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 