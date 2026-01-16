import React, { useState, useRef } from 'react';
import { transcribeAudio } from '../../services/transcriptionApi';
import { Mic, Square, Loader2 } from 'lucide-react';

interface AudioRecorderProps {
    onTranscriptionComplete: (text: string) => void;
    className?: string;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ onTranscriptionComplete, className }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' }); /* Chrome prefers webm */

            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
                await handleTranscribe(audioBlob);

                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error('Error accessing microphone:', err);
            alert('Could not access microphone. Please ensure permission is granted.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const handleTranscribe = async (audioBlob: Blob) => {
        setIsProcessing(true);
        try {
            // Create a wav file from blob if needed, but backend handles webm usually if dev installed libraries right.
            // MedASR via HuggingFace pipeline often handles raw audio file input well. 
            // We send webm directly.
            const text = await transcribeAudio(audioBlob);
            onTranscriptionComplete(text);
        } catch (error) {
            console.error('Transcription failed:', error);
            alert('Failed to transcribe audio. Please try again.');
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className={`inline-flex items-center ${className || ''}`}>
            {isProcessing ? (
                <button disabled className="p-2 rounded-full bg-gray-100 text-primary animate-spin">
                    <Loader2 size={20} />
                </button>
            ) : isRecording ? (
                <button
                    onClick={stopRecording}
                    className="p-2 rounded-full bg-red-100 text-red-600 hover:bg-red-200 transition-colors animate-pulse"
                    title="Stop Recording"
                    type="button"
                >
                    <Square size={20} fill="currentColor" />
                </button>
            ) : (
                <button
                    onClick={startRecording}
                    className="p-2 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors"
                    title="Start Dictation"
                    type="button"
                >
                    <Mic size={20} />
                </button>
            )}
        </div>
    );
};

export default AudioRecorder;
