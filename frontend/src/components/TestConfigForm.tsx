import React, { useState, useEffect } from 'react';
import { Plus, Save, Play } from 'lucide-react';
import toast from 'react-hot-toast';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import ScreenshotInstructionField from './ScreenshotInstructionField';
import JsonPreview from './JsonPreview';
import SavedWorkflows from './SavedWorkflows';
import { TestConfig, ScreenshotInstruction, SavedWorkflow } from '../types/TestConfig';

const initialScreenshotInstruction: ScreenshotInstruction = {
  step_description: '',
  filename: ''
};

const initialTestConfig: TestConfig = {
  target_url: '',
  task_description: '',
  screenshot_instructions: [{ ...initialScreenshotInstruction }]
};

interface TestConfigFormProps {
  onExecuteTest?: (testConfig: TestConfig) => void;
  isExecuting?: boolean;
}

const TestConfigForm: React.FC<TestConfigFormProps> = ({ onExecuteTest, isExecuting = false }) => {
  const [testConfig, setTestConfig] = useState<TestConfig>(initialTestConfig);
  const [workflowName, setWorkflowName] = useState('');
  const [isFormValid, setIsFormValid] = useState(false);
  const [formTouched, setFormTouched] = useState(false);
  const [savedWorkflows, setSavedWorkflows] = useState<SavedWorkflow[]>(() => {
    const saved = localStorage.getItem('savedWorkflows');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    const validateForm = () => {
      const { target_url, task_description, screenshot_instructions } = testConfig;
      
      const basicFieldsValid = target_url.trim() !== '' && task_description.trim() !== '';
      
      const filledScreenshots = screenshot_instructions.filter(
        instruction => 
          instruction.step_description.trim() !== '' || 
          instruction.filename.trim() !== ''
      );
      
      const screenshotsValid = filledScreenshots.every(
        instruction => 
          instruction.step_description.trim() !== '' && 
          instruction.filename.trim() !== ''
      );
      
      return basicFieldsValid && screenshotsValid;
    };
    
    setIsFormValid(validateForm());
  }, [testConfig]);

  const handleBasicFieldChange = (field: keyof Omit<TestConfig, 'screenshot_instructions'>, value: string) => {
    setTestConfig(prev => ({ ...prev, [field]: value }));
    if (!formTouched) setFormTouched(true);
  };

  const handleScreenshotChange = (index: number, field: keyof ScreenshotInstruction, value: string) => {
    setTestConfig(prev => {
      const updatedInstructions = [...prev.screenshot_instructions];
      updatedInstructions[index] = { ...updatedInstructions[index], [field]: value };
      return { ...prev, screenshot_instructions: updatedInstructions };
    });
    if (!formTouched) setFormTouched(true);
  };

  const addScreenshotInstruction = () => {
    setTestConfig(prev => ({
      ...prev,
      screenshot_instructions: [...prev.screenshot_instructions, { ...initialScreenshotInstruction }]
    }));
  };

  const removeScreenshotInstruction = (index: number) => {
    setTestConfig(prev => {
      const updatedInstructions = prev.screenshot_instructions.filter((_, i) => i !== index);
      
      // Ensure at least one screenshot instruction remains
      if (updatedInstructions.length === 0) {
        return {
          ...prev,
          screenshot_instructions: [{ ...initialScreenshotInstruction }]
        };
      }
      
      return {
        ...prev,
        screenshot_instructions: updatedInstructions
      };
    });
    if (!formTouched) setFormTouched(true);
  };

  const handleExecuteTest = () => {
    if (isFormValid && onExecuteTest) {
      const cleanedConfig = {
        ...testConfig,
        screenshot_instructions: testConfig.screenshot_instructions.filter(
          instruction => 
            instruction.step_description.trim() !== '' && 
            instruction.filename.trim() !== ''
        )
      };
      onExecuteTest(cleanedConfig);
    }
  };

  const handleSaveWorkflow = () => {
    if (!workflowName.trim()) {
      toast.error('Please enter a workflow name');
      return;
    }

    if (!isFormValid) {
      toast.error('Please fill in all required fields first');
      return;
    }

    const newWorkflow: SavedWorkflow = {
      id: Date.now().toString(),
      name: workflowName.trim(),
      config: {
        ...testConfig,
        screenshot_instructions: testConfig.screenshot_instructions.filter(
          instruction => 
            instruction.step_description.trim() !== '' && 
            instruction.filename.trim() !== ''
        )
      },
      created_at: new Date().toISOString()
    };

    const updatedWorkflows = [...savedWorkflows, newWorkflow];
    setSavedWorkflows(updatedWorkflows);
    localStorage.setItem('savedWorkflows', JSON.stringify(updatedWorkflows));
    
    setWorkflowName('');
    toast.success('Workflow saved successfully!');
  };

  const handleLoadWorkflow = (workflow: SavedWorkflow) => {
    setTestConfig(workflow.config);
    setFormTouched(true);
    toast.success(`Loaded workflow: ${workflow.name}`);
  };

  const handleDeleteWorkflow = (workflowId: string) => {
    const updatedWorkflows = savedWorkflows.filter(w => w.id !== workflowId);
    setSavedWorkflows(updatedWorkflows);
    localStorage.setItem('savedWorkflows', JSON.stringify(updatedWorkflows));
    toast.success('Workflow deleted');
  };

  return (
    <div className="max-w-7xl mx-auto p-8">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left Column - Main Configuration Form */}
        <div className="lg:col-span-3 space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Test Configuration</CardTitle>
              <CardDescription>
                Configure your website automation test parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
          {/* Target URL */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">
              Target URL
            </label>
            <Input
              type="url"
              placeholder="https://example.com"
              value={testConfig.target_url}
              onChange={(e) => handleBasicFieldChange('target_url', e.target.value)}
              className="w-full"
            />
            <p className="text-xs text-[#A1A1A1]">
              The website URL to test
            </p>
          </div>

          {/* Task Description */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">
              Task Description
            </label>
            <Textarea
              placeholder="Describe what the automation should do..."
              value={testConfig.task_description}
              onChange={(e) => handleBasicFieldChange('task_description', e.target.value)}
              className="min-h-[120px] resize-y"
            />
            <p className="text-xs text-[#A1A1A1]">
              Detailed instructions for the AI agent
            </p>
          </div>

          {/* Screenshot Instructions */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-white">Screenshot Instructions</h3>
                <p className="text-xs text-[#A1A1A1] mt-1">
                  Specify when to capture screenshots during execution
                </p>
              </div>
              <Button
                onClick={addScreenshotInstruction}
                size="sm"
                variant="outline"
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Screenshot
              </Button>
            </div>

            <div className="space-y-3">
              {testConfig.screenshot_instructions.map((instruction, index) => (
                <ScreenshotInstructionField
                  key={index}
                  index={index}
                  instruction={instruction}
                  onChange={handleScreenshotChange}
                  onRemove={removeScreenshotInstruction}
                />
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-[#A1A1A1]/10">
            <Button
              onClick={handleExecuteTest}
              disabled={!isFormValid || isExecuting}
              className="flex items-center gap-2 flex-1"
            >
              <Play className="h-4 w-4" />
              {isExecuting ? 'Executing...' : 'Execute Test'}
            </Button>
            
            <div className="flex gap-2 sm:flex-none">
              <Input
                placeholder="Workflow name"
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="sm:w-48"
              />
              <Button
                onClick={handleSaveWorkflow}
                variant="outline"
                disabled={!isFormValid || !workflowName.trim()}
                className="flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                Save
              </Button>
            </div>
          </div>

          {/* Form Status */}
          {formTouched && (
            <div className="flex items-center gap-2">
              <Badge variant={isFormValid ? "success" : "destructive"}>
                {isFormValid ? "Valid" : "Invalid"}
              </Badge>
              <span className="text-xs text-[#A1A1A1]">
                {isFormValid 
                  ? "Configuration is ready to execute"
                  : "Please complete all required fields"
                }
              </span>
            </div>
          )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Configuration Preview and Saved Workflows */}
        <div className="lg:col-span-2 space-y-4">
          {/* JSON Preview */}
          <JsonPreview config={testConfig} />

          {/* Saved Workflows */}
          <SavedWorkflows
            workflows={savedWorkflows}
            onLoadWorkflow={handleLoadWorkflow}
            onDeleteWorkflow={handleDeleteWorkflow}
          />
        </div>
      </div>
    </div>
  );
};

export default TestConfigForm;