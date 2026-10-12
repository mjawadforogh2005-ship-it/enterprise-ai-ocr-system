"use client";

import React, { useState, useEffect } from "react";
import { Upload, FileText, CheckCircle, RefreshCw, Download } from "lucide-react";

export default function Home() {
  // ۱. تمام متغیرهای useState باید دقیقا همین‌جا (داخل تابع) باشند
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [imageId, setImageId] = useState("");
  
  // نگهداری جداگانه متن اولیه برای CER واقعی و متن قابل ویرایش برای کاربر
  const [rawOcrText, setRawOcrText] = useState("");
  const [editableText, setEditableText] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [metrics, setMetrics] = useState({
    total_samples: 0,
    avg_cer: 0.0,
    accuracy_percentage: 100.0,
  });

  const fetchMetrics = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/metrics");
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setRawOcrText("");
      setEditableText("");
      setImageId("");
    }
  };

  const handleRunOcr = async () => {
    if (!selectedFile) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch("http://localhost:8000/api/ocr", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("OCR Processing Failed");

      const data = await res.json();
      setImageId(data.image_id);
      setRawOcrText(data.extracted_text);
      setEditableText(data.extracted_text);
    } catch (err) {
      alert("خطا در پردازش تصویر: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveFeedback = async () => {
    if (!imageId) {
      alert("ابتدا یک تصویر را پردازش کنید.");
      return;
    }
    setSubmitting(true);

    try {
      const res = await fetch("http://localhost:8000/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_id: imageId,
          original_text: rawOcrText,
          corrected_text: editableText,
        }),
      });

      if (!res.ok) throw new Error("Failed to save feedback");

      const data = await res.json();
      alert(`بازخورد ثبت شد! CER محاسبه‌شده: ${data.cer}`);
      fetchMetrics();
    } catch (err) {
      alert("خطا در ثبت بازخورد: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadTxt = () => {
    if (!editableText) return;
    const element = document.createElement("a");
    const file = new Blob([editableText], { type: "text/plain;charset=utf-8" });
    element.href = URL.createObjectURL(file);
    element.download = `ocr_result_${imageId || "document"}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      <header className="text-center my-6">
        <h1 className="text-3xl font-bold text-sky-400 tracking-wide">
          AI-Powered Offline OCR System
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          سیستم هوشمند تشخیص و استخراج متن با قابلیت یادگیری از بازخورد کاربر
        </p>
      </header>

      {/* Metric Cards */}
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <span className="text-xs text-slate-400">تعداد نمونه‌های Feedback</span>
          <div className="text-2xl font-extrabold text-sky-400 mt-1">
            {metrics.total_samples}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <span className="text-xs text-slate-400">(CER) نرخ خطای کاراکتر</span>
          <div className="text-2xl font-extrabold text-rose-500 mt-1">
            {metrics.avg_cer}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center">
          <span className="text-xs text-slate-400">دقت فعلی مدل</span>
          <div className="text-2xl font-extrabold text-emerald-400 mt-1">
            {metrics.accuracy_percentage}%
          </div>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Upload Box */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4 text-sky-400 font-semibold">
              <Upload size={18} />
              <h2>بارگذاری تصویر سند / تذکره</h2>
            </div>

            <div className="border-2 border-dashed border-slate-700 rounded-lg p-4 text-center hover:border-sky-500 transition-colors cursor-pointer relative min-h-[220px] flex flex-col items-center justify-center">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Document Preview"
                  className="max-h-52 object-contain rounded"
                />
              ) : (
                <div className="text-slate-500 flex flex-col items-center gap-2">
                  <Upload size={32} />
                  <span>برای انتخاب تصویر کلیک کنید</span>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleRunOcr}
            disabled={!selectedFile || loading}
            className="w-full mt-4 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white py-2.5 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? <RefreshCw className="animate-spin" size={18} /> : "شروع پردازش OCR"}
          </button>
        </div>

        {/* Result & Feedback Box */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold">
                <FileText size={18} />
                <h2>متن استخراج‌شده و ویرایش (Feedback)</h2>
              </div>
              {editableText && (
                <button
                  onClick={handleDownloadTxt}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded flex items-center gap-1 border border-slate-700"
                >
                  <Download size={14} /> دانلود TXT
                </button>
              )}
            </div>

            <textarea
              dir="rtl"
              value={editableText}
              onChange={(e) => setEditableText(e.target.value)}
              placeholder="متن استخراج‌شده در اینجا نمایش داده می‌شود..."
              className="w-full h-56 bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-sky-500 transition-colors resize-none leading-relaxed text-sm"
            />
          </div>

          <button
            onClick={handleSaveFeedback}
            disabled={!editableText || submitting}
            className="w-full mt-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white py-2.5 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {submitting ? (
              <RefreshCw className="animate-spin" size={18} />
            ) : (
              <>
                <CheckCircle size={18} /> ثبت اصلاحات و بروزرسانی مدل (Retrain)
              </>
            )}
          </button>
        </div>
      </div>
    </main>
  );
}