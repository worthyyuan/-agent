from sqlalchemy import create_engine, select, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship


# 1. 基类：所有"表对应的类"都继承它，SQLAlchemy 靠它记住一共有哪些表
#    （注意：不能 from unittest.mock import Base，那是 mock 的假类，会把这里顶掉）
class Base(DeclarativeBase):
    pass


# 2. 一对多关系：一次 review（审核）下面挂多条 finding（发现的问题）
#    多的那一方（Finding）存一个外键 review_id，指向 reviews.id
class Finding(Base):
    __tablename__ = "findings"                                        # 表名

    id: Mapped[int] = mapped_column(primary_key=True)                 # 主键，自动递增
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"))  # 外键：属于哪次 review
    message: Mapped[str]                                              # 问题描述

    # relationship = 反向关系：从一条 finding 能直接拿到它属于的那次 review
    review: Mapped["Review"] = relationship(back_populates="findings")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str]                                            # 审核的文件名

    # 一对多的"一"方：一次 review 下面挂很多 findings
    findings: Mapped[list["Finding"]] = relationship(back_populates="review")


def main():
    # 3. 连数据库：sqlite 就是连一个文件，无账号密码
    engine = create_engine("sqlite:///./review.db")

    # 4. 先删旧表再建表，保证每次运行结果干净、可重复
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # 5. Session = 一次"数据库会话"，统一管理你这一批操作（增删改查）
    with Session(engine) as session:
        # 6. 造一次 review，挂 2 条 finding
        review = Review(file_name="app.py")
        review.findings = [
            Finding(message="SQL 注入"),
            Finding(message="硬编码密钥"),
        ]

        # 7. add 只加父对象，子对象会跟着一起存（relationship 自动级联）
        session.add(review)
        session.commit()                                              # commit 才真正写进数据库

        # 8. 查出来验证：select(Review) 查所有 review
        saved = session.scalars(select(Review)).one()                 # one() = 期望恰好一条
        print("查到的 review:", saved.file_name)
        for f in saved.findings:                                      # 通过关系直接拿到子对象
            print("  - finding:", f.message)


if __name__ == "__main__":
    main()
