"""
2025-06-03
By Unclcode:
C4A-Script Language Documentation    
Feeds Crawl4AI via CrawlerRunConfig(js_code=[ ... ]) – no core modifications.
"""

from __future__ import annotations
import pathlib, re, sys, textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Union

from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedToken, UnexpectedCharacters, VisitError


# --------------------------------------------------------------------------- #
# Custom Error Classes
# --------------------------------------------------------------------------- #
class C4AScriptError(Exception):
    """Custom error class for C4A-Script compilation errors"""
    
    def __init__(self, message: str, line: int = None, column: int = None, 
                 error_type: str = "Syntax Error", details: str = None):
        self.message = message
        self.line = line
        self.column = column
        self.error_type = error_type
        self.details = details
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Format a clear error message"""
        lines = [f"\n{'='*60}"]
        lines.append(f"C4A-Script {self.error_type}")
        lines.append(f"{'='*60}")
        
        if self.line:
            lines.append(f"Location: Line {self.line}" + (f", Column {self.column}" if self.column else ""))
        
        lines.append(f"Error: {self.message}")
        
        if self.details:
            lines.append(f"\nDetails: {self.details}")
        
        lines.append("="*60)
        return "\n".join(lines)
    
    @classmethod
    def from_exception(cls, exc: Exception, script: Union[str, List[str]]) -> 'C4AScriptError':
        """Create C4AScriptError from another exception"""
        script_text = script if isinstance(script, str) else '\n'.join(script)
        script_lines = script_text.split('\n')
        
        if isinstance(exc, UnexpectedToken):
            # Extract line and column from UnexpectedToken
            line = exc.line
            column = exc.column
            
            # Get the problematic line
            if 0 < line <= len(script_lines):
                problem_line = script_lines[line - 1]
                marker = " " * (column - 1) + "^"
                
                details = f"\nCode:\n  {problem_line}\n  {marker}\n"
                
                # Improve error message based on context
                if exc.token.type == 'CLICK' and 'THEN' in str(exc.expected):
                    message = "Missing 'THEN' keyword after IF condition"
                elif exc.token.type == '$END':
                    message = "Unexpected end of script. Check for missing ENDPROC or incomplete commands"
                elif 'RPAR' in str(exc.expected):
                    message = "Missing closing parenthesis ')'"
                elif 'COMMA' in str(exc.expected):
                    message = "Missing comma ',' in command"
                else:
                    message = f"Unexpected '{exc.token}'"
                    if exc.expected:
                        expected_list = [str(e) for e in exc.expected if not e.startswith('_')]
                        if expected_list:
                            message += f". Expected: {', '.join(expected_list[:3])}"
                
                details += f"Token: {exc.token.type} ('{exc.token.value}')"
            else:
                message = str(exc)
                details = None
            
            return cls(message, line, column, "Syntax Error", details)
        
        elif isinstance(exc, UnexpectedCharacters):
            # Extract line and column
            line = exc.line
            column = exc.column
            
            if 0 < line <= len(script_lines):
                problem_line = script_lines[line - 1]
                marker = " " * (column - 1) + "^"
                
                details = f"\nCode:\n  {problem_line}\n  {marker}\n"
                message = f"Invalid character or unexpected text at position {column}"
            else:
                message = str(exc)
                details = None
            
            return cls(message, line, column, "Syntax Error", details)
        
        elif isinstance(exc, ValueError):
            # Handle runtime errors like undefined procedures
            message = str(exc)
            
            # Try to find which line caused the error
            if "Unknown procedure" in message:
                proc_name = re.search(r"'([^']+)'", message)
                if proc_name:
                    proc_name = proc_name.group(1)
                    for i, line in enumerate(script_lines, 1):
                        if proc_name in line and not line.strip().startswith('PROC'):
                            details = f"\nCode:\n  {line.strip()}\n\nMake sure the procedure '{proc_name}' is defined with PROC...ENDPROC"
                            return cls(f"Undefined procedure '{proc_name}'", i, None, "Runtime Error", details)
            
            return cls(message, None, None, "Runtime Error", None)
        
        else:
            # Generic error
            return cls(str(exc), None, None, "Compilation Error", None)


# --------------------------------------------------------------------------- #
# 1. Grammar
# --------------------------------------------------------------------------- #
GRAMMAR = r"""
start           : line*
?line           : command | proc_def | include | comment

