# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, r'E:\code\OA_V2.1.0_Backend\OA_V2.1.0_Backend')

from module_resume_kb.service.resume_kb_service import ResumeKbService
from module_bid_kb.service.bid_kb_service import BidKbService

# ===== 模拟投标文件中的简历文本 =====
# 模拟格式：多个人员，每个人员有：简历正文 + 学信网截图OCR + 身份证截图OCR

bid_text = """
投标文件 - 2026-2027年度劳务外包（软件研发类）服务

========================================
人员简历列表
========================================

--- 人员1 ---
初级工程师-尹洁
个人信息
姓名：尹洁
性别：女
年龄：28
电话：13800138001
邮箱：yinjie@example.com

工作经历
2022-2024 某科技公司 软件工程师

=== 学历证明 - 学信网截图 ===
【中国高等教育学生信息网】
姓名：尹洁
性别：女
出生日期：1997年05月12日
院校名称：盐城工学院
专业名称：计算机科学与技术
层次：本科
学制：4年
学习形式：普通全日制
毕（结）业日期：2020年06月30日
学位：学士

=== 身份证明 - 身份证复印件 ===
中华人民共和国居民身份证
姓名 尹洁
性别 女
民族 汉
出生 1997年 5 月12日
住址 江苏省盐城市亭湖区解放路1号
公民身份号码 320901199705121234

--- 人员2 ---
高级工程师-崔恒
个人信息
姓名：崔恒
性别：男
年龄：32
电话：13800138002
邮箱：cuiheng@example.com

工作经历
2018-2024 某大型互联网公司 高级软件工程师

=== 学历证明 - 学信网截图 ===
【中国高等教育学历证书查询】
姓名：崔恒
性别：男
出生日期：1994年07月22日
入学日期：2012年09月01日
毕（结）业日期：2016年06月20日
学校名称：盐城工学院
专业：计算机科学与技术
学历类别：普通高等教育
学制：4
学习形式：普通全日制
层次：本科
毕（结）业：毕业

=== 身份证明 - 身份证复印件 ===
中华人民共和国居民身份证
姓名 崔恒
性别 男
民族 满
出生 1994年 7 月22日
住址 河北省承德市承德县六沟镇前五沟村六组45号
公民身份号码 130821199407223317

--- 人员3 ---
中级工程师-张明
个人信息
姓名：张明
性别：男
年龄：30

=== 身份证明 - 身份证复印件 ===
姓名 张明
性别 男
出生 1995年 3 月15日
公民身份号码 110101199503151234

"""

print("="*70)
print("【测试1：投标文件人员识别和分割】")
print("="*70)

# 测试分割
resumes = BidKbService._split_resumes(bid_text)
print(f"成功识别并分割出 {len(resumes)} 份简历")

for i, resume in enumerate(resumes):
    # 从简历片段中提取姓名用于显示
    import re
    name_match = re.search(r'(?:姓\s*名|姓名)\s*[:：\s]\s*([\u4e00-\u9fa5·]{2,10})', resume)
    name = name_match.group(1) if name_match else f"人员{i+1}"
    print(f"\n--- 第 {i+1} 份简历 [{name}] (长度: {len(resume)} 字符) ---")
    # 显示前300字符内容
    preview = resume[:300].replace('\n', ' | ')
    print(f"内容预览: {preview[:150]}...")

print("\n" + "="*70)
print("【测试2：学信网和身份证信息提取】")
print("="*70)

# 测试学信网和身份证提取
for i, resume in enumerate(resumes):
    print(f"\n--- 第 {i+1} 份简历解析结果 ---")
    info = {}
    ResumeKbService._extract_from_xuexin(resume, info)
    ResumeKbService._extract_from_id_card(resume, info)
    
    print(f"姓名: {info.get('name', '❌ 未提取')}")
    print(f"性别: {info.get('gender', '❌ 未提取')}")
    print(f"出生日期: {info.get('birth_date', '❌ 未提取')}")
    print(f"年龄: {info.get('age', '❌ 未提取')}")
    print(f"身份证号: {info.get('id_card_number', '❌ 未提取')}")
    print(f"学历: {info.get('education', '❌ 未提取')}")
    print(f"专业: {info.get('major', '❌ 未提取')}")
    print(f"学校: {info.get('school', '❌ 未提取')}")
    print(f"毕业日期: {info.get('graduation_date', '❌ 未提取')}")
    print(f"学位: {info.get('degree', '❌ 未提取')}")
    print(f"学制: {info.get('school_system', '❌ 未提取')}")
    print(f"学习形式: {info.get('study_form', '❌ 未提取')}")
    print(f"地址: {info.get('id_card_address', '❌ 未提取')}")

print("\n" + "="*70)
print("【测试3：完整的结构化信息提取】")
print("="*70)

# 测试完整提取流程（模拟异步调用）
import asyncio

async def test_full_extract():
    for i, resume in enumerate(resumes):
        print(f"\n--- 第 {i+1} 份简历 - 完整解析 ---")
        structured = await ResumeKbService._extract_structured_info(resume)
        
        key_fields = ['name', 'gender', 'birth_date', 'age', 'education', 'major', 
                     'school', 'graduation_date', 'degree', 'school_system', 
                     'study_form', 'id_card_number', 'id_card_address']
        
        extracted = sum(1 for k in key_fields if structured.get(k))
        print(f"✅ 成功提取 {extracted}/{len(key_fields)} 个关键字段")
        
        for k in key_fields:
            val = structured.get(k)
            if val:
                print(f"   {k}: {val}")

asyncio.run(test_full_extract())

print("\n" + "="*70)
print("【测试完成】")
print("="*70)