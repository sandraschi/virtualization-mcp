import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Layout from "./Layout";
import Apps from "./pages/apps";
import Chat from "./pages/chat";
import Dashboard from "./pages/dashboard";
import Help from "./pages/help";
import HyperV from "./pages/hyperv";
import Logs from "./pages/logs";
import PromptsSkills from "./pages/prompts-skills";
import Sandbox from "./pages/sandbox";
import Settings from "./pages/settings";
import Tools from "./pages/tools";
import VirtualBox from "./pages/virtualbox";
import VmConsole from "./pages/vm-console";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="virtualbox" element={<VirtualBox />} />
          <Route path="hyperv" element={<HyperV />} />
          <Route path="sandbox" element={<Sandbox />} />
          <Route path="tools" element={<Tools />} />
          <Route path="apps" element={<Apps />} />
          <Route path="prompts-skills" element={<PromptsSkills />} />
          <Route path="chat" element={<Chat />} />
          <Route path="logs" element={<Logs />} />
          <Route path="help" element={<Help />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="/vm/:name/console" element={<VmConsole />} />
      </Routes>
    </Router>
  );
}

export default App;
