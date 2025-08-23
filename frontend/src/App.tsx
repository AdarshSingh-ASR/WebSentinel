import { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import Footer from './components/Footer';
import TestConfigForm from './components/TestConfigForm';
import { TestConfig } from './types/TestConfig';

interface TaskStatus {
  task_id: string;
  status: string;
  progress?: string;
  start_time?: string;
  end_time?: string;
  error?: string;
}

interface ExecutionStep {
  step_number: number;
  action: string;
  result: string;
  timestamp: string;
  screenshot_url?: string;
  screenshot?: string;
  action_type?: string;
  success?: boolean;
  duration?: number;
}

interface EnhancedStep {
  step_number: number;
  timestamp: string;
  action_summary: string;
  action_details: any;
  result_summary: string;
  result_details: any;
  action_type: string;
  success_status: string;
  screenshot_url?: string;
  errors: string[];
  metadata: any;
}

interface ExecutionResult {
  task_id: string;
  success: boolean;
  timestamp: string;
  task_details: any;
  execution_steps: ExecutionStep[];
  enhanced_steps?: EnhancedStep[];
  screenshots: string[];
  screenshot_urls: string[];
  full_conversation: any[];
  error?: string;
  log_file?: string;
  detailed_log_file?: string;
  stdout_log_file?: string;
  stderr_log_file?: string;
  agent_thoughts_file?: string;
}

interface AnalysisResult {
  task_id: string;
  analysis_content?: string;
  analysis_report?: string;
  detailed_analysis?: {
    execution_summary?: {
      success?: boolean;
      steps_completed?: number;
      screenshots_captured?: number;
    };
    compliance_check?: {
      target_url_accessed?: boolean;
    };
    recommendations?: string[];
  };
  timestamp: string;
  analysis_method?: string;
}

const API_BASE_URL = 'http://localhost:8000';



function App() {
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [pollingInterval, setPollingInterval] = useState<number | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Poll task status
  useEffect(() => {
    let interval: number;
    
    if (currentTaskId && isExecuting) {
      interval = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/task-status/${currentTaskId}`);
          if (response.ok) {
            const status = await response.json();
            setTaskStatus(status);
            
            if (status.status === 'completed' || status.status === 'failed') {
              setIsExecuting(false);
              
              if (status.status === 'completed') {
                const resultsResponse = await fetch(`${API_BASE_URL}/task-results/${currentTaskId}`);
                if (resultsResponse.ok) {
                  const results = await resultsResponse.json();
                  setExecutionResult(results);
                }
              }
            }
          }
        } catch (error) {
          console.error('Error polling task status:', error);
          setIsExecuting(false);
        }
      }, 2000);
    }
    
    return () => clearInterval(interval);
  }, [currentTaskId, isExecuting]);

  const executeTest = async (testConfig: TestConfig) => {
    console.log('executeTest called with:', testConfig); // Debug log
    try {
      setIsExecuting(true);
      setTaskStatus(null);
      setExecutionResult(null);
      setAnalysisResult(null);
      
      console.log('Starting test execution with config:', testConfig);
      
      const response = await fetch(`${API_BASE_URL}/execute-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testConfig),
      });

      console.log('API response status:', response.status); // Debug log

      if (response.ok) {
        const data = await response.json();
        console.log('API response data:', data); // Debug log
        setCurrentTaskId(data.task_id);
        setTaskStatus({ 
          task_id: data.task_id, 
          status: data.status,
          progress: 'Task queued for execution'
        });

        // Start polling for status updates
        const taskId = data.task_id;
        const interval = setInterval(async () => {
          try {
            const statusResponse = await fetch(`${API_BASE_URL}/task-status/${taskId}`);
            if (statusResponse.ok) {
              const status = await statusResponse.json();
              console.log('Task status update:', status);
              setTaskStatus(status);

              if (status.status === 'completed' || status.status === 'failed') {
                clearInterval(interval);
                setPollingInterval(null);
                setIsExecuting(false);

                if (status.status === 'completed') {
                  // Fetch execution results
                  const resultsResponse = await fetch(`${API_BASE_URL}/task-results/${taskId}`);
                  if (resultsResponse.ok) {
                    const executionResults = await resultsResponse.json();
                    console.log('Execution results:', executionResults);
                    setExecutionResult(executionResults);
                  }
                }
              }
            }
          } catch (error) {
            console.error('Error polling task status:', error);
          }
        }, 2000); // Poll every 2 seconds

        setPollingInterval(interval);
      } else {
        const errorText = await response.text();
        console.error('API error:', response.status, errorText);
        throw new Error(`Failed to start test execution: ${response.status}`);
      }
    } catch (error) {
      console.error('Error executing test:', error);
      setIsExecuting(false);
    }
  };

  const analyzeResults = async () => {
    if (!currentTaskId) return;

    try {
      setIsAnalyzing(true);
      
      // Clear any previous analysis to show loading state
      setAnalysisResult(null);
      
      const response = await fetch(`${API_BASE_URL}/analyze-results/${currentTaskId}`, {
        method: 'POST',
      });

      if (response.ok) {
        const analysis = await response.json();
        console.log('Analysis result received:', analysis);
        
        // Validate the analysis result before setting it
        if (analysis && (analysis.analysis_content || analysis.analysis_report || analysis.detailed_analysis)) {
          setAnalysisResult(analysis);
        } else {
          console.warn('Received incomplete analysis result:', analysis);
          // Create a fallback analysis result
          setAnalysisResult({
            task_id: currentTaskId,
            analysis_content: `⚠️ **Analysis Incomplete**

The analysis completed but returned incomplete data. This may indicate a temporary issue with the AI analysis system.

**Status:** Analysis system responded but with incomplete data
**Recommendation:** Please try running the analysis again

**Note:** Your task execution completed successfully - this only affects the analysis report generation.`,
            timestamp: new Date().toISOString(),
            analysis_method: 'incomplete_response'
          });
        }
      } else {
        const errorText = await response.text();
        console.error('Analysis API error:', response.status, errorText);
        
        // Create an error analysis result instead of throwing
        setAnalysisResult({
          task_id: currentTaskId,
          analysis_content: `❌ **Analysis Failed**

The AI analysis system encountered an error while processing your results.

**Error Details:**
- Status Code: ${response.status}
- Error: ${errorText || 'Unknown server error'}

**Troubleshooting:**
- Check that the task completed successfully above
- Try running the analysis again in a few moments
- Verify your internet connection
- Contact support if the issue persists

**Note:** Your task execution was successful - only the AI analysis failed.`,
          timestamp: new Date().toISOString(),
          analysis_method: 'error_fallback'
        });
      }
    } catch (error) {
      console.error('Error analyzing results:', error);
      
      // Create a network error analysis result
      setAnalysisResult({
        task_id: currentTaskId || 'unknown',
        analysis_content: `🚫 **Analysis Network Error**

There was a network error while trying to analyze your results.

**Error Details:**
- ${error instanceof Error ? error.message : 'Unknown network error'}

**Troubleshooting:**
- Check your internet connection
- Verify the API server is running
- Try refreshing the page and running analysis again
- Contact support if connectivity issues persist

**Note:** This is a connectivity issue and does not affect your task execution results.`,
        timestamp: new Date().toISOString(),
        analysis_method: 'network_error'
      });
    } finally {
      setIsAnalyzing(false);
    }
  };



  return (
    <div className="min-h-screen flex flex-col bg-primary-50">
      <Toaster position="top-right" />
      <Header />
      
      <main className="flex-grow flex-shrink-0 pb-16">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-primary-900 mb-2">AI Automated Web Testing</h1>
            <p className="text-lg text-primary-600 max-w-3xl mx-auto">
              Create and execute automated web testing scenarios powered by AI.
            </p>
          </div>
          
          <TestConfigForm 
            onExecuteTest={executeTest}
            isExecuting={isExecuting}
          />

          {/* Task Status */}
          {taskStatus && (
            <div className="max-w-7xl mx-auto mt-8 px-4 sm:px-6 lg:px-8">
              <div className="bg-white rounded-xl shadow-sm p-6 border border-primary-200">
                <h3 className="text-lg font-semibold text-primary-900 mb-4">Execution Status</h3>
                <div className="space-y-2">
                  <p><span className="font-medium">Task ID:</span> {taskStatus.task_id}</p>
                  <p><span className="font-medium">Status:</span> 
                    <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                      taskStatus.status === 'completed' ? 'bg-green-100 text-green-800' :
                      taskStatus.status === 'failed' ? 'bg-red-100 text-red-800' :
                      taskStatus.status === 'running' ? 'bg-blue-100 text-blue-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {taskStatus.status}
                    </span>
                  </p>
                  {taskStatus.progress && <p><span className="font-medium">Progress:</span> {taskStatus.progress}</p>}
                  {taskStatus.error && <p className="text-red-600"><span className="font-medium">Error:</span> {taskStatus.error}</p>}
                </div>
              </div>
            </div>
          )}

          {/* Execution Results */}
          {executionResult && (
            <div className="max-w-7xl mx-auto mt-8 px-4 sm:px-6 lg:px-8">
              <div className="bg-white rounded-xl shadow-sm p-6 border border-primary-200">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-semibold text-primary-900">📊 Execution Results</h3>
                  <button
                    onClick={analyzeResults}
                    disabled={isAnalyzing}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
                  >
                    {isAnalyzing ? '🔄 Analyzing...' : '🔍 Analyze Results'}
                  </button>
                </div>
                


                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-2xl font-bold text-primary-600 mb-1">
                      {executionResult.success ? '✅' : '❌'}
                    </div>
                    <div className="text-sm text-gray-600">Success</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-600 mb-1">
                      {executionResult.execution_steps?.length || 0}
                    </div>
                    <div className="text-sm text-gray-600">Steps</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-2xl font-bold text-purple-600 mb-1">
                      {executionResult.screenshot_urls?.length || 0}
                    </div>
                    <div className="text-sm text-gray-600">Screenshots</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <div className="text-2xl font-bold text-indigo-600 mb-1">
                      {executionResult.full_conversation?.length || 0}
                    </div>
                    <div className="text-sm text-gray-600">AI Messages</div>
                  </div>
                </div>

                {/* Screenshots Gallery */}
                {executionResult.screenshot_urls && executionResult.screenshot_urls.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-md font-semibold text-gray-900 mb-3">📸 Screenshots Captured</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {executionResult.screenshot_urls.map((screenshotUrl, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg overflow-hidden shadow-sm">
                          <img
                            src={`${API_BASE_URL}${screenshotUrl}`}
                            alt={`Screenshot ${index + 1}`}
                            className="w-full h-48 object-cover hover:scale-105 transition-transform cursor-pointer"
                            onClick={() => window.open(`${API_BASE_URL}${screenshotUrl}`, '_blank')}
                            onError={(e) => {
                              console.error('Failed to load screenshot:', screenshotUrl);
                              e.currentTarget.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><text y="50" font-size="12">Screenshot unavailable</text></svg>';
                            }}
                          />
                          <div className="p-3 bg-gray-50">
                            <div className="text-sm font-medium text-gray-700">Step {index + 1}</div>
                            <div className="text-xs text-gray-500">Click to view full size</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Execution Steps */}
                {executionResult.execution_steps && executionResult.execution_steps.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-md font-semibold text-gray-900 mb-3">🔄 Execution Steps</h4>
                    <div className="space-y-4 max-h-[600px] overflow-y-auto">
                      {executionResult.execution_steps.map((step, index) => {
                        // Enhanced step processing for better display
                        const actionType = step.action?.toLowerCase() || '';
                        const resultType = step.result?.toLowerCase() || '';
                        
                        // Determine step status
                        let stepStatus = 'unknown';
                        let statusIcon = '🔵';
                        let statusColor = 'text-gray-600';
                        
                        if (resultType.includes('success') || resultType.includes('completed') || resultType.includes('done')) {
                          stepStatus = 'success';
                          statusIcon = '✅';
                          statusColor = 'text-green-600';
                        } else if (resultType.includes('failed') || resultType.includes('error') || resultType.includes('timeout')) {
                          stepStatus = 'failed';
                          statusIcon = '❌';
                          statusColor = 'text-red-600';
                        } else if (resultType.includes('[]') || resultType.includes('empty')) {
                          stepStatus = 'empty';
                          statusIcon = '⚪';
                          statusColor = 'text-yellow-600';
                        } else if (step.result && step.result !== 'N/A' && step.result.length > 0) {
                          stepStatus = 'completed';
                          statusIcon = '✓';
                          statusColor = 'text-blue-600';
                        }
                        
                        // Determine action type for icon
                        let actionIcon = '🔧';
                        if (actionType.includes('navigate') || actionType.includes('goto')) {
                          actionIcon = '🧭';
                        } else if (actionType.includes('click') || actionType.includes('tap')) {
                          actionIcon = '💆';
                        } else if (actionType.includes('type') || actionType.includes('input')) {
                          actionIcon = '⌨️';
                        } else if (actionType.includes('scroll')) {
                          actionIcon = '📜';
                        } else if (actionType.includes('screenshot')) {
                          actionIcon = '📸';
                        } else if (actionType.includes('search')) {
                          actionIcon = '🔍';
                        }
                        
                        // Create action summary
                        const actionSummary = step.action && step.action !== 'N/A' 
                          ? (step.action.split('\n')[0].length > 80 
                             ? step.action.split('\n')[0].substring(0, 80) + '...' 
                             : step.action.split('\n')[0])
                          : 'No action specified';
                        
                        // Create result summary
                        const resultSummary = step.result && step.result !== 'N/A'
                          ? (step.result.split('\n')[0].length > 80
                             ? step.result.split('\n')[0].substring(0, 80) + '...'
                             : step.result.split('\n')[0])
                          : 'No result available';
                        
                        return (
                          <div key={index} className="border border-gray-200 rounded-xl p-5 bg-white hover:shadow-md transition-shadow">
                            {/* Step Header */}
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center space-x-3">
                                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-sm font-bold text-blue-600">
                                  {step.step_number}
                                </div>
                                <div>
                                  <div className="text-sm font-semibold text-gray-900 flex items-center space-x-2">
                                    <span>{actionIcon} Step {step.step_number}</span>
                                    <span className={`text-xs ${statusColor} flex items-center space-x-1`}>
                                      <span>{statusIcon}</span>
                                      <span className="uppercase tracking-wide">{stepStatus}</span>
                                    </span>
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    {new Date(step.timestamp).toLocaleString()}
                                  </div>
                                </div>
                              </div>
                              {step.screenshot_url && (
                                <div className="flex-shrink-0">
                                  <img
                                    src={`${API_BASE_URL}${step.screenshot_url}`}
                                    alt={`Step ${step.step_number} preview`}
                                    className="w-16 h-12 object-cover border rounded cursor-pointer hover:shadow-lg transition-shadow"
                                    onClick={() => window.open(`${API_BASE_URL}${step.screenshot_url}`, '_blank')}
                                    onError={(e) => {
                                      e.currentTarget.style.display = 'none';
                                    }}
                                  />
                                </div>
                              )}
                            </div>
                            
                            {/* Action Section */}
                            <div className="mb-4">
                              <div className="flex items-center space-x-2 mb-2">
                                <span className="text-xs font-semibold text-green-700 bg-green-50 px-2 py-1 rounded uppercase tracking-wide">
                                  ⚡ Action
                                </span>
                              </div>
                              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                <div className="text-sm font-medium text-green-800 mb-1">
                                  {actionSummary}
                                </div>
                                {step.action && step.action !== 'N/A' && step.action.split('\n').length > 1 && (
                                  <details className="mt-2">
                                    <summary className="text-xs text-green-600 cursor-pointer hover:text-green-800">
                                      Show full action details
                                    </summary>
                                    <div className="mt-2 p-2 bg-white rounded border text-xs text-gray-700 max-h-32 overflow-y-auto font-mono">
                                      {step.action}
                                    </div>
                                  </details>
                                )}
                              </div>
                            </div>
                            
                            {/* Result Section */}
                            <div>
                              <div className="flex items-center space-x-2 mb-2">
                                <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded uppercase tracking-wide">
                                  📊 Result
                                </span>
                              </div>
                              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                <div className="text-sm font-medium text-blue-800 mb-1">
                                  {resultSummary}
                                </div>
                                {step.result && step.result !== 'N/A' && step.result.split('\n').length > 1 && (
                                  <details className="mt-2">
                                    <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                                      Show full result details
                                    </summary>
                                    <div className="mt-2 p-2 bg-white rounded border text-xs text-gray-700 max-h-32 overflow-y-auto font-mono">
                                      {step.result}
                                    </div>
                                  </details>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* AI Conversation */}
                {executionResult.full_conversation && executionResult.full_conversation.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-md font-semibold text-gray-900 mb-3">💬 AI Conversation</h4>
                    <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
                      {executionResult.full_conversation.map((conv, index) => (
                        <div key={index} className="mb-2 p-2 bg-white rounded border">
                          <div className="flex justify-between items-start">
                            <span className="text-xs font-medium text-blue-600">Step {conv.step}</span>
                            <span className="text-xs text-gray-500">
                              {new Date(conv.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="text-sm text-gray-800 mt-1">{conv.model_output}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Log File Links */}
                {(executionResult.log_file || executionResult.detailed_log_file || executionResult.stdout_log_file || executionResult.agent_thoughts_file) && (
                  <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h4 className="text-sm font-medium text-blue-800 mb-2">📄 Generated Log Files</h4>
                    <div className="space-y-1 text-xs text-blue-700">
                      {executionResult.agent_thoughts_file && (
                        <div className="font-semibold">🤖 Agent thoughts & actions: {executionResult.agent_thoughts_file}</div>
                      )}
                      {executionResult.log_file && (
                        <div>• Execution results: {executionResult.log_file}</div>
                      )}
                      {executionResult.detailed_log_file && (
                        <div>• Detailed agent log: {executionResult.detailed_log_file}</div>
                      )}
                      {executionResult.stdout_log_file && (
                        <div>• Agent stdout: {executionResult.stdout_log_file}</div>
                      )}
                      {executionResult.stderr_log_file && (
                        <div>• Agent stderr: {executionResult.stderr_log_file}</div>
                      )}
                    </div>
                  </div>
                )}

                {/* Error Display */}
                {executionResult.error && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="text-sm font-medium text-red-800 mb-2">❌ Error Details</h4>
                    <p className="text-sm text-red-700">{executionResult.error}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Analysis Results */}
          {analysisResult && (
            <div className="max-w-7xl mx-auto mt-8 px-4 sm:px-6 lg:px-8">
              <div className="bg-white rounded-xl shadow-sm p-6 border border-primary-200">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-primary-900">🤖 AI Analysis Report</h3>
                  <div className="flex items-center space-x-3">
                    {/* Retry button for failed analyses */}
                    {analysisResult.analysis_method && 
                     ['error_fallback', 'network_error', 'incomplete_response', 'emergency_fallback'].includes(analysisResult.analysis_method) && (
                      <button
                        onClick={analyzeResults}
                        disabled={isAnalyzing}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm font-medium"
                      >
                        {isAnalyzing ? '🔄 Retrying...' : '🔄 Retry Analysis'}
                      </button>
                    )}
                    <div className="text-xs text-gray-500">
                      {analysisResult.analysis_method && (
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          analysisResult.analysis_method === 'portia' ? 'bg-green-100 text-green-800 border border-green-200' :
                          analysisResult.analysis_method === 'fallback' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                          analysisResult.analysis_method === 'emergency_fallback' ? 'bg-orange-100 text-orange-800 border border-orange-200' :
                          analysisResult.analysis_method === 'error_fallback' ? 'bg-red-100 text-red-800 border border-red-200' :
                          analysisResult.analysis_method === 'network_error' ? 'bg-red-100 text-red-800 border border-red-200' :
                          analysisResult.analysis_method === 'incomplete_response' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                          'bg-gray-100 text-gray-800 border border-gray-200'
                        }`}>
                          {analysisResult.analysis_method === 'portia' ? '✅ AI Powered' :
                           analysisResult.analysis_method === 'fallback' ? '⚠️ Fallback Mode' :
                           analysisResult.analysis_method === 'emergency_fallback' ? '🆘 Emergency Mode' :
                           analysisResult.analysis_method === 'error_fallback' ? '❌ Error Recovery' :
                           analysisResult.analysis_method === 'network_error' ? '🚫 Network Error' :
                           analysisResult.analysis_method === 'incomplete_response' ? '⚠️ Incomplete' :
                           '🔧 Basic Analysis'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  {(() => {
                    // Handle different types of analysis content with comprehensive validation
                    let content = analysisResult.analysis_content || analysisResult.analysis_report || 'No analysis content available';
                    
                    // Enhanced detection of raw object representations
                    const isRawObject = typeof content === 'string' && (
                      content.startsWith('Run(') ||
                      content.startsWith('PlanRun(') ||
                      content.includes('id=prun-') ||
                      content.includes('state=PlanRunState') ||
                      content.includes('plan_id=plan-') ||
                      content.includes('current_step_index=') ||
                      content.includes('final_output=set') ||
                      content.includes('final_output=<') ||
                      (content.includes('object at 0x') && content.includes('Run')) ||
                      (content.length < 30 && content.includes('Run('))
                    );
                    
                    // Enhanced detection of other problematic content
                    const isProblematicContent = typeof content === 'string' && (
                      content.trim().length < 10 ||
                      content === 'None' ||
                      content === 'null' ||
                      content === '{}' ||
                      content === '[]' ||
                      content.startsWith('<__main__') ||
                      content.startsWith('<portia')
                    );
                    
                    if (isRawObject || isProblematicContent) {
                      content = `⚠️ **Analysis Processing Issue**

The AI analysis encountered a technical issue and returned raw system data instead of the formatted report. This typically indicates a temporary processing problem with the AI analysis engine.

**Fallback Summary:**
- Task Status: ${analysisResult.detailed_analysis?.execution_summary?.success ? 'Completed Successfully ✅' : 'Needs Review ⚠️'}
- URL Access: ${analysisResult.detailed_analysis?.compliance_check?.target_url_accessed ? 'Successful ✅' : 'Failed ❌'}
- Steps: ${analysisResult.detailed_analysis?.execution_summary?.steps_completed || 'Unknown'}
- Screenshots: ${analysisResult.detailed_analysis?.execution_summary?.screenshots_captured || 'Unknown'}

**Recommendations:**
${analysisResult.detailed_analysis?.recommendations?.map((rec: string) => `- ${rec}`).join('\n') || '- Review execution results manually\n- Retry analysis if needed'}

**Next Steps:**
- Try running the analysis again by clicking the "Analyze Results" button
- Check the detailed technical analysis section below for raw data
- Contact support if this issue persists

**Note:** The execution results above show the actual task completion status. This display issue does not affect the underlying task execution.`;
                    }
                    
                    // Ensure content is a string for further processing
                    if (typeof content !== 'string') {
                      try {
                        // Try to extract meaningful content from objects
                        if (content && typeof content === 'object') {
                          const contentObj = content as any; // Type assertion for object access
                          if (contentObj.analysis || contentObj.content || contentObj.text) {
                            content = contentObj.analysis || contentObj.content || contentObj.text;
                          } else {
                            content = JSON.stringify(content, null, 2);
                          }
                        } else {
                          content = String(content);
                        }
                      } catch (e) {
                        content = 'Error processing analysis content';
                      }
                    }
                    
                    return (
                      <div className="max-h-96 overflow-y-auto">
                        {content.includes('**') || content.includes('##') ? (
                          // Render markdown-style content
                          <div className="prose prose-sm max-w-none">
                            {content.split('\n').map((line: string, index: number) => {
                              if (line.startsWith('**') && line.endsWith('**')) {
                                return (
                                  <h4 key={index} className="font-semibold text-gray-900 mt-4 mb-2">
                                    {line.replace(/\*\*/g, '')}
                                  </h4>
                                );
                              } else if (line.startsWith('##')) {
                                return (
                                  <h3 key={index} className="font-bold text-gray-900 mt-6 mb-3 text-lg">
                                    {line.replace(/##/g, '')}
                                  </h3>
                                );
                              } else if (line.startsWith('- ')) {
                                return (
                                  <div key={index} className="flex items-start space-x-2 mb-1">
                                    <span className="text-primary-600 mt-2">•</span>
                                    <span className="text-gray-700">{line.substring(2)}</span>
                                  </div>
                                );
                              } else if (line.trim()) {
                                return (
                                  <p key={index} className="text-gray-700 mb-2">
                                    {line}
                                  </p>
                                );
                              }
                              return <br key={index} />;
                            })}
                          </div>
                        ) : (
                          // Fallback to preformatted text
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                            {content}
                          </pre>
                        )}
                      </div>
                    );
                  })()}
                </div>
                
                {/* Show timestamp */}
                {analysisResult.timestamp && (
                  <div className="mt-3 text-xs text-gray-500 text-right">
                    Generated: {new Date(analysisResult.timestamp).toLocaleString()}
                  </div>
                )}
                
                {/* Show detailed analysis if available */}
                {analysisResult.detailed_analysis && (
                  <details className="mt-4">
                    <summary className="text-sm text-primary-600 cursor-pointer hover:text-primary-800 font-medium">
                      📊 View Detailed Technical Analysis
                    </summary>
                    <div className="mt-3 p-4 bg-gray-100 rounded-lg">
                      <pre className="text-xs text-gray-600 overflow-x-auto">
                        {JSON.stringify(analysisResult.detailed_analysis, null, 2)}
                      </pre>
                    </div>
                  </details>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}

export default App