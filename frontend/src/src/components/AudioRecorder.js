import React, { useState, useRef, useEffect } from 'react';
import './AudioRecorder.css';

function AudioRecorder({ onAudioData, disabled }) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [hasRecording, setHasRecording] = useState(false);
  
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const timerInterval = useRef(null);
  
  const MAX_RECORDING_TIME = 120; // 2 minutes in seconds

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (timerInterval.current) {
        clearInterval(timerInterval.current);
      }
      if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
        mediaRecorder.current.stop();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      mediaRecorder.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunks.current = [];
      
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };
      
      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm;codecs=opus' });
        setAudioBlob(audioBlob);
        setHasRecording(true);
        convertToBase64(audioBlob);
        
        // Stop all tracks to free up microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.current.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      timerInterval.current = setInterval(() => {
        setRecordingTime(prevTime => {
          const newTime = prevTime + 1;
          if (newTime >= MAX_RECORDING_TIME) {
            stopRecording();
            return MAX_RECORDING_TIME;
          }
          return newTime;
        });
      }, 1000);
      
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Unable to access microphone. Please check your browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop();
    }
    setIsRecording(false);
    
    if (timerInterval.current) {
      clearInterval(timerInterval.current);
      timerInterval.current = null;
    }
  };

  const convertToBase64 = (blob) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64String = reader.result.split(',')[1]; // Remove data:audio/webm;base64, prefix
      onAudioData(base64String);
    };
    reader.readAsDataURL(blob);
  };

  const resetRecording = () => {
    setAudioBlob(null);
    setHasRecording(false);
    setRecordingTime(0);
    onAudioData(null);
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getRemainingTime = () => {
    return MAX_RECORDING_TIME - recordingTime;
  };

  return (
    <div className="audio-recorder">
      <div className="recording-controls">
        {!hasRecording ? (
          <>
            <button
              type="button"
              className={`record-button ${isRecording ? 'recording' : ''}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={disabled}
            >
              {isRecording ? (
                <span className="recording-indicator">
                  <span className="pulse-dot"></span>
                  Stop Recording
                </span>
              ) : (
                <span>
                  🎤 Start Recording
                </span>
              )}
            </button>
            
            <div className="timer-section">
              <div className="current-time">
                {formatTime(recordingTime)}
              </div>
              <div className="max-time">
                / {formatTime(MAX_RECORDING_TIME)}
              </div>
              {isRecording && (
                <div className="remaining-time">
                  ({formatTime(getRemainingTime())} remaining)
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="recording-complete">
            <div className="success-message">
              ✅ Recording Complete ({formatTime(recordingTime)})
            </div>
            <div className="recording-actions">
              <button
                type="button"
                className="reset-button"
                onClick={resetRecording}
                disabled={disabled}
              >
                🔄 Record Again
              </button>
              {audioBlob && (
                <audio 
                  controls 
                  className="audio-playback"
                  src={URL.createObjectURL(audioBlob)}
                />
              )}
            </div>
          </div>
        )}
      </div>
      
      <div className="recording-instructions">
        <h4>Recording Instructions:</h4>
        <ul>
          <li>Click "Start Recording" and speak clearly</li>
          <li>Maximum recording time: 2 minutes</li>
          <li>Cover: your approach, key insights, solution prioritization, and learnings</li>
          <li>You can review your recording before submitting</li>
        </ul>
      </div>
    </div>
  );
}

export default AudioRecorder; 