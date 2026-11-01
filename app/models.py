from enum import Enum
from pydantic import BaseModel

class Severity(str,Enum):
    critical="critical"
    high="high"
    medium="medium"
    low="low"
    info="info"

class AgentType(str,Enum):
    logic="logic"
    style="style"
    performance="performance"
    security="security"

class Finding(BaseModel):
    severity:Severity
    file:str | None = None#可选字段，默认值是None
    line:int|None#必填字段，单值可以是None或者Int
    message:str
    suggestion:str
    agent_type:AgentType

class ReviewResult(BaseModel):
    diff_summary:str
    findings:list[Finding]
    status:str

class DiffHunk(BaseModel):
    old_start:int
    old_lines:int
    new_start:int
    new_lines:int
    content:list[str]

class ReviewRequest(BaseModel):
    code: str
    file_name: str = ""
   

class FileDiff(BaseModel):
    file:str
    hunks:list[DiffHunk]

class ReviewFindings(BaseModel):
    findings:list[Finding]

class DiffRequest(BaseModel):
    diff_text:str

def dedup_findings(findings:list[Finding]):
    serervity={"critical":0,"high":1,"medium":2,"low":3,"info":4}
    de_duplication_findings=[]
    for f in findings:
        for newf in de_duplication_findings:
            if newf.file==f.file and newf.line==f.line and newf.agent_type==f.agent_type:
                if serervity[newf.severity]>serervity[f.severity]:
                    newf.severity=f.severity
                break
            
            
        else:
            de_duplication_findings.append(f)

    return de_duplication_findings