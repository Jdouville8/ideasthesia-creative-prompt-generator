import React, { useState, useEffect } from 'react';

function DrawingPromptDisplay({ prompt }) {
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [timerStarted, setTimerStarted] = useState(false);

  useEffect(() => {
    if (prompt?.estimatedTime) {
      const minutes = parseInt(prompt.estimatedTime);
      setTimeRemaining(minutes * 60);
      setIsTimerRunning(false);
      setTimerStarted(false);
    }
  }, [prompt]);

  useEffect(() => {
    let interval;
    if (isTimerRunning && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            setIsTimerRunning(false);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning, timeRemaining]);

  const toggleTimer = () => {
    setIsTimerRunning(!isTimerRunning);
    if (!timerStarted) {
      setTimerStarted(true);
    }
  };

  const resetTimer = () => {
    if (prompt?.estimatedTime) {
      const minutes = parseInt(prompt.estimatedTime);
      setTimeRemaining(minutes * 60);
      setIsTimerRunning(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!prompt) return null;

  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-gray-800 dark:to-gray-900 rounded-lg shadow-xl p-8">
      {/* Header with Title and Metadata */}
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          {prompt.title}
        </h2>
        <div className="flex flex-wrap gap-3 text-sm">
          <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-full font-medium">
            {prompt.difficulty}
          </span>
          <span className="px-3 py-1 bg-pink-100 dark:bg-pink-900 text-pink-800 dark:text-pink-200 rounded-full font-medium">
            ⏱ {prompt.estimatedTime}
          </span>
          {prompt.skills && prompt.skills.map((skill, idx) => (
            <span key={idx} className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full font-medium">
              🎨 {skill}
            </span>
          ))}
        </div>
      </div>

      {/* Timer */}
      {timeRemaining !== null && (
        <div className="mb-6 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Time Remaining</p>
              <p className={`text-4xl font-bold ${timeRemaining === 0 ? 'text-red-500' : 'text-gray-900 dark:text-white'}`}>
                {formatTime(timeRemaining)}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={toggleTimer}
                className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
                  isTimerRunning
                    ? 'bg-yellow-500 hover:bg-yellow-600 text-white'
                    : 'bg-green-500 hover:bg-green-600 text-white'
                }`}
              >
                {isTimerRunning ? '⏸ Pause' : timerStarted ? '▶ Resume' : '▶ Start'}
              </button>
              <button
                onClick={resetTimer}
                className="px-6 py-3 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-semibold transition-colors"
              >
                🔄 Reset
              </button>
            </div>
          </div>
          {timeRemaining === 0 && (
            <p className="mt-2 text-red-500 font-semibold">⏰ Time's up!</p>
          )}
        </div>
      )}

      {/* Exercise Content */}
      <div className="prose prose-lg dark:prose-invert max-w-none">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md whitespace-pre-wrap text-gray-900 dark:text-gray-100">
          {prompt.content}
        </div>
      </div>

      {/* Tips Section */}
      {prompt.tips && prompt.tips.length > 0 && (
        <div className="mt-6 p-6 bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-900 dark:to-pink-900 rounded-lg">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            💡 Drawing Tips
          </h3>
          <ul className="space-y-2">
            {prompt.tips.map((tip, index) => (
              <li key={index} className="flex items-start">
                <span className="text-purple-600 dark:text-purple-400 mr-2">▸</span>
                <span className="text-gray-800 dark:text-gray-200">{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default DrawingPromptDisplay;
