import React, { useState, useEffect } from 'react';
import { 
  analyzeFootage, 
  getFootageJobStatus, 
  getFootageVideoUrl, 
  getFootageSummaryUrl 
} from '../services/api';

const FootageUploader = () => {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [progress, setProgress] = useState(0);

  // Poll for status updates
  useEffect(() => {
    let intervalId;
    if (jobId && jobStatus !== 'done' && jobStatus !== 'error') {
      intervalId = setInterval(async () => {
        try {
          const statusData = await getFootageJobStatus(jobId);
          setJobStatus(statusData.status);
          setProgress(statusData.progress);
        } catch (error) {
          console.error("Error polling status:", error);
        }
      }, 2000); // Poll every 2 seconds
    }
    return () => clearInterval(intervalId);
  }, [jobId, jobStatus]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    try {
      setJobStatus('queued');
      setProgress(0);
      const data = await analyzeFootage(file, true);
      setJobId(data.job_id);
    } catch (error) {
      console.error("Upload failed", error);
      setJobStatus('error');
    }
  };

  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-xl font-bold mb-4">Post-Incident Footage Analysis</h2>
      
      <form onSubmit={handleUpload} className="mb-4">
        <input 
          type="file" 
          accept="video/*" 
          onChange={(e) => setFile(e.target.files[0])} 
          className="mb-2 block w-full"
        />
        <button 
          type="submit" 
          disabled={!file || jobStatus === 'running' || jobStatus === 'queued'}
          className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
        >
          {jobStatus === 'running' || jobStatus === 'queued' ? 'Processing...' : 'Analyze Video'}
        </button>
      </form>

      {jobId && (
        <div className="mt-4 p-4 border rounded">
          <p><strong>Job ID:</strong> {jobId}</p>
          <p><strong>Status:</strong> {jobStatus} ({progress}%)</p>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2.5 mt-2">
            <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${progress}%` }}></div>
          </div>

          {/* Download Links (Only show when done) */}
          {jobStatus === 'done' && (
            <div className="mt-4 flex gap-4">
              <a 
                href={getFootageVideoUrl(jobId)} 
                download
                className="bg-green-500 text-white px-4 py-2 rounded no-underline"
              >
                Download Highlight Video
              </a>
              <a 
                href={getFootageSummaryUrl(jobId)} 
                download
                className="bg-gray-800 text-white px-4 py-2 rounded no-underline"
              >
                Download Summary Text
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FootageUploader;