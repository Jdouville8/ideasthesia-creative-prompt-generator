import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const SynthSelector = ({ selectedSynthesizer, onSynthesizerChange, selectedExerciseType, onExerciseTypeChange }) => {
  const { isDarkMode } = useTheme();

  const synthesizers = ['Serum 2', 'Phase Plant', 'Vital'];
  const exerciseTypes = [
    { value: 'technical', label: 'Technical', description: 'Step-by-step synthesis techniques' },
    { value: 'creative', label: 'Creative/Abstract', description: 'Emotion and concept-based challenges' }
  ];

  return (
    <div className="space-y-6">
      {/* Synthesizer Selection */}
      <div>
        <label className={`block text-sm font-semibold mb-3 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>
          Select Synthesizer
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {synthesizers.map((synth) => (
            <button
              key={synth}
              onClick={() => onSynthesizerChange(synth)}
              className={`p-4 rounded-lg font-medium transition-all duration-200 border-2 ${
                selectedSynthesizer === synth
                  ? isDarkMode
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-lg transform scale-105'
                    : 'bg-indigo-600 text-white border-indigo-600 shadow-lg transform scale-105'
                  : isDarkMode
                  ? 'bg-gray-700 text-gray-200 border-gray-600 hover:bg-gray-600 hover:border-gray-500'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'
              }`}
            >
              <div className="flex items-center justify-center">
                <span className="text-lg">🎹</span>
                <span className="ml-2">{synth}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Exercise Type Selection */}
      <div>
        <label className={`block text-sm font-semibold mb-3 ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>
          Exercise Type
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {exerciseTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => onExerciseTypeChange(type.value)}
              className={`p-4 rounded-lg text-left transition-all duration-200 border-2 ${
                selectedExerciseType === type.value
                  ? isDarkMode
                    ? 'bg-purple-600 text-white border-purple-500 shadow-lg'
                    : 'bg-purple-600 text-white border-purple-600 shadow-lg'
                  : isDarkMode
                  ? 'bg-gray-700 text-gray-200 border-gray-600 hover:bg-gray-600 hover:border-gray-500'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 hover:border-gray-400'
              }`}
            >
              <div className="font-semibold text-lg mb-1">{type.label}</div>
              <div className={`text-sm ${selectedExerciseType === type.value ? 'text-gray-100' : isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                {type.description}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SynthSelector;
