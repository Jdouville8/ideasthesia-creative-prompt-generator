import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const SoundDesignPromptDisplay = ({ prompt }) => {
  const { isDarkMode } = useTheme();
  const [copied, setCopied] = useState(false);
  
  // Timer state
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [initialTime, setInitialTime] = useState(null);

  // Parse estimated time to seconds
  useEffect(() => {
    if (prompt.estimatedTime) {
      const match = prompt.estimatedTime.match(/(\d+)\s*minute/i);
      if (match) {
        const minutes = parseInt(match[1]);
        const seconds = minutes * 60;
        setInitialTime(seconds);
        setTimeRemaining(seconds);
      }
    }
  }, [prompt.estimatedTime]);

  // Timer countdown effect
  useEffect(() => {
    let interval = null;
    if (isTimerRunning && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(time => {
          if (time <= 1) {
            setIsTimerRunning(false);
            return 0;
          }
          return time - 1;
        });
      }, 1000);
    } else if (!isTimerRunning && interval) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning, timeRemaining]);

  const formatTime = (seconds) => {
    if (seconds === null) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStartPause = () => {
    setIsTimerRunning(!isTimerRunning);
  };

  const handleReset = () => {
    setIsTimerRunning(false);
    setTimeRemaining(initialTime);
  };

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

  const getTimerColor = () => {
    if (timeRemaining === null || initialTime === null) return '';
    const percentage = (timeRemaining / initialTime) * 100;
    if (percentage > 50) return isDarkMode ? 'text-emerald-400' : 'text-emerald-600';
    if (percentage > 25) return isDarkMode ? 'text-yellow-400' : 'text-yellow-600';
    return isDarkMode ? 'text-red-400' : 'text-red-600';
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

      {/* Timer and Stats */}
      <div className="grid grid-cols-1 gap-4 mb-6">
        {/* Timer Display */}
        <div className={`p-4 rounded-lg border-2 ${isDarkMode ? 'bg-gray-900 border-gray-700' : 'bg-gray-50 border-gray-200'}`}>
          <div className="flex items-center justify-between mb-3">
            <p className={`text-sm font-semibold ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Timer</p>
            <p className={`text-xs ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>Estimated: {prompt.estimatedTime}</p>
          </div>
          
          {/* Timer Display */}
          <div className="text-center mb-4">
            <div className={`text-5xl font-bold font-mono ${getTimerColor()}`}>
              {formatTime(timeRemaining)}
            </div>
          </div>

          {/* Timer Controls */}
          <div className="flex gap-2 justify-center">
            <button
              onClick={handleStartPause}
              disabled={timeRemaining === 0}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                timeRemaining === 0
                  ? isDarkMode
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : isTimerRunning
                  ? isDarkMode
                    ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                    : 'bg-yellow-500 hover:bg-yellow-600 text-white'
                  : isDarkMode
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : 'bg-emerald-500 hover:bg-emerald-600 text-white'
              }`}
            >
              {timeRemaining === 0 ? "Time's Up!" : isTimerRunning ? "Pause" : "Start"}
            </button>
            <button
              onClick={handleReset}
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                isDarkMode
                  ? 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              }`}
            >
              🔄 Reset
            </button>
          </div>
        </div>

        {/* Difficulty */}
        <div className={`p-3 rounded ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Difficulty</p>
          <p className={`font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{prompt.difficulty}</p>
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
