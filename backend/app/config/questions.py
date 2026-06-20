"""Investor risk assessment questionnaire — 15 questions covering financial
status, investment experience, risk attitude, and behavioral patterns.

Each question has 5 choices (A-E) with scores 1-5 that map directly to the
existing ``_calculate_risk_score`` algorithm in UserService.
"""

from app.schemas.user import Choice, RiskQuestion

RISK_QUESTIONS: list[RiskQuestion] = [
    # ==================================================================
    # 财务状况与投资目标 (Q1-4)
    # ==================================================================
    RiskQuestion(
        question_id=1,
        question_text="您的年龄范围是？",
        choices=[
            Choice(label="A", text="60岁以上", score=1),
            Choice(label="B", text="51-60岁", score=2),
            Choice(label="C", text="41-50岁", score=3),
            Choice(label="D", text="31-40岁", score=4),
            Choice(label="E", text="30岁以下", score=5),
        ],
    ),
    RiskQuestion(
        question_id=2,
        question_text="您的家庭年收入状况是？",
        choices=[
            Choice(label="A", text="10万元以下", score=1),
            Choice(label="B", text="10-30万元", score=2),
            Choice(label="C", text="30-50万元", score=3),
            Choice(label="D", text="50-100万元", score=4),
            Choice(label="E", text="100万元以上", score=5),
        ],
    ),
    RiskQuestion(
        question_id=3,
        question_text="您目前的可投资资产（不含自住房产）规模为？",
        choices=[
            Choice(label="A", text="10万元以下", score=1),
            Choice(label="B", text="10-50万元", score=2),
            Choice(label="C", text="50-100万元", score=3),
            Choice(label="D", text="100-500万元", score=4),
            Choice(label="E", text="500万元以上", score=5),
        ],
    ),
    RiskQuestion(
        question_id=4,
        question_text="您计划将资产投资于股票/基金等风险资产的比例是？",
        choices=[
            Choice(label="A", text="0%（不投资）", score=1),
            Choice(label="B", text="10%以下", score=2),
            Choice(label="C", text="10%-30%", score=3),
            Choice(label="D", text="30%-50%", score=4),
            Choice(label="E", text="50%以上", score=5),
        ],
    ),
    # ==================================================================
    # 投资经验与知识水平 (Q5-8)
    # ==================================================================
    RiskQuestion(
        question_id=5,
        question_text="您的证券/基金投资经验有多久？",
        choices=[
            Choice(label="A", text="没有经验", score=1),
            Choice(label="B", text="不到1年", score=2),
            Choice(label="C", text="1-3年", score=3),
            Choice(label="D", text="3-10年", score=4),
            Choice(label="E", text="10年以上", score=5),
        ],
    ),
    RiskQuestion(
        question_id=6,
        question_text="您对以下哪类金融产品最熟悉？",
        choices=[
            Choice(label="A", text="银行存款/国债", score=1),
            Choice(label="B", text="货币基金/银行理财", score=2),
            Choice(label="C", text="债券基金/偏债混合", score=3),
            Choice(label="D", text="股票基金/指数基金", score=4),
            Choice(label="E", text="个股/期货/期权", score=5),
        ],
    ),
    RiskQuestion(
        question_id=7,
        question_text="您进行投资决策的主要方式是？",
        choices=[
            Choice(label="A", text="听从他人推荐，很少自己做决定", score=1),
            Choice(label="B", text="主要参考银行/券商理财经理建议", score=2),
            Choice(label="C", text="参考专业机构研究报告", score=3),
            Choice(label="D", text="自己分析基本面和技术面", score=4),
            Choice(label="E", text="自主研究并结合量化工具分析", score=5),
        ],
    ),
    RiskQuestion(
        question_id=8,
        question_text="您如何评价自己的投资知识水平？",
        choices=[
            Choice(label="A", text="完全不了解投资", score=1),
            Choice(label="B", text="了解一些基本概念", score=2),
            Choice(label="C", text="有一定的投资知识和经验", score=3),
            Choice(label="D", text="具备较丰富的投资知识", score=4),
            Choice(label="E", text="具备专业水平的投资知识", score=5),
        ],
    ),
    # ==================================================================
    # 风险承受意愿 (Q9-12)
    # ==================================================================
    RiskQuestion(
        question_id=9,
        question_text="假设您持有一只基金，短期内下跌了15%，您会怎么做？",
        choices=[
            Choice(label="A", text="立即全部赎回，避免更大损失", score=1),
            Choice(label="B", text="赎回大部分，保留小部分观察", score=2),
            Choice(label="C", text="持仓不动，等待反弹", score=3),
            Choice(label="D", text="适当补仓，摊低成本", score=4),
            Choice(label="E", text="大幅加仓，认为是难得的买入机会", score=5),
        ],
    ),
    RiskQuestion(
        question_id=10,
        question_text="您能承受的最大年度投资亏损是？",
        choices=[
            Choice(label="A", text="不能承受任何亏损", score=1),
            Choice(label="B", text="亏损不超过5%", score=2),
            Choice(label="C", text="亏损5%-10%", score=3),
            Choice(label="D", text="亏损10%-20%", score=4),
            Choice(label="E", text="亏损20%以上也可以接受", score=5),
        ],
    ),
    RiskQuestion(
        question_id=11,
        question_text="您的投资目标是？",
        choices=[
            Choice(label="A", text="资产保值，跑赢通胀即可", score=1),
            Choice(label="B", text="获取稳定的固定收益", score=2),
            Choice(label="C", text="兼顾收益与安全，平衡配置", score=3),
            Choice(label="D", text="追求资产中长期增值", score=4),
            Choice(label="E", text="追求高收益，愿意承担较大风险", score=5),
        ],
    ),
    RiskQuestion(
        question_id=12,
        question_text="您期望的投资期限是？",
        choices=[
            Choice(label="A", text="1年以内", score=1),
            Choice(label="B", text="1-2年", score=2),
            Choice(label="C", text="2-3年", score=3),
            Choice(label="D", text="3-5年", score=4),
            Choice(label="E", text="5年以上", score=5),
        ],
    ),
    # ==================================================================
    # 投资行为倾向 (Q13-15)
    # ==================================================================
    RiskQuestion(
        question_id=13,
        question_text="您通常多久进行一次交易操作？",
        choices=[
            Choice(label="A", text="几乎不交易，买入后长期持有", score=1),
            Choice(label="B", text="每季度调仓一次", score=2),
            Choice(label="C", text="每月操作1-2次", score=3),
            Choice(label="D", text="每周操作", score=4),
            Choice(label="E", text="频繁交易，每日操作", score=5),
        ],
    ),
    RiskQuestion(
        question_id=14,
        question_text="您是否使用过融资融券、股指期货等杠杆工具？",
        choices=[
            Choice(label="A", text="完全不了解，也不会使用", score=1),
            Choice(label="B", text="了解但从未使用", score=2),
            Choice(label="C", text="偶尔使用，杠杆比例很低", score=3),
            Choice(label="D", text="会使用，杠杆控制在1倍以内", score=4),
            Choice(label="E", text="经常使用，可接受较高杠杆", score=5),
        ],
    ),
    RiskQuestion(
        question_id=15,
        question_text="您获取投资信息的主要渠道是？",
        choices=[
            Choice(label="A", text="银行/券商客户经理推荐", score=1),
            Choice(label="B", text="财经新闻和电视节目", score=2),
            Choice(label="C", text="专业财经网站和App", score=3),
            Choice(label="D", text="上市公司公告和研报", score=4),
            Choice(label="E", text="专业的金融数据终端（如Wind、Bloomberg）", score=5),
        ],
    ),
]
