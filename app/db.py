from sqlalchemy import ForeignKey, create_engine,select
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,Session, relationship,selectinload
from datetime import datetime
from app.models import ReviewResult
# 定义数据库模型
class Base(DeclarativeBase):
    pass

class ReviewRecord(Base):
    __tablename__="reviews"

    id:Mapped[int]=mapped_column(primary_key=True)
    diff_summary:Mapped[str]
    status:Mapped[str]
    created_at:Mapped[datetime]=mapped_column(default=datetime.now)
    # 多键关联Finding，索引加速查询
    findings:Mapped[list["FindingRecord"]]=relationship(back_populates="review")


  


class FindingRecord(Base):
    __tablename__="findings"
    id:Mapped[int]=mapped_column(primary_key=True)
    # 外键关联ReviewRecord，索引加速查询
    review_id:Mapped[int]=mapped_column(ForeignKey("reviews.id"),index=True)
    severity:Mapped[str]
    file:Mapped[str|None]
    line:Mapped[int|None]
    message:Mapped[str]
    suggestion:Mapped[str]
    agent_type:Mapped[str]
    # 外键关联ReviewRecord，索引加速查询
    review:Mapped["ReviewRecord"]=relationship(back_populates="findings")
# 创建数据库引擎
# 连接数据库
engine=create_engine("sqlite:///./review.db",connect_args={"check_same_thread":False})

Base.metadata.create_all(engine)    

def save_review(result:ReviewResult)->int:
    with Session(engine)as session:
        review_record=ReviewRecord(
            diff_summary=result.diff_summary,
            status=result.status,   
            findings=[
                FindingRecord(
                    severity=f.severity.value,
                    file=f.file,
                    line=f.line,
                    message=f.message,
                    suggestion=f.suggestion,
                    agent_type=f.agent_type.value,
                )for f in result.findings
            ]
            
        )
        session.add(review_record)
        session.commit()
        return review_record.id

def list_reviews()->list[ReviewRecord]:
    # 查询所有ReviewRecord，关联Finding
    with Session(engine)as session:
        
        query=select(ReviewRecord).options(selectinload(ReviewRecord.findings))
        return  session.scalars(query).all()

def list_findings(review_id:int)->list[FindingRecord]:
    with Session(engine)as session:
        query=select(FindingRecord).where(FindingRecord.review_id==review_id)
        return session.scalars(query).all()
    