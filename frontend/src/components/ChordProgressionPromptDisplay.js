import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ChordProgressionPromptDisplay = ({ progression }) => {
  const { isDarkMode } = useTheme();
  const [copied, setCopied] = useState(false);

  // Timer state
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [initialTime, setInitialTime] = useState(null);

  // Parse estimated time to seconds
  useEffect(() => {
    if (progression.estimatedTime) {
      const match = progression.estimatedTime.match(/(\d+)\s*minute/i);
      if (match) {
        const minutes = parseInt(match[1]);
        const seconds = minutes * 60;
        setInitialTime(seconds);
        setTimeRemaining(seconds);
      }
    }
  }, [progression.estimatedTime]);

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

  const getTimerColor = () => {
    if (timeRemaining === null || initialTime === null) return '';
    const percentage = (timeRemaining / initialTime) * 100;
    if (percentage > 50) return isDarkMode ? 'text-emerald-400' : 'text-emerald-600';
    if (percentage > 25) return isDarkMode ? 'text-yellow-400' : 'text-yellow-600';
    return isDarkMode ? 'text-red-400' : 'text-red-600';
  };

  const handleStartPause = () => {
    setIsTimerRunning(!isTimerRunning);
  };

  const handleReset = () => {
    setIsTimerRunning(false);
    setTimeRemaining(initialTime);
  };

  const handleCopy = () => {
    const textToCopy = `${progression.title}\n\n${progression.progression}\n\n${progression.explanation}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMIDI = () => {
    if (!progression.midiFile) return;

    // Decode base64 MIDI file
    const byteCharacters = atob(progression.midiFile);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'audio/midi' });

    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${progression.title.replace(/[^a-z0-9]/gi, '_')}.mid`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!progression) {
    return (
      <div className={`text-center py-12 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
        <p>Select emotions and click "Generate Progression" to begin.</p>
      </div>
    );
  }

  return (
    <div className={`${isDarkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg shadow-lg p-6 max-w-4xl mx-auto`}>
      {/* Header with Title and Emotions */}
      <div className="mb-6">
        <h2 className={`text-2xl font-bold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          {progression.title}
        </h2>
        <div className="flex flex-wrap gap-2 mb-3">
          {progression.emotions && progression.emotions.map((emotion, index) => (
            <span
              key={index}
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                isDarkMode
                  ? 'bg-purple-900 text-purple-200'
                  : 'bg-purple-100 text-purple-800'
              }`}
            >
              {emotion}
            </span>
          ))}
        </div>
      </div>

      {/* Metadata Bar */}
      <div className={`flex flex-wrap gap-4 mb-6 pb-4 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Difficulty:
          </span>
          <span className={`px-2 py-1 rounded text-sm font-medium ${
            progression.difficulty === 'Beginner'
              ? isDarkMode ? 'bg-green-900 text-green-200' : 'bg-green-100 text-green-800'
              : progression.difficulty === 'Intermediate'
              ? isDarkMode ? 'bg-yellow-900 text-yellow-200' : 'bg-yellow-100 text-yellow-800'
              : isDarkMode ? 'bg-red-900 text-red-200' : 'bg-red-100 text-red-800'
          }`}>
            {progression.difficulty}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            Estimated Time:
          </span>
          <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {progression.estimatedTime}
          </span>
        </div>
      </div>

      {/* Timer */}
      {timeRemaining !== null && (
        <div className={`mb-6 p-4 rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
          <div className="flex items-center justify-between">
            <div>
              <span className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                Time Remaining:
              </span>
              <div className={`text-3xl font-mono font-bold mt-1 ${getTimerColor()}`}>
                {formatTime(timeRemaining)}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleStartPause}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  isDarkMode
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                {timeRemaining === 0 ? "Time's Up!" : isTimerRunning ? "Pause" : "Start"}
              </button>
              <button
                onClick={handleReset}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  isDarkMode
                    ? 'bg-gray-600 hover:bg-gray-500 text-white'
                    : 'bg-gray-300 hover:bg-gray-400 text-gray-800'
                }`}
              >
                Reset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chord Progression */}
      <div className="mb-6">
        <h3 className={`text-lg font-semibold mb-3 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          Chord Progression
        </h3>
        <div className={`p-4 rounded-lg font-mono text-lg ${
          isDarkMode ? 'bg-gray-700 text-blue-300' : 'bg-blue-50 text-blue-900'
        }`}>
          {progression.progression}
        </div>
      </div>

      {/* Explanation */}
      <div className="mb-6">
        <h3 className={`text-lg font-semibold mb-3 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
          Why This Progression?
        </h3>
        <div className={`prose max-w-none ${isDarkMode ? 'prose-invert' : ''}`}>
          <p className={`whitespace-pre-wrap ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            {progression.explanation}
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleDownloadMIDI}
          className={`flex-1 py-3 rounded-lg font-medium transition-colors ${
            isDarkMode
              ? 'bg-purple-600 hover:bg-purple-700 text-white'
              : 'bg-purple-500 hover:bg-purple-600 text-white'
          }`}
        >
          Download MIDI File
        </button>
        <button
          onClick={handleCopy}
          className={`px-6 py-3 rounded-lg font-medium transition-colors ${
            copied
              ? isDarkMode
                ? 'bg-green-600 text-white'
                : 'bg-green-500 text-white'
              : isDarkMode
              ? 'bg-gray-700 hover:bg-gray-600 text-white'
              : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
          }`}
        >
          {copied ? 'Copied!' : 'Copy Text'}
        </button>
      </div>
    </div>
  );
};

export default ChordProgressionPromptDisplay;
