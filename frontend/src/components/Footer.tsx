import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="border-t border-[#A1A1A1]/10 bg-[#1E1E1E] py-8 px-8 mt-16">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-[#A1A1A1] mb-4 md:mb-0">
            © {new Date().getFullYear()} WebSentinel. All rights reserved.
          </p>
          <div className="flex space-x-8">
            <a href="#" className="text-sm text-[#A1A1A1] hover:text-white transition-colors duration-200">
              Privacy Policy
            </a>
            <a href="#" className="text-sm text-[#A1A1A1] hover:text-white transition-colors duration-200">
              Terms of Service
            </a>
            <a href="#" className="text-sm text-[#A1A1A1] hover:text-white transition-colors duration-200">
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer