import React from 'react';
import { Activity } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="border-b border-[#A1A1A1]/10 bg-[#1E1E1E] py-6 px-8">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-[#D9653B]">
            <Activity className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-xl font-medium text-white tracking-tight">WebSentinel</h1>
        </div>
        <nav>
          <ul className="flex space-x-8">
            <li>
              <a href="#" className="text-sm text-[#A1A1A1] hover:text-white transition-colors duration-200">
                Documentation
              </a>
            </li>
            <li>
              <a href="#" className="text-sm text-[#A1A1A1] hover:text-white transition-colors duration-200">
                Examples
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;