import React from 'react';
import { Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { ScreenshotInstruction } from '../types/TestConfig';

interface ScreenshotInstructionFieldProps {
  instruction: ScreenshotInstruction;
  index: number;
  onChange: (index: number, field: keyof ScreenshotInstruction, value: string) => void;
  onRemove: (index: number) => void;
}

const ScreenshotInstructionField: React.FC<ScreenshotInstructionFieldProps> = ({
  instruction,
  index,
  onChange,
  onRemove
}) => {
  return (
    <div className="notion-surface p-4 animate-fadeIn">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-sm font-medium text-white">Screenshot {index + 1}</h4>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onRemove(index)}
          className="text-[#A1A1A1] hover:text-red-400 h-8 w-8 p-0 transition-colors"
          title="Remove screenshot"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
      
      <div className="space-y-3">
        <div className="space-y-2">
          <label htmlFor={`step-description-${index}`} className="text-sm font-medium text-white">
            Step Description
          </label>
          <Textarea
            id={`step-description-${index}`}
            value={instruction.step_description}
            onChange={(e) => onChange(index, 'step_description', e.target.value)}
            rows={2}
            placeholder="Describe when to take the screenshot..."
          />
        </div>
        
        <div className="space-y-2">
          <label htmlFor={`filename-${index}`} className="text-sm font-medium text-white">
            Filename
          </label>
          <Input
            id={`filename-${index}`}
            value={instruction.filename}
            onChange={(e) => onChange(index, 'filename', e.target.value)}
            placeholder="screenshot_name.png"
          />
        </div>
      </div>
    </div>
  );
};

export default ScreenshotInstructionField;