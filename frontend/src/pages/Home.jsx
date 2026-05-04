import { useNavigate } from "react-router-dom";
import AppNavbar from "../components/AppNavbar";
import SearchBar from "../components/SearchBar";
import ChatBot from "../components/ChatBot";
import OcrCamera from "../components/OcrCamera";
import "../css/Home.css";

function Home() {
  const navigate = useNavigate();

  return (
    <>
      <AppNavbar />

      <div className="home-container">
        <SearchBar onSearch={(q) => navigate(`/medicine/${q}`)} />

        <div className="options">
          <ChatBot />
          <OcrCamera />
        </div>
      </div>
    </>
  );
}

export default Home;
