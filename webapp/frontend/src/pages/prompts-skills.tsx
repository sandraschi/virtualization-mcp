import { useEffect, useState } from 'react';
import { BookOpen, FileText, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { API_BASE } from '../api/config';

interface PromptMeta {
  name: string;
  description: string;
  arguments?: { name: string; default?: string; description?: string }[];
}

interface SkillMeta {
  id: string;
  name: string;
  description: string;
}

export default function PromptsSkills() {
  const [prompts, setPrompts] = useState<PromptMeta[]>([]);
  const [skills, setSkills] = useState<SkillMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);
  const [skillContent, setSkillContent] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const [pRes, sRes] = await Promise.all([
          fetch(`${API_BASE}/api/v1/prompts`),
          fetch(`${API_BASE}/api/v1/skills`),
        ]);
        const pData = await pRes.json().catch(() => ({ prompts: [] }));
        const sData = await sRes.json().catch(() => ({ skills: [] }));
        setPrompts(pData.prompts ?? []);
        setSkills(sData.skills ?? []);
      } catch (e) {
        console.error('Failed to fetch prompts/skills:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const loadSkillContent = async (id: string) => {
    if (skillContent[id]) {
      setExpandedSkill(expandedSkill === id ? null : id);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v1/skills/${id}`);
      const data = await res.json();
      setSkillContent((prev) => ({ ...prev, [id]: data.content ?? '' }));
      setExpandedSkill(id);
    } catch (e) {
      console.error('Failed to load skill content:', e);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[40vh]">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-10 pb-20">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-widest">
          <BookOpen className="w-3 h-3" />
          FastMCP 3.1
        </div>
        <h2 className="text-4xl font-black tracking-tighter">Prompts & Skills</h2>
        <p className="text-muted-foreground text-lg max-w-xl mx-auto">
          MCP prompts and bundled skills for virtualization-expert behavior in AI clients.
        </p>
      </div>

      <section className="space-y-4">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <FileText className="w-5 h-5 text-primary" />
          Prompts
        </h3>
        <p className="text-sm text-muted-foreground">
          Prompts return instruction text that clients can inject so the LLM behaves as a virtualization expert.
        </p>
        <div className="grid gap-4">
          {prompts.length === 0 ? (
            <div className="p-6 rounded-2xl border border-border bg-card/40 text-muted-foreground text-center">
              No prompts available. Ensure the backend is running and MCP is initialized.
            </div>
          ) : (
            prompts.map((p) => (
              <div
                key={p.name}
                className="p-6 rounded-2xl border border-border bg-card/40 hover:bg-white/5 transition-colors"
              >
                <div className="font-mono font-bold text-primary mb-2">{p.name}</div>
                <p className="text-muted-foreground text-sm mb-3">{p.description}</p>
                {p.arguments && p.arguments.length > 0 && (
                  <div className="text-xs text-muted-foreground">
                    <span className="font-medium">Arguments:</span>{' '}
                    {p.arguments.map((a) => `${a.name}${a.default != null ? `=${a.default}` : ''}`).join(', ')}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </section>

      <section className="space-y-4">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary" />
          Skills
        </h3>
        <p className="text-sm text-muted-foreground">
          Bundled skills exposed as MCP resources (e.g. skill://virtualization-expert/SKILL.md).
        </p>
        <div className="grid gap-4">
          {skills.length === 0 ? (
            <div className="p-6 rounded-2xl border border-border bg-card/40 text-muted-foreground text-center">
              No skills available.
            </div>
          ) : (
            skills.map((s) => (
              <div
                key={s.id}
                className="rounded-2xl border border-border bg-card/40 overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => loadSkillContent(s.id)}
                  className="w-full p-6 flex items-center justify-between hover:bg-white/5 transition-colors text-left"
                >
                  <div>
                    <div className="font-bold">{s.name}</div>
                    <div className="text-sm text-muted-foreground mt-1">{s.description}</div>
                  </div>
                  {expandedSkill === s.id ? (
                    <ChevronUp className="w-5 h-5 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-muted-foreground" />
                  )}
                </button>
                {expandedSkill === s.id && skillContent[s.id] !== undefined && (
                  <div className="border-t border-border px-6 py-4 bg-background/50">
                    <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono overflow-x-auto max-h-[400px] overflow-y-auto">
                      {skillContent[s.id]}
                    </pre>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
