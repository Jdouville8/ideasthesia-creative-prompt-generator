import React from 'react';

const PromptDisplay = ({ prompt, genres }) => {
  // Function to parse markdown-style bold text
  const parseMarkdown = (text) => {
    if (!text) return null;
    
    // Split by **bold** markers
    const parts = text.split(/(\*\*.*?\*\*)/g);
    
    return parts.map((part, index) => {
      // Check if this part is wrapped in **
      if (part.startsWith('**') && part.endsWith('**')) {
        const boldText = part.slice(2, -2);
        return <strong key={index} className="font-semibold text-gray-900">{boldText}</strong>;
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Split content by lines and render with bold parsing and spacing
  const renderContent = () => {
    if (!prompt.content) return null;
    
    const lines = prompt.content.split('\n');
    const elements = [];
    
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      
      // Empty line - add spacing
      if (trimmedLine === '') {
        elements.push(<div key={`space-${index}`} className="h-4"></div>);
        return;
      }
      
      // Check if line starts with a bold section (like **Goal**: or **Exercise**:)
      const isSectionHeader = trimmedLine.match(/^\*\*[^*]+\*\*:/);
      
      // Add extra spacing before section headers (except the first one)
      if (isSectionHeader && elements.length > 0) {
        elements.push(<div key={`space-before-${index}`} className="h-3"></div>);
      }
      
      // Render the line with markdown parsing
      elements.push(
        <div key={index} className={trimmedLine.match(/^\d+\./) ? 'ml-4' : ''}>
          {parseMarkdown(line)}
        </div>
      );
      
      // Add spacing after section headers
      if (isSectionHeader) {
        elements.push(<div key={`space-after-${index}`} className="h-1"></div>);
      }
    });
    
    return elements;
  };

  return (
    <div className="bg-white rounded-lg shadow-xl p-8 animate-fadeIn">
      <h3 className="text-2xl font-bold text-gray-800 mb-4">
        {prompt.title}
      </h3>
      
      <div className="mb-4">
        <span className="text-sm text-gray-600">Genres: </span>
        {genres.map((genre, index) => (
          <span key={genre} className="inline-block bg-indigo-100 text-indigo-800 px-2 py-1 rounded-md text-sm mr-2">
            {genre}
          </span>
        ))}
      </div>
      
      <div className="text-gray-700 leading-relaxed mb-6">
        {renderContent()}
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-sm text-gray-600">Difficulty</p>
          <p className="font-semibold">{prompt.difficulty}</p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-sm text-gray-600">Suggested Word Count</p>
          <p className="font-semibold">{prompt.wordCount} words</p>
        </div>
      </div>
      
      {prompt.tips && prompt.tips.length > 0 && (
        <div>
          <h4 className="font-semibold text-gray-800 mb-2">Writing Tips:</h4>
          <ul className="space-y-2">
            {prompt.tips.map((tip, index) => (
              <li key={index} className="flex items-start">
                <span className="text-indigo-600 mr-2">•</span>
                <span className="text-gray-600 text-sm">{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default PromptDisplay;
