import React, { useState } from 'react';
import LandingPage from './pages/LandingPage';
import AnalysisPage from './pages/AnalysisPage';
import { AnalysisResult } from './types/api';
import './App.css';

type Screen = 'landing' | 'analysis';

export interface AppState {
  projectId: string;
  projectName: string;
  projectPath: string;
  changeDescription: string;
  diffText: string;
  changedFiles: string[];
  analysisId: string | null;
  result: AnalysisResult | null;
}

const defaultState: AppState = {
  projectId: '',
  projectName: '',
  projectPath: '',
  changeDescription: '',
  diffText: '',
  changedFiles: [],
  analysisId: null,
  result: null,
};

export default function App() {
  const [screen, setScreen] = useState<Screen>('landing');
  const [appState, setAppState] = useState<AppState>(defaultState);

  const handleStartAnalysis = (state: AppState) => {
    setAppState(state);
    setScreen('analysis');
  };

  const handleReset = () => {
    setAppState(defaultState);
    setScreen('landing');
  };

  return (
    <div className="app">
      {screen === 'landing' ? (
        <LandingPage onStartAnalysis={handleStartAnalysis} />
      ) : (
        <AnalysisPage appState={appState} onReset={handleReset} />
      )}
    </div>
  );
}
