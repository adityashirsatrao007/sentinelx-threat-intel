import { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { ForceGraphMethods } from 'react-force-graph-2d';
import { Network, ZoomIn, ZoomOut, Maximize2, ShieldAlert } from 'lucide-react';

// Generate mock blast radius data
const generateGraphData = () => {
  const nodes: any[] = [];
  const links: any[] = [];

  // Departments (Green)
  const depts = [
    { id: 'Executive', group: 'dept', size: 12, color: '#10b981' },
    { id: 'Finance', group: 'dept', size: 12, color: '#10b981' },
    { id: 'Engineering', group: 'dept', size: 12, color: '#10b981' },
    { id: 'HR', group: 'dept', size: 12, color: '#10b981' }
  ];
  nodes.push(...depts);

  // Employees (Blue)
  const employees = [
    { id: 'alice@enron.com', group: 'emp', dept: 'Executive', size: 6, color: '#3b82f6' },
    { id: 'bob@enron.com', group: 'emp', dept: 'Finance', size: 6, color: '#3b82f6' },
    { id: 'charlie@enron.com', group: 'emp', dept: 'Engineering', size: 6, color: '#3b82f6' },
    { id: 'dave@enron.com', group: 'emp', dept: 'Finance', size: 6, color: '#3b82f6' },
    { id: 'eve@enron.com', group: 'emp', dept: 'HR', size: 6, color: '#3b82f6' },
    { id: 'frank@enron.com', group: 'emp', dept: 'Engineering', size: 6, color: '#3b82f6' },
    { id: 'grace@enron.com', group: 'emp', dept: 'Executive', size: 6, color: '#3b82f6' },
    { id: 'heidi@enron.com', group: 'emp', dept: 'HR', size: 6, color: '#3b82f6' }
  ];
  nodes.push(...employees);

  // Link employees to departments
  employees.forEach(emp => {
    links.push({ source: emp.id, target: emp.dept, value: 1, color: '#e2e8f0' });
  });

  // Attackers (Red)
  const attackers = [
    { id: 'ceo-urgent@enron-secure.com', group: 'threat', size: 15, color: '#ef4444' },
    { id: 'payroll-update@hr-portal.net', group: 'threat', size: 15, color: '#ef4444' },
    { id: 'vendor-invoice@fraud.org', group: 'threat', size: 15, color: '#ef4444' }
  ];
  nodes.push(...attackers);

  // Link attackers to employees
  const attackLinks = [
    { source: 'ceo-urgent@enron-secure.com', target: 'bob@enron.com' },
    { source: 'ceo-urgent@enron-secure.com', target: 'alice@enron.com' },
    { source: 'ceo-urgent@enron-secure.com', target: 'grace@enron.com' },
    { source: 'payroll-update@hr-portal.net', target: 'eve@enron.com' },
    { source: 'payroll-update@hr-portal.net', target: 'heidi@enron.com' },
    { source: 'payroll-update@hr-portal.net', target: 'dave@enron.com' },
    { source: 'vendor-invoice@fraud.org', target: 'bob@enron.com' },
    { source: 'vendor-invoice@fraud.org', target: 'dave@enron.com' }
  ];

  attackLinks.forEach(link => {
    links.push({ ...link, value: 2, color: '#ef4444' });
  });

  return { nodes, links };
};

interface GraphNode {
  id: string;
  group: string;
  size: number;
  color: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphLink {
  source: string;
  target: string;
  value: number;
  color: string;
  group?: string;
}

export default function ThreatGraph() {
  const fgRef = useRef<ForceGraphMethods<any> | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setGraphData(generateGraphData() as any);
    
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const handleZoomIn = useCallback(() => {
    const fg = fgRef.current as any;
    const currentZoom = fg?.zoom() || 1;
    fg?.zoom(currentZoom * 1.5, 400);
  }, []);

  const handleZoomOut = useCallback(() => {
    const fg = fgRef.current as any;
    const currentZoom = fg?.zoom() || 1;
    fg?.zoom(currentZoom / 1.5, 400);
  }, []);

  const handleFit = useCallback(() => {
    fgRef.current?.zoomToFit(400, 50);
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto h-screen flex flex-col animate-fade-in transition-colors duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-8 shrink-0">
        <div>
          <div className="flex items-center gap-2.5 text-primary mb-2.5">
            <Network className="w-5 h-5" />
            <span className="text-sm font-bold uppercase tracking-[0.3em]">Threat Topology</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight leading-none uppercase">
            Knowledge <span className="text-muted-foreground/30">Graph</span>
          </h1>
          <p className="text-muted-foreground mt-4 max-w-lg font-medium leading-relaxed">
            Visualize the blast radius of active threats. See how malicious actors connect to your internal departments and employees.
          </p>
        </div>
        
        <div className="flex bg-card border border-border p-1 rounded-xl shadow-sm">
           <div className="flex items-center gap-4 px-6 py-2">
              <div className="flex items-center gap-2">
                 <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"></div>
                 <span className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Threat Actor</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                 <span className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Employee</span>
              </div>
              <div className="flex items-center gap-2">
                 <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                 <span className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Department</span>
              </div>
           </div>
        </div>
      </div>

      <div 
        ref={containerRef}
        className="flex-1 bg-card border border-border rounded-3xl overflow-hidden shadow-inner relative group"
      >
        <div className="absolute top-6 right-6 z-10 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={handleZoomIn} className="p-3 bg-background border border-border hover:bg-muted text-foreground rounded-xl shadow-sm transition-all">
            <ZoomIn className="w-5 h-5" />
          </button>
          <button onClick={handleZoomOut} className="p-3 bg-background border border-border hover:bg-muted text-foreground rounded-xl shadow-sm transition-all">
            <ZoomOut className="w-5 h-5" />
          </button>
          <button onClick={handleFit} className="p-3 bg-background border border-border hover:bg-muted text-foreground rounded-xl shadow-sm transition-all">
            <Maximize2 className="w-5 h-5" />
          </button>
        </div>

        <ForceGraph2D
          ref={fgRef as any}
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeLabel="id"
          nodeColor={node => (node as any).color}
          nodeRelSize={1}
          nodeVal={node => (node as any).size}
          linkColor={link => (link as any).color}
          linkWidth={link => (link as any).value}
          linkDirectionalParticles={link => (link as any).group === 'threat' ? 4 : 0}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleSpeed={0.005}
          backgroundColor="hsl(var(--card))"
          onNodeDragEnd={(node: any) => {
            node.fx = node.x;
            node.fy = node.y;
          }}
        />
        
        <div className="absolute bottom-6 left-6 z-10 px-4 py-3 bg-background border border-border rounded-xl shadow-sm flex items-center gap-3">
           <ShieldAlert className="w-5 h-5 text-red-500 animate-pulse" />
           <span className="text-sm font-bold uppercase tracking-widest text-foreground">Live Physics Engine Active</span>
        </div>
      </div>
    </div>
  );
}
