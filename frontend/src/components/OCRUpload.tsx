import { useRef, useState } from 'react';
import { api, type OCRResponse } from '../api/client';
import { useToast } from './Toast';

export function OCRUpload({ userId }: { userId: number }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OCRResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const { show } = useToast();

  const selectFile = (file?: File) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      show('Please choose a prescription image file.', 'error');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      show('Image is too large. Maximum size is 10MB.', 'error');
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
  };

  const handleUpload = async (autoRegister: boolean) => {
    if (!selectedFile) {
      show('Choose or drop a prescription image first.', 'error');
      return;
    }
    setLoading(true);
    try {
      const data = await api.ocrUpload(selectedFile, userId, autoRegister);
      setResult(data);
      const count = data.medications.length;
      const registered = data.registered_ids.length;
      show(
        autoRegister
          ? `Scanned ${count} medication(s), registered ${registered}.`
          : `Scanned ${count} medication(s).`,
        'success',
      );
    } catch (error) {
      show(error instanceof Error ? error.message : 'OCR failed. Check API key and image quality.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h2 className="text-lg font-semibold">📷 Prescription OCR</h2>
          <p className="text-sm text-slate-500">
            Upload a prescription image. Gemini Vision extracts medications, dosage, instructions, and suggested times.
          </p>
        </div>
        {result && (
          <span className="text-xs px-2 py-1 rounded-full bg-teal-100 text-teal-700 dark:bg-teal-900 dark:text-teal-200">
            {result.confidence} confidence
          </span>
        )}
      </div>

      <div
        className={`border-2 border-dashed rounded-2xl p-4 transition-colors ${
          dragging
            ? 'border-teal-500 bg-teal-50 dark:bg-teal-950/30'
            : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900'
        }`}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          selectFile(event.dataTransfer.files[0]);
        }}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(event) => selectFile(event.target.files?.[0])}
        />

        {previewUrl ? (
          <div className="grid sm:grid-cols-[96px_1fr] gap-3 items-center">
            <img
              src={previewUrl}
              alt="Prescription preview"
              className="h-24 w-24 rounded-xl object-cover border border-slate-200 dark:border-slate-700"
            />
            <div>
              <p className="font-medium text-sm">{selectedFile?.name}</p>
              <p className="text-xs text-slate-500">
                {selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB` : ''}
              </p>
              <button
                type="button"
                className="text-xs text-teal-600 dark:text-teal-400 mt-2"
                onClick={() => fileRef.current?.click()}
              >
                Choose a different image
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            className="w-full text-left"
            onClick={() => fileRef.current?.click()}
          >
            <div className="text-sm font-medium">Drop a prescription image here, or click to browse</div>
            <div className="text-xs text-slate-500 mt-1">JPEG/PNG/WebP up to 10MB</div>
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-2 mt-3">
        <button disabled={loading || !selectedFile} onClick={() => handleUpload(false)} className="btn-secondary text-sm">
          {loading ? 'Scanning...' : 'Scan Only'}
        </button>
        <button disabled={loading || !selectedFile} onClick={() => handleUpload(true)} className="btn-primary text-sm">
          {loading ? 'Registering...' : 'Scan & Register'}
        </button>
      </div>

      {result && (
        <div className="mt-4 space-y-3">
          <div className="grid sm:grid-cols-2 gap-2 text-xs text-slate-500">
            <div>Patient: <span className="font-medium text-slate-700 dark:text-slate-300">{result.patient_name || 'Not visible'}</span></div>
            <div>Doctor: <span className="font-medium text-slate-700 dark:text-slate-300">{result.doctor_name || 'Not visible'}</span></div>
          </div>

          {result.medications.length === 0 ? (
            <div className="rounded-xl bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-200 p-3 text-sm">
              No medications were detected. Try a clearer image with the medication name and dosage visible.
            </div>
          ) : (
            <div className="space-y-2">
              {result.medications.map((medication, index) => (
                <div key={`${medication.name}-${index}`} className="rounded-xl border border-slate-200 dark:border-slate-800 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-semibold text-sm">{medication.name || 'Unnamed medication'}</div>
                    {result.registered_ids[index] && (
                      <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200">
                        Registered #{result.registered_ids[index]}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    {medication.dosage || 'Dosage not visible'} · {medication.time_of_day || 'No time extracted'}
                  </div>
                  {medication.instructions && (
                    <div className="mt-2 text-sm text-slate-700 dark:text-slate-300">
                      {medication.instructions}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
