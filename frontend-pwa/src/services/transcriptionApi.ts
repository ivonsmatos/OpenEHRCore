const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface TranscriptionResponse {
    resourceType: string;
    status: string;
    type: {
        text: string;
    };
    content: {
        attachment: {
            data: string;
        }
    }[];
    description?: string;
}

export const transcribeAudio = async (audioBlob: Blob): Promise<string> => {
    const formData = new FormData();
    // Append as 'audio' to match backend expectation
    // Filename is optional but good practice
    formData.append('audio', audioBlob, 'recording.wav');

    const response = await fetch(`${API_URL}/asr/transcribe/`, {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        }
        // Do not set Content-Type header manually when using FormData
        // The browser sets it with the boundary
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.issue?.[0]?.diagnostics || 'Transcription failed');
    }

    const data: TranscriptionResponse = await response.json();

    // FHIR-like response handling
    // Return the text data from the attachment
    if (data.content && data.content.length > 0) {
        return data.content[0].attachment.data;
    }

    return '';
};
