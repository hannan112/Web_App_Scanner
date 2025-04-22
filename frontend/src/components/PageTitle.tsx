import React from 'react';

interface PageTitleProps {
  title: string;
  subtitle?: string;
}

const PageTitle: React.FC<PageTitleProps> = ({ title, subtitle }) => {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-semibold text-gray-700 hover:text-gray-800 transition-colors">{title}</h1>
      {subtitle && (
        <p className="mt-1 text-sm text-gray-500 hover:text-gray-600 transition-colors">{subtitle}</p>
      )}
    </div>
  );
};

export default PageTitle;
