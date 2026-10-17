import { useContext } from 'react';
import { ThemeContext } from '../context/ThemeContext.jsx';
export default function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error('useTheme must be used within ThemeProvider');
  return value;
}
