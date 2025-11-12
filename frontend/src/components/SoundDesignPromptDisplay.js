import React, { useState } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const SoundDesignPromptDisplay = ({ prompt }) => {
  const { isDarkMode } = useTheme();
  const [copied, setCopied] = useState(false);

  const parseMarkdown = (text) => {
    if (!text) return null;
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const boldText = part.slice(2, -2);
        return <strong key={index} className={`font-semibold ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{boldText}</strong>;
      }
      return <span key={index}>{part}</span>;
    });
  };

  const renderContent = () => {
    if (!prompt.content) return null;
    const lines = prompt.content.split('\n');
    const elements = [];

    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      if (trimmedLine === '') {
        elements.push(<div key={`space-${index}`} className="h-4"></div>);
        return;
      }
      const isSectionHeader = trimmedLine.match(/^\*\*[^*]+\*\*:/);
      const isNumberedList = trimmedLine.match(/^\d+\./);

      if (isSectionHeader && elements.length > 0) {
        elements.push(<div key={`space-before-${index}`} className="h-3"></div>);
      }
      elements.push(
        <div key={index} className={isNumberedList ? 'ml-4' : ''}>
          {parseMarkdown(line)}
        </div>
      );
      if (isSectionHeader) {
        elements.push(<div key={`space-after-${index}`} className="h-1"></div>);
      }
    });
    return elements;
  };

  const handleCopyToClipboard = () => {
    const textToCopy = `${prompt.title}\n\n${prompt.content}\n\nTips:\n${prompt.tips.map(tip => `- ${tip}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`rounded-lg shadow-xl p-8 animate-fadeIn transition-colors duration-200 ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
      {/* Header with synth icon */}
      <div className="flex items-center justify-between mb-4">
        <h3 className={`text-2xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
          {prompt.title}
        </h3>
        <button
          onClick={handleCopyToClipboard}
          className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
            isDarkMode
              ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
          }`}
        >
          {copied ? '✓ Copied!' : '📋 Copy'}
        </button>
      </div>

      {/* Synthesizer and Exercise Type badges */}
      <div className="mb-6 flex flex-wrap gap-2">
        <span className={`inline-block px-3 py-1 rounded-md text-sm font-medium ${isDarkMode ? 'bg-indigo-900 text-indigo-200' : 'bg-indigo-100 text-indigo-800'}`}>
          🎹 {prompt.synthesizer}
        </span>
        <span className={`inline-block px-3 py-1 rounded-md text-sm font-medium ${isDarkMode ? 'bg-purple-900 text-purple-200' : 'bg-purple-100 text-purple-800'}`}>
          {prompt.exerciseType === 'technical' ? '⚙️ Technical' : '🎨 Creative'}
        </span>
      </div>

      {/* Main content */}
      <div className={`leading-relaxed mb-6 ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
        {renderContent()}
      </div>

      {/* Difficulty and Time */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className={`p-3 rounded ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Difficulty</p>
          <p className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{prompt.difficulty}</p>
        </div>
        <div className={`p-3 rounded ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Estimated Time</p>
          <p className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{prompt.estimatedTime}</p>
        </div>
      </div>

      {/* Tips section */}
      {prompt.tips && prompt.tips.length > 0 && (
        <div className={`border-t-2 pt-6 ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <h4 className={`font-semibold mb-3 ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>Sound Design Tips:</h4>
          <ul className="space-y-2">
            {prompt.tips.map((tip, index) => (
              <li key={index} className="flex items-start">
                <span className={isDarkMode ? 'text-indigo-400 mr-2' : 'text-indigo-600 mr-2'}>•</span>
                <span className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SoundDesignPromptDisplay;
