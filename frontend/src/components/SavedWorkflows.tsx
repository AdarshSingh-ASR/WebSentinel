import React from 'react';
import { SavedWorkflow } from '../types/TestConfig';
import { Trash2, FileCode, Calendar, Link } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

interface SavedWorkflowsProps {
  workflows: SavedWorkflow[];
  onLoadWorkflow: (workflow: SavedWorkflow) => void;
  onDeleteWorkflow: (id: string) => void;
}

const SavedWorkflows: React.FC<SavedWorkflowsProps> = ({ workflows, onLoadWorkflow, onDeleteWorkflow }) => {
  if (workflows.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <FileCode className="h-12 w-12 text-[#A1A1A1] mb-4" />
          <p className="text-sm text-[#A1A1A1] text-center">
            No saved workflows yet. Create and save a workflow to see it here.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileCode className="h-5 w-5 text-[#D9653B]" />
          Saved Workflows
        </CardTitle>
        <CardDescription>
          Load previously saved test configurations
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {workflows.map((workflow) => (
            <div
              key={workflow.id}
              className="notion-surface p-2 hover:border-[#D9653B]/30 transition-colors group"
            >
              <div className="flex justify-between items-start mb-1">
                <h3 className="text-sm font-medium text-white truncate pr-2">{workflow.name}</h3>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    onClick={() => onLoadWorkflow(workflow)}
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-[#A1A1A1] hover:text-[#D9653B]"
                    title="Load workflow"
                  >
                    <FileCode className="h-3 w-3" />
                  </Button>
                  <Button
                    onClick={() => onDeleteWorkflow(workflow.id)}
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-[#A1A1A1] hover:text-red-400"
                    title="Delete workflow"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs text-[#A1A1A1]">
                  <Calendar className="h-3 w-3" />
                  {new Date(workflow.created_at).toLocaleDateString()}
                </div>
                
                <div className="flex items-center gap-2 text-xs text-[#A1A1A1]">
                  <Link className="h-3 w-3" />
                  <span className="truncate">{workflow.config.target_url}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default SavedWorkflows;