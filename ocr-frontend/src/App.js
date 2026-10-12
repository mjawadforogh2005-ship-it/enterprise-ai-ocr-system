import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle, RefreshCw } from 'lucide-react';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ocrData, setOcrData] = useState(null);
  const [correctedText, setCorrectedText] = useState('');
  const [feedbackStatus, setFeedbackStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);

  const fetchMetrics = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/metrics');
      setMetrics(res.data);
    } catch (err) {
      console.error("Error fetching metrics:", err);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreview(URL.createObjectURL(file));
      setOcrData(null);
      setFeedbackStatus(null);
    }
  };

  const handleProcessOCR = async () => {
    if (!selectedImage) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedImage);

    try {
      const res = await axios.post('http://localhost:8000/api/ocr', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setOcrData(res.data);
      setCorrectedText(res.data.extracted_text);
    } catch (err) {
      console.error(err);
      alert('خطا در پردازش تصویر! لطفاً ترمینال پایتون را بررسی کنید.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendFeedback = async () => {
    if (!ocrData) return;
    try {
      const res = await axios.post('http://localhost:8000/api/feedback', {
        image_id: ocrData.image_id,
        original_text: ocrData.extracted_text,
        corrected_text: correctedText
      });
      setFeedbackStatus(`بازخورد ذخیره شد! (CER: ${res.data.cer})`);
      fetchMetrics();
    } catch (err) {
      alert('خطا در ثبت بازخورد');
    }
  };

  return (
    <div className="notranslate" translate="no" style={{ fontFamily: 'Tahoma, sans-serif', backgroundColor: '#0f172a', color: '#f8fafc', minHeight: '100vh', padding: '2rem' }}>
      <header style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h1 style={{ color: '#38bdf8', fontSize: '2.2rem', marginBottom: '0.5rem' }}>AI-Powered Offline OCR System</h1>
        <p style={{ color: '#94a3b8' }}>سیستم هوشمند تشخیص و استخراج متن با قابلیت یادگیری از بازخورد کاربر</p>
      </header>

      {metrics && (
        <div style={{ maxWidth: '1200px', margin: '0 auto 2rem auto', backgroundColor: '#1e293b', padding: '1.2rem', borderRadius: '12px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-around', alignItems: 'center' }}>
          <div style={{ textAlign: 'center' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>تعداد نمونه‌های Feedback</span>
            <h3 style={{ color: '#38bdf8', fontSize: '1.5rem', margin: '0.2rem 0' }}>{metrics.total_samples}</h3>
          </div>
          <div style={{ textAlign: 'center' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>نرخ خطای کاراکتر (CER)</span>
            <h3 style={{ color: '#f43f5e', fontSize: '1.5rem', margin: '0.2rem 0' }}>{metrics.avg_cer}</h3>
          </div>
          <div style={{ textAlign: 'center' }}>
            <span style={{ color: '#94a3b8', fontSize: '0.9rem' }}>دقت فعلی مدل</span>
            <h3 style={{ color: '#4ade80', fontSize: '1.5rem', margin: '0.2rem 0' }}>{metrics.accuracy_percentage}%</h3>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '12px', border: '1px solid #334155' }}>
          <h2 style={{ fontSize: '1.2rem', color: '#e2e8f0', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Upload size={20} color="#38bdf8" /> بارگذاری تصویر سند / تذکره
          </h2>
          
          <input type="file" accept="image/*" onChange={handleImageChange} id="imgInput" style={{ display: 'none' }} />
          <label htmlFor="imgInput" style={{ display: 'block', padding: '2rem', border: '2px dashed #475569', borderRadius: '8px', textAlign: 'center', cursor: 'pointer', backgroundColor: '#0f172a' }}>
            {preview ? <img src={preview} alt="preview" style={{ maxWidth: '100%', maxHeight: '250px', borderRadius: '6px' }} /> : 'کلیک کنید یا تصویر را اینجا رها کنید'}
          </label>

          <button 
            onClick={handleProcessOCR} 
            disabled={!selectedImage || loading}
            style={{ width: '100%', marginTop: '1.5rem', padding: '0.8rem', backgroundColor: loading ? '#64748b' : '#0284c7', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}
          >
            {loading ? <RefreshCw size={20} /> : <FileText size={20} />}
            {loading ? 'در حال استخراج متن...' : 'شروع پردازش OCR'}
          </button>
        </div>

        <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '12px', border: '1px solid #334155' }}>
          <h2 style={{ fontSize: '1.2rem', color: '#e2e8f0', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={20} color="#4ade80" /> متن استخراج‌شده و ویرایش (Feedback)
          </h2>

          <textarea 
            rows="10" 
            value={correctedText} 
            onChange={(e) => setCorrectedText(e.target.value)}
            placeholder="متن استخراج‌شده در اینجا قرار می‌گیرد..."
            style={{ width: '100%', padding: '1rem', backgroundColor: '#0f172a', color: '#f1f5f9', border: '1px solid #475569', borderRadius: '6px', fontSize: '1rem', resize: 'vertical' }}
          />

          {ocrData && (
            <button 
              onClick={handleSendFeedback} 
              style={{ width: '100%', marginTop: '1rem', padding: '0.8rem', backgroundColor: '#16a34a', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem' }}
            >
              ثبت اصلاحات و بروزرسانی مدل (Retrain)
            </button>
          )}

          {feedbackStatus && (
            <div style={{ marginTop: '1rem', padding: '0.8rem', backgroundColor: '#064e3b', color: '#6ee7b7', borderRadius: '6px', border: '1px solid #047857' }}>
              {feedbackStatus}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;