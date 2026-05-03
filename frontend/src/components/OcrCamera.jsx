import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../css/OcrCamera.css";

function OcrCamera() {
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const uploadInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [facingMode, setFacingMode] = useState("environment");
  const [flash, setFlash] = useState(false);

  // Stop camera when component unmounts or modal closes
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const startCamera = async () => {
    setErrorMessage("");
    // Stop any existing stream first
    stopCamera();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: facingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      });
      streamRef.current = stream;
      setIsCameraActive(true);
      // Wait for state update before setting srcObject
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      }, 100);
    } catch (err) {
      console.error("Camera access error:", err);
      setErrorMessage("Could not access camera. Please allow permissions.");
    }
  };

  const toggleCamera = () => {
    setFacingMode(prev => prev === "environment" ? "user" : "environment");
  };

  // Restart camera when facingMode changes, but only if it was already active
  useEffect(() => {
    if (isCameraActive) {
      startCamera();
    }
  }, [facingMode]);

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;

    // Trigger Flash
    setFlash(true);
    setTimeout(() => setFlash(false), 200);

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame
    const context = canvas.getContext("2d");

    // Optional: Mirror if user facing (not requested, but standard)
    // if (facingMode === "user") {
    //   context.translate(canvas.width, 0);
    //   context.scale(-1, 1);
    // }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to blob and process
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
        stopCamera();
        setShowModal(false);
        processFile(file);
      }
    }, "image/jpeg");
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setShowModal(false);
      processFile(file);
    }
  };

  const processFile = async (file) => {
    setLoading(true);
    const imageUrl = URL.createObjectURL(file);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://127.0.0.1:8000/ocr", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      navigate("/ocr-result", {
        state: {
          image: imageUrl,
          medicine: data.medicine,
          summary: data.summary,
          success: data.success,
          confidence: data.confidence,
          citations: data.citations
        },
      });
    } catch (err) {
      console.error("OCR Error:", err);
      navigate("/ocr-result", {
        state: {
          image: imageUrl,
          success: false,
          summary: null,
          error: "Failed to process image"
        },
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tool-card">
      <div className="tool-header">OCR Camera</div>

      <div className="tool-body tool-camera">
        <button
          className="camera-button"
          onClick={() => setShowModal(true)}
          disabled={loading}
        >
          <span className="camera-icon">{loading ? "⏳" : "📷"}</span>
          <span className="camera-text">{loading ? "Processing..." : "Scan to Ask"}</span>
        </button>
      </div>

      <p className="ocr-hint">Scan a medicine to ask questions about it</p>

      {/* Hidden Upload Input */}
      <input
        type="file"
        accept="image/*"
        ref={uploadInputRef}
        hidden
        onChange={handleImageUpload}
      />

      {/* Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); stopCamera(); }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>

            {/* Camera View */}
            {isCameraActive ? (
              <div className="camera-view">
                <div className={`video-container ${flash ? "flash-active" : ""}`}>
                  <video ref={videoRef} autoPlay playsInline className="live-video"></video>
                </div>
                <canvas ref={canvasRef} hidden></canvas>
                <div className="camera-controls">
                  <button className="modal-btn switch-btn" onClick={toggleCamera}>🔄 Switch</button>
                  <button className="modal-btn capture-btn" onClick={captureImage}>Capture</button>
                  <button className="close-btn" onClick={stopCamera}>Cancel</button>
                </div>
              </div>
            ) : (
              /* Selection View */
              <>
                <h3>Choose Input Method</h3>
                {errorMessage && <p className="error-msg">{errorMessage}</p>}
                <div className="modal-actions">
                  <button
                    className="modal-btn"
                    onClick={() => uploadInputRef.current.click()}
                  >
                    📁 Upload Image
                  </button>
                  <button
                    className="modal-btn"
                    onClick={startCamera}
                  >
                    📷 Open Camera
                  </button>
                </div>
                <button className="close-btn" onClick={() => setShowModal(false)}>Cancel</button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default OcrCamera;
