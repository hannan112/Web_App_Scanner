import React from 'react';

interface PageTitleProps {
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const PageTitle: React.FC<PageTitleProps> = ({ 
  children, 
  size = 'lg',
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl'
  };

  return (
    <h1 className={`font-semibold text-gray-800 mb-6 ${sizeClasses[size]} ${className}`}>
      {children}
    </h1>
  );
};

export default PageTitle;
