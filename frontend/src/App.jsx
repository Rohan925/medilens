import { BrowserRouter, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Home from "./pages/Home";
import MedicinePage from "./pages/MedicinePage";
import OcrResultPage from "./pages/OcrResultPage";

import "./css/App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/home" element={<Home />} />
          <Route path="/medicine/:name" element={<MedicinePage />} />
          <Route path="/ocr-result" element={<OcrResultPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
