"""
harness/local_mcp.py
Local Model Context Protocol (MCP) Engine for Sovereign AI Workbench.
Standardizes tool schemas and execution according to the open Model Context Protocol.
Enables pluggable, zero-downtime tool registration for any open-weight SLM.
100% Air-Gapped / In-Memory JSON-RPC transport.
"""

from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel, Field


class MCPToolSchema(BaseModel):
    """Standard Model Context Protocol tool declaration."""
    name: str = Field(description="Unique tool identifier")
    description: str = Field(description="Detailed explanation of tool functionality")
    input_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema defining required and optional arguments"
    )


class MCPToolCall(BaseModel):
    """An invocation of an MCP tool."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPToolResult(BaseModel):
    """The result returned by an MCP tool."""
    tool_name: str
    content: Any
    is_error: bool = False
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class LocalMCPEngine:
    """
    On-Premise Model Context Protocol (MCP) Registry and Dispatcher.
    Serves as the universal bridge between local SLMs and deterministic industrial tools.
    """

    def __init__(self):
        self._tools: Dict[str, MCPToolSchema] = {}
        self._handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._register_default_industrial_tools()

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Any]
    ):
        """Registers a new industrial tool into the MCP engine."""
        schema = MCPToolSchema(name=name, description=description, input_schema=input_schema)
        self._tools[name] = schema
        self._handlers[name] = handler

    def list_tools(self) -> List[MCPToolSchema]:
        """Returns all registered MCP tool definitions."""
        return list(self._tools.values())

    def get_tool_schema(self, name: str) -> Optional[MCPToolSchema]:
        """Retrieves schema for a specific MCP tool."""
        return self._tools.get(name)

    def call_tool(self, call: MCPToolCall) -> MCPToolResult:
        """
        Executes a registered tool handler with validation.
        """
        import time
        if call.tool_name not in self._handlers:
            return MCPToolResult(
                tool_name=call.tool_name,
                content=None,
                is_error=True,
                error_message=f"MCP Tool '{call.tool_name}' not found in registry."
            )

        handler = self._handlers[call.tool_name]
        t0 = time.time()
        try:
            result = handler(call.arguments)
            elapsed_ms = (time.time() - t0) * 1000
            return MCPToolResult(
                tool_name=call.tool_name,
                content=result,
                is_error=False,
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.time() - t0) * 1000
            return MCPToolResult(
                tool_name=call.tool_name,
                content=None,
                is_error=True,
                error_message=str(e),
                execution_time_ms=round(elapsed_ms, 2)
            )

    def _register_default_industrial_tools(self):
        """Pre-loads standard MRPL refinery calculation and retrieval tools into MCP."""
        from harness.sandbox import CalculationSandbox
        from harness.sovereign_rag import SovereignRAG
        from harness.multimodal_parser import MultimodalParser

        sandbox = CalculationSandbox()
        rag = SovereignRAG()
        rag.load_file("data/refinery_sop_handbook.txt")

        # 1. ASME B31.3 Calculator
        def handle_asme_calc(args: Dict[str, Any]):
            p = float(args.get("design_pressure_mpa", 4.0))
            d = float(args.get("outer_diameter_mm", 219.1))
            s = float(args.get("allowable_stress_mpa", 137.0))
            ca = float(args.get("corrosion_allowance_mm", 3.0))
            t_meas = float(args.get("measured_thickness_mm", 7.48))
            cr = float(args.get("annual_corrosion_rate_mm", 0.25))

            script = sandbox.generate_asme_b31_3_script(
                design_pressure_mpa=p,
                outer_diameter_mm=d,
                allowable_stress_mpa=s,
                corrosion_allowance_mm=ca,
                measured_thickness_mm=t_meas,
                annual_corrosion_rate_mm_yr=cr
            )
            res = sandbox.execute(script)
            if not res.success:
                raise RuntimeError(res.error)
            return res.output

        self.register_tool(
            name="asme_b31_3_calculator",
            description="Executes ASME B31.3 modified Barlow formula in an isolated subprocess to calculate minimum wall thickness and remaining safe life.",
            input_schema={
                "type": "object",
                "properties": {
                    "design_pressure_mpa": {"type": "number", "description": "Design pressure in MPa"},
                    "outer_diameter_mm": {"type": "number", "description": "Pipe outer diameter in mm"},
                    "allowable_stress_mpa": {"type": "number", "description": "Allowable material stress in MPa"},
                    "corrosion_allowance_mm": {"type": "number", "default": 3.0},
                    "measured_thickness_mm": {"type": "number", "description": "Ultrasonic minimum measured thickness in mm"},
                    "annual_corrosion_rate_mm": {"type": "number", "default": 0.25}
                },
                "required": ["design_pressure_mpa", "outer_diameter_mm", "allowable_stress_mpa"]
            },
            handler=handle_asme_calc
        )

        # 2. Sovereign RAG Lookup
        def handle_rag_search(args: Dict[str, Any]):
            query = args.get("query", "")
            k = int(args.get("top_k", 3))
            return rag.search(query, top_k=k)

        self.register_tool(
            name="sovereign_sop_lookup",
            description="Searches MRPL refinery Standard Operating Procedures and Delegation of Power policies offline using BM25.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SOP query or policy search term"},
                    "top_k": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            },
            handler=handle_rag_search
        )

        # 3. Excel Inspection Parser
        def handle_excel_parse(args: Dict[str, Any]):
            path = args.get("file_path", "data/sample_boiler_inspection_data.xlsx")
            return MultimodalParser.parse_excel_inspection_report(path)

        self.register_tool(
            name="parse_ultrasonic_excel",
            description="Parses an ultrasonic boiler tube inspection Excel workbook and extracts grid thickness readings.",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Relative or absolute path to .xlsx file"}
                },
                "required": ["file_path"]
            },
            handler=handle_excel_parse
        )