command         : wait | nav | click_cmd | double_click | right_click | move | drag | scroll
                | type | clear | set_input | press | key_down | key_up
                | eval_cmd | setvar | proc_call | if_cmd | repeat_cmd

wait            : "WAIT" (ESCAPED_STRING|BACKTICK_STRING|NUMBER) NUMBER? -> wait_cmd
nav             : "GO" URL                             -> go
                | "RELOAD"                             -> reload
                | "BACK"                               -> back
                | "FORWARD"                            -> forward

click_cmd       : "CLICK" (BACKTICK_STRING|NUMBER NUMBER) -> click
double_click    : "DOUBLE_CLICK" (BACKTICK_STRING|NUMBER NUMBER) -> double_click  
right_click     : "RIGHT_CLICK" (BACKTICK_STRING|NUMBER NUMBER) -> right_click

move            : "MOVE" coords                        -> move
drag            : "DRAG" coords coords                 -> drag
scroll          : "SCROLL" DIR NUMBER?                 -> scroll

type            : "TYPE" (ESCAPED_STRING | NAME)       -> type
clear           : "CLEAR" BACKTICK_STRING              -> clear
set_input       : "SET" BACKTICK_STRING (ESCAPED_STRING | BACKTICK_STRING | NAME) -> set_input
press           : "PRESS" WORD                         -> press
key_down        : "KEY_DOWN" WORD                      -> key_down
key_up          : "KEY_UP" WORD                        -> key_up

eval_cmd        : "EVAL" BACKTICK_STRING               -> eval_cmd
setvar          : "SETVAR" NAME "=" value              -> setvar
proc_call       : NAME                                 -> proc_call
proc_def        : "PROC" NAME line* "ENDPROC"          -> proc_def
include         : "USE" ESCAPED_STRING                 -> include
comment         : /#.*/                                -> comment

if_cmd          : "IF" "(" condition ")" "THEN" command ("ELSE" command)?  -> if_cmd
repeat_cmd      : "REPEAT" "(" command "," repeat_count ")"  -> repeat_cmd

condition       : not_cond | exists_cond | js_cond
not_cond        : "NOT" condition                      -> not_cond
exists_cond     : "EXISTS" BACKTICK_STRING             -> exists_cond
js_cond         : BACKTICK_STRING                      -> js_cond

repeat_count    : NUMBER | BACKTICK_STRING

coords          : NUMBER NUMBER
value           : ESCAPED_STRING | BACKTICK_STRING | NUMBER
DIR             : /(UP|DOWN|LEFT|RIGHT)/i
REST            : /[^\n]+/

