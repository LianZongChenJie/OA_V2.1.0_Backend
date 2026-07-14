"""
投标文件知识库模块服务层
"""
import json
import re
import uuid
import time
import asyncio
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel, CrudResponseModel
from exceptions.exception import ServiceException
from module_bid_kb.dao.bid_dao import BidDao
from module_bid_kb.entity.do.bid_do import OaBidDocument
from module_bid_kb.entity.vo.bid_vo import (
    BidDocumentModel,
    BidDocumentPageQueryModel,
    BidDocumentUploadResultModel,
    BidDocumentDetailModel,
)
from module_resume_kb.dao.resume_dao import ResumeDao
from module_resume_kb.entity.do.resume_do import OaResume, OaResumeWork, OaResumeProject
from module_resume_kb.entity.vo.resume_vo import ResumeModel
from module_resume_kb.service.resume_kb_service import ResumeKbService
from utils.log_util import logger
from config.env import AiResumeParserConfig
from utils.common_util import CamelCaseUtil
from config.database import AsyncSessionLocal
import os
import litellm
import fitz


# 模块级进度存储（内存字典）
# key: bid_uuid, value: dict{stage, current, total, message, percent}
_bid_progress: dict[str, dict] = {}


class BidKbService:
    """
    投标文件知识库模块服务层
    """

    @classmethod
    def _set_progress(
        cls,
        bid_uuid: str,
        stage: str,
        current: int,
        total: int,
        message: str = '',
    ) -> None:
        """更新解析进度"""
        percent = int((current / total * 100)) if total > 0 else 0
        _bid_progress[bid_uuid] = {
            'stage': stage,
            'current': current,
            'total': total,
            'percent': min(percent, 99),
            'message': message,
            'update_time': int(time.time()),
        }

    @classmethod
    def _get_progress(cls, bid_uuid: str) -> dict:
        """获取解析进度"""
        return _bid_progress.get(bid_uuid, {
            'stage': 'unknown',
            'current': 0,
            'total': 0,
            'percent': 0,
            'message': '未找到解析任务',
        })

    @classmethod
    async def upload_bid_document_services(
        cls,
        query_db: AsyncSession,
        file_path: str,
        file_name: str,
        user_id: int,
    ) -> BidDocumentUploadResultModel:
        """
        上传并解析投标文件服务（异步后台解析）

        流程：
        1. 生成 bid_uuid，创建空的投标文件主记录
        2. 立返回 bid_uuid，让前端开始轮询进度
        3. 后台异步任务完成 OCR + LLM + 入库
        """
        bid_uuid = str(uuid.uuid4())
        bid_id = 0

        try:
            # 1. 获取PDF页数（很快）
            total_pages = cls._get_pdf_page_count(file_path)

            # 2. 创建投标文件主记录（status=0 表示处理中）
            bid = OaBidDocument(
                bid_uuid=bid_uuid,
                file_name=file_name,
                bid_name=file_name,  # 先存文件名，后台解析完再更新
                bid_code='',
                company_name='',
                total_pages=total_pages,
                resume_count=0,
                status=0,  # 0=处理中
                admin_id=user_id,
                create_time=int(time.time()),
                update_time=int(time.time()),
            )
            bid = await BidDao.create_bid_document(query_db, bid)
            bid_id = bid.id
            await query_db.commit()

            # 3. 启动后台异步解析任务（不等完成）
            # 调试开关：设置环境变量 BID_DEBUG_MAX_PAGES=10 只解析前10页，方便快速测试
            debug_max_pages = int(os.environ.get('BID_DEBUG_MAX_PAGES', '42'))
            cls._set_progress(bid_uuid, 'ocr', 0, total_pages, '等待启动解析...')
            asyncio.create_task(
                cls._parse_and_save_async(
                    bid_uuid=bid_uuid,
                    bid_id=bid_id,
                    file_path=file_path,
                    file_name=file_name,
                    user_id=user_id,
                    max_pages=debug_max_pages,
                )
            )

            # 4. 立返回，前端拿到 bid_uuid 后立即开始轮询
            logger.info(f'投标文件已接收，bid_uuid={bid_uuid}，后台解析任务已启动')
            return BidDocumentUploadResultModel(
                bid_id=bid_id,
                bid_uuid=bid_uuid,
                bid_name=file_name,
                bid_code='',
                resume_count=0,
                failed_count=0,
                message=f'投标文件已接收，共 {total_pages} 页，后台解析中...',
            )

        except Exception as e:
            await query_db.rollback()
            logger.error(f'投标文件接收失败: {str(e)}')
            raise ServiceException(message=f'投标文件接收失败: {str(e)}')

    @classmethod
    async def _parse_and_save_async(
        cls,
        bid_uuid: str,
        bid_id: int,
        file_path: str,
        file_name: str,
        user_id: int,
        max_pages: int = 0,
    ) -> None:
        """
        后台异步解析任务：OCR -> 提取信息 -> 拆分简历 -> LLM解析 -> 入库
        此方法和 HTTP 请求解耦，前端通过 /progress/{bid_uuid} 轮询进度
        
        Args:
            max_pages: 调试参数，>0 时只解析前 max_pages 页（用于快速测试）
        """
        start_time = time.time()

        try:
            # 1. OCR 解析PDF全文（线程池并行）
            # OCR 阶段占总进度的 0-40%
            cls._set_progress(bid_uuid, 'ocr', 0, 100, '正在读取PDF文件...')
            full_text = await asyncio.to_thread(
                cls._parse_bid_document_threaded, file_path, bid_uuid, max_pages
            )
            total_pages = cls._get_pdf_page_count(file_path)

            # 2. 提取投标项目信息（占 5%，40-45%）
            cls._set_progress(bid_uuid, 'extract', 40, 100, '正在提取投标信息...')
            bid_info = cls._extract_bid_info(full_text, file_name)
            cls._set_progress(bid_uuid, 'extract', 45, 100, '投标信息提取完成')

            # 3. 拆分简历
            resume_segments = cls._split_resumes(full_text)
            logger.info(f'投标文件共 {total_pages} 页，识别到 {len(resume_segments)} 份简历')

            # 限制解析简历数量，加快整体速度（默认前20份，BID_MAX_RESUMES 环境变量可调）
            import os
            max_resumes = int(os.environ.get('BID_MAX_RESUMES', '20'))
            if len(resume_segments) > max_resumes:
                logger.info(f'限制只解析前 {max_resumes} 份简历（共 {len(resume_segments)} 份）')
                resume_segments = resume_segments[:max_resumes]

            if not resume_segments:
                cls._set_progress(bid_uuid, 'done', 100, 100, '未识别到简历')
                await cls._update_bid_status(bid_id, bid_info.get('bid_name', file_name), 1, 0, 0)
                return

            # 4. 逐份LLM解析简历（串行，避免并发压垮LLM）
            # 解析阶段占总进度的 45-90%（共45%）
            total_resumes = len(resume_segments)
            cls._set_progress(
                bid_uuid, 'parse', 45, 100,
                f'开始逐份解析 {total_resumes} 份简历...'
            )

            parsed_results = []
            failed_count = 0

            for idx, resume_text in enumerate(resume_segments, 1):
                try:
                    structured_info = await cls._parse_resume_llm_only(resume_text)
                    parsed_results.append(structured_info)
                    # 计算解析进度：45% + (idx/total) * 45%
                    parse_percent = 45 + int(idx / total_resumes * 45)
                    cls._set_progress(
                        bid_uuid, 'parse', parse_percent, 100,
                        f'已解析 {idx}/{total_resumes}：{structured_info.get("name", "未知")}'
                    )
                except Exception as e:
                    logger.error(f'第 {idx}/{total_resumes} 份简历解析异常: {str(e)}')
                    failed_count += 1
                    parse_percent = 45 + int(idx / total_resumes * 45)
                    cls._set_progress(
                        bid_uuid, 'parse', parse_percent, 100,
                        f'第 {idx}/{total_resumes} 份解析失败: {str(e)[:50]}'
                    )

            # 去重：按 姓名+身份证号 或 姓名+出生日期 去重，保留信息更完整的那条
            unique_results = []
            seen_keys = set()
            for structured_info in parsed_results:
                name = structured_info.get('name', '')
                id_num = structured_info.get('id_card_number', '')
                birth = structured_info.get('birth_date', '')
                # 优先用身份证号去重，其次用姓名+出生日期
                if id_num:
                    dedup_key = f'id:{id_num}'
                elif name and birth:
                    dedup_key = f'name_birth:{name}:{birth}'
                else:
                    dedup_key = f'name_only:{name}'
                
                if dedup_key in seen_keys:
                    # 找到已存在的那条，比较信息完整度，保留更完整的
                    existing_idx = None
                    for i, existing in enumerate(unique_results):
                        existing_key = f'id:{existing.get("id_card_number", "")}' if existing.get('id_card_number') else \
                            f'name_birth:{existing.get("name", "")}:{existing.get("birth_date", "")}' if existing.get('name') and existing.get('birth_date') else \
                            f'name_only:{existing.get("name", "")}'
                        if existing_key == dedup_key:
                            existing_idx = i
                            break
                    if existing_idx is not None:
                        # 计算两条记录的非空字段数
                        existing_filled = sum(1 for v in unique_results[existing_idx].values() if v and v != '' and v != [] and not (isinstance(v, dict) and not v))
                        new_filled = sum(1 for v in structured_info.values() if v and v != '' and v != [] and not (isinstance(v, dict) and not v))
                        if new_filled > existing_filled:
                            unique_results[existing_idx] = structured_info
                            logger.info(f'去重: 替换为更完整的记录 (name={name})')
                    continue
                
                seen_keys.add(dedup_key)
                unique_results.append(structured_info)
            
            removed_count = len(parsed_results) - len(unique_results)
            if removed_count > 0:
                logger.info(f'简历去重: 移除 {removed_count} 条重复记录，剩余 {len(unique_results)} 条')
            
            valid_results = unique_results

            # 5. 逐份入库（串行）
            # 入库阶段占总进度的 90-100%（共10%）
            cls._set_progress(
                bid_uuid, 'save', 90, 100,
                f'正在保存 {len(valid_results)} 份简历到数据库...'
            )
            success_count = 0
            for idx, structured_info in enumerate(valid_results, 1):
                try:
                    result = await cls._save_resume_to_db(
                        structured_info,
                        file_name,
                        bid_id,
                        bid_info.get('bid_name', file_name),
                        user_id,
                    )
                    if result:
                        success_count += 1
                    # 计算保存进度：90% + (idx/total) * 10%
                    save_percent = 90 + int(idx / len(valid_results) * 10)
                    cls._set_progress(
                        bid_uuid, 'save', save_percent, 100,
                        f'已保存 {idx}/{len(valid_results)} 份简历'
                    )
                except Exception as e:
                    failed_count += 1
                    logger.error(f'第 {idx} 份简历入库异常: {str(e)}')

            # 6. 更新投标文件状态（完成）
            await cls._update_bid_status(
                bid_id, bid_info.get('bid_name', file_name), 1, success_count, failed_count,
                bid_code=bid_info.get('bid_code', ''),
                company_name=bid_info.get('company_name', ''),
            )

            parse_time = int((time.time() - start_time) * 1000)
            logger.info(
                f'投标文件后台解析完成: {file_name}，共{total_resumes}份简历，'
                f'成功{success_count}份，失败{failed_count}份，耗时{parse_time}ms'
            )

            cls._set_progress(
                bid_uuid, 'done', 100, 100,
                f'解析完成：成功{success_count}份，失败{failed_count}份'
            )

        except Exception as e:
            logger.error(f'投标文件后台解析异常: bid_uuid={bid_uuid}, error={str(e)}')
            cls._set_progress(bid_uuid, 'error', 0, 100, f'解析失败: {str(e)}')
            await cls._update_bid_status(bid_id, file_name, 2, 0, 0)  # 2=失败

    @classmethod
    async def _update_bid_status(
        cls,
        bid_id: int,
        bid_name: str,
        status: int,
        resume_count: int,
        failed_count: int,
        bid_code: str = '',
        company_name: str = '',
    ) -> None:
        """
        更新投标文件状态（后台任务完成后更新）
        status: 0=处理中, 1=已完成, 2=失败
        """
        from sqlalchemy import update
        async with AsyncSessionLocal() as db:
            try:
                update_values = {
                    'bid_name': bid_name,
                    'status': status,
                    'resume_count': resume_count,
                    'update_time': int(time.time()),
                }
                # 只有非空时才更新项目编号和投标公司
                if bid_code:
                    update_values['bid_code'] = bid_code
                if company_name:
                    update_values['company_name'] = company_name

                stmt = (
                    update(OaBidDocument)
                    .where(OaBidDocument.id == bid_id)
                    .values(**update_values)
                )
                await db.execute(stmt)
                await db.commit()
                logger.info(f'更新投标文件状态: bid_id={bid_id}, bid_code={bid_code}, company_name={company_name}')
            except Exception as e:
                await db.rollback()
                logger.error(
                    f'更新投标文件状态失败: bid_id={bid_id}, status={status}, error={str(e)}'
                )

    @classmethod
    async def _update_bid_resume_count(cls, bid_id: int, count: int) -> None:
        """
        更新投标文件简历数量（使用全新独立 session）
        """
        from sqlalchemy import update
        async with AsyncSessionLocal() as db:
            try:
                stmt = (
                    update(OaBidDocument)
                    .where(OaBidDocument.id == bid_id)
                    .values(resume_count=count, update_time=int(time.time()))
                )
                await db.execute(stmt)
                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.error(f'更新简历数量失败: bid_id={bid_id}, count={count}, error={str(e)}')
                raise

    @classmethod
    def _locate_resume_chapter(cls, doc, total_pages: int) -> tuple[int, int]:
        """
        从目录中定位"专职人员基本情况"章节的页码范围
        返回: (start_page_index, end_page_index) 0-based，end_page为排他
        如果未找到返回 (-1, -1)
        """
        # 扫描前20页找目录
        toc_text = ''
        scan_pages = min(20, total_pages)
        for i in range(scan_pages):
            toc_text += doc[i].get_text() + '\n'

        lines = toc_text.split('\n')
        start_page = -1
        end_page = -1

        for i, line in enumerate(lines):
            if '专职人员基本情况' in line:
                # 从这一行末尾提取页码（目录行通常是 "八、专职人员基本情况 ... 27" 格式）
                page_match = re.search(r'(\d{1,3})\s*$', line.strip())
                if page_match:
                    start_page = int(page_match.group(1)) - 1  # 转为0-based
                    # 找下一个章节的页码作为结束
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if not next_line:
                            continue
                        # 匹配下一个大章节（如 九、... 或 9. ... 或 十、...）
                        # 只要行尾有页码数字，就认为是目录项
                        next_page_match = re.search(r'(\d{1,3})\s*$', next_line)
                        if next_page_match:
                            # 检查是否是另一个章节标题（包含"章"、"节"、"部分"等）
                            if any(kw in next_line for kw in ['章', '节', '部分', '附录', '附件', '九、', '十、', '十一、', '9.', '10.']):
                                end_page = int(next_page_match.group(1)) - 1
                                break
                            # 如果连续多行都是页码较小的，可能是子目录，继续找
                            continue
                    break

        # 如果找到开始但找不到结束，默认到PDF末尾
        if start_page >= 0 and end_page < 0:
            end_page = total_pages

        return start_page, end_page

    @classmethod
    def _parse_bid_document_threaded(cls, file_path: str, bid_uuid: str = '', max_pages: int = 0) -> str:
        """
        线程池并行解析投标文件PDF，对嵌入图片页面进行OCR增强
        - 模型全局共享一份（类属性），不会因线程数增加内存
        - OCR 之前先渲染图片，把 img_bytes 作为任务丢给线程池
        - 用 ThreadPoolExecutor(max_workers=3)，控制并发防止内存波动
        - 只解析"专职人员基本情况"章节范围内的页面
        
        Args:
            max_pages: 调试参数，>0 时只解析前 max_pages 页（用于快速测试OCR逻辑）
        """
        try:
            import fitz
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            raise ServiceException(message='PDF解析需要依赖：pip install PyMuPDF rapidocr-onnxruntime')

        # 全局共享一个 OCR 引擎（线程安全，ONNX Runtime 推理时释放 GIL）
        if not hasattr(cls, '_ocr_engine'):
            cls._ocr_engine = RapidOCR()
        engine = cls._ocr_engine

        doc = fitz.open(file_path)
        total_pages = doc.page_count

        # 先扫描前5页（封面页）提取投标信息：项目编号、投标公司等
        cover_text = ''
        cover_pages = min(5, total_pages)
        for i in range(cover_pages):
            cover_text += doc[i].get_text() + '\n'
        # 封面文本附加到最终结果前（不影响简历拆分，只用于投标信息提取）

        # 定位"专职人员基本情况"章节范围
        start_page, end_page = cls._locate_resume_chapter(doc, total_pages)
        if start_page >= 0 and end_page >= 0:
            parse_start = start_page
            parse_end = min(end_page, total_pages)
            logger.info(f'定位到"专职人员基本情况"章节：第 {parse_start+1} 页 到 第 {parse_end} 页（共 {parse_end - parse_start} 页）')
        else:
            # 未找到章节，退化为全量解析（兜底）
            parse_start = 0
            parse_end = total_pages
            logger.warning('未定位到"专职人员基本情况"章节，退化为全量解析')
        
        # 调试模式：只解析前 max_pages 页
        if max_pages > 0:
            parse_end = min(parse_start + max_pages, parse_end, total_pages)
            if parse_end < total_pages:
                logger.info(f'【调试模式】只解析前 {parse_end - parse_start}/{parse_end - parse_start} 页')

        parse_pages = parse_end - parse_start
        if parse_pages <= 0:
            doc.close()
            return ''

        # Phase A: 逐页预处理，渲染图片 + 收集 OCR 任务
        # 只把需要 OCR 的页面收集起来，纯文字页直接取文本
        all_text = [''] * parse_pages
        ocr_tasks = []  # [(page_num, img_bytes, original_text, ocr_preview_result)]

        logger.info(f'开始解析投标文件PDF，共 {parse_pages} 页（线程池OCR，max_workers=3）')
        cls._set_progress(bid_uuid, 'ocr', 0, 100, f'正在扫描 {parse_pages} 页PDF...')

        # 定义学信网和身份证相关关键词（放宽匹配，应对OCR分词/换行）
        XUEXIN_KEYWORDS = ['学信网', 'CHSI', '学历证书', '学籍', '教育部', '学历查询', '学位查询', '教育部学历证书']
        # 身份证关键词放宽：OCR可能把"公民身份号码"拆成"公民\n身份\n号码"
        ID_CARD_KEYWORDS = ['居民身份证', '公民身份号码', '公民身份号', '身份号码', '签发机关', '住址', '中华人民共和国']

        for page_num in range(parse_pages):
            actual_page = parse_start + page_num
            page = doc[actual_page]
            text = page.get_text()
            text_stripped = text.strip()
            images = page.get_images()
            has_images = len(images) > 0

            # 章节范围内：纯文字页全部保留，不跳过（防止简历文字量少被漏掉）
            if not has_images:
                all_text[page_num] = text_stripped
                continue

            # 有图片的页面：只OCR学信网/身份证，其他图片跳过但保留原始文字
            if has_images:
                try:
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)
                    img_bytes = pix.tobytes('png')
                    
                    # 对图片进行OCR预检，判断是否为学信网或身份证
                    is_target_image = False
                    ocr_preview_result = None
                    try:
                        result, _ = engine(img_bytes)
                        if result:
                            ocr_preview_text = ' '.join([item[1] for item in result])
                            # 检查是否包含学信网或身份证关键词
                            if any(kw in ocr_preview_text for kw in XUEXIN_KEYWORDS):
                                is_target_image = True
                                ocr_preview_result = result
                                logger.info(f'第{actual_page+1}页识别为学信网页面，进行完整OCR')
                            elif any(kw in ocr_preview_text for kw in ID_CARD_KEYWORDS):
                                is_target_image = True
                                ocr_preview_result = result
                                logger.info(f'第{actual_page+1}页识别为身份证页面，进行完整OCR')
                            else:
                                logger.info(f'第{actual_page+1}页非学信网/身份证图片，跳过OCR，保留原始文字')
                    except Exception as preview_e:
                        logger.warning(f'第{actual_page+1}页OCR预检失败: {str(preview_e)}')
                    
                    if is_target_image:
                        # 预检OCR结果直接传递给Phase B，避免重复识别
                        ocr_tasks.append((page_num, img_bytes, text_stripped, ocr_preview_result))
                    else:
                        # 非目标图片，保留原始页面文字（确保简历表格文字不丢失）
                        all_text[page_num] = text_stripped
                except Exception as e:
                    logger.warning(f'第{actual_page+1}页渲染失败: {str(e)}')
                    all_text[page_num] = text_stripped
            
            # 每扫描10页更新一次进度（Phase A 占 OCR 总进度的 50%，即全局的 0-20%）
            if (page_num + 1) % 10 == 0 or page_num == parse_pages - 1:
                scan_percent = int((page_num + 1) / parse_pages * 20)
                cls._set_progress(
                    bid_uuid, 'ocr', scan_percent, 100,
                    f'正在扫描第 {page_num + 1}/{parse_pages} 页...'
                )

        doc.close()

        # Phase B: 线程池并行 OCR（模型共享，不额外占内存）
        ocr_total = len(ocr_tasks)
        if ocr_total > 0:
            max_workers = min(3, ocr_total)
            logger.info(f'OCR任务: {ocr_total} 页，启动 {max_workers} 个线程并行处理（模型共享）')

            def _do_ocr(task):
                page_num, img_bytes, original_text, ocr_preview_result = task
                try:
                    # 复用预检阶段的OCR结果，避免重复识别
                    if ocr_preview_result is not None:
                        result = ocr_preview_result
                    else:
                        result, _ = engine(img_bytes)
                    if result:
                        ocr_text = '\n'.join([item[1] for item in result])
                        if len(original_text) < 50:
                            return page_num, ocr_text
                        else:
                            return page_num, original_text + '\n' + ocr_text
                    return page_num, original_text
                except Exception as e:
                    logger.warning(f'第{page_num+1}页OCR失败: {str(e)}')
                    return page_num, original_text

            completed = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(_do_ocr, task): task for task in ocr_tasks}
                for future in as_completed(futures):
                    page_num, result_text = future.result()
                    all_text[page_num] = result_text
                    completed += 1
                    # Phase B 占 OCR 总进度的 50%，即全局的 20-40%
                    # 每完成1页或每5页更新一次
                    if completed % 5 == 0 or completed == ocr_total:
                        ocr_percent = 20 + int(completed / ocr_total * 20)
                        cls._set_progress(
                            bid_uuid, 'ocr', ocr_percent, 100,
                            f'OCR识别第 {completed}/{ocr_total} 页...'
                        )
                        logger.info(f'OCR线程池进度: {completed}/{ocr_total}')

        # OCR 阶段完成，进度到 40%
        cls._set_progress(bid_uuid, 'ocr', 40, 100, 'OCR识别完成')
        logger.info(f'投标文件OCR完成，共 {parse_pages} 页，OCR {ocr_total} 页')
        
        # 合并：封面文本 + 章节文本，确保封面信息不丢失
        resume_text = '\n'.join(filter(None, all_text))
        full_text = cover_text + '\n' + resume_text
        return full_text

    @classmethod
    def _get_pdf_page_count(cls, file_path: str) -> int:
        """获取PDF页数"""
        try:
            doc = fitz.open(file_path)
            count = doc.page_count
            doc.close()
            return count
        except:
            return 0

    @classmethod
    def _extract_bid_info(cls, text: str, file_name: str) -> dict:
        """提取投标文件基本信息"""
        info = {}

        # 提取项目编号（支持多种格式：BJFLX-2026-112, BJFLX - 2026 - 112, 带空格/换行等）
        code_patterns = [
            r'项目编号[：:\s]*\n?\s*([A-Z]{2,}[-\s]*\d{4}[-\s]*\d+)',
            r'项目编号[：:\s]*\n?\s*([A-Z]{2,}[-\s]*\d{4}[-\s]*\d+)',
            r'编号[：:\s]*\n?\s*([A-Z]{2,}[-\s]*\d{4}[-\s]*\d+)',
        ]
        for pattern in code_patterns:
            code_match = re.search(pattern, text)
            if code_match:
                # 清理编号中的空格
                bid_code = re.sub(r'\s+', '', code_match.group(1).strip())
                info['bid_code'] = bid_code
                logger.info(f'提取到项目编号: {bid_code}')
                break
        
        if not info.get('bid_code'):
            # 兜底：直接搜索格式 X-X-X 的编号
            code_match = re.search(r'(?<!\w)([A-Z]{2,}-\d{4}-\d+)(?!\w)', text)
            if code_match:
                info['bid_code'] = code_match.group(1).strip()
                logger.info(f'兜底提取到项目编号: {info["bid_code"]}')

        # 提取项目名称（多策略匹配）
        bid_name = ''
        patterns = [
            r'接受贵方\s*[：:\s]*\s*(.+?)\s*招标文件',
            r'我方接受贵方\s*[：:\s]*\s*(.+?)\s*招标文件',
            r'项目名称[：:\s]*([^\n]{3,80})',
            r'招标项目[：:\s]*([^\n]{3,80})',
            r'项目[：:\s]*名称[：:\s]*([^\n]{3,80})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1).strip()
                invalid_keywords = ['规模', '万元', '序号', '姓名', '性别', '年龄', '学历']
                if candidate and not any(kw in candidate for kw in invalid_keywords):
                    bid_name = candidate
                    break

        if not bid_name and file_name:
            name_from_file = file_name
            name_from_file = re.sub(r'^投标文件[-—\s]*', '', name_from_file)
            name_from_file = re.sub(r'\.pdf$', '', name_from_file, flags=re.IGNORECASE)
            name_from_file = re.sub(r'\d{1,2}\.\d{1,2}$', '', name_from_file)
            name_from_file = name_from_file.strip('-—\s')
            if len(name_from_file) >= 5:
                bid_name = name_from_file

        info['bid_name'] = bid_name

        # 提取投标公司（支持跨行、带"盖章"后缀等格式）
        company_patterns = [
            r'投标人[：:\s]*\n?\s*([\u4e00-\u9fa5（）()]{2,80})',
            r'投标人[：:\s]*\n?\s*(.+?公司)',
            r'公司名称[：:\s]*\n?\s*([\u4e00-\u9fa5（）()]{2,80})',
            r'投标单位[：:\s]*\n?\s*([\u4e00-\u9fa5（）()]{2,80})',
        ]
        for pattern in company_patterns:
            company_match = re.search(pattern, text)
            if company_match:
                company = company_match.group(1).strip()
                # 清理常见噪声：去除"（盖章）"等后缀
                company = re.sub(r'[（(]\s*盖章\s*[）)]', '', company).strip()
                company = re.sub(r'[（(].*?[）)]', '', company).strip()
                if len(company) >= 4:
                    info['company_name'] = company
                    logger.info(f'提取到投标公司: {company}')
                    break

        return info

    @classmethod
    def _split_resumes(cls, text: str) -> list[str]:
        """
        从投标文件文本中拆分出多份简历。
        优先使用 LLM 识别人员，LLM 失败时降级到正则规则。
        """
        # 首先尝试用 LLM 拆分
        if AiResumeParserConfig.ai_resume_parser_enabled:
            try:
                resumes = cls._split_resumes_llm(text)
                if resumes and len(resumes) > 0:
                    logger.info(f'LLM 拆分得到 {len(resumes)} 份简历文本')
                    return resumes
            except Exception as e:
                logger.warning(f'LLM 拆分失败，降级到规则拆分: {str(e)}')

        # 降级到正则规则拆分
        return cls._split_resumes_regex(text)

    @classmethod
    def _split_resumes_llm(cls, text: str) -> list[str]:
        """使用 LLM 识别人员并拆分简历"""
        # 截断文本避免超出 token 限制
        max_len = 20000
        truncated_text = text[:max_len] if len(text) > max_len else text

        prompt_lines = [
            '你是一个专业的投标文件解析助手。请从以下投标文件文本中识别所有人员（投标人员、简历人员）。',
            '',
            '【任务要求】',
            '1. 仔细阅读文本，识别每一个出现的人员',
            '2. 每个人可能出现多次（简历主体、学信网截图、身份证截图、证书截图），请将同一个人的所有相关文本合并',
            '3. 提取每个人物对应的完整文本片段（包括个人信息、教育背景、工作经历、学信网信息、身份证信息、证书信息等）',
            '4. 只输出真实存在的人员，不要编造',
            '',
            '【文本内容】',
            truncated_text,
            '【文本结束】',
            '',
            '【输出格式】',
            '请输出JSON数组，每个元素包含：',
            '{',
            '    "name": "人员姓名",',
            '    "start_char": 该人员文本在原文本中的大致起始字符位置（0开始的整数）,',
            '    "resume_text": "该人员的完整简历文本片段（尽量完整）"',
            '}',
            '',
            '如果找不到任何人员，返回空数组 []。只输出JSON，不要任何解释。',
        ]
        prompt = chr(10).join(prompt_lines)

        try:
            api_key = AiResumeParserConfig.ai_resume_parser_api_key
            base_url = AiResumeParserConfig.ai_resume_parser_base_url
            model = AiResumeParserConfig.ai_resume_parser_model
            temperature = AiResumeParserConfig.ai_resume_parser_temperature or 0.1

            if '/' in model and not model.startswith(('openai/', 'anthropic/', 'azure/', 'cohere/', 'groq/', 'ollama/', 'vertex_ai/')):
                model = f'openai/{model}'

            import asyncio
            import litellm

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    litellm.acompletion(
                        model=model,
                        messages=[
                            {'role': 'system', 'content': '你是一个专业的投标文件解析助手，善于从长文本中识别人物并提取其相关信息。'},
                            {'role': 'user', 'content': prompt},
                        ],
                        api_key=api_key,
                        base_url=base_url,
                        temperature=temperature,
                        max_tokens=8192,
                        timeout=45,
                    )
                )
            finally:
                loop.close()

            result_content = response.choices[0].message.content if response and response.choices else None
            if not result_content:
                return []

            # 解析 JSON
            parsed = cls._parse_llm_json_response(result_content)
            if not parsed or not isinstance(parsed, list):
                return []

            resume_texts = []
            names_found = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                resume_text = item.get('resume_text', '').strip()
                if resume_text and len(resume_text) > 50:
                    resume_texts.append(resume_text)
                if item.get('name') and item.get('name') not in names_found:
                    names_found.append(item.get('name'))

            # 如果 LLM 返回了文本但 resume_text 为空，尝试用名字做规则拆分
            if not resume_texts and names_found:
                return cls._split_resumes_regex_with_names(text, names_found)

            return resume_texts

        except Exception as e:
            logger.warning(f'LLM 拆分简历失败: {str(e)}')
            return []

    @classmethod
    def _parse_llm_json_response(cls, content: str):
        """解析 LLM 返回的 JSON，处理各种格式问题"""
        if not content:
            return None

        # 清理 markdown code block
        content = content.strip()
        if '```json' in content:
            content = content.split('```json', 1)[1]
        if '```' in content:
            content = content.rsplit('```', 1)[0]

        # 清理 ```
        content = content.strip()
        content = re.sub(r'^```(?:json)?', '', content)
        content = re.sub(r'```$', '', content)
        content = content.strip()

        # 尝试直接解析
        try:
            return json.loads(content)
        except:
            pass

        # 尝试找到第一个 { 或 [
        brace_idx = content.find('{')
        bracket_idx = content.find('[')
        start_idx = -1
        if brace_idx == -1 and bracket_idx == -1:
            return None
        elif brace_idx == -1:
            start_idx = bracket_idx
        elif bracket_idx == -1:
            start_idx = brace_idx
        else:
            start_idx = min(brace_idx, bracket_idx)

        content = content[start_idx:]

        # 找到对应的结束符
        if content.startswith('{'):
            end_char = '}'
        else:
            end_char = ']'

        # 尝试截断到最后一个结束符
        last_end = content.rfind(end_char)
        if last_end > 0:
            content = content[:last_end + 1]

        try:
            return json.loads(content)
        except:
            pass

        # 尝试修复常见的 JSON 错误
        # 移除尾部逗号
        fixed = re.sub(r',\s*([}\]])', r'\1', content)
        try:
            return json.loads(fixed)
        except:
            pass

        # 尝试逐行修复
        lines = content.split(chr(10))
        for i in range(len(lines), 0, -1):
            try:
                return json.loads(chr(10).join(lines[:i]) + end_char)
            except:
                continue

        return None

    @classmethod
    def _split_resumes_regex_with_names(cls, text: str, names: list[str]) -> list[str]:
        """根据给定的名字列表拆分简历"""
        if not names:
            return []

        name_positions = []
        for name in names:
            pos = text.find(name)
            if pos >= 0:
                name_positions.append((pos, name))

        name_positions = sorted(set(name_positions), key=lambda x: x[0])

        resume_texts = []
        for i, (pos, name) in enumerate(name_positions):
            start = pos
            if i + 1 < len(name_positions):
                end_pos = name_positions[i + 1][0]
            else:
                end_pos = len(text)
            segment = text[start:end_pos].strip()
            if len(segment) > 50:
                resume_texts.append(segment)

        # 去重
        filtered = []
        seen = set()
        for rt in resume_texts:
            key = rt[:200]
            if key not in seen:
                seen.add(key)
                filtered.append(rt)

        return filtered

    @classmethod
    def _split_resumes_regex(cls, text: str) -> list[str]:
        """
        正则规则拆分简历（从投标文件文本中识别人员并拆分）
        """
        names = []

        # Strategy 1: 标题格式 "章节编号 级别-姓名"
        title_pattern = re.compile(
            r'(?:^|\n)\s*(?:\d{1,3}(?:\.\d{1,3}){0,3}\s+)?'
            r'(?:初级|中级|高级|资深|专家|工程师|顾问|实习生|项目经理|技术经理|产品经理)\s*[-—]\s*'
            r'([\u4e00-\u9fa5·•]{2,10})',
            re.MULTILINE
        )
        for m in title_pattern.finditer(text):
            name = m.group(1).strip()
            if name and name not in names:
                names.append(name)

        # Strategy 2: "姓名" 标签格式（包括学信网和身份证OCR文本）
        xuexin_name_pattern = re.compile(
            r'(?:^|\n)\s*(?:姓\s*名|姓名)\s*[:：\s]\s*([\u4e00-\u9fa5·•]{2,10})',
            re.MULTILINE
        )
        for m in xuexin_name_pattern.finditer(text):
            name = m.group(1).strip()
            if name and name not in names:
                names.append(name)

        # Strategy 3: 人员清单表格
        EXCLUDE_NAMES = {'性别', '民族', '年龄', '学历', '出生', '住址', '姓名', '学制', '学位', '专业', '学校', '毕业', '身份'}
        if not names:
            person_list_pattern = re.compile(
                r'(?:^|\n)\s*(\d{1,3})\s+'
                r'([\u4e00-\u9fa5·•]{2,10})\s+'
                r'(男|女)\s+'
                r'(\d{1,3})\s+',
                re.MULTILINE
            )
            for m in person_list_pattern.finditer(text):
                name = m.group(2).strip()
                if name and name not in names and name not in EXCLUDE_NAMES:
                    names.append(name)

        # Strategy 4: 行首 姓名+性别+年龄 回退模式
        # 排除"性别""民族""年龄""学历"等字段名被误识别为姓名
        if not names:
            fallback_pattern = re.compile(
                r'(?:^|\n)\s*([\u4e00-\u9fa5·•]{2,10})\s+(男|女)\s+(\d{1,3})',
                re.MULTILINE
            )
            for m in fallback_pattern.finditer(text):
                name = m.group(1).strip()
                if name and name not in names and name not in EXCLUDE_NAMES:
                    names.append(name)

        logger.info(f'规则拆分识别到 {len(names)} 个人员: {names[:10]}')

        if not names:
            return []

        # 找到每个人的起始位置
        name_positions = []
        for name in names:
            pos = -1

            # 优先1: 标题格式位置（跳过目录项：后面跟着一堆点的是目录）
            title_re = re.compile(
                r'(?:^|\n)\s*(?:\d{1,3}(?:\.\d{1,3}){0,3}\s+)?'
                r'(?:初级|中级|高级|资深|专家|工程师|顾问|实习生|项目经理|技术经理|产品经理)\s*[-—]\s*'
                + re.escape(name)
            )
            for m in title_re.finditer(text):
                # 检查后面100字符内有没有连续的点（目录特征）
                after = text[m.end():m.end()+100]
                if '....' in after or '……' in after:
                    continue  # 目录项，跳过
                pos = m.start()
                break
            else:
                # 优先2: "姓名" 标记位置
                name_label_re = re.compile(
                    r'(?:^|\n)\s*(?:姓\s*名|姓名)\s*[:：\s]\s*' + re.escape(name)
                )
                m = name_label_re.search(text)
                if m:
                    pos = m.start()
                else:
                    # 优先3: 人员清单行首位置
                    list_re = re.compile(
                        r'(?:^|\n)\s*(?:\d{1,3}\s+)?' + re.escape(name) + r'\s+(?:男|女)'
                    )
                    m = list_re.search(text)
                    if m:
                        pos = m.start()
                    else:
                        pos = text.find(name)

            if pos >= 0 and (pos, name) not in name_positions:
                name_positions.append((pos, name))

        # 去重并按位置排序
        name_positions = sorted(set(name_positions), key=lambda x: x[0])

        # 按位置切分简历片段
        resume_texts = []
        for i, (pos, name) in enumerate(name_positions):
            start = pos
            if i + 1 < len(name_positions):
                end_pos = name_positions[i + 1][0]
            else:
                end_pos = len(text)
            segment = text[start:end_pos].strip()
            if len(segment) > 50:
                resume_texts.append(segment)

        # 去重
        filtered = []
        seen = set()
        for rt in resume_texts:
            key = rt[:200]
            if key not in seen:
                seen.add(key)
                filtered.append(rt)

        logger.info(f'规则拆分得到 {len(filtered)} 份简历文本')
        return filtered

    @classmethod
    async def _parse_resume_llm_only(
        cls,
        resume_text: str,
    ) -> dict[str, Any]:
        """Phase 1: 仅做 LLM 解析，不触碰 DB"""
        structured_info = await ResumeKbService._extract_structured_info(resume_text)
        abnormal_fields = ResumeKbService._validate_parsed_fields(structured_info)
        if abnormal_fields:
            await ResumeKbService._llm_recheck_fields(
                resume_text, abnormal_fields, structured_info
            )
        tags = ResumeKbService._generate_tags(structured_info)
        structured_info['_tags'] = tags
        return structured_info

    @classmethod
    async def _save_resume_to_db(
        cls,
        structured_info: dict[str, Any],
        file_name: str,
        bid_id: int,
        bid_name: str,
        user_id: int,
    ) -> OaResume | None:
        """Phase 2: 仅做 DB 写入"""
        async with AsyncSessionLocal() as db:
            try:
                tags = structured_info.get('_tags', [])
                resume_uuid = str(uuid.uuid4())

                certs = structured_info.get('certifications', [])
                if isinstance(certs, list) and certs and all(isinstance(c, str) for c in certs):
                    certs = [{'name': c, 'number': '', 'issue_date': '', 'issuer': ''} for c in certs]

                resume_do = OaResume(
                    resume_uuid=resume_uuid,
                    file_name=file_name,
                    name=structured_info.get('name', ''),
                    gender=structured_info.get('gender', ''),
                    age=structured_info.get('age', 0) or 0,
                    birth_date=structured_info.get('birth_date', ''),
                    phone=structured_info.get('phone', ''),
                    email=structured_info.get('email', ''),
                    education=structured_info.get('education', ''),
                    major=structured_info.get('major', ''),
                    school=structured_info.get('school', ''),
                    graduation_date=structured_info.get('graduation_date', ''),
                    work_years=structured_info.get('work_years', 0) or 0,
                    current_company=structured_info.get('current_company', ''),
                    current_position=structured_info.get('current_position', ''),
                    id_card_number=structured_info.get('id_card_number', ''),
                    id_card_address=structured_info.get('id_card_address', ''),
                    degree=structured_info.get('degree', ''),
                    school_system=structured_info.get('school_system', ''),
                    study_form=structured_info.get('study_form', ''),
                    technical_skills=json.dumps(structured_info.get('technical_skills', []), ensure_ascii=False),
                    certifications=json.dumps(certs, ensure_ascii=False),
                    tags=','.join(tags) if isinstance(tags, list) else str(tags) if tags else '',
                    full_text=structured_info.get('_full_text', '')[:5000],
                    parse_time=0,
                    status=1,
                    source_type=2,
                    source_id=bid_id,
                    source_name=bid_name,
                    admin_id=user_id,
                    create_time=int(time.time()),
                    update_time=int(time.time()),
                )

                await ResumeDao.add_resume_dao(db, resume_do)
                logger.info(f'简历主表入库: resume_id={resume_do.id}, name={resume_do.name}')

                work_experiences = structured_info.get('work_experiences', [])
                if isinstance(work_experiences, list):
                    for idx, work in enumerate(work_experiences):
                        if isinstance(work, dict):
                            work_do = OaResumeWork(
                                resume_id=resume_do.id,
                                company=work.get('company', ''),
                                position=work.get('position', ''),
                                start_date=work.get('start_date', ''),
                                end_date=work.get('end_date', ''),
                                description=work.get('description', ''),
                                sort=idx,
                                create_time=int(time.time()),
                            )
                            await ResumeDao.add_resume_work_dao(db, work_do)
                            logger.info(f'  工作经历入库: resume_id={resume_do.id}, company={work_do.company}')

                project_experiences = structured_info.get('project_experiences', [])
                if isinstance(project_experiences, list):
                    for idx, project in enumerate(project_experiences):
                        if isinstance(project, dict):
                            project_do = OaResumeProject(
                                resume_id=resume_do.id,
                                project_name=project.get('project_name', ''),
                                role=project.get('role', ''),
                                start_date=project.get('start_date', ''),
                                end_date=project.get('end_date', ''),
                                description=project.get('description', ''),
                                technologies=json.dumps(project.get('technologies', []), ensure_ascii=False),
                                sort=idx,
                                create_time=int(time.time()),
                            )
                            await ResumeDao.add_resume_project_dao(db, project_do)
                            logger.info(f'  项目经验入库: resume_id={resume_do.id}, project={project_do.project_name}')

                await db.commit()
                logger.info(f'简历入库成功: resume_id={resume_do.id}, name={resume_do.name}')
                return resume_do

            except Exception as e:
                await db.rollback()
                logger.error(f'简历入库失败: name={structured_info.get("name","")}, error={str(e)}')
                return None

    @classmethod
    async def get_bid_document_list_services(
        cls,
        query_db: AsyncSession,
        query_object: BidDocumentPageQueryModel,
        is_page: bool = False,
    ) -> PageModel | list[dict[str, Any]]:
        """获取投标文件列表（含解析进度注入）"""
        result = await BidDao.get_bid_document_list(query_db, query_object, is_page)

        # 注入解析进度（处理中的条目从内存进度字典取实时数据）
        # 同时实时统计简历数量，避免与数据库 resume_count 字段不一致
        # 注意：rows 中的键已被 CamelCaseUtil 转为小驼峰
        rows = result.rows if hasattr(result, 'rows') else result
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    bid_id = row.get('id')
                    if bid_id:
                        actual_count = await BidDao.count_bid_resumes(query_db, bid_id)
                        row['resumeCount'] = actual_count
                    if row.get('status') == 0:
                        bid_uuid = row.get('bidUuid', '')
                        progress = cls._get_progress(bid_uuid)
                        row['parseProgress'] = progress.get('percent', 0)
                        row['parseMessage'] = progress.get('message', '解析中...')

        return result

    @classmethod
    async def get_bid_detail_services(
        cls,
        query_db: AsyncSession,
        bid_id: int,
    ) -> BidDocumentDetailModel:
        """获取投标文件详情（含关联简历）"""
        bid = await BidDao.get_bid_detail_by_id(query_db, bid_id)
        if not bid:
            return BidDocumentDetailModel()

        bid_model = BidDocumentModel.model_validate(bid)
        CamelCaseUtil.transform_result(bid_model)

        resumes = await BidDao.get_bid_related_resumes(query_db, bid_id)
        resume_models = []
        for r in resumes:
            resume_models.append(ResumeModel.model_validate(r))

        # 实时同步 resume_count，避免与 oa_bid_document.resume_count 字段不一致
        bid_model.resume_count = len(resume_models)

        return BidDocumentDetailModel(
            bid=bid_model,
            resume_list=resume_models,
        )

    @classmethod
    async def delete_bid_document_services(
        cls,
        query_db: AsyncSession,
        bid_id: int,
    ) -> CrudResponseModel:
        """删除投标文件（软删除）"""
        try:
            await BidDao.delete_bid_document(query_db, bid_id)
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            logger.error(f'删除投标文件失败: {str(e)}')
            raise ServiceException(message=f'删除投标文件失败: {str(e)}')

    @classmethod
    async def get_bid_progress_services(cls, bid_uuid: str) -> dict:
        """获取投标文件解析进度"""
        return cls._get_progress(bid_uuid)