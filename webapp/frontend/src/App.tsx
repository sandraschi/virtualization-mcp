import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './Layout';
import Dashboard from './pages/dashboard';
import VirtualBox from './pages/virtualbox';
import Sandbox from './pages/sandbox';
import Chat from './pages/chat';
import Settings from './pages/settings';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="virtualbox" element={<VirtualBox />} />
          <Route path="sandbox" element={<Sandbox />} />
          <Route path="chat" element={<Chat />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
