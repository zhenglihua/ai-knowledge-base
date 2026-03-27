import React from 'react';

interface SearchHighlightProps {
  text: string;
  keyword: string;
}

export const SearchHighlight: React.FC<SearchHighlightProps> = ({ text, keyword }) => {
  if (!keyword || !text) return <>{text}</>;
  
  const parts = text.split(new RegExp(`(${keyword})`, 'gi'));
  
  return (
    <>
      {parts.map((part, index) => 
        part.toLowerCase() === keyword.toLowerCase() ? (
          <mark key={index} style={{ 
            backgroundColor: '#ffeb3b', 
            padding: '2px 4px',
            borderRadius: '4px',
            fontWeight: 500
          }}>
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        )
      )}
    </>
  );
};

export default SearchHighlight;
