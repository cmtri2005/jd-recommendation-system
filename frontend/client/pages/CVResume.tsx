import { useState } from "react";
import { Upload, FileText, ClipboardList, Check } from "lucide-react";

export function CVResume() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [useFileForJob, setUseFileForJob] = useState(false);

  const handleResumeUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setResumeFile(file);
    }
  };

  const handleJobFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setJobFile(file);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/30 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-3">
            CV & Resume Matching
          </h1>
          <p className="text-lg text-muted-foreground">
            Upload your resume and job description to see how well they match
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Resume Upload Section */}
          <div className="flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <FileText className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-semibold text-foreground">Resume</h2>
            </div>

            {!resumeFile ? (
              <label className="flex-1 border-2 border-dashed border-border rounded-lg p-8 cursor-pointer hover:border-primary hover:bg-muted/50 transition-all flex flex-col items-center justify-center">
                <Upload className="w-12 h-12 text-muted-foreground mb-3" />
                <span className="text-lg font-medium text-foreground mb-1">
                  Click to upload
                </span>
                <span className="text-sm text-muted-foreground">
                  PDF or DOCX files
                </span>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleResumeUpload}
                  className="hidden"
                />
              </label>
            ) : (
              <div className="flex-1 border-2 border-primary/20 bg-primary/5 rounded-lg p-8 flex flex-col items-center justify-center">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                  <Check className="w-6 h-6 text-primary" />
                </div>
                <span className="text-lg font-medium text-foreground mb-2">
                  {resumeFile.name}
                </span>
                <span className="text-sm text-muted-foreground mb-4">
                  {(resumeFile.size / 1024).toFixed(2)} KB
                </span>
                <button
                  onClick={() => setResumeFile(null)}
                  className="text-sm text-primary hover:underline"
                >
                  Remove file
                </button>
              </div>
            )}
          </div>

          {/* Job Description Section */}
          <div className="flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <ClipboardList className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-semibold text-foreground">
                Job Description
              </h2>
            </div>

            <div className="flex-1 flex flex-col gap-4">
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={!useFileForJob}
                    onChange={() => setUseFileForJob(false)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium text-foreground">
                    Paste text
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    checked={useFileForJob}
                    onChange={() => setUseFileForJob(true)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium text-foreground">
                    Upload file
                  </span>
                </label>
              </div>

              {!useFileForJob ? (
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description here..."
                  className="flex-1 p-4 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                />
              ) : (
                <label className="flex-1 border-2 border-dashed border-border rounded-lg p-8 cursor-pointer hover:border-primary hover:bg-muted/50 transition-all flex flex-col items-center justify-center">
                  {!jobFile ? (
                    <>
                      <Upload className="w-12 h-12 text-muted-foreground mb-3" />
                      <span className="text-lg font-medium text-foreground mb-1">
                        Click to upload
                      </span>
                      <span className="text-sm text-muted-foreground">
                        PDF or DOCX files
                      </span>
                    </>
                  ) : (
                    <>
                      <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-3">
                        <Check className="w-6 h-6 text-primary" />
                      </div>
                      <span className="text-lg font-medium text-foreground">
                        {jobFile.name}
                      </span>
                    </>
                  )}
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleJobFileUpload}
                    className="hidden"
                  />
                </label>
              )}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        {resumeFile && (jobDescription || jobFile) && (
          <div className="flex justify-center">
            <button className="px-8 py-4 bg-primary text-primary-foreground font-semibold rounded-lg hover:opacity-90 transition-opacity shadow-lg">
              Analyze Match
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
