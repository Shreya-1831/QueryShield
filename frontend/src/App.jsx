import { useRoutes } from 'react-router-dom';
import { PublicRoutes } from './routes/PublicRoutes.jsx';
import { AppRoutes } from './routes/AppRoutes.jsx';

export default function App() {
  const element = useRoutes([...PublicRoutes, ...AppRoutes]);
  return element;
}
