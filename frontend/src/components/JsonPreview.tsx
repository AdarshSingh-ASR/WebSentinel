import React, { useState } from 'react';
import { Copy, Check, Code } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { TestConfig } from '../types/TestConfig';
import toast from 'react-hot-toast';

interface JsonPreviewProps {
  config: TestConfig;
}

const JsonPreview: React.FC<JsonPreviewProps> = ({ config }) => {
  const [copied, setCopied] = useState(false);

  const formattedJson = JSON.stringify(config, null, 2);

  const handleCopy = () => {
    navigator.clipboard.writeText(formattedJson);
    setCopied(true);
    toast.success('JSON copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5 text-[#D9653B]" />
              Configuration Preview
            </CardTitle>
            <CardDescription>
              JSON representation of your test configuration
            </CardDescription>
          </div>
          <Button
            onClick={handleCopy}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4 text-green-400" />
                <span className="text-green-400">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" />
                Copy JSON
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="bg-[#252525] rounded-lg p-3 overflow-auto max-h-64">
          <pre className="text-xs font-mono text-[#A1A1A1] whitespace-pre-wrap break-words">
            {formattedJson}
          </pre>
        </div>
        
        <p className="mt-4 text-sm text-[#A1A1A1]">
          This configuration can be used with compatible web testing frameworks.
        </p>
      </CardContent>
    </Card>
  );
};

export default JsonPreview