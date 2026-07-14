"""
招标文件智能生成模块服务层
"""
import json
import os
import re
import time
import uuid
import asyncio
from typing import Any
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_tender.dao.tender_dao import TenderDao
from module_tender.entity.do.tender_do import OaTenderDocument, OaTenderRequirement, OaBidPersonnelMapping
from module_tender.entity.vo.tender_vo import (
    TenderDocumentModel,
    TenderDocumentPageQueryModel,
    TenderDocumentUploadResultModel,
    TenderDocumentDetailModel,
    TenderRequirementModel,
    BidPersonnelMappingModel,
    MatchResultModel,
)
from module_resume_kb.entity.do.resume_do import OaResume
from utils.log_util import logger
from utils.time_format_util import TimeFormatUtil
from utils.common_util import CamelCaseUtil
from config.env import AiResumeParserConfig
import litellm
import fitz


class TenderService:
    """
    招标文件智能生成模块服务层
    """

    # ========== 招标文件解析 ==========

    @classmethod
    async def upload_tender_document_services(
        cls,
        query_db: AsyncSession,
        file_path: str,
        file_name: str,
        user_id: int,
    ) -> TenderDocumentUploadResultModel:
        """
        上传并解析招标文件

        流程：
        1. 提取文件文本（PDF用PyMuPDF，Word用python-docx）
        2. LLM提取关键信息（项目信息+人员要求+评标标准）
        3. 转为结构化要求存入oa_tender_requirement
        4. 创建招标文件主记录
        """
        start_time = time.time()

        try:
            # 1. 解析文件文本
            file_ext = os.path.splitext(file_name)[1].lower()
            full_text = cls._parse_tender_document(file_path, file_ext)
            total_pages = cls._get_file_page_count(file_path, file_ext)

            if not full_text.strip():
                raise ServiceException(message='招标文件内容为空，无法解析')

            logger.info(f'招标文件解析: {file_name}，共{total_pages}页，文本长度{len(full_text)}')

            # 2. LLM提取关键信息
            tender_info = await cls._extract_tender_info_by_llm(full_text)

            # 3. 创建招标文件主记录
            tender_uuid = str(uuid.uuid4())
            requirements_json = json.dumps(tender_info.get('requirements', []), ensure_ascii=False)
            score_standard_json = json.dumps(tender_info.get('score_standards', []), ensure_ascii=False)

            tender = OaTenderDocument(
                tender_uuid=tender_uuid,
                file_name=file_name,
                tender_name=tender_info.get('tender_name', file_name),
                tender_code=tender_info.get('tender_code', ''),
                company_name=tender_info.get('company_name', ''),
                total_pages=total_pages,
                status=0,
                requirements_json=requirements_json,
                score_standard_json=score_standard_json,
                file_path=file_path,
                generated_file_path='',
                admin_id=user_id,
                create_time=TimeFormatUtil.get_current_timestamp(),
                update_time=TimeFormatUtil.get_current_timestamp(),
            )
            tender = await TenderDao.create_tender_document(query_db, tender)

            # 4. 批量创建结构化要求
            requirements_data = tender_info.get('requirements', [])
            requirement_dos = []
            for req_data in requirements_data:
                req_do = OaTenderRequirement(
                    tender_id=tender.id,
                    requirement_type=req_data.get('requirement_type', ''),
                    requirement_key=req_data.get('requirement_key', ''),
                    operator=req_data.get('operator', ''),
                    requirement_value=req_data.get('requirement_value', ''),
                    score_weight=Decimal(str(req_data.get('score_weight', 0))),
                    description=req_data.get('description', ''),
                    create_time=TimeFormatUtil.get_current_timestamp(),
                )
                requirement_dos.append(req_do)

            if requirement_dos:
                await TenderDao.batch_create_requirements(query_db, requirement_dos)

            parse_time = int((time.time() - start_time) * 1000)
            logger.info(
                f'招标文件解析完成: {file_name}，提取{len(requirement_dos)}条要求，耗时{parse_time}ms'
            )

            return TenderDocumentUploadResultModel(
                tender_id=tender.id,
                tender_uuid=tender_uuid,
                tender_name=tender.tender_name,
                tender_code=tender.tender_code,
                requirement_count=len(requirement_dos),
                message=f'解析完成：提取{len(requirement_dos)}条人员配置要求',
            )

        except ServiceException:
            await query_db.rollback()
            raise
        except Exception as e:
            await query_db.rollback()
            logger.error(f'招标文件解析入库失败: {str(e)}')
            raise ServiceException(message=f'招标文件解析入库失败: {str(e)}')

    @classmethod
    def _parse_tender_document(cls, file_path: str, file_ext: str) -> str:
        """解析招标文件文本（支持PDF和Word）"""
        try:
            if file_ext == '.pdf':
                doc = fitz.open(file_path)
                all_text = []
                for page in doc:
                    text = page.get_text()
                    if text.strip():
                        all_text.append(text)
                doc.close()
                return '\n'.join(all_text)
            elif file_ext in ('.docx', '.doc'):
                from docx import Document
                doc = Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                # 也提取表格内容
                for table in doc.tables:
                    for row in table.rows:
                        cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if cells:
                            paragraphs.append(' | '.join(cells))
                return '\n'.join(paragraphs)
            elif file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ServiceException(message=f'不支持的文件格式: {file_ext}')
        except ServiceException:
            raise
        except Exception as e:
            logger.error(f'解析招标文件失败: {str(e)}')
            raise ServiceException(message=f'解析招标文件失败: {str(e)}')

    @classmethod
    def _get_file_page_count(cls, file_path: str, file_ext: str) -> int:
        """获取文件页数"""
        try:
            if file_ext == '.pdf':
                doc = fitz.open(file_path)
                count = doc.page_count
                doc.close()
                return count
            else:
                # Word/TXT按段落估算
                return 0
        except:
            return 0

    @classmethod
    async def _extract_tender_info_by_llm(cls, text: str) -> dict[str, Any]:
        """
        使用LLM从招标文件文本中提取关键信息

        提取内容：
        - 项目信息（项目名称、编号、招标单位、投标截止日期）
        - 人员配置要求（学历、工作年限、技能、证书、业绩要求）
        - 评标标准（人员配置及权重、业绩要求及权重）
        """
        # 截断文本（保留前20000字符，招标文件通常较长）
        max_len = 20000
        truncated_text = text[:max_len] if len(text) > max_len else text

        prompt = f"""你是一个专业的招标文件分析专家。请从以下招标文件文本中精准提取人员配置要求信息，输出JSON。

【招标文件文本】
{truncated_text}
【招标文件文本结束】

【输出JSON格式】——找不到的填null：
{{
    "tender_name": "招标项目名称",
    "tender_code": "招标编号",
    "company_name": "招标单位名称",
    "requirements": [
        {{
            "requirement_type": "学历/工作/技能/证书/业绩",
            "requirement_key": "education/work_years/skills/certificates/performance",
            "operator": "eq/gte/lte/contains/in",
            "requirement_value": "具体要求值，如'本科'或'3'或'Java,Spring'或'PMP'",
            "score_weight": 评分权重数字(0-100),
            "description": "要求描述原文"
        }}
    ],
    "score_standards": [
        {{
            "category": "评标项类别",
            "criteria": "评分标准描述",
            "weight": 权重数字
        }}
    ]
}}

【运算符说明】
- eq: 等于（如学历等于"本科"）
- gte: 大于等于（如工作年限>=3年）
- lte: 小于等于
- contains: 包含（如技能包含"Java"）
- in: 在列表中（如学历在["硕士","博士"]中）

【注意】
- 仔细阅读招标文件中"人员要求"、"项目团队"、"人员配置"等章节
- 每条要求独立提取，不要合并
- score_weight根据招标文件中给出的分值，没有明确分值时根据重要性合理估算
- 输出必须是合法JSON，不要包含注释或多余文本"""

        api_key = AiResumeParserConfig.ai_resume_parser_api_key
        base_url = AiResumeParserConfig.ai_resume_parser_base_url
        model = AiResumeParserConfig.ai_resume_parser_model
        temperature = AiResumeParserConfig.ai_resume_parser_temperature or 0.1
        max_tokens = AiResumeParserConfig.ai_resume_parser_max_tokens or 8192

        # litellm 需要 provider 前缀
        if '/' in model and not model.startswith((
            'openai/', 'anthropic/', 'azure/', 'cohere/', 'groq/', 'ollama/', 'vertex_ai/'
        )):
            model = f'openai/{model}'

        def _call_litellm():
            """在线程池中执行同步litellm调用"""
            return litellm.completion(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': '你是一个专业的招标文件分析专家。请仔细阅读用户提供的招标文件文本，从中提取所有人员配置要求信息，严格按照要求的JSON格式输出。如果某个信息未在文件中提及，请返回null。不要猜测或编造任何信息。',
                    },
                    {
                        'role': 'user',
                        'content': prompt,
                    },
                ],
                api_key=api_key,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=60,
            )

        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, _call_litellm),
                timeout=65,
            )

            content = response.choices[0].message.content if response and response.choices else None
            if not content:
                return {'requirements': [], 'score_standards': []}

            result = cls._parse_llm_json_response(content)
            return result

        except asyncio.TimeoutError:
            logger.error('LLM提取招标信息超时')
            raise ServiceException(message='招标文件分析超时，请稍后重试')
        except Exception as e:
            logger.error(f'LLM提取招标信息失败: {str(e)}')
            raise ServiceException(message=f'招标文件分析失败: {str(e)}')

    @classmethod
    def _parse_llm_json_response(cls, content: str) -> dict[str, Any]:
        """解析LLM返回的JSON内容"""
        # 移除可能的markdown代码块标记
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()

        try:
            result = json.loads(content)
            # 确保关键字段存在
            if 'requirements' not in result:
                result['requirements'] = []
            if 'score_standards' not in result:
                result['score_standards'] = []
            return result
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            logger.error(f'LLM返回内容无法解析为JSON: {content[:200]}')
            return {'requirements': [], 'score_standards': []}

    # ========== 招标文件列表/详情/删除 ==========

    @classmethod
    async def get_tender_document_list_services(
        cls,
        query_db: AsyncSession,
        query_object: TenderDocumentPageQueryModel,
        is_page: bool = False,
    ) -> PageModel | list:
        """获取招标文件列表"""
        return await TenderDao.get_tender_document_list(query_db, query_object, is_page)

    @classmethod
    async def get_tender_detail_services(
        cls,
        query_db: AsyncSession,
        tender_id: int,
    ) -> TenderDocumentDetailModel:
        """获取招标文件详情（含要求列表）"""
        tender = await TenderDao.get_tender_detail_by_id(query_db, tender_id)
        if not tender:
            return TenderDocumentDetailModel()

        tender_model = TenderDocumentModel.model_validate(tender)
        CamelCaseUtil.transform_result(tender_model)

        # 获取要求列表
        requirements = await TenderDao.get_requirements_by_tender_id(query_db, tender_id)
        req_models = [TenderRequirementModel.model_validate(r) for r in requirements]

        return TenderDocumentDetailModel(
            tender=tender_model,
            requirements=req_models,
        )

    @classmethod
    async def get_tender_requirements_services(
        cls,
        query_db: AsyncSession,
        tender_id: int,
    ) -> list[TenderRequirementModel]:
        """获取招标文件的结构化要求列表"""
        requirements = await TenderDao.get_requirements_by_tender_id(query_db, tender_id)
        return [TenderRequirementModel.model_validate(r) for r in requirements]

    @classmethod
    async def delete_tender_document_services(
        cls,
        query_db: AsyncSession,
        tender_id: int,
    ) -> CrudResponseModel:
        """删除招标文件"""
        try:
            tender = await TenderDao.get_tender_detail_by_id(query_db, tender_id)
            if not tender:
                raise ServiceException(message='招标文件不存在')

            # 删除关联文件
            if tender.file_path and os.path.exists(tender.file_path):
                try:
                    os.remove(tender.file_path)
                except:
                    pass
            if tender.generated_file_path and os.path.exists(tender.generated_file_path):
                try:
                    os.remove(tender.generated_file_path)
                except:
                    pass

            await TenderDao.delete_tender_document(query_db, tender_id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except ServiceException:
            raise
        except Exception as e:
            logger.error(f'删除招标文件失败: {str(e)}')
            raise ServiceException(message=f'删除招标文件失败: {str(e)}')

    # ========== 人员匹配推荐 ==========

    @classmethod
    async def match_personnel_services(
        cls,
        query_db: AsyncSession,
        tender_id: int,
    ) -> MatchResultModel:
        """
        根据招标文件要求执行人员匹配推荐

        流程：
        1. 获取招标文件结构化要求
        2. 构建SQL查询条件，从简历库筛选候选人员
        3. 按评分权重计算匹配得分
        4. 按得分排序，保存到oa_bid_personnel_mapping
        """
        try:
            # 1. 获取要求
            requirements = await TenderDao.get_requirements_by_tender_id(query_db, tender_id)
            if not requirements:
                raise ServiceException(message='招标文件未提取到人员要求，无法匹配')

            # 更新状态为匹配中
            await TenderDao.update_tender_document(query_db, tender_id, status=1)

            # 2. 构建查询条件，从简历库筛选候选人员
            candidates = await cls._query_candidates(query_db, requirements)

            if not candidates:
                await TenderDao.update_tender_document(query_db, tender_id, status=0)
                return MatchResultModel(
                    tender_id=tender_id,
                    total_candidates=0,
                    matched_count=0,
                    selected_count=0,
                    match_list=[],
                )

            # 3. 计算匹配得分
            scored_candidates = []
            for resume in candidates:
                score, reasons = cls._calculate_match_score(resume, requirements)
                scored_candidates.append((resume, score, reasons))

            # 4. 按得分排序
            scored_candidates.sort(key=lambda x: x[1], reverse=True)

            # 5. 清除旧匹配记录，保存新匹配
            await TenderDao.delete_mappings_by_tender_id(query_db, tender_id)

            mappings = []
            for idx, (resume, score, reasons) in enumerate(scored_candidates):
                mapping = OaBidPersonnelMapping(
                    tender_id=tender_id,
                    resume_id=resume.id,
                    match_score=Decimal(str(round(score, 2))),
                    match_reason='；'.join(reasons),
                    sort_order=idx + 1,
                    is_selected=0,
                    create_time=TimeFormatUtil.get_current_timestamp(),
                )
                mappings.append(mapping)

            await TenderDao.batch_create_mappings(query_db, mappings)

            # 更新状态为已完成
            await TenderDao.update_tender_document(query_db, tender_id, status=2)

            # 构建返回结果
            match_list = []
            saved_mappings = await TenderDao.get_mappings_by_tender_id(query_db, tender_id)
            for row in saved_mappings:
                mapping = row[0]
                model = BidPersonnelMappingModel(
                    id=mapping.id,
                    tender_id=mapping.tender_id,
                    resume_id=mapping.resume_id,
                    match_score=float(mapping.match_score),
                    match_reason=mapping.match_reason,
                    sort_order=mapping.sort_order,
                    is_selected=mapping.is_selected,
                    create_time=mapping.create_time,
                    resume_name=row[1] or '',
                    resume_gender=row[2] or '',
                    resume_age=row[3] or 0,
                    resume_education=row[4] or '',
                    resume_work_years=row[5] or 0,
                    resume_current_company=row[6] or '',
                    resume_current_position=row[7] or '',
                    resume_skills=row[8] or '',
                    resume_certificates=row[9] or '',
                )
                match_list.append(model)

            return MatchResultModel(
                tender_id=tender_id,
                total_candidates=len(candidates),
                matched_count=len(match_list),
                selected_count=0,
                match_list=match_list,
            )

        except ServiceException:
            raise
        except Exception as e:
            logger.error(f'人员匹配失败: {str(e)}')
            raise ServiceException(message=f'人员匹配失败: {str(e)}')

    @classmethod
    async def _query_candidates(
        cls,
        query_db: AsyncSession,
        requirements: list[OaTenderRequirement],
    ) -> list[OaResume]:
        """
        根据要求构建SQL查询，从简历库筛选候选人员

        策略：先取满足硬性条件（学历、工作年限）的候选人，
        再在内存中按技能/证书做软匹配评分
        """
        query = select(OaResume).where(OaResume.status == 1)

        for req in requirements:
            key = req.requirement_key
            op = req.operator
            val = req.requirement_value

            if key == 'education':
                if op == 'eq':
                    query = query.where(OaResume.education == val)
                elif op == 'in':
                    edu_list = [v.strip() for v in val.split(',')]
                    query = query.where(OaResume.education.in_(edu_list))

            elif key == 'work_years':
                try:
                    years = int(val)
                except:
                    continue
                if op == 'gte':
                    query = query.where(OaResume.work_years >= years)
                elif op == 'lte':
                    query = query.where(OaResume.work_years <= years)
                elif op == 'eq':
                    query = query.where(OaResume.work_years == years)

            elif key == 'skills':
                # 技能用LIKE过滤（至少匹配一个）
                if op == 'contains':
                    skills = [s.strip() for s in val.split(',') if s.strip()]
                    if skills:
                        conditions = []
                        for skill in skills:
                            conditions.append(OaResume.technical_skills.like(f'%{skill}%'))
                        # 用OR连接，至少匹配一个技能
                        from sqlalchemy import or_
                        query = query.where(or_(*conditions))

        result = await query_db.execute(query)
        return result.scalars().all()

    @classmethod
    def _calculate_match_score(
        cls,
        resume: OaResume,
        requirements: list[OaTenderRequirement],
    ) -> tuple[float, list[str]]:
        """
        计算候选人匹配得分

        评分规则：
        - 学历匹配: +20分
        - 工作年限匹配: +20分
        - 技能匹配（每匹配一项）: +10分
        - 证书匹配（每匹配一项）: +15分
        """
        score = 0.0
        reasons = []

        for req in requirements:
            key = req.requirement_key
            op = req.operator
            val = req.requirement_value
            weight = float(req.score_weight) if req.score_weight else 0

            if key == 'education':
                if op == 'eq' and resume.education == val:
                    pts = weight if weight > 0 else 20
                    score += pts
                    reasons.append(f'学历匹配({val})+{pts}分')
                elif op == 'in':
                    edu_list = [v.strip() for v in val.split(',')]
                    if resume.education in edu_list:
                        pts = weight if weight > 0 else 20
                        score += pts
                        reasons.append(f'学历匹配({resume.education})+{pts}分')

            elif key == 'work_years':
                try:
                    years = int(val)
                except:
                    continue
                resume_years = resume.work_years or 0
                matched = False
                if op == 'gte' and resume_years >= years:
                    matched = True
                elif op == 'lte' and resume_years <= years:
                    matched = True
                elif op == 'eq' and resume_years == years:
                    matched = True
                if matched:
                    pts = weight if weight > 0 else 20
                    score += pts
                    reasons.append(f'工作年限匹配({resume_years}年)+{pts}分')

            elif key == 'skills':
                if op == 'contains':
                    skills = [s.strip() for s in val.split(',') if s.strip()]
                    resume_skills_str = resume.technical_skills or ''
                    for skill in skills:
                        if skill.lower() in resume_skills_str.lower():
                            pts = weight if weight > 0 else 10
                            score += pts
                            reasons.append(f'技能匹配({skill})+{pts}分')

            elif key == 'certificates':
                if op == 'contains':
                    certs = [c.strip() for c in val.split(',') if c.strip()]
                    resume_certs_str = resume.certifications or ''
                    for cert in certs:
                        if cert.lower() in resume_certs_str.lower():
                            pts = weight if weight > 0 else 15
                            score += pts
                            reasons.append(f'证书匹配({cert})+{pts}分')

        return score, reasons

    # ========== 获取匹配结果 ==========

    @classmethod
    async def get_match_result_services(
        cls,
        query_db: AsyncSession,
        tender_id: int,
    ) -> MatchResultModel:
        """获取匹配结果列表"""
        mappings = await TenderDao.get_mappings_by_tender_id(query_db, tender_id)
        selected_count = await TenderDao.count_selected(query_db, tender_id)

        match_list = []
        for row in mappings:
            mapping = row[0]
            model = BidPersonnelMappingModel(
                id=mapping.id,
                tender_id=mapping.tender_id,
                resume_id=mapping.resume_id,
                match_score=float(mapping.match_score),
                match_reason=mapping.match_reason,
                sort_order=mapping.sort_order,
                is_selected=mapping.is_selected,
                create_time=mapping.create_time,
                resume_name=row[1] or '',
                resume_gender=row[2] or '',
                resume_age=row[3] or 0,
                resume_education=row[4] or '',
                resume_work_years=row[5] or 0,
                resume_current_company=row[6] or '',
                resume_current_position=row[7] or '',
                resume_skills=row[8] or '',
                resume_certificates=row[9] or '',
            )
            match_list.append(model)

        return MatchResultModel(
            tender_id=tender_id,
            total_candidates=len(match_list),
            matched_count=len(match_list),
            selected_count=selected_count,
            match_list=match_list,
        )

    # ========== 选择/取消人员 ==========

    @classmethod
    async def select_personnel_services(
        cls,
        query_db: AsyncSession,
        mapping_id: int,
        is_selected: int,
    ) -> CrudResponseModel:
        """选择/取消选择人员"""
        try:
            await TenderDao.update_mapping_selection(query_db, mapping_id, is_selected)
            action = '选中' if is_selected == 1 else '取消选中'
            return CrudResponseModel(is_success=True, message=f'{action}成功')
        except Exception as e:
            logger.error(f'选择人员失败: {str(e)}')
            raise ServiceException(message=f'选择人员失败: {str(e)}')

    # ========== 生成投标文件 ==========

    @classmethod
    async def generate_bid_file_services(
        cls,
        query_db: AsyncSession,
        tender_id: int,
        output_format: str = 'docx',
    ) -> str:
        """
        根据选中人员生成标准格式投标文件

        流程：
        1. 获取选中的候选人列表
        2. 按人员一览表格式组装数据
        3. 使用python-docx生成Word文档
        4. 更新招标文件的generated_file_path
        """
        try:
            # 1. 获取选中的候选人
            selected = await TenderDao.get_selected_mappings(query_db, tender_id)
            if not selected:
                raise ServiceException(message='未选择任何人员，无法生成投标文件')

            # 获取招标文件信息
            tender = await TenderDao.get_tender_detail_by_id(query_db, tender_id)
            if not tender:
                raise ServiceException(message='招标文件不存在')

            # 2. 生成Word文档
            output_dir = './uploads/tender_generated'
            os.makedirs(output_dir, exist_ok=True)

            file_name = f"投标文件_{tender.tender_name}_{int(time.time())}.docx"
            output_path = os.path.join(output_dir, file_name)

            cls._generate_docx(tender, selected, output_path)

            # 3. 更新招标文件路径
            await TenderDao.update_tender_document(
                query_db, tender_id, generated_file_path=output_path
            )

            logger.info(f'投标文件生成成功: {output_path}，共{len(selected)}人')
            return output_path

        except ServiceException:
            raise
        except Exception as e:
            logger.error(f'生成投标文件失败: {str(e)}')
            raise ServiceException(message=f'生成投标文件失败: {str(e)}')

    @classmethod
    def _generate_docx(
        cls,
        tender: OaTenderDocument,
        selected: list,
        output_path: str,
    ) -> None:
        """使用python-docx生成投标文件Word文档"""
        from docx import Document
        from docx.shared import Pt, Cm, Inches
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml.ns import qn

        doc = Document()

        # 设置默认字体
        style = doc.styles['Normal']
        font = style.font
        font.name = '宋体'
        font.size = Pt(12)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

        # 标题
        title = doc.add_heading('', level=0)
        title_run = title.add_run(f'{tender.tender_name}投标文件')
        title_run.font.name = '黑体'
        title_run.font.size = Pt(22)
        title_run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 项目信息
        doc.add_heading('一、项目基本信息', level=1)
        info_table = doc.add_table(rows=4, cols=2, style='Table Grid')
        info_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        info_data = [
            ('项目名称', tender.tender_name),
            ('项目编号', tender.tender_code),
            ('招标单位', tender.company_name),
            ('投标人数', f'{len(selected)} 人'),
        ]
        for i, (label, value) in enumerate(info_data):
            cell_label = info_table.cell(i, 0)
            cell_value = info_table.cell(i, 1)
            cell_label.text = label
            cell_value.text = str(value)
            # 加粗标签列
            for paragraph in cell_label.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True

        # 人员一览表
        doc.add_heading('二、拟投入人员一览表', level=1)

        headers = ['序号', '姓名', '性别', '年龄', '学历', '工作年限', '当前公司', '当前职位', '专业技能']
        person_table = doc.add_table(rows=len(selected) + 1, cols=len(headers), style='Table Grid')
        person_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # 表头
        for i, header in enumerate(headers):
            cell = person_table.cell(0, i)
            cell.text = header
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(10)

        # 数据行
        for idx, row_data in enumerate(selected, 1):
            mapping = row_data[0]
            name = row_data[1] or ''
            gender = row_data[2] or ''
            age = row_data[3] or 0
            education = row_data[4] or ''
            work_years = row_data[5] or 0
            company = row_data[6] or ''
            position = row_data[7] or ''
            skills = row_data[8] or ''
            # 解析技能JSON
            try:
                skills_list = json.loads(skills)
                skills_text = '、'.join(skills_list[:10]) if isinstance(skills_list, list) else skills
            except:
                skills_text = skills[:100] if skills else ''

            row_values = [str(idx), name, gender, str(age), education, f'{work_years}年', company, position, skills_text]
            for col, val in enumerate(row_values):
                cell = person_table.cell(idx, col)
                cell.text = val
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in paragraph.runs:
                        run.font.size = Pt(10)

        # 人员详细信息
        doc.add_heading('三、人员详细信息', level=1)

        for idx, row_data in enumerate(selected, 1):
            mapping = row_data[0]
            name = row_data[1] or ''
            gender = row_data[2] or ''
            age = row_data[3] or 0
            education = row_data[4] or ''
            work_years = row_data[5] or 0
            company = row_data[6] or ''
            position = row_data[7] or ''
            skills = row_data[8] or ''
            certs = row_data[9] or ''
            major = row_data[10] or ''
            school = row_data[11] or ''

            doc.add_heading(f'{idx}. {name}（{gender}，{age}岁，{education}）', level=2)

            detail_table = doc.add_table(rows=6, cols=2, style='Table Grid')
            detail_data = [
                ('学历/专业', f'{education}，{major}，{school}'),
                ('工作年限', f'{work_years}年'),
                ('当前职务', f'{company} - {position}'),
                ('专业技能', cls._format_json_skills(skills)),
                ('持有证书', cls._format_json_skills(certs)),
                ('匹配得分', f'{float(mapping.match_score):.1f}分（{mapping.match_reason}）'),
            ]
            for i, (label, value) in enumerate(detail_data):
                detail_table.cell(i, 0).text = label
                detail_table.cell(i, 1).text = value
                for paragraph in detail_table.cell(i, 0).paragraphs:
                    for run in paragraph.runs:
                        run.font.bold = True

            doc.add_paragraph('')  # 空行分隔

        # 保存文档
        doc.save(output_path)

    @classmethod
    def _format_json_skills(cls, json_str: str) -> str:
        """格式化JSON技能/证书列表为可读文本"""
        if not json_str:
            return '无'
        try:
            items = json.loads(json_str)
            if isinstance(items, list):
                return '、'.join(items) if items else '无'
            return str(items)
        except:
            return json_str[:200] if json_str else '无'

    @classmethod
    async def download_bid_file_services(
        cls,
        query_db: AsyncSession,
        tender_id: int,
    ) -> str:
        """获取生成的投标文件路径"""
        tender = await TenderDao.get_tender_detail_by_id(query_db, tender_id)
        if not tender:
            raise ServiceException(message='招标文件不存在')
        if not tender.generated_file_path or not os.path.exists(tender.generated_file_path):
            raise ServiceException(message='投标文件尚未生成，请先执行生成操作')
        return tender.generated_file_path
