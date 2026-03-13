import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './Layout';
import Dashboard from './pages/dashboard';
import VirtualBox from './pages/virtualbox';
import Sandbox from './pages/sandbox';
import Tools from './pages/tools';
import Apps from './pages/apps';
import Chat from './pages/chat';
import Help from './pages/help';
import Settings from './pages/settings';
import PromptsSkills from './pages/prompts-skills';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="virtualbox" element={<VirtualBox />} />
          <Route path="sandbox" element={<Sandbox />} />
          <Route path="tools" element={<Tools />} />
          <Route path="apps" element={<Apps />} />
          <Route path="prompts-skills" element={<PromptsSkills />} />
          <Route path="chat" element={<Chat />} />
          <Route path="help" element={<Help />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