URL             : /(http|https):\/\/[^\s]+/
NAME            : /\$?[A-Za-z_][A-Za-z0-9_]*/
WORD            : /[A-Za-z0-9+]+/
BACKTICK_STRING : /`[^`]*`/

%import common.NUMBER
%import common.ESCAPED_STRING
%import common.WS_INLINE
%import common.NEWLINE
%ignore WS_INLINE
%ignore NEWLINE
"""

# --------------------------------------------------------------------------- #
# 2. IR dataclasses
# --------------------------------------------------------------------------- #
@dataclass
class Cmd:
    op: str
    args: List[Any]

@dataclass
class Proc:
    name: str
    body: List[Cmd]

# --------------------------------------------------------------------------- #
# 3. AST → IR
# --------------------------------------------------------------------------- #
@v_args(inline=True)
class ASTBuilder(Transformer):
    # helpers
    def _strip(self, s): 
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        elif s.startswith('`') and s.endswith('`'):
            return s[1:-1]
        return s
    def start(self,*i):  return list(i)
    def line(self,i):    return i
    def command(self,i): return i

    # WAIT
    def wait_cmd(self, rest, timeout=None):
        rest_str = str(rest)
        # Check if it's a number (including floats)
        try:
            num_val = float(rest_str)
            payload = (num_val, "seconds")
        except ValueError:
            if rest_str.startswith('"') and rest_str.endswith('"'):
                payload = (self._strip(rest_str), "text")
            elif rest_str.startswith('`') and rest_str.endswith('`'):
                payload = (self._strip(rest_str), "selector")
            else:
                payload = (rest_str, "selector")
        return Cmd("WAIT", [payload, int(timeout) if timeout else None])

    # NAV
    def go(self,u):    return Cmd("GO",[str(u)])
    def reload(self):  return Cmd("RELOAD",[])
    def back(self):    return Cmd("BACK",[])
    def forward(self): return Cmd("FORWARD",[])

    # CLICK, DOUBLE_CLICK, RIGHT_CLICK
    def click(self, *args):
        return self._handle_click("CLICK", args)
    
    def double_click(self, *args):
        return self._handle_click("DBLCLICK", args)
    
    def right_click(self, *args):
        return self._handle_click("RIGHTCLICK", args)
    
    def _handle_click(self, op, args):
        if len(args) == 1:
            # Single argument - backtick string
            target = self._strip(str(args[0]))
            return Cmd(op, [("selector", target)])
        else:
            # Two arguments - coordinates
            x, y = args
            return Cmd(op, [("coords", int(x), int(y))])


    # MOVE / DRAG / SCROLL
    def coords(self,x,y):       return ("coords",int(x),int(y))
    def move(self,c):           return Cmd("MOVE",[c])
    def drag(self,c1,c2):       return Cmd("DRAG",[c1,c2])
    def scroll(self,dir_tok,amt=None):
        return Cmd("SCROLL",[dir_tok.upper(), int(amt) if amt else 500])

    # KEYS
    def type(self,tok):     return Cmd("TYPE",[self._strip(str(tok))])
    def clear(self,sel):    return Cmd("CLEAR",[self._strip(str(sel))])
    def set_input(self,sel,val): return Cmd("SET",[self._strip(str(sel)), self._strip(str(val))])
    def press(self,w):      return Cmd("PRESS",[str(w)])
    def key_down(self,w):   return Cmd("KEYDOWN",[str(w)])
    def key_up(self,w):     return Cmd("KEYUP",[str(w)])

    # FLOW
    def eval_cmd(self,txt):     return Cmd("EVAL",[self._strip(str(txt))])
    def setvar(self,n,v):      
        # v might be a Token or a Tree, extract value properly
        if hasattr(v, 'value'):
            value = v.value
        elif hasattr(v, 'children') and len(v.children) > 0:
            value = v.children[0].value
        else:
            value = str(v)
        return Cmd("SETVAR",[str(n), self._strip(value)])
    def proc_call(self,n):      return Cmd("CALL",[str(n)])
    def proc_def(self,n,*body): return Proc(str(n),[b for b in body if isinstance(b,Cmd)])
    def include(self,p):        return Cmd("INCLUDE",[self._strip(p)])
    def comment(self,*_):       return Cmd("NOP",[])
    
    # IF-THEN-ELSE and EXISTS
    def if_cmd(self, condition, then_cmd, else_cmd=None):
        return Cmd("IF", [condition, then_cmd, else_cmd])
    
    def condition(self, cond):
        return cond
    
    def not_cond(self, cond):
        return ("NOT", cond)
    
    def exists_cond(self, selector):
        return ("EXISTS", self._strip(str(selector)))
    
    def js_cond(self, expr):
        return ("JS", self._strip(str(expr)))
    
    # REPEAT
    def repeat_cmd(self, cmd, count):
        return Cmd("REPEAT", [cmd, count])
    
    def repeat_count(self, value):
        return str(value)

# --------------------------------------------------------------------------- #
# 4. Compiler
# --------------------------------------------------------------------------- #
class Compiler:
    def __init__(self, root: pathlib.Path|None=None):
        self.parser = Lark(GRAMMAR,start="start",parser="lalr")
        self.root   = pathlib.Path(root or ".").resolve()
        self.vars: Dict[str,Any] = {}
        self.procs: Dict[str,Proc]= {}

    def compile(self, text: Union[str, List[str]]) -> List[str]:
        # Handle list input by joining with newlines
        if isinstance(text, list):
            text = '\n'.join(text)
        
        ir = self._parse_with_includes(text)
        ir = self._collect_procs(ir)
        ir = self._inline_calls(ir)
        ir = self._apply_set_vars(ir)
        return [self._emit_js(c) for c in ir if isinstance(c,Cmd) and c.op!="NOP"]

    # passes
    def _parse_with_includes(self,txt,seen=None):
        seen=seen or set()
        cmds=ASTBuilder().transform(self.parser.parse(txt))
        out=[]
        for c in cmds:
            if isinstance(c,Cmd) and c.op=="INCLUDE":
                p=(self.root/c.args[0]).resolve()
                if p in seen: raise ValueError(f"Circular include {p}")
                seen.add(p); out+=self._parse_with_includes(p.read_text(),seen)
            else: out.append(c)
        return out

    def _collect_procs(self,ir):
        out=[]
        for i in ir:
            if isinstance(i,Proc): self.procs[i.name]=i
            else: out.append(i)
        return out

    def _inline_calls(self,ir):
        out=[]
        for c in ir:
            if isinstance(c,Cmd) and c.op=="CALL":
                if c.args[0] not in self.procs:
                    raise ValueError(f"Unknown procedure {c.args[0]!r}")
                out+=self._inline_calls(self.procs[c.args[0]].body)
            else: out.append(c)
        return out

    def _apply_set_vars(self,ir):
        def sub(s): return re.sub(r"\$(\w+)",lambda m:str(self.vars.get(m.group(1),m.group(0))) ,s) if isinstance(s,str) else s
        out=[]
        for c in ir:
            if isinstance(c,Cmd):
                if c.op=="SETVAR":
                    # Store variable
                    self.vars[c.args[0].lstrip('$')]=c.args[1]
                else:
                    # Apply variable substitution to commands that use them
                    if c.op in("TYPE","EVAL","SET"): c.args=[sub(a) for a in c.args]
                    out.append(c)
        return out

    # JS emitter
    def _emit_js(self, cmd: Cmd) -> str:
        op, a = cmd.op, cmd.args
        if op == "GO":         return f"window.location.href = '{a[0]}';"
        if op == "RELOAD":     return "window.location.reload();"
        if op == "BACK":       return "window.history.back();"
        if op == "FORWARD":    return "window.history.forward();"

        if op == "WAIT":
            arg, kind = a[0]
            timeout   = a[1] or 10
            if kind == "seconds":
                return f"await new Promise(r=>setTimeout(r,{arg}*1000));"
            if kind == "selector":
                sel = arg.replace("\\","\\\\").replace("'","\\'")
                return textwrap.dedent(f"""
                    await new Promise((res,rej)=>{{
                      const max = {timeout*1000}, t0 = performance.now();
                      const id = setInterval(()=>{{
                        if(document.querySelector('{sel}')){{clearInterval(id);res();}}
                        else if(performance.now()-t0>max){{clearInterval(id);rej('WAIT selector timeout');}}
                      }},100);
                    }});
                """).strip()
            if kind == "text":
                txt = arg.replace('`', '\\`')
                return textwrap.dedent(f"""
                    await new Promise((res,rej)=>{{
                      const max={timeout*1000},t0=performance.now();
                      const id=setInterval(()=>{{
                        if(document.body.innerText.includes(`{txt}`)){{clearInterval(id);res();}}
                        else if(performance.now()-t0>max){{clearInterval(id);rej('WAIT text timeout');}}
                      }},100);
                    }});
                """).strip()

        # click-style helpers
        def _js_click(sel, evt="click", button=0, detail=1):
            sel = sel.replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.querySelector('{sel}');
                  if(el){{
                    el.focus&&el.focus();
                    el.dispatchEvent(new MouseEvent('{evt}',{{bubbles:true,button:{button},detail:{detail}}}));
                  }}
                }})();
            """).strip()

        def _js_click_xy(x, y, evt="click", button=0, detail=1):
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.elementFromPoint({x},{y});
                  if(el){{
                    el.focus&&el.focus();
                    el.dispatchEvent(new MouseEvent('{evt}',{{bubbles:true,button:{button},detail:{detail}}}));
                  }}
                }})();
            """).strip()

        if op in ("CLICK", "DBLCLICK", "RIGHTCLICK"):
            evt   = {"CLICK":"click","DBLCLICK":"dblclick","RIGHTCLICK":"contextmenu"}[op]
            btn   = 2 if op=="RIGHTCLICK" else 0
            det   = 2 if op=="DBLCLICK"   else 1
            kind,*rest = a[0]
            return _js_click_xy(*rest) if kind=="coords" else _js_click(rest[0],evt,btn,det)

        if op == "MOVE":
            _, x, y = a[0]
            return textwrap.dedent(f"""
                document.dispatchEvent(new MouseEvent('mousemove',{{clientX:{x},clientY:{y},bubbles:true}}));
            """).strip()

        if op == "DRAG":
            (_, x1, y1), (_, x2, y2) = a
            return textwrap.dedent(f"""
                (()=>{{
                  const s=document.elementFromPoint({x1},{y1});
                  if(!s) return;
                  s.dispatchEvent(new MouseEvent('mousedown',{{bubbles:true,clientX:{x1},clientY:{y1}}}));
                  document.dispatchEvent(new MouseEvent('mousemove',{{bubbles:true,clientX:{x2},clientY:{y2}}}));
                  document.dispatchEvent(new MouseEvent('mouseup',  {{bubbles:true,clientX:{x2},clientY:{y2}}}));
                }})();
            """).strip()

        if op == "SCROLL":
            dir_, amt = a
            dx, dy = {"UP":(0,-amt),"DOWN":(0,amt),"LEFT":(-amt,0),"RIGHT":(amt,0)}[dir_]
            return f"window.scrollBy({dx},{dy});"

        if op == "TYPE":
            txt = a[0].replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.activeElement;
                  if(el){{
                    el.value += '{txt}';
                    el.dispatchEvent(new Event('input',{{bubbles:true}}));
                  }}
                }})();
            """).strip()

        if op == "CLEAR":
            sel = a[0].replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.querySelector('{sel}');
                  if(el && 'value' in el){{
                    el.value = '';
                    el.dispatchEvent(new Event('input',{{bubbles:true}}));
                    el.dispatchEvent(new Event('change',{{bubbles:true}}));
                  }}
                }})();
            """).strip()

        if op == "SET" and len(a) == 2:
            # This is SET for input fields (SET `#field` "value")
            sel = a[0].replace("'", "\\'")
            val = a[1].replace("'", "\\'")
            return textwrap.dedent(f"""
                (()=>{{
                  const el=document.querySelector('{sel}');
                  if(el && 'value' in el){{
                    el.value = '';
                    el.focus&&el.focus();
                    el.value = '{val}';
                    el.dispatchEvent(new Event('input',{{bubbles:true}}));
                    el.dispatchEvent(new Event('change',{{bubbles:true}}));
                  }}
                }})();
            """).strip()

        if op in ("PRESS","KEYDOWN","KEYUP"):
            key = a[0]
            evs = {"PRESS":("keydown","keyup"),"KEYDOWN":("keydown",),"KEYUP":("keyup",)}[op]
            return ";".join([f"document.dispatchEvent(new KeyboardEvent('{e}',{{key:'{key}',bubbles:true}}))" for e in evs]) + ";"

        if op == "EVAL":
            return textwrap.dedent(f"""
                (()=>{{
                  try {{
                    {a[0]};
                  }} catch (e) {{
                    console.error('C4A-Script EVAL error:', e);
                  }}
                }})();
            """).strip()
        
        if op == "IF":
            condition, then_cmd, else_cmd = a
            
            # Generate condition JavaScript
            js_condition = self._emit_condition(condition)
            
            # Generate commands - handle both regular commands and procedure calls
            then_js = self._handle_cmd_or_proc(then_cmd)
            else_js = self._handle_cmd_or_proc(else_cmd) if else_cmd else ""
            
            if else_cmd:
                return textwrap.dedent(f"""
                    if ({js_condition}) {{
                      {then_js}
                    }} else {{
                      {else_js}
                    }}
                """).strip()
            else:
                return textwrap.dedent(f"""
                    if ({js_condition}) {{
                      {then_js}
                    }}
                """).strip()
        
        if op == "REPEAT":
            cmd, count = a
            
            # Handle the count - could be number or JS expression
            if count.isdigit():
                # Simple number
                repeat_js = self._handle_cmd_or_proc(cmd)
                return textwrap.dedent(f"""
                    for (let _i = 0; _i < {count}; _i++) {{
                      {repeat_js}
                    }}
                """).strip()
            else:
                # JS expression (from backticks)
                count_expr = count[1:-1] if count.startswith('`') and count.endswith('`') else count
                repeat_js = self._handle_cmd_or_proc(cmd)
                return textwrap.dedent(f"""
                    (()=>{{
                      const _count = {count_expr};
                      if (typeof _count === 'number') {{
                        for (let _i = 0; _i < _count; _i++) {{
                          {repeat_js}
                        }}
                      }} else if (_count) {{
                        {repeat_js}
                      }}
                    }})();
                """).strip()

        raise ValueError(f"Unhandled op {op}")
    
    def _emit_condition(self, condition):
        """Convert a condition tuple to JavaScript"""
        cond_type = condition[0]
        
        if cond_type == "EXISTS":
            return f"!!document.querySelector('{condition[1]}')"
        elif cond_type == "NOT":
            # Recursively handle the negated condition
            inner_condition = self._emit_condition(condition[1])
            return f"!({inner_condition})"
        else:  # JS condition
            return condition[1]
    
    def _handle_cmd_or_proc(self, cmd):
        """Handle a command that might be a regular command or a procedure call"""
        if not cmd:
            return ""
        
        if isinstance(cmd, Cmd):
            if cmd.op == "CALL":
                # Inline the procedure
                if cmd.args[0] not in self.procs:
                    raise ValueError(f"Unknown procedure {cmd.args[0]!r}")
                proc_body = self.procs[cmd.args[0]].body
                return "\n".join([self._emit_js(c) for c in proc_body if c.op != "NOP"])
            else:
                return self._emit_js(cmd)
        return ""

