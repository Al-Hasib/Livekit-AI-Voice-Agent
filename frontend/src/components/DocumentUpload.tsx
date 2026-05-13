import React, { useCallback, useState } from "react";
import { Upload, FileText, Trash2 } from "lucide-react";
import { api } from "../services/api";

interface UploadedDoc {
  doc_id: string;
  filename: string;
  status: string;
  message: string;
}

export const DocumentUpload: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<UploadedDoc[]>([]);
  const [textInput, setTextInput] = useState("");
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);

    try {
      const result = await api.uploadDocument(file);
      setDocuments((prev) => [
        ...prev,
        { doc_id: result.doc_id, filename: result.filename, status: result.status, message: result.message },
      ]);
      setMessage({ type: "success", text: `Uploaded: ${result.filename}` });
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Upload failed",
      });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }, []);

  const handleTextIngest = useCallback(async () => {
    if (!textInput.trim()) return;

    setUploading(true);
    setMessage(null);

    try {
      const result = await api.ingestText(textInput.trim());
      setDocuments((prev) => [
        ...prev,
        {
          doc_id: result.doc_id,
          filename: "inline-text",
          status: result.status,
          message: result.message,
        },
      ]);
      setTextInput("");
      setMessage({ type: "success", text: "Text ingested successfully" });
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Ingestion failed",
      });
    } finally {
      setUploading(false);
    }
  }, [textInput]);

  const handleDelete = useCallback(async (docId: string) => {
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
      setMessage({ type: "success", text: "Document deleted" });
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Delete failed",
      });
    }
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Knowledge Base</h3>

      {/* File Upload */}
      <label className="flex items-center justify-center gap-2 border-2 border-dashed border-gray-600 rounded-lg p-4 cursor-pointer hover:border-blue-500 transition-colors">
        <Upload size={20} className="text-gray-400" />
        <span className="text-gray-400 text-sm">
          {uploading ? "Uploading..." : "Drop a file or click to upload"}
        </span>
        <input
          type="file"
          accept=".txt,.md,.pdf,.json,.csv"
          onChange={handleFileUpload}
          className="hidden"
          disabled={uploading}
        />
      </label>

      {/* Text Ingest */}
      <div className="space-y-2">
        <textarea
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          placeholder="Or paste text directly to add to knowledge base..."
          className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm resize-none h-24"
          disabled={uploading}
        />
        <button
          onClick={handleTextIngest}
          disabled={uploading || !textInput.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          Add Text
        </button>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`rounded-lg px-3 py-2 text-sm ${
            message.type === "success"
              ? "bg-green-900/50 text-green-200 border border-green-700"
              : "bg-red-900/50 text-red-200 border border-red-700"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Document List */}
      {documents.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-400">Uploaded Documents</h4>
          {documents.map((doc) => (
            <div
              key={doc.doc_id}
              className="flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2"
            >
              <div className="flex items-center gap-2 min-w-0">
                <FileText size={16} className="text-gray-400 shrink-0" />
                <span className="text-sm text-white truncate">{doc.filename}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    doc.status === "completed"
                      ? "bg-green-900 text-green-300"
                      : "bg-yellow-900 text-yellow-300"
                  }`}
                >
                  {doc.status}
                </span>
              </div>
              <button
                onClick={() => handleDelete(doc.doc_id)}
                className="text-red-400 hover:text-red-300 shrink-0 ml-2"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};