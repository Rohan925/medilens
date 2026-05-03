function SearchBar({ onSearch }) {
  const handleSearch = () => {
    const value = document.getElementById("medicine-search").value;
    if (value.trim()) onSearch(value);
  };

  return (
    <div className="search-section">
      <input
        id="medicine-search"
        placeholder="Search for medicines..."
        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
      />
      <button onClick={handleSearch}>Search</button>
    </div>
  );
}

export default SearchBar;