# --------------------------------------------------------------------------- #
# 5. Helpers + demo
# --------------------------------------------------------------------------- #

def compile_string(script: Union[str, List[str]], *, root: Union[pathlib.Path, None] = None) -> List[str]:
    """Compile C4A-Script from string or list of strings to JavaScript.
    
    Args:
        script: C4A-Script as a string or list of command strings
        root: Root directory for resolving includes (optional)
    
    Returns:
        List of JavaScript command strings
    
    Raises:
        C4AScriptError: When compilation fails with detailed error information
    """
    try:
        return Compiler(root).compile(script)
    except Exception as e:
        # Wrap the error with better formatting
        raise C4AScriptError.from_exception(e, script)

def compile_file(path: pathlib.Path) -> List[str]:
    """Compile C4A-Script from file to JavaScript.
    
    Args:
        path: Path to C4A-Script file
    
    Returns:
        List of JavaScript command strings
    """
    return compile_string(path.read_text(), root=path.parent)

def compile_lines(lines: List[str], *, root: Union[pathlib.Path, None] = None) -> List[str]:
    """Compile C4A-Script from list of lines to JavaScript.
    
    Args:
        lines: List of C4A-Script command lines
        root: Root directory for resolving includes (optional)
    
    Returns:
        List of JavaScript command strings
    """
    return compile_string(lines, root=root)

DEMO = """
# quick sanity demo
PROC login
  SET `input[name="username"]` $user
  SET `input[name="password"]` $pass
  CLICK `button.submit`
ENDPROC

SETVAR user = "tom@crawl4ai.com"
SETVAR pass = "hunter2"

GO https://example.com/login
WAIT `input[name="username"]` 10
login
WAIT 3
EVAL `console.log('logged in')`
"""

if __name__ == "__main__":
    if len(sys.argv) == 2:
        for js in compile_file(pathlib.Path(sys.argv[1])):
            print(js)
    else:
        print("=== DEMO ===")
        for js in compile_string(DEMO):
            print(js)
